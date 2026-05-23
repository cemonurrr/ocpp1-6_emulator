# OCPP 1.6 Charge Point Emulator

This repository contains a simple **OCPP 1.6 Charge Point Emulator** for testing OCPP Central System / Backend integrations.

Bu proje, test amaçlı geliştirilmiş basit bir **OCPP 1.6 Şarj İstasyonu Emülatörüdür**. OCPP Central System / Backend sistemlerini test etmek için kullanılabilir.

---

# Türkçe Dokümantasyon

## Genel Bakış

Bu emülatör, gerçek bir elektrikli araç şarj istasyonunu taklit ederek bir **OCPP 1.6 Central System** ile WebSocket üzerinden haberleşir.

Emülatör çalıştırıldığında Central System'e bağlanır, `BootNotification` gönderir, konnektör durumunu bildirir, uzaktan başlatma/durdurma komutlarını dinler ve şarj sırasında sayaç değerleri üretir.

Temel olarak aşağıdaki senaryoları test etmek için kullanılabilir:

- OCPP WebSocket bağlantısı
- Şarj istasyonu boot bildirimi
- Konnektör durum bildirimi
- Heartbeat mesajları
- RemoteStartTransaction akışı
- RemoteStopTransaction akışı
- MeterValues gönderimi
- Reset komutu
- Konfigürasyon okuma ve değiştirme

---

## Özellikler

- OCPP 1.6 WebSocket bağlantısı
- `ocpp1.6` subprotocol desteği
- `BootNotification` gönderimi
- `StatusNotification` gönderimi
- Periyodik `Heartbeat`
- Periyodik `MeterValues`
- `Authorize` mesajı gönderimi
- `StartTransaction` ve `StopTransaction` akışı
- `RemoteStartTransaction` desteği
- `RemoteStopTransaction` desteği
- `Reset` komutu desteği
- `GetConfiguration` desteği
- `ChangeConfiguration` desteği
- Bağlantı koparsa otomatik tekrar bağlanma denemesi
- Komut satırından Charge Point ID ve Central System URL belirleme

---

## Gereksinimler

- Python 3.8 veya üzeri
- `websockets` Python paketi

Bağımlılığı kurmak için:

```bash
pip install websockets
```

---

## Dosya

Ana emülatör dosyası:

```text
ocpp_emulator.py
```

---

## Kullanım

Varsayılan ayarlarla çalıştırmak için:

```bash
python ocpp_emulator.py
```

Varsayılan değerler:

```text
Charge Point ID: EKL0001
Central System URL: ws://localhost:9000
```

Bu durumda emülatör aşağıdaki adrese bağlanmaya çalışır:

```text
ws://localhost:9000/EKL0001
```

---

## Komut Satırı Parametreleri

### Charge Point ID değiştirme

```bash
python ocpp_emulator.py --id EKL0002
```

### Central System URL değiştirme

```bash
python ocpp_emulator.py --url ws://192.168.1.100:9000
```

### Detaylı log ile çalıştırma

```bash
python ocpp_emulator.py --verbose
```

veya:

```bash
python ocpp_emulator.py -v
```

### Tam örnek kullanım

```bash
python ocpp_emulator.py --id EKL0001 --url ws://localhost:9000 --verbose
```

---

## Nasıl Çalışır?

Emülatör çalıştırıldığında aşağıdaki akış gerçekleşir:

1. Verilen Central System URL adresine WebSocket bağlantısı açılır.
2. Charge Point ID bağlantı URL'sinin sonuna eklenir.
3. WebSocket bağlantısında `ocpp1.6` subprotocol kullanılır.
4. İlk olarak `BootNotification` mesajı gönderilir.
5. Ardından konnektör durumu `Available` olarak bildirilir.
6. Belirlenen aralıklarla `Heartbeat` mesajı gönderilir.
7. Central System'den gelen komutlar dinlenir.
8. `RemoteStartTransaction` komutu gelirse şarj başlatma akışı simüle edilir.
9. Şarj sırasında periyodik olarak `MeterValues` mesajları gönderilir.
10. `RemoteStopTransaction` komutu gelirse şarj sonlandırılır.
11. Bağlantı koparsa 10 saniye sonra yeniden bağlanma denenir.

