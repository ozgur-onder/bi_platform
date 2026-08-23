from fastapi import APIRouter, Request, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import secrets
from datetime import datetime, timedelta
import zoneinfo 
from app.core.database import get_db
from app.core.security import verify_password

router = APIRouter()

@router.post("/giris-yap")
async def giris_islemi(
    request: Request,
    kullanici_adi: str = Form(...),
    sifre: str = Form(...),
    db: Session = Depends(get_db)
):
    ip_adresi = request.headers.get("X-Forwarded-For", request.client.host)
    if ip_adresi:
        ip_adresi = ip_adresi.split(",")[0].strip()
        
    tarayici = request.headers.get("user-agent")[:255] if request.headers.get("user-agent") else "Bilinmiyor"
    
    basarisiz_denemeler = db.execute(
        text("SELECT COUNT(*) FROM kullanici_giris_loglari WHERE ip_adresi = :ip AND durum = 'Başarısız' AND islem_zamani >= NOW() - INTERVAL '15 minutes'"),
        {"ip": ip_adresi}
    ).scalar()

    if basarisiz_denemeler >= 5:
        raise HTTPException(status_code=429, detail="Çok fazla hatalı deneme yaptınız. Lütfen 15 dakika bekleyin.")
    
    kullanici = db.execute(
        text("SELECT sicil, parola FROM kullanicilar WHERE sicil = :sicil"),
        {"sicil": kullanici_adi}
    ).fetchone()
    
    if not kullanici:
        raise HTTPException(status_code=401, detail="Hatalı sicil numarası veya şifre.")

    if not verify_password(sifre, kullanici.parola):
        db.execute(
            text("INSERT INTO kullanici_giris_loglari (sicil, durum, ip_adresi, tarayici, hata_mesaji) VALUES (:sicil, 'Başarısız', :ip, :tarayici, 'Hatalı şifre')"),
            {"sicil": kullanici_adi, "ip": ip_adresi, "tarayici": tarayici}
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Hatalı sicil numarası veya şifre.")
        
    oturum_token = secrets.token_hex(32)
    
    db.execute(
        text("INSERT INTO kullanici_giris_loglari (sicil, durum, ip_adresi, tarayici) VALUES (:sicil, 'Başarılı', :ip, :tarayici)"),
        {"sicil": kullanici_adi, "ip": ip_adresi, "tarayici": tarayici}
    )
    
    db.execute(
        text("INSERT INTO kullanici_oturumlari (sicil, oturum_token, ip_adresi, tarayici, durum) VALUES (:sicil, :token, :ip, :tarayici, 'aktif')"),
        {"sicil": kullanici_adi, "token": oturum_token, "ip": ip_adresi, "tarayici": tarayici}
    )
    
    db.commit()
    return {"mesaj": "Giriş başarılı."}

@router.post("/sifre-sifirlama-talep")
async def sifre_sifirlama_talep(
    request: Request,
    sicil: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    ip_adresi = request.headers.get("X-Forwarded-For", request.client.host)
    if ip_adresi:
        ip_adresi = ip_adresi.split(",")[0].strip()

    kullanici = db.execute(
        text("SELECT sicil FROM kullanicilar WHERE sicil = :sicil AND email = :email"),
        {"sicil": sicil, "email": email}
    ).fetchone()

    if kullanici:
        token = secrets.token_urlsafe(64)
        gecerlilik = datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul")) + timedelta(hours=1)
        
        db.execute(
            text("INSERT INTO sifre_sifirlama_talepleri (sicil, token, gecerlilik_suresi, ip_adresi) VALUES (:sicil, :token, :gecerlilik, :ip)"),
            {"sicil": sicil, "token": token, "gecerlilik": gecerlilik, "ip": ip_adresi}
        )
        db.commit()

        print(f"\n=======================================================")
        print(f"SIFRE SIFIRLAMA LINKI (Kullanici: {sicil})")
        print(f"http://127.0.0.1:8000/sifre-sifirla?token={token}")
        print(f"=======================================================\n")

    return {"mesaj": "Sıfırlama bağlantısı e-posta adresinize gönderildi."}