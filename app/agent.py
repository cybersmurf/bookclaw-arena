import asyncio
import json
import os
import textwrap
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session
from . import models
from sqlalchemy.orm import Session
from .database import SessionLocal, engine

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_PARALLEL = int(os.getenv("OLLAMA_PARALLEL", "4"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b") # Zvolíme Qwen pro spolehlivý structured output
OLLAMA_WRITER_MODEL = os.getenv("OLLAMA_WRITER_MODEL", "qwen2.5:14b") # Pro generování povídky klidně stejný
OLLAMA_CZECH_MODEL = os.getenv("OLLAMA_CZECH_MODEL", "jobautomation/openeurollm-czech:latest") # Model s lepším porozuměním jemnostem CZ
OLLAMA_EDITOR_MODEL = os.getenv("OLLAMA_EDITOR_MODEL", "jobautomation/openeurollm-czech:latest") # Pro finální leštění české recenze od kritiků

# GOOBALNÍ INSTANCE STAVU
class OrchestratorState:
    def __init__(self):
        self.round_num = 0
        self.is_running = False
        # author_statuses[author_id] = "Píše...", "Odpočívá", "Aktualizuje personu"
        self.author_statuses: Dict[int, str] = {}
        # critic_statuses[critic_id] = "Hodnotí povídku autora X", "Odpočívá"
        self.critic_statuses: Dict[int, str] = {}
        # reader_statuses[reader_id] = "Čte..."
        self.reader_statuses: Dict[int, str] = {}
        
    def reset(self, authors, critics, readers=None):
        self.is_running = True
        for a in authors:
            self.author_statuses[a.id] = "Připraven"
        for c in critics:
            self.critic_statuses[c.id] = "Odpočívá"
        if readers:
            for r in readers:
                self.reader_statuses[r.id] = "Čeká na povídky"

state = OrchestratorState()

async def _call_ollama_async(client, model, system_prompt, user_prompt, temperature=0.7, top_p=0.9, output_schema=None):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": 4096,
        },
    }
    
    if output_schema:
        payload["format"] = output_schema

    try:
        resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=180.0)
        resp.raise_for_status()
        raw = resp.json()["message"]["content"]
        
        if output_schema:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None
        return raw.strip()
    except Exception as e:
        print(f"[agent] Chyba při volání OLLAMA: {e}")
        return None

