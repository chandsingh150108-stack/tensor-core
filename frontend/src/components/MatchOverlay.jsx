import React from 'react';

export default function MatchOverlay({ matches }) {
  if (!matches || matches.length === 0) return null;

  return (
    <div style={{ marginTop: '10px' }}>
      <h4>Feature Matches</h4>
      <p>{matches.length} correspondences detected</p>
    </div>
  );
}
