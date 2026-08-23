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

# 1. DIŞ DÜNYAYA AÇIK TEK ROTA
@app.get("/", response_class=HTMLResponse)
async def ana_sayfa(request: Request):
    # DİKKAT: context sözlüğü yerine doğrudan request=request formatı kullanıldı
    return templates.TemplateResponse(request=request, name="index.html")

# 2. GİZLİ BİLEŞEN ROTALARI
@app.get("/bilesen/{sayfa_adi}", response_class=HTMLResponse)
async def bilesen_getir(request: Request, sayfa_adi: str):
    # Eğer index isteniyorsa ana dizine, değilse sayfalar klasörüne bak
    if sayfa_adi == "index":
        dosya_yolu = "index.html"
    else:
        dosya_yolu = f"sayfalar/{sayfa_adi}.html"
    
    # İstenen dosya klasörde varsa içeriğini geri döndür
    if os.path.exists(dosya_yolu):
        return templates.TemplateResponse(request=request, name=dosya_yolu)
    
    return HTMLResponse(content="Bileşen bulunamadı.", status_code=404)