from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- Location (Legacy/Shared) ---
class LocationCreate(BaseModel):
    state: str
    lga: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class LocationOut(LocationCreate):
    id: int
    class Config:
        from_attributes = True

# --- Facility ---
class FacilityCreate(BaseModel):
    name: str
    type: str # PHC / Hospital / Clinic
    state: str
    lga: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    username: str
    password: str = Field(..., max_length=72)

class FacilityOut(BaseModel):
    id: str # UUID
    name: str
    type: str
    state: str
    lga: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    facility: FacilityOut

# --- Daily Reports ---
class DailyReportCreate(BaseModel):
    report_date: date
    fever_cases: int = 0
    diarrhea_cases: int = 0
    vomiting_cases: int = 0
    respiratory_cases: int = 0
    hospital_admissions: int = 0
    severe_dehydration_cases: int = 0
    unexplained_deaths: int = 0
    bed_occupancy_rate: float = 0.0
    ors_stock_level: str = "Normal"
    antibiotics_stock_level: str = "Normal"
    notes: Optional[str] = None

class DailyReportOut(DailyReportCreate):
    id: str # UUID
    facility_id: str # UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class FeedbackOut(BaseModel):
    risk_level: str
    risk_trend: str
    warning_message: str
    comparison: dict  # e.g., {"my_fever": 5, "lga_avg_fever": 12}

# --- Legacy/Shared Inputs ---
class EnvMetricIn(BaseModel):
    state: str
    lga: str
    week_start: date
    rainfall_mm: Optional[float] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    flood_risk: Optional[float] = None

class CommunitySignalIn(BaseModel):
    state: str
    lga: str
    week_start: date
    fever_reports: Optional[int] = None
    cough_reports: Optional[int] = None
    diarrhea_reports: Optional[int] = None
    vomiting_reports: Optional[int] = None
    pharmacy_sales_fever: Optional[int] = None
    pharmacy_sales_antibiotics: Optional[int] = None
    pharmacy_sales_antimalarials: Optional[int] = None
    absenteeism_rate: Optional[float] = None

class DiseaseHistoryIn(BaseModel):
    state: str
    lga: str
    week_start: date
    cholera_cases: Optional[int] = None
    malaria_cases: Optional[int] = None
    lassa_cases: Optional[int] = None
    meningitis_cases: Optional[int] = None

# --- ML / Predictions ---
class PredictionOut(BaseModel):
    state: str
    lga: str
    disease: str
    prediction_date: date
    weeks_ahead: int
    risk_score: float
    risk_level: str
    top_factors: Optional[List[Any]] = [] # JSONB can be list or dict
    
    class Config:
        from_attributes = True

class HeatmapItem(BaseModel):
    state: str
    lga: str
    latitude: Optional[float]
    longitude: Optional[float]
    risk_score: float
    risk_category: str
    disease: str

class HeatmapResponse(BaseModel):
    items: List[HeatmapItem]

class AlertOut(BaseModel):
    id: int
    location: LocationOut
    created_at_week: date
    disease: str
    level: str
    message: str
    risk_score: float

    class Config:
        from_attributes = True
