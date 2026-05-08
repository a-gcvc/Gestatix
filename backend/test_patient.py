"""
test_patient.py
Testna skripta za provjeru Random Forest modela i RAG sistema.
Unosite podatke o pacijentici i dobijate predikciju rizika + preporuke iz PDF dokumenta.
"""

import sys
import json
from model_utils import predict_risk
from rag_chroma import get_relevant_advice_rag, semantic_search, build_semantic_query_bhs


def print_separator(char="=", length=60):
    """Ispisuje separator liniju."""
    print(char * length)


def print_header(text):
    """Ispisuje naslov."""
    print_separator()
    print(f"  {text}")
    print_separator()


def get_patient_input():
    """Prikuplja unos podataka o pacijentici od korisnika."""
    print_header("UNOS PODATAKA O PACIJENTICI")
    
    print("\nUnesite sljedeće parametre (za testiranje možete pritisnuti Enter za default vrijednosti):\n")
    
    # Default test pacijent (visok rizik)
    defaults = {
        'dob': 30,
        'sistolicki_krvni_tlak': 150,
        'dijastolicki_krvni_tlak': 95,
        'glukoza_u_krvi': 9.2,
        'tjelesna_temp': 98.6,
        'BMI': 32,
        'komplikacije_u_proslosti': 0,
        'dijabetes': 0,
        'gestacijski_dijabetes': 1,
        'mentalno_zdravlje': 0,
        'otkucaji_srca': 85
    }
    
    print("📋 Osnovni podaci:")
    dob = input(f"   Dob (godine) [default: {defaults['dob']}]: ").strip()
    dob = int(dob) if dob else defaults['dob']
    
    print("\n🩺 Vitalni parametri:")
    systolic = input(f"   Sistolicki krvni tlak (mmHg) [default: {defaults['sistolicki_krvni_tlak']}]: ").strip()
    systolic = int(systolic) if systolic else defaults['sistolicki_krvni_tlak']
    
    diastolic = input(f"   Dijastolicki krvni tlak (mmHg) [default: {defaults['dijastolicki_krvni_tlak']}]: ").strip()
    diastolic = int(diastolic) if diastolic else defaults['dijastolicki_krvni_tlak']
    
    glucose = input(f"   Glukoza u krvi (mmol/L) [default: {defaults['glukoza_u_krvi']}]: ").strip()
    glucose = float(glucose) if glucose else defaults['glukoza_u_krvi']
    
    temp = input(f"   Tjelesna temperatura (Fahrenheit) [default: {defaults['tjelesna_temp']}]: ").strip()
    temp = float(temp) if temp else defaults['tjelesna_temp']
    
    bmi = input(f"   BMI (kg/m²) [default: {defaults['BMI']}]: ").strip()
    bmi = float(bmi) if bmi else defaults['BMI']
    
    heart_rate = input(f"   Otkucaji srca (bpm) [default: {defaults['otkucaji_srca']}]: ").strip()
    heart_rate = int(heart_rate) if heart_rate else defaults['otkucaji_srca']
    
    print("\n🏥 Medicinska historija (0 = Ne, 1 = Da):")
    complications = input(f"   Komplikacije u prošlim trudnoćama [default: {defaults['komplikacije_u_proslosti']}]: ").strip()
    complications = int(complications) if complications else defaults['komplikacije_u_proslosti']
    
    diabetes = input(f"   Dijabetes (postojeći) [default: {defaults['dijabetes']}]: ").strip()
    diabetes = int(diabetes) if diabetes else defaults['dijabetes']
    
    gdm = input(f"   Gestacijski dijabetes [default: {defaults['gestacijski_dijabetes']}]: ").strip()
    gdm = int(gdm) if gdm else defaults['gestacijski_dijabetes']
    
    mental = input(f"   Mentalno zdravlje (depresija/anksioznost) [default: {defaults['mentalno_zdravlje']}]: ").strip()
    mental = int(mental) if mental else defaults['mentalno_zdravlje']
    
    patient_data = {
        'dob': dob,
        'sistolicki_krvni_tlak': systolic,
        'dijastolicki_krvni_tlak': diastolic,
        'glukoza_u_krvi': glucose,
        'tjelesna_temp': temp,
        'BMI': bmi,
        'komplikacije_u_proslosti': complications,
        'dijabetes': diabetes,
        'gestacijski_dijabetes': gdm,
        'mentalno_zdravlje': mental,
        'otkucaji_srca': heart_rate
    }
    
    return patient_data


def display_prediction_result(result):
    """Prikazuje rezultat predikcije rizika."""
    print_header("PREDIKCIJA RIZIKA")
    
    risk = result['risk_level']
    confidence = result['confidence']
    probs = result['probabilities']
    
    # Ikona i boja prema riziku
    if risk == 'High':
        icon = "🔴"
        risk_text = "VISOK RIZIK"
    else:
        icon = "🟢"
        risk_text = "NISKOG RIZIKA"
    
    print(f"\n   {icon} Nivo rizika: {risk_text}")
    print(f"   Pouzdanost predikcije: {confidence*100:.1f}%")
    print(f"\n   Detalji vjerovatnoće:")
    print(f"      - Low rizik: {probs['Low']*100:.1f}%")
    print(f"      - High rizik: {probs['High']*100:.1f}%")


