import React, { useState, useRef, useCallback } from 'react';

const styles = {
  container: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
    gap: '24px',
    animation: 'fadeInUp 0.6s ease-out 0.3s both',
  },
  dropzone: (isDragging, hasImage) => ({
    position: 'relative',
    padding: hasImage ? '16px' : '40px 24px',
    borderRadius: 'var(--radius)',
    border: `2px dashed ${isDragging ? 'var(--accent)' : hasImage ? 'var(--success)' : 'var(--glass-border)'}`,
    background: isDragging
      ? 'rgba(18, 19, 88, 0.08)'
      : hasImage
      ? 'rgba(34, 197, 94, 0.04)'
      : 'var(--glass)',
    backdropFilter: 'blur(8px)',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    overflow: 'hidden',
  }),
  uploadIcon: {
    fontSize: '40px',
    marginBottom: '12px',
    opacity: 0.6,
  },
  label: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    marginBottom: '4px',
  },
  sublabel: {
    fontSize: '13px',
    color: 'var(--text-muted)',
    marginBottom: '16px',
  },
  formats: {
    display: 'flex',
    gap: '6px',
    justifyContent: 'center',
    flexWrap: 'wrap',
    marginBottom: hasImage => hasImage ? '12px' : '0',
  },
  formatBadge: {
    padding: '3px 8px',
    borderRadius: '4px',
    background: 'rgba(18, 19, 88, 0.1)',
    border: '1px solid rgba(18, 19, 88, 0.2)',
    fontSize: '10px',
    fontWeight: 600,
    color: 'var(--accent-light)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  preview: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    textAlign: 'left',
  },
  thumbnail: {
    width: '100px',
    height: '80px',
    borderRadius: '8px',
    objectFit: 'cover',
    border: '2px solid var(--glass-border)',
    flexShrink: 0,
  },
  fileInfo: {
    flex: 1,
    minWidth: 0,
  },
  fileName: {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    marginBottom: '4px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  fileSize: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    marginBottom: '8px',
  },
  metadata: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  metaTag: {
    padding: '2px 8px',
    borderRadius: '4px',
    background: 'rgba(18, 19, 88, 0.1)',
    border: '1px solid rgba(18, 19, 88, 0.2)',
    fontSize: '11px',
    color: 'var(--purple)',
  },
  removeBtn: {
    position: 'absolute',
    top: '8px',
    right: '8px',
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    border: 'none',
    background: 'rgba(239, 68, 68, 0.8)',
    color: 'white',
    fontSize: '14px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
  },
  hiddenInput: {
    display: 'none',
  },
};

function UploadZone({ type, image, metadata, onUpload, onRemove }) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onUpload(file, type);
  }, [onUpload, type]);

  const handleClick = () => inputRef.current?.click();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) onUpload(file, type);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div
      style={styles.dropzone(isDragging, !!image)}
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={!image ? handleClick : undefined}
    >
      {image && (
        <button
          style={styles.removeBtn}
          onClick={(e) => {
            e.stopPropagation();
            onRemove(type);
          }}
        >
          ×
        </button>
      )}

      <input
        ref={inputRef}
        type="file"
        accept=".tif,.tiff,.img,.xml,.lbl,.dat,.raw,.bin"
        style={styles.hiddenInput}
        onChange={handleFileChange}
      />

      {image ? (
        <div style={styles.preview}>
          <img src={image} alt={type} style={styles.thumbnail} />
          <div style={styles.fileInfo}>
            <div style={styles.fileName}>{type === 'source' ? 'Source Image' : 'Reference Image'}</div>
            {metadata && (
              <div style={styles.metadata}>
                {metadata.sensor && <span style={styles.metaTag}>{metadata.sensor}</span>}
                {metadata.archive_standard && <span style={styles.metaTag}>{metadata.archive_standard}</span>}
                {metadata.pixel_scale_m && <span style={styles.metaTag}>{metadata.pixel_scale_m} m/px</span>}
              </div>
            )}
          </div>
        </div>
      ) : (
        <>
          <div style={styles.uploadIcon}>{type === 'source' ? '🛰' : '🗺'}</div>
          <div style={styles.label}>
            {type === 'source' ? 'Source Image' : 'Reference Image'}
          </div>
          <div style={styles.sublabel}>
            Drag and drop or click to browse
          </div>
          <div style={styles.formats}>
            {['.tif', '.img', '.xml', '.lbl'].map((f) => (
              <span key={f} style={styles.formatBadge}>{f}</span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default function ImageUploader({ sourceImage, referenceImage, sourceMetadata, referenceMetadata, onUpload, onRemove }) {
  return (
    <div style={styles.container}>
      <UploadZone
        type="source"
        image={sourceImage}
        metadata={sourceMetadata}
        onUpload={onUpload}
        onRemove={onRemove}
      />
      <UploadZone
        type="reference"
        image={referenceImage}
        metadata={referenceMetadata}
        onUpload={onUpload}
        onRemove={onRemove}
      />
    </div>
  );
}
