import React from 'react';

const styles = {
  container: {
    textAlign: 'center',
    padding: '60px 0 40px',
    animation: 'fadeInUp 0.8s ease-out',
  },
  moonWrapper: {
    position: 'relative',
    width: '140px',
    height: '140px',
    margin: '0 auto 28px',
    animation: 'float 5s ease-in-out infinite',
    perspective: '600px',
  },
  moon: {
    width: '140px',
    height: '140px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #2a2a3a 0%, #3a3a50 25%, #4a4a60 50%, #3a3a50 75%, #2a2a3a 100%)',
    animation: 'moonSpin3D 8s ease-in-out infinite',
    boxShadow: `
      0 0 40px rgba(120, 130, 160, 0.15),
      0 0 80px rgba(80, 100, 140, 0.1),
      inset -20px -8px 30px rgba(0,0,0,0.5),
      inset 6px 3px 12px rgba(255,255,255,0.08)
    `,
    position: 'relative',
    overflow: 'hidden',
  },
  crescentShadow: {
    position: 'absolute',
    top: 0,
    right: 0,
    width: '50%',
    height: '100%',
    borderRadius: '0 70px 70px 0',
    background: 'linear-gradient(90deg, transparent 0%, rgba(0,0,0,0.35) 60%, rgba(0,0,0,0.6) 100%)',
    pointerEvents: 'none',
  },
  surface: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    borderRadius: '50%',
    background: `
      radial-gradient(circle at 25% 35%, rgba(60,55,70,0.6) 0%, transparent 15%),
      radial-gradient(circle at 65% 25%, rgba(50,45,60,0.5) 0%, transparent 10%),
      radial-gradient(circle at 45% 65%, rgba(55,50,65,0.4) 0%, transparent 12%),
      radial-gradient(circle at 75% 60%, rgba(45,40,55,0.5) 0%, transparent 8%),
      radial-gradient(circle at 30% 75%, rgba(50,45,60,0.4) 0%, transparent 9%)
    `,
    pointerEvents: 'none',
  },
  crater: {
    position: 'absolute',
    borderRadius: '50%',
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
  // Large craters with inner shadow
  { top: '18%', left: '22%', w: 22, h: 22, inner: 'rgba(80,75,90,0.3)', shadow: 'inset 2px 1px 4px rgba(0,0,0,0.3), inset -1px -1px 2px rgba(255,255,255,0.05)' },
  { top: '55%', left: '58%', w: 18, h: 18, inner: 'rgba(75,70,85,0.25)', shadow: 'inset 1px 1px 3px rgba(0,0,0,0.25), inset -1px -1px 2px rgba(255,255,255,0.04)' },
  { top: '35%', left: '65%', w: 26, h: 26, inner: 'rgba(85,80,95,0.3)', shadow: 'inset 2px 2px 5px rgba(0,0,0,0.3), inset -1px -1px 3px rgba(255,255,255,0.06)' },
  // Medium craters
  { top: '70%', left: '25%', w: 14, h: 14, inner: 'rgba(70,65,80,0.2)', shadow: 'inset 1px 1px 3px rgba(0,0,0,0.25)' },
  { top: '15%', left: '55%', w: 12, h: 12, inner: 'rgba(65,60,75,0.2)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '45%', left: '15%', w: 10, h: 10, inner: 'rgba(60,55,70,0.18)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  // Small craters / surface dots
  { top: '80%', left: '60%', w: 6, h: 6, inner: 'rgba(55,50,65,0.15)', shadow: 'inset 1px 1px 1px rgba(0,0,0,0.2)' },
  { top: '25%', left: '42%', w: 5, h: 5, inner: 'rgba(55,50,65,0.12)', shadow: 'inset 0.5px 0.5px 1px rgba(0,0,0,0.15)' },
  { top: '60%', left: '38%', w: 7, h: 7, inner: 'rgba(50,45,60,0.15)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '40%', left: '80%', w: 8, h: 8, inner: 'rgba(60,55,70,0.18)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '85%', left: '40%', w: 4, h: 4, inner: 'rgba(50,45,60,0.1)', shadow: 'none' },
  { top: '10%', left: '35%', w: 3, h: 3, inner: 'rgba(50,45,60,0.1)', shadow: 'none' },
];

export default function HeroSection() {
  return (
    <div style={styles.container}>
      <div style={styles.moonWrapper}>
        <div style={styles.moon}>
          <div style={styles.surface} />
          {craters.map((c, i) => (
            <div
              key={i}
              style={{
                ...styles.crater,
                top: c.top,
                left: c.left,
                width: `${c.w}px`,
                height: `${c.h}px`,
                background: c.inner,
                boxShadow: c.shadow,
              }}
            />
          ))}
          <div style={styles.crescentShadow} />
        </div>
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
