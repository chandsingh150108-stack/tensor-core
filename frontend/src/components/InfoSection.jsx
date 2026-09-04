import React, { useState } from 'react';

const styles = {
  container: {
    marginBottom: '60px',
  },
  problemBanner: {
    background: 'linear-gradient(135deg, rgba(18, 19, 88, 0.1) 0%, rgba(18, 19, 88, 0.1) 100%)',
    border: '1px solid var(--glass-border)',
    borderRadius: '20px',
    padding: '48px 40px',
    marginBottom: '48px',
    position: 'relative',
    overflow: 'hidden',
  },
  topLine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '2px',
    background: 'linear-gradient(90deg, var(--accent), var(--purple), var(--cyan))',
  },
  problemTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '28px',
    fontWeight: 700,
    textAlign: 'center',
    marginBottom: '12px',
    letterSpacing: '-0.02em',
  },
  problemSubtitle: {
    fontSize: '16px',
    color: 'var(--text-secondary)',
    textAlign: 'center',
    maxWidth: '600px',
    margin: '0 auto 32px',
    lineHeight: 1.7,
  },
  challengeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
  },
  challengeCard: {
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
    borderRadius: '12px',
    padding: '24px',
    textAlign: 'center',
    transition: 'all 0.3s ease',
    cursor: 'default',
  },
  challengeIcon: {
    width: '48px',
    height: '48px',
    margin: '0 auto 16px',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    fontWeight: 700,
  },
  challengeName: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '16px',
    fontWeight: 600,
    marginBottom: '8px',
  },
  challengeDesc: {
    fontSize: '13px',
    color: 'var(--text-muted)',
    lineHeight: 1.5,
  },
  sectionTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '24px',
    fontWeight: 700,
    textAlign: 'center',
    marginBottom: '8px',
  },
  sectionSubtitle: {
    fontSize: '15px',
    color: 'var(--text-secondary)',
    textAlign: 'center',
    marginBottom: '32px',
  },
  pipelineContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    flexWrap: 'wrap',
    marginBottom: '48px',
  },
  pipelineStep: {
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px 20px',
    textAlign: 'center',
    minWidth: '140px',
    transition: 'all 0.3s ease',
  },
  pipelineStepNumber: {
    width: '32px',
    height: '32px',
    margin: '0 auto 12px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, var(--accent), var(--purple))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    fontWeight: 700,
    color: 'white',
  },
  pipelineStepTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '14px',
    fontWeight: 600,
    marginBottom: '6px',
  },
  pipelineStepDesc: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    lineHeight: 1.4,
  },
  pipelineArrow: {
    fontSize: '20px',
    color: 'var(--accent)',
    fontWeight: 700,
  },
  sourcesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '24px',
    marginBottom: '24px',
  },
  sourceCard: {
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '32px',
    transition: 'all 0.3s ease',
    position: 'relative',
    overflow: 'hidden',
  },
  sourceTopLine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '3px',
    background: 'linear-gradient(90deg, var(--accent), var(--purple))',
  },
  sourceTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '18px',
    fontWeight: 700,
    marginBottom: '8px',
  },
  sourceSubtitle: {
    fontSize: '13px',
    color: 'var(--text-muted)',
    marginBottom: '16px',
  },
  sourceList: {
    listStyle: 'none',
    padding: 0,
    margin: '0 0 20px 0',
  },
  sourceListItem: {
    fontSize: '14px',
    color: 'var(--text-secondary)',
    padding: '6px 0',
    borderBottom: '1px solid var(--glass-border)',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  sourceDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  sourceLink: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '10px 20px',
    borderRadius: '8px',
    background: 'linear-gradient(135deg, var(--accent), var(--purple))',
    color: 'white',
    fontSize: '14px',
    fontWeight: 600,
    textDecoration: 'none',
    transition: 'all 0.3s ease',
  },
  instructionsBox: {
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
    borderRadius: '12px',
    padding: '24px',
  },
  instructionsTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '16px',
    fontWeight: 600,
    marginBottom: '16px',
  },
  instructionsList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    counterReset: 'step',
  },
  instructionItem: {
    fontSize: '14px',
    color: 'var(--text-secondary)',
    padding: '8px 0',
    paddingLeft: '32px',
    position: 'relative',
    counterIncrement: 'step',
  },
  instructionNumber: {
    position: 'absolute',
    left: 0,
    width: '22px',
    height: '22px',
    borderRadius: '50%',
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '11px',
    fontWeight: 600,
    color: 'var(--accent)',
  },
  featuresGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px',
    marginBottom: '48px',
  },
  featureCard: {
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
    textAlign: 'center',
    transition: 'all 0.3s ease',
    position: 'relative',
    overflow: 'hidden',
    cursor: 'default',
  },
  featureIcon: {
    width: '48px',
    height: '48px',
    margin: '0 auto 16px',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, rgba(18, 19, 88, 0.2), rgba(18, 19, 88, 0.2))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    fontWeight: 700,
    color: 'var(--accent)',
  },
  featureTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '15px',
    fontWeight: 600,
    marginBottom: '8px',
  },
  featureDesc: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    lineHeight: 1.5,
  },
  quickStartContainer: {
    background: 'linear-gradient(135deg, rgba(182, 187, 196, 0.1) 0%, rgba(18, 19, 88, 0.1) 100%)',
    border: '1px solid var(--glass-border)',
    borderRadius: '20px',
    padding: '48px 40px',
  },
  stepsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '24px',
  },
  stepCard: {
    background: 'var(--glass)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '32px 24px',
    textAlign: 'center',
  },
  stepNumber: {
    width: '40px',
    height: '40px',
    margin: '0 auto 16px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, var(--accent), var(--purple))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '18px',
    fontWeight: 700,
    color: 'white',
  },
  stepTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '16px',
    fontWeight: 600,
    marginBottom: '8px',
  },
  stepDesc: {
    fontSize: '13px',
    color: 'var(--text-muted)',
    lineHeight: 1.5,
  },
};

