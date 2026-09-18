const RolYonetimi = (function () {
    let globalRolVerisi = [];

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

    function rolModalAc(rolVerisi = null, basariCallback) {
        const sablon = document.getElementById("sablon-rol-modal");
        if (!sablon) return;

        const modalKlon = sablon.content.cloneNode(true);
        const arkaplan = modalKlon.querySelector("#rol-modal-arkaplan");
        document.body.appendChild(arkaplan);

        const baslik = arkaplan.querySelector("#modal-rol-baslik");
        const inputEskiKod = arkaplan.querySelector("#modal-rol-eski-kodu");
        const inputKod = arkaplan.querySelector("#modal-rol-kodu");
        const inputAdi = arkaplan.querySelector("#modal-rol-adi");
        const btnKaydet = arkaplan.querySelector("#modal-kaydet-btn");
        const btnIptal = arkaplan.querySelector("#modal-iptal-btn");

        if (rolVerisi) {
            baslik.textContent = "Rol Düzenle";
            const r_kodu = rolVerisi["Rol Kodu"] || rolVerisi.rol_id || rolVerisi.id;
            inputEskiKod.value = r_kodu;
            inputKod.value = r_kodu;
            inputAdi.value = rolVerisi["Rol Adı"] || rolVerisi.rol_adi;
            btnKaydet.textContent = "Güncelle";
        }

        if (inputKod) inputKod.focus();

        const kapat = () => arkaplan.remove();
        if (btnIptal) btnIptal.addEventListener("click", kapat);
        arkaplan.addEventListener("click", (e) => {
            if (e.target === arkaplan) kapat();
        });

        if (btnKaydet) {
            btnKaydet.addEventListener("click", async () => {
                const eskiKod = inputEskiKod.value;
                const rolKodu = inputKod.value.trim();
                const rolAdi = inputAdi.value.trim();

                if (!rolKodu || !rolAdi) {
                    bildirimGoster("Lütfen tüm alanları doldurun.", "uyari");
                    return;
                }

                // DÜZELTME BURADA: rol_id yerine rol_kodu kullanıyoruz ve tam sayıya (integer) çeviriyoruz.
                const payload = { 
                    rol_kodu: parseInt(rolKodu, 10), 
                    rol_adi: rolAdi 
                };
                
                const endpoint = eskiKod ? `/api/rol/${eskiKod}` : "/api/rol";
                const method = eskiKod ? "PUT" : "POST";

                try {
                    const yanit = await fetch(endpoint, {
                        method: method,
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });

                    if (yanit.ok) {
                        kapat();
                        bildirimGoster(eskiKod ? "Rol başarıyla güncellendi." : "Rol başarıyla eklendi.", "basari");
                        if (basariCallback) basariCallback();
                    } else {
                        bildirimGoster("İşlem başarısız oldu (Yetki sorunu veya kayıt mevcut olabilir).", "hata");
                    }
                } catch (e) {
                    bildirimGoster("Sunucu bağlantı hatası.", "hata");
                }
            });
        }
    }

    function rolListesiSekmesiAc() {
        Sekme.ac("rol_listesi", "Rol Yönetimi", async (icerikAlani) => {
            const sablon = document.getElementById("sablon-rol-listesi");
            if (!sablon) return;

            icerikAlani.innerHTML = "";
            icerikAlani.appendChild(sablon.content.cloneNode(true));
            const tabloGovdesi = icerikAlani.querySelector("#rol-tablo-govdesi");

            const excelBtn = icerikAlani.querySelector("#rol-excel-aktar-btn");
            if (excelBtn) {
                excelBtn.addEventListener("click", () => excelIndir(globalRolVerisi, "Rol_Listesi.xlsx", "Roller"));
            }

            const logBtn = icerikAlani.querySelector("#rol-log-aktar-btn");
            if (logBtn) {
                logBtn.addEventListener("click", async () => {
                    try {
                        const yanit = await fetch("/api/rol/loglar");
                        if (yanit.ok) {
                            const veriler = await yanit.json();
                            excelIndir(veriler, "Rol_Guncelleme_Loglari.xlsx", "Loglar");
                        } else {
                            bildirimGoster("Loglar alınamadı.", "hata");
                        }
                    } catch (hata) {
                        bildirimGoster("Sunucu bağlantı hatası.", "hata");
                    }
                });
            }

            const ekleBtn = icerikAlani.querySelector("#yeni-rol-btn");
            if (ekleBtn) {
                ekleBtn.addEventListener("click", () => {
                    rolModalAc(null, () => rolListesiSekmesiAc());
                });
            }

            try {
                const yanit = await fetch("/api/rol");
                if (yanit.ok) {
                    const roller = await yanit.json();
                    globalRolVerisi = roller;

                    if (roller.length === 0) {
                        tabloGovdesi.innerHTML = '<tr><td colspan="5" class="yukleniyor">Kayıtlı rol bulunmuyor.</td></tr>';
                        return;
                    }

                    tabloGovdesi.innerHTML = "";
                    const satirSablonu = document.getElementById("sablon-rol-satiri");

                    roller.forEach(rol => {
                        const satirKlon = satirSablonu.content.cloneNode(true);

                        const r_id = rol["Rol Kodu"] || rol.rol_id || rol.id;
                        const r_adi = rol["Rol Adı"] || rol.rol_adi;
                        const r_islem_yapan = rol["İşlem Yapan Sicil"] || rol.islem_yapan_sicil || "SİSTEM";
                        const r_islem_zaman = rol["Son İşlem Zamanı"] || rol.islem_zamani || "";

                        satirKlon.querySelector(".rol-kodu").textContent = r_id;
                        satirKlon.querySelector(".rol-adi").textContent = r_adi;

                        const detayMetni = `${r_islem_yapan} — ${r_islem_zaman}`;
                        satirKlon.querySelector(".rol-detay").textContent = detayMetni;

                        let aktifMi = rol["Durum"] === "Aktif" || rol.durum === true;
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

                        const duzenleBtn = satirKlon.querySelector(".duzenle-btn");
                        duzenleBtn.addEventListener("click", () => {
                            rolModalAc(rol, () => rolListesiSekmesiAc());
                        });

                        aksiyonBtn.addEventListener("click", async function () {
                            const yeniDurum = !aktifMi;
                            satirDurumGuncelle(yeniDurum);
                            aksiyonBtn.disabled = true;

                            try {
                                const y = await fetch(`/api/rol/${r_id}/durum`, {
                                    method: "PATCH",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ durum: yeniDurum })
                                });

                                if (y.ok) {
                                    aktifMi = yeniDurum;
                                    const idx = globalRolVerisi.findIndex(r => (r["Rol Kodu"] || r.rol_id || r.id) == r_id);
                                    if (idx !== -1) {
                                        if (globalRolVerisi[idx]["Durum"] !== undefined) {
                                            globalRolVerisi[idx]["Durum"] = yeniDurum ? "Aktif" : "Pasif";
                                        } else {
                                            globalRolVerisi[idx].durum = yeniDurum;
                                        }
                                    }
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
                } else {
                    tabloGovdesi.innerHTML = '<tr><td colspan="5" class="yukleniyor">Sunucudan veri alınamadı.</td></tr>';
                }
            } catch (hata) {
                tabloGovdesi.innerHTML = '<tr><td colspan="5" class="yukleniyor">Sunucuya bağlanılamadı.</td></tr>';
            }
        });
    }

    return {
        baslat: rolListesiSekmesiAc
    };
})();

window.RolYonetimi = RolYonetimi;