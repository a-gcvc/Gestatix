// API base URL
const API_BASE = 'http://127.0.0.1:5000';

// DOM elementi
const heroSection = document.getElementById('hero-section');
const appMain = document.getElementById('app-main');
const startBtn = document.getElementById('start-journey-btn');
const backBtn = document.getElementById('back-to-home');
const form = document.getElementById('risk-form');
const resultsSection = document.getElementById('results-section');
const newAssessmentBtn = document.getElementById('new-assessment');
const toggleRagBtn = document.getElementById('toggle-rag-btn');
const ragContent = document.getElementById('rag-content');
const loadingOverlay = document.getElementById('loading-overlay');

let riskChart = null;
let featureChart = null;
let lastPredictionData = null;

// STAL stranica elementi
const stalSection = document.getElementById('stal-section');
const howItWorksBtn = document.getElementById('how-it-works-btn');
const backToHeroFromStal = document.getElementById('back-to-hero-from-stal');

// Prikaz STAL stranice


// Provjera API statusa pri pokretanju aplikacije
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            const data = await response.json();
            console.log('API je dostupan na', API_BASE);
            console.log('Model info:', data.model_info);
            return true;
        } else {
            console.error('API vratio status:', response.status);
            return false;
        }
    } catch (err) {
        console.error('Greška pri povezivanju na API:',  err.message);
        console.warn('API nije dostupan. Provjerite:');
        console.warn('1. Da li je backend pokrenut: cd backend && python app.py');
        console.warn('2. Da li je pokrenut na http://127.0.0.1:5000');
        console.warn('3. Konzolu za više detalja');
        return false;
    }
}

// Pozovite na početku


// Helper: Prikaz/ sakrivanje loadinga
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Funkcija za zamjenu zareza sa tačkama u numeričkim poljima
function sanitizeNumericInput(value) {
    if (typeof value !== 'string') return value;
    return value.replace(',', '.');
}

// Dodaj event listenere za sva numerička polja da spriječe unos zareza
function setupNumericInputValidation() {
    const numericInputs = ['dob', 'height', 'weight', 'systolic', 'diastolic', 'glucose', 'temperature', 'heart_rate'];
    
    numericInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', function(e) {
                if (this.value.includes(',')) {
                    this.value = this.value.replace(',', '.');
                }
            });
            
            input.addEventListener('blur', function(e) {
                if (this.value.includes(',')) {
                    this.value = this.value.replace(',', '.');
                }
                if (this.value && !isNaN(parseFloat(this.value))) {
                    this.value = parseFloat(this.value).toString();
                }
            });
            
            input.addEventListener('keypress', function(e) {
            if (e.key === ',') {
                // Ne spriječavamo default, već ćemo zamijeniti na input eventu
                // Samo dozvoljavamo unos
                return;
            }
        });
        }
    });
}

// Sanitizacija podataka prije slanja
function sanitizeFormData() {
    const numericFields = ['dob', 'height', 'weight', 'systolic', 'diastolic', 'glucose', 'temperature', 'heart_rate'];
    
    numericFields.forEach(id => {
        const input = document.getElementById(id);
        if (input && input.value) {
            let value = input.value.replace(',', '.');
            input.value = value;
        }
    });
}

