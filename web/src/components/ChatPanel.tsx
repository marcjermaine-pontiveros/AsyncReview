import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { PRSummarySkeleton } from './PRSummarySkeleton'
import type { Message, DiffSelection, AnswerBlock, DiffCitation, RLMIteration } from '../types'


interface ChatPanelProps {
  reviewId: string | null
  currentSelection: DiffSelection | null
  onCitationClick?: (citation: DiffCitation) => void
  disabled?: boolean
}

const QUICK_ACTIONS = [
  { label: 'Explain', prompt: 'Explain and breakdown what this code change does' },
  { label: 'Find bugs', prompt: 'Find and breakdown potential bugs or issues in this change' },
  { label: 'Suggest tests', prompt: 'Suggest test cases for this change' },
  { label: 'Summarize risk', prompt: 'Summarize and breakdown the risk level of this change' },
]

// Icons
const Icons = {
  Loop: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2v4" />
      <path d="m16.2 7.8 2.9-2.9" />
      <path d="M18 12h4" />
      <path d="m16.2 16.2 2.9 2.9" />
      <path d="M12 18v4" />
      <path d="m7.8 16.2-2.9 2.9" />
      <path d="M6 12H2" />
      <path d="m7.8 7.8-2.9-2.9" />
    </svg>
  ),
  Search: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  ),
  File: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  ),
  Code: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  ),
  ChevronRight: () => (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m9 18 6-6-6-6" />
    </svg>
  ),
  ChevronDown: () => (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m6 9 6 6 6-6" />
    </svg>
  ),
  Check: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

