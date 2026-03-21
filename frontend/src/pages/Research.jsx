// frontend/src/pages/Research.jsx
import { useState } from 'react'
import { runResearch } from '../services/api'
import ReactMarkdown from 'react-markdown'
import styles from './Research.module.css'

export default function Research() {
  const [query,    setQuery]   = useState('')
  const [loading,  setLoading] = useState(false)
  const [result,   setResult]  = useState(null)
  const [error,    setError]   = useState(null)

  const handleResearch = async () => {
    if (!query.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await runResearch(query.trim())
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter') handleResearch()
  }

  const scoreColor = (score) => {
    if (score >= 8) return styles.scoreGreen
    if (score >= 6) return styles.scoreAmber
    return styles.scoreRed
  }

  return (
    <div className={styles.page}>
      <div className={styles.inner}>

        {/* Header */}
        <div className={styles.header}>
          <span className={styles.headerIcon}>⊹</span>
          <div>
            <h1 className={styles.title}>Deep Research</h1>
            <p className={styles.subtitle}>AI searches the web, writes a summary, then self-critiques</p>
          </div>
        </div>

        {/* Pipeline indicator */}
        <div className={styles.pipeline}>
          {['Search web', 'Summarise', 'Critique', 'Score'].map((step, i) => (
            <div key={step} className={styles.pipelineStep}>
              <div className={`${styles.stepDot} ${loading ? styles.stepActive : ''}`}
                style={{ animationDelay: `${i * 0.2}s` }}
              />
              <span className={styles.stepLabel}>{step}</span>
              {i < 3 && <span className={styles.stepArrow}>→</span>}
            </div>
          ))}
        </div>

        {/* Input */}
        <div className={styles.inputRow}>
          <input
            className={styles.input}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder="What do you want to research?"
            disabled={loading}
          />
          <button
            className={`${styles.btn} ${query.trim() && !loading ? styles.btnActive : ''}`}
            onClick={handleResearch}
            disabled={!query.trim() || loading}
          >
            {loading ? <span className={styles.spinner} /> : 'Research →'}
          </button>
        </div>

        {loading && (
          <div className={styles.loadingState}>
            <div className={styles.loadingDots}>
              <span /><span /><span />
            </div>
            <p className={styles.loadingText}>Searching and analysing… this takes ~30 seconds</p>
          </div>
        )}

        {error && (
          <div className={styles.errorBanner}>⚠ {error}</div>
        )}

        {result && (
          <div className={styles.results}>

            {/* Summary */}
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardIcon}>◆</span>
                <span className={styles.cardTitle}>Research Summary</span>
                <span className={`${styles.verdict} ${result.passed ? styles.verdictPass : styles.verdictFail}`}>
                  {result.passed ? '✓ PASS' : '✗ FAIL'}
                </span>
                {result.attempts > 1 && (
                  <span className={styles.attempts}>{result.attempts} attempts</span>
                )}
              </div>
              <div className={styles.cardBody}>
                <ReactMarkdown>{result.summary}</ReactMarkdown>
              </div>
            </div>

            {/* Critique scores */}
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardIcon}>⊹</span>
                <span className={styles.cardTitle}>Quality Critique</span>
                <span className={`${styles.overallScore} ${scoreColor(result.critique.overall_score)}`}>
                  {result.critique.overall_score}/10
                </span>
              </div>
              <div className={styles.cardBody}>
                {/* Score bars */}
                <div className={styles.scores}>
                  {Object.entries(result.critique.scores).map(([key, val]) => (
                    <div key={key} className={styles.scoreRow}>
                      <span className={styles.scoreKey}>{key.replace('_', ' ')}</span>
                      <div className={styles.scoreBar}>
                        <div
                          className={styles.scoreBarFill}
                          style={{ width: `${val * 10}%`, opacity: 0.5 + val * 0.05 }}
                        />
                      </div>
                      <span className={styles.scoreVal}>{val}/10</span>
                    </div>
                  ))}
                </div>

                {/* Feedback */}
                <div className={styles.feedback}>
                  <p className={styles.feedbackLabel}>Feedback</p>
                  <p className={styles.feedbackText}>{result.critique.feedback}</p>
                </div>

                {/* Strengths & weaknesses */}
                <div className={styles.swRow}>
                  {result.critique.strengths?.length > 0 && (
                    <div className={styles.swBox}>
                      <p className={styles.swLabel}>Strengths</p>
                      {result.critique.strengths.map((s, i) => (
                        <p key={i} className={styles.swItem}>+ {s}</p>
                      ))}
                    </div>
                  )}
                  {result.critique.weaknesses?.length > 0 && (
                    <div className={styles.swBox}>
                      <p className={styles.swLabel}>Weaknesses</p>
                      {result.critique.weaknesses.map((w, i) => (
                        <p key={i} className={styles.swItem}>− {w}</p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  )
}
