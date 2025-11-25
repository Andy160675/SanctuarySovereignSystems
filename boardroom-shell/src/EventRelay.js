import { EventEmitter } from 'events'

// Central event bus for sovereign system state management
class SovereignEventRelay extends EventEmitter {
  constructor() {
    super()
    this.state = {
      truthEngine: 'checking',
      ollama: 'checking',
      watcher: 'checking',
      lastUpdate: new Date().toISOString()
    }
    
    // Auto-emit state changes
    this.on('stateChange', (newState) => {
      this.state = { ...this.state, ...newState, lastUpdate: new Date().toISOString() }
      this.emit('systemUpdate', this.state)
    })
  }
  
  updateState(updates) {
    this.emit('stateChange', updates)
  }
  
  getState() {
    return this.state
  }
  
  // System health check
  async performHealthCheck() {
    try {
      // Check Truth Engine
      const truthResponse = await fetch('http://localhost:5050/health')
      const truthStatus = truthResponse.ok ? 'active' : 'offline'
      
      // Check Ollama  
      const ollamaResponse = await fetch('http://localhost:11434/api/tags')
      const ollamaStatus = ollamaResponse.ok ? 'active' : 'offline'
      
      this.updateState({
        truthEngine: truthStatus,
        ollama: ollamaStatus,
        watcher: 'active' // Assume active if container is running
      })
      
    } catch (error) {
      console.error('Health check failed:', error)
      this.emit('error', { type: 'healthCheck', error: error.message })
    }
  }
}

const EventRelay = new SovereignEventRelay()

// Perform initial health check
setTimeout(() => EventRelay.performHealthCheck(), 1000)

// Periodic health checks every 30 seconds
setInterval(() => EventRelay.performHealthCheck(), 30000)

export default EventRelay