import React, { useState } from 'react';
import { getOverlayUrl } from '../api/client';

export default function BlendSlider({ jobId }) {
  const [alpha, setAlpha] = useState(0.5);
  const overlayUrl = jobId ? getOverlayUrl(jobId) : null;

  return (
    <div style={{ margin: '20px 0' }}>
      <h4>Overlay Blend</h4>
      <input
        type="range"
        min="0"
        max="100"
        value={alpha * 100}
        onChange={(e) => setAlpha(e.target.value / 100)}
        style={{ width: '300px' }}
      />
      <span> {Math.round(alpha * 100)}%</span>
      {overlayUrl && (
        <div style={{ marginTop: '10px' }}>
          <img
            src={overlayUrl}
            alt="Overlay"
            style={{ maxWidth: '500px', opacity: alpha }}
          />
        </div>
      )}
    </div>
  );
}
