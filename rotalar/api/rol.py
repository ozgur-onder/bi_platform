from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rotalar.yetki_servisi import super_admin_gerektir
from rotalar.rol_servisi import rol_listesi, rol_ekle, rol_durum_guncelle, rol_log_listesi, rol_duzenle

router = APIRouter(prefix="/api/rol")

class RolEkleIstek(BaseModel):
    rol_kodu: int
    rol_adi:  str

class RolDuzenleIstek(BaseModel):
    rol_kodu: int
    rol_adi:  str

class DurumIstek(BaseModel):
    durum: bool

@router.get("")
async def listele(kullanici: dict = Depends(super_admin_gerektir)):
    sonuc = await rol_listesi()
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])

@router.post("")
async def ekle(
    istek: RolEkleIstek,
    kullanici: dict = Depends(super_admin_gerektir)
):
    sonuc = await rol_ekle(istek.rol_kodu, istek.rol_adi.strip(), kullanici["sicil"])
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])

@router.put("/{eski_kodu}")
async def duzenle(
    eski_kodu: int,
    istek: RolDuzenleIstek,
    kullanici: dict = Depends(super_admin_gerektir)
):
    sonuc = await rol_duzenle(
        eski_kodu, 
        istek.rol_kodu, 
        istek.rol_adi.strip(), 
        kullanici["sicil"]
    )
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])

@router.patch("/{rol_kodu}/durum")
async def durum_guncelle(
    rol_kodu: int,
    istek: DurumIstek,
    kullanici: dict = Depends(super_admin_gerektir)
):
    sonuc = await rol_durum_guncelle(rol_kodu, istek.durum, kullanici["sicil"])
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])

@router.get("/loglar")
async def log_listele(kullanici: dict = Depends(super_admin_gerektir)):
    sonuc = await rol_log_listesi()
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])