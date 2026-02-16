from sqlalchemy.orm import Session
from datetime import date
from .. import models

def evaluate_alerts(db: Session, location_id: int, disease: str, base_week: date, risk_score: float):
    if risk_score > 0.7:
        level = "High"
        msg = f"High {disease} outbreak risk in next weeks"
        alert = models.Alert(
            location_id=location_id,
            created_at_week=base_week,
            disease=disease,
            level=level,
            message=msg,
            risk_score=risk_score,
        )
        db.add(alert)
        db.commit()
        return
    # Early warning: rapid increase in fever + rainfall spike
    # Compare last two weeks fever and rainfall
    envs = (
        db.query(models.EnvMetric)
        .filter(models.EnvMetric.location_id == location_id)
        .order_by(models.EnvMetric.week_start.desc())
        .limit(2)
        .all()
    )
    comms = (
        db.query(models.CommunitySignal)
        .filter(models.CommunitySignal.location_id == location_id)
        .order_by(models.CommunitySignal.week_start.desc())
        .limit(2)
        .all()
    )
    if len(envs) == 2 and len(comms) == 2:
        rainfall_spike = (envs[0].rainfall_mm or 0) > (envs[1].rainfall_mm or 0) * 1.3
        fever_spike = (comms[0].fever_reports or 0) > (comms[1].fever_reports or 0) * 1.5
        if rainfall_spike and fever_spike:
            alert = models.Alert(
                location_id=location_id,
                created_at_week=base_week,
                disease=disease,
                level="EarlyWarning",
                message="Early warning: fever increase and rainfall spike detected",
                risk_score=risk_score,
            )
            db.add(alert)
            db.commit()
