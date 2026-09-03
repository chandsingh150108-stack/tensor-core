# LUNAR IMAGE REGISTRATION — Agent Execution Feed
### 10-Session Build Plan for a Robust Multi-Scale Lunar Image Registration Framework
Domain: ISRO Chandrayaan-2 (TMC-2 / OHRC) + NASA LRO-NAC | Smart India Hackathon

Stack: Python, OpenCV, scikit-image, PyTorch, Kornia, SuperPoint, LoFTR, LightGlue, GDAL, rasterio, PDS4 tools, FastAPI, React, Docker.

---

## Corrections applied from the accuracy review

These fixes are baked into the sessions below, not left as loose notes:

1. **Dual archive-format ingestion.** Chandrayaan-2 TMC-2/OHRC data is natively PDS4. LRO NAC data is PDS3-origin (ASU now ships detached PDS4 labels over the same PDS3 image bodies, but the raw `.IMG` bodies are still PDS3-structured). Session 1 builds parsers for **both**, not just `pds4_tools`.
2. **CLAHE is spelled out correctly** as Contrast **Limited Adaptive** Histogram Equalization everywhere it appears (Session 2).
3. **DISK descriptor dropped.** It appeared in the original module table but isn't in the agreed tech stack — Session 6 implements SuperPoint / LoFTR / LightGlue only.
4. **The "~70% easy / ~30% hard" pair split is treated as a configurable assumption**, not a hard-coded empirical constant — it lives in `configs/routing.yaml` with a comment explaining it's a tunable default, and Session 7's difficulty estimator is what actually determines routing at runtime.
5. **Confidence-score metric weights are configurable**, not baked-in magic numbers, for the same reason (Session 8).
6. Any fixture or docstring referencing LROC download URLs uses the corrected domain `lroc.im-ldi.com` (not `lroc.im.-ldi.com`).

---

## Part 1: Data Ingestion & Metadata Parsing Engine

**Session Objective & Scope:**
Build the single entry point through which every downstream session gets image pixel data and standardized metadata. This session ingests raw archive products and emits a normalized in-memory/on-disk representation. It must NOT perform any radiometric correction, denoising, or feature work — output is raw (but decoded) pixel arrays plus metadata, nothing else.

**Input Prerequisites:**
None (first session). Requires sample fixtures the agent must generate itself (see Verification).

**File Structure to Create/Modify:**
```
src/common/__init__.py
src/common/schema.py
src/ingestion/__init__.py
src/ingestion/pds3_reader.py
src/ingestion/pds4_reader.py
src/ingestion/geotiff_reader.py
src/ingestion/loader.py
configs/ingestion.yaml
tests/fixtures/synth_pds3_label.lbl
tests/fixtures/synth_pds4_label.xml
tests/fixtures/synth_geotiff.tif
tests/test_ingestion.py
```

