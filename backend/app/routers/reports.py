from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from .. import models, schemas, auth_utils
from ..db import get_db
from ..ml.aggregation import aggregate_facility_reports
from ..routers.predictions import get_model, evaluate_alerts
from ..ml.model import build_feature_vector

router = APIRouter()

@router.post("/", response_model=schemas.DailyReportOut)
def submit_report(
    report: schemas.DailyReportCreate,
    current_facility: models.Facility = Depends(auth_utils.get_current_facility),
    db: Session = Depends(get_db)
):
    # Check if report already exists for today
    existing = db.query(models.DailyReport).filter(
        models.DailyReport.facility_id == current_facility.id,
        models.DailyReport.report_date == report.report_date
    ).first()
    
    if existing:
        # Update existing
        for key, value in report.dict().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        new_report = existing
    else:
        new_report = models.DailyReport(
            facility_id=current_facility.id,
            **report.dict()
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
    
    # 1. Aggregate Reports
    aggregate_facility_reports(db, current_facility.state, current_facility.lga, report.report_date)
    
    # 2. Trigger Real-time Risk Update
    try:
        loc = db.query(models.Location).filter(
            models.Location.state == current_facility.state, 
            models.Location.lga == current_facility.lga
        ).first()
        
        if loc:
            # We predict for the week containing this report
            features = build_feature_vector(db, loc.id, report.report_date)
            
            # Predict for all diseases
            for disease in ["cholera", "malaria", "lassa", "meningitis"]:
                model = get_model(disease, db)
                result = model.predict_full(features)
                
                # Update/Insert Prediction
                # Check if prediction already exists for this week/disease
                # For simplicity, we just insert a new one or update latest. 
                # Ideally, we should have unique constraint on (lga, disease, prediction_date)
                
                pred = models.RiskPrediction(
                    state=loc.state,
                    lga=loc.lga,
                    prediction_date=report.report_date,
                    weeks_ahead=2,
                    risk_score=result["risk_score"],
                    risk_level=result["risk_level"],
                    disease=disease,
                    top_factors=result["top_factors"]
                )
                db.add(pred)
                
                evaluate_alerts(db, loc.id, disease, report.report_date, result["risk_score"])
            
            db.commit()
    except Exception as e:
        print(f"Error updating risk score: {e}")
        # Don't fail the report submission if prediction fails
    
    return new_report

@router.get("/feedback", response_model=schemas.FeedbackOut)
def get_feedback(
    current_facility: models.Facility = Depends(auth_utils.get_current_facility),
    db: Session = Depends(get_db)
):
    # Get latest prediction for this location
    latest_pred = (
        db.query(models.RiskPrediction)
        .filter(models.RiskPrediction.state == current_facility.state)
        .filter(models.RiskPrediction.lga == current_facility.lga)
        .order_by(models.RiskPrediction.prediction_date.desc())
        .first()
    )
    
    risk_level = latest_pred.risk_level if latest_pred else "Unknown"
    
    # Simple trend logic (compare to previous prediction)
    prev_pred = None
    if latest_pred:
        prev_pred = (
            db.query(models.RiskPrediction)
            .filter(models.RiskPrediction.state == current_facility.state)
            .filter(models.RiskPrediction.lga == current_facility.lga)
            .filter(models.RiskPrediction.prediction_date < latest_pred.prediction_date)
            .order_by(models.RiskPrediction.prediction_date.desc())
            .first()
        )
    
    risk_trend = "Stable"
    if latest_pred and prev_pred:
        if latest_pred.risk_score > prev_pred.risk_score + 0.1:
            risk_trend = "Rising"
        elif latest_pred.risk_score < prev_pred.risk_score - 0.1:
            risk_trend = "Falling"
            
    # Warning message
    msg = "No specific warnings."
    if risk_level == "High":
        msg = "High risk of outbreak detected. Ensure ORS and antibiotics stock is sufficient."
    elif risk_level == "Medium" and risk_trend == "Rising":
        msg = "Risk is rising. Monitor fever and diarrhea cases closely."
        
    # Comparison Stats (My Facility vs LGA Avg)
    today = date.today()
    my_report = db.query(models.DailyReport).filter(
        models.DailyReport.facility_id == current_facility.id,
        models.DailyReport.report_date == today
    ).first()
    
    lga_reports = (
        db.query(models.DailyReport)
        .join(models.Facility)
        .filter(models.Facility.state == current_facility.state)
        .filter(models.Facility.lga == current_facility.lga)
        .filter(models.DailyReport.report_date == today)
        .all()
    )
    
    my_fever = my_report.fever_cases if my_report else 0
    my_respiratory = my_report.respiratory_cases if my_report else 0
    my_diarrhea = my_report.diarrhea_cases if my_report else 0
    my_vomiting = my_report.vomiting_cases if my_report else 0

    count = len(lga_reports)
    avg_fever = sum(r.fever_cases for r in lga_reports) / count if count else 0
    avg_respiratory = sum(r.respiratory_cases for r in lga_reports) / count if count else 0
    avg_diarrhea = sum(r.diarrhea_cases for r in lga_reports) / count if count else 0
    avg_vomiting = sum(r.vomiting_cases for r in lga_reports) / count if count else 0
    
    return {
        "risk_level": risk_level,
        "risk_trend": risk_trend,
        "warning_message": msg,
        "comparison": {
            "my_fever": my_fever,
            "lga_avg_fever": avg_fever,
            "my_respiratory": my_respiratory,
            "lga_avg_respiratory": avg_respiratory,
            "my_diarrhea": my_diarrhea,
            "lga_avg_diarrhea": avg_diarrhea,
            "my_vomiting": my_vomiting,
            "lga_avg_vomiting": avg_vomiting
        }
    }
