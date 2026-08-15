'use client';
// frontend/components/ChatWindow.tsx
// Main chat interface — handles messages, streaming, and citations

import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { SourceCitation, streamQuestion } from '../lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceCitation[];
  streaming?: boolean;
}

interface Props {
  hasDocuments: boolean;
}

export default function ChatWindow({ hasDocuments }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const sendMessage = async () => {
    const question = input.trim();
    if (!question || isStreaming) return;

    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
    };

    const assistantId = (Date.now() + 1).toString();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      streaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);

    let accumulatedText = '';

    await streamQuestion(
      question,
      (token) => {
        accumulatedText += token;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: accumulatedText }
              : m
          )
        );
      },
      (sources) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, sources } : m
          )
        );
      },
      () => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, streaming: false } : m
          )
        );
        setIsStreaming(false);
      },
      (error) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: `Error: ${error}`, streaming: false }
              : m
          )
        );
        setIsStreaming(false);
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-area">
      {/* Header */}
      <div className="chat-header">
        <span className="chat-header-title">Chat with your documents</span>
        <div className="status-pill">
          <span className="status-dot" />
          {hasDocuments ? 'Ready' : 'Upload a PDF to start'}
        </div>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <WelcomeScreen />
        ) : (
          messages.map((msg) => (
            <MessageRow key={msg.id} message={msg} />
          ))
        )}

        {/* Thinking indicator — shown while waiting for first token */}
        {isStreaming && messages[messages.length - 1]?.content === '' && (
          <div className="message-row assistant">
            <div className="thinking">
              <div className="dot-wave">
                <span /><span /><span />
              </div>
              Thinking…
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="input-area">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-input"
            placeholder={
              hasDocuments
                ? 'Ask anything about your documents… (Enter to send)'
                : 'Upload a PDF first to start asking questions'
            }
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={!hasDocuments || isStreaming}
            rows={1}
            id="chat-input"
          />
          <button
            className="send-btn"
            onClick={sendMessage}
            disabled={!input.trim() || !hasDocuments || isStreaming}
            id="send-btn"
            aria-label="Send message"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <div className="input-hint">
          {isStreaming ? 'Generating answer…' : 'Shift+Enter for new line'}
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────

function WelcomeScreen() {
  return (
    <div className="welcome-screen">
      <div className="welcome-icon">⚡</div>
      <div className="welcome-title">PDF-QA</div>
      <div className="welcome-subtitle">
        Upload your PDFs and ask questions. Get grounded answers with page citations — no hallucinations.
      </div>
      <div className="welcome-steps">
        {[
          { n: 1, text: 'Upload a PDF from the sidebar' },
          { n: 2, text: 'Ask any question about it' },
          { n: 3, text: 'Get cited answers instantly' },
        ].map(({ n, text }) => (
          <div key={n} className="welcome-step">
            <span className="step-num">{n}</span>
            {text}
          </div>
        ))}
      </div>
    </div>
  );
}

function MessageRow({ message }: { message: Message }) {
  return (
    <div className={`message-row ${message.role}`}>
      <div className={`message-bubble ${message.role}`}>
        <div className="markdown-body">
          <ReactMarkdown>
            {message.content}
          </ReactMarkdown>
        </div>
        {message.streaming && message.content && (
          <span className="cursor" />
        )}
        {message.role === 'assistant' && !message.streaming && message.content && (
          <CopyButton text={message.content} />
        )}
      </div>

      {/* Source citations */}
      {message.sources && message.sources.length > 0 && (
        <div className="sources-bar">
          {message.sources.map((src, i) => (
            <div
              key={i}
              className="source-badge"
              title={src.snippet}
              id={`source-${i}`}
            >
              <span className="source-badge-icon">📄</span>
              <span>{src.filename} · p.{src.page}</span>
              <span className="source-score">{src.score.toFixed(2)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <button className="btn-copy" onClick={handleCopy} title="Copy response">
      {copied ? '✅' : '📋'}
    </button>
  );
}
