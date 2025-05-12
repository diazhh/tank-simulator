"""
MQTT client for communicating with ThingsBoard.
"""
import json
import time
from typing import Dict, List, Optional

import paho.mqtt.client as mqtt
import yaml
from loguru import logger

from ..models.tank import Tank


class MQTTClient:
    """
    MQTT client for sending tank data to ThingsBoard.
    
    Attributes:
        client (mqtt.Client): MQTT client instance
        config (Dict): MQTT configuration
        connected (bool): Connection status
        tanks (Dict[str, Tank]): Dictionary mapping tank IDs to tanks
        last_telemetry_time (Dict[str, float]): Last telemetry publish time for each tank
        last_attributes_time (Dict[str, float]): Last attributes publish time for each tank
    """
    
    def __init__(self, tanks: List[Tank], config_path: str):
        """
        Initialize the MQTT client.
        
        Args:
            tanks: List of tanks to monitor
            config_path: Path to the communication configuration file
        """
        self.config = self._load_config(config_path)
        self.client = mqtt.Client(client_id=self.config['mqtt']['client_id'])
        self.connected = False
        
        # Create a dictionary for quick lookup of tanks by ID
        self.tanks = {tank.id: tank for tank in tanks}
        
        # Track last publish times
        self.last_telemetry_time = {tank_id: 0 for tank_id in self.tanks}
        self.last_attributes_time = {tank_id: 0 for tank_id in self.tanks}
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        
        # Set up authentication if provided
        if 'username' in self.config['mqtt'] and 'password' in self.config['mqtt']:
            self.client.username_pw_set(
                self.config['mqtt']['username'],
                self.config['mqtt']['password']
            )
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.connected = True
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        logger.warning(f"Disconnected from MQTT broker with code {rc}")
        self.connected = False
    
    def _on_publish(self, client, userdata, mid):
        """Callback for when a message is published."""
        logger.debug(f"Message {mid} published")
    
    def connect(self) -> bool:
        """
        Connect to the MQTT broker.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            self.client.connect(
                self.config['mqtt']['broker'],
                self.config['mqtt']['port'],
                self.config['mqtt']['connection']['keep_alive']
            )
            self.client.loop_start()
            
            # Wait for connection to establish
            timeout = 5
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
    
    # Eliminamos la función publish_telemetry ya que no se envía telemetría por MQTT
    
    def publish_tank_asset(self, tank_id: str) -> bool:
        """
        Publicar un tanque como asset en ThingsBoard.
        
        Args:
            tank_id: ID del tanque a publicar
            
        Returns:
            True si la publicación fue exitosa, False en caso contrario
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        if tank_id not in self.tanks:
            logger.error(f"Tank {tank_id} not found")
            return False
        
        tank = self.tanks[tank_id]
        
        # Convertir dimensiones de metros a milímetros
        height_mm = int(tank.height * 1000)
        diameter_mm = int(tank.diameter * 1000)
        
        # Calcular los niveles de alarma (en milímetros)
        # Alarma alta: 90% de la altura
        high_alarm = int(height_mm * 0.90)
        # Alarma alta alta: 95% de la altura
        high_high_alarm = int(height_mm * 0.95)
        # Alarma baja: 15% de la altura
        low_alarm = int(height_mm * 0.15)
        # Alarma baja baja: 10% de la altura
        low_low_alarm = int(height_mm * 0.10)
        
        # Crear payload para el asset del tanque
        tank_asset = {
            "id": tank.id,
            "name": tank.id,
            "type": "Tank",
            "patio": tank.patio,
            "product": tank.product.value,
            "height_mm": height_mm,
            "diameter_mm": diameter_mm,
            "capacity": tank.capacity,
            "tank_type": tank.tank_type.value,
            "max_level_mm": height_mm,
            "min_level_mm": 0,
            "high_alarm_mm": high_alarm,
            "high_high_alarm_mm": high_high_alarm,
            "low_alarm_mm": low_alarm,
            "low_low_alarm_mm": low_low_alarm
        }
        
        # Convertir la tabla de aforo a formato más adecuado para ThingsBoard
        # Formato: array de objetos con nivel y volumen
        strapping_table_array = [
            {"level_mm": level, "volume_barrels": volume}
            for level, volume in sorted(tank.strapping_table.items())
        ]
        
        # Agregar la tabla de calibración (strapping table)
        tank_asset["strapping_table"] = strapping_table_array
        
        # Formato para el asset en ThingsBoard
        asset_payload = {
            "asset": tank.id,
            "type": "Tank",
            "attributes": tank_asset
        }
        
        # Tópico para assets
        topic = f"{self.config['mqtt']['thingsboard']['base_topic']}/assets"
        
        # Publicar mensaje
        try:
            result = self.client.publish(
                topic,
                json.dumps(asset_payload),
                qos=self.config['mqtt']['qos'],
                retain=self.config['mqtt']['retain']
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published tank asset {tank_id}")
                return True
            else:
                logger.error(f"Failed to publish tank asset {tank_id}: {result}")
                return False
        except Exception as e:
            logger.error(f"Error publishing tank asset {tank_id}: {e}")
            return False
    
    def publish_patios_as_assets(self) -> bool:
        """
        Publicar los patios como assets en ThingsBoard.
        
        Returns:
            True si la publicación fue exitosa, False en caso contrario
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        # Obtener los patios únicos
        patios = set(tank.patio for tank in self.tanks.values())
        
        # Publicar cada patio como un asset
        for patio in patios:
            # Crear payload para el asset del patio
            patio_asset = {
                "asset": patio,
                "type": "Patio",
                "attributes": {
                    "name": patio,
                    "type": "Patio"
                }
            }
            
            # Tópico para assets
            topic = f"{self.config['mqtt']['thingsboard']['base_topic']}/assets"
            
            try:
                result = self.client.publish(
                    topic,
                    json.dumps(patio_asset),
                    qos=self.config['mqtt']['qos'],
                    retain=self.config['mqtt']['retain']
                )
                
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    logger.error(f"Failed to publish patio asset {patio}: {result}")
                    return False
                
                logger.info(f"Published patio asset {patio}")
            except Exception as e:
                logger.error(f"Error publishing patio asset {patio}: {e}")
                return False
        
        return True
    
    def publish_all_tanks_as_assets(self) -> bool:
        """
        Publicar todos los tanques como assets en ThingsBoard.
        
        Returns:
            True si la publicación fue exitosa, False en caso contrario
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        # Publicar cada tanque como un asset
        for tank_id in self.tanks:
            if not self.publish_tank_asset(tank_id):
                return False
            
            # Pequeña pausa para evitar sobrecargar el broker
            time.sleep(0.1)
        
        return True
    
    def initialize_mqtt(self) -> bool:
        """
        Inicializar la conexión MQTT y publicar los assets (patios y tanques) una sola vez.
        
        Returns:
            True si la inicialización fue exitosa, False en caso contrario
        """
        # Verificar si MQTT está habilitado
        mqtt_enabled = self.config['mqtt'].get('enabled', True)
        if not mqtt_enabled:
            logger.info("MQTT is disabled in configuration")
            return False
        
        # Intentar conectar
        if not self.connected:
            if not self.connect():
                logger.error("Failed to connect to MQTT broker")
                return False
        
        # Publicar patios como assets
        logger.info("Publishing patios as assets...")
        if not self.publish_patios_as_assets():
            logger.error("Failed to publish patios as assets")
            return False
        
        # Publicar tanques como assets
        logger.info("Publishing tanks as assets...")
        if not self.publish_all_tanks_as_assets():
            logger.error("Failed to publish tanks as assets")
            return False
        
        logger.info("All assets published successfully")
        return True
    
    def update(self) -> None:
        """Este método no hace nada ya que solo enviamos los assets una vez al inicio."""
        # No hacemos nada aquí, ya que los assets se publican solo una vez al inicio
        pass
