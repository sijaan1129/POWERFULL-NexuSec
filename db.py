from sqlalchemy import create_engine, Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class GuildSettings(Base):
    __tablename__ = "guild_settings"
    guild_id = Column(String, primary_key=True)
    antispam_enabled = Column(Boolean, default=False)
    antispam_punishment = Column(String, default="timeout")
    antispam_duration = Column(Integer, default=10)  # minutes
    antilink_enabled = Column(Boolean, default=False)
    antilink_punishment = Column(String, default="timeout")
    antilink_duration = Column(Integer, default=30)

def init_db():
    Base.metadata.create_all(engine)
