# Lunar Image Registration Framework — About

## 1. Project Overview

**Name:** `lunar-registration` (v0.1.0)  
**Title:** Multi-Scale Lunar Image Registration Framework  
**Domain:** ISRO Chandrayaan-2 (TMC-2/OHRC) & NASA LRO-NAC planetary imagery  
**Purpose:** Automatically align (register) pairs of satellite/lunar images taken by different sensors at different resolutions, lighting conditions, and viewing angles

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Computer Vision | OpenCV, scikit-image |
| Deep Learning | PyTorch, Kornia (SuperPoint, LoFTR, LightGlue) |
| Geospatial | GDAL, rasterio, pds4-tools, pvl |
| API | FastAPI, uvicorn, Pydantic |
| Frontend | React 18, Vite 5 |
| Infrastructure | Docker Compose, Nginx |

### Build Plan Reference

This project was built across 10 sessions as documented in `Agentfeed.md`:
1. Data Ingestion & Metadata Parsing
2. Photometric Correction & Illumination Normalization
3. Multi-Scale Image Pyramid & Resolution Normalizer
4. Classical Feature Detection
5. Classical Feature Matching & Transform Estimation
6. Deep Feature Matching Fallback
7. Difficulty-Aware Routing Engine
8. Quantitative Evaluation Suite
9. FastAPI Backend Service
10. Frontend Dashboard & Docker

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (React + Vite)                     │
│            http://localhost:3000                              │
│  ┌──────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │
│  │  Upload   │ │BlendSlider │ │ReportPanel │ │DualViewer  │ │
│  │  Images   │ │ (overlay)  │ │ (metrics)  │ │(unused)    │ │
│  └──────────┘ └────────────┘ └────────────┘ └────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP (proxied)
┌───────────────────────▼─────────────────────────────────────┐
│                FastAPI Backend (port 8000)                   │
│  POST /images/upload  →  image_id + metadata                │
│  POST /register       →  job_id (202 Accepted)              │
│  GET  /register/{id}  →  status (pending/running/done)      │
│  GET  /report/{id}    →  metrics + confidence               │
│  GET  /health         →  {"status": "ok"}                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Registration Pipeline (Background Job)          │
│                                                              │
│  ┌──────────┐   ┌───────────┐   ┌─────────┐   ┌─────────┐ │
│  │ Ingestion│──▶│Preprocess │──▶│ Routing │──▶│ Matching│  │
│  │ (loader) │   │ (4 stages)│   │(decide) │   │(SIFT or │  │
│  │          │   │           │   │         │   │ LoFTR)  │  │
│  └──────────┘   └───────────┘   └─────────┘   └────┬────┘ │
│                                                      │       │
│                                              ┌───────▼─────┐│
│                                              │  Evaluation  ││
│                                              │ (SSIM, MI,   ││
│                                              │  confidence) ││
│                                              └─────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Request Lifecycle

1. User uploads Source Image + Reference Image via frontend
2. Frontend calls `POST /images/upload` for each → receives `image_id` + `ImageMetadata`
3. User clicks "Start Registration" → frontend calls `POST /register` with both IDs
4. Backend creates a background job, returns `job_id` with HTTP 202
5. Frontend polls `GET /register/{job_id}` every 2 seconds
6. Background job: preprocess images → route (classical or deep) → match → warp → compute metrics
7. Frontend receives `status: "done"` → calls `GET /report/{job_id}` for metrics
8. Results displayed: overlay slider + metrics panel + confidence score

---

## 3. How It Works — Plain English Explanation

### 3.1 The Big Picture

**Problem:** Satellites take thousands of images of the Moon's surface. These images are taken by different cameras (TMC-2, OHRC, LRO-NAC), at different altitudes (different resolutions), at different times of day (different lighting/shadows), and from slightly different angles. To create accurate maps or detect changes, we need to **align** (register) these images so that the same crater/feature appears at the same pixel location in both.

**Analogy:** Imagine you take two photos of the same street from different positions and with different cameras. To overlay them perfectly, you need to find common landmarks (buildings, corners), figure out how one photo needs to be stretched/rotated to match the other, and then verify the alignment looks correct.

**Why it's hard:**
- Different sensors produce images at wildly different resolutions (5m/pixel vs 0.28m/pixel)
- Sun angle differences create different shadow patterns
- Some areas have rich texture (craters, rocks) while others are smooth (lunar mare)
- Traditional math-based methods fail on very different images; deep learning is needed as a fallback

### 3.2 The Pipeline Step-by-Step

#### Step 1: Reading the Photos (Ingestion)

When satellite images are stored, they come in specialized scientific formats:
- **PDS3** (Planetary Data System v3): An old NASA standard. A text "label" file describes the image, and a separate binary `.img` file contains the actual pixel data.
- **PDS4** (Planetary Data System v4): The newer XML-based standard. Same concept — XML label + binary body.
- **GeoTIFF**: A standard image format with embedded geolocation metadata (CRS, pixel scale).

The ingestion module reads these formats, extracts the pixel data into a NumPy array, and parses metadata (product ID, sensor type, pixel scale in meters, sun azimuth/elevation angles, bit depth). This metadata is crucial for later steps — especially sun angles for illumination correction and pixel scale for resolution matching.

