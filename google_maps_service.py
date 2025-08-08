import os
import requests
import logging
from typing import List, Dict, Optional, Tuple
import time

class GoogleMapsService:
    """Service for Google Maps Distance Matrix API integration"""
    
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        
    def get_drive_times(self, origins: List[str], destinations: List[str], 
                       departure_time: Optional[str] = None) -> Dict:
        """
        Get drive times between multiple origins and destinations using Google Maps API
        
        Args:
            origins: List of origin addresses
            destinations: List of destination addresses  
            departure_time: Optional departure time for traffic-aware routing (format: "now" or epoch time)
            
        Returns:
            Dictionary with drive time data or None if API call fails
        """
        if not self.api_key:
            logging.warning("Google Maps API key not found, falling back to estimates")
            return None
            
        params = {
            'origins': '|'.join(origins),
            'destinations': '|'.join(destinations),
            'key': self.api_key,
            'units': 'imperial',
            'mode': 'driving',
            'traffic_model': 'best_guess',
            'departure_time': departure_time or 'now'
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                logging.error(f"Google Maps API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                return None
                
            return data
            
        except requests.RequestException as e:
            logging.error(f"Google Maps API request failed: {e}")
            return None
    
    def get_route_drive_times(self, departure_address: str, stop_addresses: List[str]) -> Tuple[List[int], int, int]:
        """
        Get drive times for a complete route: departure -> stops -> departure
        
        Args:
            departure_address: Starting/ending address
            stop_addresses: List of stop addresses in route order
            
        Returns:
            Tuple of (drive_times_between_stops, departure_to_first, last_to_departure) in minutes
        """
        if not stop_addresses:
            return [], 0, 0
            
        all_addresses = [departure_address] + stop_addresses + [departure_address]
        drive_times_between_stops = []
        departure_to_first = 0
        last_to_departure = 0
        
        # Get drive time from departure to first stop
        if len(stop_addresses) > 0:
            data = self.get_drive_times([departure_address], [stop_addresses[0]])
            if data and data.get('rows'):
                element = data['rows'][0]['elements'][0]
                if element.get('status') == 'OK' and 'duration_in_traffic' in element:
                    departure_to_first = element['duration_in_traffic']['value'] // 60  # Convert to minutes
                elif element.get('status') == 'OK' and 'duration' in element:
                    departure_to_first = element['duration']['value'] // 60  # Fallback to duration without traffic
        
        # Get drive times between consecutive stops
        if len(stop_addresses) > 1:
            for i in range(len(stop_addresses) - 1):
                data = self.get_drive_times([stop_addresses[i]], [stop_addresses[i + 1]])
                if data and data.get('rows'):
                    element = data['rows'][0]['elements'][0]
                    if element.get('status') == 'OK' and 'duration_in_traffic' in element:
                        drive_time = element['duration_in_traffic']['value'] // 60
                    elif element.get('status') == 'OK' and 'duration' in element:
                        drive_time = element['duration']['value'] // 60
                    else:
                        drive_time = 10  # Fallback estimate
                    drive_times_between_stops.append(drive_time)
                else:
                    drive_times_between_stops.append(10)  # Fallback estimate
        
        # Get drive time from last stop back to departure
        if len(stop_addresses) > 0:
            data = self.get_drive_times([stop_addresses[-1]], [departure_address])
            if data and data.get('rows'):
                element = data['rows'][0]['elements'][0]
                if element.get('status') == 'OK' and 'duration_in_traffic' in element:
                    last_to_departure = element['duration_in_traffic']['value'] // 60
                elif element.get('status') == 'OK' and 'duration' in element:
                    last_to_departure = element['duration']['value'] // 60
        
        return drive_times_between_stops, departure_to_first, last_to_departure
    
    def get_fallback_drive_times(self, departure_address: str, stop_addresses: List[str], 
                                start_time: str) -> Tuple[List[int], int, int]:
        """
        Fallback method using Atlanta traffic-aware estimates when API is unavailable
        """
        if not stop_addresses:
            return [], 0, 0
            
        from datetime import datetime
        start_hour = datetime.strptime(start_time, '%H:%M').hour
        
        # Traffic-based estimates for Atlanta metro area - enforcing 5 minute minimum
        if (6 <= start_hour <= 10) or (16 <= start_hour <= 19):
            # Rush hour
            between_stops = max(12, 5)  # Minimum 5 minutes
            to_from_base = max(18, 5)
        elif (10 < start_hour < 16):
            # Mid-day optimal - enforce 5 minute minimum
            between_stops = max(8, 5)  # Minimum 5 minutes (was 8)
            to_from_base = max(12, 5)
        else:
            # Off-peak
            between_stops = max(10, 5)  # Minimum 5 minutes
            to_from_base = max(15, 5)
            
        drive_times_between_stops = [between_stops] * (len(stop_addresses) - 1) if len(stop_addresses) > 1 else []
        departure_to_first = to_from_base
        last_to_departure = to_from_base
        
        return drive_times_between_stops, departure_to_first, last_to_departure