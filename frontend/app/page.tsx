'use client';
// frontend/app/page.tsx
// Root page — composes Sidebar + ChatWindow, manages shared state

import { useCallback, useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import UploadModal from '../components/UploadModal';
import { DocumentInfo, listDocuments } from '../lib/api';

export default function Home() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [showUpload, setShowUpload] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch {
      // backend might not be running yet — silently ignore
      setDocuments([]);
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  const handleDeleted = (docId: string) => {
    setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
  };

  return (
    <div className="app-shell">
      <Sidebar
        documents={documents}
        loading={loadingDocs}
        onUploadClick={() => setShowUpload(true)}
        onDeleted={handleDeleted}
      />

      <ChatWindow hasDocuments={documents.length > 0} />

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onUploaded={fetchDocuments}
        />
      )}
    </div>
  );
}
