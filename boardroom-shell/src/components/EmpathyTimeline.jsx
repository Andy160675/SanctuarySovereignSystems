import React from 'react'

const EmpathyTimeline = () => {
  const milestones = [
    {
      phase: 'Phase 1',
      title: 'Foundation',
      date: '2025-11-01',
      status: 'complete',
      description: 'Core architecture and truth engine'
    },
    {
      phase: 'Phase 2',
      title: 'Integration',
      date: '2025-11-10',
      status: 'complete',
      description: 'Docker containers and search API'
    },
    {
      phase: 'Phase 3',
      title: 'Interface',
      date: '2025-11-15',
      status: 'active',
      description: 'Electron UI and user experience'
    },
    {
      phase: 'Phase 4',
      title: 'Sovereign',
      date: '2025-11-19',
      status: 'active',
      description: 'Full system deployment and testing'
    },
    {
      phase: 'Phase 5',
      title: 'Evolution',
      date: '2026-02-05',
      status: 'active',
      description: 'Triosphere Architecture & Software Orchestration'
    },
    {
      phase: 'Phase 6',
      title: 'Closure',
      date: 'TBD',
      status: 'pending',
      description: 'Full autonomy and final mission'
    }
  ]

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
    timeline: {
      position: 'relative'
    },
    milestone: {
      display: 'flex',
      alignItems: 'center',
      marginBottom: '30px',
      position: 'relative'
    },
    indicator: {
      width: '16px',
      height: '16px',
      borderRadius: '50%',
      marginRight: '20px',
      flexShrink: 0,
      zIndex: 2
    },
    complete: {
      background: '#4caf50'
    },
    active: {
      background: '#ff6b35',
      boxShadow: '0 0 10px rgba(255, 107, 53, 0.5)'
    },
    pending: {
      background: '#666',
      border: '2px solid #444'
    },
    content: {
      flex: 1
    },
    phase: {
      fontSize: '14px',
      color: '#ff6b35',
      fontWeight: '600'
    },
    milestoneTitle: {
      fontSize: '18px',
      color: '#e0e0e0',
      marginBottom: '5px'
    },
    description: {
      fontSize: '14px',
      color: '#999',
      marginBottom: '5px'
    },
    date: {
      fontSize: '12px',
      color: '#666'
    },
    line: {
      position: 'absolute',
      left: '7px',
      top: '16px',
      bottom: '-14px',
      width: '2px',
      background: '#333'
    }
  }

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Development Timeline</h2>
      <div style={styles.timeline}>
        {milestones.map((milestone, index) => (
          <div key={milestone.phase} style={styles.milestone}>
            {index < milestones.length - 1 && <div style={styles.line} />}
            <div
              style={{
                ...styles.indicator,
                ...styles[milestone.status]
              }}
            />
            <div style={styles.content}>
              <div style={styles.phase}>{milestone.phase}</div>
              <div style={styles.milestoneTitle}>{milestone.title}</div>
              <div style={styles.description}>{milestone.description}</div>
              <div style={styles.date}>{milestone.date}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default EmpathyTimeline