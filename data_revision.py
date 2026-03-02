from app.database import SessionLocal
from app import models

def clean_database():
    db = SessionLocal()
    try:
        # Krok 1: Smazat duplicitní povídky ve stejném kole pro stejného autora.
        # Chceme zachovat vždy jen první, kterou najdeme.
        stories = db.query(models.Story).order_by(models.Story.round, models.Story.author_id, models.Story.id).all()
        
        seen = set()
        to_delete_story_ids = []
        
        for s in stories:
            key = (s.round, s.author_id)
            if key in seen:
                to_delete_story_ids.append(s.id)
            else:
                seen.add(key)
                
        print(f"Bude smazáno {len(to_delete_story_ids)} duplicitních povídek (a k nim recenze).")
        
        if to_delete_story_ids:
            # Smažeme také recenze, které u nich byly napsány, aby nezůstali sirotci
            db.query(models.Review).filter(models.Review.story_id.in_(to_delete_story_ids)).delete(synchronize_session=False)
            db.query(models.ReaderReview).filter(models.ReaderReview.story_id.in_(to_delete_story_ids)).delete(synchronize_session=False)
            db.query(models.Story).filter(models.Story.id.in_(to_delete_story_ids)).delete(synchronize_session=False)
            db.commit()

        # Krok 2: Odstranit nedokončená kola (nemají přesně 4 různé povídky od 4 autorů)
        stories_after_dedup = db.query(models.Story).all()
        round_counts = {}
        for s in stories_after_dedup:
            round_counts[s.round] = round_counts.get(s.round, 0) + 1
            
        incomplete_rounds = [r for r, count in round_counts.items() if count != 4]
        
        print(f"Nekompletní kola k odstranění: {incomplete_rounds}")
        
        if incomplete_rounds:
            stories_to_delete = db.query(models.Story).filter(models.Story.round.in_(incomplete_rounds)).all()
            incomplete_ids = [s.id for s in stories_to_delete]
            
            db.query(models.Review).filter(models.Review.story_id.in_(incomplete_ids)).delete(synchronize_session=False)
            db.query(models.ReaderReview).filter(models.ReaderReview.story_id.in_(incomplete_ids)).delete(synchronize_session=False)
            db.query(models.Story).filter(models.Story.round.in_(incomplete_rounds)).delete(synchronize_session=False)
            db.commit()

        print("Databáze úspěšně vyčištěna!")
        
        # Zkontrolujeme nový stav
        final_stories = db.query(models.Story).all()
        final_rounds = set(s.round for s in final_stories)
        print(f"Finální stav: Celkem povídek={len(final_stories)}, Zůstala kola={sorted(final_rounds)}")

    finally:
        db.close()

if __name__ == "__main__":
    clean_database()
