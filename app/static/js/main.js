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

// XSS Prevention: HTML escape function
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

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
  const fileNameSpan = fileName.querySelector('.file-name');
  if (fileNameSpan) {
    fileNameSpan.textContent = f.name;
  } else {
    fileName.textContent = `📄 ${f.name}`;
  }
  fileName.style.display = 'flex';
  const reader = new FileReader();
  reader.onload = (ev) => { emailInput.value = ev.target.result; updateCounts(); };
  reader.readAsText(f);
});

// Drag & drop
['dragenter','dragover'].forEach(ev => dropZone.addEventListener(ev, (e) => { 
  e.preventDefault(); 
  e.stopPropagation(); 
  dropZone.classList.add('drag-over'); 
}));
['dragleave','drop'].forEach(ev => dropZone.addEventListener(ev, (e) => { 
  e.preventDefault(); 
  e.stopPropagation(); 
  dropZone.classList.remove('drag-over'); 
}));
dropZone.addEventListener('drop', (e) => {
  const f = e.dataTransfer.files && e.dataTransfer.files[0];
  if (!f) return;
  const fileNameSpan = fileName.querySelector('.file-name') || fileName;
  fileNameSpan.textContent = f.name;
  fileName.style.display = 'flex';
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
  
  // Normalize confidence: accept either 0-1 or 0-100 scales and strings
  let rawConf = data.confidence;
  if (typeof rawConf === 'string') {
    rawConf = parseFloat(rawConf.replace('%',''));
  }
  let confNorm = 0;
  if (typeof rawConf === 'number' && !isNaN(rawConf)) {
    confNorm = rawConf > 1 ? (rawConf / 100.0) : rawConf;
  }

  // Consider message high-risk if model classifies as PHISHING
  // or if the combined confidence meets/exceeds 40% (0.40).
  if (data.classification === 'PHISHING' || confNorm >= 0.20) {
    verdictClass = 'verdict-phishing'; 
    verdictIcon = 'fa-exclamation-triangle';
    verdictLabel = 'RISKY';
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
  const confPercent = (confNorm * 100).toFixed(1);
  html += `<div class="confidence-display">
    <div class="confidence-label">Detection Confidence</div>
    <div class="confidence-score">${confPercent}%</div>
  </div>`;

  // Analysis Breakdown Section
  html += `<div class="analysis-section">
    <h6 class="analysis-title"><i class="fas fa-microscope"></i> Analysis Breakdown</h6>`;
  
  // Model predictions - handle both pipeline and individual models
  if (data.model_probs) {
    html += `<div class="model-metrics">`;
    
    // If using pipeline (stacking classifier)
    if (data.model_probs.pipeline !== undefined) {
      html += `<div class="metric-card">
        <div class="metric-label">ML Model Score</div>
        <div class="metric-value">${(data.model_probs.pipeline * 100).toFixed(1)}%</div>
      </div>`;
    } else {
      // Individual models
      if (data.model_probs.logistic !== undefined) {
        html += `<div class="metric-card">
          <div class="metric-label">Logistic Regression</div>
          <div class="metric-value">${(data.model_probs.logistic * 100).toFixed(1)}%</div>
        </div>`;
      }
      if (data.model_probs.nb !== undefined) {
        html += `<div class="metric-card">
          <div class="metric-label">Naive Bayes</div>
          <div class="metric-value">${(data.model_probs.nb * 100).toFixed(1)}%</div>
        </div>`;
      }
      if (data.model_probs.svm !== undefined) {
        html += `<div class="metric-card">
          <div class="metric-label">SVM</div>
          <div class="metric-value">${(data.model_probs.svm * 100).toFixed(1)}%</div>
        </div>`;
      }
    }
    
    // Show additional scores if available
    if (data.urgency_score !== undefined) {
      html += `<div class="metric-card">
        <div class="metric-label">Urgency Score</div>
        <div class="metric-value">${data.urgency_score.toFixed(1)}/10</div>
      </div>`;
    }
    if (data.url_analysis && data.url_analysis.overall_url_risk > 0) {
      html += `<div class="metric-card">
        <div class="metric-label">URL Risk</div>
        <div class="metric-value">${data.url_analysis.overall_url_risk.toFixed(1)}/100</div>
      </div>`;
    }
    
    html += `</div>`;
  }

  // Risk factors
  if (data.risk_factors && data.risk_factors.length){
    html += `<ul class="risk-factors-list">`;
    // Escape risk factors to prevent XSS (though backend already escapes)
    data.risk_factors.forEach(f => { html += `<li>${escapeHtml(f)}</li>` });
    html += `</ul>`;
  } else {
    html += `<div class="alert alert-success" role="alert"><i class="fas fa-smile-wink"></i> No strong risk indicators detected.</div>`;
  }

  html += `</div>`;

  // Emotional Tone Analysis Section
  if (data.emotional_analysis) {
    const ea = data.emotional_analysis;
    const hiddenScore = ea.hidden_meaning_score || 0;
    const emotionalScores = ea.emotional_scores || {};
    const sentiment = ea.sentiment || {};
    const manipRisk = ea.manipulation_risk || {};
    const conflict = ea.emotional_conflict || {};

    html += `<div class="analysis-section emotional-analysis">
      <h6 class="analysis-title"><i class="fas fa-brain"></i> Emotional Tone Analysis</h6>`;
    
    // Hidden meaning score with visual indicator
    let hiddenScoreClass = 'low-risk';
    let hiddenScoreLabel = 'Low Risk';
    if (hiddenScore > 70) {
      hiddenScoreClass = 'critical-risk';
      hiddenScoreLabel = 'Critical Risk';
    } else if (hiddenScore > 50) {
      hiddenScoreClass = 'high-risk';
      hiddenScoreLabel = 'High Risk';
    } else if (hiddenScore > 30) {
      hiddenScoreClass = 'medium-risk';
      hiddenScoreLabel = 'Medium Risk';
    }
    
    html += `<div class="emotional-score-card">
      <div class="emotional-score-header">
        <span class="emotional-score-label">Hidden Meaning Score</span>
        <span class="emotional-score-badge ${hiddenScoreClass}">${hiddenScoreLabel}</span>
      </div>
      <div class="emotional-score-bar-container">
        <div class="emotional-score-bar ${hiddenScoreClass}" style="width: ${hiddenScore}%"></div>
      </div>
      <div class="emotional-score-value">${hiddenScore.toFixed(1)}/100</div>
    </div>`;
    
    // Emotional markers breakdown
    html += `<div class="emotional-markers">
      <h6 class="emotional-markers-title">Emotional Markers Detected</h6>
      <div class="emotional-markers-grid">`;
    
    const emotionIcons = {
      urgency: 'fa-clock',
      fear: 'fa-exclamation-triangle',
      anxiety: 'fa-user-shield',
      greed: 'fa-gift',
      deference: 'fa-user-tie',
      manipulation: 'fa-hands'
    };
    
    const emotionLabels = {
      urgency: 'Urgency',
      fear: 'Fear Tactics',
      anxiety: 'Anxiety',
      greed: 'Greed/Reward',
      deference: 'Deference',
      manipulation: 'Manipulation'
    };
    
    for (const [emotion, icon] of Object.entries(emotionIcons)) {
      if (emotionalScores[emotion]) {
        const score = emotionalScores[emotion].score || 0;
        const count = emotionalScores[emotion].count || 0;
        let markerClass = 'marker-low';
        if (score > 7) markerClass = 'marker-critical';
        else if (score > 5) markerClass = 'marker-high';
        else if (score > 3) markerClass = 'marker-medium';
        
        html += `<div class="emotional-marker-card ${markerClass}">
          <div class="marker-icon"><i class="fas ${icon}"></i></div>
          <div class="marker-label">${emotionLabels[emotion]}</div>
          <div class="marker-score">${score.toFixed(1)}/10</div>
          <div class="marker-count">${count} instance${count !== 1 ? 's' : ''}</div>
        </div>`;
      }
    }
    
    html += `</div></div>`;
    
    // Sentiment analysis
    if (sentiment.label) {
      let sentimentIcon = 'fa-minus-circle';
      let sentimentClass = 'sentiment-neutral';
      if (sentiment.label === 'positive') {
        sentimentIcon = 'fa-smile';
        sentimentClass = 'sentiment-positive';
      } else if (sentiment.label === 'negative') {
        sentimentIcon = 'fa-frown';
        sentimentClass = 'sentiment-negative';
      }
      
      html += `<div class="sentiment-card ${sentimentClass}">
        <div class="sentiment-header">
          <i class="fas ${sentimentIcon}"></i>
          <span class="sentiment-label">Sentiment: ${sentiment.label.toUpperCase()}</span>
        </div>
        <div class="sentiment-details">
          Polarity: ${sentiment.polarity?.toFixed(2) || 0} | 
          Positive: ${sentiment.positive_count || 0} | 
          Negative: ${sentiment.negative_count || 0}
          ${sentiment.mixed_sentiment ? ' <span class="mixed-warning">⚠️ Mixed Signals Detected</span>' : ''}
        </div>
      </div>`;
    }
    
    // Manipulation risk
    if (manipRisk.level) {
      let manipClass = 'manip-low';
      if (manipRisk.level === 'critical') manipClass = 'manip-critical';
      else if (manipRisk.level === 'high') manipClass = 'manip-high';
      else if (manipRisk.level === 'medium') manipClass = 'manip-medium';
      
      html += `<div class="manipulation-risk-card ${manipClass}">
        <div class="manip-header">
          <i class="fas fa-user-secret"></i>
          <span>Manipulation Risk: ${manipRisk.level.toUpperCase()}</span>
        </div>
        <div class="manip-details">
          Risk Score: ${manipRisk.score || 0}/100 | 
          High-Intensity Emotions: ${manipRisk.high_intensity_emotions || 0}
          ${manipRisk.manipulation_detected ? ' <span class="manip-detected">⚠️ Active manipulation detected</span>' : ''}
        </div>
      </div>`;
    }
    
    // Emotional conflict indicators
    if (conflict.has_conflict && conflict.conflicts?.length) {
      html += `<div class="emotional-conflict-card">
        <div class="conflict-header">
          <i class="fas fa-balance-scale"></i>
          <span>Emotional Conflicts Detected</span>
        </div>
        <div class="conflict-description">${conflict.description || ''}</div>
        <div class="conflict-score">Conflict Score: ${conflict.conflict_score || 0}/50</div>
      </div>`;
    }
    
    html += `</div>`;
  }

  // Detected threats & highlights
  if (data.highlighted_text) {
    html += `<div class="analysis-section">
      <h6 class="analysis-title"><i class="fas fa-highlighter"></i> Detected Threats & Highlights</h6>
      <div class="email-content">${data.highlighted_text}</div>
    </div>`;
  }

  // Word-level analysis table
  if (data.word_analysis && data.word_analysis.length) {
    html += `<div class="analysis-section">
      <h6 class="analysis-title"><i class="fas fa-list"></i> Word-level Analysis</h6>
      <div class="word-analysis-table-wrap">
        <table class="word-analysis-table">
            <thead><tr><th>Token</th><th>URL</th><th>Email</th><th>Keyword</th><th>Urgent</th><th>Digits</th><th>Indicators</th><th>Model</th></tr></thead>
          <tbody>`;
    data.word_analysis.forEach(w => {
      const token = w.token || '-';
      // Show explicit 'yes'/'no' for boolean flags to avoid blank cells
      const is_url = w.is_url ? 'yes' : 'no';
      const is_email = w.is_email ? 'yes' : 'no';
      const is_kw = w.is_academic_kw ? 'yes' : 'no';
      const urg = w.urgency ? 'yes' : 'no';
      const contains_digits = w.contains_digits ? 'yes' : 'no';
      const inds = (w.indicator_matches && w.indicator_matches.length) ? (w.indicator_matches.join(', ')) : '-';
      const mp = (w.model_prob !== null && w.model_prob !== undefined) ? (Math.round(w.model_prob * 1000)/10 + '%') : '-';
      html += `<tr>
        <td class="token-cell">${token}</td>
        <td class="center-cell">${is_url}</td>
        <td class="center-cell">${is_email}</td>
        <td class="center-cell">${is_kw}</td>
        <td class="center-cell">${urg}</td>
        <td class="center-cell">${contains_digits}</td>
        <td class="indicators-cell">${inds}</td>
        <td class="model-cell">${mp}</td>
      </tr>`;
    });
    html += `</tbody></table></div></div>`;
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
