import React, { useState, useRef, useCallback, useEffect } from 'react';

const styles = {
  container: {
    animation: 'fadeInUp 0.5s ease-out',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '16px',
  },
  title: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '18px',
    fontWeight: 600,
  },
  modeToggle: {
    display: 'flex',
    gap: '4px',
    padding: '3px',
    borderRadius: '8px',
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
  },
  modeBtn: (isActive) => ({
    padding: '6px 14px',
    borderRadius: '6px',
    border: 'none',
    background: isActive ? 'var(--accent)' : 'transparent',
    color: isActive ? 'white' : 'var(--text-muted)',
    fontSize: '12px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  }),
  comparisonWrapper: {
    position: 'relative',
    borderRadius: '12px',
    overflow: 'hidden',
    border: '1px solid var(--glass-border)',
    background: '#000',
    userSelect: 'none',
    touchAction: 'none',
  },
  sliderContainer: {
    position: 'relative',
    width: '100%',
    aspectRatio: '16/10',
    overflow: 'hidden',
  },
  imageBase: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    objectFit: 'contain',
  },
  imageOverlay: (clipPercent) => ({
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    clipPath: `inset(0 ${100 - clipPercent}% 0 0)`,
  }),
  sliderLine: (leftPercent) => ({
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: `${leftPercent}%`,
    width: '3px',
    background: 'white',
    boxShadow: '0 0 12px rgba(255,255,255,0.5)',
    transform: 'translateX(-50%)',
    zIndex: 10,
    pointerEvents: 'none',
  }),
  sliderHandle: (leftPercent) => ({
    position: 'absolute',
    top: '50%',
    left: `${leftPercent}%`,
    transform: 'translate(-50%, -50%)',
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    background: 'white',
    border: '3px solid var(--accent)',
    boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)',
    cursor: 'ew-resize',
    zIndex: 11,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    color: 'var(--accent)',
    fontWeight: 700,
    transition: 'box-shadow 0.2s ease',
  }),
  label: (side) => ({
    position: 'absolute',
    top: '12px',
    [side]: '12px',
    padding: '4px 10px',
    borderRadius: '6px',
    background: 'rgba(0,0,0,0.6)',
    backdropFilter: 'blur(4px)',
    fontSize: '11px',
    fontWeight: 600,
    color: 'white',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    zIndex: 5,
  }),
  sideBySide: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
  },
  sidePanel: {
    position: 'relative',
    borderRadius: '12px',
    overflow: 'hidden',
    border: '1px solid var(--glass-border)',
    background: '#000',
  },
  sideImage: {
    width: '100%',
    aspectRatio: '16/10',
    objectFit: 'contain',
    display: 'block',
  },
  sideLabel: {
    position: 'absolute',
    top: '8px',
    left: '8px',
    padding: '4px 10px',
    borderRadius: '6px',
    background: 'rgba(0,0,0,0.6)',
    backdropFilter: 'blur(4px)',
    fontSize: '11px',
    fontWeight: 600,
    color: 'white',
    textTransform: 'uppercase',
  },
};

export default function ImageComparison({ sourceImage, warpedImage, jobId }) {
  const [mode, setMode] = useState('slider');
  const [sliderPos, setSliderPos] = useState(50);
  const containerRef = useRef(null);
  const isDragging = useRef(false);

  const overlayUrl = jobId ? `/report/${jobId}/overlay` : null;

  const handleMouseDown = useCallback(() => {
    isDragging.current = true;
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (!isDragging.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    setSliderPos(Math.max(5, Math.min(95, x)));
  }, []);

  const handleMouseUp = useCallback(() => {
    isDragging.current = false;
  }, []);

  const handleTouchStart = useCallback(() => {
    isDragging.current = true;
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (!isDragging.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.touches[0].clientX - rect.left) / rect.width) * 100;
    setSliderPos(Math.max(5, Math.min(95, x)));
  }, []);

  useEffect(() => {
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('touchend', handleMouseUp);
    return () => {
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, [handleMouseUp, handleMouseMove]);

  if (!sourceImage && !warpedImage) return null;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.title}>Image Comparison</div>
        <div style={styles.modeToggle}>
          <button
            style={styles.modeBtn(mode === 'slider')}
            onClick={() => setMode('slider')}
          >
            Slider
          </button>
          <button
            style={styles.modeBtn(mode === 'sideBySide')}
            onClick={() => setMode('sideBySide')}
          >
            Side by Side
          </button>
        </div>
      </div>

      {mode === 'slider' ? (
        <div
          ref={containerRef}
          style={styles.sliderContainer}
          onMouseDown={handleMouseDown}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
        >
          {sourceImage && <img src={sourceImage} alt="Source" style={styles.imageBase} />}
          {warpedImage && <img src={warpedImage} alt="Warped" style={styles.imageOverlay(sliderPos)} />}

          <div style={styles.sliderLine(sliderPos)} />
          <div style={styles.sliderHandle(sliderPos)}>⇔</div>

          <div style={styles.label('left')}>Source</div>
          <div style={styles.label('right')}>Warped</div>
        </div>
      ) : (
        <div style={styles.sideBySide}>
          <div style={styles.sidePanel}>
            {sourceImage && <img src={sourceImage} alt="Source" style={styles.sideImage} />}
            <div style={styles.sideLabel}>Source</div>
          </div>
          <div style={styles.sidePanel}>
            {warpedImage && <img src={warpedImage} alt="Warped" style={styles.sideImage} />}
            <div style={styles.sideLabel}>Warped</div>
          </div>
        </div>
      )}
    </div>
  );
}