const challenges = [
  {
    name: 'Illumination Variation',
    desc: 'Different sun angles create shadows and brightness changes across lunar surface',
    color: 'var(--accent)',
    abbr: 'IV',
  },
  {
    name: 'Scale Variation',
    desc: 'TMC (5m/px) vs OHRC (28cm/px) creates 17x resolution difference',
    color: 'var(--purple)',
    abbr: 'SV',
  },
  {
    name: 'Viewpoint Variation',
    desc: 'Different camera positions cause geometric distortions and perspective changes',
    color: 'var(--cyan)',
    abbr: 'VV',
  },
  {
    name: 'Multi-Modal',
    desc: 'Different sensors capture different spectral bands and characteristics',
    color: 'var(--success)',
    abbr: 'MM',
  },
];

const pipelineSteps = [
  { title: 'Upload', desc: 'Drag & drop two lunar images' },
  { title: 'Detect', desc: 'SIFT/LoFTR feature extraction' },
  { title: 'Match', desc: 'Homography transform estimation' },
  { title: 'Result', desc: 'Confidence score & metrics' },
];

const features = [
  {
    title: 'Scale Invariant',
    desc: 'Handles 17x resolution difference between TMC and OHRC sensors',
    icon: '17x',
  },
  {
    title: 'Sun Angle Invariant',
    desc: 'Photometric correction normalizes lighting differences',
    icon: 'LA',
  },
  {
    title: 'AI Routing',
    desc: 'Automatically selects SIFT or LoFTR based on image difficulty',
    icon: 'AI',
  },
  {
    title: 'Real-time Metrics',
    desc: 'SSIM, mutual information, inlier ratio, confidence score',
    icon: 'M',
  },
  {
    title: 'Retry Loop',
    desc: 'Up to 3 attempts with different parameters for robustness',
    icon: 'R',
  },
  {
    title: 'Memory Mapped',
    desc: 'Handles 1GB+ Chandrayaan-2 images without memory issues',
    icon: 'GB',
  },
];

