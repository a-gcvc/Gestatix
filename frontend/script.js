// API base URL
const API_BASE = 'http://127.0.0.1:5000';

// DOM elementi - Main DOM elements
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
let lastPredictionData = null;

// STAL stranica elementi - STAL page elements
const stalSection = document.getElementById('stal-section');
const howItWorksBtn = document.getElementById('how-it-works-btn');
const backToHeroFromStal = document.getElementById('back-to-hero-from-stal');

// Provjera API statusa pri pokretanju aplikacije - Check API status on app startup
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

// Helper: Prikaz/ sakrivanje loadinga - Helper: Show/hide loading
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Dodaj event listenere za sva numerička polja da spriječe unos zareza i automatski ih zamijene tačkama - Add event listeners to all numeric fields to prevent comma input and automatically replace with dots
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
                return;
            }
        });
        }
    });
}

// Sanitizacija podataka prije slanja - Sanitization of data before sending
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

// Validacija forme prije slanja - BOSANSKI JEZIK - Form validation before submission - IN BOSNIAN LANGUAGE
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
    
    // Validacija brojčanih polja - Validation of numeric fields
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
    
    // Validacija select polja - Validation of select fields
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

// Izračunaj BMI na osnovu visine i težine - Calculate BMI based on height and weight
function calculateBMI(heightCm, weightKg) {
    const heightM = heightCm / 100;
    return weightKg / (heightM * heightM);
}

// Prikupljanje podataka iz forme - Collecting data from the form
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
    
    // Dohvati select vrijednosti - Get select values
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
    
    // Provjeri da li su svi podaci validni prije slanja - Check if all data is valid before sending
    console.log('Podaci za slanje (prije slanja):', JSON.stringify(data, null, 2));
    
    // Validacija da nema undefined ili NaN vrijednosti - Validation to ensure no undefined or NaN values
    for (let [key, value] of Object.entries(data)) {
        if (value === undefined || isNaN(value)) {
            console.error(`Greška: ${key} je ${value}`);
        }
    }
    
    return data;
}

