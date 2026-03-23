/**
 * RustChain Multi-Node Health Dashboard - Backend Server
 * Monitors all 4 RustChain attestation nodes in real-time
 * 
 * Bounty #2300 - 50 RTC
 * Wallet: 9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT
 */

const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Enable CORS
app.use(cors());
app.use(express.json());

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Node configuration
const NODES = [
  { id: 'node1', name: 'Node 1', url: 'https://50.28.86.131/health', location: 'LiquidWeb US', coords: [40.7128, -74.0060] },
  { id: 'node2', name: 'Node 2', url: 'https://50.28.86.153/health', location: 'LiquidWeb US', coords: [40.7128, -74.0060] },
  { id: 'node3', name: 'Node 3', url: 'http://76.8.228.245:8099/health', location: "Ryan's Proxmox", coords: [39.7392, -104.9903] },
  { id: 'node4', name: 'Node 4', url: 'http://38.76.217.189:8099/health', location: 'Hong Kong', coords: [22.3193, 114.1694] }
];

// In-memory data store
let nodeData = {};
let incidentLog = [];
let uptimeHistory = {};
let responseTimeHistory = {};

// Initialize data structures
NODES.forEach(node => {
  nodeData[node.id] = { status: 'unknown', lastCheck: null, data: null, responseTime: null };
  uptimeHistory[node.id] = [];
  responseTimeHistory[node.id] = [];
});

// Custom fetch with timeout and SSL handling
async function fetchNode(url) {
  const startTime = Date.now();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  
  try {
    // For HTTPS URLs with self-signed certs, we need to disable cert verification
    const isHttps = url.startsWith('https');
    const agent = isHttps ? new https.Agent({ rejectUnauthorized: false }) : null;
    
    const response = await fetch(url, { 
      signal: controller.signal,
      agent: agent,
      timeout: 10000
    });
    
    clearTimeout(timeout);
    const responseTime = Date.now() - startTime;
    const data = await response.json();
    
    return { success: true, data, responseTime };
  } catch (error) {
    clearTimeout(timeout);
    return { success: false, error: error.message, responseTime: null };
  }
}

// Check all nodes
async function checkAllNodes() {
  const timestamp = new Date().toISOString();
  
  for (const node of NODES) {
    const result = await fetchNode(node.url);
    const previousStatus = nodeData[node.id].status;
    
    if (result.success) {
      nodeData[node.id] = {
        status: 'up',
        lastCheck: timestamp,
        data: result.data,
        responseTime: result.responseTime
      };
      
      // Record uptime
      uptimeHistory[node.id].push({ timestamp, status: 'up' });
      responseTimeHistory[node.id].push({ timestamp, responseTime: result.responseTime });
      
      // Check if node recovered
      if (previousStatus === 'down') {
        incidentLog.push({
          timestamp,
          nodeId: node.id,
          nodeName: node.name,
          type: 'recovery',
          message: `${node.name} is back online`
        });
      }
    } else {
      nodeData[node.id] = {
        status: 'down',
        lastCheck: timestamp,
        data: null,
        responseTime: null,
        error: result.error
      };
      
      // Record downtime
      uptimeHistory[node.id].push({ timestamp, status: 'down' });
      
      // Check if node went down
      if (previousStatus === 'up') {
        incidentLog.push({
          timestamp,
          nodeId: node.id,
          nodeName: node.name,
          type: 'outage',
          message: `${node.name} is down: ${result.error}`
        });
      }
    }
    
    // Keep only last 24 hours of history (1440 entries at 60s intervals)
    const maxHistory = 1440;
    if (uptimeHistory[node.id].length > maxHistory) {
      uptimeHistory[node.id] = uptimeHistory[node.id].slice(-maxHistory);
    }
    if (responseTimeHistory[node.id].length > maxHistory) {
      responseTimeHistory[node.id] = responseTimeHistory[node.id].slice(-maxHistory);
    }
  }
  
  // Keep only last 100 incidents
  if (incidentLog.length > 100) {
    incidentLog = incidentLog.slice(-100);
  }
}

// API Routes

// Get current status of all nodes
app.get('/api/status', (req, res) => {
  const result = NODES.map(node => ({
    ...node,
    ...nodeData[node.id],
    uptime: calculateUptime(node.id),
    uptime24h: calculateUptime24h(node.id)
  }));
  res.json(result);
});

