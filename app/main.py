# app/main.py
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="İş Zekası Platformu")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".")

# Şimdilik veritabanı olmadığı için geçici kurulum bilgileri
KURULUM_TAMAMLANDI = False
ADMIN_SICIL = None
ADMIN_SIFRE = None

# 1. DIŞ DÜNYAYA AÇIK ANA SAYFA (GİRİŞ EKRANI VEYA KURULUM)
@app.get("/", response_class=HTMLResponse)
async def ana_sayfa(request: Request):
    global KURULUM_TAMAMLANDI
    
    # Kullanıcı yoksa (kurulum yapılmadıysa) direkt kurulum sayfasını aç
    if not KURULUM_TAMAMLANDI:
        return templates.TemplateResponse(request=request, name="sayfalar/kurulum.html")
    
    # Kullanıcı varsa normal giriş sayfasını aç
    return templates.TemplateResponse(request=request, name="index.html")

# 2. GİZLİ BİLEŞEN VE SAYFA ROTALARI
@app.get("/bilesen/{sayfa_adi}", response_class=HTMLResponse)
async def bilesen_getir(request: Request, sayfa_adi: str):
    # Ana sayfayı bileşen olarak çağırmayı engelle (Sonsuz döngü koruması)
    if sayfa_adi == "index":
        return RedirectResponse(url="/")
    
    dosya_yolu = f"sayfalar/{sayfa_adi}.html"
    
    if os.path.exists(dosya_yolu):
        return templates.TemplateResponse(request=request, name=dosya_yolu)
    
    return HTMLResponse(content="Sayfa bulunamadı.", status_code=404)

# 3. KURULUM İŞLEMLERİ
@app.post("/kurulum-tamamla")
async def kurulum_yap(
    kullanici_adi: str = Form(...),
    sifre: str = Form(...)
):
    global KURULUM_TAMAMLANDI, ADMIN_SICIL, ADMIN_SIFRE
    
    # Geçici olarak sicil numarası ve şifreyi hafızaya kaydediyoruz (İleride DB'ye eklenecek)
    ADMIN_SICIL = kullanici_adi
    ADMIN_SIFRE = sifre
    KURULUM_TAMAMLANDI = True 
    
    return {"mesaj": "Kurulum başarılı, ana sayfaya yönlendiriliyorsunuz..."}

# 4. GİRİŞ İŞLEMLERİ
@app.post("/giris-yap")
async def giris_islemi(
    kullanici_adi: str = Form(...),
    sifre: str = Form(...)
):
    global ADMIN_SICIL, ADMIN_SIFRE
    
    # Girilen bilgiler kurulumda belirlenen bilgilerle eşleşiyor mu kontrol et
    if kullanici_adi == ADMIN_SICIL and sifre == ADMIN_SIFRE:
        return {"mesaj": "Giriş başarılı, sisteme aktarılıyorsunuz."}
    else:
        raise HTTPException(status_code=401, detail="Hatalı giriş")

# 5. İŞ ZEKASI PLATFORMU (DASHBOARD) - BAŞARILI GİRİŞTEN SONRAKİ SAYFA
@app.get("/platform", response_class=HTMLResponse)
async def platform_dashboard():
    # Şimdilik buraya basit bir karşılama metni koyuyoruz, ileride burası ana uygulama ekranın olacak (Metabase, n8n entegrasyonu vb.)
    html_icerik = """
    <html>
        <head>
            <title>Platform - İş Zekası</title>
            <style>
                body { background-color: #0f172a; color: white; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                h1 { color: #3b82f6; }
            </style>
        </head>
        <body>
            <h1>İş Zekası Platformuna Hoş Geldiniz</h1>
            <p>Admin girişi başarıyla sağlandı. Raporlar ve entegrasyonlar yakında burada olacak.</p>
            <a href="/" style="color: white; margin-top: 20px;">Çıkış Yap</a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_icerik)