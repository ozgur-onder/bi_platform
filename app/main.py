from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db

app = FastAPI(title="İş Zekası Platformu")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".")

@app.get("/", response_class=HTMLResponse)
async def ana_sayfa(request: Request, db: Session = Depends(get_db)):
    # Veritabanında hiç kayıtlı kullanıcı var mı diye bakıyoruz
    kullanici_sayisi = db.execute(text("SELECT COUNT(*) FROM kullanicilar")).scalar()
    
    # Kullanıcı yoksa kurulum ekranına yönlendir
    if kullanici_sayisi == 0:
        return templates.TemplateResponse(request=request, name="sayfalar/kurulum.html")
    
    # Kullanıcı varsa standart giriş ekranını aç
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
    ad: str = Form(...),
    soyad: str = Form(...),
    sicil_no: str = Form(...),
    email: str = Form(...),
    sifre: str = Form(...),
    db: Session = Depends(get_db)
):
    # Başkası bizden önce kurmuş mu kontrolü
    sayi = db.execute(text("SELECT COUNT(*) FROM kullanicilar")).scalar()
    if sayi > 0:
        raise HTTPException(status_code=400, detail="Sistem zaten kurulu.")
        
    # Kullanıcıyı veritabanına kaydet
    db.execute(
        text("INSERT INTO kullanicilar (sicil, ad, soyad, email, parola, olusturan_kullanici_sicil) VALUES (:sicil, :ad, :soyad, :email, :sifre, :sicil)"),
        {"sicil": sicil_no, "ad": ad, "soyad": soyad, "email": email, "sifre": sifre}
    )
    
    # İlk kullanıcıya doğrudan Sistem Yöneticisi yetkisi ver
    db.execute(
        text("INSERT INTO kullanici_yetkileri (sicil, firma_id, rol_id, tanimlayan_kullanici_sicil) VALUES (:sicil, 1, 1, :sicil)"),
        {"sicil": sicil_no}
    )
    
    db.commit()
    return {"mesaj": "Kurulum başarılı, giriş yapabilirsiniz."}

@app.post("/giris-yap")
async def giris_islemi(
    kullanici_adi: str = Form(...),
    sifre: str = Form(...),
    db: Session = Depends(get_db)
):
    # Veritabanında sicil ve şifre eşleşmesi ara
    kullanici = db.execute(
        text("SELECT sicil FROM kullanicilar WHERE sicil = :sicil AND parola = :sifre"),
        {"sicil": kullanici_adi, "sifre": sifre}
    ).fetchone()
    
    if kullanici:
        return {"mesaj": "Giriş başarılı."}
    else:
        raise HTTPException(status_code=401, detail="Hatalı giriş.")

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