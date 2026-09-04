import React, { useState, useEffect } from 'react';

const pipelineSteps = [
  { id: 'ingest', label: 'Ingest', icon: '📂', desc: 'Loading formats' },
  { id: 'preprocess', label: 'Preprocess', icon: '🔧', desc: 'Cleaning images' },
  { id: 'pyramid', label: 'Pyramid', icon: '🔺', desc: 'Scale analysis' },
  { id: 'features', label: 'Features', icon: '🔍', desc: 'Detecting points' },
  { id: 'match', label: 'Match', icon: '🔗', desc: 'Matching features' },
  { id: 'transform', label: 'Transform', icon: '📐', desc: 'Estimating warp' },
  { id: 'warp', label: 'Warp', icon: '🔄', desc: 'Aligning images' },
  { id: 'evaluate', label: 'Evaluate', icon: '📊', desc: 'Computing metrics' },
];

const styles = {
  container: {
    animation: 'fadeIn 0.5s ease-out',
  },
  title: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '22px',
    fontWeight: 600,
    textAlign: 'center',
    marginBottom: '8px',
    color: 'var(--text-primary)',
  },
  subtitle: {
    textAlign: 'center',
    fontSize: '14px',
    color: 'var(--text-secondary)',
    marginBottom: '32px',
  },
  pipeline: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    maxWidth: '500px',
    margin: '0 auto',
  },
  stepRow: (isCompleted, isActive) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    padding: '12px 16px',
    borderRadius: '12px',
    background: isActive
      ? 'rgba(18, 19, 88, 0.1)'
      : isCompleted
      ? 'rgba(34, 197, 94, 0.06)'
      : 'transparent',
    border: `1px solid ${isActive ? 'rgba(18, 19, 88, 0.3)' : isCompleted ? 'rgba(34, 197, 94, 0.15)' : 'transparent'}`,
    transition: 'all 0.4s ease',
  }),
  stepIcon: (isCompleted, isActive) => ({
    width: '36px',
    height: '36px',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '16px',
    background: isActive
      ? 'linear-gradient(135deg, var(--accent), var(--purple))'
      : isCompleted
      ? 'linear-gradient(135deg, var(--success), #16a34a)'
      : 'var(--glass)',
    boxShadow: isActive ? '0 0 16px var(--accent-glow)' : isCompleted ? '0 0 8px var(--success-glow)' : 'none',
    flexShrink: 0,
    transition: 'all 0.4s ease',
  }),
  stepInfo: {
    flex: 1,
  },
  stepLabel: (isCompleted, isActive) => ({
    fontSize: '14px',
    fontWeight: 600,
    color: isActive ? 'var(--accent-light)' : isCompleted ? 'var(--success)' : 'var(--text-muted)',
    transition: 'color 0.3s ease',
  }),
  stepDesc: (isCompleted, isActive) => ({
    fontSize: '12px',
    color: isActive ? 'var(--text-secondary)' : 'var(--text-muted)',
    marginTop: '2px',
  }),
  stepStatus: (isCompleted, isActive) => ({
    fontSize: '11px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    padding: '3px 8px',
    borderRadius: '4px',
    background: isActive
      ? 'rgba(18, 19, 88, 0.2)'
      : isCompleted
      ? 'rgba(34, 197, 94, 0.15)'
      : 'var(--glass)',
    color: isActive ? 'var(--accent-light)' : isCompleted ? 'var(--success)' : 'var(--text-muted)',
    flexShrink: 0,
  }),
  progressBar: {
    maxWidth: '500px',
    margin: '24px auto 0',
    height: '4px',
    borderRadius: '2px',
    background: 'var(--glass)',
    overflow: 'hidden',
  },
  progressFill: (progress) => ({
    width: `${progress}%`,
    height: '100%',
    borderRadius: '2px',
    background: 'linear-gradient(90deg, var(--accent), var(--purple))',
    transition: 'width 0.3s ease',
    boxShadow: '0 0 12px var(--accent-glow)',
  }),
  spinner: {
    width: '16px',
    height: '16px',
    border: '2px solid var(--glass-border)',
    borderTopColor: 'var(--accent)',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    flexShrink: 0,
  },
};

export default function ProcessingView({ status }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState(new Set());

  useEffect(() => {
    if (status !== 'polling') return;

    const interval = setInterval(() => {
      setActiveIndex((prev) => {
        if (prev >= pipelineSteps.length - 1) return prev;
        setCompletedSteps((s) => new Set([...s, pipelineSteps[prev].id]));
        return prev + 1;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [status]);

  const progress = ((activeIndex + 1) / pipelineSteps.length) * 100;

  return (
    <div style={styles.container}>
      <div style={styles.title}>Processing Registration</div>
      <div style={styles.subtitle}>
        {status === 'polling' ? 'Analyzing and aligning your images...' : 'Starting pipeline...'}
      </div>

      <div style={styles.pipeline}>
        {pipelineSteps.map((step, index) => {
          const isCompleted = completedSteps.has(step.id);
          const isActive = index === activeIndex && status === 'polling';

          return (
            <div key={step.id} style={styles.stepRow(isCompleted, isActive)}>
              <div style={styles.stepIcon(isCompleted, isActive)}>
                {isCompleted ? '✓' : step.icon}
              </div>
              <div style={styles.stepInfo}>
                <div style={styles.stepLabel(isCompleted, isActive)}>{step.label}</div>
                <div style={styles.stepDesc(isCompleted, isActive)}>{step.desc}</div>
              </div>
              <div style={styles.stepStatus(isCompleted, isActive)}>
                {isCompleted ? 'Done' : isActive ? 'Active' : 'Pending'}
              </div>
              {isActive && <div style={styles.spinner} />}
            </div>
          );
        })}
      </div>

      <div style={styles.progressBar}>
        <div style={styles.progressFill(progress)} />
      </div>
    </div>
  );
}
