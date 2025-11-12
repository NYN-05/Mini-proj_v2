const form = document.getElementById('phishingForm');
const emailInput = document.getElementById('emailInput');
const detectBtn = document.getElementById('detectBtn');
const btnSpinner = document.getElementById('btnSpinner');
const btnText = document.getElementById('btnText');
const loadingMsg = document.getElementById('loadingMsg');
const resultsDiv = document.getElementById('results');
const resultsPlaceholder = document.getElementById('resultsPlaceholder');
const counts = document.getElementById('counts');

const fileInput = document.getElementById('fileInput');
const chooseFileBtn = document.getElementById('chooseFileBtn');
const dropZone = document.getElementById('dropZone');
const fileName = document.getElementById('fileName');

function updateCounts() {
  const text = emailInput.value || '';
  const chars = text.length;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  counts.textContent = `${chars} characters • ${words} words`;
}

emailInput.addEventListener('input', updateCounts);

// File chooser
chooseFileBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
  const f = e.target.files[0];
  if (!f) return;
  fileName.textContent = `📄 ${f.name}`;
  fileName.style.display = 'block';
  const reader = new FileReader();
  reader.onload = (ev) => { emailInput.value = ev.target.result; updateCounts(); };
  reader.readAsText(f);
});

// Drag & drop
['dragenter','dragover'].forEach(ev => dropZone.addEventListener(ev, (e) => { e.preventDefault(); e.stopPropagation(); dropZone.classList.add('dragover'); }));
['dragleave','drop'].forEach(ev => dropZone.addEventListener(ev, (e) => { e.preventDefault(); e.stopPropagation(); dropZone.classList.remove('dragover'); }));
dropZone.addEventListener('drop', (e) => {
  const f = e.dataTransfer.files && e.dataTransfer.files[0];
  if (!f) return;
  fileInput.files = e.dataTransfer.files;
  fileName.textContent = `📄 ${f.name}`;
  fileName.style.display = 'block';
  const reader = new FileReader();
  reader.onload = (ev) => { emailInput.value = ev.target.result; updateCounts(); };
  reader.readAsText(f);
});

function showLoading(on=true){
  if(on){
    detectBtn.setAttribute('disabled','disabled');
    btnSpinner.style.display = 'inline-block';
    btnText.style.display = 'none';
    loadingMsg.style.display = 'block';
  } else {
    detectBtn.removeAttribute('disabled');
    btnSpinner.style.display = 'none';
    btnText.style.display = 'inline';
    loadingMsg.style.display = 'none';
  }
}

function renderResults(data){
  resultsPlaceholder.style.display = 'none';
  resultsDiv.style.display = 'block';
  
  // Determine verdict
  let verdictClass = 'verdict-safe';
  let verdictIcon = 'fa-check-circle';
  let verdictLabel = 'SAFE';
  
  if (data.classification === 'PHISHING') { 
    verdictClass = 'verdict-phishing'; 
    verdictIcon = 'fa-exclamation-triangle';
    verdictLabel = 'HIGH RISK';
  } else if (data.classification === 'SPAM') { 
    verdictClass = 'verdict-warning'; 
    verdictIcon = 'fa-flag';
    verdictLabel = 'WARNING';
  }

  let html = '';
  
  // Main verdict badge
  html += `<div class="verdict-badge ${verdictClass}">
    <i class="fas ${verdictIcon}"></i>
    <span>${verdictLabel}</span>
  </div>`;

  // Confidence score display
  const confPercent = (data.confidence * 100).toFixed(1);
  html += `<div class="confidence-display">
    <div class="confidence-label">Detection Confidence</div>
    <div class="confidence-score">${confPercent}%</div>
  </div>`;

  // Analysis Breakdown Section
  html += `<div class="analysis-section">
    <h6 class="analysis-title"><i class="fas fa-microscope"></i> Analysis Breakdown</h6>`;
  
  // Model predictions
  if (data.model_probs) {
    html += `<div class="model-metrics">`;
    html += `<div class="metric-card">
      <div class="metric-label">Logistic Regression</div>
      <div class="metric-value">${(data.model_probs.logistic * 100).toFixed(1)}%</div>
    </div>`;
    html += `<div class="metric-card">
      <div class="metric-label">Naive Bayes</div>
      <div class="metric-value">${(data.model_probs.nb * 100).toFixed(1)}%</div>
    </div>`;
    if (data.model_probs.svm) {
      html += `<div class="metric-card">
        <div class="metric-label">SVM</div>
        <div class="metric-value">${(data.model_probs.svm * 100).toFixed(1)}%</div>
      </div>`;
    }
    html += `</div>`;
  }

  // Risk factors
  if (data.risk_factors && data.risk_factors.length){
    html += `<ul class="risk-factors-list">`;
    data.risk_factors.forEach(f => { html += `<li>${f}</li>` });
    html += `</ul>`;
  } else {
    html += `<div class="alert alert-success" role="alert"><i class="fas fa-smile-wink"></i> No strong risk indicators detected.</div>`;
  }

  html += `</div>`;

  // Detected threats & highlights
  if (data.highlighted_email) {
    html += `<div class="analysis-section">
      <h6 class="analysis-title"><i class="fas fa-highlighter"></i> Detected Threats & Highlights</h6>
      <div class="email-content">${data.highlighted_email}</div>
    </div>`;
  }

  // Recommended next steps
  html += `<div class="next-steps">
    <h6><i class="fas fa-lightbulb"></i> Recommended Next Steps</h6>
    <ol>
      <li><strong>Do not click</strong> any links or open attachments without verification.</li>
      <li><strong>Verify the sender</strong> using an official channel (phone call or institutional portal).</li>
      <li><strong>Report this email</strong> to your institution's IT/security team immediately.</li>
      <li><strong>Mark as phishing</strong> in your email client to help protect others.</li>
    </ol>
  </div>`;

  resultsDiv.innerHTML = html;
}

form.addEventListener('submit', function(e){
  e.preventDefault();
  const emailText = emailInput.value || '';
  if (!emailText.trim()){
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = `<div class="alert alert-warning" role="alert"><i class="fas fa-exclamation-circle"></i> Please paste or upload email content before analyzing.</div>`;
    return;
  }

  showLoading(true);
  resultsDiv.style.display = 'none';

  fetch('/detect', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email_text: emailText})
  }).then(r => r.json())
    .then(data => {
      showLoading(false);
      if (data.error){
        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = `<div class="alert alert-danger" role="alert"><i class="fas fa-circle-xmark"></i> ${data.error}</div>`;
        return;
      }
      renderResults(data);
    }).catch(err => {
      showLoading(false);
      resultsDiv.style.display = 'block';
      resultsDiv.innerHTML = `<div class="alert alert-danger" role="alert"><i class="fas fa-circle-xmark"></i> Error analyzing content: ${err}</div>`;
    });
});

// Initialize counts
updateCounts();
