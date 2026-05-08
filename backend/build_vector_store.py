"""
build_vector_store.py
Izgradnja vektorske baze iz PDF dokumenta na bosanskom/hrvatskom/srpskom jeziku.
Pokreni jednom prije pokretanja API-ja.
"""

import os
import sys
from rag_chroma import build_vector_store_from_pdf, test_rag_system

def main():
    print("\n" + "="*60)
    print("  IZGRADNJA VEKTORSKE BAZE ZA RAG SISTEM")
    print("="*60)
    
    # Putanja do PDF fajla (jezik: bosanski/hrvatski/srpski) 
    pdf_path = "documents/Klinicki_vodic_za_antenatalnu_zastitu.pdf"
    
    # Provjeri da li PDF postoji
    if not os.path.exists(pdf_path):
        print(f"\n❌ PDF fajl nije pronađen: {pdf_path}")
        print("\nMolimo te da:")
        print("  1. Kreiraš folder 'documents/'")
        print("  2. Staviš PDF dokument u taj folder")
        print(f"  3. Preimenuješ ga u 'Klinicki_vodic_za_antenatalnu_zastitu.pdf'")
        
        # Opciono: prikaži dostupne fajlove u folderu
        if os.path.exists('documents'):
            print("\n📁 Dostupni fajlovi u 'documents/' folderu:")
            for f in os.listdir('documents'):
                print(f"   - {f}")
        
        create_test = input("\nŽeliš li kreirati testni PDF za demonstraciju? (y/n): ")
        if create_test.lower() == 'y':
            create_test_pdf_bhs()
            pdf_path = "documents/test_vodic_bhs.pdf"
        else:
            sys.exit(1)
    
    # Izgradi vektorsku bazu
    print(f"\n📄 Učitavam PDF: {pdf_path}")
    print("🌐 Jezik dokumenta: bosanski/hrvatski/srpski")
    build_vector_store_from_pdf(pdf_path, force_rebuild=True)
    
    print("\n✅ Vektorska baza je uspješno izgrađena!")
    print("\nSada možeš pokrenuti Flask API: python app.py")
    
    # Opciono: testiraj sistem
    test = input("\nŽeliš li testirati RAG sistem na bosanskom/hrvatskom/srpskom? (y/n): ")
    if test.lower() == 'y':
        test_rag_system(pdf_path)