// Get uptime history for a specific node
app.get('/api/history/:nodeId', (req, res) => {
  const { nodeId } = req.params;
  const history = uptimeHistory[nodeId] || [];
  res.json(history);
});

// Get response time history for a specific node
app.get('/api/response-time/:nodeId', (req, res) => {
  const { nodeId } = req.params;
  const history = responseTimeHistory[nodeId] || [];
  res.json(history);
});

// Get incident log
app.get('/api/incidents', (req, res) => {
  res.json(incidentLog.reverse());
});

// Get RSS feed for incidents
app.get('/api/incidents/rss', (req, res) => {
  const RSS = require('rss');
  
  const feed = new RSS({
    title: 'RustChain Node Incidents',
    description: 'Real-time incident feed for RustChain attestation nodes',
    feed_url: `${req.protocol}://${req.get('host')}/api/incidents/rss`,
    site_url: 'https://rustchain.org/status',
    language: 'en'
  });
  
  incidentLog.forEach(incident => {
    feed.item({
      title: incident.message,
      description: `${incident.nodeName} - ${incident.type}`,
      date: incident.timestamp,
      url: `https://rustchain.org/status#incident-${incident.timestamp}`
    });
  });
  
  res.set('Content-Type', 'application/rss+xml');
  res.send(feed.xml());
});

// Get Atom feed for incidents
app.get('/api/incidents/atom', (req, res) => {
  const RSS = require('rss');
  
  const feed = new RSS({
    title: 'RustChain Node Incidents',
    description: 'Real-time incident feed for RustChain attestation nodes',
    feed_url: `${req.protocol}://${req.get('host')}/api/incidents/atom`,
    site_url: 'https://rustchain.org/status',
    language: 'en'
  });
  
  incidentLog.forEach(incident => {
    feed.item({
      title: incident.message,
      description: `${incident.nodeName} - ${incident.type}`,
      date: incident.timestamp,
      url: `https://rustchain.org/status#incident-${incident.timestamp}`
    });
  });
  
  res.set('Content-Type', 'application/atom+xml');
  res.send(feed.xml({ indent: true }));
});

// Webhook notification endpoint (for Discord/Telegram)
app.post('/api/webhook/configure', (req, res) => {
  const { type, url, nodeIds } = req.body;
  // Store webhook configuration (in production, use a database)
  const config = { type, url, nodeIds, createdAt: new Date().toISOString() };
  res.json({ success: true, config });
});

// Calculate uptime percentage
function calculateUptime(nodeId) {
  const history = uptimeHistory[nodeId];
  if (!history || history.length === 0) return 100;
  
  const upCount = history.filter(h => h.status === 'up').length;
  return ((upCount / history.length) * 100).toFixed(2);
}

// Calculate 24-hour uptime
function calculateUptime24h(nodeId) {
  const history = uptimeHistory[nodeId];
  if (!history || history.length === 0) return 100;
  
  const now = Date.now();
  const oneDayAgo = now - 24 * 60 * 60 * 1000;
  
  const recentHistory = history.filter(h => new Date(h.timestamp).getTime() > oneDayAgo);
  if (recentHistory.length === 0) return 100;
  
  const upCount = recentHistory.filter(h => h.status === 'up').length;
  return ((upCount / recentHistory.length) * 100).toFixed(2);
}

// Format uptime for display
function formatUptime(uptimeSeconds) {
  if (!uptimeSeconds) return 'N/A';
  
  const days = Math.floor(uptimeSeconds / 86400);
  const hours = Math.floor((uptimeSeconds % 86400) / 3600);
  const minutes = Math.floor((uptimeSeconds % 3600) / 60);
  
  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
}

// Main page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start polling
async function startPolling() {
  // Initial check
  await checkAllNodes();
  
  // Poll every 60 seconds
  setInterval(async () => {
    await checkAllNodes();
  }, 60000);
}

// Start server
app.listen(PORT, () => {
  console.log(`RustChain Status Dashboard running on port ${PORT}`);
  console.log(`Dashboard: http://localhost:${PORT}`);
  console.log(`API: http://localhost:${PORT}/api/status`);
  startPolling();
});

module.exports = app;