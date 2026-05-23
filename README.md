# OCPP 1.6 Charge Point Emulator

## Türkçe

Bu proje, test amaçlı geliştirilmiş basit bir **OCPP 1.6 Şarj İstasyonu Emülatörüdür**.  
Gerçek bir elektrikli araç şarj istasyonunu taklit ederek bir **OCPP Central System / Backend** ile WebSocket üzerinden haberleşir.

Emülatör; boot bildirimi, durum bildirimi, heartbeat, yetkilendirme, şarj başlatma/durdurma ve sayaç değerleri gönderme gibi temel OCPP akışlarını simüle eder.

---

## Özellikler

- OCPP 1.6 WebSocket bağlantısı
- `BootNotification` gönderimi
- `StatusNotification` gönderimi
- Periyodik `Heartbeat`
- Periyodik `MeterValues`
- `RemoteStartTransaction` desteği
- `RemoteStopTransaction` desteği
- `Reset` komutu desteği
- `GetConfiguration` desteği
- `ChangeConfiguration` desteği
- Bağlantı koparsa otomatik tekrar bağlanma denemesi
- Komut satırından Charge Point ID ve Central System URL belirleme

---

## Gereksinimler

- Python 3.8+
- websockets kütüphanesi

Kurulum:

```bash
pip install websockets

