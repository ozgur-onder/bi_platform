import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import text
from app.core.database import SessionLocal

def get_smtp_ayarlari(db):
    # Varsayılan (root) SMTP ayarını getir
    ayar = db.execute(text("SELECT * FROM smtp_ayarlari WHERE varsayilan_mi = TRUE LIMIT 1")).fetchone()
    return ayar

def reset_maili_gonder(alici_email: str, reset_link: str):
    db = SessionLocal()
    try:
        ayar = get_smtp_ayarlari(db)
        if not ayar:
            print("HATA: Sistemde tanımlı varsayılan bir SMTP ayarı bulunamadı.")
            return False

        # Email içeriğini oluştur (Şık bir HTML şablonu)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "İş Zekası Platformu - Şifre Sıfırlama Talebi"
        msg["From"] = f"{ayar.gonderici_adi} <{ayar.kullanici_adi}>"
        msg["To"] = alici_email

        html_icerik = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f5; padding: 20px; color: #334155;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <h2 style="color: #1e293b; margin-top: 0;">Şifre Sıfırlama Talebi</h2>
                <p>Merhaba,</p>
                <p>İş Zekası Platformu hesabınız için bir şifre sıfırlama talebinde bulundunuz.</p>
                <p>Aşağıdaki butona tıklayarak yeni şifrenizi belirleyebilirsiniz:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Yeni Şifre Belirle</a>
                </div>
                <p style="font-size: 0.85rem; color: #64748b;">Eğer bu talebi siz yapmadıysanız, lütfen bu e-postayı dikkate almayın.</p>
                <p style="font-size: 0.85rem; color: #64748b;">Bu bağlantı 1 saat boyunca geçerlidir.</p>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                <p style="font-size: 0.75rem; color: #94a3b8; text-align: center;">&copy; 2026 İş Zekası Platformu</p>
            </div>
        </body>
        </html>
        """
        
        part = MIMEText(html_icerik, "html")
        msg.attach(part)

        # SMTP Sunucusuna bağlan ve maili gönder
        server = smtplib.SMTP_SSL(ayar.sunucu, ayar.port) if ayar.port == 465 else smtplib.SMTP(ayar.sunucu, ayar.port)
        
        if ayar.port != 465:
            server.starttls()
            
        server.login(ayar.kullanici_adi, ayar.sifre)
        server.sendmail(ayar.kullanici_adi, alici_email, msg.as_string())
        server.quit()
        
        print(f"BAŞARILI: {alici_email} adresine şifre sıfırlama maili gönderildi.")
        return True

    except Exception as e:
        print(f"MAİL GÖNDERİM HATASI: {e}")
        return False
    finally:
        db.close()