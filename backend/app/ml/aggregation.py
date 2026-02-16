from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models
from datetime import timedelta

def aggregate_facility_reports(db: Session, state: str, lga: str, report_date):
    """
    Aggregates all daily reports for a given location and week,
    and updates the LGAWeeklyAggregate table.
    """
    # Determine week start (Sunday)
    week_start = report_date - timedelta(days=report_date.weekday() + 1)
    if report_date.weekday() == 6: # If Sunday, it is the start
        week_start = report_date
        
    week_end = week_start + timedelta(days=6)
    
    # Fetch all reports for this location in this week
    reports = (
        db.query(models.DailyReport)
        .join(models.Facility)
        .filter(models.Facility.state == state)
        .filter(models.Facility.lga == lga)
        .filter(models.DailyReport.report_date >= week_start)
        .filter(models.DailyReport.report_date <= week_end)
        .all()
    )
    
    if not reports:
        return

    # Sum up counts
    total_fever = sum(r.fever_cases for r in reports)
    total_diarrhea = sum(r.diarrhea_cases for r in reports)
    total_vomiting = sum(r.vomiting_cases for r in reports)
    total_respiratory = sum(r.respiratory_cases for r in reports)
    total_admissions = sum(r.hospital_admissions for r in reports)
    
    # Calculate avg bed occupancy
    occupancy_rates = [r.bed_occupancy_rate for r in reports if r.bed_occupancy_rate is not None]
    avg_occupancy = sum(occupancy_rates) / len(occupancy_rates) if occupancy_rates else 0.0
    
    # Count low stock alerts
    low_stock_count = sum(1 for r in reports if r.ors_stock_level != "Normal" or r.antibiotics_stock_level != "Normal")

    # Update LGAWeeklyAggregate
    agg = db.query(models.LGAWeeklyAggregate).filter(
        models.LGAWeeklyAggregate.state == state,
        models.LGAWeeklyAggregate.lga == lga,
        models.LGAWeeklyAggregate.week_start_date == week_start
    ).first()
    
    if not agg:
        agg = models.LGAWeeklyAggregate(
            state=state,
            lga=lga,
            week_start_date=week_start
        )
        db.add(agg)
    
    agg.total_fever_cases = total_fever
    agg.total_diarrhea_cases = total_diarrhea
    agg.total_respiratory_cases = total_respiratory
    agg.total_admissions = total_admissions
    agg.avg_bed_occupancy = avg_occupancy
    agg.low_stock_alerts = low_stock_count
    
    db.commit()