async def _writer_task(client, semaphore, db, author, world, round_num):
    async with semaphore:
        state.author_statuses[author.id] = f"✍️ Píše {'kapitolu románu' if author.write_mode == 'novel' else 'povídku'}..."
        try:
            # 1. Téma a Svět pro náhodný mód
            effective_world = world
            current_theme = ""
            
            if author.write_mode == "random":
                # Vybereme náhodný doplňkový svět stejné kategorie (nebo původní)
                other_worlds = db.query(models.World).filter(models.World.category == author.genre).all()
                if other_worlds:
                    import random
                    effective_world = random.choice(other_worlds)
                
                # NÁHODNÉ TÉMA
                state.author_statuses[author.id] = "🎲 Losuje náhodné téma pro povídku..."
                theme_system = "Jsi koordinátor témat pro spisovatele. MUSÍŠ VRÁTIT PLATNÝ JSON. ODPOVÍDEJ VÝHRADNĚ V ČEŠTINĚ. ŽÁDNÉ ČÍNSKÉ ZNAKY!"
                theme_user = f"Máme kolo {round_num}. Vygeneruj NÁHODNĚ originální námět na krátkou povídku (např. 'Ztracený dopis', 'Nevysvětlitelný úkaz')."
                
                theme_schema = {
                    "type": "object",
                    "properties": {
                        "theme": {"type": "string", "description": "Holý námět na povídku o délce jedné stručné věty v čisté češtině. ZAKÁZÁNA ČÍNŠTINA A VYSVĚTLIVKY."}
                    },
                    "required": ["theme"]
                }
                theme_json = await _call_ollama_async(client, OLLAMA_MODEL, theme_system, theme_user, temperature=0.6, output_schema=theme_schema)
                if theme_json and "theme" in theme_json:
                    current_theme = theme_json["theme"]
                else:
                    current_theme = f"Záhadná událost v kole {round_num}"
                print(f"[agent] Autor {author.name} si vylosoval téma: {current_theme}")
            
            # 2. Románový mód - Osnova
            novel_context = ""
            if author.write_mode == "novel":
                if not author.novel_outline:
                    # Pokud nemá osnovu, vygenerujeme ji jako první krok
                    state.author_statuses[author.id] = "🗺️ Plánuje osnovu románu..."
                    outline_prompt = f"Jsi spisovatel. Na základě tvé persony a světa '{effective_world.name}' navrhni osnovu (plán) románu o 10 kapitolách. Vrať pouze seznam s názvy a stručným obsahem."
                    author.novel_outline = await _call_ollama_async(client, OLLAMA_MODEL, author.persona_prompt, outline_prompt)
                
                novel_context = f"\n**OSNOVA ROMÁNU:**\n{author.novel_outline}\n**AKTUÁLNÍ CÍL:** Píšeš další část svého románu. Drž se osnovy a plynule navaž."

            system_prompt = author.persona_prompt
            past_stories = db.query(models.Story).filter(models.Story.author_id == author.id).order_by(models.Story.round.asc()).all()
            history_text = "Zatím jsi v tomto světě nenapsal žádnou povídku."
            if past_stories:
                history_text = "Shrnutí tvých předchozích textů:\n"
                for st in past_stories:
                    history_text += f"- Kolo {st.round}: {st.title}\n"
            
            theme_instruction = f"**Téma pro toto kolo:** {current_theme}" if author.write_mode == "random" else "**Instrukce:** Píšeš román, pokračuj další kapitolou podle osnovy. Na žádné externí téma neber ohled, prostě plynule navaž."
            
            user_prompt = textwrap.dedent(f"""
                **BIBLE SVĚTA '{effective_world.name}':**
                {effective_world.bible_md}
                
                **TVÉ LOKÁLNÍ POZNÁMKY (Co jsi v příběhu vytvořil):**
                {author.local_bible if author.local_bible else "Zatím žádné."}
                
                {novel_context}
                
                **Tvé znalosti a vztahy:**
                {author.knowledge_base}
                {author.relationships}
                
                **Historie tvé tvorby:**
                {history_text}
                
                {theme_instruction}
                
                Napiš nový ucelený text (800-1200 slov) v češtině. 
                Pokud píšeš román, na první řádek MUSÍŠ napsat: '# Kapitola [Číslo]: [Název kapitoly podle osnovy]'.
                Pokud píšeš povídku, na první řádek napiš: '# [Název povídky]'.
                """).strip()
            
            # Nasazení českého modelu pro vybrané autory (pokud se uživatel rozhodne)
            # Defaultně necháváme stávající model, lze upravovat z UI nebo manuálně
            selected_model = OLLAMA_CZECH_MODEL if getattr(author, 'use_czech_model', False) else OLLAMA_WRITER_MODEL

            story_text = await _call_ollama_async(client, selected_model, system_prompt, user_prompt, temperature=0.7)
            if not story_text:
                return None
            
            lines = story_text.split('\n')
            title = f"Povídka {author.name} (kolo {round_num})"
            for idx, line in enumerate(lines):
                if line.startswith("# "):
                    title = line[2:].strip()
                    lines.pop(idx)
                    break
            
            text_md = "\n".join(lines).strip()
            # Uložíme s ID světa, který byl skutečně použit + zapsání kompletních promptů pro analýzu BigBrotherem a UX
            return models.Story(
                author_id=author.id, 
                world_id=effective_world.id, 
                round=round_num, 
                title=title, 
                text_md=text_md,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                local_bible=author.local_bible,
                knowledge_base=author.knowledge_base,
                relationships=author.relationships
            )
        finally:
            state.author_statuses[author.id] = "☕️ Dopsal. Odpočívá."


