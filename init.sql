CREATE TABLE kullanicilar (
    id SERIAL PRIMARY KEY,
    sicil VARCHAR(20) UNIQUE NOT NULL, 
    ad VARCHAR(100) NOT NULL,
    soyad VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    parola VARCHAR(255) NOT NULL,        
    durum BOOLEAN DEFAULT TRUE,          
    olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    olusturan_kullanici_sicil VARCHAR(20)
);

CREATE TABLE iki_faktorlu_dogrulama (
    id SERIAL PRIMARY KEY,
    sicil VARCHAR(20) UNIQUE NOT NULL,
    aktif_mi BOOLEAN DEFAULT FALSE,
    gizli_anahtar VARCHAR(255),
    olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sicil) REFERENCES kullanicilar(sicil)
);

-- 2FA İÇİN YENİ EKLENEN LOG TABLOSU
CREATE TABLE iki_faktorlu_dogrulama_loglari (
    id SERIAL PRIMARY KEY,
    sicil VARCHAR(20) NOT NULL,
    islem_turu VARCHAR(50) NOT NULL, -- 'aktif_edildi', 'kapatildi', 'sifirlandi'
    islem_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    islem_yapan_kullanici_sicil VARCHAR(20) NOT NULL, 
    ip_adresi INET,
    FOREIGN KEY (sicil) REFERENCES kullanicilar(sicil)
);

CREATE TABLE firma (
    id SERIAL PRIMARY KEY,
    firma_kodu VARCHAR(50) UNIQUE NOT NULL,
    firma_adi VARCHAR(255) NOT NULL,
    durum BOOLEAN DEFAULT TRUE,            
    olusturma_guncelleme_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    olusturan_guncelleyen_sicil VARCHAR(20)
);

CREATE TABLE firma_guncelleme_loglari(
    id SERIAL PRIMARY KEY,
    firma_kodu VARCHAR(50) UNIQUE NOT NULL,
    firma_adi VARCHAR(255) NOT NULL,
    eski_durum BOOLEAN,
    yeni_durum BOOLEAN,
    islem_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    islem_yapan_kullanici_sicil VARCHAR(20)
);

CREATE TABLE roller (
    id SERIAL PRIMARY KEY,
    rol_kodu INT UNIQUE NOT NULL,          
    rol_adi VARCHAR(50) UNIQUE NOT NULL,   
    olusturma_guncelleme_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    olusturan_guncelleyen_sicil VARCHAR(20)
);

CREATE TABLE rol_guncelleme_loglari(
    id SERIAL PRIMARY KEY,
    rol_kodu VARCHAR(50) UNIQUE NOT NULL, 
    rol_adi VARCHAR(255) NOT NULL,
    eski_durum BOOLEAN,
    yeni_durum BOOLEAN,
    islem_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    islem_yapan_kullanici_sicil VARCHAR(20)
);

CREATE TABLE kullanici_yetkileri (
    id SERIAL PRIMARY KEY,
    sicil VARCHAR(20) NOT NULL,
    firma_id INT NOT NULL,
    rol_id INT NOT NULL,
    tanimlama_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tanimlayan_kullanici_sicil VARCHAR(20),   
    durum BOOLEAN DEFAULT TRUE,            
    FOREIGN KEY (sicil) REFERENCES kullanicilar(sicil),
    FOREIGN KEY (firma_id) REFERENCES firma(id),
    FOREIGN KEY (rol_id) REFERENCES roller(id),
    UNIQUE(sicil, firma_id, rol_id)
);

CREATE TABLE kullanici_giris_loglari (
    id SERIAL PRIMARY KEY,
    sicil VARCHAR(20) NOT NULL,
    durum VARCHAR(20) NOT NULL,            
    ip_adresi INET,                        
    tarayici TEXT,                 
    hata_mesaji VARCHAR(255),              
    islem_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sicil) REFERENCES kullanicilar(sicil)
);

