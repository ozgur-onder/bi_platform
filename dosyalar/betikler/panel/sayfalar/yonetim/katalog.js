const SistemYonetimiKatalog = (function () {

    function katalogSekmesiAc() {
        Sekme.ac("yonetim", "Sistem Yönetimi", (icerikAlani) => {
            const sablon = document.getElementById("sablon-yonetim");
            if (!sablon) return;

            icerikAlani.innerHTML = "";
            icerikAlani.appendChild(sablon.content.cloneNode(true));

            // Firma Kartı Yönlendirmesi
            const firmaKarti = icerikAlani.querySelector("#kart-firma");
            if (firmaKarti) {
                firmaKarti.addEventListener("click", () => {
                    const firmaMenuBtn = document.querySelector('[data-sayfa="firma_listesi"]');
                    if (firmaMenuBtn) {
                        firmaMenuBtn.click();
                    } else if (typeof FirmaYonetimi !== 'undefined' && FirmaYonetimi.baslat) {
                        FirmaYonetimi.baslat();
                    }
                });
            }

            // Rol Kartı Yönlendirmesi
            const rolKarti = icerikAlani.querySelector("#kart-rol");
            if (rolKarti) {
                rolKarti.addEventListener("click", () => {
                    if (typeof RolYonetimi !== 'undefined' && RolYonetimi.baslat) {
                        RolYonetimi.baslat();
                    } else {
                        bildirimGoster("Rol modülü yüklenemedi.", "hata");
                    }
                });
            }

            // Yetki Matrisi Yönlendirmesi (icerikAlani içinde doğru konumda)
            const yetkiMatrisiKarti = icerikAlani.querySelector("#kart-yetki-matrisi");
            if (yetkiMatrisiKarti) {
                yetkiMatrisiKarti.addEventListener("click", () => {
                    if (typeof YetkiMatrisi !== 'undefined' && YetkiMatrisi.baslat) {
                        YetkiMatrisi.baslat();
                    } else {
                        bildirimGoster("Yetki Matrisi modülü yüklenemedi.", "hata");
                    }
                });
            }
        });
    }

    // Sol menüdeki Sistem Yönetimi butonunu dinle
    document.addEventListener("DOMContentLoaded", () => {
        const yonetimBtn = document.querySelector('[data-sayfa="yonetim"]');
        if (yonetimBtn) {
            yonetimBtn.addEventListener("click", (e) => {
                e.preventDefault();
                katalogSekmesiAc();
            });
        }
    });

    return {
        baslat: katalogSekmesiAc
    };
})();

window.SistemYonetimiKatalog = SistemYonetimiKatalog;