def identify_risk_factors(patient_data):
    """Identifikuje kritične parametre na osnovu unosa."""
    risk_factors = []
    
    # Glukoza
    glucose = patient_data.get('glukoza_u_krvi', 0)
    if glucose > 7.8:
        risk_factors.append(f"Povišena glukoza ({glucose} mmol/L) - granica je 7.8")
    elif glucose > 5.6:
        risk_factors.append(f"Granična glukoza ({glucose} mmol/L)")
    
    # Krvni pritisak
    systolic = patient_data.get('sistolicki_krvni_tlak', 0)
    diastolic = patient_data.get('dijastolicki_krvni_tlak', 0)
    if systolic >= 140 or diastolic >= 90:
        risk_factors.append(f"Povišen krvni pritisak ({systolic}/{diastolic} mmHg)")
    elif systolic >= 130 or diastolic >= 85:
        risk_factors.append(f"Granični krvni pritisak ({systolic}/{diastolic} mmHg)")
    
    # BMI
    bmi = patient_data.get('BMI', 0)
    if bmi >= 30:
        risk_factors.append(f"Gojaznost (BMI = {bmi})")
    elif bmi >= 25:
        risk_factors.append(f"Prekomjerna težina (BMI = {bmi})")
    elif bmi < 18.5:
        risk_factors.append(f"Nedovoljna težina (BMI = {bmi})")
    
    # Dijabetes
    if patient_data.get('dijabetes', 0) == 1:
        risk_factors.append("Postojeći dijabetes")
    
    if patient_data.get('gestacijski_dijabetes', 0) == 1:
        risk_factors.append("Gestacijski dijabetes")
    
    # Mentalno zdravlje
    if patient_data.get('mentalno_zdravlje', 0) == 1:
        risk_factors.append("Problemi s mentalnim zdravljem")
    
    # Komplikacije
    if patient_data.get('komplikacije_u_proslosti', 0) == 1:
        risk_factors.append("Komplikacije u prethodnim trudnoćama")
    
    # Otkucaji srca
    hr = patient_data.get('otkucaji_srca', 0)
    if hr > 100:
        risk_factors.append(f"Ubrzan rad srca ({hr} bpm)")
    elif hr < 60:
        risk_factors.append(f"Usporen rad srca ({hr} bpm)")
    
    return risk_factors


