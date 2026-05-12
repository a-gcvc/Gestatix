// script.js

// API base URL - mijenjaj po potrebi
const API_BASE = 'http://localhost:5000';

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

// Helper: Prikaz/ sakrivanje loadinga
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Funkcija za zamjenu zareza sa tačkama u numeričkim poljima
function sanitizeNumericInput(value) {
    if (typeof value !== 'string') return value;
    // Zamijeni zarez sa tačkom
    return value.replace(',', '.');
}

// Dodaj event listenere za sva numerička polja da spriječe unos zareza
function setupNumericInputValidation() {
    const numericInputs = ['dob', 'height', 'weight', 'systolic', 'diastolic', 'glucose', 'temperature', 'heart_rate'];
    
    numericInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            // On input - zamijeni zarez sa tačkom
            input.addEventListener('input', function(e) {
                if (this.value.includes(',')) {
                    this.value = this.value.replace(',', '.');
                }
            });
            
            // On blur (kada napusti polje) - dodatna validacija
            input.addEventListener('blur', function(e) {
                if (this.value.includes(',')) {
                    this.value = this.value.replace(',', '.');
                }
                // Provjeri da li je validan broj
                if (this.value && !isNaN(parseFloat(this.value))) {
                    this.value = parseFloat(this.value).toString();
                }
            });
            
            // On keypress - spriječi unos zareza
            input.addEventListener('keypress', function(e) {
                if (e.key === ',') {
                    e.preventDefault();
                    // Umjesto zareza, ubaci tačku
                    const start = this.selectionStart;
                    const end = this.selectionEnd;
                    const value = this.value;
                    this.value = value.slice(0, start) + '.' + value.slice(end);
                    this.setSelectionRange(start + 1, start + 1);
                }
            });
        }
    });
}

// Izmijenjena sanitizacija podataka prije slanja
function sanitizeFormData() {
    const numericFields = ['dob', 'height', 'weight', 'systolic', 'diastolic', 'glucose', 'temperature', 'heart_rate'];
    
    numericFields.forEach(id => {
        const input = document.getElementById(id);
        if (input && input.value) {
            // Zamijeni zarez sa tačkom
            let value = input.value.replace(',', '.');
            input.value = value;
        }
    });
}

// Validacija forme prije slanja
function validateForm() {
    let isValid = true;
    
    // Prvo sanitiziraj sve numeričke unose
    sanitizeFormData();
    
    const fields = {
        dob: { element: document.getElementById('dob'), min: 15, max: 60, name: 'Dob', required: true },
        height: { element: document.getElementById('height'), min: 100, max: 220, name: 'Visina', required: true },
        weight: { element: document.getElementById('weight'), min: 30, max: 200, name: 'Težina', required: true },
        systolic: { element: document.getElementById('systolic'), min: 70, max: 200, name: 'Sistolicki pritisak', required: true },
        diastolic: { element: document.getElementById('diastolic'), min: 40, max: 130, name: 'Dijastolicki pritisak', required: true },
        glucose: { element: document.getElementById('glucose'), min: 2, max: 20, name: 'Glukoza', required: true },
        temperature: { element: document.getElementById('temperature'), min: 35, max: 40, name: 'Temperatura', required: true },
        heart_rate: { element: document.getElementById('heart_rate'), min: 50, max: 150, name: 'Otkucaji srca', required: true }
    };
    
    // Validacija brojčanih polja
    for (let [key, f] of Object.entries(fields)) {
        if (!f.element) continue;
        
        // Zamijeni zarez sa tačkom ako postoji
        let rawValue = f.element.value;
        if (rawValue.includes(',')) {
            rawValue = rawValue.replace(',', '.');
            f.element.value = rawValue;
        }
        
        const val = parseFloat(rawValue);
        const errorSpan = document.getElementById(`${key}-error`);
        
        if (isNaN(val)) {
            if (errorSpan) errorSpan.innerText = `Unesite ${f.name}`;
            isValid = false;
        } else if (val < f.min || val > f.max) {
            if (errorSpan) errorSpan.innerText = `${f.name} mora biti između ${f.min} i ${f.max}`;
            isValid = false;
        } else {
            if (errorSpan) errorSpan.innerText = '';
            // Postavi formatiranu vrijednost bez zareza
            f.element.value = val.toString();
        }
    }
    
    // Validacija select polja
    const selects = ['complications', 'diabetes', 'gdm', 'mental'];
    for (let s of selects) {
        const element = document.getElementById(s);
        const errorSpan = document.getElementById(`${s}-error`);
        
        const val = element ? element.value : null;
        if (!val || (val !== '0' && val !== '1')) {
            if (errorSpan) errorSpan.innerText = 'Obavezno polje';
            isValid = false;
        } else {
            if (errorSpan) errorSpan.innerText = '';
        }
    }
    
    return isValid;
}

