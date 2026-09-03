import React from 'react';

const steps = [
  { id: 1, label: 'Upload', icon: '⬆' },
  { id: 2, label: 'Process', icon: '⚙' },
  { id: 3, label: 'Results', icon: '✓' },
];

const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0',
    padding: '20px 0 40px',
    animation: 'fadeIn 0.6s ease-out 0.2s both',
  },
  step: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
    position: 'relative',
    zIndex: 1,
  },
  circle: (isActive, isCompleted) => ({
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '18px',
    fontWeight: 600,
    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
    background: isCompleted
      ? 'linear-gradient(135deg, var(--success) 0%, #16a34a 100%)'
      : isActive
      ? 'linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%)'
      : 'var(--glass)',
    border: isCompleted
      ? '2px solid var(--success)'
      : isActive
      ? '2px solid var(--accent)'
      : '2px solid var(--glass-border)',
    boxShadow: isActive
      ? '0 0 24px var(--accent-glow)'
      : isCompleted
      ? '0 0 16px var(--success-glow)'
      : 'none',
    color: isCompleted || isActive ? 'white' : 'var(--text-muted)',
  }),
  label: (isActive, isCompleted) => ({
    fontSize: '12px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: isCompleted
      ? 'var(--success)'
      : isActive
      ? 'var(--accent-light)'
      : 'var(--text-muted)',
    transition: 'color 0.3s ease',
  }),
  connector: (isCompleted, isActive) => ({
    width: '80px',
    height: '2px',
    margin: '0 -8px',
    marginBottom: '28px',
    background: isCompleted
      ? 'var(--success)'
      : isActive
      ? 'linear-gradient(90deg, var(--accent), var(--glass-border))'
      : 'var(--glass-border)',
    transition: 'background 0.4s ease',
    position: 'relative',
    zIndex: 0,
  }),
  checkmark: {
    fontSize: '16px',
    lineHeight: 1,
  },
};

export default function StepIndicator({ currentStep }) {
  return (
    <div style={styles.container}>
      {steps.map((step, index) => {
        const isCompleted = currentStep > step.id;
        const isActive = currentStep === step.id;
        const isLast = index === steps.length - 1;

        return (
          <React.Fragment key={step.id}>
            <div style={styles.step}>
              <div style={styles.circle(isActive, isCompleted)}>
                {isCompleted ? (
                  <span style={styles.checkmark}>✓</span>
                ) : (
                  <span>{step.icon}</span>
                )}
              </div>
              <span style={styles.label(isActive, isCompleted)}>{step.label}</span>
            </div>
            {!isLast && (
              <div style={styles.connector(isCompleted, isActive)} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
