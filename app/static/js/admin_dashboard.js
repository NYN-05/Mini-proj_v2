/* ============================================
   ADMIN DASHBOARD JAVASCRIPT
   Chart.js Integration & Real-Time Updates
   ============================================ */

// Chart instances (global for easy reference)
const charts = {};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
  initializeDashboard();
  setupEventListeners();
});

/**
 * Initialize the entire dashboard
 */
function initializeDashboard() {
  // Load initial analytics data
  loadAnalyticsData();
  
  // Set up Chart.js with default options
  Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.padding = 15;
  
  // Auto-refresh analytics every 5 minutes
  setInterval(loadAnalyticsData, 300000);
}

/**
 * Setup event listeners for interactive elements
 */
function setupEventListeners() {
  const institutionSelector = document.getElementById('institutionSelector');
  if (institutionSelector) {
    institutionSelector.addEventListener('change', loadAnalyticsData);
  }
}

/**
 * Load analytics data from backend API
 */
function loadAnalyticsData() {
  const institution = document.getElementById('institutionSelector')?.value || 'Default';
  const days = 30;
  
  // Show loading state
  showLoadingState();
  
  fetch(`/api/analytics?institution=${encodeURIComponent(institution)}&days=${days}`)
    .then(response => {
      if (!response.ok) throw new Error('Failed to fetch analytics');
      return response.json();
    })
    .then(data => {
      updateMetricsCards(data);
      updateCharts(data);
      updateTables(data);
      hideLoadingState();
      updateLastRefreshTime();
    })
    .catch(error => {
      console.error('Error loading analytics:', error);
      showErrorState();
      hideLoadingState();
    });
}

/**
 * Update metric cards with summary statistics
 */
function updateMetricsCards(data) {
  const stats = data.overall_stats || {};
  
  // Update Total Emails
  const totalEmailsEl = document.getElementById('totalEmails');
  if (totalEmailsEl) {
    totalEmailsEl.textContent = stats.total_emails || 0;
  }
  
  // Update Phishing Detected
  const phishingEl = document.getElementById('phishingDetected');
  if (phishingEl) {
    phishingEl.textContent = stats.phishing_count || 0;
  }
  
  // Update Legitimate Emails
  const legitimateEl = document.getElementById('legitimateEmails');
  if (legitimateEl) {
    legitimateEl.textContent = stats.legitimate_count || 0;
  }
  
  // Update Average Confidence
  const confidenceEl = document.getElementById('avgConfidence');
  if (confidenceEl) {
    const avgConfidence = (stats.avg_confidence * 100).toFixed(1);
    confidenceEl.textContent = avgConfidence + '%';
  }
}

/**
 * Update all charts with fresh data
 */
function updateCharts(data) {
  updateDailyTrendChart(data.daily_trends || []);
  updatePhishingPatternsChart(data.phishing_patterns || []);
  updateHourlyPatternChart(data.hourly_patterns || []);
  updateConfidenceDistributionChart(data.confidence_distribution || []);
  updateModelPerformanceChart(data.model_performance || {});
  updateAttackTrendChart(data.attack_trends || []);
}

/**
 * Chart 1: Daily Trend Chart
 */
function updateDailyTrendChart(data) {
  const ctx = document.getElementById('dailyTrendChart');
  if (!ctx) return;
  
  // Prepare data
  const dates = data.map(item => item.date || item.day || '').slice(-30);
  const phishingCounts = data.map(item => item.phishing_count || 0).slice(-30);
  const legitimateCounts = data.map(item => item.legitimate_count || 0).slice(-30);
  
  // Destroy existing chart
  if (charts.dailyTrend) {
    charts.dailyTrend.destroy();
  }
  
  // Create new chart
  charts.dailyTrend = new Chart(ctx, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [
        {
          label: 'Phishing Emails',
          data: phishingCounts,
          borderColor: '#da1e28',
          backgroundColor: 'rgba(218, 30, 40, 0.05)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: '#da1e28',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointHoverRadius: 6,
        },
        {
          label: 'Legitimate Emails',
          data: legitimateCounts,
          borderColor: '#24a148',
          backgroundColor: 'rgba(36, 161, 72, 0.05)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: '#24a148',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointHoverRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 15,
            font: { weight: '600' }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: value => value.toLocaleString() },
          grid: { color: 'rgba(0, 0, 0, 0.05)' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

/**
 * Chart 2: Phishing Patterns Distribution
 */
function updatePhishingPatternsChart(data) {
  const ctx = document.getElementById('patternsChart');
  if (!ctx) return;
  
  // Prepare data
  const patterns = data.map(item => item.pattern_type || 'Unknown');
  const counts = data.map(item => item.count || 0);
  const colors = [
    '#da1e28', '#f1c21b', '#0043ce', '#24a148', '#0f62fe', '#a56eff'
  ];
  
  // Destroy existing chart
  if (charts.patterns) {
    charts.patterns.destroy();
  }
  
  // Create new chart
  charts.patterns = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: patterns,
      datasets: [{
        data: counts,
        backgroundColor: colors.slice(0, patterns.length),
        borderColor: '#fff',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 15,
            font: { weight: '600' }
          }
        }
      }
    }
  });
}

