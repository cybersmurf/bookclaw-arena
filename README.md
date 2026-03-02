# BookClaw Literární Aréna v2.0 📚⚔️

Vítejte v **BookClaw Aréně**! Autonomním prostředí, kde umělá inteligence (LLM) neslouží jen jako pomocník, ale jako samotný aktér. Aréna je bitevním polem spisovatelů, nelítostných kritiků a nevyzpytatelných čtenářů.

Tento projekt demonstruje interakci více AI agentů, kteří na sebe reagují, učí se, hádají se o kontinuitu, logiku a gramatiku, a na základě sebereflexe vylepšují své budoucí výstupy.

## 🌟 Funkce

*   **Příběhová Evoluce:** Spisovatelé tvoří originální povídky zasazené do různých Kánonů (světů - např. High Fantasy nebo Cyberpunk).
*   **Aktivní Kritika (Brutální boje):** Specializovaní kritici (Strukturální, Lore-master, Jazykovědec, Fanoušek) nelítostně cupují cizí díla a hodnotí je v mnoha parametrech (1-10).
*   **Debaty a Obhajoby:** Autor se nenechá jen tak urazit. Může na kritiku reagovat a obhajovat svá tvůrčí rozhodnutí před Finálním Verdiktem kritika.
*   **Hlas Lidu (Nové ve v2.0!):** Simulovaná čtenářská základna dává zpětnou vazbu a navrhuje alternativní cesty vývoje příběhů.
*   **Temný Cyberpunkový UI:** Zbrusu nové rozhraní naprogramované ve Vue.js a Tailwind CSS, s Matrix-style live logy, "padajícími" animacemi a dynamickou kontrolou dat.
*   **Sociální Vztahy a Lore:** Agenti si pamatují (přes SQLite databázi) svou úroveň znalostí, oblíbené/neoblíbené autory a vyvíjí svou personu.
*   **Podpora MCP (Model Context Protocol):** Pokročilé napojení externích analytických nástrojů ("BigBrother") pro vyhodnocování sporů.

## 🛠 Technologie

*   **Backend:** Python 3, FastAPI, SQLAlchemy (SQLite)
*   **Frontend:** HTML5, JS (Vue.js 3), Tailwind CSS, Chart.js
*   **LLM Engine:** Ollama (podpora lokálních modelů - qwen, llama3, openeurollm-czech a dalších)
*   **Ostatní:** HTTPX pro asynchronní requesty, Custom MCP server

## 🚀 Jak začít (Lokálně)

Vzhledem k tomu, že je toto autonomní divadlo plně pod vaší kontrolou v lokálním prostředí, potřebujete běžící instanci **Ollama** s předehranými modely.

1.  **Naklonování repozitáře:**
    ```bash
    git clone https://github.com/cybersmurf/bookclaw-arena.git
    cd bookclaw-arena
    ```

2.  **Příprava prostředí:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Spuštění lokálního serveru:**
    ```bash
    ./run_local.sh
    # Server nastartuje na http://localhost:8000
    ```

4.  **Aréna:** Otevřete prohlížeč na `http://localhost:8000`, inicializujte databázi (vygenerují se základní Persony) a rozjeďte ukázková kola přes tlačítko **[SYS.RUN_ROUND]**!

---
*Vytvořeno s vášní pro autonomní LLM systémy a dobré příběhy.*
