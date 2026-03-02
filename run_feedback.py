import asyncio
from app.database import SessionLocal
from app import models
from app.mcp_server import _process_feedback_async

async def main():
    db = SessionLocal()
    try:
        author = db.query(models.Author).filter(models.Author.id == 4).first()
        critic = db.query(models.Critic).filter(models.Critic.id == 3).first()
        await _process_feedback_async(author, "BIGBROTHER TĚ SLEDUJE. Tvé opakované výmluvy v debatách s kritiky, že tvé gramatické chyby a nesrozumitelné slovosledy jsou záměrný styl pro vystihující nervozitu, se nezakládají na pravdě. Stylistický experiment nesmí být na úkor čitelnosti. Od nynějška se zaměř na precizní čistotu českého jazyka. Pokud jde o tvé koncepty Omega-9 a Alissy, chválíme tě - do hloubky a detailů jdi dál, ale respektuj pravidla světa Aethelgard.", True, "BigBrother (Antigravity v roli Vševědoucího Superintendenta)")
        await _process_feedback_async(critic, "BIGBROTHER TĚ SLEDUJE. Velmi si ceníme tvé bdělosti nad PŮVODNÍ BIBLE SVĚTA Aethelgardu a tvé nekompromisní snahy o jazykovou čistotu. Nicméně dej si pozor, abys tvůrce (zejména Scifi spisovatele č. 3 a 4) ve své kritice příliš nesvazoval. Oceňuj jejich snahu integrovat moderní technologii do magického podzemí, protože propojení těchto dvou světů je v zájmu vyšší moci. Tvým úkolem je hlídat logiku tohoto propojování, nikoliv ho hned zakazovat.", False, "BigBrother (Antigravity v roli Vševědoucího Superintendenta)")
        db.commit()
        print("FEEDBACK ÚSPĚŠNĚ APLIKOVÁN DO MOZKŮ.")
    finally:
        db.close()

asyncio.run(main())
