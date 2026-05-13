"""
rag_chroma.py - POBOLJŠANA VERZIJA
Sa boljom relevantnošću pretrage
"""

import os
import hashlib
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Učitavanje environment varijabli - Loading environment variables
load_dotenv()

# 2. Pristupi varijabli pomoću os.getenv - Access the variable using os.getenv
hf_token = os.getenv("HF_TOKEN")

# Sada koristi hf_token u svojoj logici - Now use hf_token in your logic
print(f"Token je uspješno učitan!")

# Globalni objekti
_chroma_client = None
_collection = None
_embedding_model = None

# Konfiguracija
CHROMA_PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "pregnancy_advice_bhs"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# POBOLJŠANJE 1: Povećani broj rezultata za bolje filtriranje
DEFAULT_N_RESULTS = 8  # Povećano sa 5 na 8
MIN_RELEVANCE_THRESHOLD = 0.45  # Povećano sa 0.35 na 0.45 (samo kvalitetniji rezultati)

# POBOLJŠANJE 2: Informacije o vodiču
GUIDE_INFO = {
    'title': 'Klinički vodič za antenatalnu zaštitu',
    'year': '2021',
    'publisher': 'Ministarstvo zdravlja',
    'version': '3.0'
}


def get_embedding_model():
    """Lazy loading embedding modela."""
    global _embedding_model
    if _embedding_model is None:
        print(f"Učitavam višejezični embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def get_chroma_client():
    """Lazy loading Chroma klijenta."""
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
    return _chroma_client


def get_collection():
    """Dohvata ili kreira Chroma kolekciju."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        
        existing_collections = [c.name for c in client.list_collections()]
        
        if COLLECTION_NAME in existing_collections:
            _collection = client.get_collection(COLLECTION_NAME)
            print(f"Kolekcija '{COLLECTION_NAME}' učitana. Broj dokumenata: {_collection.count()}")
        else:
            _collection = client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Kreirana nova kolekcija '{COLLECTION_NAME}'")
    
    return _collection


def delete_collection():
    """Briše postojeću kolekciju."""
    global _collection
    try:
        client = get_chroma_client()
        client.delete_collection(COLLECTION_NAME)
        _collection = None
        print(f"Kolekcija '{COLLECTION_NAME}' uspješno izbrisana.")
    except Exception as e:
        print(f"Kolekcija '{COLLECTION_NAME}' ne postoji: {e}")


def _chroma_embedding_function(texts: List[str]) -> List[List[float]]:
    """Embedding funkcija za Chroma."""
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    """
    POBOLJŠANO: Dijeli tekst na fragmente sa manjim preklapanjem.
    Manji chunkovi = preciznija pretraga.
    """
    if not text or len(text) < chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        # Pokušaj završiti na kraju rečenice
        if end < text_length:
            for sep in ['. ', '? ', '! ', '\n\n', '\n', '; ', ': ']:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start:
                    end = last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk and len(chunk) > 50:  # Odbaci prekratke chunkove
            chunks.append(chunk)
        
        start = max(start + 1, end - overlap)
    
    return chunks


def load_pdf_to_chunks(pdf_path: str) -> List[Dict[str, Any]]:
    """Učitava PDF i dijeli ga na fragmentove."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError("PyPDF2 nije instaliran. Pokreni: pip install PyPDF2")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF fajl nije pronađen: {pdf_path}")
    
    print(f"Učitavam PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    full_text = []
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            full_text.append(text)
        print(f"  Obrađena stranica {page_num + 1}/{len(reader.pages)}")
    
    combined_text = "\n\n".join(full_text)
    chunks = chunk_text(combined_text)
    
    print(f"Kreirano {len(chunks)} fragmenata iz PDF-a")
    
    documents = []
    for i, chunk in enumerate(chunks):
        documents.append({
            'text': chunk,
            'metadata': {
                'source': os.path.basename(pdf_path),
                'chunk_id': i,
                'page_start': i * 2,
                'page_end': i * 2 + 1
            }
        })
    
    return documents


def build_vector_store_from_pdf(pdf_path: str, force_rebuild: bool = False):
    """Gradi vektorsku bazu iz PDF dokumenta."""
    if force_rebuild:
        delete_collection()
    
    collection = get_collection()
    
    if collection.count() > 0 and not force_rebuild:
        print(f"Vektorska baza već sadrži {collection.count()} fragmenata.")
        return
    
    documents = load_pdf_to_chunks(pdf_path)
    
    if not documents:
        print("Nema fragmenata za indeksiranje.")
        return
    
    ids = []
    texts = []
    metadatas = []
    
    for i, doc in enumerate(documents):
        unique_id = hashlib.md5(f"{doc['text'][:100]}_{i}".encode()).hexdigest()[:16]
        ids.append(unique_id)
        texts.append(doc['text'])
        metadatas.append(doc['metadata'])
    
    for idx in range(0, len(ids), 100):
        batch_ids = ids[idx:idx+100]
        batch_texts = texts[idx:idx+100]
        batch_metadatas = metadatas[idx:idx+100]
        embeddings = _chroma_embedding_function(batch_texts)
        
        collection.add(
            ids=batch_ids,
            documents=batch_texts,
            metadatas=batch_metadatas,
            embeddings=embeddings
        )
        print(f"  Dodano {len(batch_ids)} fragmenata...")
    
    print(f"\nUspješno indeksirano {len(documents)} fragmenata.")


def semantic_search(query: str, n_results: int = DEFAULT_N_RESULTS) -> List[Dict[str, Any]]:
    """
    POBOLJŠANO: Semantička pretraga sa filtriranjem po relevantnosti.
    """
    collection = get_collection()
    
    if collection.count() == 0:
        print("Upozorenje: Vektorska baza je prazna.")
        return []
    
    model = get_embedding_model()
    query_embedding = model.encode([query])[0].tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    formatted_results = []
    if results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            distance = results['distances'][0][i] if results['distances'] else None
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            
            relevance_score = 1 - distance if distance else 0
            
            # POBOLJŠANJE: Filtriraj samo rezultate iznad praga
            if relevance_score >= MIN_RELEVANCE_THRESHOLD:
                formatted_results.append({
                    'text': doc,
                    'metadata': metadata,
                    'distance': distance,
                    'relevance_score': relevance_score
                })
    
    return formatted_results


def get_guide_header(risk_level: str = "Low") -> str:
    
    guide_text = ""
    
    # ISPRAVKA: Provjeri da li je risk_level string ili nešto drugo
    if "High" in str(risk_level) or "VISOK" in str(risk_level).upper():
        guide_text += "VISOK RIZIK - Preporuke za hitnu intervenciju:\n\n"
    else:
        guide_text += "STANDARDNA NJEGA - Opšte preporuke za zdravu trudnoću:\n\n"
    
    return guide_text

def get_relevant_advice_rag(query_context: str, patient_data: dict, n_results: int = 3) -> str:
    
    query = build_semantic_query_bhs(patient_data, query_context)
    
    # Povećan broj rezultata za bolju selekciju
    results = semantic_search(query, n_results=DEFAULT_N_RESULTS)
    
    if not results:
        return "Trenutno nema specifičnih preporuka za vaše parametre. Savjetujemo konsultaciju s ljekarom."
    
    # Uvodna rečenica o vodiču
    risk_level = query_context if "rizik" in query_context.lower() else "Low"
    advice_parts = [get_guide_header(risk_level)]
    
    # Dodaj relevantne preporuke
    added_count = 0
    for i, result in enumerate(results[:n_results], 1):
        if result['relevance_score'] >= MIN_RELEVANCE_THRESHOLD:
            advice_parts.append(f"**Preporuka {i}** (relevantnost: {result['relevance_score']:.0%}):")
            advice_parts.append(result['text'])
            advice_parts.append("")
            added_count += 1
    
    if added_count == 0:
        # Ako nema dovoljno kvalitetnih rezultata, smanji prag
        advice_parts = [get_guide_header(risk_level)]
        for i, result in enumerate(results[:3], 1):
            advice_parts.append(f"**Preporuka {i}:**")
            advice_parts.append(result['text'])
            advice_parts.append("")
    
    return "\n".join(advice_parts)


def build_semantic_query_bhs(patient_data: dict, context: str = "") -> str:
    """
    POBOLJŠANO: Grafi bolji semantički upit.
    Dodaje težinske faktore za važnije parametre.
    """
    query_parts = []
    
    # Dijabetes i glukoza (najveća težina)
    glucose = patient_data.get('glukoza_u_krvi', 0)
    diabetes = patient_data.get('dijabetes', 0)
    gdm = patient_data.get('gestacijski_dijabetes', 0)
    
    if glucose > 7.8 or diabetes == 1 or gdm == 1:
        query_parts.extend([
            "dijabetes gestacijski dijabetes preporuke liječenje",
            "glukoza šećer u krvi kontrola",
            "gestacijski dijabetes upute"
        ])
        if glucose > 7.8:
            query_parts.append("povišena glukoza hitna intervencija")
        if gdm == 1:
            query_parts.append("gestacijski dijabetes ishrana inzulin")
    
    # Krvni pritisak (srednja težina)
    systolic = patient_data.get('sistolicki_krvni_tlak', 0)
    diastolic = patient_data.get('dijastolicki_krvni_tlak', 0)
    
    if systolic >= 140 or diastolic >= 90:
        query_parts.extend([
            "hipertenzija preeklampsija liječenje",
            "visok krvni pritisak trudnoća",
            "antihipertenzivna terapija"
        ])
    
    # BMI i gojaznost (srednja težina)
    bmi = patient_data.get('BMI', 0)
    if bmi >= 30:
        query_parts.extend([
            "gojaznost trudnoća komplikacije",
            "BMI visok rizik preporuke"
        ])
    elif bmi >= 25:
        query_parts.append("prekomjerna težina ishrana")
    
    # Ostali parametri
    if patient_data.get('mentalno_zdravlje', 0) == 1:
        query_parts.append("mentalno zdravlje depresija anksioznost podrška")
    
    if patient_data.get('komplikacije_u_proslosti', 0) == 1:
        query_parts.append("komplikacije prethodne trudnoće praćenje")
    
    if context:
        query_parts.insert(0, context)
    
    if not query_parts:
        query_parts = ["prenatalna njega zdrava trudnoća preporuke"]
    
    # Poveži sa više termina za bolju pretragu
    query = " ".join(query_parts)
    return query


def test_rag_system(pdf_path: str = None):
    """Testira RAG sistem."""
    print("\n" + "="*50)
    print("TESTIRANJE RAG SISTEMA (poboljšana verzija)")
    print("="*50)
    
    if pdf_path and os.path.exists(pdf_path):
        print(f"\n1. Izgradnja vektorske baze iz: {pdf_path}")
        build_vector_store_from_pdf(pdf_path, force_rebuild=True)
    else:
        print("\n1. Korištenje postojeće vektorske baze")
        collection = get_collection()
        print(f"   Broj fragmenata: {collection.count()}")
    
    print("\n2. Test semantičke pretrage:")
    test_queries = [
        "dijabetes u trudnoći liječenje",
        "visok krvni pritisak preeklampsija",
        "gojaznost BMI preporuke"
    ]
    
    for query in test_queries:
        print(f"\n   Upit: '{query}'")
        results = semantic_search(query, n_results=3)
        for r in results:
            print(f"   - Relevantnost: {r['relevance_score']:.2%}")
            print(f"     {r['text'][:150]}...")


if __name__ == "__main__":
    pdf_file = "documents/Klinicki_vodic_za_antenatalnu_zastitu.pdf"
    test_rag_system(pdf_file)