from datetime import timedelta, date
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from .. import models
import joblib
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
os.makedirs(MODEL_DIR, exist_ok=True)

class RiskModel:
    def __init__(self, disease: str):
        self.disease = disease
        # Advanced model: Gradient Boosting Pipeline
        self.model = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
            ('classifier', GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42))
        ])
        self.is_trained = False
        self.feature_names = []
        self.metrics = {}

    def _load_raw_data(self, db: Session) -> pd.DataFrame:
        # Fetch Locations to map state/lga <-> id
        locs = db.query(models.Location).all()
        rev_loc_map = {(l.state, l.lga): l.id for l in locs}
        
        env = db.query(models.EnvMetric).all()
        dis = db.query(models.DiseaseHistory).all()
        agg = db.query(models.LGAWeeklyAggregate).all()

        if not env or not agg or not dis:
            return pd.DataFrame()

        # Convert to DF
        env_df = pd.DataFrame([{
            "location_id": e.location_id,
            "week_start": e.week_start,
            "rainfall_mm": e.rainfall_mm or 0.0,
            "temperature_c": e.temperature_c or 0.0,
            "humidity_pct": e.humidity_pct or 0.0,
            "flood_risk": e.flood_risk or 0.0,
        } for e in env])

        # Map LGAWeeklyAggregate to location_id
        agg_data = []
        for a in agg:
            lid = rev_loc_map.get((a.state, a.lga))
            if lid:
                agg_data.append({
                    "location_id": lid,
                    "week_start": a.week_start_date,
                    "fever_reports": a.total_fever_cases,
                    "cough_reports": a.total_respiratory_cases, # Mapping respiratory -> cough for model compatibility
                    "diarrhea_reports": a.total_diarrhea_cases,
                    "vomiting_reports": 0, # Note: vomiting removed from schema, defaulted to 0
                    # "pharmacy_sales_fever": 0, # Not in LGAWeeklyAggregate yet
                    # "pharmacy_sales_antibiotics": 0,
                    # "pharmacy_sales_antimalarials": 0,
                    # "absenteeism_rate": 0.0, 
                    "admissions": a.total_admissions,
                    "bed_occupancy": a.avg_bed_occupancy
                })
        
        if not agg_data:
            return pd.DataFrame()
            
        agg_df = pd.DataFrame(agg_data)

        dis_df = pd.DataFrame([{
            "location_id": d.location_id,
            "week_start": d.week_start,
            "cholera_cases": d.cholera_cases or 0,
            "malaria_cases": d.malaria_cases or 0,
            "lassa_cases": d.lassa_cases or 0,
            "meningitis_cases": d.meningitis_cases or 0,
        } for d in dis])

        # Merge
        df = env_df.merge(agg_df, on=["location_id", "week_start"], how="outer").merge(
            dis_df, on=["location_id", "week_start"], how="outer"
        )
        
        # Ensure proper types
        df['week_start'] = pd.to_datetime(df['week_start'])
        df = df.sort_values(['location_id', 'week_start']).reset_index(drop=True)
        return df

    def _feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Handle missing values
        df = df.sort_values(['location_id', 'week_start'])
        
        cols_to_fill = [c for c in df.columns if c not in ['location_id', 'week_start']]
        for c in cols_to_fill:
            df[c] = df.groupby('location_id')[c].ffill().fillna(0)
            
        disease_col = f"{self.disease}_cases"
        if disease_col not in df.columns:
            df[disease_col] = 0

        # 2. Create Temporal Features
        df['week_of_year'] = df['week_start'].dt.isocalendar().week.astype(int)
        df['month'] = df['week_start'].dt.month
        df['is_rainy_season'] = df['month'].between(4, 10).astype(int)

        # 3. Create Lag Features (t-1, t-2, t-3)
        lags = [1, 2, 3]
        # Added 'admissions' and 'bed_occupancy' to lag features if available
        lag_cols = [disease_col, 'rainfall_mm', 'fever_reports']
        if 'admissions' in df.columns:
            lag_cols.append('admissions')
        
        for col in lag_cols:
            if col in df.columns:
                for lag in lags:
                    df[f'{col}_lag{lag}'] = df.groupby('location_id')[col].shift(lag)

        # 4. Create Rolling Features (4-week average)
        df[f'{disease_col}_rolling_4w'] = df.groupby('location_id')[disease_col].transform(
            lambda x: x.shift(1).rolling(window=4).mean()
        )
        
        # 5. Trend Features (Growth rate)
        df[f'{disease_col}_growth'] = df.groupby('location_id')[disease_col].pct_change().replace([np.inf, -np.inf], 0).fillna(0)
        df['fever_growth'] = df.groupby('location_id')['fever_reports'].pct_change().replace([np.inf, -np.inf], 0).fillna(0)

        # 6. Target Variable: Outbreak in 2 weeks (t+2)
        df['threshold'] = df.groupby('location_id')[disease_col].transform(
            lambda x: x.rolling(window=26, min_periods=5).quantile(0.75)
        )
        df['threshold'] = df['threshold'].clip(lower=5)
        df['is_outbreak'] = (df[disease_col] > df['threshold']).astype(int)
        df['target'] = df.groupby('location_id')['is_outbreak'].shift(-2)
        
        df = df.dropna(subset=['target'])
        
        return df

    def train(self, db: Session):
        raw_df = self._load_raw_data(db)
        if raw_df.empty:
            print("No data to train")
            return

        df = self._feature_engineering(raw_df)
        
        exclude_cols = ['location_id', 'week_start', 'threshold', 'is_outbreak', 'target']
        feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in [np.float64, np.int64]]
        self.feature_names = feature_cols

        X = df[feature_cols].values
        y = df['target'].values

        if len(np.unique(y)) < 2:
            print("Not enough classes to train")
            return

        tscv = TimeSeriesSplit(n_splits=3)
        for train_index, test_index in tscv.split(X):
            X_train, X_test = X[train_index], X[test_index]
            y_train, y_test = y[train_index], y[test_index]
            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_test)
            y_prob = self.model.predict_proba(X_test)[:, 1]
            self.metrics = {
                "auc": roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else 0.0,
                "precision": precision_score(y_test, y_pred, zero_division=0),
                "recall": recall_score(y_test, y_pred, zero_division=0),
                "f1": f1_score(y_test, y_pred, zero_division=0)
            }

        self.model.fit(X, y)
        self.is_trained = True
        
        model_path = os.path.join(MODEL_DIR, f"{self.disease}_model.joblib")
        joblib.dump(self.model, model_path)
        print(f"Model trained and saved to {model_path}. Metrics: {self.metrics}")

    def load(self):
        model_path = os.path.join(MODEL_DIR, f"{self.disease}_model.joblib")
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            self.is_trained = True
            
    def predict_full(self, features: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_trained:
            self.load()
            if not self.is_trained:
                return {"risk_score": 0.0, "risk_level": "Low", "top_factors": ["Model not trained"]}

        input_df = pd.DataFrame([features])
        for col in self.feature_names:
            if col not in input_df.columns:
                input_df[col] = 0.0
                
        X_pred = input_df[self.feature_names].values
        risk_score = self.model.predict_proba(X_pred)[0][1]
        
        if risk_score >= 0.7:
            level = "High"
        elif risk_score >= 0.3:
            level = "Medium"
        else:
            level = "Low"
            
        clf = self.model.named_steps['classifier']
        importances = clf.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        top_factors = []
        for i in range(min(3, len(indices))):
            idx = indices[i]
            feat_name = self.feature_names[idx]
            importance = importances[idx]
            if importance > 0.01:
                readable = feat_name.replace("_", " ").title()
                val = features.get(feat_name, 0)
                top_factors.append(f"{readable} ({val:.1f})")
                
        return {
            "risk_score": float(risk_score),
            "risk_level": level,
            "top_factors": top_factors,
            "metrics": self.metrics
        }

    def predict_score(self, features: Dict[str, float]) -> float:
        res = self.predict_full(features)
        return res["risk_score"]

def risk_category(score: float) -> str:
    if score >= 0.7:
        return "High"
    if score >= 0.3:
        return "Medium"
    return "Low"

def build_feature_vector(db: Session, location_id: int, week_start: date) -> Dict[str, float]:
    start_date = week_start - timedelta(weeks=5)
    
    # Resolve location
    loc = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not loc:
        return {}

    def fetch_window(model):
        return db.query(model).filter(
            model.location_id == location_id,
            model.week_start >= start_date,
            model.week_start <= week_start
        ).all()
    
    def fetch_agg_window():
        return db.query(models.LGAWeeklyAggregate).filter(
            models.LGAWeeklyAggregate.state == loc.state,
            models.LGAWeeklyAggregate.lga == loc.lga,
            models.LGAWeeklyAggregate.week_start_date >= start_date,
            models.LGAWeeklyAggregate.week_start_date <= week_start
        ).all()
        
    env = fetch_window(models.EnvMetric)
    dis = fetch_window(models.DiseaseHistory)
    agg = fetch_agg_window()
    
    data = []
    dates = set()
    for l in [env, dis]:
        for i in l:
            dates.add(i.week_start)
    for a in agg:
        dates.add(a.week_start_date)
    
    sorted_dates = sorted(list(dates))
    if not sorted_dates:
        return {}
    
    records = []
    for d in sorted_dates:
        rec = {"location_id": location_id, "week_start": d}
        e = next((x for x in env if x.week_start == d), None)
        c = next((x for x in agg if x.week_start_date == d), None)
        dh = next((x for x in dis if x.week_start == d), None)
        
        if e:
            rec.update({k: getattr(e, k) for k in ["rainfall_mm", "temperature_c", "humidity_pct", "flood_risk"] if getattr(e, k) is not None})
        if c:
            rec.update({
                "fever_reports": c.total_fever_cases,
                "cough_reports": c.total_respiratory_cases,
                "diarrhea_reports": c.total_diarrhea_cases,
                "vomiting_reports": 0, # Defaulted to 0
                "admissions": c.total_admissions,
                "bed_occupancy": c.avg_bed_occupancy
            })
        if dh:
            rec.update({k: getattr(dh, k) for k in ["cholera_cases", "malaria_cases", "lassa_cases", "meningitis_cases"] if getattr(dh, k) is not None})
        records.append(rec)
        
    df = pd.DataFrame(records).fillna(0)
    
    # Feature Engineering
    df['week_start'] = pd.to_datetime(df['week_start'])
    df['week_of_year'] = df['week_start'].dt.isocalendar().week.astype(int)
    df['month'] = df['week_start'].dt.month
    df['is_rainy_season'] = df['month'].between(4, 10).astype(int)
    
    diseases = ["cholera_cases", "malaria_cases", "lassa_cases", "meningitis_cases"]
    cols_to_lag = diseases + ['rainfall_mm', 'fever_reports']
    if 'admissions' in df.columns:
        cols_to_lag.append('admissions')
    
    for col in cols_to_lag:
        if col not in df.columns:
            df[col] = 0
            
    for col in cols_to_lag:
        if col in df.columns:
            for lag in [1, 2, 3]:
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
            
    for d_col in diseases:
        df[f'{d_col}_rolling_4w'] = df[d_col].shift(1).rolling(window=4).mean()
        df[f'{d_col}_growth'] = df[d_col].pct_change().replace([np.inf, -np.inf], 0).fillna(0)
        
    df['fever_growth'] = df['fever_reports'].pct_change().replace([np.inf, -np.inf], 0).fillna(0)
    
    # Extract last row
    if df.empty:
        return {}
        
    last_row = df.iloc[-1]
    return last_row.to_dict()
