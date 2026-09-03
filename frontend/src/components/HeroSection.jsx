import React from 'react';

const SIZE = 140;

const styles = {
  container: {
    textAlign: 'center',
    padding: '60px 0 40px',
    animation: 'fadeInUp 0.8s ease-out',
  },
  moonWrapper: {
    position: 'relative',
    width: `${SIZE}px`,
    height: `${SIZE}px`,
    margin: '0 auto 28px',
    animation: 'float 5s ease-in-out infinite',
    perspective: '500px',
  },
  moonScene: {
    width: '100%',
    height: '100%',
    transformStyle: 'preserve-3d',
    animation: 'moonSpin3D 12s ease-in-out infinite',
  },
  face: {
    position: 'absolute',
    width: `${SIZE}px`,
    height: `${SIZE}px`,
    borderRadius: '50%',
    backfaceVisibility: 'hidden',
    overflow: 'hidden',
  },
  frontFace: {
    background: 'linear-gradient(135deg, #2a2a3a 0%, #3a3a50 25%, #4a4a60 50%, #3a3a50 75%, #2a2a3a 100%)',
  },
  backFace: {
    background: 'linear-gradient(215deg, #2a2a3a 0%, #3a3a50 25%, #4a4a60 50%, #3a3a50 75%, #2a2a3a 100%)',
    transform: 'rotateY(180deg)',
  },
  sphereShading: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    borderRadius: '50%',
    background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.08) 0%, transparent 50%, rgba(0,0,0,0.4) 80%, rgba(0,0,0,0.6) 100%)',
    pointerEvents: 'none',
    zIndex: 10,
  },
  atmosphere: {
    position: 'absolute',
    top: '-3px',
    left: '-3px',
    width: `${SIZE + 6}px`,
    height: `${SIZE + 6}px`,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(120,140,180,0.08) 60%, transparent 70%)',
    pointerEvents: 'none',
    zIndex: 0,
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
  dot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
  },
};

const frontCraters = [
  { top: '18%', left: '22%', w: 20, h: 20, bg: 'rgba(80,75,90,0.3)', shadow: 'inset 2px 1px 4px rgba(0,0,0,0.3), inset -1px -1px 2px rgba(255,255,255,0.05)' },
  { top: '50%', left: '55%', w: 16, h: 16, bg: 'rgba(75,70,85,0.25)', shadow: 'inset 1px 1px 3px rgba(0,0,0,0.25)' },
  { top: '30%', left: '62%', w: 24, h: 24, bg: 'rgba(85,80,95,0.3)', shadow: 'inset 2px 2px 5px rgba(0,0,0,0.3), inset -1px -1px 3px rgba(255,255,255,0.06)' },
  { top: '68%', left: '25%', w: 12, h: 12, bg: 'rgba(70,65,80,0.2)', shadow: 'inset 1px 1px 3px rgba(0,0,0,0.25)' },
  { top: '12%', left: '50%', w: 10, h: 10, bg: 'rgba(65,60,75,0.2)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '42%', left: '12%', w: 8, h: 8, bg: 'rgba(60,55,70,0.18)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '78%', left: '58%', w: 6, h: 6, bg: 'rgba(55,50,65,0.15)', shadow: 'inset 1px 1px 1px rgba(0,0,0,0.2)' },
  { top: '22%', left: '38%', w: 5, h: 5, bg: 'rgba(55,50,65,0.12)', shadow: 'none' },
  { top: '58%', left: '35%', w: 7, h: 7, bg: 'rgba(50,45,60,0.15)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '38%', left: '78%', w: 8, h: 8, bg: 'rgba(60,55,70,0.18)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
];

const backCraters = [
  { top: '20%', left: '60%', w: 18, h: 18, bg: 'rgba(80,75,90,0.3)', shadow: 'inset 2px 1px 4px rgba(0,0,0,0.3)' },
  { top: '55%', left: '30%', w: 22, h: 22, bg: 'rgba(75,70,85,0.25)', shadow: 'inset 2px 2px 4px rgba(0,0,0,0.25)' },
  { top: '35%', left: '20%', w: 14, h: 14, bg: 'rgba(85,80,95,0.3)', shadow: 'inset 1px 1px 3px rgba(0,0,0,0.3)' },
  { top: '70%', left: '55%', w: 10, h: 10, bg: 'rgba(70,65,80,0.2)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '15%', left: '40%', w: 8, h: 8, bg: 'rgba(65,60,75,0.2)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '45%', left: '70%', w: 12, h: 12, bg: 'rgba(60,55,70,0.18)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '80%', left: '35%', w: 6, h: 6, bg: 'rgba(55,50,65,0.15)', shadow: 'inset 1px 1px 1px rgba(0,0,0,0.2)' },
  { top: '25%', left: '75%', w: 5, h: 5, bg: 'rgba(50,45,60,0.12)', shadow: 'none' },
  { top: '65%', left: '15%', w: 7, h: 7, bg: 'rgba(50,45,60,0.15)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
  { top: '40%', left: '45%', w: 9, h: 9, bg: 'rgba(55,50,65,0.18)', shadow: 'inset 1px 1px 2px rgba(0,0,0,0.2)' },
];

function MoonFace({ craters }) {
  return (
    <>
      {craters.map((c, i) => (
        <div
          key={i}
          style={{
            ...styles.crater,
            top: c.top,
            left: c.left,
            width: `${c.w}px`,
            height: `${c.h}px`,
            background: c.bg,
            boxShadow: c.shadow,
          }}
        />
      ))}
    </>
  );
}

export default function HeroSection() {
  return (
    <div style={styles.container}>
      <div style={styles.moonWrapper}>
        <div style={styles.atmosphere} />
        <div style={styles.moonScene}>
          <div style={{ ...styles.face, ...styles.frontFace }}>
            <MoonFace craters={frontCraters} />
          </div>
          <div style={{ ...styles.face, ...styles.backFace }}>
            <MoonFace craters={backCraters} />
          </div>
        </div>
        <div style={styles.sphereShading} />
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
