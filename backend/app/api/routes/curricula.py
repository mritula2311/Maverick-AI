import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.curriculum import Curriculum
from app.models.fresher import Fresher

router = APIRouter(tags=["Curricula"])


@router.get("")
def list_curricula(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    curricula = db.query(Curriculum).all()
    return [_curriculum_dict(c) for c in curricula]


@router.get("/fresher/{fresher_id}")
def get_fresher_curriculum(fresher_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Return the first curriculum as default assignment
    c = db.query(Curriculum).first()
    if not c:
        raise HTTPException(status_code=404, detail="No curriculum found")
    return _curriculum_dict(c)


@router.get("/{curriculum_id}")
def get_curriculum(curriculum_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Curriculum).filter(Curriculum.id == int(curriculum_id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    return _curriculum_dict(c)


def _curriculum_dict(c: Curriculum) -> dict:
    modules = []
    if c.modules:
        try:
            modules = json.loads(c.modules)
        except Exception:
            pass
    return {
        "id": str(c.id),
        "name": c.name,
        "description": c.description,
        "duration_weeks": c.duration_weeks,
        "modules": modules,
        "created_at": str(c.created_at) if c.created_at else "",
    }