**Step-by-Step Implementation Tasks:**
1. In `src/common/schema.py`, define a frozen dataclass `ImageMetadata` with fields: `product_id: str`, `sensor: Literal["TMC2","OHRC","LRO_NAC"]`, `archive_standard: Literal["PDS3","PDS4","GEOTIFF"]`, `pixel_scale_m: float`, `swath_km: Optional[float]`, `altitude_km: Optional[float]`, `sun_azimuth_deg: Optional[float]`, `sun_elevation_deg: Optional[float]`, `acquisition_time: Optional[datetime]`, `image_shape: Tuple[int,int]`, `bit_depth: int`, `source_path: str`. All angle fields must be validated to `[0, 360)` for azimuth and `[-90, 90]` for elevation in `__post_init__`; raise `ValueError` on violation.
2. `src/ingestion/pds3_reader.py`: implement `read_pds3(label_path: str) -> Tuple[np.ndarray, ImageMetadata]` using `pvl` to parse the attached/detached label and raw binary read (or GDAL's `PDS` driver as a fallback) for the image body. Extract `SUB_SOLAR_AZIMUTH`, `SUB_SOLAR_ELEVATION` (or LRO's equivalent keys — check both `SOLAR_*` and mission-specific aliases), `LINE_SAMPLES`, `LINES`, `SAMPLE_BITS`. This is the path used for LRO NAC EDR/CDR products.
3. `src/ingestion/pds4_reader.py`: implement `read_pds4(xml_label_path: str) -> Tuple[np.ndarray, ImageMetadata]` using `pds4_tools.read()`. Map PDS4 `Observation_Area`/`Discipline_Area` geometry nodes to the same `ImageMetadata` fields. This is the path used for Chandrayaan-2 TMC-2/OHRC products.
4. `src/ingestion/geotiff_reader.py`: implement `read_geotiff(path: str) -> Tuple[np.ndarray, ImageMetadata]` via `rasterio`. Sun-angle fields will typically be `None` here (GeoTIFF derivatives often strip mission metadata) — populate what's available from tags, leave the rest `None`, and set `archive_standard="GEOTIFF"`.
5. `src/ingestion/loader.py`: implement `load_image(path: str) -> Tuple[np.ndarray, ImageMetadata]` that dispatches by file extension/magic bytes (`.img`+`.lbl`/attached label → PDS3 path; `.xml` companion → PDS4 path; `.tif`/`.tiff` → GeoTIFF path). Raise `UnsupportedFormatError` for anything else — do not silently guess.
6. Handle edge cases explicitly: missing companion label file (raise `FileNotFoundError` with a clear message naming the expected path), corrupted/truncated binary body (catch and re-raise as `CorruptImageError`), and 12-bit-in-16-bit PDS3 packing (mask/shift correctly, don't assume 8-bit).
7. Write `configs/ingestion.yaml` documenting the sensor→pixel_scale defaults used only as a sanity-check fallback (TMC-2: 5.0 m, OHRC: 0.28 m, LRO NAC: 0.5–2.0 m range) — actual values always come from the parsed label first; the config is a validation cross-check, never an override.

**Verification & Unit Tests:**
- Generate synthetic fixtures in `tests/fixtures/`: a minimal valid PDS3 label + 64×64 uint16 raw body; a minimal valid PDS4 XML label + companion binary; a 64×64 synthetic GeoTIFF via `rasterio` with a georeferenced transform.
- `pytest tests/test_ingestion.py -v` must assert:
  - `load_image(pds3_fixture)` returns `image_shape == (64,64)` and `archive_standard == "PDS3"`.
  - `load_image(pds4_fixture)` returns `archive_standard == "PDS4"` and a populated `sun_azimuth_deg`.
  - `load_image(geotiff_fixture)` returns `archive_standard == "GEOTIFF"`.
  - Passing a label with `SUB_SOLAR_AZIMUTH = 400` raises `ValueError`.
  - Passing a path with no companion label raises `FileNotFoundError`.
- All four tests must pass with zero warnings before this session is marked done.

**Handoff Artifacts & Definition of Done:**
- `src/common/schema.py` exporting the frozen `ImageMetadata` dataclass — this is the contract every later session imports.
- `src/ingestion/loader.py` exposing `load_image()` as the single public ingestion API.
- `tests/fixtures/` populated and committed (used by every later session's tests as ground-truth inputs).
- `configs/ingestion.yaml` committed.
- All ingestion tests green. Definition of done: any of the three fixture files can be round-tripped through `load_image()` and produce a schema-valid `ImageMetadata` instance with no `None` in required fields.

---

## Part 2: Photometric Correction & Illumination Normalization Pipeline

**Session Objective & Scope:**
Consume the `(np.ndarray, ImageMetadata)` pairs from Session 1 and produce illumination-normalized, denoised images. This session does NOT resize, build pyramids, or touch feature detection — output resolution and array shape must equal input.

**Input Prerequisites:**
- `src/common/schema.py::ImageMetadata` (Part 1).
- `src/ingestion/loader.py::load_image` (Part 1).
- `tests/fixtures/*` (Part 1).

**File Structure to Create/Modify:**
```
src/preprocessing/__init__.py
src/preprocessing/denoise.py
src/preprocessing/clahe.py
src/preprocessing/shadow_normalize.py
src/preprocessing/photometric.py
src/preprocessing/pipeline.py
configs/preprocessing.yaml
tests/test_preprocessing.py
```

**Step-by-Step Implementation Tasks:**
1. `src/preprocessing/denoise.py`: implement `denoise(img: np.ndarray, method: Literal["nlm","bilateral","median"]="nlm") -> np.ndarray` wrapping `cv2.fastNlMeansDenoising`, `cv2.bilateralFilter`, and `cv2.medianBlur` behind one signature. Convert to `float32` internally, preserve input dtype on return.
2. `src/preprocessing/clahe.py`: implement `apply_clahe(img: np.ndarray, clip_limit: float=2.0, tile_grid_size: Tuple[int,int]=(8,8)) -> np.ndarray` using `cv2.createCLAHE`. Name and document this correctly as **Contrast Limited Adaptive Histogram Equalization** — the "Adaptive" refers to the per-tile local equalization, which is the reason CLAHE avoids the noise amplification of global histogram equalization on flat lunar mare regions. Handle 16-bit input by rescaling to 8-bit for the CLAHE call, then rescaling back (`cv2.createCLAHE` requires 8-bit).
3. `src/preprocessing/shadow_normalize.py`: implement `shadow_aware_normalize(img: np.ndarray, shadow_thresh_percentile: float=5.0) -> np.ndarray`. Detect shadow regions as pixels below the given low percentile of the illuminated-region intensity distribution (not a fixed absolute threshold — lunar albedo varies mare-to-highland), apply local gamma correction only inside detected shadow masks, and blend at mask edges with a Gaussian-feathered alpha to avoid hard seams.
4. `src/preprocessing/photometric.py`: implement `photometric_correct(img: np.ndarray, meta: ImageMetadata) -> np.ndarray` using a Lunar-Lambert (Minnaert-style) reflectance model driven by `meta.sun_elevation_deg`. If `sun_elevation_deg is None`, log a warning and skip photometric correction (return input unchanged) rather than guessing a sun angle.
5. `src/preprocessing/pipeline.py`: implement `PreprocessingPipeline` class with a `.run(img, meta) -> np.ndarray` method that chains denoise → photometric_correct → shadow_aware_normalize → apply_clahe, with each stage individually toggleable via `configs/preprocessing.yaml`.
6. Edge cases: all-zero image (return unchanged, log warning, do not divide by zero in normalization steps); saturated (all-max-value) image; image with `NaN`/`Inf` from a bad GeoTIFF nodata fill (mask and interpolate before any processing).

**Verification & Unit Tests:**
- `pytest tests/test_preprocessing.py -v` must assert:
  - Output shape and dtype match input for every stage individually and for the full pipeline.
  - `apply_clahe` on a synthetic low-contrast gradient image increases the image's global standard deviation by at least 20%.
  - `photometric_correct` with `sun_elevation_deg=None` returns an array identical (via `np.array_equal`) to the input.
  - `shadow_aware_normalize` on an all-zero image returns an all-zero image without raising.
  - Full pipeline run on the Part-1 PDS3 and PDS4 fixtures completes without exception and without any `NaN` in the output (`np.isnan(out).sum() == 0`).

**Handoff Artifacts & Definition of Done:**
- `src/preprocessing/pipeline.py::PreprocessingPipeline` as the public API — Session 3 imports this directly.
- `configs/preprocessing.yaml` with per-stage on/off flags and default parameters.
- All preprocessing tests green, zero NaNs on both archive-format fixtures. Definition of done: a normalized image can be passed straight into `PreprocessingPipeline().run()` regardless of whether it came from the PDS3 or PDS4 ingestion path with no format-specific branching required by the caller.

---

## Part 3: Multi-Scale Image Pyramid & Resolution Normalizer

**Session Objective & Scope:**
Build Gaussian/Laplacian pyramids for a preprocessed image pair and estimate the scale ratio between them so that comparable pyramid levels can be selected before feature detection. This session does NOT detect or match features — its output is a set of pyramid levels plus a recommended level pairing.

**Input Prerequisites:**
- `ImageMetadata.pixel_scale_m` (Part 1) — primary source of scale-ratio estimation.
- `src/preprocessing/pipeline.py::PreprocessingPipeline` output (Part 2) as the pyramid's base-level input.

**File Structure to Create/Modify:**
```
src/pyramid/__init__.py
src/pyramid/builder.py
src/pyramid/scale_estimator.py
configs/pyramid.yaml
tests/test_pyramid.py
```

**Step-by-Step Implementation Tasks:**
1. `src/pyramid/builder.py`: implement `build_gaussian_pyramid(img: np.ndarray, levels: int) -> List[np.ndarray]` via repeated `cv2.pyrDown`, and `build_laplacian_pyramid(gaussian_pyramid: List[np.ndarray]) -> List[np.ndarray]` as the standard difference-of-upsampled-Gaussian construction. Guard against `levels` that would reduce the image below 16×16 px — clamp `levels` automatically and log the clamp.
2. `src/pyramid/scale_estimator.py`: implement `estimate_scale_ratio(meta_a: ImageMetadata, meta_b: ImageMetadata) -> float` returning `meta_b.pixel_scale_m / meta_a.pixel_scale_m` when both are populated (e.g., TMC-2 at 5 m vs OHRC at 0.28 m gives a ratio of ~17.9×). When either `pixel_scale_m` is missing or the label-derived value looks implausible (`<0.01` or `>1000`), fall back to `estimate_scale_ratio_by_phase_correlation(img_a, img_b) -> float` using `cv2.phaseCorrelate` across a small set of resized candidate scales — this is the fallback path, metadata is always tried first.
3. Implement `select_pyramid_levels(ratio: float, max_levels: int) -> Tuple[int,int]` that returns the `(level_a, level_b)` pair whose effective resolutions are closest to equal, using `log2(ratio)` to pick the level offset, clamped to `[0, max_levels-1]`.
4. Edge cases: `ratio` very close to 1.0 (same-sensor pair) → should return `(0,0)`; `ratio` larger than `2**max_levels` → should return the maximum offset available and log a warning that full scale compensation isn't possible within pyramid depth, since matching will need to rely more heavily on the deep fallback in Session 6/7.

**Verification & Unit Tests:**
- `pytest tests/test_pyramid.py -v` must assert:
  - `build_gaussian_pyramid` on a 512×512 image with `levels=4` returns arrays of shape `512,256,128,64` (square case) in sequence.
  - `estimate_scale_ratio` between synthetic metadata with `pixel_scale_m=5.0` and `pixel_scale_m=0.25` returns `20.0` within 1e-6 tolerance.
  - `estimate_scale_ratio` with one `pixel_scale_m=None` falls through to the phase-correlation path without raising.
  - `select_pyramid_levels(ratio=20.0, max_levels=6)` returns a tuple where `abs(level_a - level_b) == round(log2(20.0))`.

**Handoff Artifacts & Definition of Done:**
- `src/pyramid/builder.py` and `src/pyramid/scale_estimator.py` public APIs.
- `configs/pyramid.yaml` (default `max_levels`, phase-correlation candidate scale list).
- Definition of done: given any two Part-1/Part-2 outputs, `select_pyramid_levels(estimate_scale_ratio(meta_a, meta_b), max_levels)` returns a valid level pair consumed directly by Session 4 without any manual scale bookkeeping by the caller.

---

## Part 4: Classical Feature Detection & Descriptor Extraction

**Session Objective & Scope:**
Provide a single, swappable interface over SIFT/ORB/AKAZE that Session 5 (matching) and Session 7 (routing) call identically regardless of which detector is active. This session does NOT do matching, RANSAC, or warping.

**Input Prerequisites:**
- Preprocessed, pyramid-leveled image arrays from Parts 2–3 (this session is detector-agnostic to how the image got here — it just needs a `np.ndarray`).

**File Structure to Create/Modify:**
```
src/features/__init__.py
src/features/base.py
src/features/sift_detector.py
src/features/orb_detector.py
src/features/akaze_detector.py
src/features/factory.py
configs/features.yaml
tests/test_features.py
```

**Step-by-Step Implementation Tasks:**
1. `src/features/base.py`: define `FeatureResult` dataclass with `keypoints: np.ndarray` (Nx2 float32, x,y), `descriptors: np.ndarray` (NxD), `responses: np.ndarray` (N,), `detector_name: str`. Define abstract `BaseDetector` with `.detect_and_compute(img: np.ndarray) -> FeatureResult`.
2. `src/features/sift_detector.py`, `orb_detector.py`, `akaze_detector.py`: each implements `BaseDetector` wrapping `cv2.SIFT_create`, `cv2.ORB_create`, `cv2.AKAZE_create` respectively. Every constructor accepts a `**params` dict validated against a per-detector allow-list (reject unknown kwargs with `ValueError` naming the bad key — don't silently swallow typos in tuning params).
3. `src/features/factory.py`: implement `get_detector(name: Literal["sift","orb","akaze"], **params) -> BaseDetector` as the single construction entry point used everywhere else in the codebase — no other module should import a concrete detector class directly.
4. Edge cases: zero keypoints found (return `FeatureResult` with empty arrays, not `None`, so downstream code doesn't need null-checks); image smaller than the detector's minimum patch size (raise `ImageTooSmallError` with the offending shape); non-uint8 input to ORB/AKAZE (auto-convert with a logged warning, since OpenCV's binary descriptors expect 8-bit).

**Verification & Unit Tests:**
- `pytest tests/test_features.py -v` must assert:
  - Each of the three detectors returns `len(keypoints) > 0` on a textured synthetic checkerboard fixture and `len(keypoints) == 0` (not an exception) on a flat all-gray image.
  - `descriptors.shape[0] == keypoints.shape[0]` for all three detectors.
  - `get_detector("sift", nfeatures=500).detect_and_compute(img)` returns at most 500 keypoints.
  - `get_detector("orb", bogus_param=1)` raises `ValueError`.

**Handoff Artifacts & Definition of Done:**
- `src/features/factory.py::get_detector` as the public API.
- `configs/features.yaml` with default parameter sets per detector, including one "fast/low-quality" and one "thorough/high-quality" named preset for the routing engine to choose between.
- Definition of done: swapping `detector: sift` → `detector: akaze` in `configs/features.yaml` changes zero calling code in Session 5.

---

## Part 5: Classical Feature Matching & Geometric Transform Estimation

**Session Objective & Scope:**
Take two `FeatureResult` objects and produce a validated geometric transform plus the warped source image. This session does NOT decide whether to use classical vs. deep matching — that's Session 7's job; this session assumes it's already been told to run classically.

**Input Prerequisites:**
- `src/features/base.py::FeatureResult` (Part 4).
- Preprocessed reference/source images (Parts 2–3) for the final warp step.

**File Structure to Create/Modify:**
```
src/matching/__init__.py
src/matching/classical_matcher.py
src/matching/transform_estimator.py
src/matching/warp.py
configs/matching.yaml
tests/test_classical_matching.py
```

**Step-by-Step Implementation Tasks:**
1. `src/matching/classical_matcher.py`: implement `match_features(fr_a: FeatureResult, fr_b: FeatureResult, method: Literal["flann","bruteforce"]="flann", ratio_thresh: float=0.75) -> np.ndarray` (Mx2 int array of index pairs). For FLANN with binary descriptors (ORB/AKAZE-MLDB), use `FLANN_INDEX_LSH` params, not the KD-tree params meant for float descriptors (SIFT) — branch on `descriptors.dtype`. Apply Lowe's ratio test via `knnMatch(k=2)` and the `ratio_thresh` cutoff.
2. `src/matching/transform_estimator.py`: implement `estimate_transform(pts_a: np.ndarray, pts_b: np.ndarray, model: Literal["homography","affine","tps"]="homography", method: int=cv2.USAC_MAGSAC, ransac_thresh: float=3.0) -> Tuple[np.ndarray, np.ndarray]` returning `(transform_matrix_or_tps_object, inlier_mask)`. Use `cv2.findHomography`/`cv2.estimateAffinePartial2D` with the MAGSAC++ flag for the first two; implement TPS via `cv2.createThinPlateSplineShapeTransformer` for the non-rigid case. Require a minimum of 4 point correspondences for homography/affine and 3 for TPS's minimum set — raise `InsufficientCorrespondencesError` below threshold rather than letting OpenCV fail cryptically.
3. `src/matching/warp.py`: implement `warp_source(src_img: np.ndarray, transform: np.ndarray, model: str, output_shape: Tuple[int,int]) -> np.ndarray` dispatching to `cv2.warpPerspective`/`cv2.warpAffine`/TPS's `.warpImage`.
4. Edge cases: degenerate correspondences (all points collinear — MAGSAC++ will reject internally, but wrap the OpenCV call in a check for `transform is None` and raise `TransformEstimationFailedError` with the inlier count for diagnostics); fewer than 4 raw matches before RANSAC even runs.

**Verification & Unit Tests:**
- `pytest tests/test_classical_matching.py -v` must assert:
  - On a synthetic pair (reference image + a known-homography-warped copy), `match_features` + `estimate_transform` recovers a homography within `1e-2` Frobenius-normalized error of the ground truth.
  - Inlier ratio on this synthetic pair is `>= 0.8`.
  - `estimate_transform` with only 3 correspondences and `model="homography"` raises `InsufficientCorrespondencesError`.
  - `warp_source` output shape exactly equals the requested `output_shape`.

**Handoff Artifacts & Definition of Done:**
- `src/matching/classical_matcher.py`, `transform_estimator.py`, `warp.py` public APIs.
- `configs/matching.yaml` (ratio threshold, RANSAC threshold, default model per scene-planarity heuristic).
- Definition of done: given two `FeatureResult` objects and their source images, the full classical path produces a warped image and an inlier mask with zero manual tuning required for the synthetic ground-truth test case.

---

## Part 6: Deep Feature Matching Fallback Integration

**Session Objective & Scope:**
Provide a deep-learning matching path (SuperPoint, LoFTR, LightGlue via Kornia) with the same external contract as Session 5's classical path, so Session 7 can call either interchangeably. Does not implement the routing decision itself.

**Input Prerequisites:**
- Preprocessed image pairs (Parts 2–3).
- The `(transform_matrix, inlier_mask)` output contract established in Part 5 — this session must match it exactly.

**File Structure to Create/Modify:**
```
src/deep_matching/__init__.py
src/deep_matching/superpoint_wrapper.py
src/deep_matching/loftr_wrapper.py
src/deep_matching/lightglue_wrapper.py
src/deep_matching/device_manager.py
configs/deep_matching.yaml
tests/test_deep_matching.py
```

**Step-by-Step Implementation Tasks:**
1. `src/deep_matching/device_manager.py`: implement `get_device(prefer_gpu: bool=True) -> torch.device` returning `cuda` if available and requested, else `cpu`, with a single log line stating which was chosen — every wrapper below must call this rather than hard-coding a device.
2. `src/deep_matching/superpoint_wrapper.py`: implement `SuperPointExtractor` using `kornia.feature.SuperPoint` (or the Kornia `LightGlueMatcher`'s bundled SuperPoint extractor) with a `.detect_and_compute(img: np.ndarray) -> FeatureResult` method — reuse the exact `FeatureResult` schema from Part 4 so downstream evaluation code doesn't branch on classical-vs-deep.
3. `src/deep_matching/loftr_wrapper.py`: implement `LoFTRMatcher` using `kornia.feature.LoFTR(pretrained="outdoor")` with a `.match(img_a: np.ndarray, img_b: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]` returning `(pts_a, pts_b, confidence)` — LoFTR is detector-free and matches directly, so it does not go through the `FeatureResult`/matcher split the classical path uses; document this difference clearly in the module docstring so Session 7 doesn't assume a uniform internal shape.
4. `src/deep_matching/lightglue_wrapper.py`: implement `LightGlueMatcher` pairing Kornia's SuperPoint extractor output with `kornia.feature.LightGlue` for matching, returning the same `(pts_a, pts_b, confidence)` shape as the LoFTR wrapper for interface consistency between the two deep matchers.
5. All three wrappers must accept an explicit `device: torch.device` argument (from `device_manager.get_device`) — no wrapper should silently move tensors to a device the caller didn't request, since the CPU-only judging-environment fallback (documented in the roadmap's risk table) depends on this being controllable.
6. Edge cases: model weights not present on disk / no network access at runtime — catch the download/load exception and raise a single `ModelWeightsUnavailableError` with instructions, rather than letting a raw `urllib` or `torch.hub` traceback surface; out-of-memory on GPU — catch `torch.cuda.OutOfMemoryError`, clear cache, and retry once on CPU with a logged warning.

**Verification & Unit Tests:**
- `pytest tests/test_deep_matching.py -v` must assert (mark GPU-only assertions with `@pytest.mark.skipif(not torch.cuda.is_available())`):
  - `get_device(prefer_gpu=False)` always returns `cpu`.
  - `SuperPointExtractor().detect_and_compute(img)` returns a `FeatureResult` with `keypoints.shape[1] == 2`.
  - `LoFTRMatcher().match(img_a, img_b)` on an identical image pair (`img_a is img_b`) returns a confidence array whose mean exceeds `0.5`.
  - `LightGlueMatcher` runs end-to-end on CPU without raising (perf is not asserted, only correctness/no-crash).

**Handoff Artifacts & Definition of Done:**
- `src/deep_matching/*_wrapper.py` public APIs and `device_manager.get_device`.
- `configs/deep_matching.yaml` (model variant, confidence threshold, GPU/CPU default).
- Definition of done: on a machine with no GPU, every wrapper still runs to completion on CPU and produces schema-valid output — this is the explicit CPU-fallback demo path required by the roadmap's risk mitigation table.

---

## Part 7: Difficulty-Aware Dynamic Routing Engine & Feedback Loops

**Session Objective & Scope:**
Own the decision of classical-vs-deep per pair, plus retry/escalation on failure. This session imports Parts 4–6 as black boxes and does not modify their internals.

**Input Prerequisites:**
- `src/matching/*` (Part 5) and `src/deep_matching/*` (Part 6) — both matching paths must already exist and expose compatible enough outputs (transform + inlier info) for a common `RegistrationResult`.
- `src/pyramid/*` (Part 3) for the multi-resolution escalation loop.

**File Structure to Create/Modify:**
```
src/routing/__init__.py
src/routing/difficulty_estimator.py
src/routing/router.py
src/routing/retry_loop.py
configs/routing.yaml
tests/test_routing.py
```

**Step-by-Step Implementation Tasks:**
1. `src/routing/difficulty_estimator.py`: implement `estimate_difficulty(img_a: np.ndarray, img_b: np.ndarray, meta_a: ImageMetadata, meta_b: ImageMetadata) -> float` (0=trivial, 1=hardest) as a weighted combination of: (a) low-texture score via normalized Laplacian variance, (b) illumination-gap score via `abs(meta_a.sun_elevation_deg - meta_b.sun_elevation_deg)` when both present, (c) scale-ratio extremity from `scale_estimator.estimate_scale_ratio`. Weights live in `configs/routing.yaml` as named, commented constants — not hard-coded in the function body — so they can be recalibrated without a code change.
2. `src/routing/router.py`: implement `route_and_register(img_a, img_b, meta_a, meta_b, config) -> RegistrationResult` where `RegistrationResult` bundles the transform, inlier ratio, matcher used, and difficulty score. Logic: if `estimate_difficulty(...) < config.difficulty_threshold`, attempt Part 5's classical path first; else go straight to Part 6. `config.difficulty_threshold` defaults to a value documented in `configs/routing.yaml` as an **assumption to be tuned against real data, not an empirical constant** — the comment must say this explicitly, since no labeled difficulty ground truth exists yet.
3. `src/routing/retry_loop.py`: implement `register_with_retry(img_a, img_b, meta_a, meta_b, config, max_retries: int=2) -> RegistrationResult`. On classical-path failure (inlier ratio below `config.min_inlier_ratio` or `TransformEstimationFailedError`), escalate to deep matching. On deep-path failure or low confidence, escalate to the next coarser pyramid level from Part 3 and retry once more. After `max_retries` exhausted, return a `RegistrationResult` with `success=False` and the best partial result found — never raise out of this function; callers (Session 9's API) need a always-returns contract.
4. Edge cases: both classical and deep paths fail at every pyramid level (return `success=False`, do not crash the service); `difficulty_threshold` misconfigured outside `[0,1]` (validate and raise at config-load time, not mid-registration).

**Verification & Unit Tests:**
- `pytest tests/test_routing.py -v` must assert:
  - `estimate_difficulty` on an identical image pair with identical metadata returns a low score (`< 0.3`).
  - `estimate_difficulty` on a pair with a synthetic 60° sun-angle gap returns a higher score than a pair with a 5° gap, all else equal.
  - `route_and_register` on the Part-5 synthetic ground-truth pair uses the classical path (assert `result.matcher_used == "classical"`) and succeeds.
  - `register_with_retry` on a deliberately pathological pair (near-zero texture, injected in the test) exhausts retries and returns `success=False` without raising.

**Handoff Artifacts & Definition of Done:**
- `src/routing/router.py::route_and_register` and `retry_loop.py::register_with_retry` as the single public entry points Session 9's API calls.
- `configs/routing.yaml` with all thresholds/weights named and comment-documented as tunable assumptions.
- Definition of done: Session 9 needs to import exactly one function (`register_with_retry`) to perform a full, failure-tolerant registration — everything upstream is hidden behind it.

---

## Part 8: Rigorous Quantitative Evaluation Suite & Confidence Scoring

**Session Objective & Scope:**
Given a `RegistrationResult` (Part 7) and the original image pair, compute the metrics suite and a single composite confidence score. Does not re-run registration or alter the transform.

**Input Prerequisites:**
- `src/routing/router.py::RegistrationResult` (Part 7).
- Warp function from `src/matching/warp.py` (Part 5) for producing the warped/aligned image needed by the metrics.

**File Structure to Create/Modify:**
```
src/evaluation/__init__.py
src/evaluation/metrics.py
src/evaluation/self_consistency.py
src/evaluation/confidence.py
configs/evaluation.yaml
tests/test_evaluation.py
```

**Step-by-Step Implementation Tasks:**
1. `src/evaluation/metrics.py`: implement `compute_ssim(ref: np.ndarray, warped: np.ndarray) -> float` via `skimage.metrics.structural_similarity` (restrict to the overlapping valid-pixel region only — mask out the warp's black border, since SSIM over padded zeros is meaningless); `compute_mutual_information(ref, warped) -> float` via a joint-histogram entropy calculation (`np.histogram2d` + Shannon entropy formula); `compute_inlier_ratio(result: RegistrationResult) -> float` as a direct passthrough of the value already computed in Part 5/6/7; `compute_corner_reprojection_error(transform, model, image_shape, ground_truth_corners=None) -> Optional[float]` — return `None` (not zero, not NaN) when no ground-truth control points exist, since a fabricated zero would misleadingly suggest perfect geometric accuracy.
2. `src/evaluation/self_consistency.py`: implement `forward_backward_rmse(img_a, img_b, meta_a, meta_b, config) -> float` by registering A→B, then independently registering B→A, composing the two transforms, and measuring the RMS pixel displacement of a regular grid of test points under the composed (should-be-identity) transform. This is the RMSE proxy used when no ground-truth control points are available (per the roadmap's risk mitigation).
3. `src/evaluation/confidence.py`: implement `composite_confidence(metrics: Dict[str, Optional[float]], weights: Dict[str,float]) -> float` producing a 0–100 score as a weighted sum of the normalized metrics that are actually available (renormalize weights over present metrics when `corner_reprojection_error is None`, rather than treating the missing metric as zero). Weights are loaded from `configs/evaluation.yaml`, documented in that file as **configurable, not empirically derived** — the docstring must state this so nobody presents the composite score as more rigorously calibrated than it is.
4. Edge cases: `ref`/`warped` of mismatched shape (raise `ValueError` naming both shapes); fully black warped region (SSIM/MI both degenerate — detect this case, return a confidence of `0.0` with a `reason="no_overlap"` field rather than a misleading numeric artifact from the underlying library).

**Verification & Unit Tests:**
- `pytest tests/test_evaluation.py -v` must assert:
  - `compute_ssim(img, img)` (identical images) returns `>= 0.99`.
  - `compute_mutual_information(img, img)` returns a value strictly greater than `compute_mutual_information(img, np.random.randint(0,255,img.shape))`.
  - `forward_backward_rmse` on a synthetic pair with a known, invertible homography returns `< 1.0` px.
  - `composite_confidence` with `corner_reprojection_error=None` still returns a value in `[0,100]` and doesn't raise a `KeyError`/`ZeroDivisionError`.
  - Mismatched-shape inputs to `compute_ssim` raise `ValueError`.

**Handoff Artifacts & Definition of Done:**
- `src/evaluation/confidence.py::composite_confidence` as the function Session 9's API calls to build its JSON report.
- `configs/evaluation.yaml` with named, documented weights.
- Definition of done: every `RegistrationResult` (success or failure) can be passed through this suite and produce a fully-populated, JSON-serializable metrics dict plus a 0–100 score, with `None` used explicitly for any metric that couldn't be computed — never a fabricated placeholder number.

---

## Part 9: FastAPI Backend Service & Inference Endpoints

**Session Objective & Scope:**
Expose Parts 1–8 as a REST API. Does not implement any new CV logic — pure orchestration and serialization.

**Input Prerequisites:**
- `src/ingestion/loader.py::load_image` (Part 1).
- `src/preprocessing/pipeline.py::PreprocessingPipeline` (Part 2).
- `src/routing/retry_loop.py::register_with_retry` (Part 7).
- `src/evaluation/confidence.py::composite_confidence` (Part 8).

**File Structure to Create/Modify:**
```
src/api/__init__.py
src/api/main.py
src/api/schemas.py
src/api/routes/upload.py
src/api/routes/register.py
src/api/routes/report.py
src/api/background.py
tests/test_api.py
```

**Step-by-Step Implementation Tasks:**
1. `src/api/schemas.py`: define Pydantic models mirroring `ImageMetadata` (Part 1) and the evaluation output dict (Part 8) — do not redefine the fields independently; import and wrap the dataclasses/dicts to avoid schema drift between the CV core and the API contract.
2. `src/api/routes/upload.py`: `POST /images/upload` accepts a multipart file, calls `load_image` after writing to a temp path, stores the resulting `(array, metadata)` in an in-memory or Redis-backed session store keyed by a generated `image_id`, and returns the `image_id` plus serialized metadata.
3. `src/api/routes/register.py`: `POST /register` accepts `{source_image_id, reference_image_id, params}`, runs `PreprocessingPipeline` on both, calls `register_with_retry`, and — because this can be slow (deep fallback) — dispatches to a background task (`src/api/background.py`, FastAPI `BackgroundTasks` or a Celery/RQ queue) returning a `job_id` immediately with `202 Accepted`. Provide `GET /register/{job_id}` for polling status/result.
4. `src/api/routes/report.py`: `GET /report/{job_id}` returns the full JSON evaluation report (Part 8 output) once the job is complete; `GET /report/{job_id}/overlay` streams a PNG blend/overlay image generated on demand from the stored transform.
5. Edge cases: unknown `image_id`/`job_id` → `404` with a structured error body, not a stack trace; upload of a file type `load_image` can't dispatch → `422` surfacing the `UnsupportedFormatError` message; registration job still running when `/report/{job_id}` is polled → `202` with `{status: "pending"}`, not a `404` or an empty `200`.
6. Add a `configs/api.yaml`-driven CORS policy scoped to the frontend's dev/prod origins for Session 10.

**Verification & Unit Tests:**
- `pytest tests/test_api.py -v` using FastAPI's `TestClient` must assert:
  - Uploading the Part-1 PDS4 fixture returns `200` and a valid `image_id`.
  - `POST /register` with two valid `image_id`s returns `202` and a `job_id`.
  - Polling `/register/{job_id}` eventually (test polls in a loop with a timeout) reaches `status == "done"`.
  - `/report/{job_id}` for a completed job returns a body containing all metric keys from Part 8's schema.
  - `/register` with a bogus `image_id` returns `404`.

**Handoff Artifacts & Definition of Done:**
- Running `uvicorn src.api.main:app` serves all documented endpoints, visible at `/docs` (FastAPI's auto-generated OpenAPI UI).
- `openapi.json` exported and committed to `src/api/openapi.json` (via `TestClient(app).get("/openapi.json")`) — this is the exact contract Session 10's frontend codes against.
- Definition of done: a full upload → register → poll → report round trip succeeds against the Part-5 synthetic ground-truth pair via the API alone (no direct Python imports from the test), proving the service layer is fully decoupled from the CV core's internals.

---

## Part 10: Frontend Interactive Dashboard & Docker Containerization

**Session Objective & Scope:**
Build the user-facing dashboard against Session 9's committed `openapi.json` contract, and package the whole system for reproducible deployment. Does not modify any backend route behavior — if the frontend needs something the API doesn't provide, that's flagged as a gap for a future session, not silently patched here.

**Input Prerequisites:**
- `src/api/openapi.json` (Part 9) — the frontend's API client is generated/hand-written against this exact contract.
- A running `src/api/main.py` service (Part 9) for local integration testing.

**File Structure to Create/Modify:**
```
frontend/src/App.jsx
frontend/src/components/DualImageViewer.jsx
frontend/src/components/MatchOverlay.jsx
frontend/src/components/BlendSlider.jsx
frontend/src/components/ReportPanel.jsx
frontend/src/api/client.js
frontend/package.json
docker/backend.Dockerfile
docker/frontend.Dockerfile
docker-compose.yml
tests/test_e2e_smoke.py
```

**Step-by-Step Implementation Tasks:**
1. `frontend/src/api/client.js`: thin fetch wrapper with one function per Part-9 endpoint (`uploadImage`, `startRegistration`, `pollRegistration`, `getReport`, `getOverlay`), all base-URLed via an env var (`VITE_API_BASE_URL` or equivalent) so the same build works against local Docker Compose or a deployed backend.
2. `DualImageViewer.jsx`: side-by-side (or Leaflet/Deck.gl synced-pan) view of reference and source images, using Leaflet's simple-CRS image overlay mode for non-georeferenced product views and its standard tile/geo mode when `ImageMetadata` carries real georeferencing.
3. `MatchOverlay.jsx`: renders detected keypoint correspondences as connecting lines between the two panes, toggleable by matcher type (classical/deep) using the `matcher_used` field from the report.
4. `BlendSlider.jsx`: alpha-blend slider between the reference image and the warped source (fetched from `/report/{job_id}/overlay`), for visual QA of alignment quality.
5. `ReportPanel.jsx`: renders the full metrics JSON (SSIM, MI, inlier ratio, RMSE, composite confidence) from Part 8/9, with the composite score's weights disclosed in a tooltip (surfacing the "configurable, not empirically fixed" note from Part 8, so end users aren't misled about its precision).
6. `docker/backend.Dockerfile`: multi-stage build — install GDAL system deps (`libgdal-dev`) before `pip install`, since `rasterio`/`GDAL` wheels can fail without them; final stage runs `uvicorn` with a non-root user.
7. `docker/frontend.Dockerfile`: standard Node build stage → static Nginx serve stage.
8. `docker-compose.yml`: services `backend` (with an optional `runtime: nvidia` / `deploy.resources.reservations.devices` block for GPU, commented as opt-in since the CPU-only fallback is the default demo path per the roadmap's risk table), `frontend`, and — if a queue was used in Part 9 — `redis`/`worker`. Wire `VITE_API_BASE_URL` to the `backend` service name for inter-container networking.
9. Edge cases: backend not yet ready when the frontend container starts (add a `depends_on` + basic retry/backoff in `client.js` rather than a hard `condition: service_healthy` dependency that could deadlock on cold GPU model loads); overlay image not yet generated when `BlendSlider` mounts (show a loading state, don't request `/overlay` until `status == "done"`).

**Verification & Unit Tests:**
- `docker compose up --build` must bring up both services with no crash-loop (`docker compose ps` shows both `Up`).
- `tests/test_e2e_smoke.py` (run against the Compose stack, e.g. with `playwright` or a plain `requests`-based smoke test hitting both the frontend's served `index.html` and the backend's `/docs`) asserts both return `200`.
- Manual/frontend unit tests (`npm test` if a test runner is configured) assert `client.js`'s functions construct the correct request paths/methods for each Part-9 endpoint.
- Confirm the dashboard end-to-end: upload two of the Part-1 fixture-derived sample images through the UI, trigger registration, and visually confirm the overlay/report panel populate — this manual check is required before sign-off since UI correctness isn't fully capturable by the automated smoke test alone.

**Handoff Artifacts & Definition of Done:**
- `docker-compose.yml` bringing up the full stack with one command.
- Frontend build artifacts served correctly against the committed `openapi.json` contract with no manual endpoint patching.
- Definition of done: a fresh clone of the repo, given `docker compose up --build`, produces a working dashboard reachable in a browser that can upload a Chandrayaan-2/LRO image pair, run registration, and display the confidence report — this is the final, demoable state of the project.
