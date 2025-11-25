import React from 'react'

const SystemStatus = ({ status, onRefresh }) => {
  const getStatusColor = (state) => {
    switch (state) {
      case 'active': return '#4caf50'
      case 'checking': return '#ff9800'
      case 'offline': return '#f44336'
      default: return '#666'
    }
  }

  const getStatusText = (state) => {
    switch (state) {
      case 'active': return 'ACTIVE'
      case 'checking': return 'CHECKING'
      case 'offline': return 'OFFLINE'
      default: return 'UNKNOWN'
    }
  }

  const styles = {
    container: {
      padding: '20px'
    },
    title: {
      fontSize: '24px',
      color: '#ff6b35',
      marginBottom: '30px',
      textAlign: 'center'
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
      gap: '20px',
      marginBottom: '30px'
    },
    card: {
      background: '#1a1a1a',
      border: '1px solid #333',
      borderRadius: '8px',
      padding: '20px'
    },
    cardTitle: {
      fontSize: '18px',
      color: '#e0e0e0',
      marginBottom: '15px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    },
    status: {
      fontSize: '12px',
      fontWeight: '600',
      padding: '4px 8px',
      borderRadius: '4px',
      border: '1px solid'
    },
    description: {
      fontSize: '14px',
      color: '#999',
      lineHeight: '1.5'
    },
    refreshButton: {
      background: '#ff6b35',
      color: 'white',
      border: 'none',
      padding: '12px 24px',
      borderRadius: '6px',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500',
      display: 'block',
      margin: '0 auto'
    },
    info: {
      background: '#1a1a1a',
      border: '1px solid #333',
      borderRadius: '8px',
      padding: '20px',
      marginTop: '20px'
    },
    infoTitle: {
      fontSize: '16px',
      color: '#ff6b35',
      marginBottom: '15px'
    },
    infoList: {
      listStyle: 'none',
      padding: 0
    },
    infoItem: {
      fontSize: '14px',
      color: '#ccc',
      marginBottom: '8px',
      display: 'flex',
      justifyContent: 'space-between'
    },
    label: {
      color: '#999'
    },
    value: {
      color: '#e0e0e0',
      fontWeight: '500'
    }
  }

  const services = [
    {
      name: 'Truth Engine',
      key: 'truthEngine',
      description: 'txtai + FastAPI search service',
      endpoint: 'http://localhost:5050'
    },
    {
      name: 'Ollama',
      key: 'ollama',
      description: 'Local LLM inference server',
      endpoint: 'http://localhost:11434'
    },
    {
      name: 'Index',
      key: 'index',
      description: 'Sovereign corpus embeddings',
      endpoint: 'Local filesystem'
    }
  ]

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>System Status</h2>
      
      <div style={styles.grid}>
        {services.map(service => {
          const serviceStatus = status[service.key]
          const statusColor = getStatusColor(serviceStatus)
          
          return (
            <div key={service.key} style={styles.card}>
              <div style={styles.cardTitle}>
                {service.name}
                <span
                  style={{
                    ...styles.status,
                    color: statusColor,
                    borderColor: statusColor
                  }}
                >
                  {getStatusText(serviceStatus)}
                </span>
              </div>
              <div style={styles.description}>
                {service.description}
                <br />
                <small style={{ color: '#666' }}>Endpoint: {service.endpoint}</small>
              </div>
            </div>
          )
        })}
      </div>

      <button style={styles.refreshButton} onClick={onRefresh}>
        Refresh Status
      </button>

      <div style={styles.info}>
        <div style={styles.infoTitle}>System Information</div>
        <ul style={styles.infoList}>
          <li style={styles.infoItem}>
            <span style={styles.label}>Platform:</span>
            <span style={styles.value}>{window.electronAPI?.platform || 'Unknown'}</span>
          </li>
          <li style={styles.infoItem}>
            <span style={styles.label}>Electron:</span>
            <span style={styles.value}>{window.electronAPI?.version || 'Unknown'}</span>
          </li>
          <li style={styles.infoItem}>
            <span style={styles.label}>Phase:</span>
            <span style={styles.value}>4 (Sovereign)</span>
          </li>
          <li style={styles.infoItem}>
            <span style={styles.label}>Build:</span>
            <span style={styles.value}>2025-11-19</span>
          </li>
        </ul>
      </div>
    </div>
  )
}

export default SystemStatus