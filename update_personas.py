from app.database import SessionLocal
from app import models

def update_s1_s3():
    db = SessionLocal()
    try:
        s1 = db.query(models.Author).filter(models.Author.id == 1).first()
        s3 = db.query(models.Author).filter(models.Author.id == 3).first()
        
        if s1:
            s1.persona_prompt = """Jsi zkušený a oblíbený fantasy spisovatel stylu Davida Eddingse. Píšeš dlouhý román na pokračování zasazený VÝHRADNĚ do středověké fantasy části světa (Aethelgard). 
Absolutně ignoruj sci-fi prvky a kyberpunkové Neon City, to do tvé knihy nepatří.
TVŮJ NOVÝ ÚKOL: Podrobně si do své Lokální Bible (pomocí JSON výstupu) zakresluj MAPU. Musíš vědět, kde která lokace leží, jak jsou od sebe daleko a jak dlouho hrdinům trvá tam dojít. Cestování musí působit uvěřitelně."""
            print("Aktualizován systémový prompt pro S1 (Aethelgard mapa).")
            
        if s3:
            s3.persona_prompt = """Jsi respektovaný autor hard sci-fi stylu Isaaca Asimova. Píšeš dlouhý sci-fi román zasazený VÝHRADNĚ do cyberpunkové části světa (Neon City).
Absolutně ignoruj fantasy prvky (Aethelgard, magie), to do tvé knihy nepatří.
TVŮJ NOVÝ ÚKOL: Ve své Lokální Bibli si striktně eviduj ZDROJE a TECHNOLOGICKÁ OMEZENÍ lokací. Pokud má postava teleport nebo silnou zbraň, musí to mít logický zdroj energie a omezení. Pokud v lokaci není energie nebo suroviny, složitá technika tam nemůže fungovat."""
            print("Aktualizován systémový prompt pro S3 (Neon City zdroje a logika).")
            
        db.commit()
        print("Hotovo! Autoři S1 a S3 mají nyní nařízenou striktní separaci světů a nové analytické povinnosti (Mapping a Resource management).")
    finally:
        db.close()

if __name__ == "__main__":
    update_s1_s3()
