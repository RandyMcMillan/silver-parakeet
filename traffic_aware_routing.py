import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import math

class TrafficAwareRouter:
    """
    Advanced routing system that considers traffic patterns to optimize driver assignments
    and route timing to avoid high traffic areas during peak hours.
    """
    
    def __init__(self):
        # Define high traffic zones in Atlanta metro area
        self.high_traffic_zones = {
            'downtown_atlanta': {
                'center': (33.7490, -84.3880),
                'radius_miles': 5,
                'peak_hours': [(7, 10), (16, 19)],  # 7-10am, 4-7pm
                'traffic_multiplier': 2.5
            },
            'buckhead': {
                'center': (33.8484, -84.3781),
                'radius_miles': 3,
                'peak_hours': [(7, 10), (16, 19)],
                'traffic_multiplier': 2.0
            },
            'midtown': {
                'center': (33.7838, -84.3831),
                'radius_miles': 2,
                'peak_hours': [(7, 10), (16, 19)],
                'traffic_multiplier': 1.8
            },
            'perimeter_center': {
                'center': (33.9157, -84.3446),
                'radius_miles': 2,
                'peak_hours': [(7, 10), (16, 19)],
                'traffic_multiplier': 1.7
            }
        }
        
        # Time-based traffic patterns
        self.traffic_patterns = {
            'early_morning': {'hours': (5, 7), 'multiplier': 0.8},   # Light traffic
            'morning_rush': {'hours': (7, 10), 'multiplier': 2.2},   # Heavy traffic
            'midday': {'hours': (10, 15), 'multiplier': 1.0},        # Normal traffic
            'afternoon_rush': {'hours': (15, 19), 'multiplier': 2.0}, # Heavy traffic
            'evening': {'hours': (19, 22), 'multiplier': 1.2},       # Moderate traffic
            'night': {'hours': (22, 5), 'multiplier': 0.7}           # Light traffic
        }
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in miles"""
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 3959 * c  # Earth radius in miles
    
    def is_in_high_traffic_zone(self, coords: Tuple[float, float], time_hour: int) -> Dict:
        """Check if coordinates are in a high traffic zone during peak hours"""
        traffic_info = {'in_zone': False, 'zone_name': None, 'multiplier': 1.0}
        
        for zone_name, zone_data in self.high_traffic_zones.items():
            distance = self.calculate_distance(coords, zone_data['center'])
            
            if distance <= zone_data['radius_miles']:
                # Check if current time is during peak hours for this zone
                for start_hour, end_hour in zone_data['peak_hours']:
                    if start_hour <= time_hour < end_hour:
                        traffic_info = {
                            'in_zone': True,
                            'zone_name': zone_name,
                            'multiplier': zone_data['traffic_multiplier']
                        }
                        break
                break
        
        return traffic_info
    
    def get_traffic_multiplier_for_time(self, time_hour: int) -> float:
        """Get traffic multiplier based on time of day"""
        for pattern_name, pattern_data in self.traffic_patterns.items():
            start_hour, end_hour = pattern_data['hours']
            
            # Handle overnight pattern (22-5)
            if start_hour > end_hour:
                if time_hour >= start_hour or time_hour < end_hour:
                    return pattern_data['multiplier']
            else:
                if start_hour <= time_hour < end_hour:
                    return pattern_data['multiplier']
        
        return 1.0  # Default multiplier
    
    def optimize_route_timing(self, stops: List[Dict], start_time: int = 7) -> Dict:
        """
        Optimize route timing to minimize time spent in high traffic areas
        
        Args:
            stops: List of stop dictionaries with coordinates
            start_time: Preferred start time (24-hour format)
            
        Returns:
            Dictionary with optimized timing strategy
        """
        optimization_strategies = []
        
        # Strategy 1: Early Start (before rush hour)
        early_start_time = 6
        early_strategy = self._evaluate_timing_strategy(stops, early_start_time, "Early Start")
        optimization_strategies.append(early_strategy)
        
        # Strategy 2: Late Start (after morning rush)
        late_start_time = 10
        late_strategy = self._evaluate_timing_strategy(stops, late_start_time, "Late Start")
        optimization_strategies.append(late_strategy)
        
        # Strategy 3: Split Shift (morning suburban, afternoon city)
        split_strategy = self._evaluate_split_shift_strategy(stops)
        optimization_strategies.append(split_strategy)
        
        # Choose best strategy
        best_strategy = min(optimization_strategies, key=lambda s: s['total_traffic_impact'])
        
        return best_strategy
    
    def _evaluate_timing_strategy(self, stops: List[Dict], start_time: int, strategy_name: str) -> Dict:
        """Evaluate a specific timing strategy"""
        total_traffic_impact = 0
        current_time = start_time
        service_time_per_stop = 1  # 1 hour per stop
        
        for stop in stops:
            # Get coordinates (use fallback if not available)
            coords = stop.get('coordinates', (33.7490, -84.3880))
            
            # Check traffic impact at current time
            traffic_info = self.is_in_high_traffic_zone(coords, current_time)
            time_multiplier = self.get_traffic_multiplier_for_time(current_time)
            
            # Calculate combined traffic impact
            zone_impact = traffic_info['multiplier'] if traffic_info['in_zone'] else 1.0
            combined_impact = zone_impact * time_multiplier
            total_traffic_impact += combined_impact
            
            # Advance time for next stop
            current_time += service_time_per_stop
            if current_time >= 24:
                current_time -= 24
        
        return {
            'strategy_name': strategy_name,
            'start_time': start_time,
            'total_traffic_impact': total_traffic_impact,
            'avg_traffic_impact': total_traffic_impact / len(stops) if stops else 0,
            'recommendations': self._generate_recommendations(strategy_name, start_time)
        }
    
    def _evaluate_split_shift_strategy(self, stops: List[Dict]) -> Dict:
        """Evaluate split shift strategy: suburban stops early, city stops later"""
        suburban_stops = []
        city_stops = []
        
        for stop in stops:
            coords = stop.get('coordinates', (33.7490, -84.3880))
            # Check if stop is in high traffic zone
            in_city = any(
                self.calculate_distance(coords, zone['center']) <= zone['radius_miles']
                for zone in self.high_traffic_zones.values()
            )
            
            if in_city:
                city_stops.append(stop)
            else:
                suburban_stops.append(stop)
        
        # Suburban stops: 6 AM start
        suburban_impact = sum(
            self.get_traffic_multiplier_for_time(6 + i) 
            for i in range(len(suburban_stops))
        ) if suburban_stops else 0
        
        # City stops: 10 AM start (after morning rush)
        city_impact = sum(
            self.get_traffic_multiplier_for_time(10 + i) * 1.2  # Slight penalty for city
            for i in range(len(city_stops))
        ) if city_stops else 0
        
        total_impact = suburban_impact + city_impact
        
        return {
            'strategy_name': 'Split Shift',
            'start_time': 6,
            'total_traffic_impact': total_impact,
            'avg_traffic_impact': total_impact / len(stops) if stops else 0,
            'suburban_stops': len(suburban_stops),
            'city_stops': len(city_stops),
            'recommendations': [
                f"Start suburban routes at 6:00 AM ({len(suburban_stops)} stops)",
                f"Start city routes at 10:00 AM ({len(city_stops)} stops)",
                "Avoid downtown Atlanta during 7-10 AM and 4-7 PM",
                "Complete city stops before afternoon rush hour"
            ]
        }
    
    def _generate_recommendations(self, strategy_name: str, start_time: int) -> List[str]:
        """Generate specific recommendations for a strategy"""
        recommendations = []
        
        if strategy_name == "Early Start":
            recommendations = [
                f"Start routes at {start_time}:00 AM to avoid morning rush hour",
                "Complete high traffic area stops before 7:00 AM",
                "Finish suburban stops by early afternoon",
                "Drivers can avoid afternoon rush by ending early"
            ]
        elif strategy_name == "Late Start":
            recommendations = [
                f"Start routes at {start_time}:00 AM after morning rush subsides",
                "Focus on city stops during midday low traffic period",
                "Plan to finish before 3:00 PM to avoid afternoon rush",
                "May require overtime if all stops can't be completed"
            ]
        
        return recommendations
    
    def get_geographic_route_optimization(self, stops: List[Dict], num_drivers: int) -> Dict:
        """
        Optimize routes geographically while considering traffic patterns
        """
        # Categorize stops by traffic zones
        zone_analysis = self._analyze_stops_by_zones(stops)
        
        # Generate route assignments that minimize traffic exposure
        optimized_assignments = self._create_traffic_aware_assignments(stops, num_drivers)
        
        # Get timing recommendations
        timing_optimization = self.optimize_route_timing(stops)
        
        return {
            'zone_analysis': zone_analysis,
            'route_assignments': optimized_assignments,
            'timing_strategy': timing_optimization,
            'traffic_avoidance_tips': self._get_traffic_avoidance_tips()
        }
    
    def _analyze_stops_by_zones(self, stops: List[Dict]) -> Dict:
        """Analyze stop distribution across traffic zones"""
        zone_counts = {zone: 0 for zone in self.high_traffic_zones.keys()}
        zone_counts['suburban'] = 0
        
        for stop in stops:
            coords = stop.get('coordinates', (33.7490, -84.3880))
            assigned_to_zone = False
            
            for zone_name, zone_data in self.high_traffic_zones.items():
                distance = self.calculate_distance(coords, zone_data['center'])
                if distance <= zone_data['radius_miles']:
                    zone_counts[zone_name] += 1
                    assigned_to_zone = True
                    break
            
            if not assigned_to_zone:
                zone_counts['suburban'] += 1
        
        return zone_counts
    
    def _create_traffic_aware_assignments(self, stops: List[Dict], num_drivers: int) -> List[Dict]:
        """Create driver assignments that minimize traffic exposure"""
        assignments = []
        
        for driver_num in range(1, num_drivers + 1):
            # Simple round-robin assignment for now
            # In practice, this would use more sophisticated clustering
            driver_stops = stops[driver_num-1::num_drivers]
            
            assignments.append({
                'driver_number': driver_num,
                'stop_count': len(driver_stops),
                'recommended_start_time': '06:00' if driver_num % 2 == 1 else '10:00',
                'strategy': 'Early Start' if driver_num % 2 == 1 else 'Late Start'
            })
        
        return assignments
    
    def _get_traffic_avoidance_tips(self) -> List[str]:
        """Get general traffic avoidance tips"""
        return [
            "Avoid I-285 (Perimeter) during 7-10 AM and 4-7 PM",
            "Use surface streets in Buckhead during rush hours",
            "Complete downtown stops before 7 AM or after 10 AM",
            "Plan lunch breaks during 11 AM - 2 PM low traffic window",
            "Consider GA-400 alternatives during peak hours",
            "Use real-time traffic apps for dynamic routing adjustments"
        ]