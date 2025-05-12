#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento de pymodbus 3.9.2
"""
import threading
import time
from loguru import logger

from pymodbus.server import StartSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification

# Configurar logger
logger.remove()
logger.add(lambda msg: print(msg), level="DEBUG")

class ModbusTestServer:
    """Servidor Modbus RTU de prueba."""
    
    def __init__(self, port="/tmp/ttyS10"):
        """Inicializar el servidor de prueba."""
        self.port = port
        self.running = False
        self.context = None
        self.server = None
        self.server_thread = None
        
    def _create_context(self):
        """Crear el contexto del servidor Modbus."""
        # Crear un bloque de datos para registros holding
        block_size = 100
        hr_block = ModbusSequentialDataBlock(0, [0] * block_size)
        
        # Crear contexto de esclavo
        slave_context = ModbusSlaveContext(
            hr=hr_block,
            ir=ModbusSequentialDataBlock(0, [0] * block_size),
            co=ModbusSequentialDataBlock(0, [0] * block_size),
            di=ModbusSequentialDataBlock(0, [0] * block_size)
        )
        
        # Crear contexto de servidor con un solo esclavo
        slave_id = 1
        context = ModbusServerContext(slaves={slave_id: slave_context}, single=False)
        
        return context
    
    def _update_registers(self):
        """Actualizar los registros con valores de prueba."""
        slave_id = 1
        
        if not hasattr(self, 'context') or self.context is None:
            logger.error("Modbus context not initialized")
            return
            
        try:
            if hasattr(self.context, 'slaves'):
                logger.debug("Accediendo al contexto a través de slaves")
                slave_context = self.context.slaves[slave_id]
                
                # Imprimir información sobre el contexto
                logger.debug(f"Tipo de slave_context: {type(slave_context)}")
                logger.debug(f"Métodos disponibles: {dir(slave_context)}")
                
                # Intentar escribir en los registros
                try:
                    # Escribir en el registro holding (tipo 3) en la dirección 10
                    slave_context.setValues(3, 10, [42])
                    logger.info(f"Valor escrito correctamente en el registro 10")
                    
                    # Leer el valor escrito
                    value = slave_context.getValues(3, 10, 1)
                    logger.info(f"Valor leído del registro 10: {value}")
                except Exception as e:
                    logger.error(f"Error al acceder a los registros: {e}")
            else:
                logger.error("Unable to access slave context")
                return
        except Exception as e:
            logger.error(f"Error updating registers: {e}")
    
    def _server_loop(self):
        """Bucle principal del servidor para actualizar registros."""
        while self.running:
            # Actualizar registros con datos de prueba
            self._update_registers()
            
            # Esperar un tiempo
            time.sleep(1)
    
    def start(self):
        """Iniciar el servidor Modbus."""
        if self.running:
            logger.warning("Modbus server already running")
            return True
        
        try:
            # Crear contexto del servidor
            self.context = self._create_context()
            
            # Configuración del puerto serie
            port_settings = {
                'port': self.port,
                'baudrate': 9600,
                'bytesize': 8,
                'parity': 'N',
                'stopbits': 1,
                'timeout': 1
            }
            
            logger.info(f"Starting Modbus RTU server on {port_settings['port']} at {port_settings['baudrate']} baud")
            
            # Iniciar hilo del servidor para actualizar registros
            self.running = True
            self.update_thread = threading.Thread(target=self._server_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
            
            # Iniciar el servidor RTU en un hilo separado
            self._start_rtu_server(port_settings)
            
            return True
        except Exception as e:
            logger.error(f"Error starting Modbus server: {e}")
            self.running = False
            return False
    
    def _start_rtu_server(self, port_settings):
        """Iniciar el servidor Modbus RTU en un puerto serie."""
        try:
            # Crear identidad del dispositivo Modbus
            identity = ModbusDeviceIdentification()
            identity.VendorName = 'Test Server'
            identity.ProductCode = 'TS-RTU'
            identity.VendorUrl = 'https://example.com/'
            identity.ProductName = 'Test Modbus Server'
            identity.ModelName = 'Test Model'
            identity.MajorMinorRevision = '1.0'
            
            # Iniciar el servidor RTU en un hilo separado
            self.server_thread = threading.Thread(
                target=self._run_rtu_server,
                args=(port_settings, identity)
            )
            self.server_thread.daemon = True
            self.server_thread.start()
            logger.info(f"Modbus RTU server thread started")
        except Exception as e:
            logger.error(f"Error starting RTU server thread: {e}")
    
    def _run_rtu_server(self, port_settings, identity):
        """Ejecutar el servidor Modbus RTU en un hilo separado."""
        try:
            # Iniciar el servidor RTU
            self.server = StartSerialServer(
                context=self.context,
                identity=identity,
                port=port_settings['port'],
                baudrate=port_settings['baudrate'],
                bytesize=port_settings['bytesize'],
                parity=port_settings['parity'],
                stopbits=port_settings['stopbits'],
                timeout=port_settings['timeout']
            )
            # StartSerialServer bloquea este hilo hasta que se detenga el servidor
        except Exception as e:
            logger.error(f"Error in RTU server: {e}")
    
    def stop(self):
        """Detener el servidor Modbus."""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)
        
        # Detener el servidor si está en ejecución
        if hasattr(self, 'server') and self.server:
            self.server.shutdown()

if __name__ == "__main__":
    # Verificar si existe el puerto serie virtual
    import os
    if not os.path.exists("/tmp/ttyS10"):
        logger.warning("Puerto serie virtual /tmp/ttyS10 no encontrado. Ejecute scripts/setup_virtual_serial.sh primero.")
        exit(1)
    
    # Crear y ejecutar el servidor de prueba
    server = ModbusTestServer()
    try:
        server.start()
        logger.info("Servidor Modbus RTU iniciado. Presione Ctrl+C para detener.")
        # Mantener el script en ejecución
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Deteniendo el servidor...")
        server.stop()
        logger.info("Servidor detenido.")
