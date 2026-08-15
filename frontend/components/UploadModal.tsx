'use client';
// frontend/components/UploadModal.tsx
// Drag-and-drop PDF upload modal

import { useRef, useState } from 'react';
import { uploadDocuments } from '../lib/api';

interface Props {
  onClose: () => void;
  onUploaded: () => void;
}

export default function UploadModal({ onClose, onUploaded }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = (newFiles: FileList | null) => {
    if (!newFiles) return;
    const pdfs = Array.from(newFiles).filter((f) => f.name.endsWith('.pdf'));
    setFiles((prev) => [...prev, ...pdfs]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const handleUpload = async () => {
    if (!files.length) return;
    setUploading(true);
    setStatus('Uploading and indexing...');
    try {
      const results = await uploadDocuments(files);
      const total = results.reduce((s, r) => s + r.chunk_count, 0);
      setStatus(`✓ ${results.length} file(s) indexed (${total} chunks)`);
      setTimeout(() => { onUploaded(); onClose(); }, 1200);
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : 'Upload failed'}`);
      setUploading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-title">📄 Upload PDFs</div>

        {/* Dropzone */}
        <div
          className={`dropzone${dragging ? ' drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <div className="dropzone-icon">📂</div>
          <div className="dropzone-text">Drop PDFs here or click to browse</div>
          <div className="dropzone-hint">Multiple files supported</div>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            multiple
            style={{ display: 'none' }}
            onChange={(e) => addFiles(e.target.files)}
          />
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="file-list">
            {files.map((f, i) => (
              <div key={i} className="file-item">
                <span className="file-item-icon">📄</span>
                <span className="file-item-name">{f.name}</span>
                <span className="file-item-size">
                  {(f.size / 1024).toFixed(1)} KB
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Status */}
        {status && (
          <div className="upload-progress">
            {uploading && !status.startsWith('✓') && (
              <span className="spinner" />
            )}
            {status}
          </div>
        )}

        <div className="modal-actions">
          <button className="btn-cancel" onClick={onClose} disabled={uploading}>
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={handleUpload}
            disabled={!files.length || uploading}
            id="upload-submit-btn"
          >
            {uploading ? 'Indexing…' : `Upload ${files.length || ''} file${files.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
}
