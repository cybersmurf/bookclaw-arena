import asyncio
from app.database import SessionLocal
from app import models

db = SessionLocal()
authors = db.query(models.Author).all()
critics = db.query(models.Critic).all()
world = db.query(models.World).first()
print("AUTHORS:", len(authors), "CRITICS:", len(critics), "WORLD:", world.id if world else None)
