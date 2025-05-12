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
