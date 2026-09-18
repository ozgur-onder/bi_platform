import sys
import psycopg2, os
from datetime import datetime

def db_baglan():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT", "5432")
    )

def tarih_bicimlendir(dt):
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except:
            return dt
    return dt.strftime("%d.%m.%Y %H:%M:%S")

async def firma_listesi() -> dict:
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT firma_kodu, firma_adi, durum, olusturma_guncelleme_zamani, olusturan_guncelleyen_sicil FROM firma ORDER BY firma_adi"
        )
        satırlar = cursor.fetchall()
        firmalar = [
            {
                "Firma Kodu": r[0],
                "Firma Adı": r[1],
                "Durum": "Aktif" if r[2] else "Pasif",
                "Son İşlem Zamanı": tarih_bicimlendir(r[3]),
                "İşlem Yapan Sicil": r[4] or "SİSTEM"
            }
            for r in satırlar
        ]
        return {"icerik": firmalar, "statu": 200}
    except Exception as e:
        print(f"[firma_servisi] listele {type(e).__name__}: {e}", file=sys.stderr)
        return {"icerik": {"detail": "Firmalar alınamadı."}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

async def firma_ekle(firma_kodu: str, firma_adi: str, islem_yapan_sicil: str) -> dict:
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM firma WHERE firma_kodu=%s", (firma_kodu,))
        if cursor.fetchone():
            return {"icerik": {"detail": "Bu firma kodu zaten kayıtlı."}, "statu": 409}

        cursor.execute(
            """INSERT INTO firma (firma_kodu, firma_adi, olusturan_guncelleyen_sicil)
               VALUES (%s, %s, %s)""",
            (firma_kodu, firma_adi, islem_yapan_sicil)
        )
        
        cursor.execute(
            """INSERT INTO firma_guncelleme_loglari
               (firma_kodu, firma_adi, yapilan_islem, islem_yapan_kullanici_sicil)
               VALUES (%s, %s, %s, %s)""",
            (firma_kodu, firma_adi, "Firma Eklendi", islem_yapan_sicil)
        )
        
        conn.commit()
        return {"icerik": {"mesaj": "Firma başarıyla eklendi."}, "statu": 201}
    except Exception as e:
        print(f"[firma_servisi] ekle {type(e).__name__}: {e}", file=sys.stderr)
        if conn: conn.rollback()
        return {"icerik": {"detail": "Firma eklenemedi."}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

async def firma_durum_guncelle(firma_kodu: str, yeni_durum: bool,
                               islem_yapan_sicil: str) -> dict:
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT firma_adi, durum FROM firma WHERE firma_kodu=%s", (firma_kodu,)
        )
        satir = cursor.fetchone()
        if not satir:
            return {"icerik": {"detail": "Firma bulunamadı."}, "statu": 404}

        firma_adi, eski_durum = satir
        if eski_durum == yeni_durum:
            return {"icerik": {"detail": "Durum zaten bu değerde."}, "statu": 400}

        cursor.execute(
            """UPDATE firma
               SET durum=%s, olusturma_guncelleme_zamani=NOW(), olusturan_guncelleyen_sicil=%s
               WHERE firma_kodu=%s""",
            (yeni_durum, islem_yapan_sicil, firma_kodu)
        )
        
        durum_str = f"Statü Değişikliği: {'Aktif' if eski_durum else 'Pasif'}-{'Aktif' if yeni_durum else 'Pasif'}"
        cursor.execute(
            """INSERT INTO firma_guncelleme_loglari
               (firma_kodu, firma_adi, yapilan_islem, islem_yapan_kullanici_sicil)
               VALUES (%s, %s, %s, %s)""",
            (firma_kodu, firma_adi, durum_str, islem_yapan_sicil)
        )
        conn.commit()
        durum_yazi = "aktifleştirildi" if yeni_durum else "pasife alındı"
        return {"icerik": {"mesaj": f"Firma {durum_yazi}."}, "statu": 200}
    except Exception as e:
        print(f"[firma_servisi] durum {type(e).__name__}: {e}", file=sys.stderr)
        if conn: conn.rollback()
        return {"icerik": {"detail": "Durum güncellenemedi."}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

async def firma_duzenle(eski_kodu: str, yeni_kodu: str, yeni_adi: str, islem_yapan_sicil: str) -> dict:
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()
        
        cursor.execute("SELECT firma_kodu, firma_adi FROM firma WHERE firma_kodu=%s", (eski_kodu,))
        eski_veri = cursor.fetchone()
        if not eski_veri:
            return {"icerik": {"detail": "Firma bulunamadı."}, "statu": 404}
        
        eski_kod, eski_adi = eski_veri
        
        cursor.execute("""
            UPDATE firma 
            SET firma_kodu=%s, firma_adi=%s, olusturma_guncelleme_zamani=NOW(), olusturan_guncelleyen_sicil=%s
            WHERE firma_kodu=%s
        """, (yeni_kodu, yeni_adi, islem_yapan_sicil, eski_kodu))
        
        islem_metni = []
        if eski_kod != yeni_kodu:
            islem_metni.append(f"Firma Kodu Değişikliği: {eski_kod}-{yeni_kodu}")
        if eski_adi != yeni_adi:
            islem_metni.append(f"Firma Adı Değişikliği: {eski_adi}-{yeni_adi}")
        
        if islem_metni:
            yapilan_islem_str = " | ".join(islem_metni)
            cursor.execute(
                """INSERT INTO firma_guncelleme_loglari
                   (firma_kodu, firma_adi, yapilan_islem, islem_yapan_kullanici_sicil)
                   VALUES (%s, %s, %s, %s)""",
                (yeni_kodu, yeni_adi, yapilan_islem_str, islem_yapan_sicil)
            )
        
        conn.commit()
        return {"icerik": {"mesaj": "Firma bilgileri başarıyla güncellendi."}, "statu": 200}
    except Exception as e:
        if conn: conn.rollback()
        print(f"[firma_duzenle] Hata: {e}", file=sys.stderr)
        return {"icerik": {"detail": "Firma güncellenemedi. Yeni yazdığınız firma kodu başka bir firmaya ait olabilir."}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

async def firma_loglari_getir() -> dict:
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, firma_kodu, firma_adi, yapilan_islem, 
                   islem_zamani, islem_yapan_kullanici_sicil 
            FROM firma_guncelleme_loglari 
            ORDER BY islem_zamani DESC
        """)
        satirlar = cursor.fetchall()
        loglar = [
            {
                "Log ID": r[0],
                "Firma Kodu": r[1],
                "Firma Adı": r[2],
                "Yapılan İşlem": r[3],
                "İşlem Zamanı": tarih_bicimlendir(r[4]),
                "İşlem Yapan Sicil": r[5] or "SİSTEM"
            }
            for r in satirlar
        ]
        return {"icerik": loglar, "statu": 200}
    except Exception as e:
        print(f"[firma_servisi] log_getir {type(e).__name__}: {e}", file=sys.stderr)
        return {"icerik": {"detail": "Loglar alınamadı."}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()