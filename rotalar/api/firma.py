from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rotalar.yetki_servisi import super_admin_gerektir
# firma_duzenle servise eklendi
from rotalar.firma_servisi import firma_listesi, firma_ekle, firma_durum_guncelle, firma_loglari_getir, firma_duzenle

router = APIRouter(prefix="/api/firma")

class FirmaEkleIstek(BaseModel):
    firma_kodu: str
    firma_adi:  str

# Düzenleme isteği için model
class FirmaDuzenleIstek(BaseModel):
    firma_kodu: str
    firma_adi:  str

class DurumIstek(BaseModel):
    durum: bool

@router.get("")
async def listele(kullanici: dict = Depends(super_admin_gerektir)):
    sonuc = await firma_listesi()
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])

@router.post("")
async def ekle(
    istek:      FirmaEkleIstek,
    kullanici: dict = Depends(super_admin_gerektir)
):
    sonuc = await firma_ekle(
        istek.firma_kodu.strip().upper(),
        istek.firma_adi.strip(),
        kullanici["sicil"]
    )
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])

# YENİ EKLENEN: Firma Düzenleme Rotası
@router.put("/{eski_kodu}")
async def duzenle(
    eski_kodu: str,
    istek:     FirmaDuzenleIstek,
    kullanici: dict = Depends(super_admin_gerektir)
):
    sonuc = await firma_duzenle(
        eski_kodu,
        istek.firma_kodu.strip().upper(),
        istek.firma_adi.strip(),
        kullanici["sicil"]
    )
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])

@router.patch("/{firma_kodu}/durum")
async def durum_guncelle(
    firma_kodu: str,
    istek:      DurumIstek,
    kullanici:  dict = Depends(super_admin_gerektir)
):
    sonuc = await firma_durum_guncelle(firma_kodu, istek.durum, kullanici["sicil"])
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])

@router.get("/loglar")
async def loglari_getir(kullanici: dict = Depends(super_admin_gerektir)):
    sonuc = await firma_loglari_getir()
    return JSONResponse(content=sonuc["icerik"], status_code=sonuc["statu"])