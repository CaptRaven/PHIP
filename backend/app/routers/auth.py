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
