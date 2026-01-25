import React, { useState } from 'react'
import { ReviewIssue } from '../types'

interface BugsPanelProps {
    issues: ReviewIssue[]
    onIssueClick: (issue: ReviewIssue) => void
    isLoading?: boolean
}

export function BugsPanelComponent({ issues, onIssueClick, isLoading }: BugsPanelProps) {
    const [isSevereExpanded, setIsSevereExpanded] = useState(true)
    const [isNonSevereExpanded, setIsNonSevereExpanded] = useState(true)

    // Filter for bugs
    const bugs = issues.filter(i => i.category === 'bug')
    const severeBugs = bugs.filter(i => i.severity === 'high' || i.severity === 'critical')
    const nonSevereBugs = bugs.filter(i => i.severity === 'low' || i.severity === 'medium')

    if (bugs.length === 0 && !isLoading) {
        return (
            <div style={{ padding: '20px', color: 'var(--text-secondary)', textAlign: 'center', fontSize: '13px' }}>
                No bugs found.
            </div>
        )
    }

    const renderIssue = (issue: ReviewIssue, index: number, isLast: boolean) => {
        const severityColor = (issue.severity === 'high' || issue.severity === 'critical') ? '#ef4444' : '#eab308'

        // Format location
        const citation = issue.citations[0]
        const location = citation ? `${citation.path.split('/').pop()}:${citation.startLine}${citation.endLine !== citation.startLine ? `-${citation.endLine}` : ''}` : ''

        return (
            <div
                key={index}
                onClick={() => onIssueClick(issue)}
                style={{
                    padding: '12px',
                    borderBottom: !isLast ? '1px solid #27272a' : 'none',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                    display: 'flex',
                    gap: '12px'
                }}
                className="flag-item"
            >
                <div style={{ marginTop: '2px', color: severityColor }}>
                    {/* Ladybug icon */}
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        {/* Body */}
                        <ellipse cx="12" cy="14" rx="7" ry="8" fill={severityColor} />
                        {/* Head */}
                        <circle cx="12" cy="6" r="3" fill={severityColor} />
                        {/* Center line */}
                        <line x1="12" y1="6" x2="12" y2="22" stroke="#18181b" strokeWidth="1.5" />
                        {/* Spots */}
                        <circle cx="9" cy="11" r="1.5" fill="#18181b" />
                        <circle cx="15" cy="11" r="1.5" fill="#18181b" />
                        <circle cx="8" cy="16" r="1.5" fill="#18181b" />
                        <circle cx="16" cy="16" r="1.5" fill="#18181b" />
                        <circle cx="10" cy="19" r="1.2" fill="#18181b" />
                        <circle cx="14" cy="19" r="1.2" fill="#18181b" />
                    </svg>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                        fontSize: '13px',
                        fontWeight: 500,
                        color: '#e4e4e7',
                        marginBottom: '4px',
                        lineHeight: '1.4'
                    }}>
                        {issue.title}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
                        <span style={{ color: severityColor, fontWeight: 500, textTransform: 'capitalize' }}>{issue.severity}</span>
                        <span style={{ color: '#71717a' }}>{location}</span>
                    </div>
                </div>
            </div>
        )
    }

    const renderSection = (title: string, items: ReviewIssue[], isExpanded: boolean, setIsExpanded: (v: boolean) => void) => {
        if (items.length === 0) return null
        return (
            <div style={{
                backgroundColor: '#18181b',
                border: '1px solid #27272a',
                borderRadius: '8px',
                overflow: 'hidden',
                marginBottom: '8px'
            }}>
                <div
                    onClick={() => setIsExpanded(!isExpanded)}
                    style={{
                        padding: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: 600,
                        color: '#e4e4e7'
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>{title} ({items.length})</span>
                    </div>
                    <span style={{
                        transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.2s',
                        color: '#71717a'
                    }}>
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor">
                            <path d="M2 4L6 8L10 4" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </span>
                </div>

                {isExpanded && (
                    <div style={{ borderTop: '1px solid #27272a' }}>
                        {items.map((issue, index) => renderIssue(issue, index, index === items.length - 1))}
                    </div>
                )}
            </div>
        )
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', padding: '16px' }}>
            {isLoading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#a1a1aa', fontSize: '13px' }}>
                    <div className="spinner-border" style={{
                        width: '12px',
                        height: '12px',
                        border: '2px solid #f59e0b',
                        borderRightColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }} />
                    <span>Scanning for bugs...</span>
                </div>
            )}

            {renderSection("Severe", severeBugs, isSevereExpanded, setIsSevereExpanded)}
            {renderSection("Non-severe", nonSevereBugs, isNonSevereExpanded, setIsNonSevereExpanded)}
        </div>
    )
}

export const BugsPanel = React.memo(BugsPanelComponent)
