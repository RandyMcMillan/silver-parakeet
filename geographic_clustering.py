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
            
        try:
            # Use shorter timeout to prevent worker crashes
            location = self.geocoder.geocode(address, timeout=2)
            if location:
                coords = (location.latitude, location.longitude)
                self.geocache[address] = coords
                return coords
            else:
                logging.warning(f"Could not geocode address: {address}")
                fallback = self.get_area_fallback_coordinates(address)
                self.geocache[address] = fallback
                return fallback
        except Exception as e:
            logging.error(f"Geocoding error for {address}: {e}")
            fallback = self.get_area_fallback_coordinates(address)
            self.geocache[address] = fallback
            return fallback
    
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
    
    def get_optimized_stop_distribution(self, stops: List[Dict], num_drivers: int) -> List[List[int]]:
        """
        Get stop distribution optimized for geographic proximity
        
        Args:
            stops: List of stop dictionaries
            num_drivers: Number of drivers
            
        Returns:
            List of lists containing stop indices for each driver
        """
        try:
            # Cluster stops by proximity
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
            
            # Log cluster information
            for i, cluster_indices in enumerate(stop_distribution):
                cluster_stops = [stops[idx]['address'] for idx in cluster_indices]
                logging.info(f"Driver {i+1} cluster: {len(cluster_indices)} stops in proximity")
                for addr in cluster_stops:
                    logging.debug(f"  - {addr}")
            
            return stop_distribution
            
        except Exception as e:
            logging.error(f"Geographic clustering failed: {e}, falling back to simple distribution")
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