(function () {
    let globalFirmaVerisi = [];

    // Excel İndirme Fonksiyonu
    function excelIndir(veriDizisi, dosyaAdi, sayfaAdi) {
        if (!veriDizisi || veriDizisi.length === 0) {
            bildirimGoster("Dışa aktarılacak veri bulunamadı.", "uyari");
            return;
        }
        try {
            const calismaSayfasi = XLSX.utils.json_to_sheet(veriDizisi);
            const calismaKitabi = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(calismaKitabi, calismaSayfasi, sayfaAdi);
            XLSX.writeFile(calismaKitabi, dosyaAdi);
        } catch (hata) {
            bildirimGoster("Excel dosyası oluşturulamadı.", "hata");
        }
    }

    // Yönetim Sekmesi (Kartların Bağlandığı Yer)
    function yonetimSekmesiAc() {
        Sekme.ac("yonetim", "Yönetim", (icerikAlani) => {
            const sablon = document.getElementById("sablon-yonetim");
            if (!sablon) return;

            icerikAlani.innerHTML = "";
            icerikAlani.appendChild(sablon.content.cloneNode(true));

            // Firma Kartı
            const firmaKarti = icerikAlani.querySelector("#kart-firma");
            if (firmaKarti) firmaKarti.addEventListener("click", firmaListesiSekmesiAc);

            // Rol Kartı
            const rolKarti = icerikAlani.querySelector("#kart-rol");
            if (rolKarti) {
                rolKarti.addEventListener("click", () => {
                    if (typeof RolYonetimi !== 'undefined') RolYonetimi.baslat();
                    else bildirimGoster("Rol modülü yüklenemedi.", "hata");
                });
            }

            // Kullanıcı Kartı
            const kullaniciKarti = icerikAlani.querySelector("#kart-kullanici");
            if (kullaniciKarti) {
                kullaniciKarti.addEventListener("click", () => {
                    if (typeof KullaniciYonetimi !== 'undefined') KullaniciYonetimi.baslat();
                    else bildirimGoster("Kullanıcı modülü yüklenemedi.", "hata");
                });
            }
        });
    }

    // Yeni Firma Ekleme Modalı (Sadece Ekleme İşlemi Yapar)
    function yeniFirmaModalAc(basariCallback) {
        const sablon = document.getElementById("sablon-firma-modal");
        if (!sablon) return;

        const modalKlon = sablon.content.cloneNode(true);
        const arkaplan = modalKlon.querySelector("#firma-modal-arkaplan");
        
        document.body.appendChild(arkaplan);

        const inputKod = arkaplan.querySelector("#modal-firma-kodu");
        const inputAdi = arkaplan.querySelector("#modal-firma-adi");
        const btnKaydet = arkaplan.querySelector("#modal-kaydet-btn");
        const btnIptal = arkaplan.querySelector("#modal-iptal-btn");

        if (inputKod) inputKod.focus();

        const kapat = () => arkaplan.remove();

        if (btnIptal) btnIptal.addEventListener("click", kapat);
        arkaplan.addEventListener("click", (e) => {
            if (e.target === arkaplan) kapat();
        });

        if (btnKaydet) {
            btnKaydet.addEventListener("click", async () => {
                const firmaKodu = inputKod.value.trim().toUpperCase();
                const firmaAdi = inputAdi.value.trim();

                if (!firmaKodu || !firmaAdi) {
                    bildirimGoster("Lütfen tüm alanları doldurun.", "uyari");
                    return;
                }

                try {
                    const yanit = await fetch("/api/firma", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ firma_kodu: firmaKodu, firma_adi: firmaAdi })
                    });

                    if (yanit.ok) {
                        kapat();
                        bildirimGoster("Firma başarıyla eklendi.", "basari");
                        if (basariCallback) basariCallback();
                    } else {
                        bildirimGoster("Firma eklenemedi (Mükerrer kod veya yetki sorunu).", "hata");
                    }
                } catch (e) {
                    bildirimGoster("Sunucu bağlantı hatası.", "hata");
                }
            });
        }
    }

    // Firma Listesi Ana Tablo
    function firmaListesiSekmesiAc() {
        Sekme.ac("firma_listesi", "Firma Yönetimi", async (icerikAlani) => {
            const sablon = document.getElementById("sablon-firma-listesi");
            if (!sablon) return;

            icerikAlani.innerHTML = "";
            icerikAlani.appendChild(sablon.content.cloneNode(true));

            const tabloGovdesi = icerikAlani.querySelector("#firma-tablo-govdesi");

            // Excel İndir Butonu
            const excelBtn = icerikAlani.querySelector("#excel-aktar-btn");
            if (excelBtn) {
                excelBtn.addEventListener("click", () => excelIndir(globalFirmaVerisi, "Firma_Listesi.xlsx", "Firmalar"));
            }

            // Logları İndir Butonu (Eksik Olan Kısım Eklendi)
            const logBtn = icerikAlani.querySelector("#log-aktar-btn");
            if (logBtn) {
                logBtn.addEventListener("click", async () => {
                    try {
                        const yanit = await fetch("/api/firma/loglar");
                        if (yanit.ok) {
                            const veriler = await yanit.json();
                            excelIndir(veriler, "Firma_Guncelleme_Loglari.xlsx", "Loglar");
                        } else {
                            bildirimGoster("Loglar alınamadı.", "hata");
                        }
                    } catch (hata) {
                        bildirimGoster("Sunucu bağlantı hatası.", "hata");
                    }
                });
            }

            // Yeni Firma Ekle Butonu
            const ekleBtn = icerikAlani.querySelector("#yeni-firma-btn");
            if (ekleBtn) {
                ekleBtn.addEventListener("click", () => {
                    yeniFirmaModalAc(() => firmaListesiSekmesiAc());
                });
            }

            // Tabloyu Doldur
            try {
                const yanit = await fetch("/api/firma");
                if (yanit.ok) {
                    const firmalar = await yanit.json();
                    globalFirmaVerisi = firmalar;

                    if (firmalar.length === 0) {
                        tabloGovdesi.innerHTML = '<tr><td colspan="5" class="yukleniyor">Kayıtlı firma bulunmuyor.</td></tr>';
                        return;
                    }

                    tabloGovdesi.innerHTML = "";
                    const satirSablonu = document.getElementById("sablon-firma-satiri");

                    firmalar.forEach(firma => {
                        const satirKlon = satirSablonu.content.cloneNode(true);

                        satirKlon.querySelector(".firma-kodu").textContent = firma["Firma Kodu"];
                        satirKlon.querySelector(".firma-adi").textContent = firma["Firma Adı"];

                        const detayMetni = `${firma["İşlem Yapan Sicil"]} — ${firma["Son İşlem Zamanı"]}`;
                        satirKlon.querySelector(".firma-detay").textContent = detayMetni;

                        let aktifMi = firma["Durum"] === "Aktif";
                        const badge = satirKlon.querySelector(".durum-badge");
                        const aksiyonBtn = satirKlon.querySelector(".aksiyon-btn");

                        function satirDurumGuncelle(durum) {
                            badge.textContent = durum ? "Aktif" : "Pasif";
                            badge.className = durum ? "badge durum-badge badge-aktif" : "badge durum-badge badge-pasif";
                            
                            if (durum) {
                                aksiyonBtn.innerHTML = `<svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg> Pasife Al`;
                                aksiyonBtn.className = "btn btn-kucuk aksiyon-btn btn-tehlike";
                            } else {
                                aksiyonBtn.innerHTML = `<svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"></path></svg> Aktifleştir`;
                                aksiyonBtn.className = "btn btn-kucuk aksiyon-btn btn-basari";
                            }
                        }

                        satirDurumGuncelle(aktifMi);

                        aksiyonBtn.addEventListener("click", async function () {
                            const yeniDurum = !aktifMi;
                            satirDurumGuncelle(yeniDurum);
                            aksiyonBtn.disabled = true;

                            try {
                                const y = await fetch(`/api/firma/${firma["Firma Kodu"]}/durum`, {
                                    method: "PATCH",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ durum: yeniDurum })
                                });

                                if (y.ok) {
                                    aktifMi = yeniDurum;
                                    const idx = globalFirmaVerisi.findIndex(f => f["Firma Kodu"] === firma["Firma Kodu"]);
                                    if (idx !== -1) globalFirmaVerisi[idx]["Durum"] = yeniDurum ? "Aktif" : "Pasif";
                                } else {
                                    satirDurumGuncelle(aktifMi);
                                    bildirimGoster("Durum güncellenemedi.", "hata");
                                }
                            } catch (e) {
                                satirDurumGuncelle(aktifMi);
                                bildirimGoster("İşlem sırasında hata oluştu.", "hata");
                            } finally {
                                aksiyonBtn.disabled = false;
                            }
                        });

                        tabloGovdesi.appendChild(satirKlon);
                    });
                }
            } catch (hata) {
                tabloGovdesi.innerHTML = '<tr><td colspan="5" class="yukleniyor">Veri çekilemedi.</td></tr>';
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        const yonetimBtn = document.querySelector('[data-sayfa="yonetim"]');
        if (yonetimBtn) yonetimBtn.addEventListener("click", yonetimSekmesiAc);
    });
})();