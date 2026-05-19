"""
setup.py
Jednokratna inicijalizacija projekta — pokrenuti nakon kloniranja repozitorija.

Redoslijed koraka:
  1. Provjera Python verzije
  2. Provjera instaliranih biblioteka
  3. Provjera .env fajla
  4. Provjera PDF dokumenta
  5. Treniranje modela (ako model ne postoji)
  6. Izgradnja vektorske baze (ako baza ne postoji ili je prazna)
"""

import os
import sys

# Apsolutna putanja do backend/ foldera — radi bez obzira odakle se pokreće
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_PATH      = os.path.join(BASE_DIR, "documents", "Klinicki_vodic_za_antenatalnu_zastitu.pdf")
CHROMA_DIR    = os.path.join(BASE_DIR, "chroma_db")
DATASET_PATH  = os.path.join(BASE_DIR, "data", "dataset.csv")
MODEL_PATH    = os.path.join(BASE_DIR, "models", "rf_model.pkl")
ENCODER_PATH  = os.path.join(BASE_DIR, "models", "label_encoder_rf.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "models", "feature_cols_rf.pkl")


# ─────────────────────────────────────────────────────────────────────────────
# 1. PROVJERA PYTHON VERZIJE
# ─────────────────────────────────────────────────────────────────────────────

def check_python_version():
    major, minor = sys.version_info[:2]
    print(f"  Python verzija: {major}.{minor}")
    if major < 3 or (major == 3 and minor < 9):
        print("  GREŠKA: Potreban Python 3.9 ili noviji.")
        sys.exit(1)
    print("  Python verzija: OK")


# ─────────────────────────────────────────────────────────────────────────────
# 2. PROVJERA BIBLIOTEKA
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_PACKAGES = [
    ("flask",                 "Flask"),
    ("flask_cors",            "flask-cors"),
    ("sklearn",               "scikit-learn"),
    ("pandas",                "pandas"),
    ("numpy",                 "numpy"),
    ("joblib",                "joblib"),
    ("chromadb",              "chromadb"),
    ("sentence_transformers", "sentence-transformers"),
    ("PyPDF2",                "PyPDF2"),
    ("dotenv",                "python-dotenv"),
]

def check_packages():
    missing = []
    for import_name, pip_name in REQUIRED_PACKAGES:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"\n  GREŠKA: Nedostaju biblioteke: {', '.join(missing)}")
        print("  Pokreni: pip install -r requirements.txt")
        sys.exit(1)

    print("  Sve biblioteke: OK")


# ─────────────────────────────────────────────────────────────────────────────
# 3. PROVJERA .env FAJLA
# ─────────────────────────────────────────────────────────────────────────────

def check_env_file():
    env_path         = os.path.join(BASE_DIR, ".env")
    env_example_path = os.path.join(BASE_DIR, ".env.example")

    if not os.path.exists(env_path):
        print("\n  Kreiranje .env fajla iz predloška...")
        if os.path.exists(env_example_path):
            import shutil
            shutil.copy(env_example_path, env_path)
            print("  .env kreiran iz .env.example — popuni vrijednosti po potrebi.")
        else:
            with open(env_path, "w") as f:
                f.write("# Hugging Face token (opcionalno, za privatne modele)\n")
                f.write("HF_TOKEN=\n")
            print("  .env kreiran s praznim vrijednostima.")
    else:
        print("  .env fajl: OK")


# ─────────────────────────────────────────────────────────────────────────────
# 4. PROVJERA PDF DOKUMENTA
# ─────────────────────────────────────────────────────────────────────────────

def check_pdf():
    if not os.path.exists(PDF_PATH):
        print(f"\n  UPOZORENJE: PDF nije pronađen na putanji: {PDF_PATH}")
        print("  Opcije:")
        print("    a) Stavi PDF u 'backend/documents/' folder i preimenuji ga u:")
        print("       'Klinicki_vodic_za_antenatalnu_zastitu.pdf'")
        print("    b) Pokreni setup s flagom --demo za testni PDF")

        if "--demo" in sys.argv:
            _create_demo_pdf()
            return True

        odgovor = input("\n  Kreirati demo PDF za testiranje? (y/n): ").strip().lower()
        if odgovor == 'y':
            _create_demo_pdf()
            return True
        else:
            print("  Bez PDF-a RAG sistem neće raditi.")
            return False
    else:
        size_kb = os.path.getsize(PDF_PATH) // 1024
        print(f"  PDF dokument: OK ({size_kb} KB)")
        return True


