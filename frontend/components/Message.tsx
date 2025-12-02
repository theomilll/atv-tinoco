'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface Citation {
  document_title: string
  chunk_index: number
}

interface Attachment {
  filename: string
  file_type: string
  file_path: string
  category: 'image' | 'document'
}

interface MessageProps {
  role: 'user' | 'assistant' | 'system'
  content: string
  username?: string
  citations?: Citation[]
  attachments?: Attachment[]
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ''

export function Message({ role, content, username = 'USER', citations, attachments }: MessageProps) {
  const isUser = role === 'user'
  const isSystem = role === 'system'
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className={`border border-border ${isUser ? 'bg-bg-elevated' : 'bg-bg-surface'} group`}>
      {/* Header */}
      <div className="px-4 py-2 border-b border-dotted border-border flex items-center justify-between">
        <div className="text-xs tracking-wider text-text-muted">
          {isUser ? username.toUpperCase() : isSystem ? 'SYSTEM' : 'GEPETO'}
        </div>
        <div className="flex items-center gap-3">
          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="text-xs text-text-muted hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
            title="Copy to clipboard"
          >
            {copied ? 'COPIED' : 'COPY'}
          </button>
          <div className="text-xs text-text-muted">
            {isUser ? 'OUTBOUND' : 'INBOUND'}
          </div>
        </div>
      </div>

      {/* Attachments */}
      {attachments && attachments.length > 0 && (
        <div className="p-4 pb-0">
          <div className="flex flex-wrap gap-2">
            {attachments.map((att, i) => (
              att.category === 'image' ? (
                <img
                  key={i}
                  src={`${API_BASE_URL}/media/${att.file_path}`}
                  alt={att.filename}
                  className="max-h-48 border border-border"
                />
              ) : (
                <div key={i} className="flex items-center gap-2 bg-bg-dark border border-border px-3 py-2">
                  <span className="text-text-muted">📄</span>
                  <span className="text-xs">{att.filename}</span>
                </div>
              )
            ))}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        {isUser ? (
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {content}
          </div>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  const isInline = !match && !className

                  if (isInline) {
                    return (
                      <code className="bg-bg-dark px-1 py-0.5 rounded text-accent-light" {...props}>
                        {children}
                      </code>
                    )
                  }

                  return (
                    <SyntaxHighlighter
                      style={oneDark}
                      language={match ? match[1] : 'text'}
                      PreTag="div"
                      customStyle={{
                        margin: 0,
                        background: '#1a1a1a',
                        border: '1px solid #3a3a3a',
                      }}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  )
                },
                pre({ children }) {
                  return <div className="my-3">{children}</div>
                },
                p({ children }) {
                  return <p className="mb-3 last:mb-0">{children}</p>
                },
                ul({ children }) {
                  return <ul className="list-disc pl-5 mb-3">{children}</ul>
                },
                ol({ children }) {
                  return <ol className="list-decimal pl-5 mb-3">{children}</ol>
                },
                li({ children }) {
                  return <li className="mb-1">{children}</li>
                },
                a({ href, children }) {
                  return (
                    <a href={href} className="text-accent-light hover:underline" target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  )
                },
                blockquote({ children }) {
                  return (
                    <blockquote className="border-l-2 border-accent pl-3 italic text-text-muted my-3">
                      {children}
                    </blockquote>
                  )
                },
                table({ children }) {
                  return (
                    <div className="overflow-x-auto my-3">
                      <table className="border-collapse border border-border w-full text-sm">
                        {children}
                      </table>
                    </div>
                  )
                },
                th({ children }) {
                  return (
                    <th className="border border-border bg-bg-elevated px-3 py-2 text-left">
                      {children}
                    </th>
                  )
                },
                td({ children }) {
                  return (
                    <td className="border border-border px-3 py-2">
                      {children}
                    </td>
                  )
                },
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {/* Citations */}
      {citations && citations.length > 0 && (
        <div className="px-4 pb-4">
          <div className="border-t border-dashed border-border pt-3">
            <div className="text-xs tracking-wider text-text-muted mb-2">SOURCES</div>
            {citations.map((citation, idx) => (
              <div key={idx} className="text-xs text-text-secondary py-1 border-l-2 border-accent pl-3 mb-1">
                [{idx + 1}] {citation.document_title} (CHUNK {citation.chunk_index})
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
