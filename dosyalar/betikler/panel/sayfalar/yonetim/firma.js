const FirmaYonetimi = (function () {
    let globalFirmaVerisi = [];

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
                    bildirimGoster("Lütfen tüm alanları doldurun.", "hata");
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
                        bildirimGoster("Firma eklenemedi (Mükerrer kod veya yetki sorunu olabilir).", "hata");
                    }
                } catch (e) {
                    bildirimGoster("Sunucu bağlantı hatası.", "hata");
                }
            });
        }
    }

    function firmaListesiSekmesiAc() {
        Sekme.ac("firma_listesi", "Firma Yönetimi", async (icerikAlani) => {
            const sablon = document.getElementById("sablon-firma-listesi");
            if (!sablon) {
                icerikAlani.innerHTML = '<div style="color:var(--hata-renk); padding:20px;">Firma listesi şablonu bulunamadı!</div>';
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
                        if (yanit.ok) {
                            excelIndir(await yanit.json(), "Firma_Guncelleme_Loglari.xlsx", "Loglar");
                        } else {
                            bildirimGoster("Loglar alınamadı.", "hata");
                        }
                    } catch (hata) {
                        bildirimGoster("Sunucu bağlantı hatası.", "hata");
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
                            badge.className = durum ? "badge durum-badge badge-aktif" : "badge durum-badge badge-pasif";
                            aksiyonBtn.textContent = durum ? "Pasife Al" : "Aktifleştir";
                            aksiyonBtn.className = durum ? "btn-ikincil aksiyon-btn btn-tehlike" : "btn-ikincil aksiyon-btn btn-basari";
                        }

                        satirDurumGuncelle(aktifMi);

                        // Sistem Firması (F001) Koruması
                        if (firma["Firma Kodu"] === "F001") {
                            aksiyonBtn.disabled = true;
                            aksiyonBtn.style.opacity = "0.4";
                            aksiyonBtn.style.cursor = "not-allowed";
                            aksiyonBtn.title = "Sistem firması pasife alınamaz.";
                        } else {
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
                                        bildirimGoster("Firma durumu güncellendi.", "basari");
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
                        }

                        tabloGovdesi.appendChild(satirKlon);
                    });
                } else {
                    tabloGovdesi.innerHTML = '<tr><td colspan="5" class="yukleniyor">Firmalar alınamadı.</td></tr>';
                }
            } catch (hata) {
                tabloGovdesi.innerHTML = '<tr><td colspan="5" class="yukleniyor">Sunucu bağlantı hatası.</td></tr>';
            }
        });
    }

    return {
        baslat: firmaListesiSekmesiAc
    };
})();

window.FirmaYonetimi = FirmaYonetimi;