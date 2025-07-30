from app import db
from datetime import datetime, date
from sqlalchemy import DateTime, String, Integer, Boolean, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

class Stop(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_type: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False, index=True)  # Index for frequent searches
    service_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # Index for filtering
    is_asap: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # Index for priority queries
    required_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)  # Index for date filtering
    agent_sign_description: Mapped[str | None] = mapped_column(Text, nullable=True)  # For installs
    has_riders_toppers: Mapped[bool] = mapped_column(Boolean, default=False)
    riders_toppers_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_shelter: Mapped[bool] = mapped_column(Boolean, default=False)
    # Pickup/Reinstall functionality
    is_pickup_reinstall: Mapped[bool] = mapped_column(Boolean, default=False)  # Whether this is a pickup+reinstall pair
    pickup_address: Mapped[str | None] = mapped_column(Text, nullable=True)  # Pickup location (first stop)
    reinstall_address: Mapped[str | None] = mapped_column(Text, nullable=True)  # Reinstall location (second stop)
    pair_group_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # Links paired stops together
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)  # Index for chronological queries
    
    def __repr__(self):
        return f'<Stop {self.id}: {self.post_type} at {self.address}>'

class Route(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_number: Mapped[int] = mapped_column(Integer, nullable=False)
    stop_sequence: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of stop IDs in order
    total_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False, default='07:00')
    route_date: Mapped[date] = mapped_column(db.Date, nullable=False, default=lambda: date.today())
    google_maps_data: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string of drive time data
    overtime_approved: Mapped[bool] = mapped_column(Boolean, default=False)  # Overtime with 8-week lead time
    lead_time_weeks: Mapped[int] = mapped_column(Integer, nullable=True)  # Weeks of advance notice
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Route {self.id}: Driver {self.driver_number}>'

class AgentSignHistory(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    sign_description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AgentSignHistory {self.id}: {self.address}>'

class DriverDepartureAddress(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DriverDepartureAddress {self.id}: {self.address}>'

class TrafficData(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_address: Mapped[str] = mapped_column(Text, nullable=False)
    to_address: Mapped[str] = mapped_column(Text, nullable=False)
    travel_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_miles: Mapped[float] = mapped_column(db.Float, nullable=True)
    traffic_factor: Mapped[float] = mapped_column(db.Float, default=1.0)  # Multiplier for base time
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrafficData {self.id}: {self.from_address} to {self.to_address}>'

class OvertimePolicy(db.Model):
    """Manages overtime approval policies with lead time requirements"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    minimum_lead_time_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    max_overtime_hours_daily: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    overtime_rate_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<OvertimePolicy {self.id}: {self.minimum_lead_time_weeks} weeks lead time>'

class TrafficSnapshot(db.Model):
    """Store monthly traffic snapshots with variance tracking"""
    __tablename__ = 'traffic_snapshots'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    route_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    origin_address: Mapped[str] = mapped_column(String(500), nullable=False)
    destination_address: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Traffic timing data (in minutes)
    morning_rush_time: Mapped[float | None] = mapped_column(Float, nullable=True)  # 7-10 AM average
    midday_time: Mapped[float | None] = mapped_column(Float, nullable=True)        # 10 AM - 4 PM average
    evening_rush_time: Mapped[float | None] = mapped_column(Float, nullable=True)  # 4-8 PM average
    off_peak_time: Mapped[float | None] = mapped_column(Float, nullable=True)      # 8 PM - 7 AM average
    
    # Variance tracking
    variance_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100 scale
    construction_flag: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    last_weekly_check: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    
    # Metadata
    data_source: Mapped[str] = mapped_column(String(100), default='Google Maps API')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrafficSnapshot {self.id}: {self.origin_address} to {self.destination_address}>'