def create_test_pdf_bhs():
    """Kreira testni PDF na bosanskom/hrvatskom/srpskom jeziku za potrebe demonstracije."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        
        os.makedirs("documents", exist_ok=True)
        pdf_path = "documents/test_vodic_bhs.pdf"
        
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Dodaj sadržaj na bosanskom/hrvatskom/srpskom jeziku
        content = [
            "KLINIČKI VODIČ ZA ANTENATALNU ZAŠTITU",
            "",
            "=== DIJABETES U TRUDNOĆI ===",
            "Gestacijski dijabetes (GDM) je stanje povišene glukoze u krvi koje se prvi put",
            "dijagnostikuje tokom trudnoće. Dijagnostičke vrijednosti: glukoza natašte ≥5.3 mmol/L",
            "ili 2h nakon opterećenja ≥8.6 mmol/L.",
            "",
            "PREPORUKE ZA LIJEČENJE GDM:",
            "1. Medicinska nutritivna terapija - dijeta sa 40-45% ugljikohidrata",
            "2. Redovna fizička aktivnost (30 minuta hodanja dnevno)",
            "3. Monitoring glukoze 4 puta dnevno (natašte i 1h nakon obroka)",
            "4. Insulin ili metformin ako se ne postižu ciljne vrijednosti",
            "5. Ciljne vrijednosti: glukoza natašte <5.3 mmol/L, 1h postprandijalno <7.8 mmol/L",
            "",
            "=== VISOK KRVNI PRITISAK (HIPERTENZIJA) ===",
            "Hipertenzija u trudnoći definiše se kao krvni pritisak ≥140/90 mmHg.",
            "Preeklampsija je stanje koje karakteriše visok krvni pritisak i oštećenje organa,",
            "najčešće jetre i bubrega, nakon 20. sedmice trudnoće.",
            "",
            "SIMTOMI PREEKLAMPSIJE:",
            "- Jaka glavobolja koja ne prolazi nakon uzimanja lijekova",
            "- Promjene vida (zamućen vid, osjetljivost na svjetlo)",
            "- Bol u gornjem dijelu stomaka (posebno desno)",
            "- Mučnina i povraćanje",
            "- Otežano disanje",
            "- Nenormalno oticanje ruku i lica",
            "",
            "LIJEČENJE HIPERTENZIJE U TRUDNOĆI:",
            "- Antihipertenzivna terapija: labetalol, nifedipin, metildopa",
            "- Magnezijum sulfat za prevenciju eklampsije",
            "- Indukcija porođaja nakon 37 sedmice kod teške preeklampsije",
            "- Ciljni krvni pritisak: 130-155/80-105 mmHg",
            "",
            "=== GOJAZNOST I BMI ===",
            "Gojaznost u trudnoći (BMI >30 kg/m²) povećava rizik od komplikacija:",
            "- Preeklampsija (3-4 puta veći rizik)",
            "- Gestacijski dijabetes (2-3 puta veći rizik)",
            "- Makrozomija (velika beba)",
            "- Prijevremeni porođaj",
            "- Tromboembolija",
            "",
            "PREPORUKE ZA TRUDNICE SA GOJAZNOŠĆU:",
            "- Preporučeno povećanje tjelesne težine: 5-9 kg tokom trudnoće",
            "- Suplementacija: folna kiselina 5 mg dnevno (prvih 12 sedmica)",
            "- Vitamin D 400-1000 IU dnevno",
            "- Redovna fizička aktivnost (plivanje, šetnja, prenatalna joga)",
            "- Konsultacija s nutricionistom",
            "",
            "=== PROBLEMI SA ŠTITNOM ŽLIJEZDOM ===",
            "Trudnoća značajno utiče na funkciju štitne žlijezde.",
            "Preporučuje se kontrola nivoa TSH, FT3 i FT4.",
            "Hipotireoza se liječi levotiroksinom sa ciljnim TSH <2.5 mIU/L.",
            "Konsultacija s endokrinologom je obavezna.",
            "",
            "=== ANEMIJA U TRUDNOĆI ===",
            "Anemija (hemoglobin <110 g/L) je česta u trudnoći.",
            "PREPORUKE:",
            "- Suplementacija gvožđem (30-60 mg elementarnog gvožđa dnevno)",
            "- Folna kiselina 400-800 mcg dnevno",
            "- Ishrana bogata mesom, mahunarkama, zelenim lisnatim povrćem",
            "- Vitamin C za bolju apsorpciju gvožđa",
            "",
            "=== MENTALNO ZDRAVLJE U TRUDNOĆI ===",
            "Depresija i anksioznost pogađaju 10-20% trudnica.",
            "PREPORUKE:",
            "- Psihološka podrška i savjetovanje",
            "- Grupni programi za trudnice",
            "- Razgovor s porodičnim ljekarom o sigurnim terapijskim opcijama",
            "- Izbjegavanje stresa i dovoljno odmora",
            "",
            "=== KOMPLIKACIJE U PROŠLOSTI ===",
            "Trudnice sa komplikacijama u prethodnim trudnoćama zahtijevaju:",
            "- Češće ultrazvučno praćenje",
            "- Ranije preglede (prije 12. sedmice)",
            "- Planiranje porođaja u tercijarnom centru",
            "- Dodatne konsultacije (perinatolog, anesteziolog, neonatolog)",
            "",
            "=== OPŠTE PREPORUKE ZA ZDRAVU TRUDNOĆU ===",
            "- Redovni prenatalni pregledi (10-14 puta tokom trudnoće)",
            "- Zdrava ishrana bogata voćem, povrćem, cjelovitim žitaricama",
            "- Umjerena fizička aktivnost (30 minuta dnevno)",
            "- Izbjegavanje alkohola, cigareta i droga",
            "- Suplementacija folnom kiselinom (400-800 mcg dnevno)",
            "- Adekvatan unos tečnosti (2-3 litra dnevno)",
            "- Dovoljno sna i odmora (7-9 sati noću)",
        ]
        
        y = height - 50
        for line in content:
            c.drawString(50, y, line)
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50
        
        c.save()
        print(f"✅ Kreiran testni PDF na bosanskom/hrvatskom/srpskom: {pdf_path}")
        
    except ImportError:
        print("ReportLab nije instaliran. Instaliraj sa: pip install reportlab")
        print("Ili ručno stavi svoj PDF u documents/ folder.")

if __name__ == "__main__":
    main()