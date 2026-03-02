import textwrap
from app.database import SessionLocal
from app import models

db = SessionLocal()
try:
    reviews = db.query(models.Review).join(models.Story).filter(
        models.Story.round >= 14,
        models.Review.author_rebuttal.isnot(None),
        models.Review.critic_final_response.isnot(None)
    ).order_by(models.Story.round.desc()).limit(10).all()

    print("=== LITERALNÍ PERLY: POSLEDNÍ HLÁŠKY Z ARÉNY ===")
    out = ""
    for r in reviews:
        story = db.query(models.Story).filter_by(id=r.story_id).first()
        critic = db.query(models.Critic).filter_by(id=r.critic_id).first()
        author = db.query(models.Author).filter_by(id=story.author_id).first()
        
        out += f"\n🏆 KOLO {story.round} | {author.name} ⚔️ {critic.name}\n"
        out += f"Povídka: {story.title}\n"
        out += f"Kritika: {textwrap.shorten(r.review_md, width=250)}\n"
        out += f"Obrana: {textwrap.shorten(r.author_rebuttal, width=250)}\n"
        out += f"Verdikt: {textwrap.shorten(r.critic_final_response, width=250)}\n"
        out += "-"*60
    
    with open("pearls_new.txt", "w") as f:
        f.write(out)
    print(out)
finally:
    db.close()
