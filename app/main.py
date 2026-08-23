# app/main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="İş Zekası Platformu")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".")

# Şimdilik kurulum durumunu hafızada tutan geçici bir anahtar (İleride veritabanına bağlanacak)
KURULUM_TAMAMLANDI = False

# 1. DIŞ DÜNYAYA AÇIK TEK ROTA
@app.get("/", response_class=HTMLResponse)
async def ana_sayfa(request: Request):
    global KURULUM_TAMAMLANDI
    
    # Kullanıcı yoksa (kurulum yapılmadıysa) direkt kurulum sayfasını aç
    if not KURULUM_TAMAMLANDI:
        return templates.TemplateResponse(request=request, name="sayfalar/kurulum.html")
    
    # Kullanıcı varsa normal giriş sayfasını aç
    return templates.TemplateResponse(request=request, name="index.html")

# 2. GİZLİ BİLEŞEN ROTALARI
@app.get("/bilesen/{sayfa_adi}", response_class=HTMLResponse)
async def bilesen_getir(request: Request, sayfa_adi: str):
    if sayfa_adi == "index":
        return HTMLResponse(content="Lütfen ana sayfaya dönmek için sayfayı yenileyin veya '/' adresine gidin.", status_code=400)
    
    dosya_yolu = f"sayfalar/{sayfa_adi}.html"
    
    if os.path.exists(dosya_yolu):
        return templates.TemplateResponse(request=request, name=dosya_yolu)
    
    return HTMLResponse(content="Bileşen bulunamadı.", status_code=404)

# 3. KURULUM İŞLEMLERİNİ ALACAK ROTA
@app.post("/kurulum-tamamla")
async def kurulum_yap(
    kullanici_adi: str = Form(...),
    sifre: str = Form(...)
):
    global KURULUM_TAMAMLANDI
    # İleride veritabanı kayıt işlemi burada olacak
    
    # Kurulum yapıldı olarak sistemi güncelliyoruz
    KURULUM_TAMAMLANDI = True 
    return {"mesaj": "Kurulum başarılı, ana sayfaya gidip giriş yapabilirsiniz!"}