/**
 * Chart 3: Hourly Attack Pattern
 */
function updateHourlyPatternChart(data) {
  const ctx = document.getElementById('hourlyPatternChart');
  if (!ctx) return;
  
  // Prepare data
  const hours = data.map(item => (item.hour || item.time || '').toString().padStart(2, '0') + ':00');
  const counts = data.map(item => item.attack_count || 0);
  
  // Destroy existing chart
  if (charts.hourlyPattern) {
    charts.hourlyPattern.destroy();
  }
  
  // Create new chart
  charts.hourlyPattern = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: hours,
      datasets: [{
        label: 'Attacks by Hour',
        data: counts,
        backgroundColor: 'rgba(15, 98, 254, 0.7)',
        borderColor: '#0f62fe',
        borderWidth: 1,
        borderRadius: 4,
        hoverBackgroundColor: '#0f62fe'
      }]
    },
    options: {
      indexAxis: 'x',
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: value => value.toLocaleString() },
          grid: { color: 'rgba(0, 0, 0, 0.05)' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

/**
 * Chart 4: Confidence Score Distribution
 */
function updateConfidenceDistributionChart(data) {
  const ctx = document.getElementById('confidenceChart');
  if (!ctx) return;
  
  // Prepare data (confidence ranges)
  const ranges = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'];
  const distribution = data.map(item => item.count || 0);
  
  // Destroy existing chart
  if (charts.confidence) {
    charts.confidence.destroy();
  }
  
  // Create new chart
  charts.confidence = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ranges,
      datasets: [{
        label: 'Predictions Count',
        data: distribution,
        backgroundColor: [
          'rgba(218, 30, 40, 0.7)',    // 0-20% - Red
          'rgba(241, 194, 27, 0.7)',   // 20-40% - Yellow
          'rgba(0, 67, 206, 0.7)',     // 40-60% - Blue
          'rgba(15, 98, 254, 0.7)',    // 60-80% - Light Blue
          'rgba(36, 161, 72, 0.7)'     // 80-100% - Green
        ],
        borderColor: [
          '#da1e28', '#f1c21b', '#0043ce', '#0f62fe', '#24a148'
        ],
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'x',
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0, 0, 0, 0.05)' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

/**
 * Chart 5: Model Performance Comparison
 */
function updateModelPerformanceChart(data) {
  const ctx = document.getElementById('performanceChart');
  if (!ctx) return;
  
  const models = Object.keys(data);
  const accuracies = models.map(model => ((data[model].accuracy || 0) * 100).toFixed(1));
  const precisions = models.map(model => ((data[model].precision || 0) * 100).toFixed(1));
  const recalls = models.map(model => ((data[model].recall || 0) * 100).toFixed(1));
  
  // Destroy existing chart
  if (charts.performance) {
    charts.performance.destroy();
  }
  
  // Create new chart
  charts.performance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: models,
      datasets: [
        {
          label: 'Accuracy',
          data: accuracies,
          borderColor: '#0f62fe',
          backgroundColor: 'rgba(15, 98, 254, 0.1)',
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: '#0f62fe'
        },
        {
          label: 'Precision',
          data: precisions,
          borderColor: '#24a148',
          backgroundColor: 'rgba(36, 161, 72, 0.1)',
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: '#24a148'
        },
        {
          label: 'Recall',
          data: recalls,
          borderColor: '#da1e28',
          backgroundColor: 'rgba(218, 30, 40, 0.1)',
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: '#da1e28'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: value => value + '%' },
          grid: { color: 'rgba(0, 0, 0, 0.05)' }
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 15,
            font: { weight: '600' }
          }
        }
      }
    }
  });
}

/**
 * Chart 6: Attack Trend Over Time
 */
function updateAttackTrendChart(data) {
  const ctx = document.getElementById('trendChart');
  if (!ctx) return;
  
  const dates = data.map(item => item.date || item.period || '');
  const severityHigh = data.map(item => item.high_severity || 0);
  const severityMedium = data.map(item => item.medium_severity || 0);
  const severityLow = data.map(item => item.low_severity || 0);
  
  // Destroy existing chart
  if (charts.attackTrend) {
    charts.attackTrend.destroy();
  }
  
  // Create new chart
  charts.attackTrend = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dates,
      datasets: [
        {
          label: 'High Severity',
          data: severityHigh,
          backgroundColor: '#da1e28',
          borderColor: '#da1e28',
          borderWidth: 1
        },
        {
          label: 'Medium Severity',
          data: severityMedium,
          backgroundColor: '#f1c21b',
          borderColor: '#f1c21b',
          borderWidth: 1
        },
        {
          label: 'Low Severity',
          data: severityLow,
          backgroundColor: '#24a148',
          borderColor: '#24a148',
          borderWidth: 1
        }
      ]
    },
    options: {
      indexAxis: 'x',
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: { stacked: true, beginAtZero: true, grid: { color: 'rgba(0, 0, 0, 0.05)' } }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 15,
            font: { weight: '600' }
          }
        }
      }
    }
  });
}

