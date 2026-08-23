# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# Platform motorunu başlatıyoruz
app = FastAPI(title="İş Zekası Platformu")

# Statik dosyaları (CSS, JS) motora tanıtıyoruz
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML sayfalarımızın nerede olduğunu belirtiyoruz (Ana dizin)
templates = Jinja2Templates(directory=".")

# 1. DIŞ DÜNYAYA AÇIK TEK ROTA (Adres çubuğunda hep bu görünecek)
@app.get("/", response_class=HTMLResponse)
async def ana_sayfa(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 2. GİZLİ BİLEŞEN ROTALARI (Sadece JavaScript arka plandan istek attığında çalışır)
@app.get("/bilesen/{sayfa_adi}", response_class=HTMLResponse)
async def bilesen_getir(request: Request, sayfa_adi: str):
    dosya_yolu = f"sayfalar/{sayfa_adi}.html"
    
    # İstenen dosya klasörde varsa içeriğini geri döndür
    if os.path.exists(dosya_yolu):
        return templates.TemplateResponse(dosya_yolu, {"request": request})
    
    return HTMLResponse(content="Bileşen bulunamadı.", status_code=404)