# 🤰 Gestatix – Asistent za procjenu rizika u trudnoći

## 📌 Šta je Gestatix?

**Gestatix** je inteligentni klinički asistent dizajniran za predviđanje komplikacija u trudnoći i pružanje smjernica zasnovanih na medicinskim protokolima.  
Kombinujući **mašinsko učenje (Random Forest)** i **semantičku pretragu (RAG)** nad kliničkim vodičem, Gestatix pomaže trudnicama i medicinskom osoblju da procijene rizik i dobiju personalizovane preporuke.

---

## 📋 Preduslovi

Prije nego što počnete, provjerite da li imate instalirano sljedeće:

- **Python 3.9 ili noviji** (preporučeno 3.11 ili 3.12)
- **Internet konekcija** (za preuzimanje biblioteka i ML modela)
- **Git** (za kloniranje repozitorija)
- **Opcionalno** *Microsoft C++ Build Tools* (samo Windows) - potrebno za instalaciju `chromadb` **ukoliko budete imali problema sa pokretanjem*

---

## 🔧 Instalacija Pythona (ako ga nemate)

### 🪟 Windows
1. Preuzmite Python sa: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Pokrenite instalaciju
3. **OBAVEZNO** označite: ✅ *"Add Python to PATH"*
4. Kliknite *"Install Now"*
5. Provjerite instalaciju:
   ```bash
   python --version
   ```

### 🍎 macOS
```bash
brew install python@3.11
```

### 🐧 Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip
```

---

## ⚙️ Instalacija C++ Build Tools (samo Windows)

`chromadb` zahtijeva Microsoft C++ Build Tools za kompajliranje native ekstenzija.

1. Preuzmite: [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. U instaleru odaberite: **"Desktop development with C++"**
3. Nakon instalacije **obavezno restartujte računar**

---

## 🗂️ Struktura projekta

```
gestatix/
├── backend/
│   ├── app.py                  # Flask API server
│   ├── setup.py                # Inicijalizacija projekta (pokrenuti jednom)
│   ├── build_vector_store.py   # Izgradnja vektorske baze iz PDF-a
│   ├── rag_chroma.py           # RAG logika i semantička pretraga
│   ├── model_train_rf.py       # Treniranje Random Forest modela
│   ├── model_utils.py          # Pomoćne funkcije za model
│   ├── requirements.txt        # Python biblioteke
│   ├── data/
│   │   └── dataset.csv         # Dataset za treniranje modela
│   ├── documents/
│   │   └── Klinicki_vodic_za_antenatalnu_zastitu.pdf  # PDF klinički vodič
│   ├── models/                 # Generiše se automatski pri setup-u
│   │   ├── rf_model.pkl
│   │   ├── label_encoder_rf.pkl
│   │   └── feature_cols_rf.pkl
│   └── chroma_db/              # Generiše se automatski pri setup-u
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

---

## 🚀 Pokretanje projekta

### Korak 1 - Kloniraj repozitorij

```bash
git clone <url-repozitorija>
cd gestatix
```

### Korak 2 - Instaliraj biblioteke

```bash
pip install -r requirements.txt
```

### Korak 3 - Pokreni inicijalizaciju projekta

```bash
python backend/setup.py
```

Ovaj korak automatski:
- Provjerava Python verziju i instalirane biblioteke
- Kreira `.env` fajl
- Trenira ML model (ako ne postoji)
- Gradi vektorsku bazu iz PDF-a (ako nije popunjena)

### Korak 4 - Pokreni API server

```bash
python backend/app.py
```

### Korak 5 - Otvori aplikaciju

U browseru idi na:
```
http://localhost:5000
```

---

## 🔄 Ako preporuke iz kliničkog vodiča nisu prikazane

Ako se umjesto preporuka prikazuje poruka *"Trenutno nema specifičnih preporuka"*, vektorska baza vjerovatno nije popunjena. Pokreni:

```bash
cd backend
python build_vector_store.py
```

Uspješan ispis izgleda ovako:
```
Učitavam PDF: backend/documents/Klinicki_vodic_za_antenatalnu_zastitu.pdf
  Obrađena stranica 1/X ...
Kreirano X valjanih fragmenata iz PDF-a
Uspješno indeksirano X fragmenata.
```

---

## 🧠 Kako funkcioniše? - STAL ciklus

Gestatix koristi STAL ciklus – Sense, Think, Act, Learn:

| Faza | Opis |
| :--- | :--- |
| **🔍 Sense** | Prikupljanje zdravstvenih podataka kroz formu |
| **🧠 Think** | Random Forest model (97.8% tačnosti) + RAG semantička pretraga |
| **🎯 Act** | Prikaz rizika i personalizovanih preporuka iz kliničkog vodiča |
| **📚 Learn** | Feedback sistem – model se poboljšava kroz interakciju |

---

## 📊 Tehnologije

| Tehnologija | Namjena |
| :--- | :--- |
| **Flask** | API server |
| **Random Forest** | ML model za klasifikaciju rizika |
| **ChromaDB** | Vektorska baza za semantičku pretragu |
| **Sentence Transformers** | Višejezični embedding model (bosanski/hrvatski/srpski) |
| **Chart.js** | Vizualizacija rezultata |

---

## ❓ Česti problemi

### `error: Microsoft Visual C++ 14.0 or greater is required`
Instaliraj C++ Build Tools (vidi korak iznad) i restartuj računar.

### `chromadb` se instalira ali vektorska baza je prazna
Pokreni `python build_vector_store.py` iz `backend/` foldera.

### Preporuke se ne prikazuju nakon setup-a
Provjeri da li `chroma_db` folder u `backend/` sadrži dokumente:
```bash
cd backend
python -c "import chromadb; c = chromadb.PersistentClient(path='chroma_db'); [print(col.name, c.get_collection(col.name).count()) for col in c.list_collections()]"
```
Ako ispiše `0` — pokreni `python build_vector_store.py`.

### PDF nije pronađen
Provjeri da se PDF nalazi na putanji `backend/documents/Klinicki_vodic_za_antenatalnu_zastitu.pdf` i da je naziv fajla tačan.

---

© 2026 Gestatix – Sva prava zadržana (All rights reserved)

💙 Gestatix – Tvoj asistent u bezbrižnoj trudnoći