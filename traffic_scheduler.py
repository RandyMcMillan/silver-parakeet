"""
Traffic Scheduler - Integration with Route Generation
Manages traffic data updates during route generation and provides construction alerts
"""

import logging
from datetime import datetime
from traffic_history_manager import traffic_history_manager
from models import db, TrafficSnapshot

logger = logging.getLogger(__name__)

class TrafficScheduler:
    """Manages traffic data collection and provides route-aware traffic estimates"""
    
    def __init__(self):
        self.departure_address = "183 DeKalb Industrial Way, Decatur, GA 30030"
    
    def update_route_traffic_data(self, stop_addresses: list) -> dict:
        """Update traffic snapshots for all route segments during route generation"""
        traffic_updates = {
            'updates_performed': 0,
            'construction_detected': [],
            'variance_alerts': [],
            'data_source': 'Historical with selective updates'
        }
        
        if not stop_addresses:
            return traffic_updates
        
        # Create all route segments (departure to first stop, between stops, last stop to departure)
        route_segments = []
        
        # Departure to first stop
        if stop_addresses:
            route_segments.append((self.departure_address, stop_addresses[0]))
        
        # Between consecutive stops
        for i in range(len(stop_addresses) - 1):
            route_segments.append((stop_addresses[i], stop_addresses[i + 1]))
        
        # Last stop back to departure
        if stop_addresses:
            route_segments.append((stop_addresses[-1], self.departure_address))
        
        # Update traffic data for each segment
        for origin, destination in route_segments:
            try:
                snapshot = traffic_history_manager.update_traffic_snapshot(origin, destination)
                
                if snapshot:
                    traffic_updates['updates_performed'] += 1
                    
                    # Check for construction alerts
                    if snapshot.construction_flag:
                        traffic_updates['construction_detected'].append({
                            'origin': origin,
                            'destination': destination,
                            'variance_minutes': snapshot.variance_score,
                            'morning_rush_time': snapshot.morning_rush_time,
                            'evening_rush_time': snapshot.evening_rush_time
                        })
                    
                    # Check for significant variance
                    elif snapshot.variance_score >= traffic_history_manager.SIGNIFICANT_VARIANCE_THRESHOLD:
                        traffic_updates['variance_alerts'].append({
                            'origin': origin,
                            'destination': destination,
                            'variance_minutes': snapshot.variance_score
                        })
                
            except Exception as e:
                logger.error(f"Error updating traffic data for {origin} to {destination}: {e}")
        
        return traffic_updates
    
    def get_route_travel_time(self, origin: str, destination: str, 
                             departure_time: datetime = None) -> float:
        """Get travel time estimate using historical traffic data"""
        try:
            return traffic_history_manager.get_traffic_estimate(origin, destination, departure_time)
        except Exception as e:
            logger.error(f"Error getting traffic estimate: {e}")
            return 15.0  # Fallback estimate
    
    def get_construction_alerts(self) -> list:
        """Get current construction alerts for the dashboard"""
        try:
            return traffic_history_manager.get_construction_alerts()
        except Exception as e:
            logger.error(f"Error getting construction alerts: {e}")
            return []
    
    def get_traffic_recommendations(self, route_stops: list) -> dict:
        """Get traffic recommendations for a specific route"""
        recommendations = {
            'optimal_start_time': '07:00',
            'avoid_times': [],
            'construction_warnings': [],
            'fuel_efficiency_tips': []
        }
        
        try:
            # Check for construction on route segments
            for i, stop in enumerate(route_stops):
                origin = self.departure_address if i == 0 else route_stops[i-1]['address']
                destination = stop['address']
                
                route_hash = traffic_history_manager.calculate_route_hash(origin, destination)
                snapshot = TrafficSnapshot.query.filter_by(route_hash=route_hash).first()
                
                if snapshot and snapshot.construction_flag:
                    recommendations['construction_warnings'].append({
                        'segment': f"{origin} to {destination}",
                        'variance_minutes': snapshot.variance_score,
                        'recommendation': 'Consider alternative timing or route'
                    })
            
            # Time recommendations based on traffic patterns
            if any(stop['address'] for stop in route_stops if 'atlanta' in stop['address'].lower()):
                recommendations['avoid_times'].extend(['07:30-09:30', '16:30-19:00'])
                recommendations['optimal_start_time'] = '06:00'  # Start early to avoid rush hour
                recommendations['fuel_efficiency_tips'].append(
                    'Start early (6 AM) to avoid Atlanta traffic - saves 20-25% fuel consumption'
                )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating traffic recommendations: {e}")
            return recommendations

# Global instance
traffic_scheduler = TrafficScheduler()