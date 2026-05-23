#!/usr/bin/env python3
"""
OCPP 1.6 Charge Point Emulator
Test için kullanılacak basit şarj istasyonu simülatörü
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime, timezone
import uuid
import random
import argparse
from typing import Dict, Any
import signal
import sys

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ocpp_emulator')

class OCPPEmulator:
    def __init__(self, charge_point_id: str, central_system_url: str):
        self.charge_point_id = charge_point_id
        self.central_system_url = central_system_url
        self.websocket = None
        self.message_id_counter = 1
        self.is_running = False
        
        # Emülatör durumu
        self.connector_status = "Available"  # Available, Occupied, Charging, Faulted
        self.current_transaction_id = None
        self.current_user = None
        self.meter_value = 0  # Wh cinsinden
        self.is_authorized = False
        
        # Konfigürasyon
        self.config = {
            'vendor': 'JOINON',
            'model': 'GWJ3614T', 
            'firmware_version': '12.1.0',
            'heartbeat_interval': 300,  # 5 dakika
            'meter_values_interval': 60,  # 1 dakika
            'connector_id': 1
        }

    def get_message_id(self) -> str:
        """Yeni message ID oluştur"""
        msg_id = str(self.message_id_counter)
        self.message_id_counter += 1
        return msg_id

    def create_call_message(self, action: str, payload: Dict[str, Any]) -> str:
        """OCPP Call mesajı oluştur"""
        message = [2, self.get_message_id(), action, payload]
        return json.dumps(message)

    def create_call_result(self, message_id: str, payload: Dict[str, Any]) -> str:
        """OCPP CallResult mesajı oluştur"""
        message = [3, message_id, payload]
        return json.dumps(message)

    def create_call_error(self, message_id: str, error_code: str, error_description: str) -> str:
        """OCPP CallError mesajı oluştur"""
        message = [4, message_id, error_code, error_description, {}]
        return json.dumps(message)

    async def send_message(self, message: str):
        """WebSocket üzerinden mesaj gönder"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(message)
            logger.info(f"Sent: {message}")
        else:
            logger.warning("WebSocket connection not available")

    async def send_boot_notification(self):
        """BootNotification mesajı gönder"""
        payload = {
            "chargePointVendor": self.config['vendor'],
            "chargePointModel": self.config['model'],
            "firmwareVersion": self.config['firmware_version']
        }
        message = self.create_call_message("BootNotification", payload)
        await self.send_message(message)

    async def send_heartbeat(self):
        """Heartbeat mesajı gönder"""
        payload = {}
        message = self.create_call_message("Heartbeat", payload)
        await self.send_message(message)

    async def send_status_notification(self, status: str = None, error_code: str = "NoError"):
        """StatusNotification mesajı gönder"""
        if status:
            self.connector_status = status
            
        payload = {
            "connectorId": self.config['connector_id'],
            "errorCode": error_code,
            "status": self.connector_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        message = self.create_call_message("StatusNotification", payload)
        await self.send_message(message)

    async def send_authorize(self, id_tag: str):
        """Authorize mesajı gönder"""
        payload = {
            "idTag": id_tag
        }
        message = self.create_call_message("Authorize", payload)
        await self.send_message(message)

    async def send_start_transaction(self, id_tag: str):
        """StartTransaction mesajı gönder"""
        payload = {
            "connectorId": self.config['connector_id'],
            "idTag": id_tag,
            "meterStart": self.meter_value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        message = self.create_call_message("StartTransaction", payload)
        await self.send_message(message)

    async def send_stop_transaction(self, transaction_id: int, reason: str = "Local"):
        """StopTransaction mesajı gönder"""
        payload = {
            "transactionId": transaction_id,
            "meterStop": self.meter_value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason
        }
        message = self.create_call_message("StopTransaction", payload)
        await self.send_message(message)

    async def send_meter_values(self, transaction_id: int = None):
        """MeterValues mesajı gönder"""
        # Şarj sırasında meter değerini artır
        if self.connector_status == "Charging":
            self.meter_value += random.randint(500, 1500)  # 0.5-1.5 kWh artış

        meter_value = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sampledValue": [
                {
                    "value": str(self.meter_value),
                    "measurand": "Energy.Active.Import.Register",
                    "unit": "Wh"
                },
                {
                    "value": str(random.randint(1000, 7400)),  # 1-7.4 kW
                    "measurand": "Power.Active.Import",
                    "unit": "W"
                }
            ]
        }

        payload = {
            "connectorId": self.config['connector_id'],
            "meterValue": [meter_value]
        }
        
        if transaction_id:
            payload["transactionId"] = transaction_id

        message = self.create_call_message("MeterValues", payload)
        await self.send_message(message)

    async def handle_incoming_message(self, message: str):
        """Gelen mesajları işle"""
        try:
            data = json.loads(message)
            message_type = data[0]
            
            if message_type == 2:  # Call
                await self.handle_call(data[1], data[2], data[3])
            elif message_type == 3:  # CallResult
                await self.handle_call_result(data[1], data[2])
            elif message_type == 4:  # CallError
                await self.handle_call_error(data[1], data[2], data[3])
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_call(self, message_id: str, action: str, payload: Dict[str, Any]):
        """Gelen Call mesajlarını işle"""
        logger.info(f"Received Call: {action} - {payload}")
        
        if action == "RemoteStartTransaction":
            await self.handle_remote_start_transaction(message_id, payload)
        elif action == "RemoteStopTransaction":
            await self.handle_remote_stop_transaction(message_id, payload)
        elif action == "Reset":
            await self.handle_reset(message_id, payload)
        elif action == "GetConfiguration":
            await self.handle_get_configuration(message_id, payload)
        elif action == "ChangeConfiguration":
            await self.handle_change_configuration(message_id, payload)
        else:
            # Desteklenmeyen action
            error_msg = self.create_call_error(message_id, "NotImplemented", f"Action {action} not implemented")
            await self.send_message(error_msg)

    async def handle_remote_start_transaction(self, message_id: str, payload: Dict[str, Any]):
        """RemoteStartTransaction komutunu işle"""
        connector_id = payload.get("connectorId", 1)
        id_tag = payload.get("idTag")
        
        if self.connector_status != "Available":
            # Kabul et ama başlatma
            response = self.create_call_result(message_id, {"status": "Rejected"})
            await self.send_message(response)
            return
        
        # Kabul et
        response = self.create_call_result(message_id, {"status": "Accepted"})
        await self.send_message(response)
        
        # Şarjı başlat
        await asyncio.sleep(1)
        await self.start_charging_sequence(id_tag)

    async def handle_remote_stop_transaction(self, message_id: str, payload: Dict[str, Any]):
        """RemoteStopTransaction komutunu işle"""
        transaction_id = payload.get("transactionId")
        
        logger.info(f"Received RemoteStopTransaction for transaction {transaction_id}, current: {self.current_transaction_id}")
        
        # Herhangi bir transaction_id ile durdurma izni ver
        response = self.create_call_result(message_id, {"status": "Accepted"})
        await self.send_message(response)
        
        # Şarjı durdur
        await asyncio.sleep(1)
        await self.stop_charging_sequence()

    async def handle_reset(self, message_id: str, payload: Dict[str, Any]):
        """Reset komutunu işle"""
        reset_type = payload.get("type", "Soft")
        
        response = self.create_call_result(message_id, {"status": "Accepted"})
        await self.send_message(response)
        
        logger.info(f"Reset command received: {reset_type}")
        # Reset işlemi simülasyonu
        await asyncio.sleep(2)
        await self.send_boot_notification()

    async def handle_get_configuration(self, message_id: str, payload: Dict[str, Any]):
        """GetConfiguration komutunu işle"""
        keys = payload.get("key", [])
        
        config_values = [
            {"key": "HeartbeatInterval", "readonly": False, "value": str(self.config['heartbeat_interval'])},
            {"key": "MeterValueSampleInterval", "readonly": False, "value": str(self.config['meter_values_interval'])},
            {"key": "ConnectorPhaseRotation", "readonly": True, "value": "RST"},
            {"key": "NumberOfConnectors", "readonly": True, "value": "1"}
        ]
        
        if keys:
            config_values = [cv for cv in config_values if cv["key"] in keys]
        
        response = self.create_call_result(message_id, {
            "configurationKey": config_values,
            "unknownKey": []
        })
        await self.send_message(response)

    async def handle_change_configuration(self, message_id: str, payload: Dict[str, Any]):
        """ChangeConfiguration komutunu işle"""
        key = payload.get("key")
        value = payload.get("value")
        
        if key == "HeartbeatInterval":
            self.config['heartbeat_interval'] = int(value)
            status = "Accepted"
        elif key == "MeterValueSampleInterval":
            self.config['meter_values_interval'] = int(value)
            status = "Accepted"
        else:
            status = "NotSupported"
        
        response = self.create_call_result(message_id, {"status": status})
        await self.send_message(response)

    async def handle_call_result(self, message_id: str, payload: Dict[str, Any]):
        """CallResult mesajlarını işle"""
        logger.info(f"Received CallResult for message {message_id}: {payload}")

    async def handle_call_error(self, message_id: str, error_code: str, error_description: str):
        """CallError mesajlarını işle"""
        logger.error(f"Received CallError for message {message_id}: {error_code} - {error_description}")

    async def start_charging_sequence(self, id_tag: str):
        """Şarj başlatma sekansı"""
        logger.info(f"Starting charging sequence for {id_tag}")
        
        # 1. Authorize
        await self.send_authorize(id_tag)
        await asyncio.sleep(1)
        
        # 2. Status: Occupied
        await self.send_status_notification("Preparing")
        await asyncio.sleep(2)
        
        # 3. StartTransaction
        await self.send_start_transaction(id_tag)
        await asyncio.sleep(1)
        
        # 4. Status: Charging
        await self.send_status_notification("Charging")
        
        # Şarj durumunu ayarla
        self.current_user = id_tag
        self.current_transaction_id = random.randint(1000, 9999)  # Simulated transaction ID

    async def stop_charging_sequence(self):
        """Şarj durdurma sekansı"""
        logger.info("Stopping charging sequence")
        
        if self.current_transaction_id:
            # 1. StopTransaction
            await self.send_stop_transaction(self.current_transaction_id)
            await asyncio.sleep(1)
            
            # 2. Status: Available
            await self.send_status_notification("Available")
            
            # Durumu temizle
            self.current_transaction_id = None
            self.current_user = None

    async def periodic_heartbeat(self):
        """Periyodik heartbeat gönder"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['heartbeat_interval'])
                if self.is_running:
                    await self.send_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def periodic_meter_values(self):
        """Periyodik meter values gönder"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['meter_values_interval'])
                if self.is_running and self.connector_status == "Charging" and self.current_transaction_id:
                    await self.send_meter_values(self.current_transaction_id)
            except Exception as e:
                logger.error(f"Meter values error: {e}")

    async def connect_and_run(self):
        """Central System'e bağlan ve çalıştır"""
        try:
            logger.info(f"Connecting to {self.central_system_url} as {self.charge_point_id}")
            
            async with websockets.connect(
                f"{self.central_system_url}/{self.charge_point_id}",
                subprotocols=["ocpp1.6"],
                ping_interval=30,
                ping_timeout=10
            ) as websocket:
                self.websocket = websocket
                self.is_running = True
                
                # İlk mesajları gönder
                await self.send_boot_notification()
                await asyncio.sleep(1)
                await self.send_status_notification("Available")
                
                # Periyodik görevleri başlat
                heartbeat_task = asyncio.create_task(self.periodic_heartbeat())
                meter_task = asyncio.create_task(self.periodic_meter_values())
                
                # Mesaj dinleme
                try:
                    async for message in websocket:
                        logger.info(f"Received: {message}")
                        await self.handle_incoming_message(message)
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed by server")
                finally:
                    self.is_running = False
                    heartbeat_task.cancel()
                    meter_task.cancel()
                    
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.is_running = False

    def stop(self):
        """Emülatörü durdur"""
        logger.info("Stopping emulator...")
        self.is_running = False

async def main():
    parser = argparse.ArgumentParser(description='OCPP 1.6 Charge Point Emulator')
    parser.add_argument('--id', default='EKL0001', help='Charge Point ID')
    parser.add_argument('--url', default='ws://localhost:9000', help='Central System URL')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    emulator = OCPPEmulator(args.id, args.url)
    
    # Signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logger.info('Interrupt received, stopping emulator...')
        emulator.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while True:
            logger.info("Starting emulator...")
            await emulator.connect_and_run()
            
            if not emulator.is_running:
                logger.info("Retrying connection in 10 seconds...")
                await asyncio.sleep(10)
            else:
                break
                
    except KeyboardInterrupt:
        logger.info("Emulator stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