**Key metadata fields:**
- `pixel_scale_m`: How many meters each pixel represents (e.g., 5.0 m for TMC-2, 0.28 m for OHRC)
- `sun_elevation_deg`: How high the sun was when the image was taken (affects shadows)
- `sensor`: Which camera took the image (determines default processing parameters)

#### Step 2: Cleaning the Photos (Preprocessing)

Raw satellite images have problems that need fixing before matching:

1. **Denoising**: Space sensors produce noisy images. We use Non-Local Means denoising (similar to how Photoshop's "Reduce Noise" works — it finds similar patches across the image and averages them).

2. **Photometric Correction**: Images taken at different sun angles have different brightness levels. We apply a Lunar-Lambert reflectance model: `corrected = pixel × cos(incidence)^(k-1)` where `k=0.6`. This brightens images taken at low sun angles (long shadows) and slightly darkens images taken at high sun angles, making them comparable.

3. **Shadow Normalization**: Even after photometric correction, deep shadows remain. We detect shadow regions (pixels below the 5th percentile of intensity), apply gamma correction to brighten them, and blend the result smoothly using a Gaussian-blurred mask to avoid harsh edges.

4. **CLAHE** (Contrast Limited Adaptive Histogram Equalization): Enhances contrast locally in small tiles of the image, preventing any single region from becoming too bright or too dark. Applied to the luminance channel only (LAB color space) to avoid color distortion.

**Why order matters:** Denoise first (removes noise that would interfere with later steps), then correct lighting, then fix shadows, then enhance contrast last (so it works on clean, well-lit data).

#### Step 3: Figuring out the Scale (Pyramid)

If one image is at 5m/pixel and another at 0.28m/pixel, the same crater appears at very different sizes. The pyramid module builds a **Gaussian pyramid** — a stack of the same image at progressively lower resolutions (each level is half the size of the previous).

**Analogy:** Like zooming out on Google Maps. At the top level, you see the whole image. At each lower level, you see half the detail but twice the coverage.

We estimate the **scale ratio** between two images using their pixel scales (metadata-based) or phase correlation (FFT-based, comparing which zoom level produces the best correlation). Then we select pyramid levels where both images are at approximately the same effective resolution.

#### Step 4: Finding Landmarks (Feature Detection)

We need to find distinctive points (keypoints) in each image that can be matched between the two. Three detectors are available:

- **SIFT** (Scale-Invariant Feature Transform): The classic. Finds ~500-5000 "interesting" corners/edges, creates a 128-dimensional descriptor (a numerical fingerprint) for each. Robust to scale and rotation changes. Uses floating-point descriptors (good for precise matching).

- **ORB** (Oriented FAST and Rotated BRIEF): Fast alternative. Creates 32-byte binary descriptors. Much faster than SIFT but less robust to scale changes. Uses Hamming distance for matching instead of Euclidean.

- **AKAZE** (Accelerated Kaze): 61-byte binary descriptors. Good balance of speed and accuracy. Uses nonlinear diffusion for feature detection (preserves edges better than Gaussian blur).

**The factory pattern** lets callers request any detector by name (`get_detector("sift")`) without knowing the implementation details. Each detector returns a `FeatureResult` with keypoints (Nx2 coordinates), descriptors (NxD array), and responses (strength scores).

#### Step 5: Matching Landmarks (Matching)

Given keypoints in Image A and Image B, we need to find which ones correspond to the same physical location.

**Classical matching** works like this:
1. For each keypoint in Image A, find the 2 nearest keypoints in Image B (by descriptor similarity)
2. Apply **Lowe's ratio test**: if the best match is much closer than the second-best (ratio < 0.75), it's likely correct. If both are similarly close, it's ambiguous and we discard it.
3. Use either **FLANN** (Fast Library for Approximate Nearest Neighbors, optimized for speed) or **brute-force** matching depending on descriptor type (float vs binary).

The result is a set of **correspondences**: pairs of points `(point_in_A, point_in_B)` that we believe represent the same physical feature.

#### Step 6: Deciding the Strategy (Routing)

Not all image pairs are equally easy to match. The routing module computes a **difficulty score** (0.0 to 1.0) from three factors:

1. **Texture richness** (weight: 0.4): Measured by Laplacian variance. Smooth lunar mare (flat basalt) = high difficulty (hard to find distinctive features). Cratered highlands = low difficulty (easy to find features).

2. **Illumination difference** (weight: 0.3): Difference in sun elevation angles. If one image was taken at dawn and another at noon, shadows look completely different = high difficulty.

3. **Scale difference** (weight: 0.3): Ratio of pixel scales. If one image is 5m/pixel and another is 0.28m/pixel = high difficulty.

**Decision logic:**
- If difficulty < 0.5 (default threshold): Use **classical path** (SIFT + FLANN). Fast, works well for similar images.
- If difficulty ≥ 0.5: Use **deep learning path** (LoFTR). Slower but handles dramatically different images.

**Retry logic:** If the first attempt fails (inlier ratio < 0.3), we retry up to 2 more times (3 total attempts). This handles cases where the initial routing decision was wrong.

#### Step 7: Warping to Align (Transform + Warp)

Once we have correspondences, we need to compute the **geometric transformation** that maps Image B onto Image A's coordinate frame.

**Homography** (most common): A 3×3 matrix that describes perspective transformation. Think of it as "how to stretch/bend/warp Image B so it overlays Image A." Requires at least 4 point correspondences.

**RANSAC** (Random Sample Consensus): Since some correspondences are wrong (outliers), RANSAC iteratively:
1. Picks 4 random correspondences
2. Computes a homography from just those 4
3. Counts how many other correspondences agree with that homography (inliers)
4. Repeats many times, keeping the homography with the most inliers

This is robust to up to 50% outliers, which is essential since real matching always produces some incorrect pairs.

**Warping:** Once we have the homography, we apply `cv2.warpPerspective` to transform every pixel of Image B into Image A's coordinate system. The result is a "warped" image that should align with Image A.

#### Step 8: Checking Quality (Evaluation)

How do we know if the registration worked? We compute several metrics:

- **SSIM** (Structural Similarity Index): Compares the structures (edges, textures) between the warped image and the reference. Range: [-1, 1]. Values near 1.0 mean excellent alignment.

- **Mutual Information**: Measures how much knowing a pixel value in one image tells you about the corresponding pixel in the other. Higher values = stronger correlation = better alignment.

- **Inlier Ratio**: What fraction of the matched points actually agreed with the final homography? Higher = more reliable matching.

- **Corner Reprojection Error**: We take the 4 corners of the image, transform them through the homography, and measure how far they are from the expected positions. Lower = more accurate.

- **Composite Confidence**: A weighted combination of the above metrics, normalized to [0, 100]. Weights are configurable (SSIM: 0.3, MI: 0.2, inlier ratio: 0.3, corner error: 0.2). This gives users a single number to judge quality.

### 3.3 The API Flow

```
User                Frontend              Backend              Pipeline
 │                    │                     │                     │
 │  Upload images     │                     │                     │
 │───────────────────▶│ POST /images/upload  │                     │
 │                    │─────────────────────▶│ load_image()        │
 │                    │                     │────────────────────▶│
 │                    │◀──── image_id ───────│                     │
 │                    │                     │                     │
 │  Start registration│                     │                     │
 │───────────────────▶│ POST /register       │                     │
 │                    │─────────────────────▶│ create job (bg)     │
 │                    │◀──── job_id (202) ───│                     │
 │                    │                     │  ┌──────────────┐   │
 │  Poll status       │                     │  │ Preprocess   │   │
 │───────────────────▶│ GET /register/{id}  │  │ Route        │   │
 │                    │─────────────────────▶│  │ Match        │   │
 │                    │◀── status: running ──│  │ Warp         │   │
 │                    │                     │  │ Evaluate     │   │
 │  Poll again        │                     │  └──────────────┘   │
 │───────────────────▶│ GET /register/{id}  │                     │
 │                    │─────────────────────▶│                     │
 │                    │◀── status: done ─────│                     │
 │                    │                     │                     │
 │  View results      │                     │                     │
 │───────────────────▶│ GET /report/{id}    │                     │
 │                    │─────────────────────▶│                     │
 │                    │◀── metrics + conf ───│                     │
 │                    │                     │                     │
 │  See overlay +     │                     │                     │
 │  metrics + score   │                     │                     │
 │◀───────────────────│                     │                     │
```

### 3.4 Key Design Decisions Explained

**Why use both classical and deep learning?**
Classical methods (SIFT) are fast and work great when images are similar. But they fail when images differ too much (different resolutions, extreme lighting). Deep learning (LoFTR) handles these hard cases but is slower and requires GPU for reasonable speed. The router picks the right tool for each job.

**Why retry up to 3 times?**
Sometimes the difficulty estimation is wrong (e.g., it says "easy" but the classical matcher fails). Retrying with the same routing gives the algorithm another chance with different random RANSAC seeds. This catches cases where a single bad random initialization caused failure.

**Why preprocess before matching?**
Noise creates false keypoints. Shadows create false intensity patterns. Different brightness levels confuse descriptor computation. Cleaning the images first makes matching more reliable.

**Why normalize sun illumination?**
The same crater looks completely different at dawn (long shadows, high contrast) vs noon (flat lighting, low contrast). Photometric correction normalizes these differences so the matcher sees similar brightness patterns regardless of when the image was taken.

---

## 4. Source Modules (src/) — Full Technical Detail

### 4.1 `common/` — Shared Types and Errors

| File | Purpose |
|------|---------|
| `schema.py` | `ImageMetadata` frozen dataclass (12 fields with validation) |
| `errors.py` | Custom exceptions |

**`ImageMetadata` fields:**

| Field | Type | Validation | Description |
|-------|------|------------|-------------|
| `product_id` | `str` | — | Product/image identifier |
| `sensor` | `Literal["TMC2", "OHRC", "LRO_NAC"]` | — | Instrument sensor type |
| `archive_standard` | `Literal["PDS3", "PDS4", "GEOTIFF"]` | — | Archive format |
| `pixel_scale_m` | `float` | Must be positive | Meters per pixel |
| `swath_km` | `Optional[float]` | — | Swath width in km (PDS4 only) |
| `altitude_km` | `Optional[float]` | — | Spacecraft altitude in km (PDS4 only) |
| `sun_azimuth_deg` | `Optional[float]` | [0, 360) | Sun azimuth in degrees |
| `sun_elevation_deg` | `Optional[float]` | [-90, 90] | Sun elevation in degrees |
| `acquisition_time` | `Optional[datetime]` | — | Image acquisition timestamp |
| `image_shape` | `Tuple[int, int]` | — | (lines, samples) |
| `bit_depth` | `int` | Default 16 | Bit depth (8, 12, or 16) |
| `source_path` | `str` | — | Original file path |

**Custom exceptions:**
- `UnsupportedFormatError` — Unrecognized file extension
- `CorruptImageError` — Defined but not currently used
- `FileNotFoundError` — Required companion file missing

### 4.2 `ingestion/` — Data Loading and Format Detection

| File | Lines | Purpose |
|------|-------|---------|
| `loader.py` | 76 | Main dispatcher, companion file resolution |
| `pds3_reader.py` | 146 | PDS3 PVL label + binary body reader |
| `pds4_reader.py` | 181 | PDS4 XML label + binary body reader |
| `geotiff_reader.py` | 61 | GeoTIFF reader via rasterio |

**`load_image(path)` dispatch logic:**
- `.xml` → `read_pds4()`
- `.tif` / `.tiff` → `read_geotiff()`
- `.img` / `.lbl` / `.dat` / `.raw` → find companion label → determine PDS3 or PDS4 → call appropriate reader

**Companion file resolution:**
- For `.img` files, searches for `.lbl` or `.xml` in the same directory
- Checks case-insensitive variants (`.LBL`, `.XML`)
- Checks `_body.img` / `_BODY.IMG` naming patterns

**Format details:**

| Format | Extensions | Label | Library | Bit Depth Support |
|--------|-----------|-------|---------|-------------------|
| PDS4 | `.xml` (label), `.img`/`.dat`/`.bin` (body) | XML | `xml.etree.ElementTree` | 16-bit unsigned |
| PDS3 | `.lbl` (label), `.img`/`.dat`/`.raw` (body) | PVL | `pvl` | 8, 12 (bitmask `& 0x0FFF`), 16-bit |
| GeoTIFF | `.tif`, `.tiff` | Embedded | `rasterio` | Single-band |

### 4.3 `preprocessing/` — 4-Stage Image Cleaning Pipeline

| File | Lines | Purpose |
|------|-------|---------|
| `pipeline.py` | 94 | Pipeline orchestrator with YAML config |
| `denoise.py` | 39 | NLM/bilateral/median denoising |
| `photometric.py` | 47 | Lunar-Lambert reflectance correction |
| `shadow_normalize.py` | 63 | Shadow detection + gamma correction |
| `clahe.py` | 44 | Contrast Limited Adaptive Histogram Equalization |

**`PreprocessingPipeline` execution order:**
1. Guard: all-zero image → return unchanged
2. Guard: NaN/Inf → replace with zeros
3. **Denoise** (if enabled) — `denoise(img, method="nlm")`
4. **Photometric correction** (if enabled) — `photometric_correct(img, meta)`
5. **Shadow normalization** (if enabled) — `shadow_aware_normalize(img, percentile=5.0)`
6. **CLAHE** (if enabled) — `apply_clahe(img, clip_limit=2.0, tile_grid_size=(8,8))`

**Denoising methods:**
- `nlm`: `cv2.fastNlMeansDenoising(h=10, templateWindowSize=7, searchWindowSize=21)` — best general-purpose
- `bilateral`: `cv2.bilateralFilter(d=9, sigmaColor=75, sigmaSpace=75)` — edge-preserving
- `median`: `cv2.medianBlur(ksize=5)` — salt-and-pepper noise

**Photometric correction formula:**
```
cos_incidence = sin(sun_elevation_rad)
corrected = normalized_pixel × cos_incidence^(k-1)   where k = 0.6
```
This simplifies to `pixel × cos_incidence^(-0.4)`, which brightens low-sun images and slightly darkens high-sun images.

**Shadow normalization algorithm:**
1. Detect shadows: pixels between 0 (exclusive) and 5th percentile (inclusive)
2. Compute gamma: `gamma = log(mean_illuminated × 0.8) / log(mean_shadow)`, clipped to [0.5, 3.0]
3. Apply gamma correction to shadow pixels
4. Blend with Gaussian-blurred mask for smooth transitions

**CLAHE on color images:** Converts BGR → LAB, applies CLAHE to L channel only, converts back to BGR. This preserves color while enhancing contrast.

### 4.4 `pyramid/` — Multi-Scale Analysis

| File | Lines | Purpose |
|------|-------|---------|
| `builder.py` | ~40 | Gaussian/Laplacian pyramid construction |
| `scale_estimator.py` | ~80 | Scale ratio estimation, pyramid level selection |

**`build_gaussian_pyramid(img, levels)`:**
- Uses `cv2.pyrDown()` for downsampling (each level is half the previous)
- Clamps levels based on minimum dimension (16px minimum)
- Returns list of progressively smaller images

**`build_laplacian_pyramid(gaussian_pyramid)`:**
- Computes difference between each level and its upsampled version
- Last level = last Gaussian level
- Useful for image reconstruction

**Scale estimation methods:**
- **Metadata-based**: `pixel_scale_a / pixel_scale_b`
- **Phase correlation**: Tests candidate scales [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0] on 128×128 resized images, returns scale with highest correlation

**Pyramid level selection:**
- `level_diff = round(log2(scale_ratio))`
- Returns `(level_a, level_b)` tuple

### 4.5 `features/` — Feature Detection (Strategy + Factory Pattern)

| File | Lines | Purpose |
|------|-------|---------|
| `base.py` | ~50 | `BaseDetector` ABC, `FeatureResult` dataclass |
| `factory.py` | ~30 | `get_detector()` with lazy imports |
| `sift_detector.py` | ~70 | SIFT implementation |
| `orb_detector.py` | ~70 | ORB implementation |
| `akaze_detector.py` | ~70 | AKAZE implementation |

**`FeatureResult` dataclass:**

| Field | Type | Description |
|-------|------|-------------|
| `keypoints` | `np.ndarray` (Nx2, float32) | x,y coordinates |
| `descriptors` | `np.ndarray` (NxD) | Feature descriptors |
| `responses` | `np.ndarray` (N,) | Keypoint response strengths |
| `detector_name` | `str` | Detector identifier |

**`get_detector(name, **params)`:**
- `"sift"` → `SIFTDetector(nfeatures=500, ...)`
- `"orb"` → `ORBDetector(nfeatures=1000, ...)`
- `"akaze"` → `AKAZEDetector(threshold=0.001, ...)`
- Raises `ValueError` for unknown names

**Detector characteristics:**

| Detector | Descriptor Size | Descriptor Type | Matching Distance | Speed |
|----------|----------------|-----------------|-------------------|-------|
| SIFT | 128D | float32 | L2 (Euclidean) | Medium |
| ORB | 32 bytes | uint8 | Hamming | Fast |
| AKAZE | 61 bytes | uint8 | Hamming | Medium |

**All detectors:**
- Validate image size (minimum 16×16)
- Copy input to avoid mutation
- Normalize non-uint8 to uint8 (float ≤1.0 → ×255; otherwise NORM_MINMAX)
- Convert BGR to grayscale if needed
- Return empty `FeatureResult` if no keypoints found

### 4.6 `matching/` — Correspondence and Transform Estimation

| File | Lines | Purpose |
|------|-------|---------|
| `classical_matcher.py` | 98 | FLANN/brute-force descriptor matching |
| `transform_estimator.py` | 70 | RANSAC homography/affine/TPS estimation |
| `warp.py` | 33 | Image warping (perspective/affine/TPS) |

**`match_features(fr_a, fr_b, method="flann", ratio_thresh=0.75)`:**
- Auto-dispatches to `_match_float` (SIFT) or `_match_binary` (ORB/AKAZE) based on descriptor dtype
- Uses `knnMatch` with k=2 for Lowe's ratio test
- Returns Nx2 array of `(queryIdx, trainIdx)` pairs

**Float matching (SIFT):**
- FLANN: `cv2.FlannBasedMatcher` with KD-tree (algorithm=1, trees=5, checks=50)
- Brute-force: `cv2.BFMatcher` with L2 norm
- Ratio threshold: 0.75

**Binary matching (ORB/AKAZE):**
- FLANN: `cv2.FlannBasedMatcher` with LSH (algorithm=6, table_number=12, key_size=12)
- Brute-force: `cv2.BFMatcher` with Hamming norm
- Ratio threshold: 0.8

**`estimate_transform(pts_a, pts_b, model="homography", method="USAC_MAGSAC", ransac_thresh=3.0)`:**

| Model | Min Points | OpenCV Function | Output |
|-------|-----------|-----------------|--------|
| `"homography"` | 4 | `cv2.findHomography(USAC_MAGSAC)` | 3×3 matrix + boolean mask |
| `"affine"` | 4 | `cv2.estimateAffinePartial2D()` | 2×3 matrix + boolean mask |
| `"tps"` | 3 | `cv2.createThinPlateSplineShapeTransformer()` | TPS object + all-True mask |

**`warp_source(src_img, transform, model, output_shape)`:**
- `"homography"` → `cv2.warpPerspective`
- `"affine"` → `cv2.warpAffine`
- `"tps"` → `cv2.remap` via TPS warpImage or meshgrid

### 4.7 `deep_matching/` — Neural Matchers

| File | Lines | Purpose |
|------|-------|---------|
| `device_manager.py` | 17 | GPU/CPU device selection |
| `superpoint_wrapper.py` | 88 | SuperPoint keypoint detector |
| `loftr_wrapper.py` | 56 | LoFTR dense matcher |
| `lightglue_wrapper.py` | 68 | LightGlue two-stage matcher |

**`get_device(prefer_gpu=True)`:**
- Returns `torch.device("cuda")` if GPU available and preferred
- Falls back to `torch.device("cpu")`

**`SuperPointExtractor`:**
- Primary: Kornia `kornia.feature.SuperPoint` → keypoints (Nx2), descriptors (Nx256), scores (N)
- Fallback: `cv2.SIFT_create(nfeatures=500)` if Kornia fails
- Returns `FeatureResult` with `detector_name="superpoint"` or `"superpoint_fallback"`

**`LoFTRMatcher`:**
- Lazy-loads `kornia.feature.LoFTR(pretrained="outdoor")`
- Input: two images → preprocess to grayscale float32 [0,1] tensors [1,1,H,W]
- Output: `mkpts0` (Nx2), `mkpts1` (Nx2), `confidence` (N,)
- Only LoFTR is actively wired into the routing module

**`LightGlueMatcher`:**
- Lazy-loads `kornia.feature.SuperPoint` + `kornia.feature.LightGlue(features="superpoint")`
- Two-stage: detect features with SuperPoint, then match with LightGlue
- Same output format as LoFTR

**Dependencies:** `torch`, `kornia`, `cv2`, `numpy`

### 4.8 `routing/` — Difficulty-Aware Dispatcher

| File | Lines | Purpose |
|------|-------|---------|
| `difficulty_estimator.py` | 72 | Weighted difficulty scoring |
| `router.py` | 143 | Classical vs deep dispatch |
| `retry_loop.py` | 44 | Retry wrapper (up to 3 attempts) |

**`estimate_difficulty(img_a, img_b, meta_a, meta_b) -> float [0, 1]`:**

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Texture | 0.4 | `1.0 - min(1.0, laplacian_variance / 500.0)` |
| Illumination | 0.3 | `abs(sun_elev_a - sun_elev_b) / 90.0` |
| Scale | 0.3 | `abs(log2(scale_ratio)) / 8.0` |

**`RegistrationResult` dataclass:**

| Field | Type | Description |
|-------|------|-------------|
| `transform` | `Optional[np.ndarray]` | 3×3 homography or 2×3 affine |
| `inlier_ratio` | `float` | Fraction of inlier correspondences |
| `matcher_used` | `str` | `"classical"`, `"deep"`, or `"none"` |
| `difficulty` | `float` | Computed difficulty score |
| `success` | `bool` | Whether registration succeeded |
| `error_message` | `str` | Human-readable error if failed |

**`route_and_register(img_a, img_b, meta_a, meta_b, config=None)`:**
- Loads config from `configs/routing.yaml`
- Computes difficulty
- If difficulty < 0.5: `_try_classical()` (SIFT + FLANN + homography)
- If difficulty ≥ 0.5: `_try_deep()` (LoFTR + homography)

**`register_with_retry(..., max_retries=2)`:**
- Calls `route_and_register()` up to `max_retries + 1` times
- Returns immediately if result succeeds with `inlier_ratio >= 0.3`
- Otherwise tracks best result and returns it marked as failed

### 4.9 `evaluation/` — Quality Metrics

| File | Lines | Purpose |
|------|-------|---------|
| `metrics.py` | 106 | SSIM, MI, inlier ratio, corner reprojection error |
| `confidence.py` | 62 | Weighted composite [0, 100] score |
| `self_consistency.py` | 49 | Forward-backward RMSE |

**`compute_ssim(ref, warped) -> float [-1, 1]`:**
- Uses `skimage.metrics.structural_similarity`
- Converts BGR to grayscale
- Restricts to overlap region (both images non-zero)
- Returns 0.0 if no overlap

**`compute_mutual_information(ref, warped) -> float [0, ∞)`:**
- 2D histogram (64 bins) over jointly valid pixels
- `MI = H(x) + H(y) - H(x,y)` where H = entropy

**`compute_inlier_ratio(inlier_mask) -> float [0, 1]`:**
- `sum(mask) / len(mask)`, or 0.0 for empty mask

**`compute_corner_reprojection_error(transform, model, image_shape, ground_truth) -> Optional[float]`:**
- Projects 4 image corners through transform
- Returns mean Euclidean error in pixels
- Returns `None` if no ground truth provided

**`composite_confidence(metrics, weights=None) -> float [0, 100]`:**

| Metric | Weight | Normalization |
|--------|--------|---------------|
| SSIM | 0.3 | Clamp to [0, 1] |
| Mutual Information | 0.2 | `min(1.0, MI / 5.0)` |
| Inlier Ratio | 0.3 | Clamp to [0, 1] |
| Corner Reproj Error | 0.2 | `max(0.0, 1.0 - error / 10.0)` |

Final: weighted sum / sum of available weights × 100, rounded to 2 decimals.

**`forward_backward_rmse(img_a, img_b, meta_a, meta_b, grid_size=10) -> float`:**
1. Register A→B (forward)
2. Register B→A (backward)
3. Generate grid of points
4. Apply forward then backward transform
5. Compute RMSE between original and round-tripped points
6. Perfect alignment = 0.0; failure = infinity

### 4.10 `api/` — REST Service

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | ~50 | FastAPI app, CORS, error handlers, health |
| `schemas.py` | ~60 | Pydantic request/response models |
| `background.py` | ~80 | In-memory job store, background worker |
| `routes/upload.py` | ~40 | POST /images/upload |
| `routes/register.py` | ~50 | POST /register, GET /register/{job_id} |
| `routes/report.py` | ~30 | GET /report/{job_id} |

**Endpoints:**

| Method | Path | Status | Purpose |
|--------|------|--------|---------|
| `GET` | `/health` | 200 | Health check |
| `POST` | `/images/upload` | 200 | Upload image, return image_id + metadata |
| `POST` | `/register` | 202 | Start registration job, return job_id |
| `GET` | `/register/{job_id}` | 200 | Poll job status |
| `GET` | `/report/{job_id}` | 200/202 | Get metrics + confidence |

**Pydantic models:**
- `ImageMetadataModel` — Request/response metadata
- `UploadResponse` — `image_id` + metadata
- `RegisterRequest` — `source_image_id` + `reference_image_id` + optional params
- `RegisterResponse` — `job_id` + status
- `JobStatus` — `job_id` + status + optional result
- `ReportResponse` — `job_id` + status + optional metrics + confidence
- `ErrorResponse` — `detail` string

**Middleware:**
- CORS: `allow_origins=["*"]`, all methods, all headers
- Error handlers: ValueError → 404, Exception → 500

**Background job (`run_registration_job`):**
1. Load images from in-memory store
2. Run preprocessing pipeline
3. Call `register_with_retry()`
4. If successful: warp image, compute SSIM, MI, inlier ratio
5. Compute composite confidence
6. Update job dict with result or error

**State:** All in-memory (image store + job store). Does not survive restarts.

---

## 5. Frontend (frontend/)

### 5.1 Stack

- **Framework:** React 18.2 (JSX, no TypeScript)
- **Build tool:** Vite 5.x
- **Port:** 3000 (dev server)
- **Proxy:** `/images`, `/register`, `/report`, `/health` → `http://localhost:8000`
- **Styling:** Inline styles only (no CSS framework)

### 5.2 Components

| Component | File | Purpose | Status |
|-----------|------|---------|--------|
| `App` | `App.jsx` | Root workflow controller | Active |
| `BlendSlider` | `BlendSlider.jsx` | Overlay opacity slider | Active |
| `ReportPanel` | `ReportPanel.jsx` | Metrics + confidence display | Active |
| `DualImageViewer` | `DualImageViewer.jsx` | Side-by-side viewer | **Unused** |
| `MatchOverlay` | `MatchOverlay.jsx` | Feature count display | **Unused** |

**`App.jsx` state machine:**
- `idle` → user uploads images
- `submitting` → POST /register called
- `polling` → GET /register/{id} every 2s (up to 60 attempts)
- `done` → GET /report/{id} → display results
- `failed` → show error
- `timeout` → 60 polls exceeded

### 5.3 API Client (`api/client.js`)

| Function | Method | Endpoint | Returns |
|----------|--------|----------|---------|
| `uploadImage(file)` | POST | `/images/upload` | `{ image_id }` |
| `startRegistration(srcId, refId, params)` | POST | `/register` | `{ job_id }` |
| `pollRegistration(jobId)` | GET | `/register/{jobId}` | `{ status }` |
| `getReport(jobId)` | GET | `/report/{jobId}` | `{ metrics, confidence }` |
| `getOverlayUrl(jobId)` | URL builder | `/report/{jobId}/overlay` | URL string |

### 5.4 Build Scripts

| Script | Command |
|--------|---------|
| `npm run dev` | Vite dev server (port 3000) |
| `npm run build` | Production build → `dist/` |
| `npm run preview` | Preview production build |

---

## 6. Tests (tests/)

### 6.1 Framework

- **pytest** >= 7.4.0
- Config: `testpaths = ["tests"]`, `addopts = "-v"`
- Optional: `pytest-cov` for coverage

### 6.2 Test Files

| File | Lines | Tests |
|------|-------|-------|
| `test_api.py` | 100 | Health, upload, register, report endpoints |
| `test_ingestion.py` | 140 | PDS3/PDS4/GeoTIFF loading, edge cases, round-trip |
| `test_preprocessing.py` | 120 | Denoise, CLAHE, shadow, photometric, full pipeline |
| `test_pyramid.py` | 75 | Gaussian/Laplacian pyramids, scale ratio, level selection |
| `test_features.py` | 81 | SIFT/ORB/AKAZE detection, factory validation |
| `test_classical_matching.py` | 80 | Feature matching, homography recovery, warp |
| `test_deep_matching.py` | 69 | SuperPoint, LoFTR, LightGlue (device, shape, confidence) |
| `test_evaluation.py` | 69 | SSIM, MI, inlier ratio, composite confidence |
| `test_routing.py` | 62 | Difficulty estimation, classical routing, retry loop |

### 6.3 Fixture Files

| File | Format | Contents |
|------|--------|----------|
| `fixtures/synth_pds3_label.lbl` | PDS3 PVL | 64×64 uint16 metadata (TMC2, sun 45°/30°, 5.0m/pixel) |
| `fixtures/synth_pds3_body.img` | Raw binary | 64×64 uint16 random pixels |
| `fixtures/synth_pds4_label.xml` | PDS4 XML | 64×64 uint16 metadata (sun 120°/35°, 0.28m/pixel) |
| `fixtures/synth_pds4_body.img` | Raw binary | 64×64 uint16 random pixels |
| `fixtures/synth_geotiff.tif` | GeoTIFF | 64×64 uint16, EPSG:4326, sun 150°/25° |

### 6.4 Key Assertions

| Pattern | Where | Purpose |
|---------|-------|---------|
| `assert response.status_code == 200/202/404` | test_api | HTTP status validation |
| `assert result.shape == expected` | test_features, test_preprocessing | Output shape correctness |
| `assert result.dtype == expected` | test_preprocessing | Data type preservation |
| `assert error < threshold` | test_classical_matching | Numerical accuracy (Frobenius norm < 0.1) |
| `assert metric >= threshold` | test_evaluation | Quality bounds (SSIM >= 0.99) |
| `assert not np.any(np.isnan(...))` | test_preprocessing | No NaN propagation |
| `pytest.raises(ExceptionType)` | test_ingestion, test_features | Expected exception validation |
| `pytest.skip("reason")` | test_api, test_deep_matching | Missing dependency skip |

---

## 7. Configuration (configs/)

| File | Key Settings |
|------|-------------|
| `ingestion.yaml` | Sensor defaults: TMC2 (5.0m), OHRC (0.28m), LRO_NAC (0.5-2.0m); pixel_scale_sanity bounds |
| `preprocessing.yaml` | Stages: denoise (nlm, enabled), photometric (enabled), shadow_normalize (percentile 5.0, enabled), clahe (clip 2.0, grid 8×8, enabled) |
| `pyramid.yaml` | max_levels: 6, phase_correlation_scales: [0.25...16.0], min_image_dim: 16 |
| `features.yaml` | SIFT: fast(500)/thorough(5000); ORB: fast(1000)/thorough(5000); AKAZE: fast(0.001)/thorough(0.0005); default: sift+fast |
| `matching.yaml` | matcher: flann, ratio_threshold: 0.75; transform: homography, ransac_threshold: 3.0 |
| `routing.yaml` | difficulty_threshold: 0.5, min_inlier_ratio: 0.3; weights: texture 0.4, illumination 0.3, scale 0.3 |
| `evaluation.yaml` | confidence.weights: ssim 0.3, mi 0.2, inlier_ratio 0.3, corner_reproj 0.2 |
| `deep_matching.yaml` | device: prefer_gpu true; superpoint: confidence 0.5; loftr: outdoor, confidence 0.5; lightglue: superpoint, confidence 0.5 |

---

## 8. Infrastructure

### 8.1 Docker Compose

- **backend:** Python 3.11 + uvicorn on port 8000, `PYTHONPATH=/app`
- **frontend:** Node 20 build → Nginx on port 80, depends on backend
- GPU support commented out (nvidia deploy resources)

### 8.2 Dockerfiles

| File | Base Image | Purpose |
|------|-----------|---------|
| `docker/backend.Dockerfile` | `python:3.11-slim` | Python backend + GDAL + rasterio |
| `docker/frontend.Dockerfile` | `node:20-alpine` → `nginx:alpine` | React build → static Nginx |

### 8.3 Dev Container

- Base: `mcr.microsoft.com/devcontainers/typescript-node:24`
- Installs: `opencode-ai`, `agent-browser`, `chromium`
- Post-create: `bash .devcontainer/setup.sh`

### 8.4 Project Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | PEP 621 metadata, setuptools build, Python >= 3.10 |
| `requirements.txt` | pip dependencies (mirrors pyproject.toml + extras) |
| `.gitignore` | Excludes node_modules, dist, .env, *.sqlite, editor artifacts |
| `opencode.json` | Agent permissions: edit, bash, webfetch, websearch, skill, task |
| `skills-lock.json` | Installed skills: agent-browser |
| `Agentfeed.md` | 10-session build plan (project spec/roadmap) |

---

## 9. Key Observations

1. **All state is in-memory** — no database; image store and job store don't survive process restarts and aren't shared across workers.

2. **No authentication** — API is fully open with CORS `allow_origins=["*"]`.

3. **Only LoFTR is wired into routing** — SuperPoint and LightGlue wrappers exist but are not called by the router. They're available as standalone components.

4. **Two frontend components are unused** — `DualImageViewer` and `MatchOverlay` are defined but not rendered in `App.jsx`. They may have been planned for future use or removed during development.

5. **Logging inconsistency** — SIFT silently converts non-uint8 images; ORB and AKAZE log warnings for the same conversion.

6. **Config weights are non-empirical** — All YAML config files explicitly note their weights are "configurable, NOT empirically derived from labeled data." They're tunable defaults.

7. **Dependency split** — `pyproject.toml` uses system-level GDAL (via rasterio), while `requirements.txt` includes `GDAL` as a separate pip package. Also, `requirements.txt` includes `Pillow` and `torchvision` not in `pyproject.toml`.

8. **No frontend testing** — No test framework, no ESLint, no Prettier configured for the React app.

9. **Descriptor dtype preservation** — SIFT descriptors are cast to float32 (for L2 matching), ORB/AKAZE remain uint8 (for Hamming matching). This is correct per algorithm characteristics.

10. **Empty-result shapes are detector-specific** — SIFT: `(0,0)` float32, ORB: `(0,32)` uint8, AKAZE: `(0,61)` uint8. This ensures downstream shape inspection works correctly even on empty results.
