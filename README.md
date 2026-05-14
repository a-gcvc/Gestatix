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

### 🍎 macOS
    brew install python@3.11

### 🐧 Linux (Ubuntu/Debian)
    sudo apt update
    sudo apt install python3 python3-pip

### 📦 Instalacija biblioteka

Nakon što ste instalirali Python, otvorite terminal u folderu projekta i pokrenite:

    pip install -r requirements.txt

Provjera instalacije:

    pip list

### 🚀 Pokretanje aplikacije
1. Pokrenite backend (API server)
    cd backend
    python app.py

2. Otvorite aplikaciju

U browseru idite na:

    http://localhost:5000

### 🧠 Kako funkcioniše? – STAL ciklus

Gestatix koristi STAL ciklus – Sense, Think, Act, Learn:
| Faza | Opis |
| :--- | :--- |
| **🔍 Sense** | Prikupljanje zdravstvenih podataka kroz formu |
| **🧠 Think** | Random Forest model (97.8% tačnosti) + RAG semantička pretraga |
| **🎯 Act** | Prikaz rizika i personalizovanih preporuka iz kliničkog vodiča |
| **📚 Learn** | Feedback sistem – model se poboljšava kroz interakciju |

### 📊 Tehnologije
| Tehnologija | Namjena |
| :--- | :--- |
| **Flask** | API server |
| **Random Forest** | ML model za klasifikaciju rizika |
| **ChromaDB** | Vektorska baza za semantičku pretragu |
| **Sentence Transformers** | Višejezični embedding model (bosanski/hrvatski/srpski) |
| **Chart.js** | Vizualizacija rezultata |


© 2026 Gestatix – Sva prava zadržana (All rights reserved)

💙 Gestatix – Tvoj asistent u bezbrižnoj trudnoći