def _build_review_schema():
    return {
        "type": "object",
        "properties": {
            "scores": {
                "type": "object",
                "properties": {
                    "plot": {"type": "integer", "minimum": 0, "maximum": 10},
                    "characters": {"type": "integer", "minimum": 0, "maximum": 10},
                    "style_and_grammar": {"type": "integer", "minimum": 0, "maximum": 10},
                    "lore_and_logic": {"type": "integer", "minimum": 0, "maximum": 10},
                    "originality": {"type": "integer", "minimum": 0, "maximum": 10},
                },
                "required": ["plot", "characters", "style_and_grammar", "lore_and_logic", "originality"]
            },
            "praise": {"type": "string", "description": "Co se povedlo."},
            "critique": {"type": "string", "description": "Hlavní výtky, nalezené logické díry, anachronismy (věci nepatřící do světa) a gramatické nesmysly."},
            "progress_comment": {"type": "string", "description": "Zhodnocení pokroku oproti minulu nebo celkový dojem."},
            "world_updates": {"type": "string", "description": "Návrhy na zaznamenání do Bible světa (nová lokace, pravidlo apod.) Null pokud nic."},
        },
        "required": ["scores", "praise", "critique", "progress_comment"]
    }

def _build_reflection_schema():
    return {
        "type": "object",
        "properties": {
            "persona_prompt": {"type": "string", "description": "Aktualizovaný vnitřní manuál/styl."},
            "knowledge_base": {"type": "string", "description": "Nově nabyté vědomosti o fungování světa a loru."},
            "relationships": {"type": "string", "description": "Aktualizovaný postoj k ostatním autorům a kritikům."}
        },
        "required": ["persona_prompt", "knowledge_base", "relationships"]
    }

def _build_reader_schema():
    return {
        "type": "object",
        "properties": {
            "review": {"type": "string", "description": "Tvé zhodnocení povídky a vyjádření k hádkám kritiků. Souhlasíš s nimi? Líbil se ti příběh?"},
            "proposed_story": {"type": "string", "description": "Rozepsaný návrh, jak by se podle tebe mohl nebo měl příběh v dalším kole vyvíjet. Tvoje vize."}
        },
        "required": ["review", "proposed_story"]
    }

async def _reader_task(client, semaphore, db, story, author, reviews, reader):
    async with semaphore:
        state.reader_statuses[reader.id] = f"📖 Čte povídku od {author.name} a debaty kritiků..."
        try:
            system_prompt = f"Jsi čtenář a fanoušek. Tvoje persona:\n{reader.persona_prompt}\nZnalosti a preference:\n{reader.knowledge_base}\nVztahy k ostatním:\n{reader.relationships}\n\nPiš vždy v češtině a vrať výhradně JSON."
            
            reviews_text = ""
            if reviews:
                for r in reviews:
                    reviews_text += f"\n--- Kritik ID {r.critic_id} ---\nSkóre: {r.scores_json}\nRecenze: {r.review_md}\nReakce autora: {r.author_rebuttal}\nVerdikt kritika: {r.critic_final_response}\n"
            
            user_prompt = textwrap.dedent(f"""
                **Přečti si následující povídku od {author.name}:**
                {story.title}
                {story.text_md}
                
                **Zde je to, co o povídce řekli kritici (včetně hádání se s autorem):**
                {reviews_text if reviews_text else "Zatím žádné kritiky."}
                
                Nyní jako čtenář zhodnoť dílo podle svého gusta a okomentuj, jestli byli kritici moc mírní nebo moc přísní. Pak pro autora vymysli SVOU VLASTNÍ VIZI, jak by měl příběh pokračovat.
                Vrať výhradně JSON.""").strip()

            schema = _build_reader_schema()
            reader_json = await _call_ollama_async(client, OLLAMA_MODEL, system_prompt, user_prompt, temperature=0.7, output_schema=schema)
            
            if not reader_json:
                return None
            
            return models.ReaderReview(
                reader_id=reader.id,
                review_md=reader_json.get("review", "Bez komentáře."),
                proposed_story_md=reader_json.get("proposed_story", "")
            )
        finally:
            state.reader_statuses[reader.id] = "☕️ Hodnocení dopsáno."

