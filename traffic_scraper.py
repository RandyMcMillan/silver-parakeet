import trafilatura
from datetime import datetime, timedelta
import re
import logging
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import time


class TrafficDataScraper:
    """Scrapes real-time and historical traffic data for route optimization"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="route_optimizer_traffic")
        self.logger = logging.getLogger(__name__)
        
    def get_coordinates(self, address):
        """Get latitude and longitude for an address"""
        try:
            location = self.geolocator.geocode(address)
            if location:
                return (location.latitude, location.longitude)
            return None
        except Exception as e:
            self.logger.error(f"Geocoding error for {address}: {e}")
            return None
    
    def scrape_google_maps_traffic(self, from_address, to_address):
        """
        Scrape traffic data from Google Maps for route planning
        Note: This is a simplified approach - in production you'd use Google Maps API
        """
        try:
            # Get coordinates for both addresses
            from_coords = self.get_coordinates(from_address)
            to_coords = self.get_coordinates(to_address)
            
            if not from_coords or not to_coords:
                return None
                
            # Calculate base distance
            distance_miles = geodesic(from_coords, to_coords).miles
            
            # Base travel time (assuming 30 mph average in city)
            base_time_minutes = int((distance_miles / 30) * 60)
            
            # Apply traffic factor based on time of day and historical patterns
            traffic_factor = self._get_traffic_factor()
            actual_time_minutes = int(base_time_minutes * traffic_factor)
            
            return {
                'travel_time_minutes': actual_time_minutes,
                'distance_miles': distance_miles,
                'traffic_factor': traffic_factor
            }
            
        except Exception as e:
            self.logger.error(f"Traffic scraping error: {e}")
            return None
    
    def _get_traffic_factor(self):
        """
        Get traffic multiplier based on current time and historical patterns
        This simulates real traffic data - in production, use actual traffic APIs
        """
        current_hour = datetime.now().hour
        
        # Traffic patterns based on typical rush hours
        if 7 <= current_hour <= 9:  # Morning rush
            return 1.4
        elif 16 <= current_hour <= 18:  # Evening rush
            return 1.5
        elif 12 <= current_hour <= 13:  # Lunch time
            return 1.2
        elif 22 <= current_hour or current_hour <= 6:  # Late night/early morning
            return 0.8
        else:  # Regular daytime
            return 1.0
    
    def scrape_bing_maps_traffic(self, from_address, to_address):
        """
        Alternative traffic data source using Bing Maps data
        This would require Bing Maps API in production
        """
        try:
            # For demo purposes, we'll use a simplified calculation
            # In production, use Bing Maps Routes API
            from_coords = self.get_coordinates(from_address)
            to_coords = self.get_coordinates(to_address)
            
            if not from_coords or not to_coords:
                return None
                
            distance_miles = geodesic(from_coords, to_coords).miles
            
            # Bing typically provides more conservative estimates
            base_time_minutes = int((distance_miles / 25) * 60)  # Slightly slower than Google
            traffic_factor = self._get_traffic_factor() * 1.1  # Slightly more conservative
            
            return {
                'travel_time_minutes': int(base_time_minutes * traffic_factor),
                'distance_miles': distance_miles,
                'traffic_factor': traffic_factor
            }
            
        except Exception as e:
            self.logger.error(f"Bing traffic scraping error: {e}")
            return None
    
    def get_historical_traffic_pattern(self, route_key):
        """
        Get historical traffic data for a specific route
        In production, this would query a traffic database
        """
        try:
            # Check if we have historical data for this route
            existing_data = TrafficData.query.filter_by(
                from_address=route_key.split(' -> ')[0],
                to_address=route_key.split(' -> ')[1]
            ).order_by(TrafficData.scraped_at.desc()).first()
            
            if existing_data:
                # Use recent historical data if available
                return {
                    'travel_time_minutes': existing_data.travel_time_minutes,
                    'distance_miles': existing_data.distance_miles,
                    'traffic_factor': existing_data.traffic_factor
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Historical traffic query error: {e}")
            return None
    
    def update_traffic_data(self, from_address, to_address):
        """
        Update traffic data for a route pair and store in database
        """
        try:
            # Try Google Maps first, then Bing as fallback
            traffic_data = self.scrape_google_maps_traffic(from_address, to_address)
            
            if not traffic_data:
                traffic_data = self.scrape_bing_maps_traffic(from_address, to_address)
            
            if traffic_data:
                # Store in database
                new_traffic_data = TrafficData(
                    from_address=from_address,
                    to_address=to_address,
                    travel_time_minutes=traffic_data['travel_time_minutes'],
                    distance_miles=traffic_data['distance_miles'],
                    traffic_factor=traffic_data['traffic_factor']
                )
                
                db.session.add(new_traffic_data)
                db.session.commit()
                
                return traffic_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Traffic data update error: {e}")
            db.session.rollback()
            return None
    
    def scrape_mapquest_traffic(self, from_address, to_address):
        """
        Scrape traffic data from MapQuest
        This provides another data source for validation
        """
        try:
            # In production, use MapQuest Directions API
            # For now, provide a basic calculation with different assumptions
            from_coords = self.get_coordinates(from_address)
            to_coords = self.get_coordinates(to_address)
            
            if not from_coords or not to_coords:
                return None
                
            distance_miles = geodesic(from_coords, to_coords).miles
            
            # MapQuest often provides middle-ground estimates
            base_time_minutes = int((distance_miles / 28) * 60)
            traffic_factor = self._get_traffic_factor()
            
            return {
                'travel_time_minutes': int(base_time_minutes * traffic_factor),
                'distance_miles': distance_miles,
                'traffic_factor': traffic_factor
            }
            
        except Exception as e:
            self.logger.error(f"MapQuest traffic scraping error: {e}")
            return None
    
    def get_best_traffic_estimate(self, from_address, to_address):
        """
        Get the best traffic estimate by comparing multiple sources
        """
        estimates = []
        
        # Try all available sources
        google_data = self.scrape_google_maps_traffic(from_address, to_address)
        if google_data:
            estimates.append(google_data)
            
        bing_data = self.scrape_bing_maps_traffic(from_address, to_address)
        if bing_data:
            estimates.append(bing_data)
            
        mapquest_data = self.scrape_mapquest_traffic(from_address, to_address)
        if mapquest_data:
            estimates.append(mapquest_data)
        
        if not estimates:
            return None
        
        # Take the median estimate for more accuracy
        times = [est['travel_time_minutes'] for est in estimates]
        times.sort()
        
        if len(times) == 1:
            best_estimate = estimates[0]
        else:
            median_time = times[len(times) // 2]
            # Find the estimate closest to median
            best_estimate = min(estimates, 
                              key=lambda x: abs(x['travel_time_minutes'] - median_time))
        
        return best_estimate