#!/usr/bin/env bash

# Tento script běží pro účely Model Context Protocol (MCP).
# Používá defaultně 'stdio' transport.
# Je určen k zavolání z externího klienta (např. Claude Desktop aplikací).

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Aktivace lokálního prostředí, kde je nainstalovaný `mcp`
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Spuštění python MCP serveru (musí běžet přes modul, aby se správně napojil na /app context)
python -m app.mcp_server
