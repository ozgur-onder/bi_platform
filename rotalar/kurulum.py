import os
import hashlib
import re
import smtplib
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
from cryptography.fernet import Fernet

router = APIRouter()

def get_cipher():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="Sistem Hatası: ENCRYPTION_KEY .env dosyasında bulunamadı!")
    return Fernet(key.encode('utf-8'))

def veritabani_baglantisi():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT", "5432")
    )

def email_gecerli_mi(email: str) -> bool:
    """E-posta adresinin geçerli bir formatta olup olmadığını kontrol eder."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))

def smtp_baglanti_testi(sunucu, port, email, sifre):
    """SMTP Sunucusunun çalışıp çalışmadığını ve kimlik doğrulamasını test eder."""
    try:
        if int(port) == 465:
            server = smtplib.SMTP_SSL(sunucu, int(port), timeout=10)
        else:
            server = smtplib.SMTP(sunucu, int(port), timeout=10)
            server.starttls()
        
        server.login(email, sifre)
        server.quit()
        return True
    except Exception as e:
        raise Exception(f"SMTP Bağlantı/Kimlik Doğrulama Hatası: {str(e)}")

@router.post("/kurulum-smtp-test")
async def kurulum_smtp_test(
    smtp_sunucu: str = Form(...),
    smtp_port: int = Form(...),
    smtp_email: str = Form(...),
    smtp_sifre: str = Form(...)
):
    if not email_gecerli_mi(smtp_email):
        return JSONResponse(content={"detail": "Geçersiz gönderici e-posta formatı."}, status_code=400)

    try:
        smtp_baglanti_testi(smtp_sunucu, smtp_port, smtp_email, smtp_sifre)
        return JSONResponse(
            content={"mesaj": "SMTP bağlantısı ve kimlik doğrulama başarıyla sağlandı!"},
            status_code=200
        )
    except Exception as e:
        hata_detayi = str(e)
        if "Authentication failed" in hata_detayi or "535" in hata_detayi:
            mesaj = "Kimlik doğrulama başarısız: E-posta adresi veya şifre hatalı."
        elif "timed out" in hata_detayi.lower() or "getaddrinfo failed" in hata_detayi.lower():
            mesaj = "Bağlantı hatası: Sunucu adresi veya port numarası ulaşılamaz durumda."
        else:
            mesaj = f"SMTP Test Hatası: {hata_detayi}"
            
        return JSONResponse(content={"detail": mesaj}, status_code=400)

@router.post("/kurulum-tamamla")
async def kurulum_tamamla(
    ad: str = Form(...),
    soyad: str = Form(...),
    sicil_no: str = Form(...),
    email: str = Form(...),
    sifre: str = Form(...),
    smtp_sunucu: str = Form(...),
    smtp_port: int = Form(...),
    smtp_email: str = Form(...),
    smtp_sifre: str = Form(...),
    smtp_gonderici: str = Form(...)
):
    # Veri Temizleme ve Büyük Harf Dönüşümü
    islenen_ad = ad.strip().upper()
    islenen_soyad = soyad.strip().upper()
    islenen_email = email.strip()

    # E-Posta Format Doğrulamaları
    if not email_gecerli_mi(islenen_email):
        raise HTTPException(status_code=400, detail="Yönetici e-posta adresi geçersiz formatta.")
    if not email_gecerli_mi(smtp_email.strip()):
        raise HTTPException(status_code=400, detail="SMTP gönderici e-posta adresi geçersiz formatta.")

    conn = None
    try:
        # SMTP Canlı Testi
        try:
            smtp_baglanti_testi(smtp_sunucu, smtp_port, smtp_email.strip(), smtp_sifre)
        except Exception as smtp_hata:
            hata_metni = str(smtp_hata)
            if "Authentication failed" in hata_metni or "535" in hata_metni:
                detay = "Kurulum engellendi: SMTP kimlik doğrulaması başarısız (E-posta veya şifre yanlış)."
            else:
                detay = f"Kurulum engellendi: {hata_metni}"
            raise HTTPException(status_code=400, detail=detay)

        cipher_suite = get_cipher()
        conn = veritabani_baglantisi()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM kullanicilar;")
        if cursor.fetchone()[0] > 0:
            cursor.close()
            raise HTTPException(status_code=403, detail="Sistem kurulumu daha önce tamamlanmıştır!")

        sifre_hash = hashlib.sha256(sifre.encode('utf-8')).hexdigest()
        kilitli_smtp_sifre = cipher_suite.encrypt(smtp_sifre.encode('utf-8')).decode('utf-8')

        # Ad ve Soyad kesinlikle BÜYÜK HARFLE kaydedilir
        cursor.execute("""
            INSERT INTO kullanicilar (sicil, ad, soyad, email, parola, olusturan_kullanici_sicil)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (sicil_no, islenen_ad, islenen_soyad, islenen_email, sifre_hash, sicil_no))

        cursor.execute("SELECT id FROM firma WHERE firma_kodu = 'F001';")
        firma_sonuc = cursor.fetchone()
        if not firma_sonuc:
            raise HTTPException(status_code=500, detail="Sistem Hatası: 'F001' kodlu firma veritabanında bulunamadı!")
        firma_id = firma_sonuc[0]

        cursor.execute("SELECT id FROM roller WHERE rol_kodu = 1;")
        rol_sonuc = cursor.fetchone()
        if not rol_sonuc:
            raise HTTPException(status_code=500, detail="Sistem Hatası: Rol kodu '1' olan rol veritabanında bulunamadı!")
        rol_id = rol_sonuc[0]

        cursor.execute("""
            INSERT INTO kullanici_yetkileri (sicil, firma_id, rol_id, tanimlayan_kullanici_sicil, durum)
            VALUES (%s, %s, %s, %s, TRUE)
        """, (sicil_no, firma_id, rol_id, sicil_no))

        cursor.execute("""
            INSERT INTO smtp_ayarlari (firma_kodu, rol_id, rapor_kodu, sunucu, port, kullanici_adi, sifre, gonderici_adi, varsayilan_mi, olusturan_guncelleyen_sicil)
            VALUES ('F001', %s, '1', %s, %s, %s, %s, %s, TRUE, %s)
            RETURNING id;
        """, (rol_id, smtp_sunucu, smtp_port, smtp_email.strip(), kilitli_smtp_sifre, smtp_gonderici, sicil_no))
        
        smtp_ayar_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO smtp_ayarlari_loglari (firma_kodu, sunucu, yapilan_islem, islem_yapan_kullanici_sicil)
            VALUES ('F001', %s, %s, %s)
        """, (smtp_sunucu, f"SMTP Ayarları Eklendi ({smtp_sunucu})", sicil_no))

        conn.commit()
        cursor.close()

        return JSONResponse(
            content={"mesaj": "Sistem kurulumu başarıyla tamamlandı! Yönlendiriliyorsunuz..."}, 
            status_code=200
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Hata detayı: {str(e)}")
    finally:
        if conn:
            conn.close()