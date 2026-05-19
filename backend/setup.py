"""
setup.py
Jednokratna inicijalizacija projekta — pokrenuti nakon kloniranja repozitorija.

Redoslijed koraka:
  1. Provjera Python verzije
  2. Provjera instaliranih biblioteka
  3. Provjera .env fajla
  4. Provjera PDF dokumenta
  5. Treniranje modela (ako model ne postoji)
  6. Izgradnja vektorske baze (ako baza ne postoji)
"""

import os
import sys


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
    ("flask",                "Flask"),
    ("flask_cors",           "flask-cors"),
    ("sklearn",              "scikit-learn"),
    ("pandas",               "pandas"),
    ("numpy",                "numpy"),
    ("joblib",               "joblib"),
    ("chromadb",             "chromadb"),
    ("sentence_transformers","sentence-transformers"),
    ("PyPDF2",               "PyPDF2"),
    ("dotenv",               "python-dotenv"),
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
    if not os.path.exists(".env"):
        print("\n  Kreiranje .env fajla iz predloška...")
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("  .env kreiran iz .env.example — popuni vrijednosti po potrebi.")
        else:
            # Kreiraj minimalni .env
            with open(".env", "w") as f:
                f.write("# Hugging Face token (opcionalno, za privatne modele)\n")
                f.write("HF_TOKEN=\n")
            print("  .env kreiran s praznim vrijednostima.")
    else:
        print("  .env fajl: OK")


# ─────────────────────────────────────────────────────────────────────────────
# 4. PROVJERA PDF DOKUMENTA
# ─────────────────────────────────────────────────────────────────────────────

PDF_PATH = "documents/Klinicki_vodic_za_antenatalnu_zastitu.pdf"

def check_pdf():
    if not os.path.exists(PDF_PATH):
        print(f"\n  UPOZORENJE: PDF nije pronađen na putanji: {PDF_PATH}")
        print("  Opcije:")
        print("    a) Stavi PDF u 'documents/' folder i preimenuji ga u:")
        print(f"       'Klinicki_vodic_za_antenatalnu_zastitu.pdf'")
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
            print("  Ostatak setup-a će biti preskočen.")
            return False
    else:
        size_kb = os.path.getsize(PDF_PATH) // 1024
        print(f"  PDF dokument: OK ({size_kb} KB)")
        return True


def _create_demo_pdf():
    """Kreira demo PDF s osnovnim medicinskim sadržajem za testiranje."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        print("  ReportLab nije instaliran. Pokreni: pip install reportlab")
        return

    os.makedirs("documents", exist_ok=True)
    demo_path = "documents/Klinicki_vodic_za_antenatalnu_zastitu.pdf"

    c = canvas.Canvas(demo_path, pagesize=letter)
    width, height = letter
    y = height - 50

    sadrzaj = [
        "KLINIČKI VODIČ ZA ANTENATALNU ZAŠTITU (DEMO VERZIJA)",
        "",
        "=== DIJABETES U TRUDNOĆI ===",
        "Gestacijski dijabetes (GDM) je poremećaj tolerancije glukoze koji se",
        "prvi put dijagnostikuje tokom trudnoće. Ciljne vrijednosti glukoze:",
        "natašte <5.3 mmol/L, jedan sat nakon obroka <7.8 mmol/L.",
        "Liječenje uključuje dijetu s 40-45% ugljikohidrata, redovnu fizičku",
        "aktivnost od 30 minuta dnevno i monitoring glukoze četiri puta dnevno.",
        "Ako se ciljne vrijednosti ne postižu dijetom, uvodi se insulin ili metformin.",
        "",
        "=== HIPERTENZIJA U TRUDNOĆI ===",
        "Hipertenzija u trudnoći definiše se kao krvni pritisak ≥140/90 mmHg.",
        "Preeklampsija nastaje nakon 20. sedmice i karakteriše se visokim",
        "krvnim pritiskom s oštećenjem organa, najčešće jetre i bubrega.",
        "Liječenje uključuje labetalol, nifedipin ili metildopu, a magnezijum",
        "sulfat se primjenjuje za prevenciju eklampsije.",
        "",
        "=== GOJAZNOST I TJELESNA MASA ===",
        "Gojaznost (BMI >30) u trudnoći povećava rizik od preeklampsije",
        "tri do četiri puta i rizik od gestacijskog dijabetesa dva do tri puta.",
        "Preporučeno povećanje tjelesne mase tokom trudnoće iznosi 5-9 kg.",
        "Suplementacija uključuje folnu kiselinu 5 mg dnevno u prvom trimestru",
        "i vitamin D od 400 do 1000 IU dnevno tokom cijele trudnoće.",
        "",
        "=== MENTALNO ZDRAVLJE ===",
        "Depresija i anksioznost tokom trudnoće javljaju se u 10-20% trudnica.",
        "Preporučuje se psihološka podrška, grupni programi i savjetovanje.",
        "Farmakoterapija se razmatra samo kada su benefiti veći od rizika.",
        "",
        "=== OPŠTE PREPORUKE ===",
        "Redovni prenatalni pregledi obavljaju se 10-14 puta tokom trudnoće.",
        "Preporučuje se zdrava ishrana bogata voćem, povrćem i cjelovitim žitaricama,",
        "umjerena fizička aktivnost od 30 minuta dnevno, te izbjegavanje alkohola,",
        "cigareta i lijekova bez preporuke ljekara.",
    ]

    for linija in sadrzaj:
        c.drawString(50, y, linija)
        y -= 18
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    print(f"  Demo PDF kreiran: {demo_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. TRENIRANJE MODELA
# ─────────────────────────────────────────────────────────────────────────────

def check_and_train_model():
    model_path    = "models/rf_model.pkl"
    encoder_path  = "models/label_encoder_rf.pkl"
    features_path = "models/feature_cols_rf.pkl"
    dataset_path  = "data/dataset.csv"

    if all(os.path.exists(p) for p in [model_path, encoder_path, features_path]):
        print("  ML model: OK (već postoji)")
        return

    print("\n  ML model nije pronađen — pokrećem trening...")

    if not os.path.exists(dataset_path):
        print(f"  GREŠKA: Dataset nije pronađen na putanji: {dataset_path}")
        print("  Dodaj 'data/dataset.csv' u projekt i ponovi setup.")
        sys.exit(1)

    try:
        from model_train_rf import train_model
        train_model()
        print("  ML model: istreniran i sačuvan.")
    except Exception as e:
        print(f"  GREŠKA pri treniranju modela: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 6. IZGRADNJA VEKTORSKE BAZE
# ─────────────────────────────────────────────────────────────────────────────

def check_and_build_vector_store(pdf_dostupan: bool):
    chroma_dir = "chroma_db"

    # Baza postoji ako folder postoji i nije prazan
    baza_postoji = (
        os.path.exists(chroma_dir) and
        any(os.scandir(chroma_dir))
    )

    if baza_postoji:
        print("  Vektorska baza: OK (već postoji)")
        return

    if not pdf_dostupan:
        print("  Vektorska baza: PRESKOČENA (PDF nije dostupan)")
        return

    print("\n  Vektorska baza nije pronađena — pokrećem izgradnju...")

    try:
        from rag_chroma import build_vector_store_from_pdf
        build_vector_store_from_pdf(PDF_PATH, force_rebuild=False)
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