export default function InfoSection() {
  const [hoveredFeature, setHoveredFeature] = useState(null);
  const [hoveredChallenge, setHoveredChallenge] = useState(null);

  return (
    <div style={styles.container}>
      {/* Problem Statement Banner */}
      <div style={styles.problemBanner}>
        <div style={styles.topLine} />
        <h2 style={styles.problemTitle}>
          Chandrayaan-2 Image Registration Challenge
        </h2>
        <p style={styles.problemSubtitle}>
          Aligning lunar images across different sensors, resolutions, and lighting conditions
          is critical for scientific analysis and mission planning.
        </p>
        <div style={styles.challengeGrid}>
          {challenges.map((c, i) => (
            <div
              key={i}
              style={{
                ...styles.challengeCard,
                ...(hoveredChallenge === i ? { transform: 'translateY(-4px)', boxShadow: `0 8px 32px ${c.color}33` } : {}),
              }}
              onMouseEnter={() => setHoveredChallenge(i)}
              onMouseLeave={() => setHoveredChallenge(null)}
            >
              <div style={{ ...styles.challengeIcon, background: `${c.color}22`, color: c.color }}>
                {c.abbr}
              </div>
              <div style={styles.challengeName}>{c.name}</div>
              <div style={styles.challengeDesc}>{c.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* How It Works */}
      <h2 style={styles.sectionTitle}>How It Works</h2>
      <p style={styles.sectionSubtitle}>
        Four-step pipeline from image upload to registration results
      </p>
      <div style={styles.pipelineContainer}>
        {pipelineSteps.map((step, i) => (
          <React.Fragment key={i}>
            <div style={styles.pipelineStep}>
              <div style={styles.pipelineStepNumber}>{i + 1}</div>
              <div style={styles.pipelineStepTitle}>{step.title}</div>
              <div style={styles.pipelineStepDesc}>{step.desc}</div>
            </div>
            {i < pipelineSteps.length - 1 && (
              <div style={styles.pipelineArrow}>{'>'}</div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Data Sources */}
      <h2 style={styles.sectionTitle}>Where to Find Images</h2>
      <p style={styles.sectionSubtitle}>
        Download real Chandrayaan-2 data from ISRO's ISSDC portal
      </p>
      <div style={styles.sourcesGrid}>
        <div style={styles.sourceCard}>
          <div style={styles.sourceTopLine} />
          <div style={styles.sourceTitle}>Chandrayaan-2 ISSDC Portal</div>
          <div style={styles.sourceSubtitle}>Primary data source for TMC, OHRC, IIRS images</div>
          <ul style={styles.sourceList}>
            <li style={styles.sourceListItem}>
              <div style={{ ...styles.sourceDot, background: 'var(--accent)' }} />
              TMC-2: 5m/px resolution, 20km swath
            </li>
            <li style={styles.sourceListItem}>
              <div style={{ ...styles.sourceDot, background: 'var(--purple)' }} />
              OHRC: 28cm/px resolution, 3km swath
            </li>
            <li style={styles.sourceListItem}>
              <div style={{ ...styles.sourceDot, background: 'var(--cyan)' }} />
              IIRS: 80m/px resolution, spectral imaging
            </li>
          </ul>
          <a
            href="https://chmapbrowse.issdc.gov.in/"
            target="_blank"
            rel="noopener noreferrer"
            style={styles.sourceLink}
          >
            Open ISSDC Portal
          </a>
        </div>
        <div style={styles.sourceCard}>
          <div style={styles.sourceTopLine} />
          <div style={styles.sourceTitle}>LRO NAC Reference Images</div>
          <div style={styles.sourceSubtitle}>High-resolution lunar surface imagery</div>
          <ul style={styles.sourceList}>
            <li style={styles.sourceListItem}>
              <div style={{ ...styles.sourceDot, background: 'var(--accent)' }} />
              Narrow Angle Camera (NAC) images
            </li>
            <li style={styles.sourceListItem}>
              <div style={{ ...styles.sourceDot, background: 'var(--purple)' }} />
              Global coverage at 0.5m/px
            </li>
            <li style={styles.sourceListItem}>
              <div style={{ ...styles.sourceDot, background: 'var(--cyan)' }} />
              Useful for cross-mission validation
            </li>
          </ul>
          <a
            href="https://lroc.sese.asu.edu/data/"
            target="_blank"
            rel="noopener noreferrer"
            style={styles.sourceLink}
          >
            Open LROC Data
          </a>
        </div>
      </div>
      <div style={styles.instructionsBox}>
        <div style={styles.instructionsTitle}>Download Instructions</div>
        <ol style={styles.instructionsList}>
          {[
            'Register at the ISSDC portal and login',
            'Select instrument (TMC-2 or OHRC)',
            'Choose PDS Product Type: Calibrated',
            'Set Area of Interest (max 5\u00b0 x 5\u00b0 search area)',
            'Download PDS4 products (XML label + IMG binary)',
            'Keep XML and IMG files in the same directory',
          ].map((text, i) => (
            <li key={i} style={styles.instructionItem}>
              <div style={styles.instructionNumber}>{i + 1}</div>
              {text}
            </li>
          ))}
        </ol>
      </div>

      {/* Key Features */}
      <h2 style={{ ...styles.sectionTitle, marginTop: '48px' }}>Key Features</h2>
      <p style={styles.sectionSubtitle}>
        Technical capabilities powering robust lunar image registration
      </p>
      <div style={styles.featuresGrid}>
        {features.map((f, i) => (
          <div
            key={i}
            style={{
              ...styles.featureCard,
              ...(hoveredFeature === i ? { transform: 'translateY(-4px)', boxShadow: '0 8px 32px rgba(18, 19, 88, 0.2)' } : {}),
            }}
            onMouseEnter={() => setHoveredFeature(i)}
            onMouseLeave={() => setHoveredFeature(null)}
          >
            <div style={styles.featureIcon}>{f.icon}</div>
            <div style={styles.featureTitle}>{f.title}</div>
            <div style={styles.featureDesc}>{f.desc}</div>
          </div>
        ))}
      </div>

      {/* Quick Start */}
      <div style={styles.quickStartContainer}>
        <h2 style={styles.sectionTitle}>Quick Start</h2>
        <p style={styles.sectionSubtitle}>
          Get started in three simple steps
        </p>
        <div style={styles.stepsGrid}>
          <div style={styles.stepCard}>
            <div style={styles.stepNumber}>1</div>
            <div style={styles.stepTitle}>Download Images</div>
            <div style={styles.stepDesc}>
              Use demo images or download from ISSDC portal
            </div>
          </div>
          <div style={styles.stepCard}>
            <div style={styles.stepNumber}>2</div>
            <div style={styles.stepTitle}>Upload & Register</div>
            <div style={styles.stepDesc}>
              Drag & drop two images, click Start Registration
            </div>
          </div>
          <div style={styles.stepCard}>
            <div style={styles.stepNumber}>3</div>
            <div style={styles.stepTitle}>View Results</div>
            <div style={styles.stepDesc}>
              Confidence score, metrics, and image comparison
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