// Prikaz rezultata i grafika - Display results and charts
async function displayResults(riskData, ragText, inputData) {
    console.log('Prikazujem rezultate:', riskData);
    
    // Sačuvaj podatke za feedback ako su dostupni - Save data for feedback if available
    if (inputData) {
        saveLastPrediction(riskData, inputData);
    }
    
    const riskLevel = riskData.risk_level;
    const confidence = (riskData.confidence * 100).toFixed(1);
    const lowProb = (riskData.probabilities.Low * 100).toFixed(1);
    const highProb = (riskData.probabilities.High * 100).toFixed(1);
    
    // Elementi za prikaz rizika i confidence bar - Elements for displaying risk and confidence bar
    const riskCard = document.getElementById('risk-card');
    const riskIcon = document.getElementById('risk-icon');
    const riskTextSpan = document.getElementById('risk-text');
    const confidenceSpan = document.getElementById('confidence-value');
    const confidenceBar = document.getElementById('confidence-bar');
    
    // Element za preporuku akcije (kreiraj ako ne postoji) - Element for action recommendation (create if it doesn't exist)
    let actionRecommendation = document.getElementById('action-recommendation');
    if (!actionRecommendation && riskCard) {
        actionRecommendation = document.createElement('div');
        actionRecommendation.id = 'action-recommendation';
        actionRecommendation.style.marginTop = '1rem';
        actionRecommendation.style.padding = '0.8rem';
        actionRecommendation.style.borderRadius = '12px';
        actionRecommendation.style.fontWeight = '500';
        actionRecommendation.style.textAlign = 'center';
        riskCard.appendChild(actionRecommendation);
    }
    
    if (riskLevel === 'High') {
        if (riskCard) riskCard.style.background = 'linear-gradient(135deg, #fff0f3, #ffe0e8)';
        if (riskIcon) {
            riskIcon.className = 'fas fa-exclamation-triangle';
            riskIcon.style.color = '#e91e63';
        }
        if (riskTextSpan) riskTextSpan.innerHTML = `Nivo rizika: <strong style="color:#e91e63">VISOK RIZIK</strong>`;
        
        // Preporuka za VISOK rizik - JAVITI SE LJEKARU - Recommendation for HIGH risk - SEE A DOCTOR
        if (actionRecommendation) {
            actionRecommendation.style.background = '#ffebee';
            actionRecommendation.style.borderLeft = '4px solid #e91e63';
            actionRecommendation.style.color = '#c2185b';
            actionRecommendation.innerHTML = `
                <i class="fas fa-stethoscope" style="color: #e91e63; margin-right: 8px;"></i>
                <strong>VAŽNA PREPORUKA:</strong><br>
                Vaši parametri ukazuju na povišen rizik po zdravlje vas i vaše bebe. <strong>Preporučujemo vam da se što prije javite svom ginekologu</strong> radi dodatnih pretraga i pravovremene intervencije.
                <div style="font-size: 0.85rem; margin-top: 8px; color: #ad1457;">
                    📞 Kontaktirajte vašu ambulantu ili hitnu službu ako osjetite bilo kakve simptome.
                </div>
            `;
        }
        
    } else {
        if (riskCard) riskCard.style.background = 'linear-gradient(135deg, #e8f5e9, #e0f2f1)';
        if (riskIcon) {
            riskIcon.className = 'fas fa-check-circle';
            riskIcon.style.color = '#2e7d32';
        }
        if (riskTextSpan) riskTextSpan.innerHTML = `Nivo rizika: <strong style="color:#2e7d32">NIZAK RIZIK</strong>`;
        
        // Preporuka za NIZAK rizik - NASTAVITE SA REDOVNIM PREGLEDIMA - Recommendation for LOW risk - CONTINUE REGULAR CHECK-UPS
        if (actionRecommendation) {
            actionRecommendation.style.background = '#e8f5e9';
            actionRecommendation.style.borderLeft = '4px solid #4caf50';
            actionRecommendation.style.color = '#1b5e20';
            actionRecommendation.innerHTML = `
                <i class="fas fa-heartbeat" style="color: #4caf50; margin-right: 8px;"></i>
                <strong>PREPORUKA:</strong><br>
                Vaši parametri su u okviru normalnih vrijednosti. Nastavite sa redovnim prenatalnim pregledima i zdravim načinom života.
                <div style="font-size: 0.85rem; margin-top: 8px; color: #2e7d32;">
                    🏃‍♀️ Preporučuje se umjerena fizička aktivnost i uravnotežena ishrana.
                </div>
            `;
        }
    }
    
    if (confidenceSpan) confidenceSpan.innerText = `${confidence}%`;
    if (confidenceBar) confidenceBar.style.width = `${confidence}%`;
    
    // ============================================================
    // PIE CHART sa procentima i responzivnošću - PIE CHART with percentages and responsiveness
    // ============================================================
    
    const isMobile = window.innerWidth < 768;
    
    const ctx = document.getElementById('riskChart');
    if (ctx) {
        if (riskChart) riskChart.destroy();
        riskChart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Nizak rizik', 'Visok rizik'],
                datasets: [{
                    data: [lowProb, highProb],
                    backgroundColor: [
                        riskLevel === 'High' ? '#f8d7da' : '#81c784',
                        riskLevel === 'High' ? '#f06292' : '#c8e6c9'
                    ],
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '72%',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.raw.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Centralni tekst sa procentima i dominantnim rizikom - Central text with percentages and dominant risk
    const chartContainer = document.getElementById('riskChart').parentElement;
    let centerText = document.getElementById('chart-center-text');
    
    // Ukloni postojeći tekst ako postoji da se ne duplira - Remove existing text if it exists to avoid duplication
    if (centerText && centerText.parentNode) {
        centerText.remove();
    }
    
    if (chartContainer && !document.getElementById('chart-center-text')) {
        centerText = document.createElement('div');
        centerText.id = 'chart-center-text';
        chartContainer.style.position = 'relative';
        chartContainer.appendChild(centerText);
    }
    
    if (centerText) {
        const dominantRisk = highProb > lowProb ? 'Visok rizik' : 'Nizak rizik';
        const dominantPercent = Math.max(highProb, lowProb).toFixed(1);
        const fontSize = isMobile ? '1rem' : '1.5rem';
        const subFontSize = isMobile ? '0.55rem' : '0.7rem';
        
        centerText.style.position = 'absolute';
        centerText.style.top = '50%';
        centerText.style.left = '50%';
        centerText.style.transform = 'translate(-50%, -50%)';
        centerText.style.textAlign = 'center';
        centerText.style.pointerEvents = 'none';
        centerText.style.zIndex = '10';
        centerText.style.backgroundColor = 'rgba(255,255,255,0.9)';
        centerText.style.borderRadius = '50%';
        centerText.style.padding = isMobile ? '5px' : '10px';
        centerText.style.minWidth = isMobile ? '55px' : '80px';
        centerText.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
        
        const isHigh = riskLevel === 'High';
        const mainColor = isHigh ? '#e91e63' : '#2e7d32';
        const bgColor   = isHigh ? 'rgba(255,240,243,0.95)' : 'rgba(240,255,244,0.95)';
        centerText.style.backgroundColor = bgColor;
        centerText.style.border = `2px solid ${mainColor}30`;
        centerText.innerHTML = `
            <div style="font-size: ${fontSize}; font-weight: 700; color: ${mainColor}; line-height: 1.1;">
                ${dominantPercent}%
            </div>
            <div style="font-size: ${subFontSize}; color: ${mainColor}cc; margin-top: 3px; font-weight: 600; letter-spacing: 0.02em;">
                ${isHigh ? 'VISOK' : 'NIZAK'}
            </div>
            <div style="font-size: calc(${subFontSize} * 0.85); color: #9e8a8f; margin-top: 1px;">
                rizik
            </div>
        `;
    }
    
    // RAG preporuke - RAG recommendations
    const ragDiv = document.getElementById('rag-recommendations');
    if (ragDiv) {
        ragDiv.innerHTML = ragText ? ragText.replace(/\n/g, '<br>') : '<p>Nema dodatnih preporuka za prikaz.</p>';
    }

    // Personalizovani prikaz parametara
    if (inputData) {
        renderParameterGauges(inputData, riskLevel);
    }
}


// ============================================================
// PERSONALIZOVANI VIZUALNI PRIKAZ PARAMETARA PACIJENTICE
// ============================================================

function renderParameterGauges(inputData, riskLevel) {
    const container = document.getElementById('parameter-gauges');
    if (!container) return;

    // Klinički referentni rasponi i klasifikacije
    const params = [
        {
            key: 'glukoza_u_krvi',
            label: 'Glukoza u krvi',
            unit: 'mmol/L',
            icon: '🩸',
            min: 2, max: 20,
            zones: [
                { from: 2,    to: 3.9,  label: 'Niska',          color: '#64b5f6', textColor: '#1565c0' },
                { from: 3.9,  to: 5.5,  label: 'Normalna',       color: '#81c784', textColor: '#2e7d32' },
                { from: 5.5,  to: 7.8,  label: 'Blago povišena',       color: '#ffb74d', textColor: '#e65100' },
                { from: 7.8,  to: 11.0, label: 'Visoka',         color: '#ef9a9a', textColor: '#b71c1c' },
                { from: 11.0, to: 20,   label: 'Kritična',       color: '#e91e63', textColor: '#880e4f' }
            ]
        },
        {
            key: 'sistolicki_krvni_tlak',
            label: 'Sistolički pritisak',
            unit: 'mmHg',
            icon: '💓',
            min: 70, max: 200,
            zones: [
                { from: 70,  to: 120, label: 'Optimalan',        color: '#81c784', textColor: '#2e7d32' },
                { from: 120, to: 130, label: 'Normalan',         color: '#a5d6a7', textColor: '#388e3c' },
                { from: 130, to: 140, label: 'Normalno visok',   color: '#ffcc80', textColor: '#e65100' },
                { from: 140, to: 160, label: 'Blaga hiper.',     color: '#ffb74d', textColor: '#bf360c' },
                { from: 160, to: 180, label: 'Umjerena hiper.',  color: '#ef9a9a', textColor: '#b71c1c' },
                { from: 180, to: 200, label: 'Teška hiper.',     color: '#e91e63', textColor: '#880e4f' }
            ]
        },
        {
            key: 'dijastolicki_krvni_tlak',
            label: 'Dijastolički pritisak',
            unit: 'mmHg',
            icon: '💗',
            min: 40, max: 130,
            zones: [
                { from: 40, to: 80,  label: 'Optimalan',         color: '#81c784', textColor: '#2e7d32' },
                { from: 80, to: 85,  label: 'Normalan',          color: '#a5d6a7', textColor: '#388e3c' },
                { from: 85, to: 90,  label: 'Normalno visok',    color: '#ffcc80', textColor: '#e65100' },
                { from: 90, to: 100, label: 'Blaga hiper.',      color: '#ffb74d', textColor: '#bf360c' },
                { from: 100,to: 110, label: 'Umjerena hiper.',   color: '#ef9a9a', textColor: '#b71c1c' },
                { from: 110,to: 130, label: 'Teška hiper.',      color: '#e91e63', textColor: '#880e4f' }
            ]
        },
        {
            key: 'BMI',
            label: 'BMI',
            unit: 'kg/m²',
            icon: '⚖️',
            min: 14, max: 45,
            zones: [
                { from: 14,   to: 18.5, label: 'Pothranjenost',  color: '#64b5f6', textColor: '#1565c0' },
                { from: 18.5, to: 25,   label: 'Normalan',       color: '#81c784', textColor: '#2e7d32' },
                { from: 25,   to: 30,   label: 'Prekomjeran',    color: '#ffcc80', textColor: '#e65100' },
                { from: 30,   to: 35,   label: 'Gojaznost I',    color: '#ffb74d', textColor: '#bf360c' },
                { from: 35,   to: 40,   label: 'Gojaznost II',   color: '#ef9a9a', textColor: '#b71c1c' },
                { from: 40,   to: 45,   label: 'Gojaznost III',  color: '#e91e63', textColor: '#880e4f' }
            ]
        },
        {
            key: 'otkucaji_srca',
            label: 'Otkucaji srca',
            unit: 'bpm',
            icon: '❤️',
            min: 40, max: 150,
            zones: [
                { from: 40,  to: 60,  label: 'Bradikardija',     color: '#64b5f6', textColor: '#1565c0' },
                { from: 60,  to: 100, label: 'Normalan',         color: '#81c784', textColor: '#2e7d32' },
                { from: 100, to: 120, label: 'Blaga tahikardija',color: '#ffcc80', textColor: '#e65100' },
                { from: 120, to: 150, label: 'Tahikardija',      color: '#ef9a9a', textColor: '#b71c1c' }
            ]
        },
        {
            key: 'tjelesna_temp',
            label: 'Tjelesna temperatura',
            unit: '°C',
            icon: '🌡️',
            min: 35, max: 40,
            decimals: 1,
            zones: [
                { from: 35,   to: 36.0, label: 'Niska',          color: '#64b5f6', textColor: '#1565c0' },
                { from: 36.0, to: 37.5, label: 'Normalna',       color: '#81c784', textColor: '#2e7d32' },
                { from: 37.5, to: 38.0, label: 'Subfebrilan',    color: '#ffcc80', textColor: '#e65100' },
                { from: 38.0, to: 40,   label: 'Febrilna',       color: '#ef9a9a', textColor: '#b71c1c' }
            ]
        }
    ];

    function getZone(value, zones) {
        for (const z of zones) {
            if (value >= z.from && value < z.to) return z;
        }
        return zones[zones.length - 1];
    }

    function getBarPercent(value, min, max) {
        return Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
    }

    function buildZoneGradient(zones, min, max) {
        const stops = zones.map(z => {
            const startPct = ((z.from - min) / (max - min)) * 100;
            const endPct   = ((z.to   - min) / (max - min)) * 100;
            return `${z.color} ${startPct.toFixed(1)}%, ${z.color} ${endPct.toFixed(1)}%`;
        });
        return `linear-gradient(to right, ${stops.join(', ')})`;
    }

    let html = `
        <div style="
            margin-top: 2rem;
            background: linear-gradient(135deg, #fff8fa, #fff0f5);
            border-radius: 18px;
            padding: 1.5rem 1.5rem 1rem;
            border: 1px solid #fce4ec;
            box-shadow: 0 4px 20px rgba(233,30,99,0.07);
        ">
            <h3 style="
                margin: 0 0 0.3rem 0;
                color: #ad1457;
                font-size: 1.1rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <i class="fas fa-chart-bar" style="color:#e91e63;"></i>
                Vaši parametri u kliničkom kontekstu
            </h3>
            <p style="margin: 0 0 1.2rem 0; font-size: 0.82rem; color: #9e6374;">
                Svaka traka prikazuje gdje se vaša vrijednost nalazi unutar kliničkih raspona.
            </p>
            <div style="display: flex; flex-direction: column; gap: 1rem;">
    `;

    for (const param of params) {
        const value = inputData[param.key];
        if (value === undefined || value === null || isNaN(value)) continue;

        const zone    = getZone(value, param.zones);
        const pct     = getBarPercent(value, param.min, param.max);
        const gradient = buildZoneGradient(param.zones, param.min, param.max);
        const decimals = param.decimals || 0;

        html += `
            <div style="display: flex; flex-direction: column; gap: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-size: 0.85rem; font-weight: 600; color: #6d2b47;">
                        ${param.icon} ${param.label}
                    </span>
                    <span style="
                        font-size: 0.9rem;
                        font-weight: 700;
                        color: ${zone.textColor};
                        background: ${zone.color}30;
                        border: 1px solid ${zone.color};
                        padding: 1px 8px;
                        border-radius: 20px;
                    ">
                        ${value.toFixed(decimals)} ${param.unit}
                        <span style="font-size: 0.72rem; font-weight: 500; margin-left: 4px; opacity: 0.85;">
                            · ${zone.label}
                        </span>
                    </span>
                </div>

                <div style="position: relative; height: 18px; border-radius: 9px; overflow: visible;">
                    <!-- Zona pozadina -->
                    <div style="
                        position: absolute; inset: 0;
                        border-radius: 9px;
                        background: ${gradient};
                        opacity: 0.35;
                    "></div>
                    <!-- Zona puna traka do vrijednosti -->
                    <div style="
                        position: absolute; top: 0; left: 0; bottom: 0;
                        width: ${pct.toFixed(1)}%;
                        border-radius: 9px;
                        background: ${gradient};
                        background-size: ${(100 / pct * 100).toFixed(1)}% 100%;
                        transition: width 0.8s cubic-bezier(.4,0,.2,1);
                    "></div>
                    <!-- Marker igla -->
                    <div style="
                        position: absolute;
                        top: -4px; bottom: -4px;
                        left: calc(${pct.toFixed(1)}% - 2px);
                        width: 4px;
                        background: ${zone.textColor};
                        border-radius: 2px;
                        box-shadow: 0 0 6px ${zone.color};
                        transition: left 0.8s cubic-bezier(.4,0,.2,1);
                        z-index: 2;
                    "></div>
                </div>

                <!-- Zone legenda -->
                <div style="display: flex; gap: 4px; flex-wrap: wrap; margin-top: 1px;">
                    ${param.zones.map(z => `
                        <span style="
                            font-size: 0.65rem;
                            padding: 1px 6px;
                            border-radius: 10px;
                            background: ${z.color}25;
                            color: ${z.textColor};
                            border: 1px solid ${z.color}60;
                            white-space: nowrap;
                        ">${z.label}: ${z.from}${z === param.zones[param.zones.length-1] ? '+' : '–'+z.to}</span>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Binarni parametri — checkboxovi
    const binaryParams = [
        { key: 'dijabetes',                label: 'Dijagnoza dijabetesa',            icon: '💉' },
        { key: 'gestacijski_dijabetes',    label: 'Gestacijski dijabetes',           icon: '🤰' },
        { key: 'komplikacije_u_proslosti', label: 'Komplikacije u prošlosti',        icon: '📋' },
        { key: 'mentalno_zdravlje',        label: 'Problemi s mentalnim zdravljem',  icon: '🧠' }
    ];

    const activeBinary = binaryParams.filter(p => inputData[p.key] === 1);
    const inactiveBinary = binaryParams.filter(p => inputData[p.key] === 0);

    html += `
        <div style="
            margin-top: 0.6rem;
            padding-top: 0.8rem;
            border-top: 1px solid #fce4ec;
            display: flex; flex-wrap: wrap; gap: 0.5rem;
        ">
    `;
    for (const p of binaryParams) {
        const active = inputData[p.key] === 1;
        html += `
            <div style="
                display: flex; align-items: center; gap: 6px;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.78rem;
                font-weight: 600;
                background: ${active ? '#fce4ec' : '#f1f8e9'};
                color: ${active ? '#c2185b' : '#558b2f'};
                border: 1px solid ${active ? '#f48fb1' : '#aed581'};
            ">
                ${p.icon}
                ${p.label}:
                <strong>${active ? 'Da ⚠️' : 'Ne ✓'}</strong>
            </div>
        `;
    }

    html += `</div></div></div>`;

    container.innerHTML = html;
}

// Dodaj event listener za resize prozora da se chart prilagodi (dodajte na kraj script.js) - Add event listener for window resize to adjust the chart (add at the end of script.js)
window.addEventListener('resize', function() {
    if (riskChart) {
        const isMobile = window.innerWidth < 768;
        riskChart.config.options.cutout = isMobile ? '60%' : '65%';
        riskChart.config.options.plugins.legend.labels.font.size = isMobile ? 10 : 12;
        riskChart.config.options.plugins.legend.labels.padding = isMobile ? 10 : 15;
        riskChart.update();
    }
    
    // Ažuriraj centralni tekst na pie chart-u - Update central text on pie chart
    const centerTextElem = document.getElementById('chart-center-text');
    if (centerTextElem) {
        const isMobileResize = window.innerWidth < 768;
        const fontSize = isMobileResize ? '1rem' : '1.5rem';
        const subFontSize = isMobileResize ? '0.55rem' : '0.7rem';
        const padding = isMobileResize ? '5px' : '10px';
        const minWidth = isMobileResize ? '55px' : '80px';
        
        centerTextElem.style.padding = padding;
        centerTextElem.style.minWidth = minWidth;
        
        const titleDiv = centerTextElem.querySelector('div:first-child');
        const subtitleDiv = centerTextElem.querySelector('div:last-child');
        if (titleDiv) titleDiv.style.fontSize = fontSize;
        if (subtitleDiv) subtitleDiv.style.fontSize = subFontSize;
    }
    
});

// Sačuvaj zadnju predikciju za feedback - Save last prediction for feedback
function saveLastPrediction(riskData, inputData) {
    lastPredictionData = {
        risk_level: riskData.risk_level,
        input_data: inputData,
        timestamp: new Date().toISOString()
    };
    localStorage.setItem('lastPrediction', JSON.stringify(lastPredictionData));
}

// Slanje feedback-a na backend - Send feedback to backend
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
        
        // SAMO SAKRIJ PORUKU NAKON 5 SEKUNDI, NE RESETUJ FORMU! - ONLY HIDE THE MESSAGE AFTER 5 SECONDS, DO NOT RESET THE FORM!
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

// Učitaj statistiku feedback sistema - Load feedback system statistics
async function loadFeedbackStats() {
    try {
        const response = await fetch(`${API_BASE}/feedback/stats`);
        if (response.ok) {
            const stats = await response.json();
            const statsDiv = document.getElementById('feedback-stats');
            const statsText = document.getElementById('stats-text');
            
            if (stats.total_feedback > 0 && statsText) {
                statsText.innerHTML = `Prikupljeno ${stats.total_feedback} povratnih informacija. ${stats.agreed_with_model} korisnika se složilo, ${stats.disagreed_with_model} nije.`;
                if (statsDiv) statsDiv.style.display = 'block';
            }
        }
    } catch (err) {
        console.warn('Nije moguće učitati statistiku feedback-a:', err);
    }
}



async function submitAssessment(event) {
    // 1. Primarna zaštita od osvježavanja stranice i duplih okidanja - Primary protection against page refresh and double triggers
    if (event) {
        event.preventDefault();
        event.stopPropagation(); 
    }

    console.log('submitAssessment pozvana');
    
    // Resetuj prethodne greške u UI-u ako postoje - Reset previous errors in the UI if they exist
    const existingErr = document.getElementById('api-error-banner');
    if (existingErr) existingErr.remove();

    // 2. Provjera validacije formi prije slanja - Check form validation before submission
    if (!validateForm()) {
        console.log('Validacija nije prošla');
        return;
    }
    
    // Prikaži loading animaciju - Show loading animation
    showLoading(true);

    const payload = getFormData();
    
    // Provjera integriteta podataka (Missing fields check) - Data integrity check (Missing fields check)
    const requiredFields = ['dob', 'sistolicki_krvni_tlak', 'dijastolicki_krvni_tlak', 
                            'glukoza_u_krvi', 'tjelesna_temp', 'BMI', 'otkucaji_srca'];
    
    const missing = requiredFields.filter(f => payload[f] === undefined || payload[f] === null || isNaN(payload[f]));
    if (missing.length > 0) {
        console.error('Nedostaju polja:', missing);
        alert(`Molimo popunite sva polja: ${missing.join(', ')}`);
        showLoading(false);
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
        
        // 3. KLJUČNI DIO: Sigurna navigacija na rezultate - KEY PART: Safe navigation to results
        // Sakrivamo SVE što bi moglo smetati - Hide ALL that could interfere
        heroSection.style.display = 'none';
        stalSection.style.display = 'none'; // Osiguranje ako je korisnik došao sa "Kako radi" - Ensure if user came from "How it works" section
        
        // Prikazujemo glavni kontejner i sekciju rezultata - Show main container and results section
        appMain.style.display = 'block';
        form.style.display = 'none'; // Sakrij formu unutar appMain da ne ostane prazna sekcija
        const formSubtitle = document.getElementById('form-subtitle');
        if (formSubtitle) formSubtitle.style.display = 'none';
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
        
        // Skroluj na vrh da korisnik vidi nivo rizika - Scroll to top so user sees the risk level
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
    } catch (err) {
        console.error('❌ Greška:', err);
        
        let errorMsg = err.message.includes('fetch') || err.message.includes('Failed to fetch')
            ? 'Server nije dostupan. Proverite da li je Python backend pokrenut.'
            : err.message;
        
        // U slučaju greške, vrati korisnika na formu da može probati opet - In case of error, return user to the form so they can try again
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
        // Obavezno sakrij loading bez obzira na ishod - Always hide loading regardless of outcome
        showLoading(false);
    }
}

// Reset forme i povratak na formu nakon pregleda rezultata - Reset form and return to form after viewing results
function resetAndShowForm() {
    heroSection.style.display = 'none';
    appMain.style.display = 'block';
    form.reset();
    const errorSpans = document.querySelectorAll('.error-message');
    errorSpans.forEach(span => span.innerText = '');
    form.style.display = 'block';
    const formSubtitleReset = document.getElementById('form-subtitle');
    if (formSubtitleReset) formSubtitleReset.style.display = 'block';
    resultsSection.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}


// ============================================================
// SENSE - THINK - ACT - LEARN CIKLUS
// ============================================================

// Opisi za svaku fazu - Descriptions for each phase
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
        title: "THINK - Analiza i predikcija",
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
        description: "Sistem uči iz svake interakcije. Korisnici daju povratnu informaciju o tačnosti predikcije, što se čuva u bazi. Administrator može pokrenuti poboljšanje modela jednim klikom na dugme.",
        details: [
            "Feedback sistem prikuplja povratne informacije",
            "Podaci se čuvaju u zasebnom fajlu za retraining",
            "Retraining se pokreće jednim klikom",
            "Model se kontinuirano poboljšava kroz vrijeme"
        ]
    }
};

// Prikaz statusa retraining-a - Display retraining status
function showRetrainingStatus(show, message = '') {
    const statusDiv = document.getElementById('retraining-status');
    const messageSpan = document.getElementById('retraining-message');
    if (statusDiv) {
        if (show) {
            statusDiv.style.display = 'block';
            if (messageSpan) messageSpan.innerHTML = message;
        } else {
            statusDiv.style.display = 'none';
        }
    }
}

// Dugme za retraining - Button for retraining
document.getElementById('retrain-btn')?.addEventListener('click', triggerRetraining);

// Ručno pokreni retraining - Manually trigger retraining
async function triggerRetraining() {
    showRetrainingStatus(true, 'Pokrećem poboljšanje modela... Molimo sačekajte.');
    
    try {
        const response = await fetch(`${API_BASE}/feedback/retrain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force: true })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showRetrainingStatus(true, `Retraining uspješan! Novi accuracy: ${(result.accuracy * 100).toFixed(2)}%`);
            
            // Sakrij poruku nakon 5 sekundi - Hide message after 5 seconds
            setTimeout(() => {
                showRetrainingStatus(false);
            }, 50000);
            
            // Osvježi statistiku - Refresh statistics
            await loadFeedbackStats();
            await loadStalStats();
            
        } else {
            showRetrainingStatus(true, `⚠️ ${result.message}`);
            setTimeout(() => {
                showRetrainingStatus(false);
            }, 3000);
        }
    } catch (err) {
        console.error('Retraining greška:', err);
        showRetrainingStatus(true, '❌ Greška pri poboljšanju modela');
        setTimeout(() => {
            showRetrainingStatus(false);
        }, 3000);
        showRetrainingStatus(true, '<i class="fas fa-times-circle" style="color:#e91e63"></i> Greška pri poboljšanju modela.');
        setTimeout(() => showRetrainingStatus(false), 4000);
    }
}

// Inicijalizacija STAL ciklusa - Initialization of the STAL cycle
function initStalCycle() {
    const steps = document.querySelectorAll('.cycle-step');
    const descriptionDiv = document.getElementById('cycle-description');
    
    if (!steps.length || !descriptionDiv) return;
    
    // Postavi default opis (Sense) - Set default description (Sense)
    updateCycleDescription('sense');
    
    // Dodaj event listenere za svaki korak - Add event listeners for each step
    steps.forEach(step => {
        step.addEventListener('click', function() {
            const stepName = this.getAttribute('data-step');
            updateCycleDescription(stepName);
            
            // Vizuelno označi aktivni korak - Visually highlight the active step
            steps.forEach(s => s.style.background = '#ffe0e8');
            this.style.background = '#f0629240';
            this.style.transform = 'scale(1.02)';
            
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 200);
        });
        
        // Hover efekat - Hover effect
        step.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.transition = 'all 0.2s ease';
        });
        step.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Ažuriraj prikaz opisa za odabranu fazu - Update the description display for the selected phase
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

// Dodaj STAL statistiku (broj feedbackova, verzija modela, itd.) - Add STAL statistics (number of feedbacks, model version, etc.)
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
// INICIJALIZACIJA — svi event listeneri registrovani JEDNOM, unutar DOMContentLoaded kako bi DOM bio siguran dostupan 
// INITIALIZATION — all event listeners registered ONCE, within DOMContentLoaded to ensure DOM is safely accessible
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

    // 1. Inicijalni prikaz — forma vidljiva, rezultati skriveni - Initial display — form visible, results hidden
    form.style.display = 'block';
    const formSubtitleReset = document.getElementById('form-subtitle');
    if (formSubtitleReset) formSubtitleReset.style.display = 'block';
    resultsSection.style.display = 'none';

    // 2. Provjera API statusa i učitavanje statistike feedback sistema - Check API status and load feedback system statistics
    checkAPIStatus();
    setupNumericInputValidation();
    loadFeedbackStats();

    console.log('App inicijalizovan!');

    // 3. Forma — jedinstven submit listener, sprječava page reload i duplu obradu - Form — single submit listener, prevents page reload and double processing
    form.onsubmit = null; // ukloni eventualne inline handlere - remove any inline handlers
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        e.stopPropagation();
        submitAssessment();
    });

    // Reset dugme na formi - Reset button on the form - dodaj event listener da očisti greške - add event listener to clear errors
    form.addEventListener('reset', function() {
        setTimeout(() => {
            document.querySelectorAll('.error-message')
                .forEach(span => span.innerText = '');
        }, 10);
    });

    // 4. Navigacija — "Započni putovanje" (STAL) - Navigation — "Start the journey" (STAL)
    startBtn?.addEventListener('click', (e) => {
        e.preventDefault();
        heroSection.style.display = 'none';
        appMain.style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // 5. Navigacija — "Kako Gestatix radi?" (STAL) - Navigation — "How does Gestatix work?" (STAL)
    howItWorksBtn?.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        heroSection.style.display = 'none';
        appMain.style.display = 'none';
        stalSection.style.display = 'block';
        initStalCycle();
        loadStalStats();
    });

    // 6. Povratak na početnu sa forme rezultata - Return to home from results form
    backBtn?.addEventListener('click', () => {
        appMain.style.display = 'none';
        heroSection.style.display = 'flex';
    });

    // 7. Povratak na početnu sa STAL stranice - Return to home from STAL page
    backToHeroFromStal?.addEventListener('click', () => {
        stalSection.style.display = 'none';
        heroSection.style.display = 'flex';
    });

    // 8. Nova procjena - Reset forme i povratak na formu nakon pregleda rezultata - New assessment - Reset form and return to form after viewing results
    newAssessmentBtn?.addEventListener('click', resetAndShowForm);

    // 9. Toggle RAG preporuke - Toggle RAG recommendations
    toggleRagBtn?.addEventListener('click', () => {
        const isHidden = ragContent.style.display === 'none';
        ragContent.style.display = isHidden ? 'block' : 'none';
        toggleRagBtn.innerHTML = isHidden
            ? '<i class="fas fa-book-open"></i> Sakrij preporuke'
            : '<i class="fas fa-book-open"></i> Saznaj više – Preporuke iz vodiča';
    });

    // 10. Feedback dugmad - Feedback buttons
    document.getElementById('feedback-yes')?.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        sendFeedback(true);
    });

    document.getElementById('feedback-no')?.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const correctRisk = confirm('Da li je tačan rizik "Low" (Nizak) ili "High" (Visok)?\n\nPritisnite OK za "High", Cancel za "Low"');
        sendFeedback(false, correctRisk ? 'High' : 'Low');
    });

});