// Validacija forme prije slanja - BOSANSKI JEZIK
function validateForm() {
    let isValid = true;
    sanitizeFormData();
    
    const fields = {
        dob: { 
            element: document.getElementById('dob'), 
            min: 15, 
            max: 60, 
            name: 'Dob',
            errorMin: 'Dob mora biti najmanje 15 godina',
            errorMax: 'Dob ne može biti veća od 60 godina',
            errorEmpty: 'Molimo unesite vašu dob'
        },
        height: { 
            element: document.getElementById('height'), 
            min: 100, 
            max: 220, 
            name: 'Visina',
            errorMin: 'Visina mora biti najmanje 100 cm',
            errorMax: 'Visina ne može biti veća od 220 cm',
            errorEmpty: 'Molimo unesite vašu visinu'
        },
        weight: { 
            element: document.getElementById('weight'), 
            min: 30, 
            max: 200, 
            name: 'Težina',
            errorMin: 'Težina mora biti najmanje 30 kg',
            errorMax: 'Težina ne može biti veća od 200 kg',
            errorEmpty: 'Molimo unesite vašu težinu'
        },
        systolic: { 
            element: document.getElementById('systolic'), 
            min: 70, 
            max: 200, 
            name: 'Sistolicki pritisak',
            errorMin: 'Sistolicki pritisak ne može biti manji od 70 mmHg',
            errorMax: 'Sistolicki pritisak ne može biti veći od 200 mmHg',
            errorEmpty: 'Molimo unesite sistolicki krvni pritisak'
        },
        diastolic: { 
            element: document.getElementById('diastolic'), 
            min: 40, 
            max: 130, 
            name: 'Dijastolicki pritisak',
            errorMin: 'Dijastolicki pritisak ne može biti manji od 40 mmHg',
            errorMax: 'Dijastolicki pritisak ne može biti veći od 130 mmHg',
            errorEmpty: 'Molimo unesite dijastolicki krvni pritisak'
        },
        glucose: { 
            element: document.getElementById('glucose'), 
            min: 2, 
            max: 20, 
            name: 'Glukoza',
            errorMin: 'Glukoza ne može biti manja od 2 mmol/L',
            errorMax: 'Glukoza ne može biti veća od 20 mmol/L',
            errorEmpty: 'Molimo unesite nivo glukoze u krvi'
        },
        temperature: { 
            element: document.getElementById('temperature'), 
            min: 35, 
            max: 40, 
            name: 'Temperatura',
            errorMin: 'Tjelesna temperatura ne može biti niža od 35°C',
            errorMax: 'Tjelesna temperatura ne može biti viša od 40°C',
            errorEmpty: 'Molimo unesite tjelesnu temperaturu'
        },
        heart_rate: { 
            element: document.getElementById('heart_rate'), 
            min: 50, 
            max: 150, 
            name: 'Otkucaji srca',
            errorMin: 'Otkucaji srca ne mogu biti manji od 50 bpm',
            errorMax: 'Otkucaji srca ne mogu biti veći od 150 bpm',
            errorEmpty: 'Molimo unesite otkucaje srca'
        }
    };
    
    // Validacija brojčanih polja
    for (let [key, f] of Object.entries(fields)) {
        if (!f.element) continue;
        
        let rawValue = f.element.value;
        if (rawValue.includes(',')) {
            rawValue = rawValue.replace(',', '.');
            f.element.value = rawValue;
        }
        
        const val = parseFloat(rawValue);
        const errorSpan = document.getElementById(`${key}-error`);
        
        if (isNaN(val)) {
            if (errorSpan) {
                errorSpan.innerText = f.errorEmpty;
                errorSpan.style.color = '#e91e63';
                errorSpan.style.fontSize = '0.8rem';
            }
            isValid = false;
        } else if (val < f.min) {
            if (errorSpan) {
                errorSpan.innerText = f.errorMin;
                errorSpan.style.color = '#e91e63';
                errorSpan.style.fontSize = '0.8rem';
            }
            isValid = false;
        } else if (val > f.max) {
            if (errorSpan) {
                errorSpan.innerText = f.errorMax;
                errorSpan.style.color = '#e91e63';
                errorSpan.style.fontSize = '0.8rem';
            }
            isValid = false;
        } else {
            if (errorSpan) errorSpan.innerText = '';
            f.element.value = val.toString();
        }
    }
    
    // Validacija select polja
    const selects = [
        { id: 'complications', name: 'Komplikacije u prošlim trudnoćama' },
        { id: 'diabetes', name: 'Dijabetes' },
        { id: 'gdm', name: 'Gestacijski dijabetes' },
        { id: 'mental', name: 'Mentalno zdravlje' }
    ];
    
    for (let s of selects) {
        const element = document.getElementById(s.id);
        const errorSpan = document.getElementById(`${s.id}-error`);
        const val = element ? element.value : null;
        
        if (!val || (val !== '0' && val !== '1')) {
            if (errorSpan) {
                errorSpan.innerText = `Molimo odaberite opciju za: ${s.name}`;
                errorSpan.style.color = '#e91e63';
                errorSpan.style.fontSize = '0.8rem';
            }
            isValid = false;
        } else {
            if (errorSpan) errorSpan.innerText = '';
        }
    }
    
    return isValid;
}

