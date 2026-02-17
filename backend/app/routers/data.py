from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from ..db import get_db
from .. import models, schemas

router = APIRouter()

def get_or_create_location(db: Session, state: str, lga: str, lat=None, lon=None):
    loc = db.query(models.Location).filter(models.Location.state == state, models.Location.lga == lga).first()
    if loc:
        return loc
    loc = models.Location(state=state, lga=lga, latitude=lat, longitude=lon)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc

@router.post("/environment")
def upload_environment(payload: schemas.EnvMetricIn, db: Session = Depends(get_db)):
    loc = get_or_create_location(db, payload.state, payload.lga)
    existing = (
        db.query(models.EnvMetric)
        .filter(models.EnvMetric.location_id == loc.id, models.EnvMetric.week_start == payload.week_start)
        .first()
    )
    if existing:
        existing.rainfall_mm = payload.rainfall_mm
        existing.temperature_c = payload.temperature_c
        existing.humidity_pct = payload.humidity_pct
        existing.flood_risk = payload.flood_risk
    else:
        rec = models.EnvMetric(
            location_id=loc.id,
            week_start=payload.week_start,
            rainfall_mm=payload.rainfall_mm,
            temperature_c=payload.temperature_c,
            humidity_pct=payload.humidity_pct,
            flood_risk=payload.flood_risk,
        )
        db.add(rec)
    db.commit()
    return {"status": "ok"}

@router.post("/seed")
def seed_data(payload: schemas.AdminAction, db: Session = Depends(get_db)):
    if payload.admin_secret != "phip_admin_secret_2026":
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    # Import here to avoid circular imports
    from ...scripts.generate_data import generate
    try:
        generate(db)
        return {"status": "success", "message": "Database seeded with synthetic data."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/community")
def upload_community(payload: schemas.CommunitySignalIn, db: Session = Depends(get_db)):
    loc = get_or_create_location(db, payload.state, payload.lga)
    existing = (
        db.query(models.CommunitySignal)
        .filter(models.CommunitySignal.location_id == loc.id, models.CommunitySignal.week_start == payload.week_start)
        .first()
    )
    if existing:
        existing.fever_reports = payload.fever_reports
        existing.cough_reports = payload.cough_reports
        existing.diarrhea_reports = payload.diarrhea_reports
        existing.vomiting_reports = payload.vomiting_reports
        existing.pharmacy_sales_fever = payload.pharmacy_sales_fever
        existing.pharmacy_sales_antibiotics = payload.pharmacy_sales_antibiotics
        existing.pharmacy_sales_antimalarials = payload.pharmacy_sales_antimalarials
        existing.absenteeism_rate = payload.absenteeism_rate
    else:
        rec = models.CommunitySignal(
            location_id=loc.id,
            week_start=payload.week_start,
            fever_reports=payload.fever_reports,
            cough_reports=payload.cough_reports,
            diarrhea_reports=payload.diarrhea_reports,
            vomiting_reports=payload.vomiting_reports,
            pharmacy_sales_fever=payload.pharmacy_sales_fever,
            pharmacy_sales_antibiotics=payload.pharmacy_sales_antibiotics,
            pharmacy_sales_antimalarials=payload.pharmacy_sales_antimalarials,
            absenteeism_rate=payload.absenteeism_rate,
        )
        db.add(rec)
    db.commit()
    return {"status": "ok"}

@router.post("/disease-history")
def upload_disease_history(payload: schemas.DiseaseHistoryIn, db: Session = Depends(get_db)):
    loc = get_or_create_location(db, payload.state, payload.lga)
    existing = (
        db.query(models.DiseaseHistory)
        .filter(models.DiseaseHistory.location_id == loc.id, models.DiseaseHistory.week_start == payload.week_start)
        .first()
    )
    if existing:
        existing.cholera_cases = payload.cholera_cases
        existing.malaria_cases = payload.malaria_cases
        existing.lassa_cases = payload.lassa_cases
        existing.meningitis_cases = payload.meningitis_cases
    else:
        rec = models.DiseaseHistory(
            location_id=loc.id,
            week_start=payload.week_start,
            cholera_cases=payload.cholera_cases,
            malaria_cases=payload.malaria_cases,
            lassa_cases=payload.lassa_cases,
            meningitis_cases=payload.meningitis_cases,
        )
        db.add(rec)
    db.commit()
    return {"status": "ok"}

