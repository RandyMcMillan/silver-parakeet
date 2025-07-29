import logging
import math
from typing import List, Dict, Tuple
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

class GeographicClusterer:
    """Clusters stops by geographic proximity for efficient route assignment"""
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="route_optimizer")
        self.geocache = {}  # Cache coordinates to avoid repeated API calls
        
    def get_coordinates(self, address: str) -> Tuple[float, float]:
        """Get latitude/longitude for an address with caching"""
        if address in self.geocache:
            return self.geocache[address]
            
        # Skip external geocoding to prevent timeouts, use area-based coordinates
        try:
            fallback = self.get_area_fallback_coordinates(address)
            self.geocache[address] = fallback
            logging.info(f"Using area-based coordinates for {address}: {fallback}")
            return fallback
        except Exception as e:
            logging.error(f"Fallback coordinate error for {address}: {e}")
            # Default Atlanta center
            default = (33.7490, -84.3880)
            self.geocache[address] = default
            return default
    
    def calculate_distance(self, addr1: str, addr2: str) -> float:
        """Calculate distance between two addresses in miles"""
        try:
            coords1 = self.get_coordinates(addr1)
            coords2 = self.get_coordinates(addr2)
            distance = geodesic(coords1, coords2).miles
            return distance
        except Exception as e:
            logging.error(f"Distance calculation error: {e}")
            return 10.0  # Fallback estimate
    
    def get_area_fallback_coordinates(self, address: str) -> Tuple[float, float]:
        """Get fallback coordinates based on Atlanta area keywords"""
        address_lower = address.lower()
        
        # Atlanta area fallback coordinates
        if 'peachtree' in address_lower or 'buckhead' in address_lower:
            return (33.8484, -84.3781)  # Buckhead area
        elif 'sandy springs' in address_lower:
            return (33.9304, -84.3733)
        elif 'marietta' in address_lower:
            return (33.9526, -84.5499)
        elif 'dunwoody' in address_lower:
            return (33.9463, -84.3346)
        elif 'roswell' in address_lower:
            return (34.0232, -84.3616)
        elif 'decatur' in address_lower:
            return (33.7748, -84.2963)
        elif 'tucker' in address_lower:
            return (33.8485, -84.2169)
        elif 'east point' in address_lower:
            return (33.6818, -84.4402)
        elif 'college park' in address_lower:
            return (33.6534, -84.4493)
        else:
            return (33.7490, -84.3880)  # Default Atlanta center
    
    def cluster_stops_by_proximity(self, stops: List[Dict], num_drivers: int) -> List[List[Dict]]:
        """
        Cluster stops by geographic proximity using a simple clustering algorithm
        
        Args:
            stops: List of stop dictionaries with 'id', 'address', etc.
            num_drivers: Number of drivers (clusters) to create
            
        Returns:
            List of clusters, each containing a list of stops
        """
        if not stops:
            return []
            
        if len(stops) <= num_drivers:
            # If we have fewer stops than drivers, each gets one stop
            return [[stop] for stop in stops]
        
        logging.info(f"Clustering {len(stops)} stops for {num_drivers} drivers based on geographic proximity")
        
        # Start with each stop as its own cluster
        clusters = [[stop] for stop in stops]
        
        # Merge clusters until we have the desired number
        while len(clusters) > num_drivers:
            min_distance = float('inf')
            merge_indices = (0, 1)
            
            # Find the two closest clusters
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # Calculate minimum distance between clusters
                    cluster_distance = self.calculate_cluster_distance(clusters[i], clusters[j])
                    if cluster_distance < min_distance:
                        min_distance = cluster_distance
                        merge_indices = (i, j)
            
            # Merge the two closest clusters
            i, j = merge_indices
            clusters[i].extend(clusters[j])
            clusters.pop(j)
            
            logging.debug(f"Merged clusters, now have {len(clusters)} clusters")
        
        # Balance clusters by size if needed
        clusters = self.balance_clusters(clusters, num_drivers)
        
        return clusters
    
    def calculate_cluster_distance(self, cluster1: List[Dict], cluster2: List[Dict]) -> float:
        """Calculate the minimum distance between any two stops in different clusters"""
        min_distance = float('inf')
        
        for stop1 in cluster1:
            for stop2 in cluster2:
                distance = self.calculate_distance(stop1['address'], stop2['address'])
                min_distance = min(min_distance, distance)
        
        return min_distance
    
    def balance_clusters(self, clusters: List[List[Dict]], target_count: int) -> List[List[Dict]]:
        """Balance cluster sizes to avoid one driver getting too many stops"""
        if len(clusters) != target_count:
            return clusters
            
        # Calculate total stops and target size per cluster
        total_stops = sum(len(cluster) for cluster in clusters)
        avg_size = total_stops / target_count
        max_size = math.ceil(avg_size * 1.5)  # Allow 50% variance
        
        # Move stops from oversized clusters to undersized ones
        balanced = True
        while balanced:
            balanced = False
            
            for i, cluster in enumerate(clusters):
                if len(cluster) > max_size:
                    # Find the smallest cluster
                    smallest_idx = min(range(len(clusters)), key=lambda x: len(clusters[x]))
                    if len(clusters[smallest_idx]) < avg_size and smallest_idx != i:
                        # Move one stop from oversized to undersized cluster
                        stop_to_move = cluster.pop()
                        clusters[smallest_idx].append(stop_to_move)
                        balanced = True
                        logging.debug(f"Moved stop between clusters for balance")
                        break
        
        return clusters
    
    def calculate_route_workload_time(self, stop_indices: List[int], stops: List[Dict], departure_address: str = "183 DeKalb Industrial Way, Decatur, GA 30030") -> int:
        """Calculate total workload time in minutes for a route including service and drive time"""
        if not stop_indices:
            return 0
        
        # Time estimates
        service_time_per_stop = 60  # 60 minutes per stop for installations/removals
        drive_time_between_stops = 20  # 20 minutes average between stops
        drive_time_to_first = 25  # 25 minutes from departure to first stop
        drive_time_back = 25  # 25 minutes back to departure
        
        total_time = 0
        
        # Service time for all stops
        total_time += len(stop_indices) * service_time_per_stop
        
        # Drive time from departure to first stop
        total_time += drive_time_to_first
        
        # Drive time between stops
        if len(stop_indices) > 1:
            total_time += (len(stop_indices) - 1) * drive_time_between_stops
        
        # Drive time back to departure
        total_time += drive_time_back
        
        return total_time

    def balance_workload_for_8_hours(self, stop_distribution: List[List[int]], stops: List[Dict], target_minutes: int = 480) -> List[List[int]]:
        """Balance workload distribution to target 8-hour (480 minute) workdays"""
        if not stop_distribution:
            return stop_distribution
        
        # Calculate current workloads
        workloads = []
        for i, route_indices in enumerate(stop_distribution):
            workload_time = self.calculate_route_workload_time(route_indices, stops)
            workloads.append({
                'driver_index': i,
                'route_indices': route_indices.copy(),
                'workload_minutes': workload_time
            })
            logging.info(f"Driver {i+1} initial workload: {workload_time} minutes ({workload_time/60:.1f} hours)")
        
        # Balance workloads by moving stops from overloaded to underloaded drivers
        max_iterations = 20
        for iteration in range(max_iterations):
            # Find most overloaded and most underloaded drivers
            overloaded = max(workloads, key=lambda x: x['workload_minutes'])
            underloaded = min(workloads, key=lambda x: x['workload_minutes'])
            
            # If difference is small or overloaded is close to target, we're done
            workload_diff = overloaded['workload_minutes'] - underloaded['workload_minutes']
            if workload_diff < 60 or overloaded['workload_minutes'] <= target_minutes + 60:
                break
            
            # Move one stop from overloaded to underloaded
            if overloaded['route_indices']:
                stop_to_move = overloaded['route_indices'].pop()
                underloaded['route_indices'].append(stop_to_move)
                
                # Recalculate workloads
                overloaded['workload_minutes'] = self.calculate_route_workload_time(overloaded['route_indices'], stops)
                underloaded['workload_minutes'] = self.calculate_route_workload_time(underloaded['route_indices'], stops)
                
                logging.debug(f"Iteration {iteration+1}: Moved stop from driver {overloaded['driver_index']+1} to driver {underloaded['driver_index']+1}")
        
        # Extract balanced routes and log final workloads
        balanced_distribution = []
        for workload in sorted(workloads, key=lambda x: x['driver_index']):
            balanced_distribution.append(workload['route_indices'])
            hours = workload['workload_minutes'] / 60
            logging.info(f"Driver {workload['driver_index']+1} final workload: {workload['workload_minutes']} minutes ({hours:.1f} hours)")
        
        return balanced_distribution

    def get_optimized_stop_distribution(self, stops: List[Dict], num_drivers: int) -> List[List[int]]:
        """
        Get stop distribution optimized for 8-hour workdays and geographic proximity
        
        Args:
            stops: List of stop dictionaries
            num_drivers: Number of drivers
            
        Returns:
            List of lists containing stop indices for each driver
        """
        try:
            # Start with geographic clustering for efficiency
            clusters = self.cluster_stops_by_proximity(stops, num_drivers)
            
            # Convert clusters to stop indices
            stop_distribution = []
            for cluster in clusters:
                indices = []
                for stop in cluster:
                    # Find the index of this stop in the original list
                    for i, original_stop in enumerate(stops):
                        if original_stop['id'] == stop['id']:
                            indices.append(i)
                            break
                stop_distribution.append(indices)
            
            # Balance workloads for 8-hour target
            logging.info("Balancing workloads for 8-hour target...")
            balanced_distribution = self.balance_workload_for_8_hours(stop_distribution, stops)
            
            # Log final cluster information
            for i, cluster_indices in enumerate(balanced_distribution):
                cluster_stops = [stops[idx]['address'] for idx in cluster_indices]
                workload_time = self.calculate_route_workload_time(cluster_indices, stops)
                logging.info(f"Driver {i+1} final route: {len(cluster_indices)} stops, {workload_time} minutes ({workload_time/60:.1f} hours)")
                for addr in cluster_stops[:3]:  # Show first 3 addresses
                    logging.debug(f"  - {addr}")
                if len(cluster_stops) > 3:
                    logging.debug(f"  ... and {len(cluster_stops)-3} more")
            
            return balanced_distribution
            
        except Exception as e:
            logging.error(f"Optimized distribution failed: {e}, falling back to simple distribution")
            # Fallback to simple distribution
            stops_per_driver = len(stops) // num_drivers
            remainder = len(stops) % num_drivers
            
            distribution = []
            current_index = 0
            
            for driver in range(num_drivers):
                driver_stops = stops_per_driver + (1 if driver < remainder else 0)
                if driver_stops > 0:
                    indices = list(range(current_index, current_index + driver_stops))
                    distribution.append(indices)
                    current_index += driver_stops
                else:
                    distribution.append([])
            
            return distribution