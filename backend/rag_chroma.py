import os
import re
import hashlib
from typing import List, Dict, Any, Tuple

import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

hf_token = os.getenv("HF_TOKEN")

# Globalni objekti - global objects for lazy loading
_chroma_client = None
_collection = None
_embedding_model = None

# Konfiguracija - configuration constants
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
COLLECTION_NAME = "pregnancy_advice_bhs"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

DEFAULT_N_RESULTS = 10
MIN_RELEVANCE_THRESHOLD = 0.45

GUIDE_INFO = {
    'title': 'Klinički vodič za antenatalnu zaštitu',
    'year': '2021',
    'publisher': 'Ministarstvo zdravlja',
    'version': '3.0'
}

# ─────────────────────────────────────────────────────────────────────────────
# KLINIČKI PRAGOVI (referentne vrijednosti za interpretaciju parametara) - clinical thresholds for interpreting patient parameters
# ─────────────────────────────────────────────────────────────────────────────

CLINICAL_THRESHOLDS = {
    'glukoza': {
        'normalna':    (3.9, 5.5),
        'blago povisena':    (5.5, 7.8),
        'visoka':      (7.8, 11.0),
        'kriticna':    (11.0, float('inf'))
    },
    'sistolicki': {
        'optimalan':           (0,   120),
        'normalan':            (120, 130),
        'normalno_visok':      (130, 140),
        'hipertenzija_1':      (140, 160),
        'hipertenzija_2':      (160, 180),
        'hipertenzija_3':      (180, float('inf'))
    },
    'dijastolicki': {
        'optimalan':           (0,   80),
        'normalan':            (80,  85),
        'normalno_visok':      (85,  90),
        'hipertenzija_1':      (90,  100),
        'hipertenzija_2':      (100, 110),
        'hipertenzija_3':      (110, float('inf'))
    },
    'bmi': {
        'normalan':    (18.5, 25.0),
        'prekomjeran': (25.0, 30.0),
        'gojaznost_1': (30.0, 35.0),
        'gojaznost_2': (35.0, 40.0),
        'gojaznost_3': (40.0, float('inf'))
    },
    'temp': {
        'normalna':    (36.0, 37.5),
        'subfebrilan': (37.5, 38.0),
        'febrilna':    (38.0, float('inf'))
    },
    'otkucaji': {
        'bradikardija': (0,   60),
        'normalan':     (60, 100),
        'tahikardija':  (100, float('inf'))
    }
}


def _klasifikuj_parametar(vrijednost: float, parametar: str) -> str:
    """Vraća kliničku klasifikaciju za dati parametar i vrijednost. - Returns clinical classification for a given parameter and value."""
    pragovi = CLINICAL_THRESHOLDS.get(parametar, {})
    for naziv, (min_v, max_v) in pragovi.items():
        if min_v <= vrijednost < max_v:
            return naziv
    return 'nepoznato'


