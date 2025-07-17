import math
import random
from typing import List, Tuple, Dict
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import logging
from datetime import datetime, timedelta

class TSPSolver:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="route_optimizer")
        self.distance_cache = {}
        
    def geocode_address(self, address: str) -> Tuple[float, float]:
        """Convert address to coordinates"""
        try:
            location = self.geolocator.geocode(address)
            if location:
                return (location.latitude, location.longitude)
            else:
                # Fallback to random coordinates for demo purposes
                logging.warning(f"Could not geocode address: {address}")
                return (40.7128 + random.uniform(-0.1, 0.1), -74.0060 + random.uniform(-0.1, 0.1))
        except Exception as e:
            logging.error(f"Geocoding error for {address}: {e}")
            return (40.7128 + random.uniform(-0.1, 0.1), -74.0060 + random.uniform(-0.1, 0.1))
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in kilometers"""
        cache_key = (coord1, coord2)
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]
        
        try:
            distance = geodesic(coord1, coord2).kilometers
            self.distance_cache[cache_key] = distance
            return distance
        except Exception as e:
            logging.error(f"Distance calculation error: {e}")
            # Fallback to Euclidean distance
            return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2) * 111  # Approximate km per degree
    
    def create_distance_matrix(self, stops: List[Dict]) -> List[List[float]]:
        """Create distance matrix for all stops"""
        n = len(stops)
        matrix = [[0.0] * n for _ in range(n)]
        
        # Get coordinates for all stops
        coordinates = []
        for stop in stops:
            coord = self.geocode_address(stop['address'])
            coordinates.append(coord)
        
        # Calculate distances
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = self.calculate_distance(coordinates[i], coordinates[j])
        
        return matrix
    
    def nearest_neighbor_tsp(self, distance_matrix: List[List[float]], start_index: int = 0) -> List[int]:
        """Solve TSP using nearest neighbor algorithm"""
        n = len(distance_matrix)
        if n <= 1:
            return list(range(n))
        
        visited = [False] * n
        tour = [start_index]
        visited[start_index] = True
        current = start_index
        
        for _ in range(n - 1):
            nearest_distance = float('inf')
            nearest_city = -1
            
            for next_city in range(n):
                if not visited[next_city] and distance_matrix[current][next_city] < nearest_distance:
                    nearest_distance = distance_matrix[current][next_city]
                    nearest_city = next_city
            
            if nearest_city != -1:
                tour.append(nearest_city)
                visited[nearest_city] = True
                current = nearest_city
        
        return tour
    
    def two_opt_improvement(self, tour: List[int], distance_matrix: List[List[float]]) -> List[int]:
        """Improve tour using 2-opt local search"""
        def calculate_tour_distance(tour_path):
            total = 0
            for i in range(len(tour_path) - 1):
                total += distance_matrix[tour_path[i]][tour_path[i + 1]]
            return total
        
        best_tour = tour[:]
        best_distance = calculate_tour_distance(best_tour)
        improved = True
        
        while improved:
            improved = False
            for i in range(1, len(tour) - 2):
                for j in range(i + 1, len(tour)):
                    if j - i == 1:
                        continue
                    
                    # Create new tour by reversing segment between i and j
                    new_tour = tour[:i] + tour[i:j][::-1] + tour[j:]
                    new_distance = calculate_tour_distance(new_tour)
                    
                    if new_distance < best_distance:
                        best_tour = new_tour
                        best_distance = new_distance
                        improved = True
            
            tour = best_tour
        
        return best_tour
    
    def solve_tsp(self, stops: List[Dict]) -> List[int]:
        """Solve TSP for given stops"""
        if len(stops) <= 1:
            return list(range(len(stops)))
        
        # Create distance matrix
        distance_matrix = self.create_distance_matrix(stops)
        
        # Solve using nearest neighbor
        tour = self.nearest_neighbor_tsp(distance_matrix)
        
        # Improve with 2-opt
        if len(stops) > 2:
            tour = self.two_opt_improvement(tour, distance_matrix)
        
        return tour
    
    def get_traffic_multiplier(self, start_time: str, elapsed_minutes: int) -> float:
        """Get traffic multiplier based on time of day"""
        # Parse start time
        try:
            start_hour, start_minute = map(int, start_time.split(':'))
        except:
            start_hour, start_minute = 7, 0
        
        # Calculate current time
        current_hour = start_hour + (start_minute + elapsed_minutes) // 60
        current_minute = (start_minute + elapsed_minutes) % 60
        current_time = current_hour + current_minute / 60
        
        # Traffic multipliers based on historical data patterns
        if 6 <= current_time < 8:  # Morning rush building
            return 1.5
        elif 8 <= current_time < 10:  # Morning rush peak
            return 2.0
        elif 10 <= current_time < 16:  # Midday normal
            return 1.0
        elif 16 <= current_time < 18:  # Evening rush building
            return 1.7
        elif 18 <= current_time < 20:  # Evening rush peak
            return 2.2
        else:  # Off-peak hours
            return 0.8
    
    def calculate_distance_with_traffic(self, coord1: Tuple[float, float], coord2: Tuple[float, float], 
                                      start_time: str, elapsed_minutes: int) -> float:
        """Calculate distance with traffic consideration"""
        base_distance = self.calculate_distance(coord1, coord2)
        traffic_multiplier = self.get_traffic_multiplier(start_time, elapsed_minutes)
        return base_distance * traffic_multiplier
    
    def create_traffic_distance_matrix(self, stops: List[Dict], start_time: str) -> List[List[float]]:
        """Create distance matrix considering traffic patterns"""
        n = len(stops)
        matrix = [[0.0] * n for _ in range(n)]
        
        # Get coordinates for all stops
        coordinates = []
        for stop in stops:
            coord = self.geocode_address(stop['address'])
            coordinates.append(coord)
        
        # Calculate distances with traffic consideration
        elapsed_time = 0
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Estimate elapsed time based on position in route
                    estimated_elapsed = elapsed_time + (i * 15)  # 15 min avg per stop
                    matrix[i][j] = self.calculate_distance_with_traffic(
                        coordinates[i], coordinates[j], start_time, estimated_elapsed
                    )
        
        return matrix
    
    def solve_tsp_with_traffic(self, stops: List[Dict], start_time: str) -> List[int]:
        """Solve TSP with traffic consideration"""
        if len(stops) <= 1:
            return list(range(len(stops)))
        
        # Create traffic-aware distance matrix
        distance_matrix = self.create_traffic_distance_matrix(stops, start_time)
        
        # Solve using nearest neighbor
        tour = self.nearest_neighbor_tsp(distance_matrix)
        
        # Improve with 2-opt
        if len(stops) > 2:
            tour = self.two_opt_improvement(tour, distance_matrix)
        
        return tour
    
    def calculate_total_time_with_traffic(self, stops: List[Dict], tour: List[int], start_time: str) -> int:
        """Calculate total time with traffic consideration"""
        if len(stops) <= 1:
            return 10 if stops else 0
        
        # Get coordinates for all stops
        coordinates = []
        for stop in stops:
            coord = self.geocode_address(stop['address'])
            coordinates.append(coord)
        
        total_time = 0
        elapsed_time = 0
        
        # Add service time for each stop (10 minutes)
        total_time += len(stops) * 10
        
        # Add travel time with traffic consideration
        for i in range(len(tour) - 1):
            distance_km = self.calculate_distance(coordinates[tour[i]], coordinates[tour[i + 1]])
            traffic_multiplier = self.get_traffic_multiplier(start_time, elapsed_time)
            
            # Base speed 30 km/h, adjusted for traffic
            adjusted_speed = 30 / traffic_multiplier
            travel_time_minutes = (distance_km / adjusted_speed) * 60
            
            total_time += travel_time_minutes
            elapsed_time += travel_time_minutes + 10  # Include service time
        
        return int(total_time)
    
    def calculate_total_time(self, stops: List[Dict], tour: List[int]) -> int:
        """Calculate total time for a tour including service time"""
        if len(stops) <= 1:
            return 10 if stops else 0
        
        distance_matrix = self.create_distance_matrix(stops)
        total_time = 0
        
        # Add service time for each stop (10 minutes)
        total_time += len(stops) * 10
        
        # Add travel time (assume 30 km/h average speed)
        for i in range(len(tour) - 1):
            distance_km = distance_matrix[tour[i]][tour[i + 1]]
            travel_time_minutes = (distance_km / 30) * 60  # 30 km/h converted to minutes
            total_time += travel_time_minutes
        
        return int(total_time)