async def _critic_task(client, semaphore, db, story, author, critic):
    async with semaphore:
        state.critic_statuses[critic.id] = f"🧐 {OLLAMA_MODEL} čte a hodnotí {author.name}"
        try:
            # Získáme bibli světa pro tuto konkrétní povídku
            world = db.query(models.World).filter(models.World.id == story.world_id).first()
            
            base_prompt = f"Jsi český literární kritik. Hodnotíš povídky žánru {author.genre}. Piš VÝHRADNĚ česky, věcně, s osobností. Vždy vrať platný JSON. ŽÁDNÉ ČÍNSKÉ ZNAKY JSOU ZAKÁZÁNY!"
            system_prompt = base_prompt + "\n\n" + critic.persona_prompt + f"\n\n**Tvé znalosti o loru a světě:**\n{critic.knowledge_base}\n\n**Tvé vztahy k autorům a dalším kritikům:**\n{critic.relationships}"
            
            user_prompt = textwrap.dedent(f"""
                **PŮVODNÍ BIBLE SVĚTA (Kánon):**
                {world.bible_md if world else "Neznámý svět"}
                
                **AUTOROVY LOKÁLNÍ POZNÁMKY:**
                {author.local_bible if author.local_bible else "Nic."}
                
                **POVÍDKA OD: {author.name}**
                **TITUL: {story.title}**
                
                --- TEXT POVÍDKY ---
                {story.text_md}
                --- KONEC TEXTU ---
                
                Ohodnoť povídku v češtině. Pokud jsi Lore-master, hlídej rozpor s PŮVODNÍ BIBLÍ. 
                Pokud autor v povídce nebo lokálních poznámkách poruší kánon (např. technologie v čistém fantasy), okamžitě ho za to sestřel.
                Vrať POUZE JSON podle schématu.""").strip()

            schema = _build_review_schema()
            review_json = await _call_ollama_async(client, OLLAMA_MODEL, system_prompt, user_prompt, temperature=0.5, output_schema=schema)
            
            if not review_json:
                return None
                
            md_text = f"**Plusy:**\n{review_json.get('praise', '')}\n\n**Mínusy:**\n{review_json.get('critique', '')}\n\n**Komentář:**\n{review_json.get('progress_comment', '')}"
            if review_json.get('world_updates'): md_text += f"\n\n**Návrh do bible světa:** {review_json.get('world_updates')}"
            
            # 2. FÁZE: OpenEuroLLM leští češtinu
            state.critic_statuses[critic.id] = f"🖌️ {OLLAMA_EDITOR_MODEL} leští češtinu recenze ({author.name})"
            editor_system = "Jsi elitní literární editor a rodilý mluvčí češtiny. Tvým úkolem je vzít hrubý text recenze (často s anglicismy nebo kostrbatou syntaxí z AI) a přepsat ho do perfektního, čtivého a břitkého českého jazyka. Můžeš být klidně mírně sarkastický a osobní jako živý kritik. ZACHOVEJ přesný styl struktury (Plusy, Mínusy, Komentář, Návrh) i podstatu výtek, neber originálu smysl, jen vylepši flow textu. Vrať pouze čistý opravený markdown text, nic víc neokecávej."
            editor_user = f"Zde je surová recenze k jazykové úpravě tónu i hrubek:\n\n{md_text}"
            
            refined_md = await _call_ollama_async(client, OLLAMA_EDITOR_MODEL, editor_system, editor_user, temperature=0.4)
            if refined_md:
                md_text = refined_md
                
            return models.Review(
                critic_id=critic.id,
                scores_json=json.dumps(review_json.get("scores", {})),
                review_md=md_text
            )
        finally:
            state.critic_statuses[critic.id] = "☕️ Zpracováno. Čeká na další."
            
async def _author_rebuttal_task(client, semaphore, author, story, review, critic):
    async with semaphore:
        state.author_statuses[author.id] = f"🥊 Čte kritiku od {critic.name} a chystá obhajobu."
        try:
            system_prompt = f"Jsi autor jménem {author.name}.\nTvůj styl: {author.style}\nTvůj manuál: {author.persona_prompt}\nTvé vztahy a názory na kritiky: {author.relationships}\nNyní ti kritik vmetl do tváře recenzi. Napiš krátkou údernou a případně mírně uraženou nebo vděčnou reakci (rebuttal). Můžeš kritika i trochu sejmout, pokud nesouhlasíš. Musíš psát v první osobě jako ten autor."
            user_prompt = f"Tvoje povídka:\n{story.title}\n{story.text_md}\n\nKritika od {critic.name}:\nSkóre: {review.scores_json}\n{review.review_md}\n\nNapiš svou reakci (ideálně odstavec nebo dva, do max 100 slov). Reakci vrať jako prostý text."
            rebuttal = await _call_ollama_async(client, OLLAMA_MODEL, system_prompt, user_prompt, temperature=0.7)
            review.author_rebuttal = rebuttal
        finally:
            pass