CREATE TABLE kullanici_sifre_degisim_loglari (
    id SERIAL PRIMARY KEY,
    sicil VARCHAR(20) NOT NULL,
    tur VARCHAR(20) NOT NULL,              
    talep_eden_kullanici_sicil VARCHAR(20) NOT NULL,
    ip_adresi INET,                        
    zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sicil) REFERENCES kullanicilar(sicil)
);

CREATE TABLE sifre_sifirlama_talepleri (
    id SERIAL PRIMARY KEY,
    sicil VARCHAR(20) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    talep_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gecerlilik_suresi TIMESTAMP,           
    kullanildi BOOLEAN DEFAULT FALSE,
    ip_adresi INET,
    FOREIGN KEY (sicil) REFERENCES kullanicilar(sicil)
);

CREATE TABLE kullanici_oturumlari (
    id SERIAL PRIMARY KEY,
    sicil VARCHAR(20) NOT NULL,
    oturum_token VARCHAR(255) UNIQUE NOT NULL,
    ip_adresi INET,
    tarayici TEXT,
    giris_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    son_aktivite_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cikis_zamani TIMESTAMP,
    durum VARCHAR(20) DEFAULT 'aktif',     
    FOREIGN KEY (sicil) REFERENCES kullanicilar(sicil)
);

CREATE TABLE kullanici_yetki_guncelleme_loglari (
    id SERIAL PRIMARY KEY,
    sicil VARCHAR(20) NOT NULL,                    
    firma_id INT NOT NULL,                         
    eski_rol_id INT,                               
    yeni_rol_id INT,                               
    eski_durum BOOLEAN,                            
    yeni_durum BOOLEAN,                            
    islem_turu VARCHAR(20) NOT NULL,               
    islem_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    islem_yapan_kullanici_sicil VARCHAR(20) NOT NULL, 
    aciklama TEXT,                                 
    FOREIGN KEY (sicil) REFERENCES kullanicilar(sicil),
    FOREIGN KEY (firma_id) REFERENCES firma(id),
    FOREIGN KEY (eski_rol_id) REFERENCES roller(id),
    FOREIGN KEY (yeni_rol_id) REFERENCES roller(id)
);

CREATE TABLE smtp_ayarlari (
    id SERIAL PRIMARY KEY,
    firma_kodu VARCHAR(50),
    rol_id INT,
    rapor_kodu VARCHAR(100),
    sunucu VARCHAR(255) NOT NULL,
    port INT NOT NULL,
    kullanici_adi VARCHAR(255) NOT NULL,
    sifre VARCHAR(255) NOT NULL,
    gonderici_adi VARCHAR(255),
    varsayilan_mi BOOLEAN DEFAULT FALSE,
    olusturma_guncelleme_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    olusturan_guncelleyen_sicil VARCHAR(20),
    FOREIGN KEY (firma_kodu) REFERENCES firma(firma_kodu),
    FOREIGN KEY (rol_id) REFERENCES roller(id),
    FOREIGN KEY (olusturan_guncelleyen_sicil) REFERENCES kullanicilar(sicil)
);

-- SMTP AYARLARI LOG TABLOSU
CREATE TABLE smtp_ayarlari_loglari (
    id SERIAL PRIMARY KEY,
    smtp_ayar_id INT,
    islem_turu VARCHAR(50) NOT NULL,
    eski_sunucu VARCHAR(255),
    yeni_sunucu VARCHAR(255),
    eski_kullanici_adi VARCHAR(255),
    yeni_kullanici_adi VARCHAR(255),
    islem_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    islem_yapan_kullanici_sicil VARCHAR(20),
    FOREIGN KEY (smtp_ayar_id) REFERENCES smtp_ayarlari(id),
    FOREIGN KEY (islem_yapan_kullanici_sicil) REFERENCES kullanicilar(sicil)
);

INSERT INTO firma (firma_kodu, firma_adi, olusturan_guncelleyen_sicil) 
VALUES ('F001', 'Yönetim Merkezi', 'SYSTEM');

INSERT INTO roller (rol_kodu, rol_adi, olusturan_guncelleyen_sicil) 
VALUES (1, 'Sistem Yöneticisi', 'SYSTEM');