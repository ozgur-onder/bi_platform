from fastapi import APIRouter, Request, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import get_password_hash

router = APIRouter()

@router.post("/kurulum-tamamla")
async def kurulum_yap(
    request: Request,
    ad: str = Form(...),
    soyad: str = Form(...),
    sicil_no: str = Form(...),
    email: str = Form(...),
    sifre: str = Form(...),
    smtp_sunucu: str = Form(...),
    smtp_port: int = Form(...),
    smtp_email: str = Form(...),
    smtp_sifre: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Sistemin daha önce kurulup kurulmadığını kontrol et
    sayi = db.execute(text("SELECT COUNT(*) FROM kullanicilar")).scalar()
    if sayi > 0:
        raise HTTPException(status_code=400, detail="Sistem zaten kurulu.")
        
    hashed_sifre = get_password_hash(sifre)
        
    # 2. Ana Yönetici Kullanıcıyı Kaydet
    db.execute(
        text("""
            INSERT INTO kullanicilar (sicil, ad, soyad, email, parola, olusturan_kullanici_sicil) 
            VALUES (:sicil, :ad, :soyad, :email, :sifre, :sicil)
        """),
        {"sicil": sicil_no, "ad": ad, "soyad": soyad, "email": email, "sifre": hashed_sifre}
    )
    
    # 3. Yöneticiye 'Sistem Yöneticisi' (1) rolünü ve 'Yönetim Merkezi' (1) firmasını ata
    db.execute(
        text("""
            INSERT INTO kullanici_yetkileri (sicil, firma_id, rol_id, tanimlayan_kullanici_sicil) 
            VALUES (:sicil, 1, 1, :sicil)
        """),
        {"sicil": sicil_no}
    )

    # 4. SMTP Ayarlarını sistemin varsayılanı olarak kaydet ve oluşturulan ID'yi döndür
    result = db.execute(
        text("""
            INSERT INTO smtp_ayarlari 
            (sunucu, port, kullanici_adi, sifre, varsayilan_mi, olusturan_guncelleyen_sicil) 
            VALUES (:sunucu, :port, :kullanici, :s_sifre, TRUE, :sicil)
            RETURNING id
        """),
        {
            "sunucu": smtp_sunucu, 
            "port": smtp_port, 
            "kullanici": smtp_email, 
            "s_sifre": smtp_sifre,
            "sicil": sicil_no
        }
    )
    smtp_id = result.scalar()

    # 5. SMTP işlemini log tablosuna kaydet
    db.execute(
        text("""
            INSERT INTO smtp_ayarlari_loglari 
            (smtp_ayar_id, islem_turu, yeni_sunucu, yeni_kullanici_adi, islem_yapan_kullanici_sicil) 
            VALUES (:smtp_id, 'EKLEME', :sunucu, :kullanici, :sicil)
        """),
        {
            "smtp_id": smtp_id,
            "sunucu": smtp_sunucu,
            "kullanici": smtp_email,
            "sicil": sicil_no
        }
    )
    
    db.commit()
    return {"mesaj": "Kurulum başarılı, giriş yapabilirsiniz."}