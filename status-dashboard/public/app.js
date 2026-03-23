/**
 * RustChain Status Dashboard - Frontend Application
 * Real-time monitoring for all RustChain attestation nodes
 */

// Configuration
const CONFIG = {
  refreshInterval: 60000, // 60 seconds
  chartMaxPoints: 1440,   // 24 hours at 1-minute intervals
  timelineBars: 144       // Each bar represents 10 minutes
};

// State
let chartInstance = null;
let lastData = null;

// Format uptime seconds to human readable
function formatUptime(seconds) {
  if (!seconds) return 'N/A';
  
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
}

// Format timestamp to relative time
function formatRelativeTime(timestamp) {
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

// Format timestamp to local time
function formatLocalTime(timestamp) {
  return new Date(timestamp).toLocaleString();
}

// Get response time CSS class
function getResponseTimeClass(ms) {
  if (!ms) return '';
  if (ms < 500) return 'response-time';
  if (ms < 2000) return 'response-time slow';
  return 'response-time very-slow';
}

// Fetch node status
async function fetchStatus() {
  try {
    const response = await fetch('/api/status');
    const data = await response.json();
    lastData = data;
    return data;
  } catch (error) {
    console.error('Failed to fetch status:', error);
    return null;
  }
}

// Fetch incidents
async function fetchIncidents() {
  try {
    const response = await fetch('/api/incidents');
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch incidents:', error);
    return [];
  }
}

// Fetch response time history for all nodes
async function fetchResponseTimeHistory() {
  try {
    const nodes = ['node1', 'node2', 'node3', 'node4'];
    const promises = nodes.map(async (nodeId) => {
      const response = await fetch(`/api/response-time/${nodeId}`);
      return { nodeId, data: await response.json() };
    });
    return await Promise.all(promises);
  } catch (error) {
    console.error('Failed to fetch response time history:', error);
    return [];
  }
}

// Render status banner
function renderStatusBanner(data) {
  const banner = document.getElementById('status-banner');
  const icon = document.getElementById('overall-status-icon');
  const text = document.getElementById('overall-status-text');
  
  const upCount = data.filter(n => n.status === 'up').length;
  const total = data.length;
  
  banner.className = 'status-banner';
  
  if (upCount === total) {
    banner.classList.add('all-up');
    icon.className = 'status-icon up';
    icon.textContent = '●';
    text.textContent = `All Systems Operational (${upCount}/${total} nodes up)`;
  } else if (upCount === 0) {
    banner.classList.add('all-down');
    icon.className = 'status-icon down';
    icon.textContent = '●';
    text.textContent = `Major Outage (${upCount}/${total} nodes up)`;
  } else {
    banner.classList.add('some-down');
    icon.className = 'status-icon partial';
    icon.textContent = '●';
    text.textContent = `Partial Outage (${upCount}/${total} nodes up)`;
  }
}

// Render node cards
function renderNodeCards(data) {
  const grid = document.getElementById('nodes-grid');
  
  grid.innerHTML = data.map(node => {
    const statusClass = node.status || 'unknown';
    const responseTimeClass = getResponseTimeClass(node.responseTime);
    const uptimeData = node.data || {};
    
    // Determine what data to show based on node type
    let extraInfo = '';
    if (uptimeData.service === 'bottube') {
      // BoTTube node
      extraInfo = `
        <div class="node-info-row">
          <span class="node-info-label">Service</span>
          <span class="node-info-value">BoTTube</span>
        </div>
        <div class="node-info-row">
          <span class="node-info-label">Videos</span>
          <span class="node-info-value">${uptimeData.videos || 'N/A'}</span>
        </div>
        <div class="node-info-row">
          <span class="node-info-label">Agents</span>
          <span class="node-info-value">${uptimeData.agents || 'N/A'}</span>
        </div>
        <div class="node-info-row">
          <span class="node-info-label">Humans</span>
          <span class="node-info-value">${uptimeData.humans || 'N/A'}</span>
        </div>
      `;
    } else {
      // RustChain node
      extraInfo = `
        <div class="node-info-row">
          <span class="node-info-label">DB Status</span>
          <span class="node-info-value">${uptimeData.db_rw ? '✅ Read/Write' : '❌ Read Only'}</span>
        </div>
        <div class="node-info-row">
          <span class="node-info-label">Tip Age</span>
          <span class="node-info-value">${uptimeData.tip_age_slots !== null ? uptimeData.tip_age_slots + ' slots' : 'N/A'}</span>
        </div>
        <div class="node-info-row">
          <span class="node-info-label">Backup Age</span>
          <span class="node-info-value">${uptimeData.backup_age_hours !== null ? uptimeData.backup_age_hours.toFixed(1) + 'h' : 'N/A'}</span>
        </div>
      `;
    }
    
    return `
      <div class="node-card status-${statusClass}">
        <div class="node-header">
          <span class="node-name">${node.name}</span>
          <span class="node-status-badge ${statusClass}">${statusClass.toUpperCase()}</span>
        </div>
        <div class="node-info">
          <div class="node-info-row">
            <span class="node-info-label">Location</span>
            <span class="node-info-value">${node.location}</span>
          </div>
          <div class="node-info-row">
            <span class="node-info-label">Version</span>
            <span class="node-info-value">${uptimeData.version || 'N/A'}</span>
          </div>
          <div class="node-info-row">
            <span class="node-info-label">Uptime</span>
            <span class="node-info-value">${formatUptime(uptimeData.uptime_s)}</span>
          </div>
          <div class="node-info-row">
            <span class="node-info-label">Response Time</span>
            <span class="node-info-value ${responseTimeClass}">${node.responseTime ? node.responseTime + 'ms' : 'N/A'}</span>
          </div>
          <div class="node-info-row">
            <span class="node-info-label">24h Uptime</span>
            <span class="node-info-value">${node.uptime24h || 100}%</span>
          </div>
          ${extraInfo}
        </div>
      </div>
    `;
  }).join('');
}

// Render timeline
function renderTimeline(data) {
  const container = document.getElementById('timeline-container');
  
  // Create timeline for each node
  container.innerHTML = data.map(node => {
    const history = node.history || [];
    const bars = [];
    
    // Group history into bars (each bar = 10 minutes = 10 data points)
    for (let i = 0; i < CONFIG.timelineBars; i++) {
      const start = i * 10;
      const end = start + 10;
      const slice = history.slice(start, end);
      
      if (slice.length === 0) {
        bars.push('<div class="timeline-bar unknown"></div>');
      } else {
        const upCount = slice.filter(h => h.status === 'up').length;
        const ratio = upCount / slice.length;
        
        if (ratio >= 0.9) {
          bars.push('<div class="timeline-bar up"></div>');
        } else if (ratio >= 0.5) {
          bars.push('<div class="timeline-bar partial" style="background-color: #f59e0b;"></div>');
        } else if (ratio > 0) {
          bars.push('<div class="timeline-bar down"></div>');
        } else {
          bars.push('<div class="timeline-bar unknown"></div>');
        }
      }
    }
    
    return `
      <div class="timeline-node">
        <span class="timeline-node-name">${node.name}</span>
        <div class="timeline-bars">
          ${bars.join('')}
        </div>
      </div>
    `;
  }).join('');
}

// Render chart
async function renderChart() {
  const historyData = await fetchResponseTimeHistory();
  
  const ctx = document.getElementById('response-time-chart').getContext('2d');
  
  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  const colors = {
    node1: '#f97316',
    node2: '#22c55e',
    node3: '#3b82f6',
    node4: '#a855f7'
  };
  
  const datasets = historyData.map(({ nodeId, data }) => {
    const nodeInfo = lastData?.find(n => n.id === nodeId) || { name: nodeId };
    return {
      label: nodeInfo.name,
      data: data.map(d => ({ x: new Date(d.timestamp), y: d.responseTime })),
      borderColor: colors[nodeId],
      backgroundColor: colors[nodeId] + '20',
      tension: 0.4,
      fill: false,
      pointRadius: 0,
      borderWidth: 2
    };
  });
  
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          labels: {
            color: '#94a3b8'
          }
        },
        tooltip: {
          callbacks: {
            label: (context) => `${context.dataset.label}: ${context.parsed.y?.toFixed(0) || 'N/A'}ms`
          }
        }
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'hour',
            displayFormats: {
              hour: 'HH:mm'
            }
          },
          grid: {
            color: '#334155'
          },
          ticks: {
            color: '#94a3b8'
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: '#334155'
          },
          ticks: {
            color: '#94a3b8',
            callback: (value) => value + 'ms'
          }
        }
      }
    }
  });
}

