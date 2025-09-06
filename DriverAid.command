#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -x "$DIR/dist/main" ]; then
    echo "▶ Ejecutando binario compilado..."
    "$DIR/dist/main"
else
    echo "⚠ No se encontró dist/main. Ejecutando con Python..."
    python3 "$DIR/main.py"
fi

echo
read -n 1 -s -p "Presiona una tecla para cerrar..."
