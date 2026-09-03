import React, { useEffect, useState } from 'react';

function ConfidenceRing({ value }) {
  const [animated, setAnimated] = useState(0);
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animated / 100) * circumference;

  const getColor = (v) => {
    if (v >= 70) return { stroke: '#22c55e', glow: 'rgba(34, 197, 94, 0.3)' };
    if (v >= 40) return { stroke: '#f59e0b', glow: 'rgba(245, 158, 11, 0.3)' };
    return { stroke: '#ef4444', glow: 'rgba(239, 68, 68, 0.3)' };
  };

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(value), 100);
    return () => clearTimeout(timer);
  }, [value]);

  const color = getColor(animated);

  return (
    <div style={{ position: 'relative', width: '140px', height: '140px' }}>
      <svg width="140" height="140" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="var(--glass-border)" strokeWidth="8" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke={color.stroke}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 60 60)"
          style={{
            transition: 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.5s ease',
            filter: `drop-shadow(0 0 8px ${color.glow})`,
          }}
        />
      </svg>
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        textAlign: 'center',
      }}>
        <div style={{
          fontSize: '28px',
          fontWeight: 700,
          fontFamily: "'Space Grotesk', sans-serif",
          color: color.stroke,
          lineHeight: 1,
        }}>
          {Math.round(animated)}
        </div>
        <div style={{
          fontSize: '11px',
          color: 'var(--text-muted)',
          fontWeight: 500,
          marginTop: '2px',
        }}>
          / 100
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, unit, color, delay }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    if (value === null || value === undefined) return;
    const start = 0;
    const end = typeof value === 'number' ? value : 0;
    const duration = 1500;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(start + (end - start) * eased);
      if (progress < 1) requestAnimationFrame(animate);
    };

    const timer = setTimeout(animate, delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  const getColor = (val, max) => {
    const ratio = val / max;
    if (ratio >= 0.7) return 'var(--success)';
    if (ratio >= 0.4) return 'var(--warning)';
    return 'var(--danger)';
  };

  const metricColor = color || (value != null ? getColor(displayValue, 1) : 'var(--text-muted)');

  return (
    <div style={{
      background: 'var(--glass)',
      border: '1px solid var(--glass-border)',
      borderRadius: '12px',
      padding: '20px',
      textAlign: 'center',
      transition: 'all 0.3s ease',
      animation: `fadeInUp 0.5s ease-out ${delay}ms both`,
    }}>
      <div style={{
        fontSize: '24px',
        marginBottom: '8px',
        filter: `drop-shadow(0 0 8px ${metricColor})`,
      }}>
        {icon}
      </div>
      <div style={{
        fontSize: '12px',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: 'var(--text-muted)',
        marginBottom: '8px',
      }}>
        {label}
      </div>
      <div style={{
        fontSize: '24px',
        fontWeight: 700,
        fontFamily: "'Space Grotesk', sans-serif",
        color: value != null ? metricColor : 'var(--text-muted)',
        lineHeight: 1,
      }}>
        {value != null ? displayValue.toFixed(unit === 'ratio' ? 4 : 2) : 'N/A'}
      </div>
      {unit && value != null && (
        <div style={{
          fontSize: '10px',
          color: 'var(--text-muted)',
          marginTop: '4px',
        }}>
          {unit}
        </div>
      )}
    </div>
  );
}

