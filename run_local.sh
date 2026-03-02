#!/bin/bash
set -e

# Přechod do rootu projektu
cd "$(dirname "$0")"

# Setup venv pokud neexistuje
if [ ! -d "venv" ]; then
    echo "Vyvářím virtuální prostředí (vyžaduje Python 3)..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Spuštění
echo "Spouštím Literární arénu (BookClaw) na http://localhost:8000"
uvicorn app.main:app --reload --port 8000
