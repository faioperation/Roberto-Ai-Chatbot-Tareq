from pinecone import Pinecone
from openai import OpenAI
from core.config import PINECONE_API_KEY, PINECONE_INDEX_NAME, OPENAI_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def chunk_text(text: str, chunk_size: int = 500) -> list:
    words = text.split()
    
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    return chunks

def ingest(text: str, subject: str):
    chunks = chunk_text(text)

    vectors = []
    for i, chunk in enumerate(chunks):
        embedding = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk
        ).data[0].embedding

        vectors.append({
            "id": f"{subject}-{i}",      
            "values": embedding,           
            "metadata": {
                "text": chunk,             
                "subject": subject         
            }
        })


    index.upsert(vectors=vectors, namespace=f"base-{subject}")
    print(f"Ingested {len(vectors)} chunks for subject: {subject}")