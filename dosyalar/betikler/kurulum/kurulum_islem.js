document.addEventListener("DOMContentLoaded", function () {
    const adInput = document.getElementById('ad');
    const soyadInput = document.getElementById('soyad');

    // Kullanıcı ad ve soyad alanlarına yazı yazarken anında BÜYÜK HARFE çevir
    if (adInput) {
        adInput.addEventListener('input', function () {
            this.value = this.value.toLocaleUpperCase('tr-TR');
        });
    }
    if (soyadInput) {
        soyadInput.addEventListener('input', function () {
            this.value = this.value.toLocaleUpperCase('tr-TR');
        });
    }

    const submitBtn = document.getElementById('submitBtn');
    const smtpTestBtn = document.getElementById('smtpTestBtn');

    // SMTP Test Et Butonu Olayı
    if (smtpTestBtn) {
        smtpTestBtn.addEventListener('click', async function () {
            const smtp_sunucu = document.getElementById('smtp-sunucu').value.trim();
            const smtp_port = document.getElementById('smtp-port').value.trim();
            const smtp_email = document.getElementById('smtp-email').value.trim();
            const smtp_sifre = document.getElementById('smtp-sifre').value;

            if (!smtp_sunucu || !smtp_port || !smtp_email || !smtp_sifre) {
                window.showNotification("Lütfen testi çalıştırmadan önce sunucu, port, e-posta ve şifre alanlarını doldurun.", "error");
                return;
            }

            if (!window.isValidEmail(smtp_email)) {
                window.showNotification("Geçerli bir gönderici e-posta adresi girin.", "error");
                return;
            }

            const originalText = smtpTestBtn.innerText;
            smtpTestBtn.innerText = "Test Ediliyor...";
            smtpTestBtn.disabled = true;

            const formData = new FormData();
            formData.append("smtp_sunucu", smtp_sunucu);
            formData.append("smtp_port", smtp_port);
            formData.append("smtp_email", smtp_email);
            formData.append("smtp_sifre", smtp_sifre);

            try {
                const response = await fetch('/kurulum-smtp-test', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    window.showNotification(data.mesaj, "success");
                } else {
                    window.showNotification(data.detail || "SMTP bağlantı testi başarısız oldu.", "error");
                }
            } catch (error) {
                console.error("Hata:", error);
                window.showNotification("Sunucuya ulaşılamıyor. Lütfen bağlantınızı kontrol edin.", "error");
            } finally {
                smtpTestBtn.innerText = originalText;
                smtpTestBtn.disabled = false;
            }
        });
    }

    // Sistemi Başlat (Kurulum Tamamla) Butonu Olayı
    if (submitBtn) {
        submitBtn.addEventListener('click', async function () {
            const ad = adInput ? adInput.value.trim() : '';
            const soyad = soyadInput ? soyadInput.value.trim() : '';
            const sicil_no = document.getElementById('sicil-no').value.trim();
            const email = document.getElementById('email').value.trim();
            const passwordInput = document.getElementById('password');
            const p1 = passwordInput ? passwordInput.value : '';
            
            const smtp_sunucu = document.getElementById('smtp-sunucu').value.trim();
            const smtp_port = document.getElementById('smtp-port').value.trim();
            const smtp_email = document.getElementById('smtp-email').value.trim();
            const smtp_sifre = document.getElementById('smtp-sifre').value;
            const smtp_gonderici = document.getElementById('smtp-gonderici').value.trim();

            if (!ad || !soyad || !sicil_no || !email) {
                window.showNotification("Lütfen yönetici kimlik bilgilerini eksiksiz doldurun.", "error");
                return;
            }

            if (!window.isValidEmail(email)) {
                window.showNotification("Lütfen geçerli bir yönetici e-posta adresi girin.", "error");
                return;
            }

            if (!smtp_sunucu || !smtp_port || !smtp_email || !smtp_sifre || !smtp_gonderici) {
                window.showNotification("Lütfen tüm mail ayarlarını eksiksiz doldurun.", "error");
                return;
            }

            if (!window.isValidEmail(smtp_email)) {
                window.showNotification("Lütfen geçerli bir gönderici e-posta adresi girin.", "error");
                return;
            }

            const originalText = submitBtn.innerText;
            submitBtn.innerText = "Kuruluyor...";
            submitBtn.disabled = true;

            const formData = new FormData();
            formData.append("ad", ad); 
            formData.append("soyad", soyad); 
            formData.append("sicil_no", sicil_no); 
            formData.append("email", email); 
            formData.append("sifre", p1);
            
            formData.append("smtp_sunucu", smtp_sunucu);
            formData.append("smtp_port", smtp_port);
            formData.append("smtp_email", smtp_email);
            formData.append("smtp_sifre", smtp_sifre);
            formData.append("smtp_gonderici", smtp_gonderici);

            try {
                const response = await fetch('/kurulum-tamamla', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    window.showNotification(data.mesaj, "success"); 
                    setTimeout(() => {
                        window.location.href = "/";
                    }, 1500);
                } else {
                    const errorData = await response.json();
                    window.showNotification(errorData.detail || "Kurulum sırasında sunucu hatası oluştu.", "error");
                    submitBtn.innerText = originalText;
                    submitBtn.disabled = false;
                }
            } catch (error) {
                console.error("Hata:", error);
                window.showNotification("Sunucuya ulaşılamıyor. Lütfen bağlantınızı kontrol edin.", "error");
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});