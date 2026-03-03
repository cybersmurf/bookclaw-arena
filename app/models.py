from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from .database import Base

class World(Base):
    __tablename__ = "world"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bible_md = Column(Text, default="")
    category = Column(String, default="fantasy") # 'fantasy' nebo 'scifi'
    is_original = Column(Integer, default=1) # 1 pro hlavní, 0 pro doplňkové
    
    authors = relationship("Author", back_populates="world")
    stories = relationship("Story", back_populates="world")

class Author(Base):
    __tablename__ = "author"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    genre = Column(String) # 'fantasy' nebo 'scifi'
    style = Column(Text)
    persona_prompt = Column(Text)
    knowledge_base = Column(Text, default="Zatím nevím nic nad rámec své výchozí povahy.")
    relationships = Column(Text, default="Zatím nemám vyhraněný vztah k žádnému z kolegů ani kritiků.")
    
    # Fáze 4: Rozšíření pro romány a režimy psaní
    write_mode = Column(String, default="random") # 'novel' nebo 'random'
    novel_outline = Column(Text, default="") # Seznam kapitol/plán
    local_bible = Column(Text, default="") # Vlastní poznámky k loru

    world_id = Column(Integer, ForeignKey("world.id"))

    world = relationship("World", back_populates="authors")
    stories = relationship("Story", back_populates="author")

class Story(Base):
    __tablename__ = "story"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("author.id"))
    world_id = Column(Integer, ForeignKey("world.id"))
    round = Column(Integer)
    title = Column(String)
    text_md = Column(Text)
    system_prompt = Column(Text, nullable=True)
    user_prompt = Column(Text, nullable=True)
    local_bible = Column(Text, nullable=True)
    knowledge_base = Column(Text, nullable=True)
    relationships = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    author = relationship("Author", back_populates="stories")
    world = relationship("World", back_populates="stories")
    reviews = relationship("Review", back_populates="story")
    reader_reviews = relationship("ReaderReview", back_populates="story")

class Review(Base):
    __tablename__ = "review"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("story.id"))
    critic_id = Column(Integer) # Id kritika 1-4 (foreign key to critic.id by logicky sedel, ale resim pres id)
    scores_json = Column(Text) # JSON skóre
    review_md = Column(Text)
    author_rebuttal = Column(Text, nullable=True) # ZASTARALÉ: bude smazáno po migraci nebo fallback
    critic_final_response = Column(Text, nullable=True) # ZASTARALÉ
    discussion_json = Column(Text, default="[]") # NOVÉ: Pole historie konverzace [role, text]
    created_at = Column(TIMESTAMP, server_default=func.now())

    story = relationship("Story", back_populates="reviews")

class Critic(Base):
    __tablename__ = "critic"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    persona_prompt = Column(Text)
    knowledge_base = Column(Text, default="Zatím se jen rozkoukávám, mé vědomosti čerpají jen z vnitřního manuálu.")
    relationships = Column(Text, default="Zatím jsem objektivní, žádná averze ani sympatie k autorům.")

class Reader(Base):
    __tablename__ = "reader"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    persona_prompt = Column(Text)
    knowledge_base = Column(Text, default="Jsem náhodný čtenář bez hlubokých profesionálních znalostí.")
    relationships = Column(Text, default="Zatím jsem objektivní, žádná averze ani sympatie k nikomu.")
    
    reviews = relationship("ReaderReview", back_populates="reader")

class ReaderReview(Base):
    __tablename__ = "reader_review"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("story.id"))
    reader_id = Column(Integer, ForeignKey("reader.id"))
    review_md = Column(Text) # Zhodnocení povídky a reakce na kritiky
    proposed_story_md = Column(Text) # Vlastní vize příběhu od čtenáře
    created_at = Column(TIMESTAMP, server_default=func.now())

    story = relationship("Story", back_populates="reader_reviews")
    reader = relationship("Reader", back_populates="reviews")
