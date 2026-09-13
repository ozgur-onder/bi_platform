const KullaniciYonetimi = (function () {
    let globalKullaniciVerisi = [];

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

    function tarihiBicimlendir(tarihStr) {
        if (!tarihStr) return "-";
        try {
            const tarih = new Date(tarihStr);
            if (isNaN(tarih.getTime())) return tarihStr; 

            const gun = String(tarih.getDate()).padStart(2, '0');
            const ay = String(tarih.getMonth() + 1).padStart(2, '0');
            const yil = tarih.getFullYear();
            const saat = String(tarih.getHours()).padStart(2, '0');
            const dakika = String(tarih.getMinutes()).padStart(2, '0');
            const saniye = String(tarih.getSeconds()).padStart(2, '0');

            return `${gun}.${ay}.${yil} ${saat}:${dakika}:${saniye}`;
        } catch (e) {
            return tarihStr;
        }
    }

    function yeniKullaniciModalAc(basariCallback) {
        const sablon = document.getElementById("sablon-kullanici-modal");
        if (!sablon) return;

        const modalKlon = sablon.content.cloneNode(true);
        const arkaplan = modalKlon.querySelector("#kullanici-modal-arkaplan");
        
        document.body.appendChild(arkaplan);

        const inputKodu = arkaplan.querySelector("#modal-kullanici-kodu"); 
        const inputAdi = arkaplan.querySelector("#modal-kullanici-adi"); 
        const btnKaydet = arkaplan.querySelector("#modal-kullanici-kaydet-btn");
        const btnIptal = arkaplan.querySelector("#modal-kullanici-iptal-btn");

        if (inputKodu) inputKodu.focus();

        const kapat = () => arkaplan.remove();

        if (btnIptal) btnIptal.addEventListener("click", kapat);
        arkaplan.addEventListener("click", (e) => {
            if (e.target === arkaplan) kapat();
        });

        if (btnKaydet) {
            btnKaydet.addEventListener("click", async () => {
                const kullaniciKodu = inputKodu.value.trim();
                const tamAd = inputAdi.value.trim();

                if (!kullaniciKodu || !tamAd) {
                    bildirimGoster("Lütfen tüm alanları doldurun.", "uyari");
                    return;
                }

                const adParcalari = tamAd.split(" ");
                const soyad = adParcalari.length > 1 ? adParcalari.pop() : "";
                const ad = adParcalari.join(" ");

                try {
                    const yanit = await fetch("/api/kullanici", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ 
                            sicil: kullaniciKodu, 
                            ad: ad, 
                            soyad: soyad,
                            email: `${kullaniciKodu.toLowerCase()}@viontra.com`,
                            durum: true
                        })
                    });

                    if (yanit.ok) {
                        kapat();
                        if (basariCallback) basariCallback();
                    } else {
                        bildirimGoster("Kullanıcı eklenemedi.", "hata");
                    }
                } catch (e) {
                    bildirimGoster("Sunucu bağlantı hatası.", "hata");
                }
            });
        }
    }

    function kullaniciListesiSekmesiAc() {
        Sekme.ac("kullanici_listesi", "Kullanıcı Yönetimi", async (icerikAlani) => {
            const sablon = document.getElementById("sablon-kullanici-listesi");
            if (!sablon) return;

            icerikAlani.innerHTML = "";
            icerikAlani.appendChild(sablon.content.cloneNode(true));

            const tabloGovdesi = icerikAlani.querySelector("#kullanici-tablo-govdesi");

            const excelBtn = icerikAlani.querySelector("#kullanici-excel-aktar-btn");
            if (excelBtn) {
                excelBtn.addEventListener("click", () => excelIndir(globalKullaniciVerisi, "Kullanici_Listesi.xlsx", "Kullanıcılar"));
            }

            const ekleBtn = icerikAlani.querySelector("#yeni-kullanici-btn");
            if (ekleBtn) {
                ekleBtn.addEventListener("click", () => {
                    yeniKullaniciModalAc(() => kullaniciListesiSekmesiAc());
                });
            }

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

                    kullanicilar.forEach(kullanici => {
                        const satirKlon = satirSablonu.content.cloneNode(true);

                        satirKlon.querySelector(".kullanici-kodu").textContent = kullanici.sicil || "-";
                        satirKlon.querySelector(".kullanici-adi").textContent = `${kullanici.ad || ""} ${kullanici.soyad || ""}`.trim();
                        satirKlon.querySelector(".kullanici-eposta").textContent = kullanici.email || "-";

                        const islemYapanAd = kullanici.olusturan_ad_soyad || kullanici.olusturan_kullanici_id || "Sistem";
                        const formatliZaman = tarihiBicimlendir(kullanici.olusturma_zamani);
                        satirKlon.querySelector(".kullanici-detay").textContent = `${islemYapanAd} — ${formatliZaman}`;

                        // --- PASİFE AL / AKTİFLEŞTİR BUTONU ---
                        let aktifMi = kullanici.durum === true || kullanici.durum === "true";
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
                                const y = await fetch(`/api/kullanici/${kullanici.sicil}/durum`, {
                                    method: "PATCH",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ durum: yeniDurum })
                                });

                                if (y.ok) {
                                    aktifMi = yeniDurum;
                                    const idx = globalKullaniciVerisi.findIndex(k => k.sicil === kullanici.sicil);
                                    if (idx !== -1) globalKullaniciVerisi[idx].durum = yeniDurum;
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

                        // --- ŞİFRE GÖNDER BUTONU ---
                        const sifreBtn = satirKlon.querySelector(".sifre-btn");
                        sifreBtn.addEventListener("click", async function () {
                            const orjinalYazi = sifreBtn.innerText;
                            sifreBtn.innerText = "Gönderiliyor...";
                            sifreBtn.disabled = true;

                            const formVerisi = new FormData();
                            formVerisi.append("sicil", kullanici.sicil);
                            formVerisi.append("email", kullanici.email);

                            try {
                                const istek = await fetch("/sifre-sifirlama-talep", {
                                    method: "POST",
                                    body: formVerisi
                                });

                                const cevap = await istek.json();

                                if (istek.ok) {
                                    bildirimGoster(cevap.mesaj || "Şifre sıfırlama e-postası gönderildi.", "basari", 3);
                                } else {
                                    bildirimGoster(cevap.detail || "Bir hata oluştu, lütfen tekrar deneyin.", "hata");
                                }
                            } catch (hata) {
                                bildirimGoster("Sunucuya ulaşılamıyor. Lütfen bağlantınızı kontrol edin.", "hata");
                            } finally {
                                sifreBtn.innerText = orjinalYazi;
                                sifreBtn.disabled = false;
                            }
                        });

                        tabloGovdesi.appendChild(satirKlon);
                    });
                } else {
                    tabloGovdesi.innerHTML = '<tr><td colspan="6" class="yukleniyor" style="color: #ef4444;">Sunucudan veri alınamadı.</td></tr>';
                }
            } catch (hata) {
                tabloGovdesi.innerHTML = '<tr><td colspan="6" class="yukleniyor" style="color: #ef4444;">Sunucuya bağlanılamadı.</td></tr>';
            }
        });
    }

    return {
        baslat: kullaniciListesiSekmesiAc
    };
})();

window.KullaniciYonetimi = KullaniciYonetimi;

document.addEventListener("DOMContentLoaded", () => {
    document.addEventListener("click", (e) => {
        const kullaniciKarti = e.target.closest("#kart-kullanici");
        if (kullaniciKarti) {
            if (typeof window.KullaniciYonetimi !== 'undefined') {
                window.KullaniciYonetimi.baslat();
            } else {
                alert("Kullanıcı modülü yüklenemedi.");
            }
        }
    });
});