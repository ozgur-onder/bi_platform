# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import ayarlar

# Async bağlantı motoru
engine = create_async_engine(
    ayarlar.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

# Her istek için oturum fabrikası
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Tüm modeller bu Base'den türeyecek
class Base(DeclarativeBase):
    pass

# Endpoint'lerde kullanılacak bağımlılık (dependency)
async def db_oturumu():
    async with AsyncSessionLocal() as oturum:
        try:
            yield oturum
            await oturum.commit()
        except Exception:
            await oturum.rollback()
            raise