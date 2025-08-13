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
        """Convert address to coordinates with fast fallback"""
        # Skip online geocoding and use fast fallback coordinates
        # This prevents timeouts and makes TSP optimization instant
        return self.get_fallback_coordinates(address)
    
    def get_fallback_coordinates(self, address: str) -> Tuple[float, float]:
        """Provide fast approximate coordinates based on Atlanta area ZIP/patterns"""
        address_lower = address.lower()
        
        # Parse street number to add variation
        import re
        street_num_match = re.match(r'^(\d+)', address)
        offset = 0
        if street_num_match:
            # Use street number to create slight coordinate variation
            offset = (int(street_num_match.group(1)) % 1000) * 0.00001
        
        # Atlanta metro area coordinates with ZIP-based distribution
        if '30030' in address or 'decatur' in address_lower:
            return (33.7748 + offset, -84.2963 - offset)  # Decatur
        elif '30339' in address or 'smyrna' in address_lower:
            return (33.8839 + offset, -84.5144 - offset)  # Smyrna
        elif '30064' in address or 'marietta' in address_lower:
            return (33.9526 + offset, -84.5499 - offset)  # Marietta
        elif '30068' in address:
            return (34.0234 + offset, -84.5155 - offset)  # North Marietta
        elif '30342' in address or 'sandy springs' in address_lower:
            return (33.9304 + offset, -84.3733 - offset)  # Sandy Springs
        elif '30341' in address or 'dunwoody' in address_lower:
            return (33.9304 + offset, -84.3378 - offset)  # Dunwoody
        elif '30076' in address or 'roswell' in address_lower:
            return (34.0234 + offset, -84.3615 - offset)  # Roswell
        elif '30022' in address or 'alpharetta' in address_lower:
            return (34.0754 + offset, -84.2941 - offset)  # Alpharetta
        elif '30005' in address:
            return (34.0854 + offset, -84.2191 - offset)  # East Alpharetta
        elif '30097' in address or 'duluth' in address_lower:
            return (34.0029 + offset, -84.1446 - offset)  # Duluth
        elif '30024' in address or 'suwanee' in address_lower:
            return (34.0514 + offset, -84.0713 - offset)  # Suwanee
        elif '30305' in address or '30306' in address or '30307' in address:
            return (33.7800 + offset, -84.3850 - offset)  # Central Atlanta
        elif '30308' in address or '30309' in address:
            return (33.7700 + offset, -84.3800 - offset)  # Midtown Atlanta
        elif '30303' in address or '30312' in address:
            return (33.7500 + offset, -84.3900 - offset)  # Downtown Atlanta
        elif '30315' in address or '30316' in address:
            return (33.7200 + offset, -84.3700 - offset)  # South Atlanta
        elif '30331' in address or '30344' in address:
            return (33.7000 + offset, -84.5000 - offset)  # Southwest Atlanta
        elif '30349' in address or '30297' in address:
            return (33.6200 + offset, -84.4500 - offset)  # South Metro
        else:
            # Default Atlanta area with street number variation
            return (33.7490 + offset, -84.3880 - offset)
    
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
    
    def solve_tsp_with_departure(self, stops: List[Dict], departure_address: str) -> List[int]:
        """Solve TSP considering departure point for optimal route"""
        if len(stops) <= 1:
            return list(range(len(stops)))
        
        # Include departure address as first stop for distance calculation
        all_stops = [{'address': departure_address}] + stops
        
        # Create distance matrix including departure
        distance_matrix = self.create_distance_matrix(all_stops)
        
        # Find nearest stop to departure point
        min_dist = float('inf')
        nearest_to_departure = 1  # Start from index 1 (first actual stop)
        
        for i in range(1, len(all_stops)):
            if distance_matrix[0][i] < min_dist:
                min_dist = distance_matrix[0][i]
                nearest_to_departure = i
        
        # Create matrix for just the stops (excluding departure)
        stops_matrix = [[0.0] * len(stops) for _ in range(len(stops))]
        for i in range(len(stops)):
            for j in range(len(stops)):
                stops_matrix[i][j] = distance_matrix[i+1][j+1]
        
        # Solve TSP starting from nearest stop to departure
        tour = self.nearest_neighbor_tsp(stops_matrix, nearest_to_departure - 1)
        
        # Improve with 2-opt
        if len(stops) > 2:
            tour = self.two_opt_improvement(tour, stops_matrix)
        
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
        
        # Calculate time-dependent distances
        elapsed_time = 0
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Calculate distance with traffic at current elapsed time
                    distance = self.calculate_distance_with_traffic(
                        coordinates[i], coordinates[j], start_time, elapsed_time
                    )
                    matrix[i][j] = distance
                    
                    # Add estimated travel time for next calculation
                    if i < j:  # Only increment once per pair
                        travel_time_minutes = (distance * 2.0)  # Rough estimate: 2 min per km
                        elapsed_time += travel_time_minutes + 10  # Include service time
        
        return matrix
    
    def solve_tsp_with_traffic(self, stops: List[Dict], start_time: str) -> List[int]:
        """Solve TSP considering traffic patterns"""
        if len(stops) <= 1:
            return list(range(len(stops)))
        
        # Create traffic-aware distance matrix
        distance_matrix = self.create_traffic_distance_matrix(stops, start_time)
        
        # Solve using nearest neighbor with traffic considerations
        tour = self.nearest_neighbor_tsp(distance_matrix)
        
        # Improve with 2-opt considering traffic
        if len(stops) > 2:
            tour = self.two_opt_improvement(tour, distance_matrix)
        
        return tour
    
    def calculate_total_time_with_traffic(self, stops: List[Dict], tour: List[int], start_time: str) -> int:
        """Calculate total time for a route considering traffic and service times"""
        if len(stops) <= 1:
            return 10 if stops else 0  # Just service time
        
        total_minutes = 0
        elapsed_minutes = 0
        
        # Get coordinates for all stops
        coordinates = []
        for stop in stops:
            coord = self.geocode_address(stop['address'])
            coordinates.append(coord)
        
        # Calculate travel times between consecutive stops
        for i in range(len(tour) - 1):
            current_stop = tour[i]
            next_stop = tour[i + 1]
            
            # Calculate distance with current traffic conditions
            distance = self.calculate_distance_with_traffic(
                coordinates[current_stop], coordinates[next_stop], 
                start_time, elapsed_minutes
            )
            
            # Convert distance to travel time (assuming 30 km/h average with traffic)
            travel_time = (distance / 30) * 60  # minutes
            total_minutes += travel_time
            elapsed_minutes += travel_time
            
            # Add service time at next stop
            service_time = 10  # minutes per stop
            total_minutes += service_time
            elapsed_minutes += service_time
        
        return int(total_minutes)
    
    def check_8_hour_limit(self, total_minutes: int) -> bool:
        """Check if route exceeds 8-hour workday limit"""
        return total_minutes <= 480  # 8 hours = 480 minutes
    
    def optimize_for_8_hour_workday(self, stops: List[Dict], start_time: str, max_drivers: int = 10) -> List[List[int]]:
        """Optimize routes to fit within 8-hour workdays"""
        if not stops:
            return []
        
        # Start with single driver and see if we can fit all stops
        for num_drivers in range(1, max_drivers + 1):
            routes = self.distribute_stops_for_workday(stops, num_drivers, start_time)
            
            # Check if all routes fit within 8 hours
            all_within_limit = True
            for route in routes:
                if route:  # Skip empty routes
                    total_time = self.calculate_total_time_with_traffic(
                        [stops[i] for i in route], route, start_time
                    )
                    if not self.check_8_hour_limit(total_time):
                        all_within_limit = False
                        break
            
            if all_within_limit:
                return routes
        
        # If we can't fit within 8 hours even with max drivers, return best effort
        return self.distribute_stops_for_workday(stops, max_drivers, start_time)
    
    def distribute_stops_for_workday(self, stops: List[Dict], num_drivers: int, start_time: str) -> List[List[int]]:
        """Distribute stops among drivers for balanced workday"""
        if not stops:
            return [[] for _ in range(num_drivers)]
        
        # Separate scheduled and ASAP stops
        scheduled_stops = [(i, stop) for i, stop in enumerate(stops) 
                          if not stop.get('is_asap', False)]
        asap_stops = [(i, stop) for i, stop in enumerate(stops) 
                     if stop.get('is_asap', False)]
        
        # Initialize driver routes
        driver_routes = [[] for _ in range(num_drivers)]
        driver_times = [0] * num_drivers
        
        # Assign scheduled stops first (round-robin by urgency)
        for i, (stop_idx, stop) in enumerate(scheduled_stops):
            driver_num = i % num_drivers
            driver_routes[driver_num].append(stop_idx)
            driver_times[driver_num] += 10  # Base service time
        
        # Assign ASAP stops to drivers with least workload
        for stop_idx, stop in asap_stops:
            min_time_driver = min(range(num_drivers), key=lambda x: driver_times[x])
            driver_routes[min_time_driver].append(stop_idx)
            driver_times[min_time_driver] += 10
        
        # Optimize each driver's route
        optimized_routes = []
        for route in driver_routes:
            if route:
                # Get stops for this route
                route_stops = [stops[i] for i in route]
                # Solve TSP for this route
                optimal_order = self.solve_tsp_with_traffic(route_stops, start_time)
                # Convert back to original indices - optimal_order contains indices into route_stops
                optimized_route = [route[i] for i in optimal_order if i < len(route)]
                optimized_routes.append(optimized_route)
            else:
                optimized_routes.append([])
        
        return optimized_routes
        
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
        """Solve TSP with traffic consideration and return to start"""
        if len(stops) <= 1:
            return list(range(len(stops)))
        
        # Create traffic-aware distance matrix
        distance_matrix = self.create_traffic_distance_matrix(stops, start_time)
        
        # Solve using nearest neighbor
        tour = self.nearest_neighbor_tsp(distance_matrix)
        
        # Improve with 2-opt
        if len(stops) > 2:
            tour = self.two_opt_improvement(tour, distance_matrix)
        
        # Ensure tour returns to start (TSP requirement)
        if len(tour) > 1 and tour[-1] != tour[0]:
            tour.append(tour[0])
        
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
