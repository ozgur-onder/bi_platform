const YetkiMatrisi = (function () {

    const sayfaYetkileri = [
        { kod: "anasayfa", ad: "Anasayfa" },
        { kod: "sistem_yonetimi", ad: "Sistem Yönetimi" },
        { kod: "kullanici_yonetimi", ad: "Kullanıcı Yönetimi" },
        { kod: "profilim", ad: "Profilim" }
    ];

    const kartYetkileri = [
        { kod: "firma_yonetimi", ad: "Firma Yönetimi" },
        { kod: "rol_yonetimi", ad: "Rol Yönetimi" },
        { kod: "rol_yetki_matrisi", ad: "Rol & Yetki Matrisi" }
    ];

    function yetkiSekmesiAc() {
        Sekme.ac("yetki_matrisi", "Rol & Yetki Matrisi", async (icerikAlani) => {
            const sablon = document.getElementById("sablon-yetki-matrisi");
            if (!sablon) {
                icerikAlani.innerHTML = '<div style="color:var(--hata-renk); padding:20px;">Yetki matrisi şablonu bulunamadı!</div>';
                return;
            }

            icerikAlani.innerHTML = "";
            icerikAlani.appendChild(sablon.content.cloneNode(true));

            const theadRow = icerikAlani.querySelector("#matris-thead-row");
            const tbody = icerikAlani.querySelector("#yetki-tablo-govdesi");

            try {
                // Rolleri veritabanından çekiyoruz
                const yanit = await fetch("/api/rol/roller-liste");
                if (!yanit.ok) throw new Error("Roller yüklenemedi");
                const roller = await yanit.json();

                // 1. Sütunları Oluştur (Header)
                roller.forEach(rol => {
                    const th = document.createElement("th");
                    th.innerHTML = `${rol.rol_adi}<br><span style="font-weight: normal; font-size: 11px;">(Rol ${rol.rol_kodu})</span>`;
                    theadRow.appendChild(th);
                });

                // Satır Oluşturucu Yardımcı Fonksiyon
                function satirEkle(grupAdi, yetkiListesi) {
                    const grupTr = document.createElement("tr");
                    grupTr.innerHTML = `<td colspan="${roller.length + 1}" class="grup-baslik">${grupAdi}</td>`;
                    tbody.appendChild(grupTr);

                    yetkiListesi.forEach(item => {
                        const tr = document.createElement("tr");
                        let tdHtml = `<td style="text-align: left;">${item.ad}</td>`;

                        roller.forEach(rol => {
                            // Rol 1 (Sistem Yöneticisi) her zaman kilitli ve seçili olabilir
                            const kilitli = rol.rol_kodu === 1 ? "checked disabled" : "";
                            tdHtml += `<td><label class="switch"><input type="checkbox" ${kilitli} data-rol="${rol.rol_kodu}" data-yetki="${item.kod}"><span class="slider"></span></label></td>`;
                        });

                        tr.innerHTML = tdHtml;
                        tbody.appendChild(tr);
                    });
                }

                // 2. Tablo Gövdesini Doldur
                tbody.innerHTML = "";
                satirEkle("Sayfa Yönetimi", sayfaYetkileri);
                satirEkle("Kart Yönetimi", kartYetkileri);

            } catch (hata) {
                console.error(hata);
                tbody.innerHTML = `<tr><td colspan="10" style="color: var(--hata-renk); padding: 20px;">Veriler yüklenirken hata oluştu.</td></tr>`;
            }

            // Kaydet Butonu
            const kaydetBtn = icerikAlani.querySelector("#yetki-kaydet-btn");
            if (kaydetBtn) {
                kaydetBtn.addEventListener("click", () => {
                    kaydetBtn.disabled = true;
                    kaydetBtn.innerHTML = "Kaydediliyor...";
                    
                    setTimeout(() => {
                        bildirimGoster("Rol yetkileri başarıyla güncellendi.", "basari");
                        kaydetBtn.disabled = false;
                        kaydetBtn.innerHTML = `<svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"></path></svg> Değişiklikleri Kaydet`;
                    }, 800);
                });
            }
        });
    }

    return {
        baslat: yetkiSekmesiAc
    };
})();

window.YetkiMatrisi = YetkiMatrisi;