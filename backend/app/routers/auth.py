from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, schemas, auth_utils
from ..db import get_db

router = APIRouter()

@router.post("/register", response_model=schemas.FacilityOut)
def register(facility: schemas.FacilityCreate, db: Session = Depends(get_db)):
    # Check if username exists
    existing = db.query(models.FacilityUser).filter(models.FacilityUser.username == facility.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create Facility (Location is now embedded or handled by string columns)
    new_facility = models.Facility(
        name=facility.name,
        type=facility.type,
        state=facility.state,
        lga=facility.lga,
        latitude=facility.latitude,
        longitude=facility.longitude
    )
    db.add(new_facility)
    db.commit()
    db.refresh(new_facility)
    
    # Create User
    hashed_password = auth_utils.get_password_hash(facility.password)
    new_user = models.FacilityUser(
        facility_id=new_facility.id,
        username=facility.username,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    
    return new_facility

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.FacilityUser).filter(models.FacilityUser.username == form_data.username).first()
    if not user or not auth_utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_utils.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "facility": user.facility}

@router.post("/reset-password")
def reset_password_admin(
    payload: schemas.PasswordReset,
    db: Session = Depends(get_db)
):
    # Simple admin protection via shared secret in request body
    # In production, use proper admin roles or API keys
    if payload.admin_secret != "phip_admin_secret_2026":
        raise HTTPException(status_code=403, detail="Invalid admin secret")
        
    user = db.query(models.FacilityUser).filter(models.FacilityUser.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    hashed_password = auth_utils.get_password_hash(payload.new_password)
    user.password_hash = hashed_password
    db.commit()
    
    return {"status": "success", "message": f"Password reset for {payload.username}"}

@router.post("/clear-facilities")
def clear_facilities_admin(
    payload: schemas.AdminAction,
    db: Session = Depends(get_db)
):
    if payload.admin_secret != "phip_admin_secret_2026":
        raise HTTPException(status_code=403, detail="Invalid admin secret")
        
    try:
        db.query(models.FacilityUser).delete()
        db.query(models.DailyReport).delete()
        db.query(models.Facility).delete()
        db.commit()
        return {"status": "success", "message": "All facilities cleared"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
