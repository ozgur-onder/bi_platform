from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import secrets
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db

app = FastAPI(title="İş Zekası Platformu")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".")

# --- ŞİFRELEME (HASH) YAPILANDIRMASI ---
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)

@app.get("/", response_class=HTMLResponse)
async def ana_sayfa(request: Request, db: Session = Depends(get_db)):
    kullanici_sayisi = db.execute(text("SELECT COUNT(*) FROM kullanicilar")).scalar()
    
    if kullanici_sayisi == 0:
        return templates.TemplateResponse(request=request, name="sayfalar/kurulum.html")
    
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/bilesen/{sayfa_adi}", response_class=HTMLResponse)
async def bilesen_getir(request: Request, sayfa_adi: str):
    if sayfa_adi == "index":
        return RedirectResponse(url="/")
    
    dosya_yolu = f"sayfalar/{sayfa_adi}.html"
    if os.path.exists(dosya_yolu):
        return templates.TemplateResponse(request=request, name=dosya_yolu)
    
    return HTMLResponse(content="Sayfa bulunamadı.", status_code=404)

@app.post("/kurulum-tamamla")
async def kurulum_yap(
    request: Request,
    ad: str = Form(...),
    soyad: str = Form(...),
    sicil_no: str = Form(...),
    email: str = Form(...),
    sifre: str = Form(...),
    db: Session = Depends(get_db)
):
    sayi = db.execute(text("SELECT COUNT(*) FROM kullanicilar")).scalar()
    if sayi > 0:
        raise HTTPException(status_code=400, detail="Sistem zaten kurulu.")
        
    hashed_sifre = get_password_hash(sifre)
        
    db.execute(
        text("INSERT INTO kullanicilar (sicil, ad, soyad, email, parola, olusturan_kullanici_sicil) VALUES (:sicil, :ad, :soyad, :email, :sifre, :sicil)"),
        {"sicil": sicil_no, "ad": ad, "soyad": soyad, "email": email, "sifre": hashed_sifre}
    )
    
    db.execute(
        text("INSERT INTO kullanici_yetkileri (sicil, firma_id, rol_id, tanimlayan_kullanici_sicil) VALUES (:sicil, 1, 1, :sicil)"),
        {"sicil": sicil_no}
    )
    
    db.commit()
    return {"mesaj": "Kurulum başarılı, giriş yapabilirsiniz."}

@app.post("/giris-yap")
async def giris_islemi(
    request: Request,
    kullanici_adi: str = Form(...),
    sifre: str = Form(...),
    db: Session = Depends(get_db)
):
    # İstemciden IP ve Tarayıcı bilgisini alıyoruz
    ip_adresi = request.headers.get("X-Forwarded-For", request.client.host)
    if ip_adresi:
        ip_adresi = ip_adresi.split(",")[0].strip()
        
    tarayici = request.headers.get("user-agent")[:255] if request.headers.get("user-agent") else "Bilinmiyor"
    
    # --- BRUTE FORCE (KABA KUVVET) KORUMASI ---
    # Bu IP adresinden son 15 dakikada kaç tane başarısız giriş yapılmış kontrol ediyoruz
    basarisiz_denemeler = db.execute(
        text("SELECT COUNT(*) FROM kullanici_giris_loglari WHERE ip_adresi = :ip AND durum = 'Başarısız' AND islem_zamani >= NOW() - INTERVAL '15 minutes'"),
        {"ip": ip_adresi}
    ).scalar()

    if basarisiz_denemeler >= 5:
        # 429 Too Many Requests (Çok Fazla İstek) koduyla saldırganı engelliyoruz
        raise HTTPException(status_code=429, detail="Çok fazla hatalı deneme yaptınız. Lütfen 15 dakika bekleyin.")
    
    # Kullanıcıyı sicil numarasına göre bul
    kullanici = db.execute(
        text("SELECT sicil, parola FROM kullanicilar WHERE sicil = :sicil"),
        {"sicil": kullanici_adi}
    ).fetchone()
    
    if not kullanici:
        # Sicil yoksa DB kısıtlamalarına (Foreign Key) takılmamak için doğrudan reddediyoruz
        raise HTTPException(status_code=401, detail="Hatalı sicil numarası veya şifre.")

    # Şifre Doğrulaması
    if not verify_password(sifre, kullanici.parola):
        # Şifre yanlışsa başarısız logu basıyoruz
        db.execute(
            text("INSERT INTO kullanici_giris_loglari (sicil, durum, ip_adresi, tarayici, hata_mesaji) VALUES (:sicil, 'Başarısız', :ip, :tarayici, 'Hatalı şifre')"),
            {"sicil": kullanici_adi, "ip": ip_adresi, "tarayici": tarayici}
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Hatalı sicil numarası veya şifre.")
        
    # --- BAŞARILI GİRİŞ İŞLEMLERİ ---
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

@app.get("/platform", response_class=HTMLResponse)
async def platform_dashboard():
    html_icerik = """
    <html>
        <body style="background-color: #0f172a; color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; font-family: sans-serif;">
            <h1 style="color: #3b82f6;">İş Zekası Platformuna Hoş Geldiniz</h1>
            <p>Admin girişi başarıyla sağlandı. Raporlar ve entegrasyonlar yakında burada olacak.</p>
            <a href="/" style="color: white; margin-top: 20px;">Çıkış Yap</a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_icerik)