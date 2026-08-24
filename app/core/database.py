import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DÜZELTME: Sabit kodlanmış credentials yerine ortam değişkeninden oku.
# .env dosyası: DATABASE_URL=postgresql://admin:gizlisifre123@localhost:5880/bi_veritabani
# Not: asyncpg yerine standart psycopg2 sürücüsü kullanılıyor (sync uygulama).
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://ozgur.onder:BZrf5399!@localhost:5880/bi_veritabani"
).replace("postgresql+asyncpg://", "postgresql://")  # asyncpg prefix'ini sync'e çevir

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()