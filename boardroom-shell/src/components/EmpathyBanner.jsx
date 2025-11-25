import React from 'react'

const EmpathyBanner = () => {
  const styles = {
    container: {
      background: 'linear-gradient(135deg, #2c1810 0%, #1a0f0a 100%)',
      border: '1px solid #ff6b35',
      borderRadius: '8px',
      padding: '20px',
      marginBottom: '20px',
      textAlign: 'center'
    },
    title: {
      fontSize: '18px',
      fontWeight: '600',
      color: '#ff6b35',
      marginBottom: '10px'
    },
    subtitle: {
      fontSize: '14px',
      color: '#cc9966',
      marginBottom: '15px'
    },
    message: {
      fontSize: '12px',
      color: '#999',
      lineHeight: '1.4',
      fontStyle: 'italic'
    },
    badge: {
      display: 'inline-block',
      background: 'rgba(255, 107, 53, 0.1)',
      color: '#ff6b35',
      padding: '4px 8px',
      borderRadius: '4px',
      fontSize: '10px',
      fontWeight: '500',
      marginTop: '10px',
      border: '1px solid rgba(255, 107, 53, 0.3)'
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.title}>SOVEREIGN EMPATHY</div>
      <div style={styles.subtitle}>Truth with Human Context</div>
      <div style={styles.message}>
        "Every search honors both precision and humanity.
        Every result respects both facts and feelings."
      </div>
      <div style={styles.badge}>PHASE 4 ACTIVE</div>
    </div>
  )
}

export default EmpathyBanner