# ─────────────────────────────────────────────────────────────────────────────
# LAZY LOADING MODELA I CHROMA KLIJENTA - lazy loading of embedding model and Chroma client
# ─────────────────────────────────────────────────────────────────────────────

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print(f"Učitavam višejezični embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _chroma_client


def get_collection():
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
    global _collection
    try:
        client = get_chroma_client()
        client.delete_collection(COLLECTION_NAME)
        _collection = None
        print(f"Kolekcija '{COLLECTION_NAME}' uspješno izbrisana.")
    except Exception as e:
        print(f"Kolekcija '{COLLECTION_NAME}' ne postoji: {e}")


def _chroma_embedding_function(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


# ─────────────────────────────────────────────────────────────────────────────
# ČIŠĆENJE I VALIDACIJA TEKSTA - text cleaning and validation
# ─────────────────────────────────────────────────────────────────────────────

# Izrazi koji označavaju referencu na tabelu (koje ne možemo prikazati) - expressions indicating reference to tables (which we cannot display)
_TABLE_PATTERNS = re.compile(
    r'(tabela|tablica|tabla|table|slika|grafikon|prilog|aneks|appendix'
    r'|vidjeti tabelu|prema tabeli|u tabeli|tabeli \d|tabela \d'
    r'|tablica \d|grafikon \d|slika \d)',
    re.IGNORECASE
)

# Rečenice koje počinju malim slovom (ostatak prethodne rečenice) ili su prekratke (često nepotpuni fragmenti) - sentences that start with a lowercase letter (continuation of previous sentence) or are too short (often incomplete fragments)
_MIN_SENTENCE_LENGTH = 40


def _sadrzi_referencu_na_tabelu(tekst: str) -> bool:
    """Vraća True ako tekst sadrži referencu na tabelu/grafikon koji ne možemo prikazati. Returns True if the text contains a reference to a table/figure that we cannot display."""
    return bool(_TABLE_PATTERNS.search(tekst))


def _pocinje_cjelovitom_recenicom(tekst: str) -> bool:
    """
    Provjera da li chunk počinje cjelovitom rečenicom.
    Chunk je validan ako počinje velikim slovom, brojem, ili poznatim uvodom. - A chunk is valid if it starts with a capital letter, a number, or a known introduction.
    """
    tekst = tekst.strip()
    if not tekst:
        return False
    # Prihvati ako počinje velikim slovom, brojem ili crticom (lista) - Accept if it starts with a capital letter, a number, or a dash (list)
    return bool(re.match(r'^[A-ZŠĐČĆŽ\d\-•–]', tekst))


def _zavrsava_cjelovitom_recenicom(tekst: str) -> bool:
    """
    Provjera da li chunk završava cjelovitom rečenicom. - Check if the chunk ends with a complete sentence.
    """
    tekst = tekst.strip()
    if not tekst:
        return False
    return tekst[-1] in '.!?:'


def _popravi_chunk(tekst: str) -> str:
    """
    Pokušava popraviti chunk:
    - Uklanja nepotpun početak (do prve tačke ako počinje malim slovom)
    - Uklanja nepotpun kraj (poslije zadnje tačke ako ne završava tačkom)
    - Uklanja rečenice koje referenciraju tabele 
        
    - Returns the cleaned chunk or an empty string if it cannot be fixed.

    """
    tekst = tekst.strip()

    # 1. Popravi početak: ako počinje malim slovom, presječi do prve tačke - If it starts with a lowercase letter, cut to the first period
    if tekst and tekst[0].islower():
        match = re.search(r'[.!?]\s+[A-ZŠĐČĆŽ]', tekst)
        if match:
            tekst = tekst[match.start() + 2:].strip()
        else:
            return ""  
        
    # 2. Ukloni rečenice koje spominju tabele, ali zadrži ostatak - Remove sentences that mention tables, but keep the rest
    recenice = re.split(r'(?<=[.!?])\s+', tekst)
    filtrirane = []
    for r in recenice:
        if not _sadrzi_referencu_na_tabelu(r):
            filtrirane.append(r)

    if not filtrirane:
        return ""

    tekst = ' '.join(filtrirane).strip()

    # 3. Popravi kraj: skrati do zadnje kompletne rečenice - If it doesn't end with a period, cut to the last complete sentence
    if tekst and tekst[-1] not in '.!?:':
        zadnja_tacka = max(
            tekst.rfind('.'),
            tekst.rfind('!'),
            tekst.rfind('?')
        )
        if zadnja_tacka > len(tekst) * 0.5:  # Zadrži samo ako smo zadržali >50% teksta - Only keep if we retained >50% of the text
            tekst = tekst[:zadnja_tacka + 1].strip()
        else:
            return ""

    return tekst


def _validiraj_i_popravi_chunk(tekst: str) -> str:
    """
    Glavni validator chunka. Vraća očišćen tekst ili prazan string ako chunk nije upotrebljiv.
    """
    if not tekst or len(tekst) < _MIN_SENTENCE_LENGTH:
        return ""

    # Ako cijeli chunk govori samo o tabeli, odbaci ga - If the entire chunk is just about a table, discard it
    if _sadrzi_referencu_na_tabelu(tekst):
        ociscen = _popravi_chunk(tekst)
        if len(ociscen) < _MIN_SENTENCE_LENGTH:
            return ""
        return ociscen

    # Pokušaj popraviti nepotpune rubove - Try to fix incomplete edges
    if not _pocinje_cjelovitom_recenicom(tekst) or not _zavrsava_cjelovitom_recenicom(tekst):
        ociscen = _popravi_chunk(tekst)
        if len(ociscen) < _MIN_SENTENCE_LENGTH:
            return ""
        return ociscen

    return tekst.strip()


# ─────────────────────────────────────────────────────────────────────────────
# CHUNKING PDF-A - chunking the PDF
# ─────────────────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """
    Dijeli tekst na fragmente koji završavaju na granicama rečenica.
    Veći chunk_size od originala smanjuje broj prekinutih rečenica.

    Splits the text into chunks that end at sentence boundaries. 
    A larger chunk_size than the original reduces the number of broken sentences.
    """
    if not text or len(text) < chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            # Pokušaj završiti na granici rečenice - Try to end at a sentence boundary
            for sep in ['. ', '? ', '! ', '\n\n', '\n', '; ']:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start + chunk_size // 2:  # Zadrži barem pola chunk-a - Only keep if we retain at least half of the chunk
                    end = last_sep + len(sep)
                    break

        chunk = text[start:end].strip()

        # Validiraj i popravi chunk prije dodavanja - Validate and fix the chunk before adding
        chunk_ociscen = _validiraj_i_popravi_chunk(chunk)
        if chunk_ociscen:
            chunks.append(chunk_ociscen)

        start = max(start + 1, end - overlap)

    return chunks


def load_pdf_to_chunks(pdf_path: str) -> List[Dict[str, Any]]:
    """Učitava PDF i dijeli ga na čiste, cjelovite fragmente. - Loads a PDF and splits it into clean, complete chunks."""
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

    print(f"Kreirano {len(chunks)} valjanih fragmenata iz PDF-a")

    documents = []
    for i, chunk in enumerate(chunks):
        documents.append({
            'text': chunk,
            'metadata': {
                'source': os.path.basename(pdf_path),
                'chunk_id': i,
            }
        })

    return documents


def build_vector_store_from_pdf(pdf_path: str, force_rebuild: bool = False):
    """Gradi vektorsku bazu iz PDF dokumenta. - Builds a vector store from a PDF document."""
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

    ids, texts, metadatas = [], [], []

    for i, doc in enumerate(documents):
        unique_id = hashlib.md5(f"{doc['text'][:100]}_{i}".encode()).hexdigest()[:16]
        ids.append(unique_id)
        texts.append(doc['text'])
        metadatas.append(doc['metadata'])

    for idx in range(0, len(ids), 100):
        batch_ids       = ids[idx:idx+100]
        batch_texts     = texts[idx:idx+100]
        batch_metadatas = metadatas[idx:idx+100]
        embeddings      = _chroma_embedding_function(batch_texts)

        collection.add(
            ids=batch_ids,
            documents=batch_texts,
            metadatas=batch_metadatas,
            embeddings=embeddings
        )
        print(f"  Dodano {len(batch_ids)} fragmenata u vektorsku bazu...")

    print(f"\nUspješno indeksirano {len(documents)} fragmenata.")


# ─────────────────────────────────────────────────────────────────────────────
# SEMANTIČKA PRETRAGA - semantic search
# ─────────────────────────────────────────────────────────────────────────────

def semantic_search(query: str, n_results: int = DEFAULT_N_RESULTS) -> List[Dict[str, Any]]:
    """
    Semantička pretraga sa filtriranjem po relevantnosti i kvalitetu teksta. - Semantic search with relevance and text quality filtering.
    """
    collection = get_collection()

    if collection.count() == 0:
        print("Upozorenje: Vektorska baza je prazna.")
        return []

    model = get_embedding_model()
    query_embedding = model.encode([query])[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    formatted_results = []
    if results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            distance         = results['distances'][0][i] if results['distances'] else None
            metadata         = results['metadatas'][0][i] if results['metadatas'] else {}
            relevance_score  = 1 - distance if distance is not None else 0

            if relevance_score < MIN_RELEVANCE_THRESHOLD:
                continue

            # Finalna validacija teksta (odbaci ako sadrži samo tablične reference) - Final text validation (discard if it contains only table references)
            doc_ociscen = _validiraj_i_popravi_chunk(doc)
            if not doc_ociscen:
                continue

            formatted_results.append({
                'text':            doc_ociscen,
                'metadata':        metadata,
                'distance':        distance,
                'relevance_score': relevance_score
            })

    return formatted_results


# ─────────────────────────────────────────────────────────────────────────────
# PERSONALIZOVANI UPITI NA OSNOVU PARAMETARA PACIJENTICE - personalized queries based on patient parameters
# ─────────────────────────────────────────────────────────────────────────────


def _bp_klasa_opis(klasa_s: str, klasa_d: str) -> str:
    """Vraća čitljiv opis kategorije krvnog tlaka na osnovu ESH/ESC klasifikacije."""
    # Uzmi goru od dvije klase (ako su različite, uzmi onu koja je "lošija") - Take the worse of the two classes (if different, take the one that is "worse")
    redoslijed = ['optimalan', 'normalan', 'normalno_visok',
                  'hipertenzija_1', 'hipertenzija_2', 'hipertenzija_3']
    idx_s = redoslijed.index(klasa_s) if klasa_s in redoslijed else 0
    idx_d = redoslijed.index(klasa_d) if klasa_d in redoslijed else 0
    klasa = redoslijed[max(idx_s, idx_d)]
    opisi = {
        'optimalan':      'optimalan',
        'normalan':       'normalan',
        'normalno_visok': 'normalno visok',
        'hipertenzija_1': 'blaga hipertenzija',
        'hipertenzija_2': 'umjerena hipertenzija',
        'hipertenzija_3': 'teška hipertenzija'
    }
    return opisi.get(klasa, klasa.replace('_', ' '))

def _analiziraj_parametre(patient_data: dict) -> Dict[str, Any]:
    """
    Analizira parametre pacijentice i vraća strukturiranu interpretaciju
    sa konkretnim vrijednostima i kliničkom klasifikacijom. 

    Analyzes patient parameters and returns a structured interpretation with specific values and clinical classification.
    """
    analiza = {
        'faktori_rizika':    [],   # Konkretni problemi - specific issues
        'normalni_parametri':[],   # Uredni parametri - normal parameters
        'tezina_rizika':     0,    # 0-10 (za rangiranje upita) - 0-10 (for query ranking)
        'detalji':           {}    # Konkretne vrijednosti za prikaz - specific values for display
    }

    # Glukoza u krvi - blood glucose
    glukoza = float(patient_data.get('glukoza_u_krvi', 0))
    if glukoza > 0:
        klasa = _klasifikuj_parametar(glukoza, 'glukoza')
        analiza['detalji']['glukoza'] = {'vrijednost': glukoza, 'klasa': klasa}
        if klasa == 'kriticna':
            analiza['faktori_rizika'].append(('glukoza_kriticna', glukoza, 4))
        elif klasa == 'visoka':
            analiza['faktori_rizika'].append(('glukoza_visoka', glukoza, 3))
        elif klasa == 'povisena':
            analiza['faktori_rizika'].append(('glukoza_povisena', glukoza, 2))
        else:
            analiza['normalni_parametri'].append('glukoza')

    # Dijabetes i gestacijski dijabetes - diabetes and gestational diabetes
    if patient_data.get('dijabetes', 0) == 1:
        analiza['faktori_rizika'].append(('dijabetes_tip1_2', None, 3))
    if patient_data.get('gestacijski_dijabetes', 0) == 1:
        analiza['faktori_rizika'].append(('gestacijski_dijabetes', None, 3))
 
    # Krvni tlak - blood pressure
    sistolicki  = float(patient_data.get('sistolicki_krvni_tlak', 0))
    dijastolicki = float(patient_data.get('dijastolicki_krvni_tlak', 0))
    if sistolicki > 0 and dijastolicki > 0:
        klasa_s = _klasifikuj_parametar(sistolicki, 'sistolicki')
        klasa_d = _klasifikuj_parametar(dijastolicki, 'dijastolicki')
        analiza['detalji']['krvni_tlak'] = {
            'sistolicki': sistolicki, 'dijastolicki': dijastolicki,
            'klasa_s': klasa_s, 'klasa_d': klasa_d
        }
        if klasa_s == 'hipertenzija_3' or klasa_d == 'hipertenzija_3':
            analiza['faktori_rizika'].append(('hipertenzija_3', (sistolicki, dijastolicki), 5))
        elif klasa_s == 'hipertenzija_2' or klasa_d == 'hipertenzija_2':
            analiza['faktori_rizika'].append(('hipertenzija_2', (sistolicki, dijastolicki), 4))
        elif klasa_s == 'hipertenzija_1' or klasa_d == 'hipertenzija_1':
            analiza['faktori_rizika'].append(('hipertenzija_1', (sistolicki, dijastolicki), 3))
        elif klasa_s == 'normalno_visok' or klasa_d == 'normalno_visok':
            analiza['faktori_rizika'].append(('normalno_visok_tlak', (sistolicki, dijastolicki), 1))
        else:
            analiza['normalni_parametri'].append('krvni_tlak')

    # BMI - body mass index
    bmi = float(patient_data.get('BMI', 0))
    if bmi > 0:
        klasa = _klasifikuj_parametar(bmi, 'bmi')
        analiza['detalji']['bmi'] = {'vrijednost': bmi, 'klasa': klasa}
        if klasa in ('gojaznost_2', 'gojaznost_3'):
            analiza['faktori_rizika'].append(('gojaznost_teska', bmi, 3))
        elif klasa == 'gojaznost_1':
            analiza['faktori_rizika'].append(('gojaznost', bmi, 2))
        elif klasa == 'prekomjeran':
            analiza['faktori_rizika'].append(('prekomjerna_tezina', bmi, 1))
        else:
            analiza['normalni_parametri'].append('bmi')

    # Tjelesna temperatura - body temperature
    temp = float(patient_data.get('tjelesna_temp', 0))
    if temp > 0:
        klasa = _klasifikuj_parametar(temp, 'temp')
        analiza['detalji']['temp'] = {'vrijednost': temp, 'klasa': klasa}
        if klasa == 'febrilna':
            analiza['faktori_rizika'].append(('febrilno_stanje', temp, 3))
        elif klasa == 'subfebrilan':
            analiza['faktori_rizika'].append(('subfebrilan', temp, 1))

    # Otkucaji srca - heart rate
    otkucaji = float(patient_data.get('otkucaji_srca', 0))
    if otkucaji > 0:
        klasa = _klasifikuj_parametar(otkucaji, 'otkucaji')
        analiza['detalji']['otkucaji'] = {'vrijednost': otkucaji, 'klasa': klasa}
        if klasa == 'tahikardija':
            analiza['faktori_rizika'].append(('tahikardija', otkucaji, 2))
        elif klasa == 'bradikardija':
            analiza['faktori_rizika'].append(('bradikardija', otkucaji, 1))

    # Mentalno zdravlje i komplikacije u prošlosti - mental health and past complications
    if patient_data.get('mentalno_zdravlje', 0) == 1:
        analiza['faktori_rizika'].append(('mentalno_zdravlje', None, 2))
    if patient_data.get('komplikacije_u_proslosti', 0) == 1:
        analiza['faktori_rizika'].append(('komplikacije_proslost', None, 2))

    # Ukupna težina rizika (suma bodova) - Total risk weight (sum of points)
    analiza['tezina_rizika'] = sum(r[2] for r in analiza['faktori_rizika'])

    return analiza


def build_semantic_query_bhs(patient_data: dict, context: str = "") -> str:
    """
    Gradi personalizovani semantički upit na osnovu konkretnih vrijednosti
    parametara pacijentice i njihove kliničke interpretacije.

    Builds a personalized semantic query based on the specific values of patient parameters and their clinical interpretation.
    """
    analiza = _analiziraj_parametre(patient_data)
    query_parts = []

    if context:
        query_parts.append(context)

    for faktor, vrijednost, _ in analiza['faktori_rizika']:

        if faktor == 'glukoza_kriticna':
            query_parts += [
                f"kritično povišena glukoza u krvi {vrijednost:.1f} mmol/L trudnoća hitna intervencija",
                "hiperglikemija liječenje inzulin trudnoća",
                "visoka glukoza komplikacije prevencija"
            ]
        elif faktor == 'glukoza_visoka':
            query_parts += [
                f"povišena glukoza {vrijednost:.1f} mmol/L gestacijski dijabetes",
                "kontrola šećera u krvi preporuke trudnoća",
                "dijeta glukoza trudnoća ishrana"
            ]
        elif faktor == 'glukoza_povisena':
            query_parts += [
                f"granično povišena glukoza {vrijednost:.1f} mmol/L",
                "prevencija gestacijskog dijabetesa ishrana fizička aktivnost"
            ]

        elif faktor == 'dijabetes_tip1_2':
            query_parts += [
                "dijabetes tip 1 tip 2 trudnoća liječenje kontrola",
                "insulin dijabetes trudnoća preporuke",
                "komplikacije dijabetesa trudnoća praćenje"
            ]
        elif faktor == 'gestacijski_dijabetes':
            query_parts += [
                "gestacijski dijabetes dijeta terapija insulin",
                "GDM liječenje preporuke monitoring glukoze",
                "gestacijski dijabetes ishrana fizička aktivnost"
            ]

        elif faktor == 'hipertenzija_3':
            s, d = vrijednost
            query_parts += [
                f"teška hipertenzija trudnoća {s:.0f}/{d:.0f} mmHg hitna intervencija",
                "hipertenzija 3 stupnja preeklampsija eklampsija liječenje",
                "antihipertenzivna terapija trudnoća visok rizik"
            ]
        elif faktor == 'hipertenzija_2':
            s, d = vrijednost
            query_parts += [
                f"umjerena hipertenzija trudnoća {s:.0f}/{d:.0f} mmHg liječenje",
                "preeklampsija krvni pritisak terapija antihipertenzivi",
                "hipertenzija trudnoća komplikacije praćenje"
            ]
        elif faktor == 'hipertenzija_1':
            s, d = vrijednost
            query_parts += [
                f"blaga hipertenzija trudnoća {s:.0f}/{d:.0f} mmHg praćenje",
                "hipertenzija 1 stupnja trudnoća preporuke monitoring"
            ]
        elif faktor == 'normalno_visok_tlak':
            s, d = vrijednost
            query_parts += [
                f"normalno visok krvni tlak trudnoća {s:.0f}/{d:.0f} mmHg praćenje",
                "granično povišen tlak trudnoća preporuke"
            ]

        elif faktor == 'gojaznost_teska':
            query_parts += [
                f"teška gojaznost BMI {vrijednost:.1f} trudnoća komplikacije",
                "gojaznost trudnoća visok rizik praćenje liječenje",
                "BMI iznad 35 trudnoća preporuke"
            ]
        elif faktor == 'gojaznost':
            query_parts += [
                f"gojaznost BMI {vrijednost:.1f} trudnoća preporuke",
                "gojaznost trudnoća ishrana fizička aktivnost",
                "komplikacije gojaznosti trudnoća prevencija"
            ]
        elif faktor == 'prekomjerna_tezina':
            query_parts += [
                "prekomjerna težina trudnoća kontrola tjelesne mase",
                "ishrana prekomjerna težina trudnoća preporuke"
            ]

        elif faktor == 'febrilno_stanje':
            query_parts += [
                f"febrilno stanje temperatura {vrijednost:.1f}°C trudnoća liječenje",
                "infekcija temperatura trudnoća intervencija"
            ]
        elif faktor == 'subfebrilan':
            query_parts += [
                "subfebrilan temperatura trudnoća praćenje"
            ]

        elif faktor == 'tahikardija':
            query_parts += [
                f"tahikardija otkucaji srca {vrijednost:.0f} trudnoća",
                "ubrzani rad srca trudnoća uzroci liječenje"
            ]
        elif faktor == 'bradikardija':
            query_parts += [
                f"bradikardija otkucaji srca {vrijednost:.0f} trudnoća praćenje"
            ]

        elif faktor == 'mentalno_zdravlje':
            query_parts += [
                "mentalno zdravlje depresija anksioznost trudnoća podrška",
                "psihološka podrška trudnoća liječenje preporuke"
            ]
        elif faktor == 'komplikacije_proslost':
            query_parts += [
                "komplikacije prethodne trudnoće praćenje prevencija",
                "visokorizična trudnoća prethodni problemi monitoring"
            ]

    # Ako nema faktora rizika – opće preporuke - If no risk factors – general recommendations
    if not analiza['faktori_rizika']:
        dob = patient_data.get('dob', 0)
        if dob > 35:
            query_parts.append(f"trudnoća starosna dob {dob} preporuke praćenje")
        query_parts += [
            "zdrava trudnoća prenatalna njega preporuke",
            "antenatalna zaštita redovni pregledi"
        ]

    return " ".join(query_parts)


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-QUERY PRETRAGA - multi-query search
# ─────────────────────────────────────────────────────────────────────────────

def _multi_query_search(patient_data: dict, n_results_per_query: int = 5) -> List[Dict[str, Any]]:
    """
    Radi više ciljanih pretraga (po jednu za svaki faktor rizika) i
    spaja rezultate, eliminirajući duplikate.
    Ovo osigurava da svaki klinički problem dobije relevantne preporuke.

    Performs multiple targeted searches (one for each risk factor) and merges results, eliminating duplicates.
    """
    analiza    = _analiziraj_parametre(patient_data)
    svi_rezultati: List[Dict[str, Any]] = []
    videni_tekstovi: set = set()

    # Generiši poseban upit za svaki faktor rizika - Generate a separate query for each risk factor
    upiti = []

    for faktor, vrijednost, tezina in sorted(analiza['faktori_rizika'],
                                              key=lambda x: x[2], reverse=True):
        upit = build_semantic_query_bhs(
            {k: v for k, v in patient_data.items()},  # kopija
            context=faktor.replace('_', ' ')
        )
        upiti.append((upit, tezina))

    # Dodaj generalni upit na osnovu ukupne analize (bez specifičnog faktora) - Add a general query based on the overall analysis (without specific factor)
    generalni_upit = build_semantic_query_bhs(patient_data)
    upiti.append((generalni_upit, 1))

    for upit, tezina in upiti:
        rezultati = semantic_search(upit, n_results=n_results_per_query)
        for r in rezultati:
            # Deduplikacija po prvih 80 znakova teksta (da se izbjegne ponavljanje istih preporuka) - Deduplication by the first 80 characters of the text (to avoid repeating the same recommendations)
            kljuc = r['text'][:80]
            if kljuc not in videni_tekstovi:
                videni_tekstovi.add(kljuc)
                # Poveći score rezultata proporcionalno težini faktora - Increase the score of the result proportionally to the weight of the factor
                r['weighted_score'] = r['relevance_score'] * (1 + tezina * 0.1)
                svi_rezultati.append(r)

    # Sortiraj po ponderovanom score-u i vrati - Sort by weighted score and return
    svi_rezultati.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
    return svi_rezultati


# ─────────────────────────────────────────────────────────────────────────────
# FORMATIRANJE PREPORUKA I PERSONALIZOVANI UVOD - formatting recommendations and personalized introduction
# ─────────────────────────────────────────────────────────────────────────────

def get_guide_header(risk_level: str = "Low") -> str:
    """Vraća uvodni tekst o nivou rizika. - Returns an introductory text about the risk level."""
    if "High" in str(risk_level) or "VISOK" in str(risk_level).upper():
        return "VISOK RIZIK – Prioritetne preporuke za kliničku intervenciju\n\n"
    else:
        return "STANDARDNA NJEGA – Preporuke za zdravu trudnoću\n\n"


def _generiši_personalizovani_uvod(patient_data: dict, analiza: dict) -> str:
    """
    Kreira kratki personalizovani uvod koji navodi konkretne vrijednosti
    parametara pacijentice koji su izvan normalnog raspona.

    Creates a short personalized introduction that lists the specific values of patient parameters that are outside the normal range.
    """
    if not analiza['faktori_rizika']:
        return "Na osnovu unesenih parametara, vaša trudnoća je uredna. Nastavite s redovnim pregledima.\n\n"

    linije = ["Na osnovu vaših parametara, uočeni su sljedeći faktori koji zahtijevaju pažnju:\n"]

    detalji = analiza['detalji']

    if 'glukoza' in detalji and detalji['glukoza']['klasa'] != 'normalna':
        g = detalji['glukoza']
        linije.append(f"  • Glukoza u krvi: {g['vrijednost']:.1f} mmol/L "
                      f"({g['klasa'].replace('_', ' ')})")

    if 'krvni_tlak' in detalji:
        kt = detalji['krvni_tlak']
        if kt['klasa_s'] not in ('normalan', 'optimalan') or kt['klasa_d'] not in ('normalan', 'optimalan'):
            linije.append(f"  • Krvni tlak: {kt['sistolicki']:.0f}/{kt['dijastolicki']:.0f} mmHg "
                          f"({_bp_klasa_opis(kt['klasa_s'], kt['klasa_d'])})")

    if 'bmi' in detalji and detalji['bmi']['klasa'] != 'normalan':
        b = detalji['bmi']
        linije.append(f"  • BMI: {b['vrijednost']:.1f} kg/m² "
                      f"({b['klasa'].replace('_', ' ')})")

    if 'temp' in detalji and detalji['temp']['klasa'] != 'normalna':
        t = detalji['temp']
        linije.append(f"  • Tjelesna temperatura: {t['vrijednost']:.1f}°C "
                      f"({t['klasa'].replace('_', ' ')})")

    if 'otkucaji' in detalji and detalji['otkucaji']['klasa'] != 'normalan':
        o = detalji['otkucaji']
        linije.append(f"  • Otkucaji srca: {o['vrijednost']:.0f}/min "
                      f"({o['klasa'].replace('_', ' ')})")

    for faktor, _, _ in analiza['faktori_rizika']:
        if faktor == 'dijabetes_tip1_2':
            linije.append("  • Dijagnoza dijabetesa tip 1 ili tip 2")
        elif faktor == 'gestacijski_dijabetes':
            linije.append("  • Gestacijski dijabetes")
        elif faktor == 'mentalno_zdravlje':
            linije.append("  • Problemi s mentalnim zdravljem")
        elif faktor == 'komplikacije_proslost':
            linije.append("  • Komplikacije u prethodnim trudnoćama")

    return "\n".join(linije) + "\n\nPreporučene smjernice iz kliničkog vodiča:\n\n"


def get_relevant_advice_rag(query_context: str, patient_data: dict, n_results: int = 4) -> str:
    """
    Glavni endpoint za RAG preporuke.
    Koristi multi-query pretragu, personalizovani uvod i čiste cjelovite preporuke.

    Main endpoint for RAG recommendations.
    Uses multi-query search, personalized introduction, and clean complete recommendations.
    """
    analiza = _analiziraj_parametre(patient_data)

    # Multi-query pretraga (ciljana po faktorima rizika) - Multi-query search (targeted by risk factors)
    svi_rezultati = _multi_query_search(patient_data, n_results_per_query=6)

    if not svi_rezultati:
        return ("Trenutno nema specifičnih preporuka za unesene parametre. "
                "Savjetujemo konsultaciju s ljekarom ili odabranim ginekologom.")

    # Uvod na osnovu nivoa rizika i konkretnih parametara - Introduction based on risk level and specific parameters
    risk_level   = query_context
    uvod         = get_guide_header(risk_level)
    personalizov = _generiši_personalizovani_uvod(patient_data, analiza)

    dijelovi = [uvod, personalizov]

    # Dodaj preporuke (bez ponavljanja sličnog sadržaja) - Add recommendations (without repeating similar content)
    dodano = 0
    za_prikaz = svi_rezultati[:n_results * 2]  # Uzmemo više pa filtriramo - Take more and then filter

    for i, rezultat in enumerate(za_prikaz):
        if dodano >= n_results:
            break
        tekst = rezultat['text']
        score = rezultat['relevance_score']

        if len(tekst) < _MIN_SENTENCE_LENGTH:
            continue

        dijelovi.append(f"**Preporuka {dodano + 1}** (relevantnost: {score:.0%}):")
        dijelovi.append(tekst)
        dijelovi.append("")
        dodano += 1

    if dodano == 0:
        dijelovi.append("Nije pronađen dovoljno relevantan sadržaj. "
                        "Obratite se svom ginekologu za detaljne smjernice.")

    return "\n".join(dijelovi)


# ─────────────────────────────────────────────────────────────────────────────
# TESTIRANJE RAG SISTEMA - testing the RAG system
# ─────────────────────────────────────────────────────────────────────────────

def test_rag_system(pdf_path: str = None):
    """Testira poboljšani RAG sistem. - Tests the improved RAG system."""
    print("\n" + "="*60)
    print("TESTIRANJE POBOLJŠANOG RAG SISTEMA")
    print("="*60)

    if pdf_path and os.path.exists(pdf_path):
        print(f"\n1. Izgradnja vektorske baze iz: {pdf_path}")
        build_vector_store_from_pdf(pdf_path, force_rebuild=True)
    else:
        print("\n1. Korištenje postojeće vektorske baze")
        collection = get_collection()
        print(f"   Broj fragmenata: {collection.count()}")

    # Test sa konkretnim parametrima pacijentice - Test with specific patient parameters
    test_slucajevi = [
        {
            'naziv': 'Gestacijski dijabetes + hipertenzija',
            'data': {
                'dob': 32, 'glukoza_u_krvi': 9.2,
                'sistolicki_krvni_tlak': 145, 'dijastolicki_krvni_tlak': 95,
                'BMI': 28.5, 'tjelesna_temp': 36.8, 'otkucaji_srca': 88,
                'dijabetes': 0, 'gestacijski_dijabetes': 1,
                'mentalno_zdravlje': 0, 'komplikacije_u_proslosti': 0
            }
        },
        {
            'naziv': 'Gojaznost + mentalno zdravlje',
            'data': {
                'dob': 28, 'glukoza_u_krvi': 5.1,
                'sistolicki_krvni_tlak': 118, 'dijastolicki_krvni_tlak': 76,
                'BMI': 36.2, 'tjelesna_temp': 36.6, 'otkucaji_srca': 78,
                'dijabetes': 0, 'gestacijski_dijabetes': 0,
                'mentalno_zdravlje': 1, 'komplikacije_u_proslosti': 0
            }
        },
        {
            'naziv': 'Uredna trudnoća',
            'data': {
                'dob': 25, 'glukoza_u_krvi': 4.8,
                'sistolicki_krvni_tlak': 112, 'dijastolicki_krvni_tlak': 72,
                'BMI': 22.4, 'tjelesna_temp': 36.6, 'otkucaji_srca': 74,
                'dijabetes': 0, 'gestacijski_dijabetes': 0,
                'mentalno_zdravlje': 0, 'komplikacije_u_proslosti': 0
            }
        }
    ]

    for slucaj in test_slucajevi:
        print(f"\n{'─'*60}")
        print(f"Test slučaj: {slucaj['naziv']}")
        print(f"{'─'*60}")
        analiza = _analiziraj_parametre(slucaj['data'])
        print(f"Faktori rizika: {[f[0] for f in analiza['faktori_rizika']]}")
        print(f"Težina rizika:  {analiza['tezina_rizika']}")

        upit = build_semantic_query_bhs(slucaj['data'])
        print(f"\nUpit: {upit[:120]}...")

        rezultati = semantic_search(upit, n_results=3)
        print(f"Pronađeno rezultata: {len(rezultati)}")
        for r in rezultati:
            print(f"  [{r['relevance_score']:.2%}] {r['text'][:100]}...")


if __name__ == "__main__":
    pdf_file = "documents/Klinicki_vodic_za_antenatalnu_zastitu.pdf"
    test_rag_system(pdf_file)
    print(f"Token je uspješno učitan!")