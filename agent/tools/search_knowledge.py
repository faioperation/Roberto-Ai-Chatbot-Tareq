from langchain_core.tools import tool
from rag.retriever import retrieve

@tool
async def search_knowledge(query: str, subject: str) -> str:
    """
    Search the knowledge base for relevant information.
    Use this when you need facts about services, pricing, destinations,
    procedures, or any business-specific information.
    Always use the correct subject: cargo, law, or education.
    Never use 'pricing' or any other value as subject.
    """
    # Force subject to be valid — prevent wrong namespace calls
    valid_subjects = ["cargo", "law", "education"]
    if subject not in valid_subjects:
        subject = "cargo"  # Default fallback

    result = await retrieve(query, subject)
    return result if result else "No relevant information found."