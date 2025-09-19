from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.models.template import Template
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateOut
from app.api.auth import require_admin  # <-- guard

router = APIRouter()

# ----- WRITE (protected) -----
@router.post("/", response_model=TemplateOut, status_code=201, dependencies=[Depends(require_admin)])
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    exists = db.query(Template).filter(Template.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="template name already exists")
    t = Template(
        name=payload.name,
        body=payload.body,
        media_refs=payload.media_refs or [],
        locale=payload.locale,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@router.patch("/{template_id}", response_model=TemplateOut, dependencies=[Depends(require_admin)])
def update_template(template_id: int, payload: TemplateUpdate, db: Session = Depends(get_db)):
    t = db.query(Template).get(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="template not found")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != t.name:
        clash = db.query(Template).filter(Template.name == data["name"]).first()
        if clash:
            raise HTTPException(status_code=409, detail="template name already exists")
    for k, v in data.items():
        setattr(t, k, v)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@router.delete("/{template_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(Template).get(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="template not found")
    db.delete(t)
    db.commit()
    return

# ----- READ (public) -----
@router.get("/", response_model=List[TemplateOut])
def list_templates(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="search by name prefix"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(Template)
    if q:
        query = query.filter(Template.name.ilike(f"{q}%"))
    return query.order_by(Template.id.desc()).offset(offset).limit(limit).all()

@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(Template).get(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="template not found")
    return t