/**
 * Update data tables with recent predictions and keywords
 */
function updateTables(data) {
  updateKeywordsTable(data.keywords || []);
  updateRecentPredictionsTable(data.recent_predictions || []);
}

/**
 * Update Top Keywords table
 */
function updateKeywordsTable(keywords) {
  const tableBody = document.querySelector('#keywordsTable tbody');
  if (!tableBody) return;
  
  tableBody.innerHTML = '';
  
  keywords.slice(0, 10).forEach((keyword, index) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${index + 1}</td>
      <td><strong>${keyword.keyword || 'N/A'}</strong></td>
      <td>${keyword.frequency || 0}</td>
      <td>
        <span class="badge ${keyword.threat_level === 'high' ? 'badge-danger' : 
                            keyword.threat_level === 'medium' ? 'badge-warning' : 
                            'badge-info'}">
          ${(keyword.threat_level || 'low').toUpperCase()}
        </span>
      </td>
    `;
    tableBody.appendChild(row);
  });
  
  if (keywords.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No data available</td></tr>';
  }
}

/**
 * Update Recent Predictions table
 */
function updateRecentPredictionsTable(predictions) {
  const tableBody = document.querySelector('#predictionsTable tbody');
  if (!tableBody) return;
  
  tableBody.innerHTML = '';
  
  predictions.slice(0, 20).forEach((prediction, index) => {
    const row = document.createElement('tr');
    const confidence = (prediction.confidence * 100).toFixed(1);
    const timestamp = new Date(prediction.timestamp).toLocaleString();
    
    row.innerHTML = `
      <td>${index + 1}</td>
      <td>${timestamp}</td>
      <td class="text-truncate" style="max-width: 200px; cursor: pointer;" title="${prediction.subject || 'N/A'}">
        ${prediction.subject ? prediction.subject.substring(0, 30) + '...' : 'N/A'}
      </td>
      <td>
        <span class="badge ${prediction.label === 'phishing' ? 'badge-phishing' : 'badge-legitimate'}">
          ${prediction.label ? prediction.label.toUpperCase() : 'UNKNOWN'}
        </span>
      </td>
      <td><strong>${confidence}%</strong></td>
    `;
    tableBody.appendChild(row);
  });
  
  if (predictions.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No predictions yet</td></tr>';
  }
}

/**
 * Update last refresh timestamp
 */
function updateLastRefreshTime() {
  const refreshEl = document.getElementById('lastRefresh');
  if (refreshEl) {
    const now = new Date();
    refreshEl.textContent = now.toLocaleTimeString();
  }
}

/**
 * Show loading state on dashboard
 */
function showLoadingState() {
  const cards = document.querySelectorAll('.chart-card');
  cards.forEach(card => {
    const body = card.querySelector('.card-body');
    if (body && !body.querySelector('.loading-spinner')) {
      const spinner = document.createElement('div');
      spinner.className = 'loading-spinner';
      spinner.innerHTML = '<div class="spinner-border spinner-border-sm text-primary"></div>';
      spinner.style.position = 'absolute';
      spinner.style.top = '50%';
      spinner.style.left = '50%';
      spinner.style.transform = 'translate(-50%, -50%)';
      body.appendChild(spinner);
    }
  });
}

/**
 * Hide loading state
 */
function hideLoadingState() {
  document.querySelectorAll('.loading-spinner').forEach(el => el.remove());
}

/**
 * Show error state
 */
function showErrorState() {
  const errorAlert = document.createElement('div');
  errorAlert.className = 'alert alert-danger alert-dismissible fade show';
  errorAlert.innerHTML = `
    <strong>Error!</strong> Failed to load analytics data. Please try again later.
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  const header = document.querySelector('.admin-header');
  if (header) {
    header.parentNode.insertBefore(errorAlert, header.nextSibling);
    setTimeout(() => errorAlert.remove(), 5000);
  }
}

/**
 * Export analytics data to CSV
 */
function exportAnalytics() {
  const institution = document.getElementById('institutionSelector')?.value || 'Default';
  const timestamp = new Date().toISOString().split('T')[0];
  const filename = `analytics_${institution}_${timestamp}.csv`;
  
  // Implement CSV export logic here
  console.log('Exporting analytics to:', filename);
  
  // For now, just show a message
  alert('Analytics export feature coming soon!');
}

/**
 * Print dashboard
 */
function printDashboard() {
  window.print();
}
