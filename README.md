# ocpp1-6_emulator
OCPP 1.6 Charge Point Emulator
OCPP 1.6 protokolüne göre çalışan bir şarj istasyonu emülatörüdür. Şu işlemleri başarıyla simüle ediyor:
BootNotification
Heartbeat
StatusNotification
Authorize
StartTransaction
StopTransaction
MeterValues
RemoteStartTransaction / RemoteStopTransaction
Reset
GetConfiguration / ChangeConfiguration

Örnek Kullanımlar:
python emulator.py
Bu komut varsayılan değerlerle çalışır (id=EKL0001, url=ws://localhost:9000, verbose kapalı).


python emulator.py --id TEST123 --url ws://192.168.1.10:9000
İstasyon kimliği TEST123, bağlanacağı URL ws://192.168.1.10:9000 olur.

python emulator.py -v
Varsayılan ayarlarla çalışır, ama loglar ayrıntılı şekilde gösterilir (verbose açık).