---

## OCPP Başlangıç Akışı

Emülatör Central System'e bağlandıktan sonra şu mesajları gönderir:

```text
Emulator -> Central System: BootNotification
Emulator -> Central System: StatusNotification Available
```

---

## RemoteStartTransaction Akışı

Central System aşağıdaki komutu gönderdiğinde:

```text
Central System -> Emulator: RemoteStartTransaction
```

Emülatör şu adımları uygular:

```text
Emulator -> Central System: RemoteStartTransaction Accepted
Emulator -> Central System: Authorize
Emulator -> Central System: StatusNotification Preparing
Emulator -> Central System: StartTransaction
Emulator -> Central System: StatusNotification Charging
```

Bu noktadan sonra emülatör şarj durumuna geçer ve periyodik olarak sayaç değerleri gönderir:

```text
Emulator -> Central System: MeterValues
```

---

## RemoteStopTransaction Akışı

Central System aşağıdaki komutu gönderdiğinde:

```text
Central System -> Emulator: RemoteStopTransaction
```

Emülatör şu adımları uygular:

```text
Emulator -> Central System: RemoteStopTransaction Accepted
Emulator -> Central System: StopTransaction
Emulator -> Central System: StatusNotification Available
```

Şarj durumu temizlenir ve konnektör tekrar `Available` olur.

---

## Varsayılan Konfigürasyon

```text
Vendor: JOINON
Model: GWJ3614T
Firmware Version: 12.1.0
Heartbeat Interval: 300 saniye
Meter Values Interval: 60 saniye
Connector ID: 1
```

---

## Desteklenen Central System Komutları

| Komut | Açıklama |
|---|---|
| `RemoteStartTransaction` | Uzaktan şarj başlatır |
| `RemoteStopTransaction` | Uzaktan şarj durdurur |
| `Reset` | Emülatörü resetler ve yeniden BootNotification gönderir |
| `GetConfiguration` | Konfigürasyon değerlerini döner |
| `ChangeConfiguration` | Desteklenen konfigürasyon değerlerini değiştirir |

Desteklenmeyen komutlar için emülatör `NotImplemented` hatası döner.

---

## Desteklenen ChangeConfiguration Anahtarları

| Key | Açıklama |
|---|---|
| `HeartbeatInterval` | Heartbeat gönderim aralığını değiştirir |
| `MeterValueSampleInterval` | MeterValues gönderim aralığını değiştirir |

Desteklenmeyen anahtarlar için `NotSupported` cevabı döner.

---

## Sayaç Değerleri

Emülatör şarj durumundayken, yani konnektör durumu `Charging` olduğunda, her `MeterValues` periyodunda sayaç değerini artırır.

Gönderilen örnek ölçümler:

| Measurand | Açıklama | Birim |
|---|---|---|
| `Energy.Active.Import.Register` | Toplam tüketilen enerji | Wh |
| `Power.Active.Import` | Anlık güç değeri | W |

Enerji değeri her gönderimde rastgele olarak yaklaşık `500 - 1500 Wh` arasında artırılır.

Anlık güç değeri ise rastgele olarak yaklaşık `1000 - 7400 W` arasında üretilir.

---

## Loglama

Emülatör gönderilen ve alınan tüm OCPP mesajlarını terminale loglar.

Örnek log çıktısı:

```text
Connecting to ws://localhost:9000 as EKL0001
Sent: [2, "1", "BootNotification", {...}]
Received: [3, "1", {...}]
Sent: [2, "2", "StatusNotification", {...}]
```

Daha detaylı log için:

```bash
python ocpp_emulator.py --verbose
```

---

## Otomatik Yeniden Bağlanma

Central System bağlantısı koparsa emülatör 10 saniye bekler ve yeniden bağlanmayı dener.

Örnek log:

```text
Retrying connection in 10 seconds...
```

---

## Emülatörü Durdurma

