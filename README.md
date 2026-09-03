# Lunar Image Registration Framework

**Multi-Scale Lunar Image Registration for ISRO Chandrayaan-2**

A complete pipeline for automatically aligning satellite and lunar images taken by different sensors, at different resolutions, under different lighting conditions. The system decides between classical computer vision (SIFT) and deep learning (LoFTR) matching based on image-pair difficulty.

## Overview

This framework solves the problem of registering (aligning) pairs of lunar/satellite images that differ in:

- **Resolution** — TMC-2 at 5m/pixel vs OHRC at 0.28m/pixel
- **Lighting** — Different sun angles create different shadow patterns
- **Sensor characteristics** — Different cameras produce different noise profiles and dynamic ranges

### Features

- **Multi-format ingestion** — Reads PDS3, PDS4, and GeoTIFF planetary image formats
- **4-stage preprocessing** — Denoising, photometric correction, shadow normalization, CLAHE
- **Multi-scale pyramid** — Gaussian/Laplacian pyramids for resolution normalization
- **Feature detection** — SIFT, ORB, AKAZE via a pluggable factory pattern
- **Difficulty-aware routing** — Automatically selects classical (fast) or deep learning (robust) matching
- **Retry logic** — Up to 3 attempts with automatic escalation
- **Quality evaluation** — SSIM, mutual information, inlier ratio, composite confidence score
- **REST API** — FastAPI backend with async job processing
- **Web dashboard** — React frontend with overlay blending and metrics display

### Supported Sensors

| Sensor | Mission | Pixel Scale | Archive Format |
|--------|---------|-------------|----------------|
| TMC-2 | ISRO Chandrayaan-2 | ~5.0 m/pixel | PDS4 |
| OHRC | ISRO Chandrayaan-2 | ~0.28 m/pixel | PDS4 |

## Architecture

```
Frontend (React, port 3000)
    │
    ▼
FastAPI Backend (port 8000)
    │
    ▼
┌─────────────────────────────────────────────┐
│  Upload → Preprocess → Route → Match → Eval │
│                                             │
│  Ingestion: PDS3/PDS4/GeoTIFF parsing       │
│  Preprocessing: Denoise → Photometric →     │
│                 Shadow → CLAHE               │
│  Routing: Difficulty score → Classical/Deep  │
│  Matching: SIFT+FLANN or LoFTR+RANSAC       │
│  Evaluation: SSIM, MI, confidence           │
└─────────────────────────────────────────────┘
```

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.10+ | 3.11 |
| Node.js | 18+ | 20+ |
| RAM | 4 GB | 8 GB+ |
| Disk | 2 GB | 5 GB+ (for PyTorch) |
| GPU | None (CPU fallback) | NVIDIA with CUDA 11.7+ |

**System-level dependencies:**
- **GDAL** — Required for GeoTIFF reading via rasterio
- **libgdal-dev** — GDAL development headers (Linux)

## Quick Start — Docker (Easiest)

Docker handles all system dependencies (GDAL, Python, Node) automatically.

```bash
# Clone the repository
git clone <https://github.com/chandsingh150108-stack/tensor-core2.git>
cd crm

# Start all services
docker-compose up --build

# Access the application
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

### GPU Support (Optional)

To enable GPU acceleration for deep matching, edit `docker-compose.yml` and uncomment the GPU section under the `backend` service:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Requires: [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### Stopping Services

```bash
docker-compose down
```

## Manual Local Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd crm
```

### Step 2: Install System Dependencies

#### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y python3-dev libgdal-dev gdal-bin
```

Verify GDAL version (must be 3.6+):

```bash
gdal-config --version
```

#### Fedora / RHEL

```bash
sudo dnf install -y gdal-devel gdal
```

#### Windows

**Option A — pip (simpler):**

```powershell
pip install GDAL==$(gdal-config --version)
```

**Option B — OSGeo4W (more reliable):**

1. Download [OSGeo4W](https://trac.osgeo.org/osgeo4w/)
2. Run the installer, select `gdal` and `python` packages
3. Add OSGeo4W to your PATH

**Note:** On Windows, you may need to install Visual C++ Build Tools for some Python packages.

### Step 3: Set Up Python Backend

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Start the Backend

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The backend is running when you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify with:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

API documentation is available at: `http://localhost:8000/docs` (Swagger UI)

### Step 5: Set Up Frontend (New Terminal)

```bash
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

The frontend is running at: `http://localhost:3000`

### Step 6: Open in Browser

Navigate to `http://localhost:3000` and upload two lunar images to test the registration pipeline.

## API Reference

### Health Check

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

### Upload Image

```bash
curl -X POST http://localhost:8000/images/upload \
  -F "file=@path/to/image.tif"
```

