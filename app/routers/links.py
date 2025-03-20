from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import schemas, models
from app.services import create_link
from app.deps import get_db, get_current_user, get_current_user_optional
from app.config import settings
import redis
from datetime import datetime, timezone


router = APIRouter()
r = redis.Redis.from_url(settings.REDIS_URL)


@router.post("/links/shorten", response_model=schemas.LinkOut)
def shorten(link: schemas.LinkCreate, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    owner_id = user.id if user else None
    db_link = create_link(db, link, owner_id)
    r.delete(f"link:{db_link.short_code}")
    return db_link

@router.get("/links/search", response_model=list[schemas.LinkOut])
def search(original_url: str, db: Session = Depends(get_db)):
    return db.query(models.Link).filter(models.Link.original_url == original_url).all()

@router.get("/links/{short_code}")
def redirect(short_code: str, db: Session = Depends(get_db)):
    key = f"link:{short_code}"
    cached = r.hget(key, "original_url")
    if cached:
        url = cached.decode()
    else:
        link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
        if not link or (link.expires_at and link.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)):
            raise HTTPException(status_code=404, detail="Link not found")
        url = link.original_url
        r.hset(key, mapping={"original_url": url})
    db.query(models.Link).filter(models.Link.short_code == short_code).update({"clicks": models.Link.clicks + 1, "last_used": datetime.now(timezone.utc)})
    db.commit()
    return RedirectResponse(url)

@router.put("/links/{short_code}", response_model=schemas.LinkOut)
def update_link(short_code: str, update: schemas.LinkUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code, models.Link.owner_id == user.id).first()
    if not link: raise HTTPException(status_code=404)
    link.original_url = str(update.original_url)
    db.commit(); db.refresh(link)
    r.delete(f"link:{short_code}")
    return link

@router.delete("/links/{short_code}")
def delete_link(short_code: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code, models.Link.owner_id == user.id).first()
    if not link: raise HTTPException(status_code=404)
    db.delete(link); db.commit()
    r.delete(f"link:{short_code}")
    return {"detail": "Deleted"}

@router.get("/links/{short_code}/stats", response_model=schemas.LinkOut)
def stats(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link: raise HTTPException(status_code=404)
    return link
