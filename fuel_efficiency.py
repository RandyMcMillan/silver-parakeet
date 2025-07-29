"""
Fuel efficiency calculations for 2004-2006 Toyota Tundra
Integrates with traffic-aware routing for cost optimization
"""

import logging
from typing import Dict, List, Tuple

class TundraFuelCalculator:
    """
    Fuel efficiency and cost calculator for 2004-2006 Toyota Tundra
    Considers traffic conditions, route distance, and current gas prices
    """
    
    def __init__(self):
        # 2004-2006 Toyota Tundra fuel efficiency (EPA estimates and real-world data)
        self.city_mpg = 15.0      # City driving MPG
        self.highway_mpg = 18.0   # Highway driving MPG
        self.combined_mpg = 16.0  # Combined MPG
        
        # Current gas prices (updated from EIA data July 2025)
        self.gas_price_per_gallon = 3.14  # US national average $3.14/gallon (July 2025)
        
        # Traffic impact on fuel efficiency
        self.traffic_multipliers = {
            'heavy_traffic': 0.75,    # 25% worse fuel economy in heavy traffic
            'moderate_traffic': 0.85, # 15% worse fuel economy in moderate traffic
            'light_traffic': 0.95,    # 5% worse fuel economy in light traffic
            'free_flow': 1.0          # Normal fuel economy
        }
        
        # Route type fuel efficiency adjustments
        self.route_type_mpg = {
            'city': self.city_mpg,
            'highway': self.highway_mpg,
            'mixed': self.combined_mpg
        }
    
    def calculate_fuel_cost(self, distance_miles: float, traffic_condition: str = 'moderate_traffic', 
                           route_type: str = 'mixed') -> Dict[str, float]:
        """
        Calculate fuel cost for a given route considering traffic and route type
        
        Args:
            distance_miles: Total distance in miles
            traffic_condition: Traffic level (heavy_traffic, moderate_traffic, light_traffic, free_flow)
            route_type: Type of route (city, highway, mixed)
        
        Returns:
            Dictionary with fuel consumption and cost details
        """
        try:
            # Get base MPG for route type
            base_mpg = self.route_type_mpg.get(route_type, self.combined_mpg)
            
            # Apply traffic multiplier
            traffic_multiplier = self.traffic_multipliers.get(traffic_condition, 0.85)
            effective_mpg = base_mpg * traffic_multiplier
            
            # Calculate fuel consumption
            gallons_used = distance_miles / effective_mpg
            fuel_cost = gallons_used * self.gas_price_per_gallon
            
            return {
                'distance_miles': distance_miles,
                'base_mpg': base_mpg,
                'effective_mpg': effective_mpg,
                'traffic_condition': traffic_condition,
                'route_type': route_type,
                'gallons_used': gallons_used,
                'fuel_cost': fuel_cost,
                'cost_per_mile': fuel_cost / distance_miles if distance_miles > 0 else 0
            }
            
        except Exception as e:
            logging.error(f"Fuel cost calculation error: {e}")
            return {
                'distance_miles': distance_miles,
                'fuel_cost': distance_miles * 0.20,  # Fallback estimate
                'error': str(e)
            }
    
    def get_traffic_condition_from_time(self, hour: int, is_weekend: bool = False) -> str:
        """
        Determine traffic condition based on time of day
        
        Args:
            hour: Hour of day (0-23)
            is_weekend: Whether it's weekend
        
        Returns:
            Traffic condition string
        """
        if is_weekend:
            if 10 <= hour <= 16:
                return 'moderate_traffic'
            else:
                return 'light_traffic'
        else:
            # Weekday traffic patterns
            if 7 <= hour <= 10 or 16 <= hour <= 19:  # Rush hours
                return 'heavy_traffic'
            elif 10 <= hour <= 16:  # Midday
                return 'moderate_traffic'
            else:  # Early morning, late evening
                return 'light_traffic'
    
    def calculate_route_fuel_efficiency(self, stops: List[Dict], departure_address: str, 
                                      start_time_hour: int) -> Dict[str, float]:
        """
        Calculate total fuel cost for an entire route with multiple stops
        
        Args:
            stops: List of stop dictionaries with addresses
            departure_address: Starting address
            start_time_hour: Starting hour (0-23)
        
        Returns:
            Dictionary with total fuel cost and efficiency metrics
        """
        try:
            total_distance = 0
            total_fuel_cost = 0
            segments = []
            
            # Estimate distances between stops (this would integrate with Google Maps in practice)
            current_hour = start_time_hour
            
            # Distance from departure to first stop
            if stops:
                segment_distance = self._estimate_distance(departure_address, stops[0]['address'])
                traffic_condition = self.get_traffic_condition_from_time(current_hour)
                
                fuel_data = self.calculate_fuel_cost(segment_distance, traffic_condition, 'mixed')
                total_distance += segment_distance
                total_fuel_cost += fuel_data['fuel_cost']
                segments.append({
                    'from': 'Departure',
                    'to': stops[0]['address'],
                    'distance': segment_distance,
                    'fuel_cost': fuel_data['fuel_cost'],
                    'traffic_condition': traffic_condition
                })
                
                current_hour += 1  # Assume 1 hour per stop including service time
            
            # Distance between stops
            for i in range(len(stops) - 1):
                segment_distance = self._estimate_distance(stops[i]['address'], stops[i + 1]['address'])
                traffic_condition = self.get_traffic_condition_from_time(current_hour)
                
                fuel_data = self.calculate_fuel_cost(segment_distance, traffic_condition, 'mixed')
                total_distance += segment_distance
                total_fuel_cost += fuel_data['fuel_cost']
                segments.append({
                    'from': stops[i]['address'],
                    'to': stops[i + 1]['address'],
                    'distance': segment_distance,
                    'fuel_cost': fuel_data['fuel_cost'],
                    'traffic_condition': traffic_condition
                })
                
                current_hour += 1
            
            # Distance from last stop back to departure
            if stops:
                segment_distance = self._estimate_distance(stops[-1]['address'], departure_address)
                traffic_condition = self.get_traffic_condition_from_time(current_hour)
                
                fuel_data = self.calculate_fuel_cost(segment_distance, traffic_condition, 'mixed')
                total_distance += segment_distance
                total_fuel_cost += fuel_data['fuel_cost']
                segments.append({
                    'from': stops[-1]['address'],
                    'to': 'Departure',
                    'distance': segment_distance,
                    'fuel_cost': fuel_data['fuel_cost'],
                    'traffic_condition': traffic_condition
                })
            
            return {
                'total_distance_miles': total_distance,
                'total_fuel_cost': total_fuel_cost,
                'cost_per_mile': total_fuel_cost / total_distance if total_distance > 0 else 0,
                'estimated_mpg': total_distance / (total_fuel_cost / self.gas_price_per_gallon) if total_fuel_cost > 0 else 0,
                'segments': segments,
                'vehicle': '2004-2006 Toyota Tundra'
            }
            
        except Exception as e:
            logging.error(f"Route fuel efficiency calculation error: {e}")
            return {
                'total_fuel_cost': 0,
                'error': str(e)
            }
    
    def _estimate_distance(self, address1: str, address2: str) -> float:
        """
        Estimate distance between two addresses (placeholder for Google Maps integration)
        
        Args:
            address1: Starting address
            address2: Ending address
        
        Returns:
            Estimated distance in miles
        """
        # This is a simple estimate - in practice would use Google Maps Distance Matrix API
        # For Atlanta metro area, average distance between service stops
        if 'DeKalb Industrial' in address1 or 'DeKalb Industrial' in address2:
            return 15.0  # Average distance from depot to service area
        else:
            return 8.0   # Average distance between service stops
    
    def get_fuel_efficiency_recommendations(self, routes: List[Dict]) -> List[Dict]:
        """
        Analyze routes and provide fuel efficiency recommendations
        
        Args:
            routes: List of route dictionaries
        
        Returns:
            List of recommendations for fuel optimization
        """
        recommendations = []
        
        for i, route in enumerate(routes, 1):
            fuel_data = self.calculate_route_fuel_efficiency(
                route.get('stops', []), 
                route.get('departure_address', ''),
                route.get('start_hour', 7)
            )
            
            # Generate recommendations based on fuel cost
            if fuel_data['total_fuel_cost'] > 50:  # High fuel cost threshold
                recommendations.append({
                    'driver': i,
                    'issue': 'High fuel cost',
                    'cost': fuel_data['total_fuel_cost'],
                    'recommendation': 'Consider consolidating stops or adjusting start time to avoid rush hour'
                })
            
            if fuel_data.get('estimated_mpg', 0) < 14:  # Below expected efficiency
                recommendations.append({
                    'driver': i,
                    'issue': 'Low fuel efficiency',
                    'mpg': fuel_data.get('estimated_mpg', 0),
                    'recommendation': 'Route involves heavy traffic - consider alternative timing or route optimization'
                })
        
        return recommendations