from fastapi import APIRouter, Request, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import get_password_hash

# Bu dosyadaki rotaları ana uygulamaya bağlamak için router oluşturuyoruz
router = APIRouter()

@router.post("/kurulum-tamamla")
async def kurulum_yap(
    request: Request,
    ad: str = Form(...),
    soyad: str = Form(...),
    sicil_no: str = Form(...),
    email: str = Form(...),
    sifre: str = Form(...),
    db: Session = Depends(get_db)
):
    sayi = db.execute(text("SELECT COUNT(*) FROM kullanicilar")).scalar()
    if sayi > 0:
        raise HTTPException(status_code=400, detail="Sistem zaten kurulu.")
        
    hashed_sifre = get_password_hash(sifre)
        
    db.execute(
        text("INSERT INTO kullanicilar (sicil, ad, soyad, email, parola, olusturan_kullanici_sicil) VALUES (:sicil, :ad, :soyad, :email, :sifre, :sicil)"),
        {"sicil": sicil_no, "ad": ad, "soyad": soyad, "email": email, "sifre": hashed_sifre}
    )
    
    db.execute(
        text("INSERT INTO kullanici_yetkileri (sicil, firma_id, rol_id, tanimlayan_kullanici_sicil) VALUES (:sicil, 1, 1, :sicil)"),
        {"sicil": sicil_no}
    )
    
    db.commit()
    return {"mesaj": "Kurulum başarılı, giriş yapabilirsiniz."}