Terminal üzerinden emülatörü durdurmak için:

```bash
CTRL + C
```

---

## Test Senaryosu Örneği

1. OCPP Central System / Backend uygulamanızı başlatın.
2. WebSocket portunun açık olduğundan emin olun. Örneğin: `9000`.
3. Emülatörü çalıştırın:

```bash
python ocpp_emulator.py --id EKL0001 --url ws://localhost:9000 --verbose
```

4. Backend tarafında `BootNotification` mesajının geldiğini kontrol edin.
5. Backend üzerinden `RemoteStartTransaction` gönderin.
6. Emülatörün şarj başlatma akışını tamamladığını kontrol edin.
7. `MeterValues` mesajlarının geldiğini kontrol edin.
8. Backend üzerinden `RemoteStopTransaction` gönderin.
9. Emülatörün şarjı sonlandırıp tekrar `Available` durumuna döndüğünü kontrol edin.

---

## Notlar

Bu emülatör üretim ortamı için tasarlanmamıştır. Test ve geliştirme amaçlıdır.

Gerçek bir OCPP şarj istasyonunun tüm davranışlarını kapsamaz. Temel Central System entegrasyon testleri, uzaktan başlatma/durdurma senaryoları ve sayaç verisi akışını test etmek için kullanılabilir.

---

# English Documentation

## Overview

This emulator simulates an electric vehicle charge point and communicates with an **OCPP 1.6 Central System** over WebSocket.

When started, the emulator connects to the Central System, sends a `BootNotification`, reports connector status, listens for remote start/stop commands, and sends meter values while charging.

It can be used to test the following scenarios:

- OCPP WebSocket connection
- Charge point boot notification
- Connector status notification
- Heartbeat messages
- RemoteStartTransaction flow
- RemoteStopTransaction flow
- MeterValues reporting
- Reset command
- Configuration read and update

---

## Features

- OCPP 1.6 WebSocket connection
- `ocpp1.6` subprotocol support
- Sends `BootNotification`
- Sends `StatusNotification`
- Periodic `Heartbeat`
- Periodic `MeterValues`
- Sends `Authorize`
- Supports `StartTransaction` and `StopTransaction` flows
- Supports `RemoteStartTransaction`
- Supports `RemoteStopTransaction`
- Supports `Reset`
- Supports `GetConfiguration`
- Supports `ChangeConfiguration`
- Automatic reconnect attempt after connection loss
- Configurable Charge Point ID and Central System URL via command-line arguments

---

## Requirements

- Python 3.8 or later
- `websockets` Python package

Install the dependency:

```bash
pip install websockets
```

---

## File

Main emulator file:

```text
ocpp_emulator.py
```

---

## Usage

Run with default settings:

```bash
python ocpp_emulator.py
```

Default values:

```text
Charge Point ID: EKL0001
Central System URL: ws://localhost:9000
```

In this case, the emulator will try to connect to:

```text
ws://localhost:9000/EKL0001
```

---

## Command-Line Arguments

### Change Charge Point ID

```bash
python ocpp_emulator.py --id EKL0002
```

### Change Central System URL

```bash
python ocpp_emulator.py --url ws://192.168.1.100:9000
```

### Run with verbose logging

```bash
python ocpp_emulator.py --verbose
```

or:

```bash
python ocpp_emulator.py -v
```

### Full example

```bash
python ocpp_emulator.py --id EKL0001 --url ws://localhost:9000 --verbose
```

---

## How It Works

When the emulator starts, the following flow is executed:

1. Opens a WebSocket connection to the given Central System URL.
2. Appends the Charge Point ID to the connection URL.
3. Uses the `ocpp1.6` WebSocket subprotocol.
4. Sends a `BootNotification`.
5. Reports the connector status as `Available`.
6. Sends `Heartbeat` messages at the configured interval.
7. Listens for commands from the Central System.
8. If a `RemoteStartTransaction` command is received, it simulates the charging start flow.
9. During charging, it periodically sends `MeterValues`.
10. If a `RemoteStopTransaction` command is received, it stops the charging session.
11. If the connection is lost, it attempts to reconnect after 10 seconds.

