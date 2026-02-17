from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta
from typing import List
from ..db import get_db
from .. import models, schemas
from ..ml.model import RiskModel, build_feature_vector, risk_category
from ..alerts.rules import evaluate_alerts

router = APIRouter()

_models_cache = {}

def get_model(disease: str, db: Session) -> RiskModel:
    model = _models_cache.get(disease)
    if not model:
        model = RiskModel(disease=disease)
        model.train(db)
        _models_cache[disease] = model
    return model

@router.post("/retrain")
def retrain_models(db: Session = Depends(get_db)):
    for disease in ["cholera", "malaria", "lassa", "meningitis"]:
        model = RiskModel(disease=disease)
        model.train(db)
        _models_cache[disease] = model
    return {"status": "ok"}

@router.get("/{state}/{lga}")
def get_predictions(state: str, lga: str, weeks_ahead: int = 2, disease: str = "cholera", db: Session = Depends(get_db)):
    loc = db.query(models.Location).filter(models.Location.state == state, models.Location.lga == lga).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    model = get_model(disease, db)
    # Use latest available week in datasets
    latest_week = (
        db.query(models.DiseaseHistory.week_start)
        .filter(models.DiseaseHistory.location_id == loc.id)
        .order_by(models.DiseaseHistory.week_start.desc())
        .first()
    )
    base_week = latest_week[0] if latest_week else date.today()
    # target_week = base_week + timedelta(days=7 * weeks_ahead)
    features = build_feature_vector(db, loc.id, base_week)
    
    # New full prediction
    result = model.predict_full(features)
    score = result["risk_score"]
    category = result["risk_level"]
    factors = result["top_factors"]
    
    # Update to use RiskPrediction
    pred = models.RiskPrediction(
        state=loc.state,
        lga=loc.lga,
        prediction_date=base_week,
        weeks_ahead=weeks_ahead,
        risk_score=score,
        risk_level=category,
        disease=disease,
        top_factors=factors
    )
    db.add(pred)
    db.commit()
    evaluate_alerts(db, loc.id, disease, base_week, score)
    
    return schemas.PredictionOut(
        state=loc.state,
        lga=loc.lga,
        disease=disease,
        prediction_date=base_week,
        weeks_ahead=weeks_ahead,
        risk_score=score,
        risk_level=category,
        top_factors=factors
    )

@router.get("/heatmap-data")
def heatmap_data(disease: str = "cholera", db: Session = Depends(get_db)):
    # 1. First, try to fetch the LATEST pre-calculated predictions for all locations
    # This avoids re-running the model for every single request and ensures we see what was just saved
    
    # Subquery to find the latest prediction date per LGA
    # (In a real production app, we might just filter by date > today - 7 days)
    
    latest_preds = (
        db.query(models.RiskPrediction)
        .filter(models.RiskPrediction.disease == disease)
        .order_by(models.RiskPrediction.prediction_date.desc())
        .all()
    )
    
    # De-duplicate by LGA (take the newest one)
    # Map (state, lga) -> prediction
    pred_map = {}
    for p in latest_preds:
        key = (p.state, p.lga)
        if key not in pred_map:
            pred_map[key] = p
            
    items = []
    locations = db.query(models.Location).all()
    
    for loc in locations:
        key = (loc.state, loc.lga)
        
        # If we have a recent prediction, use it
        if key in pred_map:
            p = pred_map[key]
            items.append(
                schemas.HeatmapItem(
                    state=loc.state,
                    lga=loc.lga,
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                    risk_score=p.risk_score,
                    risk_category=p.risk_level,
                    disease=disease,
                )
            )
        else:
            # Fallback: Compute on the fly if no prediction exists (e.g. fresh data or no report yet)
            # This ensures we don't show empty map if jobs haven't run
            try:
                model = get_model(disease, db)
                features = build_feature_vector(db, loc.id, date.today())
                score = model.predict_score(features)
                items.append(
                    schemas.HeatmapItem(
                        state=loc.state,
                        lga=loc.lga,
                        latitude=loc.latitude,
                        longitude=loc.longitude,
                        risk_score=score,
                        risk_category=risk_category(score),
                        disease=disease,
                    )
                )
            except Exception:
                # If model fails (e.g. no data), skip or show low risk
                pass

    return schemas.HeatmapResponse(items=items)