// Render incidents
function renderIncidents(incidents) {
  const list = document.getElementById('incidents-list');
  
  if (incidents.length === 0) {
    list.innerHTML = '<div class="no-incidents">No incidents in the last 30 days</div>';
    return;
  }
  
  list.innerHTML = incidents.map(incident => `
    <div class="incident-item">
      <span class="incident-icon ${incident.type}">${incident.type === 'outage' ? '🔴' : '🟢'}</span>
      <div class="incident-content">
        <div class="incident-message">${incident.message}</div>
        <div class="incident-time">${formatLocalTime(incident.timestamp)} (${formatRelativeTime(incident.timestamp)})</div>
      </div>
    </div>
  `).join('');
}

// Render map
function renderMap(data) {
  const container = document.getElementById('map-container');
  
  // Simple SVG world map background
  const worldMapSvg = `
    <svg class="map-world" viewBox="0 0 1000 500" preserveAspectRatio="xMidYMid meet">
      <!-- Simple world map outline -->
      <path d="M150,100 Q200,80 250,100 Q300,120 280,150 Q260,180 200,170 Q140,160 150,100" fill="#334155" />
      <path d="M400,80 Q450,60 500,80 Q550,100 530,150 Q510,200 450,180 Q390,160 400,80" fill="#334155" />
      <path d="M500,100 Q600,80 700,100 Q800,120 780,200 Q760,280 650,260 Q540,240 500,100" fill="#334155" />
      <path d="M750,150 Q850,130 900,180 Q950,230 920,300 Q890,370 800,350 Q710,330 750,150" fill="#334155" />
      <path d="M200,200 Q250,180 300,220 Q350,260 320,320 Q290,380 230,360 Q170,340 200,200" fill="#334155" />
      <path d="M600,250 Q700,230 750,300 Q800,370 750,420 Q700,470 620,450 Q540,430 600,250" fill="#334155" />
      <path d="M150,300 Q200,280 250,340 Q300,400 250,450 Q200,500 150,480 Q100,460 150,300" fill="#334155" />
    </svg>
  `;
  
  // Convert coordinates to SVG positions
  const coordsToSvg = (lat, lon) => {
    const x = ((lon + 180) / 360) * 1000;
    const y = ((90 - lat) / 180) * 500;
    return { x, y };
  };
  
  // Create node markers
  const markers = data.map(node => {
    const [lat, lon] = node.coords || [0, 0];
    const { x, y } = coordsToSvg(lat, lon);
    const statusClass = node.status === 'up' ? 'up' : 'down';
    return `
      <circle 
        class="map-node-marker ${statusClass}" 
        cx="${x}" 
        cy="${y}" 
        r="8"
        data-node="${node.name}"
        data-status="${node.status}"
        data-location="${node.location}"
      />
      <text x="${x}" y="${y - 15}" fill="#f8fafc" font-size="10" text-anchor="middle">${node.name}</text>
    `;
  }).join('');
  
  container.innerHTML = `
    <svg class="map-world" viewBox="0 0 1000 500" preserveAspectRatio="xMidYMid meet">
      <!-- World map background -->
      <rect width="1000" height="500" fill="#1e293b" />
      
      <!-- Simplified continents -->
      <ellipse cx="250" cy="150" rx="120" ry="80" fill="#334155" />
      <ellipse cx="500" cy="180" rx="100" ry="120" fill="#334155" />
      <ellipse cx="700" cy="150" rx="150" ry="100" fill="#334155" />
      <ellipse cx="800" cy="350" rx="100" ry="80" fill="#334155" />
      <ellipse cx="250" cy="320" rx="80" ry="100" fill="#334155" />
      <ellipse cx="600" cy="350" rx="60" ry="50" fill="#334155" />
      
      <!-- Node markers -->
      ${markers}
    </svg>
  `;
}

// Update last update time
function updateLastUpdateTime() {
  const el = document.getElementById('last-update');
  el.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
}

// Main update function
async function update() {
  console.log('Updating status...');
  
  const data = await fetchStatus();
  const incidents = await fetchIncidents();
  
  if (data) {
    renderStatusBanner(data);
    renderNodeCards(data);
    renderTimeline(data);
    renderMap(data);
  }
  
  renderIncidents(incidents);
  updateLastUpdateTime();
  
  // Update chart less frequently
  if (!chartInstance || Math.random() < 0.1) {
    await renderChart();
  }
}

// Initialize
async function init() {
  console.log('Initializing RustChain Status Dashboard...');
  
  await update();
  
  // Set up auto-refresh
  setInterval(update, CONFIG.refreshInterval);
  
  console.log('Dashboard initialized. Auto-refresh every 60 seconds.');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}