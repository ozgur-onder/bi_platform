from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# docker-compose.yml ayarlarına göre tam eşleşen bağlantı adresi
SQLALCHEMY_DATABASE_URL = "postgresql://ozgur.onder:BZrf5399!@localhost:5880/bi_veritabani"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()