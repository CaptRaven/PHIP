import sys
import os

# Add /app to path (Docker container path)
sys.path.append('/app')
# Also add parent directory for local execution
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import random
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app import models

N_WEEKS = 260  # 5 years
STATES_LGAS = [
    ("Kano", "Kano Municipal", 12.0000, 8.5167),
    ("Lagos", "Ikeja", 6.6018, 3.3515),
    ("Kaduna", "Zaria", 11.0667, 7.7167),
    ("Rivers", "Port Harcourt", 4.8242, 7.0336),
    ("Kano", "Nassarawa", 12.0100, 8.5300), # Adding the location of our test user
]

def seed_locations(db: Session):
    for state, lga, lat, lon in STATES_LGAS:
        existing = db.query(models.Location).filter(models.Location.state == state, models.Location.lga == lga).first()
        if not existing:
            loc = models.Location(state=state, lga=lga, latitude=lat, longitude=lon)
            db.add(loc)
    db.commit()

def generate(db: Session):
    Base.metadata.create_all(bind=engine)
    seed_locations(db)
    
    # Clear existing data to avoid conflicts when regenerating
    db.query(models.EnvMetric).delete()
    db.query(models.LGAWeeklyAggregate).delete() # Updated from CommunitySignal
    db.query(models.DiseaseHistory).delete()
    db.query(models.RiskPrediction).delete() # Updated from Prediction
    db.query(models.Alert).delete()
    db.commit()

    today = date.today()
    start_week = today - timedelta(days=7 * N_WEEKS)
    
    for loc in db.query(models.Location).all():
        # Generate base signals
        rainfall = []
        temperature = []
        
        # Simple seasonality simulation
        for i in range(N_WEEKS):
            week_of_year = (i % 52)
            is_rainy = 15 <= week_of_year <= 40
            
            # Rain: higher in rainy season
            base_rain = 150 if is_rainy else 10
            rain_val = max(0, random.gauss(base_rain, 30))
            rainfall.append(rain_val)
            
            # Temp: cooler in rainy season
            base_temp = 25 if is_rainy else 32
            temp_val = max(15, random.gauss(base_temp, 3))
            temperature.append(temp_val)

        humidity = [min(100, max(20, r * 0.4 + 40 + random.uniform(-5, 5))) for r in rainfall]
        flood_risk = [min(1.0, r / 250.0) for r in rainfall]

        # Community signals influenced by environment
        fever = [int(max(0, random.gauss(20, 5) + (r / 20))) for r in rainfall] 
        respiratory = [int(max(0, random.gauss(15, 4))) for _ in range(N_WEEKS)] # Renamed from cough
        diarrhea = [int(max(0, random.gauss(10, 3) + (f / 30) + (r/50))) for f, r in zip(fever, rainfall)] 
        vomiting = [int(max(0, random.gauss(5, 2))) for _ in range(N_WEEKS)]
        
        # New aggregates for LGAWeeklyAggregate
        admissions = [int(max(0, f * 0.05 + random.uniform(0, 2))) for f in fever]
        bed_occupancy = [min(100, max(20, 40 + (f/2))) for f in fever]
        low_stock = [int(max(0, random.choice([0, 0, 0, 1, 2]))) for _ in range(N_WEEKS)]

        # Disease outcomes
        cholera = []
        malaria = []
        lassa = []
        meningitis = []
        
        for i in range(N_WEEKS):
            # Cholera spikes with high rain and diarrhea
            c_risk = (rainfall[i] > 100) and (diarrhea[i] > 20)
            c_cases = int(random.gauss(50, 15)) if c_risk else int(max(0, random.gauss(2, 2)))
            cholera.append(c_cases)
            
            # Malaria follows fever and rain
            m_cases = int(max(0, fever[i] * 0.6 + random.gauss(0, 5)))
            malaria.append(m_cases)
            
            # Lassa random but seasonal (dry season usually)
            is_dry = rainfall[i] < 50
            l_cases = int(max(0, random.gauss(10, 3))) if is_dry else int(max(0, random.gauss(1, 1)))
            lassa.append(l_cases)
            
            # Meningitis (dry season, heat)
            is_hot_dry = (temperature[i] > 30) and (rainfall[i] < 20)
            men_cases = int(max(0, random.gauss(20, 5))) if is_hot_dry else int(max(0, random.gauss(0, 1)))
            meningitis.append(men_cases)

        # Bulk insert
        for i in range(N_WEEKS):
            week = start_week + timedelta(days=7 * i)

            db.add(models.EnvMetric(
                location_id=loc.id,
                week_start=week,
                rainfall_mm=float(rainfall[i]),
                temperature_c=float(temperature[i]),
                humidity_pct=float(humidity[i]),
                flood_risk=float(flood_risk[i]),
            ))
            
            # Populate new LGAWeeklyAggregate instead of CommunitySignal
            db.add(models.LGAWeeklyAggregate(
                lga=loc.lga,
                state=loc.state,
                week_start_date=week,
                total_fever_cases=int(fever[i]),
                total_respiratory_cases=int(respiratory[i]),
                total_diarrhea_cases=int(diarrhea[i]),
                # total_vomiting_cases=int(vomiting[i]), # Removed as it's not in the model
                total_admissions=int(admissions[i]),
                avg_bed_occupancy=float(bed_occupancy[i]),
                low_stock_alerts=int(low_stock[i])
            ))
            
            db.add(models.DiseaseHistory(
                location_id=loc.id,
                week_start=week,
                cholera_cases=int(cholera[i]),
                malaria_cases=int(malaria[i]),
                lassa_cases=int(lassa[i]),
                meningitis_cases=int(meningitis[i]),
            ))
        db.commit()

    # Run initial prediction for the latest week so the heatmap is populated immediately
    from app.routers.predictions import get_model, evaluate_alerts
    from app.ml.model import build_feature_vector, risk_category
    
    print("Generating initial predictions...")
    for loc in db.query(models.Location).all():
        latest_week_rec = (
            db.query(models.DiseaseHistory.week_start)
            .filter(models.DiseaseHistory.location_id == loc.id)
            .order_by(models.DiseaseHistory.week_start.desc())
            .first()
        )
        base_week = latest_week_rec[0] if latest_week_rec else date.today()
        features = build_feature_vector(db, loc.id, base_week)
        
        for disease in ["cholera", "malaria", "lassa", "meningitis"]:
            model = get_model(disease, db)
            result = model.predict_full(features)
            
            pred = models.RiskPrediction(
                state=loc.state,
                lga=loc.lga,
                prediction_date=base_week,
                weeks_ahead=2,
                risk_score=result["risk_score"],
                risk_level=result["risk_level"],
                disease=disease,
                top_factors=result["top_factors"]
            )
            db.add(pred)
            evaluate_alerts(db, loc.id, disease, base_week, result["risk_score"])
            
    db.commit()
    print("Initial predictions generated.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        generate(db)
        print("Data generation completed successfully.")
    except Exception as e:
        print(f"Error generating data: {e}")
    finally:
        db.close()
