from app import db
from datetime import datetime
from sqlalchemy import DateTime, String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

class Stop(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_type: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'install' or 'pickup'
    is_asap: Mapped[bool] = mapped_column(Boolean, default=False)
    required_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    agent_sign_description: Mapped[str] = mapped_column(Text, nullable=True)  # For installs
    has_riders_toppers: Mapped[bool] = mapped_column(Boolean, default=False)
    riders_toppers_description: Mapped[str] = mapped_column(Text, nullable=True)
    has_shelter: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Stop {self.id}: {self.post_type} at {self.address}>'

class Route(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_number: Mapped[int] = mapped_column(Integer, nullable=False)
    stop_sequence: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of stop IDs in order
    total_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False, default='07:00')
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
