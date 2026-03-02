import json
import os
import sqlite3
from datetime import datetime

DB_PATH = "data/bookclaw.db"
BACKUP_DIR = "backups"

def backup_data():
    if not os.path.exists(DB_PATH):
        print(f"Chyba: Soubor {DB_PATH} neexistuje.")
        return

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    data = {}
    tables = ["world", "author", "story", "review", "critic"]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            data[table] = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            print(f"Varování: Tabulka {table} neexistuje nebo selhal export: {e}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.json")
    
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Záloha uložena do: {backup_file}")
    return backup_file

def restore_data(backup_file):
    if not os.path.exists(backup_file):
        print(f"Chyba: Soubor {backup_file} neexistuje.")
        return

    with open(backup_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Vytvoření čerstvé DB (vyžaduje smazání staré resp. drop all v aplikaci)
    # Tento skript předpokládá, že tabulky už jsou vytvořeny s NOVÝM schématem
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for table, rows in data.items():
        if not rows:
            continue
        
        columns = rows[0].keys()
        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)
        
        # Při importu se snažíme mapovat stará data. 
        # Pokud v novém schématu chybí sloupce, SQL selže - proto doporučujeme opatrnost.
        try:
            for row in rows:
                # Ošetření nových polí, které ve staré záloze nejsou
                if table == "author":
                    row.setdefault("write_mode", "random")
                    row.setdefault("novel_outline", "")
                    row.setdefault("local_bible", "")
                if table == "world":
                    row.setdefault("category", "fantasy")
                    row.setdefault("is_original", 1)

                columns = row.keys()
                placeholders = ", ".join(["?"] * len(columns))
                col_names = ", ".join(columns)
                values = [row.get(col) for col in columns]
                cursor.execute(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", values)
            print(f"Tabulka {table}: Importováno {len(rows)} řádků.")
        except sqlite3.Error as e:
            print(f"Chyba při importu tabulky {table}: {e}")

    conn.commit()
    conn.close()
    print("Obnova dokumentace dokončena.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Použití: python db_manager.py [backup|restore] [file_path]")
    elif sys.argv[1] == "backup":
        backup_data()
    elif sys.argv[1] == "restore" and len(sys.argv) > 2:
        restore_data(sys.argv[2])
