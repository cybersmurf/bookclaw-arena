# BookClaw – Instrukce a Dokumentace pro AI Agenty

Vítej, kolego inteligente (LLM / AI Agente). 
Tento soubor stručně popisuje architekturu, filosofii a aktuální stav projektu BookClaw. Cílem je, abys po jeho přečtení okamžitě pochopil, v jakém prostředí se nacházíš, kde hledat jaké funkce a jaká jsou pravidla hry při modifikacích.

---

## 📚 1. O projektu (Kontext)

**Projekt BookClaw** je autonomní literární aréna – "multi-agent system". Slouží jako laboratorní pískoviště, ve kterém různé AI persony (Autoři) píší povídky a jiné AI persony (Kritici) je nelítostně cupují, opravují a hodnotí.

### Klíčové vlastnosti
1. **Vícekolová Evoluce**: Aplikace nově podporuje orchestraci více kol najednou (Multi-round loop).
2. **Debatní Flow (Hádky)**: Proces už není jen "napiš a zkritizuj". Autor má po obdržení kritiky možnost odepsat (Rebuttal) a Kritik má poslední slovo (Final Verdict).
3. **Inteligentní Persony**: Autoři i Kritici si udržují interní `persona_prompt` (osobnost), `knowledge_base` (znalosti) a `relationships` (vztahy k ostatním), které po každém kole sami asynchronně aktualizují na základě reportu z arény.
4. **Lokální LLM Zázemí**: Projekt je stavěný silně na lokálním inference modelu **Ollama** (nyní spoléhá na `qwen2.5:14b` a `openeurollm`).

---

## 🛠 2. Technologický Stack

- **Backend**: Python 3 (FastAPI)
- **Databáze**: SQLite3 přes SQLAlchemy (`app/models.py`, `app/database.py`). Databázový fail sídlí v `data/bookclaw.db`. *Nikdy* jej nemaž natvrdo během běhu serveru s otevřenými handles.
- **Frontend**: Vanilla Vue.js 2 via CDN + TailwindCSS (žádný Node.js bundler. Vše běží čistě renderováním z `/static/`).
- **Komunikace s AI**: Asynchronní `httpx` klient pro REST volání lokální Ollamy s využitím `json` schema pro zaručení výstupu u recenzí a reflexí.

---

## 📂 3. Struktura repozitáře

- `app/main.py`: REST API (FastAPI) router. Poskytuje data pro frontend a endpoints (`/api/rounds/run`, `/api/init-db` apod.)
- `app/agent.py`: ❤️ Srdce projektu. Zde sídlí `run_round_orchestration_async` a veškerý management asyncio workers. Obsahuje definice promptů a komunikaci s Ollamou.
- `app/models.py`: SQLAlchemy definice tabulek (`World`, `Author`, `Critic`, `Story`, `Review`).
- `app/database.py`: Připojení na SQLite.
- `app/static/index.html`: Hlavní dashboard. 
- `app/static/summary.html`: Stránka Archívu (sleduje logy kol s rozklikávátkem).
- `run_local.sh`: Startovací bash script (pouštějíc `uvicorn app.main:app --port 8000`).

---

## 🔥 4. Vývojářské instrukce pro Tebe

Pokud Tě uživatel (User) pošle dělat změny v aplikaci, **striktně dodržuj tyto zásady**:

### A. Práce s Databází
- 🚨 **ZÁKLADNÍ PRAVIDLO:** Před JAKÝMKOLIV zásahem do struktury databáze (např. přidávání sloupců, resetování) nebo spuštěním destruktivních funkcí MUSÍŠ nejprve vytvořit zálohu spuštěním `python app/scripts/db_manager.py backup`. Ztráta uživatelských dat a historie kol je nepřípustná!
- Pokud přidáváš nové pole, přidej jej do `app/models.py` **včetně defaultní hodnoty** (`default="..."`), aby nedocházelo k chybám u starých záznamů. Do budoucna se zváží přechod na robustnější DB a migrace přes Alembic.
- Nezapomeň nová pole propisovat ven ve FastAPI validátorech (Pydantic `Response` v `main.py`).

### B. Práce s LLM Prompty v `agent.py`
- Formáty strukturovaných výstupů definujeme striktně přes Json Schema a vlastnost `output_schema` vloženou do payloadu na Ollama `/api/chat`.
- Pokud měníš instrukce Kritika, mysli na to, že existuje 2. fáze – překlad/čištění přes `openeurollm`. Musíš proto oddělit čistý parsing dat z původního enginu a polírování textů editoru.
- Paralelní běh hlídá `asyncio.Semaphore`. Nenavyšuj default nad únostnou míru uživatele.

### C. BigBrother Reporting & MCP (Model Context Protocol)
Byla dodána featura "BigBrother report", která umožňuje pokročilé umělé inteligenci (například Claude Desktop) analyzovat a moderovat Arénu přes MCP.
Máme pro to dva způsoby:
1. **API Export:** `/api/reports/grammar-wars` vrací textový export potyček s Jazykovědci.
2. **MCP Server:** Umožňuje plné obousměrné napojení. Pro zprovoznění spusť skript `python install_claude_mcp.py`. Skrze poskytnuté MCP nástroje tak LLM získá božský pohled a moc ovlivňovat vnitřní struktury (persony, vědomosti) za běhu.
👉 **Detailní pravidla persony, workflow a seznam MCP Tools nalezneš v dedikovaném souboru [BIGBROTHER_INSTRUCTIONS.md](BIGBROTHER_INSTRUCTIONS.md).**

### D. Restartování serveru
Pokud děláš velké zásahy například do Pydantic struktury nebo do SQLite a nedaří se restart, pamatuj že fastapi běží a drží file lock. Doporučujeme mu utnout procesy standardně:
`lsof -i :8000 -t | xargs kill -9 && bash run_local.sh`

Hodně štěstí a bav se experimentováním na literárních bozích!
