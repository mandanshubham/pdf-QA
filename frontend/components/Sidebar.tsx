'use client';
// frontend/components/Sidebar.tsx
// Document list + upload button

import { DocumentInfo, deleteDocument, formatFileSize, formatDate } from '../lib/api';

interface Props {
  documents: DocumentInfo[];
  loading: boolean;
  onUploadClick: () => void;
  onDeleted: (docId: string) => void;
}

export default function Sidebar({ documents, loading, onUploadClick, onDeleted }: Props) {
  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Delete "${filename}" and all its indexed content?`)) return;
    try {
      await deleteDocument(docId);
      onDeleted(docId);
    } catch {
      alert('Failed to delete document.');
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">⚡ PDF-QA</div>
        <div className="sidebar-subtitle">RAG-powered document chat</div>
      </div>

      <div className="sidebar-body">
        {/* Upload button */}
        <button
          className="upload-btn"
          onClick={onUploadClick}
          id="upload-pdf-btn"
        >
          <span>+</span>
          Upload PDF
        </button>

        {/* Document list */}
        {loading ? (
          <div className="empty-docs">
            <span className="spinner" />
            <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Loading…</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-docs">
            <div className="empty-docs-icon">📂</div>
            <div className="empty-docs-text">
              No documents yet.<br />Upload a PDF to get started.
            </div>
          </div>
        ) : (
          <>
            <div className="doc-section-label">
              {documents.length} document{documents.length !== 1 ? 's' : ''}
            </div>
            {documents.map((doc) => (
              <div key={doc.doc_id} className="doc-card">
                <div className="doc-card-name" title={doc.filename}>
                  📄 {doc.filename}
                </div>
                <div className="doc-card-meta">
                  {doc.chunk_count} chunks · {formatFileSize(doc.file_size_bytes)}
                </div>
                <div className="doc-card-meta">{formatDate(doc.upload_timestamp)}</div>
                <div className="doc-card-actions">
                  <button
                    className="btn-delete"
                    onClick={() => handleDelete(doc.doc_id, doc.filename)}
                    id={`delete-doc-${doc.doc_id.slice(0, 8)}`}
                  >
                    🗑 Remove
                  </button>
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </aside>
  );
}
