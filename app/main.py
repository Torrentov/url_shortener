from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, links


Base.metadata.create_all(bind=engine)
app = FastAPI(title="URL Shortener Service")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(links.router, tags=["links"])
