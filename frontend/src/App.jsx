import React, { useState, useCallback } from 'react';
import './App.css';
import Particles from './components/Particles';
import HeroSection from './components/HeroSection';
import StepIndicator from './components/StepIndicator';
import ImageUploader from './components/ImageUploader';
import ProcessingView from './components/ProcessingView';
import ImageComparison from './components/ImageComparison';
import ResultsDashboard from './components/ResultsDashboard';
import { uploadImage, startRegistration, pollRegistration, getReport } from './api/client';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function getStepFromStatus(status) {
  if (status === 'idle') return 1;
  if (status === 'submitting' || status === 'polling') return 2;
  if (status === 'done' || status === 'failed' || status === 'timeout') return 3;
  return 1;
}

function App() {
  const [sourceImage, setSourceImage] = useState(null);
  const [referenceImage, setReferenceImage] = useState(null);
  const [sourceId, setSourceId] = useState(null);
  const [referenceId, setReferenceId] = useState(null);
  const [sourceMetadata, setSourceMetadata] = useState(null);
  const [referenceMetadata, setReferenceMetadata] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [warpedImage, setWarpedImage] = useState(null);

  const currentStep = getStepFromStatus(status);

  const handleUpload = useCallback(async (file, type) => {
    try {
      setError(null);
      const result = await uploadImage(file);
      const url = URL.createObjectURL(file);
      if (type === 'source') {
        setSourceImage(url);
        setSourceId(result.image_id);
        setSourceMetadata(result.metadata);
      } else {
        setReferenceImage(url);
        setReferenceId(result.image_id);
        setReferenceMetadata(result.metadata);
      }
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const handleRemove = useCallback((type) => {
    if (type === 'source') {
      setSourceImage(null);
      setSourceId(null);
      setSourceMetadata(null);
    } else {
      setReferenceImage(null);
      setReferenceId(null);
      setReferenceMetadata(null);
    }
  }, []);

  const handleRegister = useCallback(async () => {
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
  }, [sourceId, referenceId]);

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
          if (result.status === 'done') {
            setWarpedImage(`${API_BASE}/report/${jid}/warped-image`);
          }
          return;
        }
        await new Promise((r) => setTimeout(r, 2000));
        attempts++;
      } catch {
        await new Promise((r) => setTimeout(r, 2000));
        attempts++;
      }
    }
    setStatus('timeout');
    setError('Registration timed out');
  };

  const handleReset = () => {
    setSourceImage(null);
    setReferenceImage(null);
    setSourceId(null);
    setReferenceId(null);
    setSourceMetadata(null);
    setReferenceMetadata(null);
    setJobId(null);
    setStatus('idle');
    setReport(null);
    setError(null);
    setWarpedImage(null);
  };

  return (
    <>
      <Particles />
      <div className="app-container">
        <div className="main-content">
          <HeroSection />
          <StepIndicator currentStep={currentStep} />

          {status === 'idle' && (
            <div style={{ animation: 'fadeInUp 0.6s ease-out 0.4s both' }}>
              <ImageUploader
                sourceImage={sourceImage}
                referenceImage={referenceImage}
                sourceMetadata={sourceMetadata}
                referenceMetadata={referenceMetadata}
                onUpload={handleUpload}
                onRemove={handleRemove}
              />

              <div style={{ textAlign: 'center', marginTop: '32px' }}>
                <button
                  className="btn btn-primary"
                  onClick={handleRegister}
                  disabled={!sourceId || !referenceId}
                  style={{ padding: '14px 40px', fontSize: '16px' }}
                >
                  ⚡ Start Registration
                </button>
              </div>
            </div>
          )}

          {(status === 'submitting' || status === 'polling') && (
            <ProcessingView status={status} />
          )}

          {(status === 'done' || status === 'failed' || status === 'timeout') && (
            <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
              <ResultsDashboard
                report={report}
                sourceImage={sourceImage}
                featurePoints={report?.feature_points || []}
              />

              {sourceImage && (
                <div style={{ marginTop: '32px' }}>
                  <ImageComparison
                    sourceImage={sourceImage}
                    warpedImage={warpedImage}
                    jobId={jobId}
                  />
                </div>
              )}

              <div style={{ textAlign: 'center', marginTop: '32px' }}>
                <button className="btn btn-secondary" onClick={handleReset}>
                  ↻ Register Another Pair
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="error-toast" onClick={() => setError(null)}>
              ✗ {error}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default App;
