import sys
import psycopg2, os
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from rotalar.yetki_servisi import oturum_gerektir

router = APIRouter(prefix="/api")

def db_baglan():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT", "5432")
    )

@router.get("/ben")
async def beni_al(kullanici: dict = Depends(oturum_gerektir)):
    """Oturumdaki kullanıcının bilgilerini ve rol listesini döndürür."""
    conn = cursor = None
    try:
        conn   = db_baglan()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT rol_id FROM kullanici_yetkileri WHERE sicil=%s AND durum=TRUE",
            (kullanici["sicil"],)
        )
        roller = [r[0] for r in cursor.fetchall()]
        return JSONResponse(content={
            "sicil":    kullanici["sicil"],
            "ad_soyad": kullanici["ad_soyad"],
            "email":    kullanici["email"],
            "roller":   roller
        })
    except Exception as e:
        print(f"[kullanici] {type(e).__name__}: {e}", file=sys.stderr)
        return JSONResponse(content={"detail": "Kullanıcı bilgisi alınamadı."}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

@router.get("/profil")
async def profil_al(kullanici: dict = Depends(oturum_gerektir)):
    """Arayüzdeki sol menü ve anasayfa için profil bilgilerini döndürür."""
    conn = cursor = None
    try:
        conn   = db_baglan()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rol_id FROM kullanici_yetkileri WHERE sicil=%s AND durum=TRUE LIMIT 1",
            (kullanici["sicil"],)
        )
        rol_kayit = cursor.fetchone()
        rol = rol_kayit[0] if rol_kayit else "Kullanıcı"
        
        return JSONResponse(content={
            "ad_soyad": kullanici["ad_soyad"],
            "rol": rol
        })
    except Exception as e:
        print(f"[profil] {type(e).__name__}: {e}", file=sys.stderr)
        return JSONResponse(content={
            "ad_soyad": kullanici.get("ad_soyad", "Bilinmeyen Kullanıcı"),
            "rol": "Belirtilmemiş"
        })
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

@router.get("/kullanici")
async def kullanici_listesi(kullanici: dict = Depends(oturum_gerektir)):
    """Veritabanındaki tüm kullanıcıları listeler."""
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()
        
        # Sütun adı veritabanındaki şekliyle olusturan_kullanici_sicil olarak güncellendi
        cursor.execute("""
            SELECT sicil, ad, soyad, email, durum, olusturan_kullanici_sicil, 
                   TO_CHAR(olusturma_zamani, 'YYYY-MM-DD"T"HH24:MI:SS') 
            FROM kullanicilar 
            ORDER BY sicil
        """)
        
        kolonlar = ["sicil", "ad", "soyad", "email", "durum", "olusturan_kullanici_id", "olusturma_zamani"]
        kullanicilar = [dict(zip(kolonlar, satir)) for satir in cursor.fetchall()]
        
        return JSONResponse(content=kullanicilar)
    except Exception as e:
        print(f"[kullanici_liste] Hata: {e}", file=sys.stderr)
        return JSONResponse(content={"detail": "Kullanıcı listesi alınamadı."}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@router.post("/kullanici")
async def kullanici_ekle(yeni_kullanici: dict, kullanici: dict = Depends(oturum_gerektir)):
    """Yeni kullanıcı kaydı oluşturur."""
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO kullanicilar (sicil, ad, soyad, email, parola, durum, olusturan_kullanici_sicil)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            yeni_kullanici["sicil"], 
            yeni_kullanici["ad"], 
            yeni_kullanici["soyad"], 
            yeni_kullanici["email"],
            "gecici_parola_123",
            yeni_kullanici.get("durum", True),
            kullanici["sicil"]
        ))
        conn.commit()
        return JSONResponse(content={"mesaj": "Kullanıcı başarıyla eklendi."})
    except Exception as e:
        if conn: conn.rollback()
        print(f"[kullanici_ekle] Hata: {e}", file=sys.stderr)
        return JSONResponse(content={"detail": "Kullanıcı eklenemedi."}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@router.patch("/kullanici/{sicil_no}/durum")
async def kullanici_durum_guncelle(sicil_no: str, veri: dict, kullanici: dict = Depends(oturum_gerektir)):
    """Kullanıcının aktif/pasif durumunu günceller."""
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()
        cursor.execute("UPDATE kullanicilar SET durum = %s WHERE sicil = %s", (veri["durum"], sicil_no))
        conn.commit()
        return JSONResponse(content={"mesaj": "Durum güncellendi."})
    except Exception as e:
        if conn: conn.rollback()
        print(f"[durum_guncelle] Hata: {e}", file=sys.stderr)
        return JSONResponse(content={"detail": "Durum güncellenemedi."}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@router.get("/kullanici/loglar")
async def kullanici_loglari(kullanici: dict = Depends(oturum_gerektir)):
    """Kullanıcı işlem loglarını döndürür."""
    return JSONResponse(content=[{"mesaj": "Log sistemi henüz aktif değil."}])