from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Form, Request
from sqlalchemy.orm import Session
from datetime import datetime, date
import re
from typing import Optional
from .. import models, db
from ..ml.aggregation import aggregate_facility_reports

router = APIRouter()

# Regex pattern for SMS parsing
# Format: ID#DATE#F..#D..#V..#R..#A..#SD..#BO..#ORS..#AB..
# Example: PHC123#2026-02-09#F23#D10#V5#R12#A6#SD2#BO78#ORSLOW#ABNORM

def process_sms_logic(text: str, db: Session, background_tasks: BackgroundTasks):
    """
    Shared logic to process SMS text and store report.
    """
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty message")

    # 1. Parse content
    try:
        parts = text.split("#")
        if len(parts) < 3:
            raise ValueError("Invalid format. Use ID#DATE#DATA...")
            
        fac_username = parts[0].strip()
        report_date_str = parts[1].strip()
        
        # Parse Date
        try:
            report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

        # Parse Data Fields
        data_map = {}
        
        for part in parts[2:]:
            part = part.upper().strip()
            if part.startswith("F"):
                data_map["fever_cases"] = int(re.findall(r'\d+', part)[0])
            elif part.startswith("D"):
                data_map["diarrhea_cases"] = int(re.findall(r'\d+', part)[0])
            elif part.startswith("V"):
                data_map["vomiting_cases"] = int(re.findall(r'\d+', part)[0])
            elif part.startswith("R"):
                data_map["respiratory_cases"] = int(re.findall(r'\d+', part)[0])
            elif part.startswith("A") and not part.startswith("AB"): # A vs AB
                data_map["hospital_admissions"] = int(re.findall(r'\d+', part)[0])
            elif part.startswith("SD"):
                data_map["severe_dehydration_cases"] = int(re.findall(r'\d+', part)[0])
            elif part.startswith("BO"):
                data_map["bed_occupancy_rate"] = float(re.findall(r'\d+', part)[0])
            elif part.startswith("ORS"):
                val = part[3:] # Remove ORS
                data_map["ors_stock_level"] = "Low" if "LOW" in val else "Out" if "OUT" in val else "Normal"
            elif part.startswith("AB"):
                val = part[2:] # Remove AB
                data_map["antibiotics_stock_level"] = "Low" if "LOW" in val else "Out" if "OUT" in val else "Normal"
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parsing error: {str(e)}")

    # 2. Validate Facility
    user = db.query(models.FacilityUser).filter(models.FacilityUser.username == fac_username).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Facility User '{fac_username}' not found")
        
    facility = user.facility
    if not facility:
        raise HTTPException(status_code=404, detail="Facility profile not found")

    # 3. Store Report
    existing = db.query(models.DailyReport).filter(
        models.DailyReport.facility_id == facility.id,
        models.DailyReport.report_date == report_date
    ).first()
    
    if existing:
        for k, v in data_map.items():
            setattr(existing, k, v)
        # Append note if it's not already there to avoid dupes
        note_append = " [SMS Updated]"
        if existing.notes:
            if note_append not in existing.notes:
                existing.notes = existing.notes + note_append
        else:
            existing.notes = "[SMS Submission]"
        db.commit()
    else:
        new_report = models.DailyReport(
            facility_id=facility.id,
            report_date=report_date,
            notes="[SMS Submission]",
            **data_map
        )
        db.add(new_report)
        db.commit()
        
    # 4. Trigger Aggregation
    background_tasks.add_task(aggregate_facility_reports, db, facility.state, facility.lga, report_date)
    
    return {"status": "success", "message": "Report processed successfully"}

@router.post("/ingest")
def ingest_sms(
    body: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(db.get_db)
):
    """
    Ingests a structured SMS message via JSON body (Generic Webhook).
    """
    text = body.get("text", "")
    return process_sms_logic(text, db, background_tasks)

@router.post("/twilio")
async def ingest_twilio_sms(
    background_tasks: BackgroundTasks,
    From: Optional[str] = Form(None),
    Body: str = Form(...),
    db: Session = Depends(db.get_db)
):
    """
    Ingests an SMS message specifically from Twilio Webhook.
    Twilio sends data as application/x-www-form-urlencoded.
    """
    # We can use 'From' to validate sender if we had a registry of phone numbers.
    # For now, we rely on the username in the Body string.
    try:
        process_sms_logic(Body, db, background_tasks)
        # Twilio expects TwiML XML response or empty 200 OK.
        # We'll return a simple XML to confirm receipt or just 200.
        # For simplicity, we return plain text which Twilio logs.
        # Ideally return: Response(content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>", media_type="application/xml")
        return "SMS Received"
    except HTTPException as e:
        return f"Error: {e.detail}"
    except Exception as e:
        return f"System Error: {str(e)}"
