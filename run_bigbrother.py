import asyncio
from app.database import SessionLocal
from app import models
from app.mcp_server import _process_feedback_async

async def main():
    db = SessionLocal()
    try:
        # Spisovatel 2
        author2 = db.query(models.Author).filter(models.Author.id == 2).first()
        await _process_feedback_async(author2, "TADY BIGBROTHER. Tvé neustálé výmluvy směrem ke kritikům, že tvé ploché postavy a nevyjasněné motivace jsou 'záměrnou mlhou' a 'tajemstvím Ghal-Zadu', jsou liché. Tajemno funguje jen tehdy, když má čtenář dostatek pevných vodítek. Přestaň se tvářit, že tvé nedostatky jsou umělecký záměr. Vytvoř postavám skutečnou, pevnou psychologii a motivace. Zapracuj to okamžitě do svého stylu!", True, "BigBrother")
        
        # Critic 4
        critic4 = db.query(models.Critic).filter(models.Critic.id == 4).first()
        await _process_feedback_async(critic4, "TADY BIGBROTHER. Chválím tvou bystrost, ale uber plyn ohledně nekompromisního dodržování Původního Kánonu Aethelgardu. Nech autory trochu experimentovat a inovovat. Soustřeď se teď víc na to, zda je příběh napínavý, dramatický a postavy jdou do hloubky, místo abys hned každé porušení kánonu trestal. Dovol vývoj.", False, "BigBrother")
        
        db.commit()
        print("BIGBROTHER ÚSPĚŠNĚ ZASÁHL DO DATABÁZE A DONUTIL AGENTY K REFLEXI.")
    finally:
        db.close()

asyncio.run(main())