function IterationTimeline({ iterations }: { iterations: RLMIteration[] }) {
  const [expandedIndices, setExpandedIndices] = useState<Set<number>>(new Set())

  const toggleExpand = (index: number) => {
    setExpandedIndices(prev => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  return (
    <div className="timeline-container">
      <div className="timeline-header">
        <span className="timeline-icon-header"><Icons.Loop /></span>
        <span>RLM Process ({iterations.length} steps)</span>
      </div>

      <div className="timeline-steps">
        {iterations.map((iter, i) => {
          const isExpanded = expandedIndices.has(i)
          // Heuristic to guess icon based on reasoning text
          const Icon = iter.reasoning.toLowerCase().includes('search') ? Icons.Search
            : iter.reasoning.toLowerCase().includes('read') || iter.reasoning.toLowerCase().includes('file') ? Icons.File
              : Icons.Loop

          // Extract first sentence for summary
          const summary = iter.reasoning.split('.')[0] + (iter.reasoning.includes('.') ? '.' : '')

          return (
            <div key={i} className="timeline-step">
              <div className="timeline-step-icon">
                <Icon />
              </div>
              <div className="timeline-step-content">
                <div
                  className="timeline-step-header"
                  onClick={() => toggleExpand(i)}
                >
                  <span className={`timeline-step-summary ${i === iterations.length - 1 ? 'shimmer-text' : ''}`}>{summary}</span>
                  <span className="timeline-step-toggle">
                    {isExpanded ? <Icons.ChevronDown /> : <Icons.ChevronRight />}
                  </span>
                </div>

                {isExpanded && (
                  <div className="timeline-step-details">
                    <div className="timeline-detail-block">
                      <div className="timeline-detail-label">Reasoning</div>
                      <div className="timeline-detail-text">{iter.reasoning}</div>
                    </div>
                    {iter.code && (
                      <div className="timeline-detail-block">
                        <div className="timeline-detail-label">Code</div>
                        <div className="timeline-code">
                          <SyntaxHighlighter
                            style={vscDarkPlus}
                            language="python" // Default to python for RLM code or try to detect
                            PreTag="div"
                            customStyle={{ margin: 0, padding: '12px', background: 'transparent' }}
                          >
                            {iter.code}
                          </SyntaxHighlighter>
                        </div>
                      </div>
                    )}
                    {iter.output && (
                      <details className="timeline-detail-block">
                        <summary className="timeline-detail-label" style={{ cursor: 'pointer', listStyle: 'none' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            Output <Icons.ChevronDown />
                          </span>
                        </summary>
                        <div className="timeline-output" style={{ marginTop: '8px' }}>
                          <SyntaxHighlighter
                            style={vscDarkPlus}
                            language="text"
                            PreTag="div"
                            customStyle={{ margin: 0, padding: '12px', background: 'transparent' }}
                          >
                            {iter.output}
                          </SyntaxHighlighter>
                        </div>
                      </details>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function ChatPanel({
  reviewId,
  currentSelection,
  onCitationClick: _onCitationClick,
  disabled = false,
}: ChatPanelProps) {
  // TODO: Use _onCitationClick to make citations in responses clickable
  void _onCitationClick
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive or iterations update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || !reviewId) return

    const userMessage: Message = { role: 'user', content: question }
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)
    setError(null)

    try {
      // Use streaming endpoint
      const response = await fetch('/api/diff/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewId,
          question,
          conversation: messages.map(m => ({ role: m.role, content: m.content })),
          selection: currentSelection ? {
            path: currentSelection.path,
            side: currentSelection.side,
            startLine: currentSelection.startLine,
            endLine: currentSelection.endLine,
            mode: currentSelection.mode,
          } : null,
        }),
      })

      if (!response.ok) throw new Error('Failed to get response')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      let assistantContent = ''
      const decoder = new TextDecoder()
      let buffer = '' // Buffer for incomplete SSE events

      // Add placeholder assistant message
      setMessages(prev => [...prev, { role: 'assistant', content: '' }])

      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          console.log('[SSE] Stream ended')
          break
        }

        // Append new data to buffer
        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk

        // Process complete SSE events
        // Normalizing line endings or splitting by regex is safer for inconsistent line endings
        const parts = buffer.split(/\n\n|\r\n\r\n/g)
        // Keep the last potentially incomplete event in the buffer
        buffer = parts.pop() || ''

        for (const event of parts) {
          if (!event.trim()) continue

          console.log('[SSE] Processing event:', event)
          const lines = event.split(/\r?\n/)
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                console.log('[SSE] Parsed data:', data)
                if (data.type === 'start') {
                  console.log('[SSE] Received start event')
                } else if (data.type === 'iteration') {
                  // Handle RLM iteration - add to current iterations
                  const iter = data.data as RLMIteration

                  // Update the assistant message to show current iteration status and store the iteration
                  setMessages(prev => {
                    const newMessages = [...prev]
                    const lastMsg = newMessages[newMessages.length - 1]
                    newMessages[newMessages.length - 1] = {
                      ...lastMsg,
                      role: 'assistant',
                      content: '', // Keep content empty while iterating
                      iterations: [...(lastMsg.iterations || []), iter]
                    }
                    return newMessages
                  })
                } else if (data.type === 'block') {
                  const block = data.data.block as AnswerBlock
                  assistantContent += block.content + '\n'
                  setMessages(prev => {
                    const newMessages = [...prev]
                    newMessages[newMessages.length - 1] = {
                      ...newMessages[newMessages.length - 1],
                      role: 'assistant',
                      content: assistantContent.trim()
                    }
                    return newMessages
                  })
                } else if (data.type === 'error') {
                  setError(data.data.error)
                }
              } catch (e) {
                console.error('[SSE] Parse error:', e)
              }
            }
          }
        }
      }

      // Process any remaining data in buffer
      if (buffer.trim()) {
        const lines = buffer.split(/\r?\n/)
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'block') {
                const block = data.data.block as AnswerBlock
                assistantContent += block.content + '\n'
                setMessages(prev => {
                  const newMessages = [...prev]
                  newMessages[newMessages.length - 1] = {
                    ...newMessages[newMessages.length - 1],
                    role: 'assistant',
                    content: assistantContent.trim()
                  }
                  return newMessages
                })
              }
            } catch {
              // Ignore
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setLoading(false)
    }
  }, [reviewId, messages, currentSelection])

  // Fetch suggestions when loading finishes and we have a new assistant message
  const [suggestions, setSuggestions] = useState<string[]>([])

  useEffect(() => {
    if (!loading && messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
      const fetchSuggestions = async () => {
        if (!reviewId) return
        try {
          // Get last answer
          const lastMsg = messages[messages.length - 1]
          const conversation = messages.slice(0, -1).map(m => ({ role: m.role, content: typeof m.content === 'string' ? m.content : '' }))

          const res = await fetch('/api/suggestions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              reviewId,
              conversation,
              lastAnswer: typeof lastMsg.content === 'string' ? lastMsg.content : ''
            })
          })
          if (res.ok) {
            const data = await res.json()
            setSuggestions(data.suggestions)
          }
        } catch (e) {
          console.error(e)
        }
      }
      fetchSuggestions()
    }
  }, [loading, messages, reviewId])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(inputMessage)
    }
  }

  return (
    <div className="chat-panel-inner">
      {/* Quick actions */}
      {reviewId && messages.length === 0 && (
        <div className="quick-actions">
          {QUICK_ACTIONS.map(action => (
            <button
              key={action.label}
              className="quick-action"
              onClick={() => sendMessage(action.prompt)}
              disabled={loading || disabled}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state" style={{ padding: 0, justifyContent: 'flex-start', opacity: 1 }}>
            <PRSummarySkeleton />
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`chat-message ${msg.role}`}
          >
            {msg.role === 'user' && (
              <div className="chat-message-role">
                You
              </div>
            )}

            {msg.iterations && msg.iterations.length > 0 && (
              <IterationTimeline iterations={msg.iterations} />
            )}

            <div className="chat-message-content">
              {msg.role === 'assistant' ? (
                msg.content ? (
                  <ReactMarkdown
                    components={{
                      code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || '')
                        return !inline && match ? (
                          <SyntaxHighlighter
                            style={vscDarkPlus}
                            language={match[1]}
                            PreTag="div"
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        )
                      }
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  msg.iterations && msg.iterations.length > 0 ? null : (
                    <div className="skeleton-container">
                      <div className="skeleton-line short shimmer-bg" />
                      <div className="skeleton-line medium shimmer-bg" />
                      <div className="skeleton-line long shimmer-bg" />
                    </div>
                  )
                )
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {error && <div className="chat-error">{error}</div>}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && !loading && (
        <div className="suggestions-container">
          <div className="suggestions-label">
            Suggestions
          </div>
          <div className="suggestions-list">
            {suggestions.map((suggestion, i) => (
              <button
                key={i}
                className="suggestion-chip"
                onClick={() => sendMessage(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="chat-input-container">
        <textarea
          className="chat-input"
          placeholder={currentSelection ? 'Ask about selection...' : 'Ask about this PR...'}
          value={inputMessage}
          onChange={e => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          style={{ height: 'auto', minHeight: '44px' }}
          disabled={!reviewId || loading || disabled}
        />
      </div>
    </div>
  )
}
