import sys
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, auth_utils

def reset_password(username: str, new_password: str):
    db: Session = SessionLocal()
    try:
        user = db.query(models.FacilityUser).filter(models.FacilityUser.username == username).first()
        if not user:
            print(f"User '{username}' not found.")
            return

        print(f"Resetting password for user: {username}")
        hashed_password = auth_utils.get_password_hash(new_password)
        user.password_hash = hashed_password
        db.commit()
        print("Password updated successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error resetting password: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.reset_password <username> <new_password>")
        sys.exit(1)
    
    reset_password(sys.argv[1], sys.argv[2])
