window.isPasswordValid = false;

document.addEventListener("DOMContentLoaded", function () {
    // Şifre Göster/Gizle Mekanizması
    function sifreGosterGizleAyarla(btnClass, inputId, iconId) {
        const btn = document.querySelector(btnClass);
        const input = document.getElementById(inputId);
        const icon = document.getElementById(iconId);
        
        if(btn && input && icon) {
            btn.addEventListener("click", function() {
                if (input.type === "password") {
                    input.type = "text";
                    icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
                } else {
                    input.type = "password";
                    icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
                }
            });
        }
    }

    sifreGosterGizleAyarla('.sifre-goster-btn', 'password', 'eye1');
    sifreGosterGizleAyarla('.sifre-goster-btn-onay', 'password-confirm', 'eye2');
    sifreGosterGizleAyarla('.sifre-goster-btn-smtp', 'smtp-sifre', 'eye3');

    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('password-confirm');
    const passwordPopover = document.getElementById('passwordPopover');

    // Floating Popover Göster/Gizle Mantığı
    if (passwordInput && passwordPopover) {
        passwordInput.addEventListener('focus', function() {
            passwordPopover.style.display = 'block';
        });
        passwordInput.addEventListener('blur', function() {
            // Küçük bir gecikmeyle kapat (tıklama algılansın diye)
            setTimeout(() => {
                if (document.activeElement !== passwordInput) {
                    passwordPopover.style.display = 'none';
                }
            }, 200);
        });
    }

    function parolaEslesmeKontrolEt() {
        if(!passwordInput || !confirmInput) return;
        const p1 = passwordInput.value;
        const p2 = confirmInput.value;
        const msg = document.getElementById('match-msg');

        if (p2.length === 0) {
            msg.style.display = 'none';
            return;
        }
        msg.style.display = 'block';
        if (p1 === p2) {
            msg.innerText = "✔ Parolalar eşleşiyor.";
            msg.style.color = "var(--basari-renk, #10b981)";
        } else {
            msg.innerText = "✖ Parolalar eşleşmiyor.";
            msg.style.color = "var(--hata-renk, #ef4444)";
        }
    }

    if(passwordInput) {
        passwordInput.addEventListener('input', function() {
            const p = passwordInput.value;
            const checks = {
                'rule-len': p.length >= 12,
                'rule-upper': /[A-Z]/.test(p),
                'rule-lower': /[a-z]/.test(p),
                'rule-num': /\d/.test(p),
                'rule-spec': /[!@#$%^&*(),.?":{}|<>]/.test(p)
            };

            let allValid = true;
            for (const [id, passed] of Object.entries(checks)) {
                const el = document.getElementById(id);
                if (el) {
                    if (passed) {
                        el.className = 'rule-pass';
                        el.style.color = '#10b981';
                        if (!el.innerText.startsWith('✔')) {
                            el.innerText = el.innerText.replace('✖', '✔');
                        }
                    } else {
                        el.className = 'rule-fail';
                        el.style.color = '#ef4444';
                        if (!el.innerText.startsWith('✖')) {
                            el.innerText = el.innerText.replace('✔', '✖');
                        }
                    }
                }
                if (!passed) allValid = false;
            }
            window.isPasswordValid = allValid;
            parolaEslesmeKontrolEt();
        });
    }

    if(confirmInput) {
        confirmInput.addEventListener('input', parolaEslesmeKontrolEt);
    }

    // Canlı E-Posta Format Sınama (Mail Sınama)
    const emailInput = document.getElementById('email');
    const emailCheckMsg = document.getElementById('emailCheckMsg');

    if (emailInput && emailCheckMsg) {
        emailInput.addEventListener('input', function() {
            const val = emailInput.value.trim();
            if (val.length === 0) {
                emailCheckMsg.style.display = 'none';
                return;
            }
            emailCheckMsg.style.display = 'block';
            if (window.isValidEmail(val)) {
                emailCheckMsg.innerText = "✔ Geçerli e-posta formatı";
                emailCheckMsg.style.color = "#10b981";
            } else {
                emailCheckMsg.innerText = "✖ Geçersiz e-posta formatı";
                emailCheckMsg.style.color = "#ef4444";
            }
        });
    }
});