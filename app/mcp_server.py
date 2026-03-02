import sys
import os

# Abychom mohli importovat moduly ze složky app, přidáme kořenový adresář projektu do cesty
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.fastmcp import FastMCP
from app.database import SessionLocal
from app import models
import asyncio
import httpx
from app.agent import _call_ollama_async, OLLAMA_MODEL, _build_reflection_schema

# Inicializace FastMCP instance pro BookClaw Arénu
mcp = FastMCP("BookClaw MCP Server")

@mcp.tool()
def get_completed_grammar_wars(critic_name: str = "Jazykovědec") -> str:
    """
    Returns a formatted report of all completed grammar conflicts (author rebuttal and critic final response present) for a specific critic.
    Use this to read the context before generating feedback for the critic. BigBrother should call this first.
    """
    db = SessionLocal()
    try:
        critic = db.query(models.Critic).filter(models.Critic.name.contains(critic_name)).first()
        if not critic:
            return f"Critic '{critic_name}' not found in database."

        reviews = db.query(models.Review).filter(
            models.Review.critic_id == critic.id,
            models.Review.author_rebuttal.isnot(None),
            models.Review.critic_final_response.isnot(None)
        ).all()

        if not reviews:
            return f"No completed grammar wars found for critic '{critic.name}'."

        report = f"# Grammar Wars Report for '{critic.name}'\n\n"
        for r in reviews:
            story = db.query(models.Story).filter(models.Story.id == r.story_id).first()
            author = db.query(models.Author).filter(models.Author.id == story.author_id).first()
            
            report += f"## Story: {story.title} (Round {story.round})\n"
            report += f"**Author:** {author.name}\n\n"
            report += f"**Original Review (Scores: {r.scores_json}):**\n{r.review_md}\n\n"
            report += f"**Author's Rebuttal:**\n{r.author_rebuttal}\n\n"
            report += f"**Critic's Final Verdict:**\n{r.critic_final_response}\n\n"
            report += "---\n\n"

        return report
    finally:
        db.close()

async def _process_feedback_async(agent, feedback_text: str, is_author: bool, model_signature: str) -> bool:
    role = "spisovatel" if is_author else "literární kritik"
    system_prompt = f"Jsi {role}. Dostal jsi zpětnou vazbu od vnějšího supervizora (uživatele). Tvým úkolem je tuto zpětnou vazbu zanalyzovat a zabudovat ji do příslušných sekcí své osobnosti a paměti ('persona_prompt', 'knowledge_base', 'relationships'). Vrať POUZE platný JSON."
    user_prompt = f"Tvá aktuální persona: {agent.persona_prompt}\nZnalosti: {agent.knowledge_base}\nVztahy: {agent.relationships}\n\nZpětná vazba od supervizora:\n{feedback_text}\n\nZamysli se nad radami a vygeneruj JSON s aktualizovanými poli, ať jsi v psaní/hodnocení příště lepší."
    
    schema = _build_reflection_schema()
    async with httpx.AsyncClient() as client:
        new_data = await _call_ollama_async(client, OLLAMA_MODEL, system_prompt, user_prompt, temperature=0.7, output_schema=schema)
        
    if new_data:
        agent.persona_prompt = new_data.get('persona_prompt', agent.persona_prompt)
        if model_signature:
            agent.persona_prompt += f"\n\n[Naposledy reflekoval mentorský zásah přes Ollamu od: {model_signature}]"
        agent.knowledge_base = new_data.get('knowledge_base', agent.knowledge_base)
        agent.relationships = new_data.get('relationships', agent.relationships)
        return True
    return False

@mcp.tool()
async def inject_critic_feedback(critic_name: str, feedback_text: str, model_signature: str = None) -> str:
    """
    Passes feedback to a specific critic, asking them to self-reflect and organically update
    their persona, knowledge base, and relationships, instead of hard-rewriting them.
    If 'model_signature' is provided (e.g., 'Claude-3.5-Sonnet'), it will be appended.
    """
    db = SessionLocal()
    try:
        critic = db.query(models.Critic).filter(models.Critic.name.contains(critic_name)).first()
        if not critic:
            return f"Critic '{critic_name}' not found."
            
        success = await _process_feedback_async(critic, feedback_text, False, model_signature)
        
        if success:
            db.commit()
            return f"Successfully passed feedback to critic '{critic.name}' and they updated their internal persona."
        else:
            return f"Failed to get structured JSON reflection from critic '{critic.name}'."
    finally:
        db.close()

@mcp.tool()
async def inject_author_feedback(author_name: str, feedback_text: str, model_signature: str = None) -> str:
    """
    Passes feedback to a specific author, asking them to self-reflect and organically update
    their persona, knowledge base, and relationships, instead of hard-rewriting them.
    If 'model_signature' is provided (e.g., 'Claude-3.5-Sonnet'), it will be appended.
    """
    db = SessionLocal()
    try:
        author = db.query(models.Author).filter(models.Author.name.contains(author_name)).first()
        if not author:
            return f"Author '{author_name}' not found."
            
        success = await _process_feedback_async(author, feedback_text, True, model_signature)
            
        if success:
            db.commit()
            return f"Successfully passed feedback to author '{author.name}' and they organically updated their knowledge/persona."
        else:
            return f"Failed to get structured JSON reflection from author '{author.name}'."
    finally:
        db.close()

@mcp.tool()
def get_agents() -> str:
    """
    Returns a list of all authors and critics currently existing in the BookClaw Arena.
    """
    db = SessionLocal()
    try:
        authors = db.query(models.Author).all()
        critics = db.query(models.Critic).all()
        
        report = "## Authors\n"
        for a in authors:
            report += f"- {a.name} (Genre: {a.genre})\n"
            
        report += "\n## Critics\n"
        for c in critics:
            report += f"- {c.name}\n"
            
        return report
    finally:
        db.close()

@mcp.tool()
def list_stories(round_num: int = None) -> str:
    """
    Returns a list of all stories (IDs, titles, rounds, and authors).
    Optionally filter by round_num. Use this to find a story ID.
    """
    db = SessionLocal()
    try:
        query = db.query(models.Story)
        if round_num is not None:
            query = query.filter(models.Story.round == round_num)
        stories = query.all()
        
        if not stories:
            return "No stories found."
            
        report = "## Stories\n"
        for s in stories:
            author = db.query(models.Author).filter(models.Author.id == s.author_id).first()
            author_name = author.name if author else "Unknown"
            report += f"- ID: {s.id} | Round: {s.round} | Title: '{s.title}' | Author: {author_name}\n"
        return report
    finally:
        db.close()

@mcp.tool()
def get_story_text(story_id: int) -> str:
    """
    Returns the full markdown text of a specific story by its ID.
    BigBrother should use this to read the entire story content for deep language or thematic analysis.
    """
    db = SessionLocal()
    try:
        story = db.query(models.Story).filter(models.Story.id == story_id).first()
        if not story:
            return f"Story with ID {story_id} not found."
            
        author = db.query(models.Author).filter(models.Author.id == story.author_id).first()
        author_name = author.name if author else "Unknown"
            
        report = f"# {story.title} (Round {story.round})\n"
        report += f"**Author:** {author_name}\n\n"
        report += f"{story.text_md}\n"
        return report
    finally:
        db.close()

if __name__ == "__main__":
    # Stdout je defaultní stdio transport pro MCP komunikaci s Claude desktop (či jinými LLM klienty)
    mcp.run(transport="stdio")