async def _critic_final_task(client, semaphore, critic, review, author):
    async with semaphore:
        state.critic_statuses[critic.id] = f"🥊 Reaguje na obhajobu od {author.name}."
        try:
            system_prompt = f"{critic.persona_prompt}\nTvoje vztahy k ostatním: {critic.relationships}\nJsi kritik {critic.name}. Hodnotils autora {author.name} a dostals od něj obhajobu na svou recenzi. Napiš krátké konečné shrnutí - 'final verdict'. Můžeš mu ustoupit, nebo ho zaříznout ještě více. Piš v první osobě jako ten kritik."
            user_prompt = f"Tvoje skóre: {review.scores_json}\nTvůj text: {review.review_md}\n\nAutorova obhajoba:\n{review.author_rebuttal}\n\nNapiš svou finální krátkou reakci na autora (do 50 slov) jako prostý text."
            final_response = await _call_ollama_async(client, OLLAMA_MODEL, system_prompt, user_prompt, temperature=0.6)
            review.critic_final_response = final_response
        finally:
            state.critic_statuses[critic.id] = "☕️ Souboj dobojován."

async def _reflection_task(client, semaphore, author, latest_story, reviews, arena_summary):
    async with semaphore:
        state.author_statuses[author.id] = "🧠 Aktualizuje osnovu a lokální bibli..."
        try:
            system_prompt = "Jsi spisovatel. Vracíš POUZE platný JSON obsahující tvůj aktualizovaný vnitřní manuál 'persona_prompt', 'knowledge_base', 'relationships' a zejména 'local_bible' (tvé nové poznatky o loru, které jsi v příběhu vytvořil) a případně upravenou 'novel_outline'. ODPOVÍDEJ VÝHRADNĚ V ČEŠTINĚ! ŽÁDNÁ ČÍNŠTINA NENÍ POVOLENA!"
            reviews_text = "".join([f"\n--- Kritik {r.critic_id} ---\nSkóre: {r.scores_json}\nText: {r.review_md}\n" for r in reviews])
            user_prompt = f"""Tvá povídka: {latest_story.title}\nRecenze: {reviews_text}\nShrnutí arény: {arena_summary}\n\nTvé stávající údaje:\nLocal Bible (Lore): {author.local_bible}\nOsnova: {author.novel_outline}\n\nNa základě zpětné vazby aktualizuj svůj styl, vztahy a hlavně si zapiš do 'local_bible' nové postavy/místa, které jsi v tomto kole vymyslel, aby byly v příštím kole konzistentní."""
            
            schema = {
                "type": "object",
                "properties": {
                    "persona_prompt": {"type": "string"},
                    "knowledge_base": {"type": "string"},
                    "relationships": {"type": "string"},
                    "local_bible": {"type": "string"},
                    "novel_outline": {"type": "string"}
                }
            }
            new_data = await _call_ollama_async(client, OLLAMA_MODEL, system_prompt, user_prompt, temperature=0.6, output_schema=schema)
            if new_data:
                author.persona_prompt = new_data.get('persona_prompt', author.persona_prompt)
                author.knowledge_base = new_data.get('knowledge_base', author.knowledge_base)
                author.relationships = new_data.get('relationships', author.relationships)
                author.local_bible = new_data.get('local_bible', author.local_bible)
                if author.write_mode == "novel":
                    author.novel_outline = new_data.get('novel_outline', author.novel_outline)
            return True
        finally:
            state.author_statuses[author.id] = "🛌🏻 Hotovo."