Response:

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "product_id": "CH2_TMC2_20230101",
    "sensor": "TMC2",
    "archive_standard": "GEOTIFF",
    "pixel_scale_m": 5.0,
    "image_shape": [1024, 1024],
    "bit_depth": 16
  }
}
```

### Start Registration

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "source_image_id": "<source-image-id>",
    "reference_image_id": "<reference-image-id>"
  }'
```

Response (HTTP 202 Accepted):

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending"
}
```

### Poll Registration Status

```bash
curl http://localhost:8000/register/<job_id>
```

Response:

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "done",
  "result": { ... }
}
```

Status values: `pending` | `running` | `done` | `failed`

### Get Registration Report

```bash
curl http://localhost:8000/report/<job_id>
```

Response:

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "done",
  "metrics": {
    "ssim": 0.87,
    "mutual_information": 3.42,
    "inlier_ratio": 0.73,
    "corner_reprojection_error": 2.1
  },
  "confidence": 82.5
}
```

### Complete Workflow Example

```bash
# 1. Upload source image
SOURCE_ID=$(curl -s -X POST http://localhost:8000/images/upload \
  -F "file=@source.tif" | python3 -c "import sys,json;print(json.load(sys.stdin)['image_id'])")

# 2. Upload reference image
REF_ID=$(curl -s -X POST http://localhost:8000/images/upload \
  -F "file=@reference.tif" | python3 -c "import sys,json;print(json.load(sys.stdin)['image_id'])")

# 3. Start registration
JOB_ID=$(curl -s -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d "{\"source_image_id\":\"$SOURCE_ID\",\"reference_image_id\":\"$REF_ID\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")

