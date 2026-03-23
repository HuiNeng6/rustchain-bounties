# RustChain Multi-Node Health Dashboard

> **Bounty #2300** - Real-time monitoring for all RustChain attestation nodes

## 🌐 Live Demo

Deploy target: `rustchain.org/status`

## 📊 Features

- ✅ **Real-time Monitoring**: Polls all 4 RustChain nodes every 60 seconds
- ✅ **Status Display**: Shows up/down status, response time, version, uptime
- ✅ **24-Hour Timeline**: Visual uptime history for all nodes
- ✅ **Response Time Charts**: Interactive graphs showing performance trends
- ✅ **Incident Log**: Records when nodes go down or recover
- ✅ **Mobile-Friendly**: Responsive design works on all devices
- ✅ **RSS/Atom Feeds**: Subscribe to incident notifications
- ✅ **Geographic Map**: Visual node location display

## 🚀 Quick Start

### Using Node.js

```bash
# Install dependencies
npm install

# Start server
npm start

# Open http://localhost:3000
```

### Using Docker

```bash
# Build and run
docker-compose up -d

# Open http://localhost:3000
```

## 📋 Monitored Nodes

| Node | Endpoint | Location |
|------|----------|----------|
| Node 1 | https://50.28.86.131/health | LiquidWeb US |
| Node 2 | https://50.28.86.153/health | LiquidWeb US |
| Node 3 | http://76.8.228.245:8099/health | Ryan's Proxmox |
| Node 4 | http://38.76.217.189:8099/health | Hong Kong |

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | Current status of all nodes |
| `GET /api/history/:nodeId` | Uptime history for a node |
| `GET /api/response-time/:nodeId` | Response time history |
| `GET /api/incidents` | Recent incident log |
| `GET /api/incidents/rss` | RSS feed for incidents |
| `GET /api/incidents/atom` | Atom feed for incidents |

## 📱 Screenshots

### Desktop View
- Clean dark theme dashboard
- Node cards with detailed metrics
- Interactive response time charts
- 24-hour uptime timeline

### Mobile View
- Fully responsive design
- Touch-friendly interface
- Optimized for small screens

## 🔔 Bonus Features

### RSS/Atom Feeds
Subscribe to incident notifications:
- RSS: `/api/incidents/rss`
- Atom: `/api/incidents/atom`

### Webhook Integration (Coming Soon)
Configure Discord/Telegram webhooks for node down notifications:
```bash
POST /api/webhook/configure
{
  "type": "discord",
  "url": "https://discord.com/api/webhooks/...",
  "nodeIds": ["node1", "node2", "node3", "node4"]
}
```

## 🛠️ Tech Stack

- **Backend**: Node.js + Express
- **Frontend**: Vanilla JS + Chart.js
- **Styling**: Pure CSS (Dark theme)
- **Deployment**: Docker + nginx

## 📦 Deployment

### nginx Configuration

```nginx
server {
    listen 80;
    server_name rustchain.org;
    
    location /status {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Systemd Service

```ini
[Unit]
Description=RustChain Status Dashboard
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/rustchain-status
ExecStart=/usr/bin/node server.js
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 📄 License

MIT License

## 💰 Bounty

This project was created for **RustChain Bounty #2300** (50 RTC).

**Wallet Address**: `9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT`

---

Built with ❤️ for the RustChain community