import React, { useState, useEffect } from 'react'
import EmpathyBanner from './components/EmpathyBanner'
import EmpathyTimeline from './components/EmpathyTimeline'
import TruthPanel from './components/TruthPanel'
import SystemStatus from './components/SystemStatus'
import TriosphereStatus from './components/TriosphereStatus'

const App = () => {
  const [currentView, setCurrentView] = useState('truth')
  const [systemStatus, setSystemStatus] = useState({
    truthEngine: 'checking',
    ollama: 'checking',
    index: 'checking',
    triosphere: {
      intent: 'active',
      evidence: 'active',
      action: 'active'
    }
  })

  useEffect(() => {
    checkSystemStatus()
  }, [])

  const checkSystemStatus = async () => {
    // Check Truth Engine
    try {
      const response = await fetch('http://localhost:5050/search?q=test&limit=1')
      if (response.ok) {
        setSystemStatus(prev => ({ ...prev, truthEngine: 'active' }))
      }
    } catch {
      setSystemStatus(prev => ({ ...prev, truthEngine: 'offline' }))
    }

    // Check Ollama
    try {
      const response = await fetch('http://localhost:11434/api/tags')
      if (response.ok) {
        setSystemStatus(prev => ({ ...prev, ollama: 'active' }))
      }
    } catch {
      setSystemStatus(prev => ({ ...prev, ollama: 'offline' }))
    }

    // Index status (simulated)
    setSystemStatus(prev => ({ ...prev, index: 'active' }))
  }

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)'
    },
    header: {
      padding: '20px',
      borderBottom: '1px solid #333',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    },
    title: {
      fontSize: '24px',
      fontWeight: '300',
      color: '#ff6b35'
    },
    nav: {
      display: 'flex',
      gap: '20px'
    },
    navButton: {
      background: 'none',
      border: '1px solid #444',
      color: '#e0e0e0',
      padding: '10px 20px',
      cursor: 'pointer',
      borderRadius: '4px',
      transition: 'all 0.3s'
    },
    activeNavButton: {
      borderColor: '#ff6b35',
      backgroundColor: 'rgba(255, 107, 53, 0.1)'
    },
    main: {
      flex: 1,
      display: 'flex',
      overflow: 'hidden'
    },
    sidebar: {
      width: '300px',
      borderRight: '1px solid #333',
      padding: '20px'
    },
    content: {
      flex: 1,
      padding: '20px',
      overflow: 'auto'
    }
  }

  const renderContent = () => {
    switch (currentView) {
      case 'empathy':
        return <EmpathyTimeline />
      case 'truth':
        return <TruthPanel />
      case 'system':
        return <SystemStatus status={systemStatus} onRefresh={checkSystemStatus} />
      default:
        return <TruthPanel />
    }
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.title}>Boardroom Shell</div>
        <nav style={styles.nav}>
          <button
            style={{
              ...styles.navButton,
              ...(currentView === 'empathy' ? styles.activeNavButton : {})
            }}
            onClick={() => setCurrentView('empathy')}
          >
            Empathy
          </button>
          <button
            style={{
              ...styles.navButton,
              ...(currentView === 'truth' ? styles.activeNavButton : {})
            }}
            onClick={() => setCurrentView('truth')}
          >
            Truth
          </button>
          <button
            style={{
              ...styles.navButton,
              ...(currentView === 'system' ? styles.activeNavButton : {})
            }}
            onClick={() => setCurrentView('system')}
          >
            System
          </button>
        </nav>
      </header>
      
      <main style={styles.main}>
        <aside style={styles.sidebar}>
          <EmpathyBanner />
          <TriosphereStatus telemetry={systemStatus.triosphere} />
        </aside>
        <div style={styles.content}>
          {renderContent()}
        </div>
      </main>
    </div>
  )
}

export default App