// Izračunaj BMI na osnovu visine (cm) i težine (kg)
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
    
    console.log('Visina:', height, 'Težina:', weight, 'BMI:', bmi);
    
    // Helper funkcija za sigurno parsiranje brojeva
    function parseNumericValue(id, defaultValue = 0) {
        const element = document.getElementById(id);
        if (!element) return defaultValue;
        let value = element.value;
        value = value.replace(',', '.');
        const parsed = parseFloat(value);
        return isNaN(parsed) ? defaultValue : parsed;
    }
    
    function parseIntValue(id, defaultValue = 0) {
        return Math.round(parseNumericValue(id, defaultValue));
    }
    
    const data = {
        dob: parseIntValue('dob'),
        sistolicki_krvni_tlak: parseIntValue('systolic'),
        dijastolicki_krvni_tlak: parseIntValue('diastolic'),
        glukoza_u_krvi: parseNumericValue('glucose'),
        tjelesna_temp: parseNumericValue('temperature'),
        BMI: parseFloat(bmi.toFixed(1)),
        komplikacije_u_proslosti: parseInt(document.getElementById('complications').value),
        dijabetes: parseInt(document.getElementById('diabetes').value),
        gestacijski_dijabetes: parseInt(document.getElementById('gdm').value),
        mentalno_zdravlje: parseInt(document.getElementById('mental').value),
        otkucaji_srca: parseIntValue('heart_rate')
    };
    
    console.log('Podaci za slanje:', data);
    return data;
}

// Prikaz rezultata i grafika
// Prikaz rezultata i grafika
function displayResults(riskData, ragText) {
    console.log('Prikazujem rezultate:', riskData);
    
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
        if (riskTextSpan) riskTextSpan.innerHTML = `Nivo rizika: <strong style="color:#2e7d32">NISKOG RIZIKA</strong>`;
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
    
    // Bar chart
    const ctx2 = document.getElementById('featureChart');
    if (ctx2) {
        if (featureChart) featureChart.destroy();
        featureChart = new Chart(ctx2.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Glukoza', 'Dijabetes', 'BMI', 'Krvni pritisak', 'Otkucaji srca'],
                datasets: [{
                    label: 'Utjecaj na rizik (%)',
                    data: [35, 28, 18, 12, 7],
                    backgroundColor: '#f06292'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });
    }
    
    // RAG preporuke
    const ragDiv = document.getElementById('rag-recommendations');
    if (ragDiv) {
        ragDiv.innerHTML = ragText ? ragText.replace(/\n/g, '<br>') : '<p>Nema dodatnih preporuka za prikaz.</p>';
    }
}

// Slanje zahtjeva ka API-ju
// Slanje zahtjeva ka API-ju
async function submitAssessment() {
    console.log('submitAssessment pozvana');
    
    if (!validateForm()) {
        console.log('Validacija nije prošla');
        return;
    }
    
    showLoading(true);
    const payload = getFormData();
    console.log('Podaci za slanje:', payload);

    try {
        const response = await fetch(`${API_BASE}/predict_with_rag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API greška:', errorText);
            throw new Error(`API greška: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Rezultat od API-ja:', result);
        
        const risk = result.risk;
        const ragRecommendations = result.rag_recommendations || 'Nema dodatnih preporuka.';
        
        // Sakrij formu, prikaži rezultate
        form.style.display = 'none';
        resultsSection.style.display = 'block';
        
        displayResults(risk, ragRecommendations);
        
    } catch (err) {
        console.error('Greška:', err);
        alert('Došlo je do greške: ' + err.message);
    } finally {
        showLoading(false);
    }
}

// Reset forme i povratak na formu
function resetAndShowForm() {
    form.reset();
    // Očisti sve error poruke
    const errorSpans = document.querySelectorAll('.error-message');
    errorSpans.forEach(span => span.innerText = '');
    form.style.display = 'block';
    resultsSection.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Event listeneri
startBtn.addEventListener('click', () => {
    heroSection.style.display = 'none';
    appMain.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
});
backBtn.addEventListener('click', () => {
    appMain.style.display = 'none';
    heroSection.style.display = 'flex';
});
newAssessmentBtn.addEventListener('click', resetAndShowForm);
toggleRagBtn.addEventListener('click', () => {
    if (ragContent.style.display === 'none') {
        ragContent.style.display = 'block';
        toggleRagBtn.innerHTML = '<i class="fas fa-book-open"></i> Sakrij preporuke';
    } else {
        ragContent.style.display = 'none';
        toggleRagBtn.innerHTML = '<i class="fas fa-book-open"></i> Saznaj više – Preporuke iz vodiča';
    }
});

// Inicijalno stanje
form.style.display = 'block';
resultsSection.style.display = 'none';
        // Opciono: slanje feedback podataka (ne automatski, ostaviti korisniku opciju)


// SUBMIT FORME - ISPRAVLJENO
form.addEventListener('submit', function(event) {
    event.preventDefault();  // SPRJEČAVA REFRESH STRANICE
    event.stopPropagation(); // SPRJEČAVA PROPAGACIJU DOGADJAJA
    console.log('Forma poslata, validacija...');
    submitAssessment();
});

// Reset dugme
form.addEventListener('reset', function() {
    // Očisti sve error poruke
    setTimeout(() => {
        const errorSpans = document.querySelectorAll('.error-message');
        errorSpans.forEach(span => span.innerText = '');
    }, 10);
});

// Inicijalno stanje
form.style.display = 'block';
resultsSection.style.display = 'none';

// Postavi validaciju numeričkih polja
setupNumericInputValidation();

console.log('App inicijalizovan!');
