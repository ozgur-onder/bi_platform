import sys
import psycopg2, os
from datetime import datetime

def db_baglan():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT", "5432")
    )

def tarih_formatla(zaman):
    if not zaman: return "-"
    return zaman.strftime("%d.%m.%Y %H:%M:%S")

async def rol_listesi() -> dict:
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT rol_kodu, rol_adi, durum, olusturan_guncelleyen_sicil, olusturma_guncelleme_zamani 
               FROM roller ORDER BY rol_kodu"""
        )
        roller = [
            {
                "Rol Kodu": r[0], 
                "Rol Adı": r[1],
                "Durum": "Aktif" if r[2] else "Pasif", 
                "İşlem Yapan Sicil": r[3] or "-",
                "Son İşlem Zamanı": tarih_formatla(r[4])
            }
            for r in cursor.fetchall()
        ]
        return {"icerik": roller, "statu": 200}
    except Exception as e:
        print(f"[rol_servisi] listele {type(e).__name__}: {e}", file=sys.stderr)
        return {"icerik": {"detail": f"Roller alınamadı: {str(e)}"}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

async def rol_ekle(rol_kodu: int, rol_adi: str, islem_yapan_sicil: str) -> dict:
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM roller WHERE rol_kodu=%s", (rol_kodu,))
        if cursor.fetchone():
            return {"icerik": {"detail": "Bu rol kodu zaten kayıtlı."}, "statu": 409}

        cursor.execute(
            """INSERT INTO roller (rol_kodu, rol_adi, durum, olusturan_guncelleyen_sicil, olusturma_guncelleme_zamani)
               VALUES (%s, %s, True, %s, NOW())""",
            (rol_kodu, rol_adi, islem_yapan_sicil)
        )
        
        cursor.execute(
            """INSERT INTO rol_guncelleme_loglari 
               (firma_kodu, firma_adi, yapilan_islem, islem_yapan_kullanici_sicil, islem_zamani)
               VALUES (%s, %s, %s, %s, NOW())""",
            (str(rol_kodu), rol_adi, "Rol Eklendi", islem_yapan_sicil)
        )
        conn.commit()
        return {"icerik": {"mesaj": "Rol başarıyla eklendi."}, "statu": 201}
    except Exception as e:
        print(f"[rol_servisi] ekle {type(e).__name__}: {e}", file=sys.stderr)
        if conn: conn.rollback()
        return {"icerik": {"detail": f"Rol eklenemedi: {str(e)}"}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

async def rol_durum_guncelle(rol_kodu: int, yeni_durum: bool, islem_yapan_sicil: str) -> dict:
    if rol_kodu == 1 or str(rol_kodu) == '1':
        return {"icerik": {"detail": "İlk eklenen sistem rolü (Rol Kodu: 1) pasife alınamaz."}, "statu": 403}
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()

        cursor.execute("SELECT rol_adi, durum FROM roller WHERE rol_kodu=%s", (rol_kodu,))
        satir = cursor.fetchone()
        if not satir:
            return {"icerik": {"detail": "Rol bulunamadı."}, "statu": 404}
        
        rol_adi, eski_durum = satir

        if eski_durum == yeni_durum:
            return {"icerik": {"detail": "Durum zaten bu değerde."}, "statu": 400}

        cursor.execute(
            """UPDATE roller
               SET durum=%s, olusturan_guncelleyen_sicil=%s, olusturma_guncelleme_zamani=NOW()
               WHERE rol_kodu=%s""",
            (yeni_durum, islem_yapan_sicil, rol_kodu)
        )
        
        durum_str = f"Statü Değişikliği: {'Aktif' if eski_durum else 'Pasif'}-{'Aktif' if yeni_durum else 'Pasif'}"
        cursor.execute(
            """INSERT INTO rol_guncelleme_loglari 
               (firma_kodu, firma_adi, yapilan_islem, islem_yapan_kullanici_sicil, islem_zamani)
               VALUES (%s, %s, %s, %s, NOW())""",
            (str(rol_kodu), rol_adi, durum_str, islem_yapan_sicil)
        )
        conn.commit()
        durum_metni = "aktifleştirildi" if yeni_durum else "pasife alındı"
        return {"icerik": {"mesaj": f"Rol başarıyla {durum_metni}."}, "statu": 200}
    except Exception as e:
        print(f"[rol_servisi] durum {type(e).__name__}: {e}", file=sys.stderr)
        if conn: conn.rollback()
        return {"icerik": {"detail": f"Durum güncellenemedi: {str(e)}"}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

async def rol_duzenle(eski_kodu: int, yeni_kodu: int, yeni_adi: str, islem_yapan_sicil: str) -> dict:
    if eski_kodu == 1 or yeni_kodu == 1 or str(eski_kodu) == '1' or str(yeni_kodu) == '1':
        return {"icerik": {"detail": "İlk eklenen sistem rolü (Rol Kodu: 1) üzerinde düzenleme yapılamaz."}, "statu": 403}
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()
        
        cursor.execute("SELECT rol_kodu, rol_adi FROM roller WHERE rol_kodu=%s", (eski_kodu,))
        eski_veri = cursor.fetchone()
        if not eski_veri:
            return {"icerik": {"detail": "Rol bulunamadı."}, "statu": 404}
        
        eski_kod, eski_adi = eski_veri
        
        cursor.execute("""
            UPDATE roller 
            SET rol_kodu=%s, rol_adi=%s, olusturan_guncelleyen_sicil=%s, olusturma_guncelleme_zamani=NOW()
            WHERE rol_kodu=%s
        """, (yeni_kodu, yeni_adi, islem_yapan_sicil, eski_kodu))
        
        islem_metni = []
        if eski_kod != yeni_kodu:
            islem_metni.append(f"Rol Kodu Değişikliği: {eski_kod}-{yeni_kodu}")
        if eski_adi != yeni_adi:
            islem_metni.append(f"Rol Adı Değişikliği: {eski_adi}-{yeni_adi}")
        
        if islem_metni:
            yapilan_islem_str = " | ".join(islem_metni)
            cursor.execute(
                """INSERT INTO rol_guncelleme_loglari 
                   (firma_kodu, firma_adi, yapilan_islem, islem_yapan_kullanici_sicil, islem_zamani)
                   VALUES (%s, %s, %s, %s, NOW())""",
                (str(yeni_kodu), yeni_adi, yapilan_islem_str, islem_yapan_sicil)
            )
        
        conn.commit()
        return {"icerik": {"mesaj": "Rol bilgileri başarıyla güncellendi."}, "statu": 200}
    except Exception as e:
        if conn: conn.rollback()
        print(f"[rol_servisi] duzenle {type(e).__name__}: {e}", file=sys.stderr)
        return {"icerik": {"detail": "Rol güncellenemedi. Yeni yazdığınız rol kodu başka bir role ait olabilir."}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

async def rol_log_listesi() -> dict:
    conn = cursor = None
    try:
        conn = db_baglan()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, firma_kodu, firma_adi, yapilan_islem, islem_zamani, islem_yapan_kullanici_sicil 
               FROM rol_guncelleme_loglari ORDER BY islem_zamani DESC"""
        )
        loglar = [
            {
                "Log ID": r[0],
                "Rol Kodu": r[1], 
                "Rol Adı": r[2],
                "Yapılan İşlem": r[3],
                "İşlem Zamanı": tarih_formatla(r[4]),
                "İşlem Yapan Sicil": r[5] or "-"
            }
            for r in cursor.fetchall()
        ]
        return {"icerik": loglar, "statu": 200}
    except Exception as e:
        print(f"[rol_servisi] log_listele {type(e).__name__}: {e}", file=sys.stderr)
        return {"icerik": {"detail": "Loglar alınamadı."}, "statu": 500}
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()