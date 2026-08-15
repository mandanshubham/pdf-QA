import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'PDF-QA — RAG-Powered Document Chat',
  description:
    'Upload PDFs and ask questions. Get grounded answers with source citations powered by Gemini and ChromaDB.',
  keywords: ['PDF', 'RAG', 'AI', 'document chat', 'question answering'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
