import fitz
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from core.config import PINECONE_API_KEY, PINECONE_INDEX_NAME, OPENAI_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def create_index_if_not_exists():
    existing_indexes = [index.name for index in pc.list_indexes()]
    if PINECONE_INDEX_NAME in existing_indexes:
        print(f"Index '{PINECONE_INDEX_NAME}' already exists. Skipping creation.")
        return
    print(f"Creating index '{PINECONE_INDEX_NAME}'...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    print(f"Index created successfully!")

def clear_namespace(subject: str):
    # Delete all vectors in this namespace before re-ingesting
    index = pc.Index(PINECONE_INDEX_NAME)
    try:
        index.delete(delete_all=True, namespace=f"base-{subject}")
        print(f"Cleared namespace: base-{subject}")
    except Exception as e:
        # Namespace doesn't exist yet (fresh index) — safe to skip
        print(f"Namespace base-{subject} not found, skipping clear.")

def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text

def split_by_subject(full_text: str) -> dict:
    subjects = {}
    cargo_start = full_text.find("TUGATAI CARGO")
    education_start = full_text.find("EDUCATION SECTOR")
    law_start = full_text.find("LAW SECTOR")
    subjects["cargo"] = full_text[cargo_start:education_start]
    subjects["education"] = full_text[education_start:law_start]
    subjects["law"] = full_text[law_start:]
    return subjects

def chunk_text(text: str, chunk_size: int = 60, overlap: int = 20) -> list:
    # overlap means chunks share some words
    # This ensures pricing data doesn't get cut off between chunks
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        # Move forward by chunk_size minus overlap
        # So next chunk starts 20 words back = overlap
        i += chunk_size - overlap
    return chunks

def ingest(text: str, subject: str):
    index = pc.Index(PINECONE_INDEX_NAME)
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

if __name__ == "__main__":
    create_index_if_not_exists()

    pdf_path = "data/MATRIX_AI.pdf"
    print("Extracting text from PDF...")
    full_text = extract_text_from_pdf(pdf_path)

    print("Splitting by subject...")
    subjects = split_by_subject(full_text)

    for subject, text in subjects.items():
        if text.strip():
            # Clear old data first
            print(f"Clearing old data for {subject}...")
            clear_namespace(subject)

            print(f"Ingesting {subject}...")
            ingest(text, subject)
            print(f"{subject} done!")

    print("\nAll done! Data stored in Pinecone successfully.")