// Izračunaj BMI
function calculateBMI(heightCm, weightKg) {
    const heightM = heightCm / 100;
    return weightKg / (heightM * heightM);
}

// Prikupljanje podataka iz forme
function getFormData() {
    const height = parseFloat(document.getElementById('height').value);
    const weight = parseFloat(document.getElementById('weight').value);
    
    let bmi = 0;
    if (height > 0 && weight > 0) {
        bmi = calculateBMI(height, weight);
    }
    
    function parseNumericValue(id, defaultValue = 0) {
        const element = document.getElementById(id);
        if (!element) return defaultValue;
        let value = element.value.trim();
        if (value === '') return defaultValue;
        value = value.replace(',', '.');
        const parsed = parseFloat(value);
        return isNaN(parsed) ? defaultValue : parsed;
    }
    
    function parseIntValue(id, defaultValue = 0) {
        return Math.round(parseNumericValue(id, defaultValue));
    }
    
    // Dohvati select vrijednosti
    const complications = document.getElementById('complications').value;
    const diabetes = document.getElementById('diabetes').value;
    const gdm = document.getElementById('gdm').value;
    const mental = document.getElementById('mental').value;
    
    const data = {
        dob: parseIntValue('dob'),
        sistolicki_krvni_tlak: parseIntValue('systolic'),
        dijastolicki_krvni_tlak: parseIntValue('diastolic'),
        glukoza_u_krvi: parseNumericValue('glucose'),
        tjelesna_temp: parseNumericValue('temperature'),
        BMI: parseFloat(bmi.toFixed(1)),
        komplikacije_u_proslosti: parseInt(complications),
        dijabetes: parseInt(diabetes),
        gestacijski_dijabetes: parseInt(gdm),
        mentalno_zdravlje: parseInt(mental),
        otkucaji_srca: parseIntValue('heart_rate')
    };
    
    // Provjeri da li su svi podaci validni
    console.log('Podaci za slanje (prije slanja):', JSON.stringify(data, null, 2));
    
    // Validacija da nema undefined ili NaN
    for (let [key, value] of Object.entries(data)) {
        if (value === undefined || isNaN(value)) {
            console.error(`Greška: ${key} je ${value}`);
        }
    }
    
    return data;
}