def test_semantic_search():
    """Testira semantičku pretragu baze znanja."""
    print_header("TEST SEMANTIČKE PRETRAGE")
    
    test_queries = [
        "dijabetes u trudnoći",
        "visok krvni pritisak",
        "gojaznost i trudnoća",
        "preeklampsija simptomi",
        "anemija liječenje"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Upit: '{query}'")
        results = semantic_search(query, n_results=2)
        if results:
            for i, r in enumerate(results):
                print(f"   Rezultat {i+1} (relevantnost: {r['relevance_score']:.2f}):")
                # Prikaži prvih 150 karaktera
                preview = r['text'][:150].replace('\n', ' ')
                print(f"      {preview}...")
        else:
            print("   Nema rezultata.")


def run_test_scenarios():
    """Pokreće predefinirane test scenarije."""
    print_header("TEST SCENARIJI")
    
    scenarios = [
        {
            'name': "Scenarij 1: Zdravija trudnoća (nizak rizik)",
            'data': {
                'dob': 25,
                'sistolicki_krvni_tlak': 110,
                'dijastolicki_krvni_tlak': 70,
                'glukoza_u_krvi': 5.2,
                'tjelesna_temp': 98.6,
                'BMI': 22,
                'komplikacije_u_proslosti': 0,
                'dijabetes': 0,
                'gestacijski_dijabetes': 0,
                'mentalno_zdravlje': 0,
                'otkucaji_srca': 75
            }
        },
        {
            'name': "Scenarij 2: Gestacijski dijabetes (visok rizik)",
            'data': {
                'dob': 32,
                'sistolicki_krvni_tlak': 125,
                'dijastolicki_krvni_tlak': 80,
                'glukoza_u_krvi': 9.5,
                'tjelesna_temp': 98.6,
                'BMI': 28,
                'komplikacije_u_proslosti': 0,
                'dijabetes': 0,
                'gestacijski_dijabetes': 1,
                'mentalno_zdravlje': 0,
                'otkucaji_srca': 82
            }
        },
        {
            'name': "Scenarij 3: Hipertenzija + gojaznost (visok rizik)",
            'data': {
                'dob': 35,
                'sistolicki_krvni_tlak': 155,
                'dijastolicki_krvni_tlak': 95,
                'glukoza_u_krvi': 6.2,
                'tjelesna_temp': 98.6,
                'BMI': 34,
                'komplikacije_u_proslosti': 0,
                'dijabetes': 0,
                'gestacijski_dijabetes': 0,
                'mentalno_zdravlje': 0,
                'otkucaji_srca': 90
            }
        },
        {
            'name': "Scenarij 4: Postojeći dijabetes (visok rizik)",
            'data': {
                'dob': 28,
                'sistolicki_krvni_tlak': 130,
                'dijastolicki_krvni_tlak': 85,
                'glukoza_u_krvi': 8.0,
                'tjelesna_temp': 98.6,
                'BMI': 26,
                'komplikacije_u_proslosti': 0,
                'dijabetes': 1,
                'gestacijski_dijabetes': 0,
                'mentalno_zdravlje': 0,
                'otkucaji_srca': 78
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 {scenario['name']}")
        print("-" * 40)
        
        # Predikcija
        result = predict_risk(scenario['data'])
        
        # RAG preporuke
        advice = get_relevant_advice_rag(
            f"Trudnoća sa nivoom rizika {result['risk_level']}",
            scenario['data'],
            n_results=2
        )
        
        print(f"   Nivo rizika: {'🔴 VISOK' if result['risk_level'] == 'High' else '🟢 NISK'}")
        print(f"   Pouzdanost: {result['confidence']*100:.1f}%")
        
        # Prikaži prvu preporuku (ukratko)
        if advice and len(advice) > 0:
            first_advice = advice.split('\n')[0] if '\n' in advice else advice[:200]
            print(f"   Preporuka: {first_advice[:150]}...")
        print()


def main():
    """Glavna funkcija za testiranje."""
    print_header("TESTIRANJE RANDOM FOREST MODELA I RAG SISTEMA")
    print("\nDostupne opcije:")
    print("  1. Unos vlastitih podataka")
    print("  2. Testiranje semantičke pretrage")
    print("  3. Pokretanje predefiniranih scenarija")
    print("  4. Sve navedeno")
    
    choice = input("\nOdaberite opciju (1-4) [default: 4]: ").strip()
    choice = choice if choice else "4"
    
    if choice == "1":
        # Unos podataka
        patient_data = get_patient_input()
        
        # Prikaz unesenih podataka
        print_header("UNESENI PODACI")
        for key, value in patient_data.items():
            print(f"   {key}: {value}")
        
        # Identifikacija rizičnih faktora
        risk_factors = identify_risk_factors(patient_data)
        if risk_factors:
            print_header("IDENTIFIKOVANI RIZIČNI FAKTORI")
            for factor in risk_factors:
                print(f"   ⚠️ {factor}")
        
        # Predikcija
        result = predict_risk(patient_data)
        display_prediction_result(result)
        
        # RAG preporuke
        print_header("PREPORUKE IZ KLINIČKOG VODIČA")
        print("\nTragam za relevantnim savjetima...\n")
        
        advice = get_relevant_advice_rag(
            f"Trudnoća sa nivoom rizika {result['risk_level']}",
            patient_data,
            n_results=4
        )
        
        print(advice)
        
    elif choice == "2":
        test_semantic_search()
        
    elif choice == "3":
        run_test_scenarios()
        
    elif choice == "4":
        # Prvo testiraj scenarije
        run_test_scenarios()
        
        print("\n" + "="*60)
        test_semantic_search()
        
        # Pitaj za vlastiti unos
        custom = input("\nŽelite li unijeti vlastite podatke? (y/n): ").strip().lower()
        if custom == 'y':
            patient_data = get_patient_input()
            
            print_header("UNESENI PODACI")
            for key, value in patient_data.items():
                print(f"   {key}: {value}")
            
            risk_factors = identify_risk_factors(patient_data)
            if risk_factors:
                print_header("IDENTIFIKOVANI RIZIČNI FAKTORI")
                for factor in risk_factors:
                    print(f"   ⚠️ {factor}")
            
            result = predict_risk(patient_data)
            display_prediction_result(result)
            
            print_header("PREPORUKE IZ KLINIČKOG VODIČA")
            advice = get_relevant_advice_rag(
                f"Trudnoća sa nivoom rizika {result['risk_level']}",
                patient_data,
                n_results=4
            )
            print(advice)
    
    print("\n" + "="*60)
    print("  TESTIRANJE ZAVRŠENO")
    print("="*60)

    # Dio u test_patient.py koji prikazuje preporuke

def display_recommendations(advice_text, risk_level):
    """
    Prikazuje preporuke sa uvodnom rečenicom.
    """
    print_header("PREPORUKE IZ KLINIČKOG VODIČA")
    
    # Uvodna rečenica o vodiču
    print(f"\n📚 Prema **Kliničkom vodiču za antenatalnu zaštitu** (izdanje 2021.):\n")
    
    if risk_level == "High":
        print("🔴 **VISOK RIZIK** - Preporuke za hitnu intervenciju:\n")
    else:
        print("🟢 **STANDARDNA NJEGA** - Opšte preporuke za zdravu trudnoću:\n")
    
    # Prikaz preporuka
    print(advice_text)


if __name__ == "__main__":
    main()