from pinecone import Pinecone
from openai import OpenAI
from core.config import PINECONE_API_KEY, PINECONE_INDEX_NAME, OPENAI_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

async def retrieve(query: str, subject: str, top_k: int = 4) -> str:
    # Embed the query
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = embedding_response.data[0].embedding

    # Search Pinecone
    results = index.query(
        namespace=f"base-{subject}",
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )

    # Debug — see what Pinecone is returning
    print(f"\n[RAG DEBUG] Query: {query}")
    print(f"[RAG DEBUG] Namespace: base-{subject}")
    print(f"[RAG DEBUG] Matches found: {len(results.matches)}")
    for i, match in enumerate(results.matches):
        print(f"[RAG DEBUG] Match {i+1} score: {match.score}")
        print(f"[RAG DEBUG] Match {i+1} text: {match.metadata.get('text', '')[:100]}")

    # Extract chunks
    chunks = []
    for match in results.matches:
        if match.metadata and "text" in match.metadata:
            chunks.append(match.metadata["text"])

    result = "\n\n".join(chunks)
    print(f"[RAG DEBUG] Total context length: {len(result)} chars\n")
    
    return result