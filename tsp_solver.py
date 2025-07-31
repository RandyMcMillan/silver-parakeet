import math
import random
from typing import List, Tuple, Dict
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import logging
from datetime import datetime, timedelta
from distance_cache import distance_cache
from christofides_tsp import ChristofidesTSPSolver

class TSPSolver:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="route_optimizer")
        self.distance_cache = {}
        self.christofides_solver = ChristofidesTSPSolver()
        self.use_advanced_algorithms = True
        
    def geocode_address(self, address: str) -> Tuple[float, float]:
        """Convert address to coordinates with reliable fallback"""
        try:
            # Try online geocoding first with timeout
            location = self.geolocator.geocode(address, timeout=3)
            if location:
                return (location.latitude, location.longitude)
            else:
                logging.warning(f"Could not geocode address: {address}, using fallback")
                return self.get_fallback_coordinates(address)
        except Exception as e:
            logging.error(f"Geocoding error for {address}: {e}, using fallback")
            return self.get_fallback_coordinates(address)
    
    def get_fallback_coordinates(self, address: str) -> Tuple[float, float]:
        """Provide fallback coordinates based on city/ZIP patterns"""
        address_lower = address.lower()
        
        # Atlanta area fallback coordinates
        if 'atlanta' in address_lower or '303' in address:
            return (33.7490, -84.3880)  # Atlanta downtown
        
        # New York area fallback coordinates  
        if 'new york' in address_lower or 'ny' in address_lower or '100' in address:
            return (40.7128, -74.0060)  # NYC downtown
        
        # Los Angeles area fallback coordinates
        if 'los angeles' in address_lower or 'beverly hills' in address_lower or '902' in address:
            return (34.0522, -118.2437)  # LA downtown
            
        # Chicago area fallback coordinates
        if 'chicago' in address_lower or '606' in address:
            return (41.8781, -87.6298)  # Chicago downtown
            
        # Miami area fallback coordinates
        if 'miami' in address_lower or '331' in address:
            return (25.7617, -80.1918)  # Miami downtown
        
        # Default fallback to Atlanta if no pattern matches
        logging.info(f"No location pattern found for {address}, defaulting to Atlanta")
        return (33.7490, -84.3880)
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in kilometers with advanced caching"""
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
    
    def calculate_distance_with_cache(self, addr1: str, addr2: str, traffic_hour: float = 12.0) -> Tuple[float, float]:
        """Calculate distance using database cache for performance optimization"""
        # Try database cache first
        cached_result = distance_cache.get_cached_distance(addr1, addr2, traffic_hour)
        if cached_result:
            return cached_result  # (distance_km, travel_time_minutes)
        
        # Calculate fresh values
        coord1 = self.geocode_address(addr1)
        coord2 = self.geocode_address(addr2)
        distance_km = self.calculate_distance(coord1, coord2)
        
        # Base travel time (assuming 30 km/h average in city)
        base_travel_time = (distance_km / 30) * 60  # minutes
        
        # Cache the result
        distance_cache.cache_distance(addr1, addr2, distance_km, base_travel_time)
        
        # Apply traffic multiplier for return value
        traffic_multiplier = distance_cache._get_traffic_multiplier(traffic_hour)
        adjusted_time = base_travel_time * traffic_multiplier
        
        return (distance_km, adjusted_time)
    
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
        """Solve TSP using advanced algorithms for optimal routes"""
        if len(stops) <= 1:
            return list(range(len(stops)))
        
        # Create distance matrix with caching
        distance_matrix = self.create_distance_matrix_optimized(stops)
        
        # Choose algorithm based on problem size and settings
        if self.use_advanced_algorithms and len(stops) >= 4:
            try:
                # Use Christofides algorithm for better solutions
                christofides_tour, christofides_distance = self.christofides_solver.solve_tsp(distance_matrix)
                logging.info(f"Christofides algorithm: {len(stops)} stops, distance: {christofides_distance:.1f}")
                
                # Apply 2-opt improvement to Christofides solution
                if len(stops) > 6:
                    improved_tour = self.christofides_solver.two_opt_improvement(christofides_tour, distance_matrix)
                    return improved_tour
                
                return christofides_tour
                
            except Exception as e:
                logging.warning(f"Christofides failed, using nearest neighbor: {e}")
        
        # Fallback to nearest neighbor + 2-opt
        tour = self.nearest_neighbor_tsp(distance_matrix)
        
        # Improve with 2-opt
        if len(stops) > 2:
            tour = self.two_opt_improvement(tour, distance_matrix)
        
        return tour
    
    def create_distance_matrix_optimized(self, stops: List[Dict]) -> List[List[float]]:
        """Create distance matrix with database caching for performance"""
        n = len(stops)
        matrix = [[0.0] * n for _ in range(n)]
        
        cache_hits = 0
        cache_misses = 0
        
        # Calculate distances with caching
        for i in range(n):
            for j in range(n):
                if i != j:
                    addr1 = stops[i]['address']
                    addr2 = stops[j]['address']
                    
                    # Use cached distance calculation
                    distance_km, _ = self.calculate_distance_with_cache(addr1, addr2)
                    matrix[i][j] = distance_km
                    
                    if distance_cache.hit_count > cache_hits:
                        cache_hits += 1
                    else:
                        cache_misses += 1
        
        # Log cache performance
        total_requests = cache_hits + cache_misses
        if total_requests > 0:
            hit_rate = (cache_hits / total_requests) * 100
            logging.info(f"Distance matrix cache performance: {hit_rate:.1f}% hit rate ({cache_hits}/{total_requests})")
        
        return matrix
    
    def get_traffic_multiplier(self, start_time: str, elapsed_minutes: float) -> float:
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
                                      start_time: str, elapsed_minutes: float) -> float:
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
    
    def check_overtime_approval(self, total_minutes: int, lead_time_weeks: int, 
                               allow_overtime: bool = True) -> Tuple[bool, str]:
        """Check if overtime is approved based on 8.5-hour target and 9-hour limit policy"""
        # Target 8.5-hour workday = 510 minutes  
        # Hard limit 9-hour workday = 540 minutes
        
        if total_minutes <= 510:  # Within 8.5-hour target
            return True, "Within 8.5-hour target workday"
        
        if total_minutes <= 540:  # Within 9-hour limit but over target
            return True, "Acceptable: Under 9-hour limit but exceeds 8.5h target"
        
        if not allow_overtime:
            return False, "Exceeds 9-hour limit, overtime not permitted"
        
        # Over 9-hour limit - requires special approval with 8-week lead time
        minimum_lead_time = 8  # weeks
        if lead_time_weeks >= minimum_lead_time:
            overtime_hours = (total_minutes - 480) / 60
            return True, f"CRITICAL overtime approved ({overtime_hours:.1f} hours) with {lead_time_weeks}-week lead time"
        else:
            needed_weeks = minimum_lead_time - lead_time_weeks
            return False, f"Exceeds 9-hour limit, requires {minimum_lead_time}-week lead time (need {needed_weeks} more weeks)"
    
    def optimize_for_8_hour_workday(self, stops: List[Dict], start_time: str, max_drivers: int = 10, 
                                   allow_overtime: bool = True, lead_time_weeks: int = 0) -> List[List[int]]:
        """Optimize routes to fit within 8-hour workdays"""
        if not stops:
            return []
        
        # Start with single driver and see if we can fit all stops
        for num_drivers in range(1, max_drivers + 1):
            routes = self.distribute_stops_for_workday(stops, num_drivers, start_time)
            
            # Check if all routes fit within 8 hours or have overtime approval
            all_within_limit = True
            for route in routes:
                if route:  # Skip empty routes
                    total_time = self.calculate_total_time_with_traffic(
                        [stops[i] for i in route], route, start_time
                    )
                    
                    # Check overtime approval if exceeds 8 hours
                    overtime_approved, reason = self.check_overtime_approval(
                        total_time, lead_time_weeks, allow_overtime
                    )
                    
                    if not overtime_approved:
                        all_within_limit = False
                        logging.info(f"Route exceeds limits: {reason}")
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
    
    def group_paired_stops(self, stops: List[Dict]) -> Tuple[List[List[Dict]], List[Dict]]:
        """
        Group pickup/reinstall pairs together and return paired groups and single stops
        """
        paired_groups = {}
        single_stops = []
        
        for stop in stops:
            if stop.get('is_pickup_reinstall', False):
                pair_id = stop.get('pair_group_id')
                if pair_id:
                    if pair_id not in paired_groups:
                        paired_groups[pair_id] = []
                    paired_groups[pair_id].append(stop)
                else:
                    # Fallback: pair by pickup/reinstall addresses
                    pickup_addr = stop.get('pickup_address', '')
                    reinstall_addr = stop.get('reinstall_address', '')
                    pair_key = f"{pickup_addr}|{reinstall_addr}"
                    
                    if pair_key not in paired_groups:
                        paired_groups[pair_key] = []
                    paired_groups[pair_key].append(stop)
            else:
                single_stops.append(stop)
        
        # Convert paired groups to list and ensure proper ordering (pickup first, reinstall second)
        paired_lists = []
        for group in paired_groups.values():
            if len(group) == 2:
                # Sort so pickup comes before reinstall
                sorted_group = sorted(group, key=lambda x: 0 if x.get('service_type') == 'pickup' else 1)
                paired_lists.append(sorted_group)
            else:
                # If incomplete pair, treat as single stops
                single_stops.extend(group)
        
        return paired_lists, single_stops

    def optimize_routes_with_traffic(self, stops: List[Dict], departure_address: str, num_drivers: int, start_time: str) -> List[Dict]:
        """
        Main optimization function that creates routes respecting 9-hour limit and paired stops
        """
        if not stops:
            return []
        
        try:
            logging.info(f"Starting route optimization for {len(stops)} stops with {num_drivers} drivers")
            
            # Group paired stops and single stops
            paired_groups, single_stops = self.group_paired_stops(stops)
            
            logging.info(f"Found {len(paired_groups)} pickup/reinstall pairs and {len(single_stops)} single stops")
            
            # Calculate maximum capacity considering paired stops count as 2
            max_stops_per_driver = 16
            max_total_capacity = num_drivers * max_stops_per_driver
            
            # Count total stops including pairs
            total_stop_count = len(single_stops) + (len(paired_groups) * 2)
            
            # Priority sorting for single stops: scheduled first, then ASAP (both by timestamp)
            scheduled_single = [s for s in single_stops if not s.get('is_asap', False)]
            asap_single = [s for s in single_stops if s.get('is_asap', False)]
            
            # Sort scheduled by required date, ASAP by created timestamp (oldest first) 
            scheduled_single.sort(key=lambda x: x.get('required_date') or datetime.now())
            asap_single.sort(key=lambda x: x.get('created_at', datetime.now()))
            
            # Priority sorting for paired groups (use pickup stop for sorting)
            scheduled_pairs = [pair for pair in paired_groups if not pair[0].get('is_asap', False)]
            asap_pairs = [pair for pair in paired_groups if pair[0].get('is_asap', False)]
            
            scheduled_pairs.sort(key=lambda x: x[0].get('required_date') or datetime.now())
            asap_pairs.sort(key=lambda x: x[0].get('created_at', datetime.now()))
            
            # Combine: scheduled first, then ASAP (both pairs and singles interleaved by priority)
            all_scheduled = scheduled_pairs + [[s] for s in scheduled_single]
            all_asap = asap_pairs + [[s] for s in asap_single]
            
            # Merge scheduled and ASAP maintaining relative order
            prioritized_work_units = all_scheduled + all_asap
            
            # Handle capacity limits - ignore excess work units
            if total_stop_count > max_total_capacity:
                # Remove excess work units from the end (lowest priority ASAP)
                current_count = 0
                final_work_units = []
                
                for work_unit in prioritized_work_units:
                    unit_size = len(work_unit)  # 1 for single, 2 for pair
                    if current_count + unit_size <= max_total_capacity:
                        final_work_units.append(work_unit)
                        current_count += unit_size
                    else:
                        break
                
                excess_count = total_stop_count - current_count
                prioritized_work_units = final_work_units
                logging.warning(f"Capacity exceeded: ignoring {excess_count} excess stops")
            
            logging.info(f"Processing {len(prioritized_work_units)} work units (capacity: {max_total_capacity})")
            
            # Distribute work units across drivers using round-robin
            driver_assignments = [[] for _ in range(num_drivers)]
            driver_stop_counts = [0] * num_drivers
            
            for work_unit in prioritized_work_units:
                # Find driver with lowest stop count
                min_count = min(driver_stop_counts)
                min_driver_idx = driver_stop_counts.index(min_count)
                
                # Assign work unit to this driver
                driver_assignments[min_driver_idx].extend(work_unit)
                driver_stop_counts[min_driver_idx] += len(work_unit)
            
            # Create routes for each driver
            routes = []
            for driver_num in range(1, num_drivers + 1):
                driver_stops = driver_assignments[driver_num - 1]
                
                if driver_stops:
                    route = self.create_route_with_timing(driver_stops, departure_address, driver_num, start_time)
                    routes.append(route)
            
            return routes
            
        except Exception as e:
            logging.error(f"Route optimization error: {e}")
            return []
    
    def create_route_with_timing(self, stops: List[Dict], departure_address: str, driver_num: int, start_time: str) -> Dict:
        """
        Create a route with timing information for a driver
        """
        if not stops:
            return {
                'driver_number': driver_num,
                'stops': [],
                'total_time': 0,
                'departure_address': departure_address,
                'start_time': start_time
            }
        
        try:
            # Optimize the order of stops for this driver
            optimized_indices = self.solve_tsp_with_traffic(stops, start_time)
            
            # Create ordered stops list
            ordered_stops = [stops[i] for i in optimized_indices if i < len(stops)]
            
            # Calculate total time
            total_time = self.calculate_total_time_with_traffic(ordered_stops, list(range(len(ordered_stops))), start_time)
            
            # Add departure and return trips (25 minutes each)
            total_time += 50  # 25 min to first stop + 25 min back from last stop
            
            return {
                'driver_number': driver_num,
                'stops': ordered_stops,
                'total_time': total_time,
                'departure_address': departure_address,
                'start_time': start_time,
                'ordered_stop_indices': optimized_indices
            }
            
        except Exception as e:
            logging.error(f"Error creating route for driver {driver_num}: {e}")
            return {
                'driver_number': driver_num,
                'stops': stops,
                'total_time': len(stops) * 10 + 50,  # Fallback estimate
                'departure_address': departure_address,
                'start_time': start_time
            }
