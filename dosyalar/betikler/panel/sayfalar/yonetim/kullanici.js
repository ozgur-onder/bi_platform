(function () {
    let globalFirmaVerisi = [];

    function excelIndir(veriDizisi, dosyaAdi, sayfaAdi) {
        if (!veriDizisi || veriDizisi.length === 0) {
            alert("Dışa aktarılacak veri bulunamadı.");
            return;
        }
        try {
            const calismaSayfasi = XLSX.utils.json_to_sheet(veriDizisi);
            const calismaKitabi = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(calismaKitabi, calismaSayfasi, sayfaAdi);
            XLSX.writeFile(calismaKitabi, dosyaAdi);
        } catch (hata) {
            alert("Excel dosyası oluşturulamadı.");
        }
    }

    function yonetimSekmesiAc() {
        Sekme.ac("yonetim", "Yönetim", (icerikAlani) => {
            const sablon = document.getElementById("sablon-yonetim");
            if (!sablon) {
                console.error("sablon-yonetim bulunamadı!");
                return;
            }

            icerikAlani.innerHTML = "";
            icerikAlani.appendChild(sablon.content.cloneNode(true));

            // FİRMA KARTI BAĞLANTISI
            const firmaKarti = icerikAlani.querySelector("#kart-firma");
            if (firmaKarti) {
                firmaKarti.addEventListener("click", firmaListesiSekmesiAc);
            }

            // ROL KARTI BAĞLANTISI
            const rolKarti = icerikAlani.querySelector("#kart-rol");
            if (rolKarti) {
                rolKarti.addEventListener("click", () => {
                    if (typeof RolYonetimi !== 'undefined') {
                        RolYonetimi.baslat();
                    } else {
                        alert("Rol modülü yüklenemedi.");
                    }
                });
            }

            // KULLANICI KARTI BAĞLANTISI
            const kullaniciKarti = icerikAlani.querySelector("#kart-kullanici");
            if (kullaniciKarti) {
                kullaniciKarti.addEventListener("click", () => {
                    if (typeof KullaniciYonetimi !== 'undefined') {
                        KullaniciYonetimi.baslat();
                    } else {
                        alert("Kullanıcı modülü yüklenemedi.");
                    }
                });
            }
        });
    }

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
                    alert("Lütfen tüm alanları doldurun.");
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
                        if (basariCallback) basariCallback();
                    } else {
                        alert("Firma eklenemedi (Mükerrer kod veya yetki sorunu).");
                    }
                } catch (e) {
                    alert("Sunucu bağlantı hatası.");
                }
            });
        }
    }

    function firmaListesiSekmesiAc() {
        Sekme.ac("firma_listesi", "Firma Yönetimi", async (icerikAlani) => {
            const sablon = document.getElementById("sablon-firma-listesi");
            if (!sablon) {
                console.error("sablon-firma-listesi bulunamadı!");
                return;
            }

            icerikAlani.innerHTML = "";
            icerikAlani.appendChild(sablon.content.cloneNode(true));

            const tabloGovdesi = icerikAlani.querySelector("#firma-tablo-govdesi");

            const excelBtn = icerikAlani.querySelector("#excel-aktar-btn");
            if (excelBtn) {
                excelBtn.addEventListener("click", () => excelIndir(globalFirmaVerisi, "Firma_Listesi.xlsx", "Firmalar"));
            }

            const logBtn = icerikAlani.querySelector("#log-aktar-btn");
            if (logBtn) {
                logBtn.addEventListener("click", async () => {
                    try {
                        const yanit = await fetch("/api/firma/loglar");
                        if (yanit.ok) excelIndir(await yanit.json(), "Firma_Guncelleme_Loglari.xlsx", "Loglar");
                        else alert("Loglar alınamadı.");
                    } catch (hata) {
                        alert("Sunucu bağlantı hatası.");
                    }
                });
            }

            const ekleBtn = icerikAlani.querySelector("#yeni-firma-btn");
            if (ekleBtn) {
                ekleBtn.addEventListener("click", () => {
                    yeniFirmaModalAc(() => firmaListesiSekmesiAc());
                });
            }

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
                            badge.classList.remove("badge-aktif", "badge-pasif");
                            badge.classList.add(durum ? "badge-aktif" : "badge-pasif");
                            aksiyonBtn.textContent = durum ? "Pasife Al" : "Aktifleştir";
                            aksiyonBtn.classList.remove("btn-tehlike", "btn-basari");
                            aksiyonBtn.classList.add(durum ? "btn-tehlike" : "btn-basari");
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
                                    alert("Durum güncellenemedi.");
                                }
                            } catch (e) {
                                satirDurumGuncelle(aktifMi);
                                alert("İşlem sırasında hata oluştu.");
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
        if (yonetimBtn) {
            yonetimBtn.addEventListener("click", yonetimSekmesiAc);
        }
    });
})();