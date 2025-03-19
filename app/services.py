from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.utils import generate_short_code
from app.config import settings
from datetime import datetime


def create_link(db: Session, link: schemas.LinkCreate, user_id: int):
    if link.custom_alias:
        if db.query(models.Link).filter(models.Link.short_code == link.custom_alias).first():
            raise HTTPException(status_code=400, detail="Custom alias already in use")
        code = link.custom_alias
    else:
        code = generate_short_code()
        attempt = 1
        while db.query(models.Link).filter(models.Link.short_code == code).first():
            if attempt >= settings.SHORT_CODE_MAX_ATTEMPTS:
                raise HTTPException(status_code=500, detail="Could not generate unique short code")
            code = generate_short_code()
            attempt += 1

    db_link = models.Link(
        short_code=code,
        original_url=str(link.original_url),
        owner_id=user_id,
        expires_at=link.expires_at
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link
