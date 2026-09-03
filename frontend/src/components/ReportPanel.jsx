import React from 'react';

export default function ReportPanel({ report }) {
  if (!report) return null;

  const metrics = report.metrics || {};
  const confidence = report.confidence;

  return (
    <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3>Registration Report</h3>
      <p><strong>Status:</strong> {report.status}</p>

      <h4>Metrics</h4>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <tbody>
          <tr>
            <td style={{ padding: '5px 10px', border: '1px solid #ddd' }}>SSIM</td>
            <td style={{ padding: '5px 10px', border: '1px solid #ddd' }}>
              {metrics.ssim != null ? metrics.ssim.toFixed(4) : 'N/A'}
            </td>
          </tr>
          <tr>
            <td style={{ padding: '5px 10px', border: '1px solid #ddd' }}>Mutual Information</td>
            <td style={{ padding: '5px 10px', border: '1px solid #ddd' }}>
              {metrics.mutual_information != null ? metrics.mutual_information.toFixed(4) : 'N/A'}
            </td>
          </tr>
          <tr>
            <td style={{ padding: '5px 10px', border: '1px solid #ddd' }}>Inlier Ratio</td>
            <td style={{ padding: '5px 10px', border: '1px solid #ddd' }}>
              {metrics.inlier_ratio != null ? metrics.inlier_ratio.toFixed(4) : 'N/A'}
            </td>
          </tr>
          <tr>
            <td style={{ padding: '5px 10px', border: '1px solid #ddd' }}>Corner Reprojection Error</td>
            <td style={{ padding: '5px 10px', border: '1px solid #ddd' }}>
              {metrics.corner_reprojection_error != null ? metrics.corner_reprojection_error.toFixed(4) : 'N/A (no ground truth)'}
            </td>
          </tr>
        </tbody>
      </table>

      {confidence != null && (
        <div style={{ marginTop: '15px' }}>
          <h4>Composite Confidence Score</h4>
          <div style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: confidence > 70 ? 'green' : confidence > 40 ? 'orange' : 'red'
          }}>
            {confidence.toFixed(1)} / 100
          </div>
          <p style={{ fontSize: '12px', color: '#666' }}>
            Note: Confidence weights are configurable, not empirically derived from labeled data.
          </p>
        </div>
      )}
    </div>
  );
}