---

## OCPP Startup Flow

After connecting to the Central System, the emulator sends:

```text
Emulator -> Central System: BootNotification
Emulator -> Central System: StatusNotification Available
```

---

## RemoteStartTransaction Flow

When the Central System sends:

```text
Central System -> Emulator: RemoteStartTransaction
```

The emulator performs the following steps:

```text
Emulator -> Central System: RemoteStartTransaction Accepted
Emulator -> Central System: Authorize
Emulator -> Central System: StatusNotification Preparing
Emulator -> Central System: StartTransaction
Emulator -> Central System: StatusNotification Charging
```

After this point, the emulator enters charging state and periodically sends:

```text
Emulator -> Central System: MeterValues
```

---

## RemoteStopTransaction Flow

When the Central System sends:

```text
Central System -> Emulator: RemoteStopTransaction
```

The emulator performs:

```text
Emulator -> Central System: RemoteStopTransaction Accepted
Emulator -> Central System: StopTransaction
Emulator -> Central System: StatusNotification Available
```

The charging state is cleared and the connector becomes `Available` again.

---

## Default Configuration

```text
Vendor: JOINON
Model: GWJ3614T
Firmware Version: 12.1.0
Heartbeat Interval: 300 seconds
Meter Values Interval: 60 seconds
Connector ID: 1
```

---

## Supported Central System Commands

| Command | Description |
|---|---|
| `RemoteStartTransaction` | Starts a charging transaction remotely |
| `RemoteStopTransaction` | Stops a charging transaction remotely |
| `Reset` | Simulates reset and sends BootNotification again |
| `GetConfiguration` | Returns configuration values |
| `ChangeConfiguration` | Updates supported configuration values |

Unsupported commands return a `NotImplemented` error.

---

## Supported ChangeConfiguration Keys

| Key | Description |
|---|---|
| `HeartbeatInterval` | Changes the heartbeat interval |
| `MeterValueSampleInterval` | Changes the meter values interval |

Unsupported keys return `NotSupported`.

---

## Meter Values

When the emulator is charging, meaning the connector status is `Charging`, it increases the meter value on each `MeterValues` interval.

Sample measurements:

| Measurand | Description | Unit |
|---|---|---|
| `Energy.Active.Import.Register` | Total imported energy | Wh |
| `Power.Active.Import` | Current power value | W |

The energy value is randomly increased by approximately `500 - 1500 Wh` on each interval.

The current power value is randomly generated between approximately `1000 - 7400 W`.

---

## Logging

The emulator logs all sent and received OCPP messages to the terminal.

Example log output:

```text
Connecting to ws://localhost:9000 as EKL0001
Sent: [2, "1", "BootNotification", {...}]
Received: [3, "1", {...}]
Sent: [2, "2", "StatusNotification", {...}]
```

For more detailed logs:

```bash
python ocpp_emulator.py --verbose
```

---

## Automatic Reconnect

If the Central System connection is lost, the emulator waits for 10 seconds and then attempts to reconnect.

Example log:

```text
Retrying connection in 10 seconds...
```

---

## Stopping the Emulator

To stop the emulator from the terminal:

```bash
CTRL + C
```

---

## Example Test Scenario

1. Start your OCPP Central System / Backend application.
2. Make sure the WebSocket port is open. For example: `9000`.
3. Start the emulator:

```bash
python ocpp_emulator.py --id EKL0001 --url ws://localhost:9000 --verbose
```

4. Check that the backend receives the `BootNotification`.
5. Send a `RemoteStartTransaction` command from the backend.
6. Verify that the emulator completes the charging start flow.
7. Check that `MeterValues` messages are received.
8. Send a `RemoteStopTransaction` command from the backend.
9. Verify that the emulator stops charging and returns to `Available` status.

---

## Notes

This emulator is not designed for production use. It is intended for testing and development.

It does not implement every behavior of a real OCPP charge point. It is useful for testing basic Central System integrations, remote start/stop scenarios, and meter value communication.
