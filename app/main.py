from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from . import models
from .database import engine, get_db
from .agent import run_round_orchestration

# Vytvoření tabulek
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="BookClaw Literární Aréna")

@app.get("/")
def redirect_to_index():
    return RedirectResponse(url="/static/index.html")

# Přistoupení k lokální app/static
app.mount("/static", StaticFiles(directory="app/static"), name="static")


class AuthorResponse(BaseModel):
    id: int
    name: str
    genre: str
    style: str
    persona_prompt: str
    knowledge_base: str
    relationships: str
    world_id: Optional[int]
    write_mode: str
    novel_outline: str
    local_bible: str

    class Config:
        from_attributes = True

class WorldResponse(BaseModel):
    id: int
    name: str
    bible_md: str
    category: str
    is_original: int

    class Config:
        from_attributes = True

class StoryResponse(BaseModel):
    id: int
    author_id: int
    world_id: int
    round: int
    title: str
    text_md: str
    created_at: str

    class Config:
        from_attributes = True

class ReviewResponse(BaseModel):
    id: int
    story_id: int
    critic_id: int
    scores_json: str
    review_md: str
    author_rebuttal: Optional[str] = None
    critic_final_response: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class CriticResponse(BaseModel):
    id: int
    name: str
    persona_prompt: str
    knowledge_base: str
    relationships: str

    class Config:
        from_attributes = True

class ReaderResponse(BaseModel):
    id: int
    name: str
    persona_prompt: str
    knowledge_base: str
    relationships: str

    class Config:
        from_attributes = True

class ReaderReviewResponse(BaseModel):
    id: int
    story_id: int
    reader_id: int
    review_md: str
    proposed_story_md: str
    created_at: str

    class Config:
        from_attributes = True

@app.get("/api/authors", response_model=List[AuthorResponse])
def get_authors(db: Session = Depends(get_db)):
    return db.query(models.Author).all()

@app.get("/api/worlds", response_model=List[WorldResponse])
def get_worlds(db: Session = Depends(get_db)):
    return db.query(models.World).all()

@app.get("/api/critics", response_model=List[CriticResponse])
def get_critics(db: Session = Depends(get_db)):
    return db.query(models.Critic).all()

@app.get("/api/readers", response_model=List[ReaderResponse])
def get_readers(db: Session = Depends(get_db)):
    return db.query(models.Reader).all()

@app.get("/api/stories", response_model=List[StoryResponse])
def get_stories(db: Session = Depends(get_db)):
    stories = db.query(models.Story).order_by(models.Story.round.desc()).all()
    res = []
    for s in stories:
        res.append({
            "id": s.id,
            "author_id": s.author_id,
            "world_id": s.world_id,
            "round": s.round,
            "title": s.title,
            "text_md": s.text_md,
            "created_at": str(s.created_at)
        })
    return res

@app.get("/api/reviews", response_model=List[ReviewResponse])
def get_reviews(story_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.Review)
    if story_id:
        query = query.filter(models.Review.story_id == story_id)
    reviews = query.all()
    res = []
    for r in reviews:
        res.append({
            "id": r.id,
            "story_id": r.story_id,
            "critic_id": r.critic_id,
            "scores_json": r.scores_json,
            "review_md": r.review_md,
            "author_rebuttal": r.author_rebuttal,
            "critic_final_response": r.critic_final_response,
            "created_at": str(r.created_at)
        })
    return res

@app.get("/api/reader-reviews", response_model=List[ReaderReviewResponse])
def get_reader_reviews(story_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.ReaderReview)
    if story_id:
        query = query.filter(models.ReaderReview.story_id == story_id)
    reviews = query.all()
    res = []
    for r in reviews:
        res.append({
            "id": r.id,
            "story_id": r.story_id,
            "reader_id": r.reader_id,
            "review_md": r.review_md,
            "proposed_story_md": r.proposed_story_md,
            "created_at": str(r.created_at)
        })
    return res

class RoundRequest(BaseModel):
    num_rounds: int = 1

