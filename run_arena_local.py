import asyncio
from app.agent import run_round_orchestration_async
from app.database import SessionLocal
from app import models

def main():
    db = SessionLocal()
    max_round = db.query(models.Story).order_by(models.Story.round.desc()).first()
    next_round = max_round.round + 1 if max_round else 1
    db.close()
    
    print(f"Spouštím 3 kola iterace od kola {next_round}...")
    asyncio.run(run_round_orchestration_async(
        start_round_num=next_round, 
        theme_fantasy="Půlnoční odhalení", 
        theme_scifi="Ztráta kontroly", 
        num_rounds=3
    ))
    print("Hotovo!")

if __name__ == "__main__":
    main()
