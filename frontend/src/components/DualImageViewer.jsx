import React from 'react';

export default function DualImageViewer({ sourceImage, referenceImage }) {
  return (
    <div style={{ display: 'flex', gap: '10px' }}>
      <div>
        <h4>Source</h4>
        {sourceImage ? (
          <img src={sourceImage} alt="Source" style={{ maxWidth: '400px' }} />
        ) : (
          <div style={{ width: '400px', height: '300px', border: '1px dashed #ccc', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            No source image
          </div>
        )}
      </div>
      <div>
        <h4>Reference</h4>
        {referenceImage ? (
          <img src={referenceImage} alt="Reference" style={{ maxWidth: '400px' }} />
        ) : (
          <div style={{ width: '400px', height: '300px', border: '1px dashed #ccc', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            No reference image
          </div>
        )}
      </div>
    </div>
  );
}