# 4. Poll until done
while true; do
  STATUS=$(curl -s http://localhost:8000/register/$JOB_ID | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])")
  echo "Status: $STATUS"
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then break; fi
  sleep 2
done

# 5. Get report
curl http://localhost:8000/report/$JOB_ID
```

## Testing

### Run All Tests

```bash
# Ensure virtual environment is active
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

pytest
```

### Run Specific Test Files

```bash
pytest tests/test_api.py           # API endpoint tests
pytest tests/test_ingestion.py     # Format reader tests
pytest tests/test_preprocessing.py # Pipeline tests
pytest tests/test_features.py      # Feature detector tests
pytest tests/test_routing.py       # Routing engine tests
pytest tests/test_evaluation.py    # Metrics tests
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=term-missing
```

## Project Structure

```
crm/
├── src/                          # Python backend source
│   ├── api/                      # FastAPI REST service
│   │   ├── main.py               # App, CORS, error handlers
│   │   ├── schemas.py            # Pydantic request/response models
│   │   ├── background.py         # Background job runner
│   │   └── routes/               # Endpoint handlers
│   │       ├── upload.py         # POST /images/upload
│   │       ├── register.py       # POST /register, GET /register/{id}
│   │       └── report.py         # GET /report/{id}
│   ├── common/                   # Shared types and errors
│   │   ├── schema.py             # ImageMetadata dataclass
│   │   └── errors.py             # Custom exceptions
│   ├── ingestion/                # Image loading and format parsing
│   │   ├── loader.py             # Format dispatcher
│   │   ├── pds3_reader.py        # PDS3 PVL format reader
│   │   ├── pds4_reader.py        # PDS4 XML format reader
│   │   └── geotiff_reader.py     # GeoTIFF reader
│   ├── preprocessing/            # 4-stage image cleaning
│   │   ├── pipeline.py           # Pipeline orchestrator
│   │   ├── denoise.py            # NLM/bilateral/median denoising
│   │   ├── photometric.py        # Lunar-Lambert correction
│   │   ├── shadow_normalize.py   # Shadow gamma correction
│   │   └── clahe.py              # Adaptive histogram equalization
│   ├── pyramid/                  # Multi-scale analysis
│   │   ├── builder.py            # Gaussian/Laplacian pyramids
│   │   └── scale_estimator.py    # Scale ratio estimation
│   ├── features/                 # Feature detection
│   │   ├── base.py               # BaseDetector ABC, FeatureResult
│   │   ├── factory.py            # get_detector() factory
│   │   ├── sift_detector.py      # SIFT implementation
│   │   ├── orb_detector.py       # ORB implementation
│   │   └── akaze_detector.py     # AKAZE implementation
│   ├── matching/                 # Correspondence and transforms
│   │   ├── classical_matcher.py  # FLANN/brute-force matching
│   │   ├── transform_estimator.py # RANSAC homography/affine/TPS
│   │   └── warp.py               # Image warping
│   ├── deep_matching/            # Neural network matchers
│   │   ├── device_manager.py     # GPU/CPU selection
│   │   ├── superpoint_wrapper.py # SuperPoint detector
│   │   ├── loftr_wrapper.py      # LoFTR dense matcher
│   │   └── lightglue_wrapper.py  # LightGlue matcher
│   ├── routing/                  # Strategy dispatcher
│   │   ├── difficulty_estimator.py # Difficulty scoring
│   │   ├── router.py             # Classical vs deep dispatch
│   │   └── retry_loop.py         # Retry with escalation
│   └── evaluation/               # Quality metrics
│       ├── metrics.py            # SSIM, MI, inlier ratio
│       ├── confidence.py         # Composite confidence score
│       └── self_consistency.py   # Forward-backward RMSE
├── frontend/                     # React web dashboard
│   ├── src/
│   │   ├── App.jsx               # Root component
│   │   ├── main.jsx              # Entry point
│   │   ├── api/client.js         # API client
│   │   └── components/
│   │       ├── BlendSlider.jsx   # Overlay opacity slider
│   │       └── ReportPanel.jsx   # Metrics display
│   ├── index.html                # HTML shell
│   ├── package.json              # Node dependencies
│   └── vite.config.js            # Vite build config
├── tests/                        # Pytest test suite
│   ├── fixtures/                 # Synthetic test data
│   ├── test_api.py
│   ├── test_ingestion.py
│   ├── test_preprocessing.py
│   ├── test_pyramid.py
│   ├── test_features.py
│   ├── test_classical_matching.py
│   ├── test_deep_matching.py
│   ├── test_routing.py
│   └── test_evaluation.py
├── configs/                      # YAML configuration files
│   ├── ingestion.yaml
│   ├── preprocessing.yaml
│   ├── pyramid.yaml
│   ├── features.yaml
│   ├── matching.yaml
│   ├── routing.yaml
│   ├── evaluation.yaml
│   └── deep_matching.yaml
├── docker/                       # Dockerfiles
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── docker-compose.yml            # Docker Compose orchestration
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project metadata
├── .gitignore
└── README.md
```

## Configuration

All configuration files are in the `configs/` directory. Each module reads its own YAML file with safe fallback defaults.

| File | Controls | Key Settings |
|------|----------|-------------|
| `ingestion.yaml` | Sensor defaults, pixel scale validation | TMC2: 5.0m, OHRC: 0.28m |
| `preprocessing.yaml` | 4-stage pipeline toggles and parameters | All stages enabled by default |
| `pyramid.yaml` | Pyramid construction parameters | max_levels: 6, min_image_dim: 16 |
| `features.yaml` | Detector presets (fast/thorough) | Default: SIFT fast (500 features) |
| `matching.yaml` | Matcher and transform settings | FLANN, ratio 0.75, RANSAC threshold 3.0 |
| `routing.yaml` | Difficulty weights and thresholds | threshold: 0.5, min_inlier_ratio: 0.3 |
| `evaluation.yaml` | Confidence score weights | SSIM: 0.3, MI: 0.2, inlier: 0.3, reproj: 0.2 |
| `deep_matching.yaml` | Neural model settings | LoFTR outdoor, confidence threshold 0.5 |

### Changing the Default Detector

Edit `configs/features.yaml`:

```yaml
default_detector: sift  # Change to: sift, orb, or akaze
default_preset: fast    # Change to: fast or thorough
```

### Adjusting Difficulty Threshold

Edit `configs/routing.yaml`:

```yaml
difficulty_threshold: 0.5  # Lower = more classical, Higher = more deep learning
```

## Troubleshooting

### GDAL Installation Issues

**Error:** `gdal-config: not found`

```bash
# Ubuntu/Debian
sudo apt install libgdal-dev gdal-bin

# Verify version (must be 3.6+)
gdal-config --version
```

**Error:** `pip install GDAL` fails

```bash
# Install exact version matching your system GDAL
pip install GDAL==$(gdal-config --version)
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Use a different port
uvicorn src.api.main:app --port 8001
```

### CUDA / GPU Issues

**Error:** `CUDA out of memory`

The system automatically falls back to CPU. For large images, processing will be slower but functional.

**Error:** `No CUDA GPUs are available`

Ensure NVIDIA drivers and CUDA toolkit are installed. The system falls back to CPU automatically.

### ModuleNotFoundError

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Proxy Errors

Ensure the backend is running on port 8000 before starting the frontend dev server. The Vite proxy configuration in `vite.config.js` forwards `/images`, `/register`, `/report`, and `/health` to `http://localhost:8000`.

### Large File Upload Failures

For very large images, you may need to increase uvicorn's limits:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 300
```

### Missing Test Fixtures

If tests fail due to missing fixture files, regenerate them:

```bash
python tests/generate_fixtures.py
```

## License

[Add your license here]