async def _critic_reflection_task(client, semaphore, critic, reviews_made, arena_summary):
    async with semaphore:
        state.critic_statuses[critic.id] = f"🧠 Přemýšlí nad svými radami a aktualizuje blacklist..."
        try:
            system_prompt = "Jsi literární kritik. Vracíš POUZE platný JSON obsahující tvůj aktualizovaný vnitřní 'persona_prompt', nové znalosti o fungování světa z povídek a aktualizované vztahy či blacklist k autorům/kolegům. ODPOVÍDEJ VÝHRADNĚ V ČEŠTINĚ! ŽÁDNÁ ČÍNŠTINA NENÍ POVOLENA!"
            reviews_text = "".join([f"\n--- Recenze {r.id} ---\nSkóre: {r.scores_json}\nText: {r.review_md}\nObhajoba autora: {r.author_rebuttal}\nTvůj finální verdikt: {r.critic_final_response}\n" for r in reviews_made])
            user_prompt = f"Tvůj stávající manuál:\n{critic.persona_prompt}\nTvé stávající znalosti loru:\n{critic.knowledge_base}\nTvé stávající vztahy:\n{critic.relationships}\n\nTvé interakce (hádkání s autory):\n{reviews_text}\n\nSHRNUTÍ DĚNÍ V ARÉNĚ OSTATNÍCH:\n{arena_summary}\n\nVygeneruj JSON s aktualizovanými poli."
            schema = _build_reflection_schema()
            new_data = await _call_ollama_async(client, OLLAMA_MODEL, system_prompt, user_prompt, temperature=0.6, output_schema=schema)
            if new_data:
                critic.persona_prompt = new_data.get('persona_prompt', critic.persona_prompt)
                critic.knowledge_base = new_data.get('knowledge_base', critic.knowledge_base)
                critic.relationships = new_data.get('relationships', critic.relationships)
            return True
        finally:
            state.critic_statuses[critic.id] = "🛌🏻 Skončil a chystá se spát."

