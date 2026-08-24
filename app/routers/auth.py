from fastapi import APIRouter, Request, Form, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
import secrets
from datetime import datetime, timedelta
import zoneinfo 
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.core.mailer import reset_maili_gonder

router = APIRouter()

# Ortak IP alma fonksiyonu
def get_ip(request: Request):
    try:
        ip = request.headers.get("X-Forwarded-For")
        if not ip:
            ip = request.client.host if request.client else "127.0.0.1"
        return ip.split(",")[0].strip()
    except:
        return "Bilinmiyor"

@router.post("/giris-yap")
def giris_islemi(
    request: Request,
    kullanici_adi: str = Form(...),
    sifre: str = Form(...),
    db: Session = Depends(get_db)
):
    ip_adresi = get_ip(request)
    tarayici = request.headers.get("user-agent", "Bilinmiyor")[:255]
    
    basarisiz = db.execute(
        text("SELECT COUNT(*) FROM kullanici_giris_loglari WHERE ip_adresi = :ip AND durum = 'Başarısız' AND islem_zamani >= NOW() - INTERVAL '15 minutes'"),
        {"ip": ip_adresi}
    ).scalar()

    if basarisiz >= 5:
        raise HTTPException(status_code=429, detail="Çok fazla hatalı deneme yaptınız. Lütfen 15 dakika bekleyin.")
    
    kullanici = db.execute(text("SELECT sicil, parola FROM kullanicilar WHERE sicil = :sicil"), {"sicil": kullanici_adi}).fetchone()
    
    if not kullanici or not verify_password(sifre, kullanici.parola):
        db.execute(text("INSERT INTO kullanici_giris_loglari (sicil, durum, ip_adresi, tarayici, hata_mesaji) VALUES (:sicil, 'Başarısız', :ip, :tarayici, 'Hatalı şifre')"), {"sicil": kullanici_adi, "ip": ip_adresi, "tarayici": tarayici})
        db.commit()
        raise HTTPException(status_code=401, detail="Hatalı sicil numarası veya şifre.")
        
    oturum_token = secrets.token_hex(32)
    
    db.execute(text("INSERT INTO kullanici_giris_loglari (sicil, durum, ip_adresi, tarayici) VALUES (:sicil, 'Başarılı', :ip, :tarayici)"), {"sicil": kullanici_adi, "ip": ip_adresi, "tarayici": tarayici})
    db.execute(text("INSERT INTO kullanici_oturumlari (sicil, oturum_token, ip_adresi, tarayici, durum) VALUES (:sicil, :token, :ip, :tarayici, 'aktif')"), {"sicil": kullanici_adi, "token": oturum_token, "ip": ip_adresi, "tarayici": tarayici})
    
    db.commit()
    return {"mesaj": "Giriş başarılı."}

@router.post("/sifre-sifirlama-talep")
def sifre_sifirlama_talep(
    request: Request,
    background_tasks: BackgroundTasks,
    sicil: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    ip_adresi = get_ip(request)
    kullanici = db.execute(text("SELECT sicil FROM kullanicilar WHERE sicil = :sicil AND email = :email"), {"sicil": sicil, "email": email}).fetchone()

    if kullanici:
        token = secrets.token_urlsafe(64)
        gecerlilik = datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul")) + timedelta(hours=1)
        
        db.execute(text("INSERT INTO sifre_sifirlama_talepleri (sicil, token, gecerlilik_suresi, ip_adresi) VALUES (:sicil, :token, :gecerlilik, :ip)"), {"sicil": sicil, "token": token, "gecerlilik": gecerlilik, "ip": ip_adresi})
        db.commit()

        reset_link = f"http://127.0.0.1:8000/bilesen/sifre-sifirla?token={token}"
        
        print(f"\n=======================================================")
        print(f"ŞİFRE SIFIRLAMA LİNKİ (Kullanıcı: {sicil})")
        print(reset_link)
        print(f"=======================================================\n")
        
        # SİLDİĞİMİZ MAİL GÖNDERME KODU GERİ GELDİ!
        background_tasks.add_task(reset_maili_gonder, email, reset_link)
        
    return {"mesaj": "Sıfırlama bağlantısı e-posta adresinize gönderildi."}

@router.post("/yeni-sifre-belirle")
def yeni_sifre_belirle(
    request: Request,
    token: str = Form(...),
    yeni_sifre: str = Form(...),
    db: Session = Depends(get_db)
):
    ip_adresi = get_ip(request)
    
    talep = db.execute(text("SELECT id, sicil, gecerlilik_suresi FROM sifre_sifirlama_talepleri WHERE token = :token AND kullanildi = FALSE"), {"token": token}).fetchone()

    if not talep:
        raise HTTPException(status_code=400, detail="Geçersiz veya kullanılmış şifre sıfırlama bağlantısı.")

    if datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul")) > talep.gecerlilik_suresi:
        raise HTTPException(status_code=400, detail="Şifre sıfırlama bağlantısının süresi dolmuş.")

    hashed_sifre = get_password_hash(yeni_sifre)
    db.execute(text("UPDATE kullanicilar SET parola = :sifre WHERE sicil = :sicil"), {"sifre": hashed_sifre, "sicil": talep.sicil})
    db.execute(text("UPDATE sifre_sifirlama_talepleri SET kullanildi = TRUE WHERE id = :id"), {"id": talep.id})
    db.execute(text("INSERT INTO kullanici_sifre_degisim_loglari (sicil, tur, talep_eden_kullanici_sicil, ip_adresi) VALUES (:sicil, 'Şifremi Unuttum', :sicil, :ip)"), {"sicil": talep.sicil, "ip": ip_adresi})

    db.commit()
    return {"mesaj": "Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz."}