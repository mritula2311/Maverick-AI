from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(tags=["Authentication"])


def require_role(*roles):
    """Dependency to enforce role-based access control"""
    async def check_role(current_user: User = Depends(__import__("app.api.deps", fromlist=["get_current_user"]).get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Access denied. Required role: {', '.join(roles)}")
        return current_user
    return check_role


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1440,
        "user": _user_dict(user, db),
    }


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=req.email,
        first_name=req.first_name,
        last_name=req.last_name,
        hashed_password=get_password_hash(req.password),
        role=req.role or "fresher",
        department=req.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1440,
        "user": _user_dict(user, db),
    }


@router.post("/refresh")
def refresh_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(__import__("app.api.deps", fromlist=["get_current_user"]).get_current_user),
):
    """Refresh access token"""
    token = create_access_token(data={"sub": str(current_user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1440,
    }


@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(__import__("app.api.deps", fromlist=["get_current_user"]).get_current_user),
):
    return _user_dict(current_user, db)



def _user_dict(user: User, db: Session) -> dict:
    from app.models.fresher import Fresher

    # Reuse the existing db session — never open a new SessionLocal() here
    fresher_id = None
    if user.role == "fresher":
        fresher = db.query(Fresher).filter(Fresher.user_id == user.id).first()
        if fresher:
            fresher_id = fresher.id

    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "department": user.department,
        "is_active": user.is_active,
        "fresher_id": fresher_id,
        "created_at": str(user.created_at) if user.created_at else "",
        "updated_at": str(user.updated_at) if user.updated_at else "",
    }
