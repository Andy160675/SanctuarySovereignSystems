# Boardroom Shell

Electron + React Phase 3 UI

## Quick Start

```bash
cd boardroom-shell
npm install
npm run electron-dev
```

## Build for Production

```bash
npm run build
npm run electron
```

## Package Application

```bash
npm run dist
```

## Architecture

- **Electron:** Main process with secure preload
- **React:** Modern functional components with hooks
- **Webpack:** Hot reload development server
- **IPC:** Secure communication with truth engine

## Components

- **EmpathyBanner:** Sovereign empathy messaging
- **EmpathyTimeline:** Development phase tracker  
- **TruthPanel:** Search interface for truth engine
- **SystemStatus:** Service health monitoring

## Features

- ✅ Truth engine integration
- ✅ Real-time search
- ✅ System status monitoring
- ✅ Sovereign empathy UI
- ✅ Phase timeline tracking
- ✅ Secure file access

## Development

The UI connects to:
- Truth Engine: `http://localhost:5050`
- Ollama: `http://localhost:11434`

Ensure these services are running via `docker compose up -d`

## Security

- Context isolation enabled
- Node integration disabled
- Preload script for secure API exposure
- Read-only corpus access
