from app.database import SessionLocal
from app import models

db = SessionLocal()
try:
    critics = db.query(models.Critic).all()
    out = ""
    for critic in critics:
        out += f"\n\n{'='*50}\nCRITIC: {critic.name}\n{'='*50}\n"
        reviews = db.query(models.Review).filter(
            models.Review.critic_id == critic.id,
            models.Review.author_rebuttal.isnot(None),
            models.Review.critic_final_response.isnot(None)
        ).all()
        
        for r in reviews:
            story = db.query(models.Story).filter(models.Story.id == r.story_id).first()
            author = db.query(models.Author).filter(models.Author.id == story.author_id).first()
            out += f"\n--- Story: {story.title} (Round {story.round}) --- Author: {author.name} ---\n"
            out += f"Critic:\n{r.review_md}\n"
            out += f"Author Rebuttal:\n{r.author_rebuttal}\n"
            out += f"Critic Final:\n{r.critic_final_response}\n"
            
    with open("pearls.txt", "w") as f:
        f.write(out)
finally:
    db.close()
