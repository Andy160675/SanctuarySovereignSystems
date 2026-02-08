import React, { useState, useEffect } from 'react'
import EventRelay from '../EventRelay'

const TruthPanel = () => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [systemState, setSystemState] = useState({})

  useEffect(() => {
    // Listen to system updates from EventRelay
    const handleSystemUpdate = (state) => {
      setSystemState(state)
    }
    
    EventRelay.on('systemUpdate', handleSystemUpdate)
    setSystemState(EventRelay.getState())
    
    return () => {
      EventRelay.off('systemUpdate', handleSystemUpdate)
    }
  }, [])

  const handleSearch = async () => {
    if (!query.trim()) return
    
    setLoading(true)
    setError(null)
    
    try {
      EventRelay.emit('searchStart', { query })
      
      const truthUrl = process.env.TRUTH_ENGINE_URL || 'http://localhost:5050'
      const response = await fetch(`${truthUrl}/search?q=${encodeURIComponent(query)}&limit=10`)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      setResults(data.results || [])
      EventRelay.updateState({ truthEngine: 'active' })
      EventRelay.emit('searchComplete', { query, results: data.results?.length || 0 })
      
    } catch (err) {
      setError(err.message)
      setResults([])
      EventRelay.updateState({ truthEngine: 'offline' })
      EventRelay.emit('searchError', { query, error: err.message })
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const styles = {
    container: {
      padding: '20px'
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '30px'
    },
    title: {
      fontSize: '24px',
      color: '#ff6b35'
    },
    statusBadge: {
      fontSize: '12px',
      padding: '4px 8px',
      borderRadius: '4px',
      fontWeight: '600'
    },
    searchBox: {
      marginBottom: '30px'
    },
    searchInput: {
      width: '100%',
      padding: '15px',
      fontSize: '16px',
      background: '#1a1a1a',
      border: '1px solid #444',
      borderRadius: '8px',
      color: '#e0e0e0',
      marginBottom: '10px',
      outline: 'none'
    },
    searchButton: {
      background: '#ff6b35',
      color: 'white',
      border: 'none',
      padding: '12px 24px',
      borderRadius: '6px',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500'
    },
    results: {
      marginTop: '20px'
    },
    result: {
      background: '#1a1a1a',
      border: '1px solid #333',
      borderRadius: '8px',
      padding: '20px',
      marginBottom: '15px'
    },
    resultTitle: {
      fontSize: '16px',
      color: '#ff6b35',
      marginBottom: '10px',
      fontWeight: '500'
    },
    resultText: {
      fontSize: '14px',
      color: '#ccc',
      lineHeight: '1.5'
    },
    resultMeta: {
      fontSize: '12px',
      color: '#666',
      marginTop: '10px',
      padding: '5px 0',
      borderTop: '1px solid #333'
    },
    loading: {
      textAlign: 'center',
      color: '#ff6b35',
      padding: '40px'
    },
    error: {
      background: 'rgba(255, 0, 0, 0.1)',
      border: '1px solid rgba(255, 0, 0, 0.3)',
      borderRadius: '6px',
      padding: '15px',
      color: '#ff6666',
      marginTop: '15px'
    },
    noResults: {
      textAlign: 'center',
      color: '#666',
      padding: '40px',
      fontStyle: 'italic'
    }
  }

  const getStatusColor = () => {
    switch (systemState.truthEngine) {
      case 'active': return { background: 'rgba(76, 175, 80, 0.2)', color: '#4caf50' }
      case 'checking': return { background: 'rgba(255, 152, 0, 0.2)', color: '#ff9800' }
      default: return { background: 'rgba(244, 67, 54, 0.2)', color: '#f44336' }
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>Truth Engine Search</h2>
        <span style={{
          ...styles.statusBadge,
          ...getStatusColor()
        }}>
          {systemState.truthEngine?.toUpperCase() || 'UNKNOWN'}
        </span>
      </div>
      
      <div style={styles.searchBox}>
        <input
          type="text"
          placeholder="Search the sovereign corpus..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          style={styles.searchInput}
        />
        <button
          onClick={handleSearch}
          disabled={loading || systemState.truthEngine === 'offline'}
          style={{
            ...styles.searchButton,
            opacity: (loading || systemState.truthEngine === 'offline') ? 0.6 : 1
          }}
        >
          {loading ? 'Searching...' : 'Search Truth'}
        </button>
      </div>

      {error && (
        <div style={styles.error}>
          Error: {error}
        </div>
      )}

      {loading && (
        <div style={styles.loading}>
          Searching sovereign corpus...
        </div>
      )}

      {!loading && results.length === 0 && query && !error && (
        <div style={styles.noResults}>
          No results found for "{query}"
        </div>
      )}

      <div style={styles.results}>
        {results.map((result, index) => (
          <div key={index} style={styles.result}>
            <div style={styles.resultTitle}>
              Document {index + 1} (Score: {result.score?.toFixed(3) || 'N/A'})
            </div>
            <div style={styles.resultText}>
              {result.text || result.content || 'No content available'}
            </div>
            <div style={styles.resultMeta}>
              {result.id && `Source: ${result.id}`}
              {result.path && ` | Path: ${result.path}`}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default TruthPanel