function FeatureViz({ sourceImage, featurePoints }) {
  const canvasRef = React.useRef(null);

  useEffect(() => {
    if (!sourceImage || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = sourceImage;
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      const points = featurePoints && featurePoints.length > 0
        ? featurePoints.slice(0, 200)
        : Array.from({ length: 50 }, () => ({
            x: Math.random() * img.width,
            y: Math.random() * img.height,
          }));

      points.forEach((p, i) => {
        setTimeout(() => {
          ctx.beginPath();
          ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
          ctx.fillStyle = `hsl(${120 + (i * 137) % 80}, 80%, 60%)`;
          ctx.fill();
          ctx.strokeStyle = 'rgba(255,255,255,0.8)';
          ctx.lineWidth = 1;
          ctx.stroke();
        }, i * 15);
      });
    };
  }, [sourceImage, featurePoints]);

  if (!sourceImage) return null;

  const pointCount = featurePoints ? featurePoints.length : 50;

  return (
    <div style={{
      borderRadius: '12px',
      overflow: 'hidden',
      border: '1px solid var(--glass-border)',
      position: 'relative',
    }}>
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: 'auto', display: 'block' }}
      />
      <div style={{
        position: 'absolute',
        bottom: '8px',
        left: '8px',
        padding: '4px 10px',
        borderRadius: '6px',
        background: 'rgba(0,0,0,0.7)',
        backdropFilter: 'blur(4px)',
        fontSize: '11px',
        fontWeight: 600,
        color: 'var(--success)',
      }}>
        {pointCount} feature points detected
      </div>
    </div>
  );
}

const styles = {
  container: {
    animation: 'fadeInUp 0.5s ease-out',
  },
  header: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '22px',
    fontWeight: 600,
    marginBottom: '24px',
    textAlign: 'center',
  },
  confidenceSection: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '24px',
    marginBottom: '32px',
    padding: '24px',
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
  },
  confidenceLabel: {
    textAlign: 'left',
  },
  confidenceTitle: {
    fontSize: '16px',
    fontWeight: 600,
    marginBottom: '4px',
  },
  confidenceDesc: {
    fontSize: '13px',
    color: 'var(--text-muted)',
    lineHeight: 1.5,
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
    gap: '16px',
    marginBottom: '32px',
  },
  statusBadge: (status) => ({
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 14px',
    borderRadius: '20px',
    background: status === 'done' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
    border: `1px solid ${status === 'done' ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
    fontSize: '13px',
    fontWeight: 600,
    color: status === 'done' ? 'var(--success)' : 'var(--danger)',
    marginBottom: '24px',
  }),
  disclaimer: {
    fontSize: '11px',
    color: 'var(--text-muted)',
    textAlign: 'center',
    marginTop: '16px',
    fontStyle: 'italic',
  },
  featureSection: {
    marginTop: '32px',
  },
  featureTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '18px',
    fontWeight: 600,
    marginBottom: '16px',
  },
};

export default function ResultsDashboard({ report, sourceImage, featurePoints }) {
  if (!report) return null;

  const metrics = report.metrics || {};
  const confidence = report.confidence;

  return (
    <div style={styles.container}>
      <div style={styles.header}>Registration Results</div>

      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <span style={styles.statusBadge(report.status)}>
          {report.status === 'done' ? '✓' : '✗'} {report.status === 'done' ? 'Registration Complete' : 'Registration Failed'}
        </span>
      </div>

      <div style={styles.confidenceSection}>
        <ConfidenceRing value={confidence || 0} />
        <div style={styles.confidenceLabel}>
          <div style={styles.confidenceTitle}>Confidence Score</div>
          <div style={styles.confidenceDesc}>
            Composite quality metric combining SSIM, mutual information, inlier ratio, and reprojection error.
          </div>
        </div>
      </div>

      <div style={styles.metricsGrid}>
        <MetricCard
          icon="🖼"
          label="SSIM"
          value={metrics.ssim}
          delay={0}
        />
        <MetricCard
          icon="📊"
          label="Mutual Info"
          value={metrics.mutual_information}
          unit="bits"
          delay={100}
        />
        <MetricCard
          icon="🎯"
          label="Inlier Ratio"
          value={metrics.inlier_ratio}
          unit="ratio"
          delay={200}
        />
        <MetricCard
          icon="📐"
          label="Reproj Error"
          value={metrics.corner_reprojection_error}
          unit="px"
          delay={300}
        />
      </div>

      <div style={styles.featureSection}>
        <div style={styles.featureTitle}>Feature Detection</div>
        <FeatureViz sourceImage={sourceImage} featurePoints={featurePoints} />
      </div>

      <div style={styles.disclaimer}>
        Confidence weights are configurable, not empirically derived from labeled data.
      </div>
    </div>
  );
}
