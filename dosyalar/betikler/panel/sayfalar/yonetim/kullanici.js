const KullaniciYonetimi = (function () {
    let globalKullaniciVerisi = [];

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

    function kullaniciListesiSekmesiAc() {
        Sekme.ac("kullanici_yonetimi", "Kullanıcı Yönetimi", async (icerikAlani) => {
            const sablon = document.getElementById("sablon-kullanici-listesi");
            if (!sablon) {
                icerikAlani.innerHTML = '<div class="sayfa-icerik"><p style="color:var(--hata-renk);">Kullanıcı şablonu yüklenemedi.</p></div>';
                return;
            }

            icerikAlani.innerHTML = "";
            icerikAlani.appendChild(sablon.content.cloneNode(true));

            const tabloGovdesi = icerikAlani.querySelector("#kullanici-tablo-govdesi");

            // Excel Aktar Butonu
            const excelBtn = icerikAlani.querySelector("#kullanici-excel-aktar-btn");
            if (excelBtn) {
                excelBtn.addEventListener("click", () => excelIndir(globalKullaniciVerisi, "Kullanici_Listesi.xlsx", "Kullanıcılar"));
            }

            // Log Aktar Butonu
            const logBtn = icerikAlani.querySelector("#kullanici-log-aktar-btn");
            if (logBtn) {
                logBtn.addEventListener("click", async () => {
                    try {
                        const yanit = await fetch("/api/kullanici/loglar");
                        if (yanit.ok) {
                            const veriler = await yanit.json();
                            excelIndir(veriler, "Kullanici_Guncelleme_Loglari.xlsx", "Loglar");
                        } else {
                            bildirimGoster("Loglar alınamadı.", "hata");
                        }
                    } catch (hata) {
                        bildirimGoster("Sunucu bağlantı hatası.", "hata");
                    }
                });
            }

            // Verileri Çek ve Listele
            try {
                const yanit = await fetch("/api/kullanici");
                if (yanit.ok) {
                    const kullanicilar = await yanit.json();
                    globalKullaniciVerisi = kullanicilar;

                    if (kullanicilar.length === 0) {
                        tabloGovdesi.innerHTML = '<tr><td colspan="6" class="yukleniyor">Kayıtlı kullanıcı bulunmuyor.</td></tr>';
                        return;
                    }

                    tabloGovdesi.innerHTML = "";
                    const satirSablonu = document.getElementById("sablon-kullanici-satiri");

                    kullanicilar.forEach(kul => {
                        const satirKlon = satirSablonu.content.cloneNode(true);

                        satirKlon.querySelector(".kullanici-sicil").textContent = kul["Sicil"];
                        satirKlon.querySelector(".kullanici-ad-soyad").textContent = `${kul["Ad"]} ${kul["Soyad"]}`;
                        satirKlon.querySelector(".kullanici-email").textContent = kul["E-Posta"];
                        satirKlon.querySelector(".kullanici-firma").textContent = kul["Firma Adı"] || "-";
                        satirKlon.querySelector(".kullanici-rol").textContent = kul["Rol Adı"] || "-";

                        let aktifMi = kul["Durum"] === "Aktif" || kul.durum === true;
                        const badge = satirKlon.querySelector(".durum-badge");

                        if (badge) {
                            badge.textContent = aktifMi ? "Aktif" : "Pasif";
                            badge.className = aktifMi ? "badge durum-badge badge-aktif" : "badge durum-badge badge-pasif";
                        }

                        tabloGovdesi.appendChild(satirKlon);
                    });
                } else {
                    tabloGovdesi.innerHTML = '<tr><td colspan="6" class="yukleniyor" style="color:var(--hata-renk);">Kullanıcılar alınamadı.</td></tr>';
                }
            } catch (hata) {
                tabloGovdesi.innerHTML = '<tr><td colspan="6" class="yukleniyor" style="color:var(--hata-renk);">Sunucu bağlantı hatası.</td></tr>';
            }
        });
    }

    // Sol Menüdeki "Kullanıcı Yönetimi" bağlantısını dinle
    document.addEventListener("DOMContentLoaded", () => {
        const menuBtn = document.querySelector('[data-sayfa="kullanici_yonetimi"]');
        if (menuBtn) {
            menuBtn.addEventListener("click", (e) => {
                e.preventDefault();
                kullaniciListesiSekmesiAc();
            });
        }
    });

    return {
        baslat: kullaniciListesiSekmesiAc
    };
})();

window.KullaniciYonetimi = KullaniciYonetimi;