async def run_round_orchestration_async(start_round_num: int, num_rounds: int = 1):
    db = Session(bind=engine, expire_on_commit=False)
    try:
        authors = db.query(models.Author).all()
        critics = db.query(models.Critic).all()
        readers = db.query(models.Reader).all()
        world = db.query(models.World).first()
        
        if not authors or not world or not critics: return

        state.is_running = True
        semaphore = asyncio.Semaphore(OLLAMA_PARALLEL)
        
        async with httpx.AsyncClient() as client:
            for round_offset in range(num_rounds):
                round_num = start_round_num + round_offset
                print(f"=== SPUŠTĚNO KOLO {round_num} ({round_offset+1}/{num_rounds}) ===")
                state.round_num = round_num
                state.reset(authors, critics, readers)

                writer_tasks = []
                for author in authors:
                    writer_tasks.append(_writer_task(client, semaphore, db, author, world, round_num))
                
                # Spuštění spisovatelů (return_exceptions zabrání pádu smyčky při TimeOutu jednoho agenta)
                stories_results = await asyncio.gather(*writer_tasks, return_exceptions=True)
                valid_stories = [s for s in stories_results if s is not None and not isinstance(s, Exception)]
                
                if not valid_stories:
                    print(f"[Orkestrace] Kolo {round_num} nemá žádné platné povídky. Přeskakuji.")
                    continue
                
                db.add_all(valid_stories)
                db.commit()
                for s in valid_stories: db.refresh(s)
                
                # Kritika - Fáze 1 (Čtení + Recenzování)
                critic_tasks = []
                for story in valid_stories:
                    story_author = next(a for a in authors if a.id == story.author_id)
                    for critic in critics:
                        critic_tasks.append(_critic_task(client, semaphore, db, story, story_author, critic))
                
                reviews_results = await asyncio.gather(*critic_tasks, return_exceptions=True)
                valid_reviews = []
                # Odfiltrování exceptions
                clean_reviews = [r if not isinstance(r, Exception) else None for r in reviews_results]
                for (story, critic), rev in zip([(s, c) for s in valid_stories for c in critics], clean_reviews):
                    if rev:
                        rev.story_id = story.id 
                        valid_reviews.append(rev)
                
                db.add_all(valid_reviews)
                db.commit()

                # Debata - Fáze 2 (Rebuttal autorek na recenze)
                rebuttal_tasks = []
                for review in valid_reviews:
                    author = next(a for a in authors if a.id == next(s.author_id for s in valid_stories if s.id == review.story_id))
                    critic = next(c for c in critics if c.id == review.critic_id)
                    story = next(s for s in valid_stories if s.id == review.story_id)
                    rebuttal_tasks.append(_author_rebuttal_task(client, semaphore, author, story, review, critic))
                
                await asyncio.gather(*rebuttal_tasks, return_exceptions=True)
                db.commit()

                # Debata - Fáze 3 (Final Verdict kritiků)
                final_tasks = []
                for review in valid_reviews:
                    author = next(a for a in authors if a.id == next(s.author_id for s in valid_stories if s.id == review.story_id))
                    critic = next(c for c in critics if c.id == review.critic_id)
                    final_tasks.append(_critic_final_task(client, semaphore, critic, review, author))
                
                await asyncio.gather(*final_tasks, return_exceptions=True)
                db.commit()
                
                for c in critics: state.critic_statuses[c.id] = "🏁 Hodnocení dobojováno."

                # Čtenáři - Fáze 4 (Čtenářské ohlasy po vydání)
                reader_tasks = []
                for story in valid_stories:
                    story_author = next(a for a in authors if a.id == story.author_id)
                    story_reviews = [r for r in valid_reviews if r.story_id == story.id]
                    for reader in readers:
                        reader_tasks.append(_reader_task(client, semaphore, db, story, story_author, story_reviews, reader))
                
                reader_results = await asyncio.gather(*reader_tasks, return_exceptions=True)
                valid_reader_reviews = []
                clean_r_reviews = [r if not isinstance(r, Exception) else None for r in reader_results]
                
                for (story, reader), rr in zip([(s, rd) for s in valid_stories for rd in readers], clean_r_reviews):
                    if rr:
                        rr.story_id = story.id
                        valid_reader_reviews.append(rr)
                
                db.add_all(valid_reader_reviews)
                db.commit()

                # Příprava SHRNUTÍ DĚNÍ
                arena_summary = f"Shrnutí událostí kola {round_num}:\n"
                for s in valid_stories:
                    arena_summary += f"\n--- Povídka: {s.title} (Autor ID: {s.author_id}) ---\n"
                    reves = [r for r in valid_reviews if r.story_id == s.id]
                    for r in reves:
                        arena_summary += f"- Kritik {r.critic_id} skóre: {r.scores_json}. Finální verdikt: {r.critic_final_response}\n"
                    r_reves = [rr for rr in valid_reader_reviews if rr.story_id == s.id]
                    for rr in r_reves:
                        arena_summary += f"- Čtenář {rr.reader_id} říká: {rr.review_md}\n"

                # Reflexe autorů
                reflection_tasks_authors = []
                for author in authors:
                    auth_story = next((s for s in valid_stories if s.author_id == author.id), None)
                    if auth_story:
                        auth_reviews = [r for r in valid_reviews if r.story_id == auth_story.id]
                        reflection_tasks_authors.append(_reflection_task(client, semaphore, author, auth_story, auth_reviews, arena_summary))
                    else:
                        async def dummy_ret(p): return True
                        reflection_tasks_authors.append(dummy_ret(author.persona_prompt))
                
                # Reflexe kritiků
                reflection_tasks_critics = []
                for critic in critics:
                    critic_reviews = [r for r in valid_reviews if r.critic_id == critic.id]
                    reflection_tasks_critics.append(_critic_reflection_task(client, semaphore, critic, critic_reviews, arena_summary))

                # Spuštění všech reflexí najednou
                await asyncio.gather(*reflection_tasks_authors, return_exceptions=True)
                await asyncio.gather(*reflection_tasks_critics, return_exceptions=True)
                    
                db.commit()
                for author in authors: state.author_statuses[author.id] = "Zasloužený spánek."
                for critic in critics: state.critic_statuses[critic.id] = "Zasloužený spánek."
                for reader in readers: state.reader_statuses[reader.id] = "Kniha odložena na noční stolek."
                
                print(f"=== KOLO {round_num} DOKONČENO ===")

    finally:
        state.is_running = False
        db.close()

def run_round_orchestration(round_num: int, num_rounds: int = 1):
    asyncio.run(run_round_orchestration_async(round_num, num_rounds))
