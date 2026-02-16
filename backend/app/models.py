import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, JSON, Text
from sqlalchemy.orm import relationship
from .db import Base

# Keep Location for other metrics if needed, or we can rely on string state/lga
class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, index=True, nullable=False)
    lga = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    __table_args__ = (UniqueConstraint("state", "lga", name="uq_state_lga"),)

class EnvMetric(Base):
    __tablename__ = "env_metrics"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    rainfall_mm = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    flood_risk = Column(Float, nullable=True)
    location = relationship("Location")
    __table_args__ = (UniqueConstraint("location_id", "week_start", name="uq_env_week"),)

class DiseaseHistory(Base):
    __tablename__ = "disease_history"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    cholera_cases = Column(Integer, nullable=True)
    malaria_cases = Column(Integer, nullable=True)
    lassa_cases = Column(Integer, nullable=True)
    meningitis_cases = Column(Integer, nullable=True)
    location = relationship("Location")
    __table_args__ = (UniqueConstraint("location_id", "week_start", name="uq_disease_week"),)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    created_at_week = Column(Date, nullable=False)
    disease = Column(String, nullable=False)
    level = Column(String, nullable=False)  # Low/Medium/High/EarlyWarning
    message = Column(String, nullable=False)
    risk_score = Column(Float, nullable=True)
    location = relationship("Location")

# --- New Schema Implementation ---

class Facility(Base):
    __tablename__ = "facilities"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    type = Column(String, nullable=False) # PHC / Hospital / Clinic
    state = Column(String, nullable=False)
    lga = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("FacilityUser", back_populates="facility")
    reports = relationship("DailyReport", back_populates="facility")

class FacilityUser(Base):
    __tablename__ = "facility_users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String, ForeignKey("facilities.id"), nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String, default="facility_user")
    created_at = Column(DateTime, default=datetime.utcnow)

    facility = relationship("Facility", back_populates="users")

class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String, ForeignKey("facilities.id"), nullable=False)
    report_date = Column(Date, nullable=False)
    
    fever_cases = Column(Integer, default=0)
    diarrhea_cases = Column(Integer, default=0)
    vomiting_cases = Column(Integer, default=0)
    respiratory_cases = Column(Integer, default=0)
    
    hospital_admissions = Column(Integer, default=0)
    severe_dehydration_cases = Column(Integer, default=0)
    unexplained_deaths = Column(Integer, nullable=True, default=0)
    
    bed_occupancy_rate = Column(Float, default=0.0)
    ors_stock_level = Column(String, default="Normal") # Normal / Low / Out
    antibiotics_stock_level = Column(String, default="Normal") # Normal / Low / Out
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    facility = relationship("Facility", back_populates="reports")
    __table_args__ = (UniqueConstraint("facility_id", "report_date", name="uq_facility_date"),)

class LGAWeeklyAggregate(Base):
    __tablename__ = "lga_weekly_aggregates"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lga = Column(String, nullable=False)
    state = Column(String, nullable=False)
    week_start_date = Column(Date, nullable=False)
    
    total_fever_cases = Column(Integer, default=0)
    total_diarrhea_cases = Column(Integer, default=0)
    total_respiratory_cases = Column(Integer, default=0)
    total_admissions = Column(Integer, default=0)
    avg_bed_occupancy = Column(Float, default=0.0)
    low_stock_alerts = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("state", "lga", "week_start_date", name="uq_lga_week"),)

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lga = Column(String, nullable=False)
    state = Column(String, nullable=False)
    disease = Column(String, nullable=False)
    prediction_date = Column(Date, nullable=False)
    weeks_ahead = Column(Integer, nullable=False)
    
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    top_factors = Column(JSON, nullable=True) # JSONB in Postgres
    
    created_at = Column(DateTime, default=datetime.utcnow)
