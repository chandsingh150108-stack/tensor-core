import React from 'react';

const styles = {
  container: {
    textAlign: 'center',
    padding: '60px 0 40px',
    animation: 'fadeInUp 0.8s ease-out',
  },
  moonIcon: {
    width: '80px',
    height: '80px',
    margin: '0 auto 24px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%)',
    boxShadow: '0 0 60px rgba(59, 130, 246, 0.3), inset -8px -4px 16px rgba(0,0,0,0.4), inset 4px 2px 8px rgba(255,255,255,0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    animation: 'float 4s ease-in-out infinite',
    position: 'relative',
  },
  moonCrater: {
    position: 'absolute',
    borderRadius: '50%',
    background: 'rgba(0,0,0,0.2)',
  },
  title: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: 'clamp(32px, 5vw, 56px)',
    fontWeight: 700,
    lineHeight: 1.1,
    marginBottom: '16px',
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontSize: 'clamp(14px, 2vw, 17px)',
    color: 'var(--text-secondary)',
    maxWidth: '640px',
    margin: '0 auto 24px',
    lineHeight: 1.7,
  },
  badges: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 14px',
    borderRadius: '20px',
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
    fontSize: '12px',
    fontWeight: 500,
    color: 'var(--text-secondary)',
  },
  dot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
  },
};

const craters = [
  { top: '20%', left: '25%', width: '12px', height: '12px' },
  { top: '45%', left: '60%', width: '8px', height: '8px' },
  { top: '65%', left: '35%', width: '10px', height: '10px' },
  { top: '30%', left: '70%', width: '6px', height: '6px' },
];

export default function HeroSection() {
  return (
    <div style={styles.container}>
      <div style={styles.moonIcon}>
        {craters.map((c, i) => (
          <div key={i} style={{ ...styles.moonCrater, ...c }} />
        ))}
      </div>

      <h1 style={styles.title}>
        <span className="gradient-text">Lunar Image Registration</span>
      </h1>

      <p style={styles.subtitle}>
        Multi-scale satellite image alignment for ISRO Chandrayaan-2 missions.
        Automatically register images across different sensors, resolutions, and lighting conditions.
      </p>

      <div style={styles.badges}>
        <span style={styles.badges}>
          <span style={{ ...styles.dot, background: 'var(--accent)' }} />
          ISRO Chandrayaan-2
        </span>
        <span style={styles.badges}>
          <span style={{ ...styles.dot, background: 'var(--cyan)' }} />
          AI-Powered Routing
        </span>
      </div>
    </div>
  );
}
