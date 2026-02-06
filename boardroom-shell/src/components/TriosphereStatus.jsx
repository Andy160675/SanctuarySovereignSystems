import React from 'react'

const TriosphereStatus = ({ telemetry }) => {
  const spheres = [
    { id: 'intent', name: 'IntentSphere', description: 'Governance & Logic' },
    { id: 'evidence', name: 'EvidenceSphere', description: 'Immutable Ledger' },
    { id: 'action', name: 'ActionSphere', description: 'Actuator & Effect' }
  ]

  const styles = {
    container: {
      marginTop: '20px',
      padding: '15px',
      background: '#151515',
      border: '1px solid #333',
      borderRadius: '8px'
    },
    title: {
      fontSize: '14px',
      color: '#ff6b35',
      marginBottom: '15px',
      fontWeight: '600',
      letterSpacing: '0.05em'
    },
    sphereGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '10px'
    },
    sphereCard: {
      padding: '10px',
      background: '#202020',
      border: '1px solid #444',
      borderRadius: '4px',
      textAlign: 'center'
    },
    sphereName: {
      fontSize: '12px',
      color: '#e0e0e0',
      marginBottom: '5px'
    },
    sphereStatus: {
      fontSize: '10px',
      fontWeight: '700',
      padding: '2px 6px',
      borderRadius: '3px'
    },
    active: {
      background: 'rgba(76, 175, 80, 0.1)',
      color: '#4caf50',
      border: '1px solid #4caf50'
    },
    inactive: {
      background: 'rgba(244, 67, 54, 0.1)',
      color: '#f44336',
      border: '1px solid #f44336'
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.title}>TRIOSPHERE TELEMETRY</div>
      <div style={styles.sphereGrid}>
        {spheres.map(s => (
          <div key={s.id} style={styles.sphereCard}>
            <div style={styles.sphereName}>{s.name}</div>
            <span style={{
              ...styles.sphereStatus,
              ...(telemetry?.[s.id] === 'active' ? styles.active : styles.inactive)
            }}>
              {telemetry?.[s.id] === 'active' ? 'PROTECTED' : 'OFFLINE'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default TriosphereStatus