// Prikaz rezultata i grafika
async function displayResults(riskData, ragText, inputData) {
    console.log('Prikazujem rezultate:', riskData);
    
    // Sačuvaj podatke za feedback
    if (inputData) {
        saveLastPrediction(riskData, inputData);
    }
    
    const riskLevel = riskData.risk_level;
    const confidence = (riskData.confidence * 100).toFixed(1);
    const lowProb = (riskData.probabilities.Low * 100).toFixed(1);
    const highProb = (riskData.probabilities.High * 100).toFixed(1);
    
    // Elementi za prikaz rizika
    const riskCard = document.getElementById('risk-card');
    const riskIcon = document.getElementById('risk-icon');
    const riskTextSpan = document.getElementById('risk-text');
    const confidenceSpan = document.getElementById('confidence-value');
    const confidenceBar = document.getElementById('confidence-bar');
    
    if (riskLevel === 'High') {
        if (riskCard) riskCard.style.background = 'linear-gradient(135deg, #fff0f3, #ffe0e8)';
        if (riskIcon) {
            riskIcon.className = 'fas fa-exclamation-triangle';
            riskIcon.style.color = '#e91e63';
        }
        if (riskTextSpan) riskTextSpan.innerHTML = `Nivo rizika: <strong style="color:#e91e63">VISOK RIZIK</strong>`;
    } else {
        if (riskCard) riskCard.style.background = 'linear-gradient(135deg, #e8f5e9, #e0f2f1)';
        if (riskIcon) {
            riskIcon.className = 'fas fa-check-circle';
            riskIcon.style.color = '#2e7d32';
        }
        if (riskTextSpan) riskTextSpan.innerHTML = `Nivo rizika: <strong style="color:#2e7d32">NIZAK RIZIK</strong>`;
    }
    
    if (confidenceSpan) confidenceSpan.innerText = `${confidence}%`;
    if (confidenceBar) confidenceBar.style.width = `${confidence}%`;
    
    // Pie chart
    const ctx = document.getElementById('riskChart');
    if (ctx) {
        if (riskChart) riskChart.destroy();
        riskChart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Nizak rizik', 'Visok rizik'],
                datasets: [{
                    data: [lowProb, highProb],
                    backgroundColor: ['#81c784', '#f06292'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
    
    // Bar chart - učitaj stvarne vrijednosti iz modela
    let featureData;
    try {
        featureData = await loadFeatureImportance();
    } catch (err) {
        console.error('Greška pri učitavanju feature importance:', err);
        featureData = {
            labels: ['dijabetes', 'glukoza_u_krvi', 'otkucaji_srca', 'BMI', 'gestacijski_dijabetes'],
            values: [0.2262, 0.2159, 0.1464, 0.1438, 0.0959],
            percentages: [22.62, 21.59, 14.64, 14.38, 9.59]
        };
    }
    
    // Mapa za prikaz imena na bosanskom
    const featureNamesMap = {
        'dijabetes': 'Dijabetes',
        'glukoza_u_krvi': 'Glukoza u krvi',
        'otkucaji_srca': 'Otkucaji srca',
        'BMI': 'BMI',
        'gestacijski_dijabetes': 'Gestacijski dijabetes',
        'mentalno_zdravlje': 'Mentalno zdravlje',
        'komplikacije_u_proslosti': 'Komplikacije u prošlosti',
        'dob': 'Dob',
        'sistolicki_krvni_tlak': 'Sistolicki pritisak',
        'dijastolicki_krvni_tlak': 'Dijastolicki pritisak',
        'tjelesna_temp': 'Tjelesna temperatura'
    };
    
    const displayLabels = featureData.labels.slice(0, 5).map(label => 
        featureNamesMap[label] || label
    );
    const displayValues = featureData.values.slice(0, 5);
    const displayPercentages = featureData.percentages.slice(0, 5);
    
    const ctx2 = document.getElementById('featureChart');
    if (ctx2) {
        if (featureChart) featureChart.destroy();
        featureChart = new Chart(ctx2.getContext('2d'), {
            type: 'bar',
            data: {
                labels: displayLabels,
                datasets: [{
                    label: 'Utjecaj na rizik (%)',
                    data: displayPercentages,
                    backgroundColor: '#f06292',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: { 
                    y: { 
                        beginAtZero: true, 
                        max: 30,
                        title: { display: true, text: 'Utjecaj (%)' }
                    },
                    x: {
                        title: { display: true, text: 'Faktori rizika' }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.raw.toFixed(1)}% utjecaja na predikciju`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // RAG preporuke
    const ragDiv = document.getElementById('rag-recommendations');
    if (ragDiv) {
        ragDiv.innerHTML = ragText ? ragText.replace(/\n/g, '<br>') : '<p>Nema dodatnih preporuka za prikaz.</p>';
    }
}

// Sačuvaj zadnju predikciju za feedback
function saveLastPrediction(riskData, inputData) {
    lastPredictionData = {
        risk_level: riskData.risk_level,
        input_data: inputData,
        timestamp: new Date().toISOString()
    };
    localStorage.setItem('lastPrediction', JSON.stringify(lastPredictionData));
}

// Slanje feedback-a na backend
async function sendFeedback(userAgrees, correctRisk = null) {
    console.log('sendFeedback pozvana, userAgrees:', userAgrees);
    
    if (!lastPredictionData) {
        console.warn('Nema podataka o posljednjoj predikciji');
        return;
    }
    
    const feedbackData = {
        input_data: lastPredictionData.input_data,
        original_risk: lastPredictionData.risk_level,
        user_agrees: userAgrees
    };
    
    if (!userAgrees && correctRisk) {
        feedbackData.correct_risk = correctRisk;
    }
    
    try {
        const response = await fetch(`${API_BASE}/feedback/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(feedbackData)
        });
        
        const result = await response.json();
        const messageDiv = document.getElementById('feedback-message');
        
        if (result.success) {
            heroSection.style.display = 'none';
            appMain.style.display = 'block';
            messageDiv.innerHTML = '<i class="fas fa-check-circle"></i> Hvala na povratnoj informaciji! Pomažete nam da poboljšamo model.';
            messageDiv.style.display = 'block';
            messageDiv.style.color = '#2e7d32';
            
            if (result.needs_retraining) {
                messageDiv.innerHTML += `<br><i class="fas fa-sync-alt"></i> Model će biti poboljšan nakon ${result.retrain_threshold} prikupljenih feedbackova.`;
            }
            
            loadFeedbackStats();
        } else {
            messageDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Greška pri slanju feedback-a.';
            messageDiv.style.display = 'block';
            messageDiv.style.color = '#e91e63';
        }
        
        // SAMO SAKRIJ PORUKU NAKON 5 SEKUNDI, NE RESETUJ FORMU!
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
        
    } catch (err) {
        console.error('Feedback greška:', err);
        const messageDiv = document.getElementById('feedback-message');
        messageDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Greška pri slanju feedback-a.';
        messageDiv.style.display = 'block';
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }
}

// Učitaj statistiku feedback sistema
async function loadFeedbackStats() {
    try {
        const response = await fetch(`${API_BASE}/feedback/stats`);
        if (response.ok) {
            const stats = await response.json();
            const statsDiv = document.getElementById('feedback-stats');
            const statsText = document.getElementById('stats-text');
            
            if (stats.total_feedback > 0 && statsText) {
                statsText.innerHTML = `📊 Prikupljeno ${stats.total_feedback} povratnih informacija. ${stats.agreed_with_model} korisnika se složilo, ${stats.disagreed_with_model} nije.`;
                if (statsDiv) statsDiv.style.display = 'block';
            }
        }
    } catch (err) {
        console.warn('Nije moguće učitati statistiku feedback-a:', err);
    }
}

// Ručno pokreni retraining
async function triggerRetraining() {
    try {
        const response = await fetch(`${API_BASE}/feedback/retrain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force: true })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Retraining uspješan! Novi accuracy: ${(result.accuracy * 100).toFixed(2)}%`);
            loadFeedbackStats();
        } else {
            alert(`${result.message}`);
        }
    } catch (err) {
        console.error('Retraining greška:', err);
        alert('Greška pri retraining-u modela.');
    }
}

async function submitAssessment(event) {
    // 1. Primarna zaštita od osvježavanja stranice i duplih okidanja
    if (event) {
        event.preventDefault();
        event.stopPropagation(); 
    }

    console.log('submitAssessment pozvana');
    
    // Resetuj prethodne greške u UI-u ako postoje
    const existingErr = document.getElementById('api-error-banner');
    if (existingErr) existingErr.remove();

    // 2. Provjera validacije
    if (!validateForm()) {
        console.log('Validacija nije prošla');
        return;
    }
    
    // Prikaži loading animaciju
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    showLoading(true);

    const payload = getFormData();
    
    // Provjera integriteta podataka (Missing fields check)
    const requiredFields = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak', 
                            'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 'otkucaji_srca'];
    
    const missing = requiredFields.filter(f => payload[f] === undefined || payload[f] === null || isNaN(payload[f]));
    if (missing.length > 0) {
        console.error('Nedostaju polja:', missing);
        alert(`Molimo popunite sva polja: ${missing.join(', ')}`);
        showLoading(false);
        if (loadingOverlay) loadingOverlay.style.display = 'none';
        return;
    }
    
    console.log('Podaci za slanje (JSON):', JSON.stringify(payload));

    try {
        console.log('Šaljem zahtjev na API na:', API_BASE);
        
        const response = await fetch(`${API_BASE}/predict_with_rag`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        console.log('Response primljen, status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API greška ${response.status}: ${errorText.substring(0, 200)}`);
        }
        
        const result = await response.json();
        console.log('Rezultat uspješno parsovan:', result);
        
        const risk = result.risk;
        const ragRecommendations = result.rag_recommendations || 'Nema dodatnih preporuka.';
        
        if (!risk || typeof risk !== 'object') {
            throw new Error('Neispravan odgovor servera: nedostaje objekat rizika');
        }
        
        // 3. KLJUČNI DIO: Sigurna navigacija na rezultate
        // Sakrivamo SVE što bi moglo smetati
        heroSection.style.display = 'none';
        stalSection.style.display = 'none'; // Osiguranje ako je korisnik došao sa "Kako radi"
        
        // Prikazujemo glavni kontejner i sekciju rezultata
        appMain.style.display = 'block';
        form.style.display = 'none'; // Sakrij formu unutar appMain
        resultsSection.style.display = 'block';
        
        try {
            await displayResults(risk, ragRecommendations, payload);
        } catch (displayErr) {
            console.error('Greška pri prikazu rezultata:', displayErr);
            const errDiv = document.createElement('div');
            errDiv.id = 'api-error-banner';
            errDiv.className = 'error-banner'; // Koristi klasu za stil ako postoji
            errDiv.style = 'background:#fff0f3;color:#c62828;padding:1rem;border-radius:12px;margin-top:1rem;text-align:center;border:1px solid #ffccd5;';
            errDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Greška pri renderovanju grafikona. Rezultati su primljeni ali se ne mogu prikazati vizuelno.`;
            resultsSection.prepend(errDiv);
        }
        
        // Skroluj na vrh da korisnik vidi nivo rizika
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
    } catch (err) {
        console.error('❌ Greška:', err);
        
        let errorMsg = err.message.includes('fetch') || err.message.includes('Failed to fetch')
            ? 'Server nije dostupan. Proverite da li je Python backend pokrenut.'
            : err.message;
        
        // U slučaju greške, vrati korisnika na formu da može probati opet
        heroSection.style.display = 'none';
        appMain.style.display = 'block';
        form.style.display = 'block';
        resultsSection.style.display = 'none';
        
        const errDiv = document.createElement('div');
        errDiv.id = 'api-error-banner';
        errDiv.style = 'background:#fff0f3;color:#c62828;padding:1rem;border-radius:12px;margin-top:1rem;text-align:center;border:1px solid #ffccd5;';
        errDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${errorMsg}`;
        form.after(errDiv);
        
    } finally {
        // Obavezno sakrij loading bez obzira na ishod
        showLoading(false);
        if (loadingOverlay) loadingOverlay.style.display = 'none';
    }
}

// Reset forme i povratak na formu
function resetAndShowForm() {
    heroSection.style.display = 'none';
    appMain.style.display = 'block';
    form.reset();
    const errorSpans = document.querySelectorAll('.error-message');
    errorSpans.forEach(span => span.innerText = '');
    form.style.display = 'block';
    resultsSection.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Učitaj stvarnu feature importance iz modela
async function loadFeatureImportance() {
    try {
        const response = await fetch(`${API_BASE}/model/features`);
        if (response.ok) {
            const data = await response.json();
            console.log('Feature importance učitana:', data);
            return data;
        }
    } catch (err) {
        console.warn('Nije moguće učitati feature importance:', err);
    }
    // Fallback vrijednosti ako API ne radi
    console.log('Koristim fallback vrijednosti za feature importance');
    return {
        labels: ['dijabetes', 'glukoza_u_krvi', 'otkucaji_srca', 'BMI', 'gestacijski_dijabetes'],
        values: [0.2262, 0.2159, 0.1464, 0.1438, 0.0959],
        percentages: [22.62, 21.59, 14.64, 14.38, 9.59]
    };
}

// ============================================================
// SENSE - THINK - ACT - LEARN CIKLUS
// ============================================================

// Opisi za svaku fazu
const cycleDescriptions = {
    sense: {
        title: "SENSE - Prikupljanje podataka",
        icon: "fa-database",
        description: "Sistem prikuplja zdravstvene podatke trudnice kroz formu: dob, krvni pritisak, nivo glukoze, BMI (izračunat iz visine i težine), otkucaje srca, temperaturu, te medicinsku historiju. Ovi podaci se validiraju i pripremaju za analizu.",
        details: [
            "11 ključnih zdravstvenih parametara",
            "Automatska validacija unosa (15-60 godina, 50-150 bpm, itd.)",
            "BMI se automatski izračunava iz visine i težine",
            "Podaci se šalju Random Forest modelu na analizu"
        ]
    },
    think: {
        title: "HINK - Analiza i predikcija",
        icon: "fa-brain",
        description: "Random Forest model (100 stabala, max depth 10) analizira prikupljene podatke i predviđa nivo rizika. Model je treniran na 1140 primjera sa 11 karakteristika, sa tačnošću od 97.8%.",
        details: [
            "Random Forest klasifikator sa 100 stabala",
            "97.8% tačnost na testnom skupu",
            "Top 3 faktora: Dijabetes (22.6%), Glukoza (21.6%), Otkucaji srca (14.6%)",
            "RAG sistem pretražuje klinički vodič (1105 fragmenata)"
        ]
    },
    act: {
        title: "ACT - Akcija i preporuke",
        icon: "fa-bullhorn",
        description: "Na osnovu predikcije, sistem generiše personalizovane preporuke. Za visok rizik prikazuju se hitne intervencije, za nizak rizik standardne preporuke iz kliničkog vodiča.",
        details: [
            "Vizuelni prikaz nivoa rizika (crveni/zeleni indikator)",
            "Preporuke iz kliničkog vodiča za antenatalnu zaštitu",
            "Semantička pretraga pronalazi relevantne dijelove dokumenta",
            "Prikazuje relevantnost pronađenih informacija (80%+)"
        ]
    },
    learn: {
        title: "LEARN - Kontinuirano učenje",
        icon: "fa-graduation-cap",
        description: "Sistem uči iz svake interakcije. Korisnici daju povratnu informaciju o tačnosti predikcije, što se čuva u bazi. Nakon 10 novih primjera, model se automatski poboljšava (retraining).",
        details: [
            "Feedback sistem prikuplja povratne informacije",
            "Podaci se čuvaju u zasebnom fajlu za retraining",
            "Retraining nakon 10 novih primjera",
            "Model se kontinuirano poboljšava kroz vrijeme"
        ]
    }
};

// Inicijalizacija STAL ciklusa
function initStalCycle() {
    const steps = document.querySelectorAll('.cycle-step');
    const descriptionDiv = document.getElementById('cycle-description');
    
    if (!steps.length || !descriptionDiv) return;
    
    // Postavi default opis (Sense)
    updateCycleDescription('sense');
    
    // Dodaj event listenere za svaki korak
    steps.forEach(step => {
        step.addEventListener('click', function() {
            const stepName = this.getAttribute('data-step');
            updateCycleDescription(stepName);
            
            // Vizuelno označi aktivni korak
            steps.forEach(s => s.style.background = '#ffe0e8');
            this.style.background = '#f0629240';
            this.style.transform = 'scale(1.02)';
            
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 200);
        });
        
        // Hover efekat
        step.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.transition = 'all 0.2s ease';
        });
        step.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Ažuriraj prikaz opisa za odabranu fazu
function updateCycleDescription(stepName) {
    const desc = cycleDescriptions[stepName];
    const descriptionDiv = document.getElementById('cycle-description');
    
    if (!desc || !descriptionDiv) return;
    
    let detailsHtml = '';
    desc.details.forEach(detail => {
        detailsHtml += `<li style="margin-bottom: 5px;">${detail}</li>`;
    });
    
    descriptionDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <i class="fas ${desc.icon}" style="font-size: 1.3rem; color: #e91e63;"></i>
            <strong style="color: #ad1457;">${desc.title}</strong>
        </div>
        <p style="margin-bottom: 10px;">${desc.description}</p>
        <ul style="margin-left: 1.5rem; color: #6a4e5a;">${detailsHtml}</ul>
        <div style="margin-top: 10px; font-size: 0.8rem; color: #7a5d66; border-top: 1px solid #f8ced9; padding-top: 8px;">
            <i class="fas fa-chart-line"></i> STAL ciklus: Kontinuirano poboljšanje agenta kroz interakciju.
        </div>
    `;
}

// Dodaj STAL statistiku (broj feedbackova, verzija modela, itd.)
async function loadStalStats() {
    try {
        const response = await fetch(`${API_BASE}/feedback/stats`);
        if (response.ok) {
            const stats = await response.json();
            const stalStatsDiv = document.getElementById('stal-stats');
            if (stalStatsDiv) {
                stalStatsDiv.innerHTML = `
                    <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin-top: 0.5rem;">
                        <span><i class="fas fa-comments"></i> Feedback: ${stats.total_feedback || 0}</span>
                        <span><i class="fas fa-check-circle"></i> Tačnih: ${stats.agreed_with_model || 0}</span>
                        <span><i class="fas fa-times-circle"></i> Netačnih: ${stats.disagreed_with_model || 0}</span>
                        <span><i class="fas fa-sync-alt"></i> Nova za učenje: ${stats.new_samples_pending || 0}/${stats.retrain_threshold || 10}</span>
                    </div>
                `;
            }
        }
    } catch (err) {
        console.warn('Nije moguće učitati STAL statistiku:', err);
    }
}

// ============================================================
// EVENT LISTENERI 
// ============================================================

// Start putovanja
startBtn.addEventListener('click', () => {
    heroSection.style.display = 'none';
    appMain.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Povratak na početnu sa FORME (ne sa rezultata)
backBtn.addEventListener('click', () => {
    appMain.style.display = 'none';
    heroSection.style.display = 'flex';
});

// Povratak sa STAL na početnu (ISTI STIL kao backBtn)
backToHeroFromStal?.addEventListener('click', () => {
    stalSection.style.display = 'none';
    heroSection.style.display = 'flex';
});

// Nova procjena - OVDJE SE RESETUJE FORMA
newAssessmentBtn.addEventListener('click', resetAndShowForm);

// Toggle RAG preporuke
toggleRagBtn.addEventListener('click', () => {
    if (ragContent.style.display === 'none') {
        ragContent.style.display = 'block';
        toggleRagBtn.innerHTML = '<i class="fas fa-book-open"></i> Sakrij preporuke';
    } else {
        ragContent.style.display = 'none';
        toggleRagBtn.innerHTML = '<i class="fas fa-book-open"></i> Saznaj više – Preporuke iz vodiča';
    }
});

// Reset dugme na formi
form.addEventListener('reset', function() {
    setTimeout(() => {
        const errorSpans = document.querySelectorAll('.error-message');
        errorSpans.forEach(span => span.innerText = '');
    }, 10);
});

// Feedback dugmad - NE RESETUJU FORMU, samo šalju feedback
document.getElementById('feedback-yes')?.addEventListener('click', function(event) {
    event.preventDefault();
    event.stopPropagation();
    console.log('Feedback YES kliknut');
    event.stopPropagation(); sendFeedback(true);
});

document.getElementById('feedback-no')?.addEventListener('click', function(event) {
    event.preventDefault();
    event.stopPropagation();
    console.log('Feedback NO kliknut');
    const correctRisk = confirm('Da li je tačan rizik "Low" (Nizak) ili "High" (Visok)?\n\nPritisnite OK za "High", Cancel za "Low"');
    const risk = correctRisk ? 'High' : 'Low';
    sendFeedback(false, risk);
});

// Prikaz STAL stranice (Kako Gestatix radi?)


// Inicijalizacija
form.style.display = 'block';
resultsSection.style.display = 'none';
setupNumericInputValidation();
loadFeedbackStats();

console.log('App inicijalizovan!');

// Centralizovana inicijalizacija
document.addEventListener('DOMContentLoaded', () => {
    // 1. Provjera API statusa samo jednom
    checkAPIStatus();
    setupNumericInputValidation();
    loadFeedbackStats();

    // 2. Jedinstven listener za formu
    const riskForm = document.getElementById('risk-form');
    if (riskForm) {
        // Uklanjamo sve stare listenere (ako postoje) i dodajemo jedan čisti
        riskForm.onsubmit = null; 
        riskForm.addEventListener('submit', function(e) {
            e.preventDefault(); 
            e.stopPropagation();
            console.log('Forma pokrenuta...');
            submitAssessment();
        });
    }

    // 3. Navigacija - Započni putovanje
    startBtn?.addEventListener('click', () => {
        heroSection.style.display = 'none';
        appMain.style.display = 'block';
        window.scrollTo(0, 0);
    });

    // 4. Navigacija - Kako radi (STAL)
    const handleNavigation = (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        heroSection.style.display = 'none';
        appMain.style.display = 'none';
        stalSection.style.display = 'block';
        if (typeof initStalCycle === 'function') initStalCycle();
    };

    if (howItWorksBtn) {
        howItWorksBtn.onclick = handleNavigation;
    }
    
    // Nazad dugmad
    backBtn?.addEventListener('click', () => {
        appMain.style.display = 'none';
        heroSection.style.display = 'block';
    });

    backToHeroFromStal?.addEventListener('click', () => {
        stalSection.style.display = 'none';
        heroSection.style.display = 'block';
    });
});

