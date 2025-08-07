import logging
import math
from typing import List, Dict, Tuple
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
from traffic_aware_routing import TrafficAwareRouter

class GeographicClusterer:
    """Clusters stops by geographic proximity for efficient route assignment"""
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="route_optimizer")
        self.geocache = {}  # Cache coordinates to avoid repeated API calls
        self.traffic_router = TrafficAwareRouter()  # Traffic-aware routing system
        
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
            # Simple distance calculation to avoid geopy library issues
            lat_diff = coords1[0] - coords2[0]
            lon_diff = coords1[1] - coords2[1]
            # Approximate distance using simple formula (1 degree ≈ 69 miles)
            distance = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 69
            return max(distance, 0.1)  # Minimum distance
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
        """
        Balance workloads to target 8-hour minimum shifts while minimizing overtime
        
        Args:
            stop_distribution: Initial distribution of stop indices per driver
            stops: List of stop dictionaries
            target_minutes: 8-hour minimum (480 minutes) per shift
            
        Returns:
            Balanced distribution targeting 8-hour minimum shifts with minimal overtime
        """
        if not stop_distribution:
            return stop_distribution
        
        max_minutes = 600  # 10 hours maximum (allow more overtime to ensure 8-hour minimums)
        
        # Calculate current workloads
        workloads = []
        for i, route_indices in enumerate(stop_distribution):
            workload_time = self.calculate_route_workload_time(route_indices, stops)
            workloads.append({
                'driver_index': i,
                'route_indices': route_indices.copy(),
                'workload_minutes': workload_time,
                'overtime_minutes': max(0, workload_time - target_minutes),
                'undertime_minutes': max(0, target_minutes - workload_time)
            })
            logging.info(f"Driver {i+1} initial workload: {workload_time} minutes ({workload_time/60:.1f} hours)")
        
        # Sort by priority: minimize overtime first, then maximize utilization
        workloads.sort(key=lambda x: (x['overtime_minutes'], -x['workload_minutes']))
        
        # Rebalance to minimize overtime and meet 8-hour minimum
        max_iterations = 30
        for iteration in range(max_iterations):
            improved = False
            
            # Find drivers with overtime and drivers with undertime
            overtime_drivers = [w for w in workloads if w['workload_minutes'] > target_minutes]
            undertime_drivers = [w for w in workloads if w['workload_minutes'] < target_minutes]
            
            # Priority 1: Move stops to drivers under 8 hours (even if it creates overtime)
            for under_driver in undertime_drivers:
                if under_driver['workload_minutes'] < target_minutes:
                    # Find any driver with extra stops who can spare one
                    for donor_driver in [w for w in workloads if len(w['route_indices']) > 1]:
                        if donor_driver != under_driver and donor_driver['route_indices']:
                            # Try moving one stop to get undertime driver closer to 8 hours
                            stop_time = 75  # Service time + average drive time estimate
                            
                            new_under_workload = under_driver['workload_minutes'] + stop_time
                            new_donor_workload = donor_driver['workload_minutes'] - stop_time
                            
                            # Target exactly 8 hours as ideal, allow minimal overage if needed
                            gets_to_minimum = new_under_workload >= target_minutes  # Must reach 8h minimum
                            reasonable_overage = new_under_workload <= target_minutes + 90  # Minimal overage allowed
                            donor_keeps_viable = new_donor_workload >= target_minutes - 90  # Donor doesn't go too low
                            stays_within_max = new_under_workload <= max_minutes
                            
                            # Move stop if it gets driver to 8h+ with minimal overage
                            if gets_to_minimum and reasonable_overage and donor_keeps_viable and stays_within_max:
                                # Perform the move
                                stop_to_move = donor_driver['route_indices'].pop()
                                under_driver['route_indices'].append(stop_to_move)
                                
                                # Update workloads with actual calculations
                                under_driver['workload_minutes'] = self.calculate_route_workload_time(under_driver['route_indices'], stops)
                                donor_driver['workload_minutes'] = self.calculate_route_workload_time(donor_driver['route_indices'], stops)
                                under_driver['overtime_minutes'] = max(0, under_driver['workload_minutes'] - target_minutes)
                                donor_driver['overtime_minutes'] = max(0, donor_driver['workload_minutes'] - target_minutes)
                                under_driver['undertime_minutes'] = max(0, target_minutes - under_driver['workload_minutes'])
                                donor_driver['undertime_minutes'] = max(0, target_minutes - donor_driver['workload_minutes'])
                                
                                improved = True
                                logging.info(f"Iteration {iteration+1}: Moved stop from driver {donor_driver['driver_index']+1} to driver {under_driver['driver_index']+1} (ensuring 8h minimum)")
                                break
                
                if improved:
                    break
                
                if improved:
                    break
            
            if not improved:
                break
        
        # Priority 2: CRITICAL - Ensure ALL drivers reach 8-hour minimum before worrying about overtime
        still_undertime_drivers = [w for w in workloads if w['workload_minutes'] < target_minutes]
        
        # Multi-round redistribution to ensure 8-hour minimum for ALL drivers
        for redistribution_round in range(3):  # Up to 3 rounds of aggressive redistribution
            still_undertime_drivers = [w for w in workloads if w['workload_minutes'] < target_minutes]
            
            if not still_undertime_drivers:
                break  # All drivers now meet minimum
                
            logging.info(f"Redistribution round {redistribution_round + 1}: {len(still_undertime_drivers)} drivers still under 8h minimum")
            
            for under_driver in still_undertime_drivers:
                needed_minutes = target_minutes - under_driver['workload_minutes']
                logging.info(f"Driver {under_driver['driver_index']+1} needs {needed_minutes} more minutes to reach 8h minimum")
                
                # Find donors with multiple stops, prioritizing those with most overtime
                donor_candidates = [w for w in workloads if len(w['route_indices']) > 1 and w != under_driver]
                donor_candidates.sort(key=lambda x: x['workload_minutes'], reverse=True)  # Most overtime first
                
                stops_moved = 0
                for donor_driver in donor_candidates:
                    if under_driver['workload_minutes'] >= target_minutes:
                        break  # Driver reached minimum
                        
                    if donor_driver['route_indices'] and len(donor_driver['route_indices']) > 1:
                        # Move stop to get driver closer to 8h minimum
                        stop_to_move = donor_driver['route_indices'].pop()
                        under_driver['route_indices'].append(stop_to_move)
                        stops_moved += 1
                        
                        # Recalculate workloads
                        donor_driver['workload_minutes'] = self.calculate_route_workload_time(donor_driver['route_indices'], stops)
                        under_driver['workload_minutes'] = self.calculate_route_workload_time(under_driver['route_indices'], stops)
                        
                        logging.info(f"Moved stop #{stops_moved} from driver {donor_driver['driver_index']+1} ({donor_driver['workload_minutes']}min) to driver {under_driver['driver_index']+1} ({under_driver['workload_minutes']}min)")
                        
                        # Continue moving stops until driver reaches minimum
                        if under_driver['workload_minutes'] >= target_minutes:
                            logging.info(f"✓ Driver {under_driver['driver_index']+1} now meets 8h minimum!")
                            break
        
        # Priority 3: Only reduce excessive overtime if all drivers have 8h minimum
        all_drivers_meet_minimum = all(w['workload_minutes'] >= target_minutes for w in workloads)
        
        if all_drivers_meet_minimum:
            excessive_overtime_drivers = [w for w in workloads if w['workload_minutes'] > target_minutes + 150]  # More than 2.5 hours overtime
            very_undertime_drivers = []  # No one should be undertime at this point
        else:
            excessive_overtime_drivers = []
            very_undertime_drivers = []
            
        for excessive_driver in excessive_overtime_drivers:
            # Only move stops if there are drivers who can take them without going under minimum
            potential_receivers = [w for w in workloads if w['workload_minutes'] < target_minutes + 60]
            
            for receiver_driver in potential_receivers:
                if excessive_driver['route_indices'] and len(excessive_driver['route_indices']) > 1:
                    # Move a stop from excessive overtime to receiver driver
                    stop_to_move = excessive_driver['route_indices'].pop()
                    receiver_driver['route_indices'].append(stop_to_move)
                    
                    # Recalculate workloads
                    excessive_driver['workload_minutes'] = self.calculate_route_workload_time(excessive_driver['route_indices'], stops)
                    receiver_driver['workload_minutes'] = self.calculate_route_workload_time(receiver_driver['route_indices'], stops)
                    
                    # Keep the move if it helps reduce overtime without going under minimum
                    if (excessive_driver['workload_minutes'] >= target_minutes and 
                        receiver_driver['workload_minutes'] <= max_minutes):
                        logging.info(f"Reduced excessive overtime for driver {excessive_driver['driver_index']+1}")
                        break
                    else:
                        # Revert if move doesn't help
                        receiver_driver['route_indices'].pop()
                        excessive_driver['route_indices'].append(stop_to_move)
                        excessive_driver['workload_minutes'] = self.calculate_route_workload_time(excessive_driver['route_indices'], stops)
                        receiver_driver['workload_minutes'] = self.calculate_route_workload_time(receiver_driver['route_indices'], stops)
        
        # Extract balanced routes and calculate final totals
        balanced_distribution = []
        total_overtime = 0
        total_undertime = 0
        
        for workload in sorted(workloads, key=lambda x: x['driver_index']):
            balanced_distribution.append(workload['route_indices'])
            
            # Recalculate final workload for accurate reporting
            final_workload = self.calculate_route_workload_time(workload['route_indices'], stops)
            hours = final_workload / 60
            
            overtime = max(0, final_workload - target_minutes)
            undertime = max(0, target_minutes - final_workload)
            
            total_overtime += overtime
            total_undertime += undertime
            
            status = ""
            if final_workload < target_minutes:
                under_hours = undertime / 60
                status = f" (UNDER MINIMUM: -{under_hours:.1f}h short of 8h target - needs more work)"
            elif final_workload <= target_minutes + 30:  # Within 30 minutes of 8h
                over_hours = overtime / 60
                status = f" (IDEAL: 8h minimum + {over_hours:.1f}h as demand allows)"
            elif final_workload <= target_minutes + 90:  # 1-1.5 hours over
                over_hours = overtime / 60
                status = f" (GOOD: 8h minimum + {over_hours:.1f}h based on workload)"
            else:  # More than 1.5 hours overtime
                over_hours = overtime / 60
                status = f" (HIGH: 8h minimum + {over_hours:.1f}h overtime)"
            
            logging.info(f"Driver {workload['driver_index']+1}: {final_workload} minutes ({hours:.1f} hours){status}")
        
        logging.info(f"Total overtime: {total_overtime/60:.1f} hours, Total undertime: {total_undertime/60:.1f} hours")
        
        return balanced_distribution

    def get_optimized_stop_distribution(self, stops: List[Dict], num_drivers: int) -> List[List[int]]:
        """
        Get stop distribution optimized for 8-hour workdays, geographic proximity, and traffic avoidance
        
        Args:
            stops: List of stop dictionaries
            num_drivers: Number of drivers
            
        Returns:
            List of lists containing stop indices for each driver
        """
        try:
            # Add coordinates to stops for traffic analysis
            stops_with_coords = []
            for stop in stops:
                coords = self.get_coordinates(stop['address'])
                stop_with_coords = stop.copy()
                stop_with_coords['coordinates'] = coords
                stops_with_coords.append(stop_with_coords)
            
            # Get traffic-aware routing analysis
            traffic_analysis = self.traffic_router.get_geographic_route_optimization(stops_with_coords, num_drivers)
            logging.info(f"Traffic zone analysis: {traffic_analysis['zone_analysis']}")
            logging.info(f"Recommended timing strategy: {traffic_analysis['timing_strategy']['strategy_name']}")
            
            # Start with geographic clustering for efficiency
            clusters = self.cluster_stops_by_proximity(stops_with_coords, num_drivers)
            
            # Apply traffic-aware optimization to clusters
            optimized_clusters = self._apply_traffic_optimization(clusters, traffic_analysis)
            
            # Convert clusters to stop indices
            stop_distribution = []
            for cluster in optimized_clusters:
                indices = []
                for stop in cluster:
                    # Find the index of this stop in the original list
                    for i, original_stop in enumerate(stops):
                        if original_stop['id'] == stop['id']:
                            indices.append(i)
                            break
                stop_distribution.append(indices)
            
            # Balance workloads for 8-hour target
            logging.info("Balancing workloads for 8-hour target with traffic considerations...")
            balanced_distribution = self.balance_workload_for_8_hours(stop_distribution, stops)
            
            # Log final cluster information with traffic insights
            for i, cluster_indices in enumerate(balanced_distribution):
                cluster_stops = [stops[idx]['address'] for idx in cluster_indices]
                workload_time = self.calculate_route_workload_time(cluster_indices, stops)
                traffic_assignment = traffic_analysis['route_assignments'][i] if i < len(traffic_analysis['route_assignments']) else {}
                
                logging.info(f"Driver {i+1} final route: {len(cluster_indices)} stops, {workload_time} minutes ({workload_time/60:.1f} hours)")
                if traffic_assignment:
                    logging.info(f"  Recommended start: {traffic_assignment.get('recommended_start_time', '07:00')} ({traffic_assignment.get('strategy', 'Standard')})")
                
                for addr in cluster_stops[:3]:  # Show first 3 addresses
                    logging.debug(f"  - {addr}")
                if len(cluster_stops) > 3:
                    logging.debug(f"  ... and {len(cluster_stops)-3} more")
            
            # Log traffic avoidance recommendations
            for tip in traffic_analysis['traffic_avoidance_tips'][:3]:
                logging.info(f"Traffic tip: {tip}")
            
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
    
    def _apply_traffic_optimization(self, clusters: List[List[Dict]], traffic_analysis: Dict) -> List[List[Dict]]:
        """Apply traffic-aware optimizations to geographic clusters"""
        # For now, return clusters as-is but log traffic insights
        # Future enhancement: reorder stops within clusters based on traffic patterns
        
        zone_analysis = traffic_analysis['zone_analysis']
        timing_strategy = traffic_analysis['timing_strategy']
        
        logging.info(f"Traffic optimization applied:")
        logging.info(f"  - High traffic stops: {zone_analysis.get('downtown_atlanta', 0) + zone_analysis.get('buckhead', 0)}")
        logging.info(f"  - Suburban stops: {zone_analysis.get('suburban', 0)}")
        logging.info(f"  - Best timing strategy: {timing_strategy['strategy_name']} (impact: {timing_strategy['avg_traffic_impact']:.2f})")
        
        return clusters