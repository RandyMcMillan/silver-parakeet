"""
Traffic History Manager - Monthly Snapshots with Variance Detection
Manages historical traffic data with intelligent update triggers based on construction-level variance
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
from app import db

logger = logging.getLogger(__name__)

# Import TrafficSnapshot from models.py instead of defining it here
from models import TrafficSnapshot

class TrafficHistoryManager:
    """Manages traffic data snapshots and variance detection"""
    
    # Variance thresholds (in minutes)
    CONSTRUCTION_VARIANCE_THRESHOLD = 15  # 15+ minute increase indicates construction
    SIGNIFICANT_VARIANCE_THRESHOLD = 8    # 8+ minute change triggers update
    WEEKLY_CHECK_INTERVAL = 7             # Check weekly for variance
    MONTHLY_SNAPSHOT_INTERVAL = 30        # Take monthly snapshots
    
    def __init__(self):
        self.google_maps_service = None
        
    def calculate_route_hash(self, origin: str, destination: str) -> str:
        """Create a consistent hash for origin-destination pairs"""
        import hashlib
        route_key = f"{origin.lower().strip()}|{destination.lower().strip()}"
        return hashlib.md5(route_key.encode()).hexdigest()
    
    def get_current_traffic_data(self, origin: str, destination: str) -> Dict[str, float]:
        """Get current traffic data for multiple time periods"""
        try:
            if not self.google_maps_service:
                from google_maps_service import GoogleMapsService
                self.google_maps_service = GoogleMapsService()
            
            # Sample different time periods for comprehensive data
            current_time = datetime.now()
            
            # Use the existing Google Maps service method
            # Get current time estimate (this will use traffic-aware routing)
            current_estimate = self.google_maps_service.get_travel_time(origin, destination)
            
            # Apply time-of-day multipliers based on traffic patterns
            morning_time = current_estimate * 1.3  # 30% longer during morning rush
            midday_time = current_estimate * 1.0   # Normal time during midday
            evening_time = current_estimate * 1.4  # 40% longer during evening rush
            off_peak_time = current_estimate * 0.8  # 20% faster during off-peak
            
            return {
                'morning_rush_time': morning_time or 0,
                'midday_time': midday_time or 0,
                'evening_rush_time': evening_time or 0,
                'off_peak_time': off_peak_time or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting current traffic data: {e}")
            return {
                'morning_rush_time': 0,
                'midday_time': 0,
                'evening_rush_time': 0,
                'off_peak_time': 0
            }
    
    def calculate_variance_score(self, current_data: Dict[str, float], 
                               historical_data: Dict[str, float]) -> float:
        """Calculate variance score between current and historical data"""
        if not historical_data or not current_data:
            return 0.0
        
        total_variance = 0.0
        periods = ['morning_rush_time', 'midday_time', 'evening_rush_time', 'off_peak_time']
        
        for period in periods:
            if period in current_data and period in historical_data:
                current_val = current_data[period]
                historical_val = historical_data[period]
                
                if historical_val > 0:
                    # Calculate percentage change
                    variance = abs(current_val - historical_val)
                    total_variance += variance
        
        # Average variance across all periods
        return total_variance / len(periods)
    
    def is_construction_level_variance(self, variance_score: float) -> bool:
        """Determine if variance indicates construction or major traffic changes"""
        return variance_score >= self.CONSTRUCTION_VARIANCE_THRESHOLD
    
    def needs_weekly_update(self, route_hash: str) -> bool:
        """Check if route needs weekly variance check"""
        snapshot = TrafficSnapshot.query.filter_by(route_hash=route_hash).first()
        
        if not snapshot:
            return True  # No snapshot exists, need to create one
        
        if not snapshot.last_weekly_check:
            return True  # Never checked weekly
        
        days_since_check = (datetime.utcnow() - snapshot.last_weekly_check).days
        return days_since_check >= self.WEEKLY_CHECK_INTERVAL
    
    def needs_monthly_snapshot(self, route_hash: str) -> bool:
        """Check if route needs monthly snapshot"""
        snapshot = TrafficSnapshot.query.filter_by(route_hash=route_hash).first()
        
        if not snapshot:
            return True  # No snapshot exists
        
        days_since_snapshot = (datetime.utcnow() - snapshot.snapshot_date).days
        return days_since_snapshot >= self.MONTHLY_SNAPSHOT_INTERVAL
    
    def update_traffic_snapshot(self, origin: str, destination: str) -> Optional[TrafficSnapshot]:
        """Update traffic snapshot based on variance or monthly schedule"""
        route_hash = self.calculate_route_hash(origin, destination)
        
        # Check if any update is needed
        needs_weekly = self.needs_weekly_update(route_hash)
        needs_monthly = self.needs_monthly_snapshot(route_hash)
        
        if not needs_weekly and not needs_monthly:
            return None  # No update needed
        
        # Get current traffic data
        current_data = self.get_current_traffic_data(origin, destination)
        if not any(current_data.values()):
            logger.warning(f"No traffic data available for {origin} to {destination}")
            return None
        
        # Get existing snapshot
        existing_snapshot = TrafficSnapshot.query.filter_by(route_hash=route_hash).first()
        
        # Calculate variance if existing snapshot exists
        variance_score = 0.0
        construction_flag = False
        
        if existing_snapshot and needs_weekly:
            historical_data = {
                'morning_rush_time': float(existing_snapshot.morning_rush_time or 0),
                'midday_time': float(existing_snapshot.midday_time or 0),
                'evening_rush_time': float(existing_snapshot.evening_rush_time or 0),
                'off_peak_time': float(existing_snapshot.off_peak_time or 0)
            }
            
            variance_score = self.calculate_variance_score(current_data, historical_data)
            construction_flag = self.is_construction_level_variance(variance_score)
            
            # Update weekly check timestamp
            existing_snapshot.last_weekly_check = datetime.utcnow()
            
            # Only update snapshot if significant variance or monthly schedule
            if variance_score < self.SIGNIFICANT_VARIANCE_THRESHOLD and not needs_monthly:
                logger.info(f"Low variance ({variance_score:.1f} min) for {origin} to {destination}, keeping existing snapshot")
                db.session.commit()
                return existing_snapshot
        
        # Create or update snapshot
        if existing_snapshot and (construction_flag or needs_monthly):
            # Update existing snapshot
            existing_snapshot.morning_rush_time = current_data['morning_rush_time']
            existing_snapshot.midday_time = current_data['midday_time']
            existing_snapshot.evening_rush_time = current_data['evening_rush_time']
            existing_snapshot.off_peak_time = current_data['off_peak_time']
            existing_snapshot.variance_score = variance_score
            existing_snapshot.construction_flag = construction_flag
            existing_snapshot.last_weekly_check = datetime.utcnow()
            existing_snapshot.updated_at = datetime.utcnow()
            
            if needs_monthly or construction_flag:
                existing_snapshot.snapshot_date = datetime.utcnow()
            
            snapshot = existing_snapshot
            
        else:
            # Create new snapshot
            snapshot = TrafficSnapshot()
            snapshot.snapshot_date = datetime.utcnow()
            snapshot.route_hash = route_hash
            snapshot.origin_address = origin
            snapshot.destination_address = destination
            snapshot.morning_rush_time = current_data['morning_rush_time']
            snapshot.midday_time = current_data['midday_time']
            snapshot.evening_rush_time = current_data['evening_rush_time']
            snapshot.off_peak_time = current_data['off_peak_time']
            snapshot.variance_score = variance_score
            snapshot.construction_flag = construction_flag
            snapshot.last_weekly_check = datetime.utcnow()
            
            db.session.add(snapshot)
        
        try:
            db.session.commit()
            
            action = "Updated" if existing_snapshot else "Created"
            variance_info = f" (variance: {variance_score:.1f} min)" if variance_score > 0 else ""
            construction_info = " [CONSTRUCTION DETECTED]" if construction_flag else ""
            
            logger.info(f"{action} traffic snapshot for {origin} to {destination}{variance_info}{construction_info}")
            
            return snapshot
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving traffic snapshot: {e}")
            return None
    
    def get_traffic_estimate(self, origin: str, destination: str, 
                           departure_time: Optional[datetime] = None) -> float:
        """Get traffic estimate using historical data or live data if needed"""
        route_hash = self.calculate_route_hash(origin, destination)
        snapshot = TrafficSnapshot.query.filter_by(route_hash=route_hash).first()
        
        if not snapshot:
            # No historical data, get live data and create snapshot
            logger.info(f"No historical data for {origin} to {destination}, getting live data")
            self.update_traffic_snapshot(origin, destination)
            snapshot = TrafficSnapshot.query.filter_by(route_hash=route_hash).first()
        
        if not snapshot:
            # Still no data, return fallback estimate
            return 15.0  # 15-minute fallback
        
        # Determine time period
        if not departure_time:
            departure_time = datetime.now()
        
        hour = departure_time.hour
        
        # Select appropriate time estimate based on hour
        if 7 <= hour < 10:  # Morning rush
            return snapshot.morning_rush_time or 15.0
        elif 16 <= hour < 20:  # Evening rush
            return snapshot.evening_rush_time or 15.0
        elif 10 <= hour < 16:  # Midday
            return snapshot.midday_time or 15.0
        else:  # Off-peak
            return snapshot.off_peak_time or 15.0
    
    def get_construction_alerts(self) -> List[Dict]:
        """Get routes with detected construction or major traffic changes"""
        construction_routes = TrafficSnapshot.query.filter_by(construction_flag=True).all()
        
        alerts = []
        for route in construction_routes:
            alerts.append({
                'origin': route.origin_address,
                'destination': route.destination_address,
                'variance_minutes': route.variance_score,
                'last_updated': route.updated_at,
                'morning_rush_time': route.morning_rush_time,
                'evening_rush_time': route.evening_rush_time
            })
        
        return alerts
    
    def cleanup_old_snapshots(self, days_to_keep: int = 90):
        """Clean up snapshots older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        old_snapshots = TrafficSnapshot.query.filter(
            TrafficSnapshot.snapshot_date < cutoff_date
        ).all()
        
        for snapshot in old_snapshots:
            db.session.delete(snapshot)
        
        try:
            db.session.commit()
            logger.info(f"Cleaned up {len(old_snapshots)} old traffic snapshots")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cleaning up old snapshots: {e}")

# Global instance
traffic_history_manager = TrafficHistoryManager()