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
