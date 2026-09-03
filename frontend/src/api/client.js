const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Request failed');
  }
  return response.json();
}

export async function uploadImage(file) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE}/images/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Upload failed');
  }
  return response.json();
}

export async function startRegistration(sourceImageId, referenceImageId, params = {}) {
  return apiRequest('/register', {
    method: 'POST',
    body: JSON.stringify({
      source_image_id: sourceImageId,
      reference_image_id: referenceImageId,
      params,
    }),
  });
}

export async function pollRegistration(jobId) {
  return apiRequest(`/register/${jobId}`);
}

export async function getReport(jobId) {
  return apiRequest(`/report/${jobId}`);
}

export async function getOverlayUrl(jobId) {
  return `${API_BASE}/report/${jobId}/overlay`;
}