@app.post("/api/rounds/run")
def run_round(req: RoundRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Zjistíme aktuální kolo
    max_round = db.query(models.Story).order_by(models.Story.round.desc()).first()
    next_round = max_round.round + 1 if max_round else 1
    
    background_tasks.add_task(run_round_orchestration, next_round, req.num_rounds)
    return {"message": f"Spouštím {req.num_rounds} kol(o) od kola {next_round} na pozadí...", "start_round": next_round, "num_rounds": req.num_rounds}

@app.post("/api/init-db")
def init_db(db: Session = Depends(get_db)):
    # Opravdový restart: smažeme tabulky a vytvoříme je znovu se správným schématem
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    
    # Zkontrolujeme, zda už přeci jen něco nezůstalo (teď už by nemělo)
    if db.query(models.World).count() > 0:
        return {"message": "Databáze už obsahuje data. Přeskakuji inicializaci."}
        
    world_original = models.World(
        name="Aethelgard & Neon City (Původní kánon)",
        category="fantasy", # Hybridní, ale primárně fantasy základ
        is_original=1,
        bible_md="""# Aethelgard & Neon City (Sdílené Univerzum)
Tento svět osciluje mezi dvěma realitami. Aethelgard (Fantasy) a Neon City (Cyberpunk). 
Pravidlo č.1: Žádná Wi-Fi ani technologie v Aethelgardu. Žádná magie v Neon City."""
    )
    db.add(world_original)
    
    # 3 Nové Fantasy Bible
    w_f1 = models.World(name="Ztracené Souostroví", category="fantasy", is_original=0, bible_md="Svět plný létajících ostrovů a krystalové magie. Doprava jen na dracích nebo vzducholodích.")
    w_f2 = models.World(name="Podzemní Říše Ghal-Zad", category="fantasy", is_original=0, bible_md="Civilizace žijící v obřích jeskyních. Světlo vydávají pouze luminiscenční houby. Povrch je neobyvatelný žárem.")
    w_f3 = models.World(name="Hvozd Tisíce Stínů", category="fantasy", is_original=0, bible_md="Nekonečný les, kde stromy mluví a čas plyne jinak. Hlavním platidlem jsou vzpomínky.")
    
    # 3 Nové Sci-Fi Bible
    w_s1 = models.World(name="Stanice Omega-9", category="scifi", is_original=0, bible_md="Těžební stanice na okraji černé díry. Časové dilatace jsou běžným jevem. Nedostatek kyslíku je věčný problém.")
    w_s2 = models.World(name="Ledová planeta Krios", category="scifi", is_original=0, bible_md="Všudypřítomný mráz. Lidé žijí v termálních dómech. Hlavním zdrojem energie je jádro planety.")
    w_s3 = models.World(name="Digitální Pustina", category="scifi", is_original=0, bible_md="Svět, kde fyzická těla zanikla a lidstvo žije v simulaci, která se začínáno rozpadat kvůli virům.")
    
    db.add_all([w_f1, w_f2, w_f3, w_s1, w_s2, w_s3])
    db.commit()
    
    authors = [
        models.Author(
            name="Spisovatel 1 (Sir Eddings - Klasická Fantasy)",
            genre="fantasy",
            style="Epické výpravy, archetypy hrdinů, vtipné dialogy.",
            write_mode="novel", # ROMÁN
            persona_prompt="""Jsi zkušený a oblíbený fantasy spisovatel stylu Davida Eddingse. Píšeš dlouhý román na pokračování.""",
            world_id=world_original.id
        ),
        models.Author(
            name="Spisovatel 2 (Mr. Zelazny - Temná Fantasy)",
            genre="fantasy",
            style="Vnitřní monology, amorální postavy, cynismus.",
            write_mode="random", # NÁHODA
            persona_prompt="""Jsi mistr surrealistické fantasy stylu Rogera Zelaznyho.""",
            world_id=world_original.id
        ),
        models.Author(
            name="Spisovatel 3 (Doktor Asimov - Hard Sci-Fi)",
            genre="scifi",
            style="Logika, dopad technologií, dedukce.",
            write_mode="novel", # ROMÁN
            persona_prompt="""Jsi respektovaný autor hard sci-fi stylu Isaaca Asimova. Píšeš dlouhý sci-fi román.""",
            world_id=world_original.id
        ),
        models.Author(
            name="Spisovatel 4 (Zero-Cool - Cyberpunk)",
            genre="scifi",
            style="Drsné tempo, slang, implantáty.",
            write_mode="random", # NÁHODA
            persona_prompt="""Jsi moderní sci-fi autor z generace cyberpunku.""",
            world_id=world_original.id
        )
    ]
    db.add_all(authors)

    critics = [
        models.Critic(name="Critic 1 (Strukturální)", persona_prompt="Jsi strukturální kritik..."),
        models.Critic(name="Critic 2 (Lore-master)", persona_prompt="Jsi Lore-master. TVŮJ ÚKOL: Okamžitě brutálně sestřel autora, pokud jeho local_bible nebo povídka odporuje HLAVNÍ BIBLI SVĚTA (Kánonu). Žádné slitování s Wi-Fi ve fantasy!"),
        models.Critic(name="Critic 3 (Jazykovědec)", persona_prompt="Jsi stylistický a gramatický jazykovědec..."),
        models.Critic(name="Critic 4 (Žánrový fanoušek)", persona_prompt="Jsi nekompromisní fanoušek žánru...")
    ]
    db.add_all(critics)

    db.add_all(critics)

    readers = [
        models.Reader(name="Čtenář 1 (Běžný Konzument)", persona_prompt="Jsi Běžný konzument popkultury. Máš rád akci, napětí a jednoduché pochopení děje. Nemáš rád složité filozofování. Přečti si povídku i kritiky, zhodnoť ji z pohledu fanouška zábavy a navrhni, kam a jak by příběh mohl pokračovat dle tvého gusta."),
        models.Reader(name="Čtenář 2 (Náročný Knihomol)", persona_prompt="Jsi Náročný knihomol. Potrpíš si na nuance, rozvoj postav, atmosférické popisy a hluboká sdělení plná skrytých významů. Přečti si povídku i názory kritiků, sepsuj její plytkost či vyzdvihni hloubku, ohodnoť profesionalitu kritiků a navrhni komplexnější a umělečtější směřování zápletky.")
    ]
    db.add_all(readers)

    db.commit()
    return {"message": "Databáze úspěšně inicializována pro Fázi 6 (Čtenáři a nové světy)."}

@app.get("/api/status")
def get_status():
    from .agent import state
    return {
        "is_running": state.is_running,
        "round_num": state.round_num,
        "authors": state.author_statuses,
        "critics": state.critic_statuses,
        "readers": state.reader_statuses
    }

@app.get("/api/reports/grammar-wars", response_class=PlainTextResponse)
def get_grammar_wars(db: Session = Depends(get_db)):
    critic = db.query(models.Critic).filter(models.Critic.name.contains("Jazykovědec")).first()
    if not critic:
        return "Jazykovědec nenalezen v databázi."

    reviews = db.query(models.Review).filter(
        models.Review.critic_id == critic.id,
        models.Review.author_rebuttal.isnot(None),
        models.Review.critic_final_response.isnot(None)
    ).all()

    report = f"# BigBrother Report: Gramatické Války (Kritik: {critic.name})\n\n"
    report += f"Celkem zaznamenaných plnohodnotných konfliktů: {len(reviews)}\n\n"

    for r in reviews:
        story = db.query(models.Story).filter(models.Story.id == r.story_id).first()
        author = db.query(models.Author).filter(models.Author.id == story.author_id).first()
        
        report += f"## Konflikt u povídky: {story.title} (Kolo {story.round})\n"
        report += f"**Autor:** {author.name}\n\n"
        report += f"**Původní recenze (skóre {r.scores_json}):**\n{r.review_md}\n\n"
        report += f"**Obhajoba autora:**\n{r.author_rebuttal}\n\n"
        report += f"**Finální verdikt kritika:**\n{r.critic_final_response}\n\n"
        report += "---\n\n"

    return report

