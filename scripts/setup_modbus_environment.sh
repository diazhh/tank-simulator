#!/bin/bash

# Script de instalación para configurar el entorno de simulación de tanques con Modbus RTU
# Este script instala todas las dependencias necesarias y configura los puertos seriales virtuales

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Configuración del entorno para simulador de tanques con Modbus RTU ===${NC}"

# Función para verificar si un comando está disponible
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar si se está ejecutando como root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Este script debe ejecutarse como root o con sudo${NC}"
    exit 1
fi

# Detectar el sistema operativo
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo -e "${RED}No se pudo detectar el sistema operativo${NC}"
    exit 1
fi

echo -e "${YELLOW}Sistema operativo detectado: $OS $VER${NC}"

# Instalar dependencias según el sistema operativo
echo -e "${GREEN}Instalando dependencias del sistema...${NC}"

if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt-get update
    apt-get install -y python3 python3-pip python3-venv socat udev
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
    yum -y update
    yum -y install python3 python3-pip socat udev
elif [[ "$OS" == *"SUSE"* ]]; then
    zypper refresh
    zypper install -y python3 python3-pip socat udev
else
    echo -e "${RED}Sistema operativo no soportado: $OS${NC}"
    echo -e "${YELLOW}Intente instalar manualmente: python3, python3-pip, socat y udev${NC}"
fi

# Verificar si socat está instalado
if ! command_exists socat; then
    echo -e "${RED}Error: socat no pudo ser instalado. Por favor, instálelo manualmente.${NC}"
    exit 1
fi

echo -e "${GREEN}Creando directorio para scripts de socat...${NC}"
mkdir -p /tmp/socat_pids

# Crear el script para los puertos seriales virtuales
echo -e "${GREEN}Creando script para puertos seriales virtuales...${NC}"
cat > /var/new-tank-simulator/scripts/setup_virtual_serial.sh << 'EOF'
#!/bin/bash

# Script para crear puertos seriales virtuales para Modbus RTU

# Crear directorio para almacenar los PIDs de los procesos socat
mkdir -p /tmp/socat_pids

# Matar cualquier instancia previa de socat
echo "Cerrando instancias previas de socat..."
if [ -d "/tmp/socat_pids" ]; then
    for pid_file in /tmp/socat_pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if kill -0 $pid 2>/dev/null; then
                echo "Terminando proceso socat con PID $pid"
                kill $pid
            fi
            rm -f "$pid_file"
        fi
    done
fi

# Crear pares de puertos seriales virtuales
echo "Creando puertos seriales virtuales..."

# Primer par para comunicación principal
echo "Creando par PTY1 <-> PTY2 para comunicación principal..."
socat -d -d pty,raw,echo=0,link=/tmp/ttyS10 pty,raw,echo=0,link=/tmp/ttyS11 &
echo $! > /tmp/socat_pids/socat_main.pid
sleep 1

# Asignar permisos adecuados
chmod 666 /tmp/ttyS10
chmod 666 /tmp/ttyS11

echo "Puertos seriales virtuales creados:"
echo "  - Servidor Modbus RTU: /tmp/ttyS10"
echo "  - Cliente Modbus RTU: /tmp/ttyS11"
echo ""
echo "Para usar estos puertos en el simulador, configura los parámetros en config/communication.yaml"
echo "Para detener los puertos virtuales: kill \$(cat /tmp/socat_pids/*.pid)"
EOF

chmod +x /var/new-tank-simulator/scripts/setup_virtual_serial.sh

# Crear un servicio systemd para iniciar los puertos seriales al arranque
echo -e "${GREEN}Creando servicio systemd para puertos seriales virtuales...${NC}"
cat > /etc/systemd/system/virtual-serial-ports.service << EOF
[Unit]
Description=Virtual Serial Ports for Modbus RTU
After=network.target

[Service]
Type=simple
ExecStart=/var/new-tank-simulator/scripts/setup_virtual_serial.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Configurar entorno Python
echo -e "${GREEN}Configurando entorno Python...${NC}"
if [ ! -d "/var/new-tank-simulator/venv" ]; then
    python3 -m venv /var/new-tank-simulator/venv
fi

# Instalar dependencias Python
echo -e "${GREEN}Instalando dependencias Python...${NC}"
/var/new-tank-simulator/venv/bin/pip install --upgrade pip
/var/new-tank-simulator/venv/bin/pip install pymodbus==3.9.2 paho-mqtt==2.2.1 pyyaml==6.0 loguru==0.7.2

# Habilitar y arrancar el servicio
echo -e "${GREEN}Habilitando servicio de puertos seriales virtuales...${NC}"
systemctl daemon-reload
systemctl enable virtual-serial-ports.service
systemctl start virtual-serial-ports.service

# Verificar estado del servicio
if systemctl is-active --quiet virtual-serial-ports.service; then
    echo -e "${GREEN}Servicio de puertos seriales virtuales iniciado correctamente${NC}"
else
    echo -e "${RED}Error al iniciar el servicio de puertos seriales virtuales${NC}"
    echo -e "${YELLOW}Intente ejecutar manualmente: /var/new-tank-simulator/scripts/setup_virtual_serial.sh${NC}"
fi

# Crear script para iniciar el simulador
echo -e "${GREEN}Creando script para iniciar el simulador...${NC}"
cat > /var/new-tank-simulator/start_simulator.sh << 'EOF'
#!/bin/bash

# Activar entorno virtual
source /var/new-tank-simulator/venv/bin/activate

# Verificar que los puertos seriales estén activos
if [ ! -e "/tmp/ttyS10" ] || [ ! -e "/tmp/ttyS11" ]; then
    echo "Los puertos seriales virtuales no están configurados. Configurando..."
    bash /var/new-tank-simulator/scripts/setup_virtual_serial.sh
fi

# Iniciar el simulador
cd /var/new-tank-simulator
python src/main.py
EOF

chmod +x /var/new-tank-simulator/start_simulator.sh

# Crear servicio systemd para el simulador
echo -e "${GREEN}Creando servicio systemd para el simulador...${NC}"
cat > /etc/systemd/system/tank-simulator.service << EOF
[Unit]
Description=Tank Simulator with Modbus RTU
After=network.target virtual-serial-ports.service
Requires=virtual-serial-ports.service

[Service]
Type=simple
WorkingDirectory=/var/new-tank-simulator
ExecStart=/var/new-tank-simulator/start_simulator.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
systemctl daemon-reload

echo -e "${GREEN}=== Instalación completada ===${NC}"
echo -e "${YELLOW}Para iniciar el simulador manualmente:${NC}"
echo -e "  ${GREEN}cd /var/new-tank-simulator && ./start_simulator.sh${NC}"
echo -e "${YELLOW}Para iniciar el simulador como servicio:${NC}"
echo -e "  ${GREEN}systemctl start tank-simulator.service${NC}"
echo -e "${YELLOW}Para habilitar el inicio automático del simulador:${NC}"
echo -e "  ${GREEN}systemctl enable tank-simulator.service${NC}"
echo -e "${YELLOW}Para verificar el estado del simulador:${NC}"
echo -e "  ${GREEN}systemctl status tank-simulator.service${NC}"
echo -e "${YELLOW}Para ver los logs del simulador:${NC}"
echo -e "  ${GREEN}journalctl -u tank-simulator.service -f${NC}"
