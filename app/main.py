from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from sqlalchemy.orm import Session
from sqlalchemy import text

# Kendi yazdığımız modülleri (veritabanı ve rotalar) içeri aktarıyoruz
from app.core.database import get_db
from app.routers import setup, auth

app = FastAPI(title="İş Zekası Platformu")

# Statik dosyaları ve şablonları bağlıyoruz
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".")

# --- ROTALARI (ROUTERS) ANA UYGULAMAYA BAĞLIYORUZ ---
app.include_router(setup.router)
app.include_router(auth.router)


# --- SADECE ARAYÜZ (HTML) ÇAĞRILARI BURADA KALDI ---
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