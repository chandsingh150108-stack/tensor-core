import React, { useState } from 'react';
import DualImageViewer from './components/DualImageViewer';
import ReportPanel from './components/ReportPanel';
import BlendSlider from './components/BlendSlider';
import { uploadImage, startRegistration, pollRegistration, getReport } from './api/client';

function App() {
  const [sourceImage, setSourceImage] = useState(null);
  const [referenceImage, setReferenceImage] = useState(null);
  const [sourceId, setSourceId] = useState(null);
  const [referenceId, setReferenceId] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async (file, type) => {
    try {
      setError(null);
      const result = await uploadImage(file);
      const url = URL.createObjectURL(file);
      if (type === 'source') {
        setSourceImage(url);
        setSourceId(result.image_id);
      } else {
        setReferenceImage(url);
        setReferenceId(result.image_id);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRegister = async () => {
    if (!sourceId || !referenceId) {
      setError('Please upload both images first');
      return;
    }
    try {
      setError(null);
      setStatus('submitting');
      const result = await startRegistration(sourceId, referenceId);
      setJobId(result.job_id);
      setStatus('polling');
      pollUntilDone(result.job_id);
    } catch (err) {
      setError(err.message);
      setStatus('idle');
    }
  };

  const pollUntilDone = async (jid) => {
    let attempts = 0;
    const maxAttempts = 60;
    while (attempts < maxAttempts) {
      try {
        const result = await pollRegistration(jid);
        if (result.status === 'done' || result.status === 'failed') {
          setStatus(result.status);
          const reportResult = await getReport(jid);
          setReport(reportResult);
          return;
        }
        await new Promise(r => setTimeout(r, 2000));
        attempts++;
      } catch (err) {
        await new Promise(r => setTimeout(r, 2000));
        attempts++;
      }
    }
    setStatus('timeout');
    setError('Registration timed out');
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Lunar Image Registration</h1>
      {error && <div style={{ color: 'red', margin: '10px 0' }}>{error}</div>}

      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        <div>
          <h3>Source Image</h3>
          <input
            type="file"
            accept=".tif,.tiff,.img,.xml,.lbl"
            onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0], 'source')}
          />
          {sourceImage && <img src={sourceImage} alt="Source" style={{ maxWidth: '300px', marginTop: '10px' }} />}
        </div>
        <div>
          <h3>Reference Image</h3>
          <input
            type="file"
            accept=".tif,.tiff,.img,.xml,.lbl"
            onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0], 'reference')}
          />
          {referenceImage && <img src={referenceImage} alt="Reference" style={{ maxWidth: '300px', marginTop: '10px' }} />}
        </div>
      </div>

      <button
        onClick={handleRegister}
        disabled={!sourceId || !referenceId || status === 'polling'}
        style={{ padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}
      >
        {status === 'polling' ? 'Registering...' : 'Start Registration'}
      </button>

      {status === 'polling' && <p>Processing registration...</p>}

      {report && (
        <div style={{ marginTop: '20px' }}>
          <h2>Results</h2>
          <BlendSlider jobId={jobId} />
          <ReportPanel report={report} />
        </div>
      )}
    </div>
  );
}

export default App;