def _create_demo_pdf():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        print("  ReportLab nije instaliran. Pokreni: pip install reportlab")
        return

    os.makedirs(os.path.join(BASE_DIR, "documents"), exist_ok=True)
    c = canvas.Canvas(PDF_PATH, pagesize=letter)
    width, height = letter
    y = height - 50

    sadrzaj = [
        "KLINIČKI VODIČ ZA ANTENATALNU ZAŠTITU (DEMO VERZIJA)",
        "",
        "=== DIJABETES U TRUDNOĆI ===",
        "Gestacijski dijabetes (GDM) je poremećaj tolerancije glukoze.",
        "Ciljne vrijednosti: natašte <5.3 mmol/L, 1h nakon obroka <7.8 mmol/L.",
        "Liječenje: dijeta 40-45% ugljikohidrata, fizička aktivnost 30 min dnevno.",
        "",
        "=== HIPERTENZIJA U TRUDNOĆI ===",
        "Hipertenzija: krvni pritisak ≥140/90 mmHg.",
        "Liječenje: labetalol, nifedipin ili metildopa.",
        "",
        "=== GOJAZNOST ===",
        "Gojaznost (BMI >30) povećava rizik od preeklampsije i GDM.",
        "Preporučeno povećanje tjelesne mase: 5-9 kg tokom trudnoće.",
    ]

    for linija in sadrzaj:
        c.drawString(50, y, linija)
        y -= 18
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    print(f"  Demo PDF kreiran: {PDF_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. TRENIRANJE MODELA
# ─────────────────────────────────────────────────────────────────────────────

def check_and_train_model():
    if all(os.path.exists(p) for p in [MODEL_PATH, ENCODER_PATH, FEATURES_PATH]):
        print("  ML model: OK (već postoji)")
        return

    print("\n  ML model nije pronađen — pokrećem trening...")

    if not os.path.exists(DATASET_PATH):
        print(f"  GREŠKA: Dataset nije pronađen: {DATASET_PATH}")
        print("  Dodaj 'backend/data/dataset.csv' u projekt i ponovi setup.")
        sys.exit(1)

    try:
        sys.path.insert(0, BASE_DIR)
        from model_train_rf import train_model
        train_model()
        print("  ML model: istreniran i sačuvan.")
    except Exception as e:
        print(f"  GREŠKA pri treniranju modela: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 6. IZGRADNJA VEKTORSKE BAZE
# ─────────────────────────────────────────────────────────────────────────────

def _baza_ima_dokumente() -> bool:
    """Provjerava da li vektorska baza stvarno sadrži dokumente."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        cols = client.list_collections()
        return any(
            client.get_collection(c.name).count() > 0
            for c in cols
        )
    except Exception:
        return False


def check_and_build_vector_store(pdf_dostupan: bool):
    # Provjera broja dokumenata — ne samo postojanja foldera
    if _baza_ima_dokumente():
        print("  Vektorska baza: OK (već postoji i popunjena)")
        return

    if not pdf_dostupan:
        print("  Vektorska baza: PRESKOČENA (PDF nije dostupan)")
        return

    print("\n  Vektorska baza nije popunjena — pokrećem izgradnju...")

    try:
        sys.path.insert(0, BASE_DIR)
        from rag_chroma import build_vector_store_from_pdf
        build_vector_store_from_pdf(PDF_PATH, force_rebuild=True)
        print("  Vektorska baza: izgrađena.")
    except Exception as e:
        print(f"  GREŠKA pri izgradnji vektorske baze: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  INICIJALIZACIJA PROJEKTA")
    print("="*60)

    print("\n[1/6] Provjera Python verzije...")
    check_python_version()

    print("\n[2/6] Provjera biblioteka...")
    check_packages()

    print("\n[3/6] Provjera .env fajla...")
    check_env_file()

    print("\n[4/6] Provjera PDF dokumenta...")
    pdf_ok = check_pdf()

    print("\n[5/6] Provjera ML modela...")
    check_and_train_model()

    print("\n[6/6] Provjera vektorske baze...")
    check_and_build_vector_store(pdf_ok)

    print("\n" + "="*60)
    if pdf_ok:
        print("  SETUP ZAVRŠEN — projekat je spreman za pokretanje.")
    else:
        print("  SETUP ZAVRŠEN (bez RAG-a) — dodaj PDF pa ponovi setup.")
    print("="*60)
    print("\n  Pokreni API sa: python app.py\n")


if __name__ == "__main__":
    main()