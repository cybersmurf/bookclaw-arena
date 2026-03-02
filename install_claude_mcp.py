import os
import json
import traceback

def get_claude_config_path():
    home_dir = os.path.expanduser("~")
    claude_dir = os.path.join(home_dir, "Library", "Application Support", "Claude")
    os.makedirs(claude_dir, exist_ok=True)
    return os.path.join(claude_dir, "claude_desktop_config.json")

def get_antigravity_config_path():
    home_dir = os.path.expanduser("~")
    ag_dir = os.path.join(home_dir, ".gemini", "antigravity")
    os.makedirs(ag_dir, exist_ok=True)
    return os.path.join(ag_dir, "mcp_config.json")

def install_to_config(config_file, server_name, command_path):
    print(f"Instaluji MCP server '{server_name}' do: {config_file}")
    
    config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    config = json.loads(content)
        except Exception as e:
            print(f"Chyba při čtení stávajícího konfigu {config_file}. Vytvoříme nový. Chyba: {e}")
            
    if "mcpServers" not in config:
        config["mcpServers"] = {}
        
    config["mcpServers"][server_name] = {
        "command": command_path,
        "args": []
    }
    
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"✅ HOTOVO pro: {config_file}")
    except Exception as e:
        print(f"❌ Nepodařilo se zapsat do konfigu {config_file}: {e}")
        traceback.print_exc()

def install():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    mcp_script = os.path.join(current_dir, "run_mcp.sh")
    
    # Práva na spuštění sh skriptu
    os.chmod(mcp_script, 0o755)
    
    print(f"Cesta k bash MCP spouštěči: {mcp_script}")
    
    # 1. Claude Desktop
    claude_config = get_claude_config_path()
    install_to_config(claude_config, "bookclaw", mcp_script)
    
    # 2. Antigravity AI
    ag_config = get_antigravity_config_path()
    install_to_config(ag_config, "bookclaw", mcp_script)
    
    print("\n🎉 MCP BookClaw server byl úspěšně nakonfigurován pro obě platformy.")
    print("💡 Nezapomeňte příslušné aplikace (Claude Desktop / Antigravity) restartovat.")

if __name__ == "__main__":
    install()
