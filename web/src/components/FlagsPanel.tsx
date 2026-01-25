import React, { useState } from 'react'
import { ReviewIssue } from '../types'

interface FlagsPanelProps {
    issues: ReviewIssue[]
    onIssueClick: (issue: ReviewIssue) => void
    isLoading?: boolean
}

export function FlagsPanelComponent({ issues, onIssueClick, isLoading }: FlagsPanelProps) {
    const [isExpanded, setIsExpanded] = useState(true)

    // Filter issues by category/severity for organization if needed, 
    // but user requested a simple list card like DevinReview.
    // DevinReview image shows "2 Flags" header that expands.

    if (issues.length === 0 && !isLoading) {
        return (
            <div style={{ padding: '20px', color: 'var(--text-secondary)', textAlign: 'center', fontSize: '13px' }}>
                No flags found.
            </div>
        )
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '16px' }}>
            {/* Flags List Card */}
            <div style={{
                backgroundColor: '#18181b',
                border: '1px solid #27272a',
                borderRadius: '8px',
                overflow: 'hidden'
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
                        color: isExpanded ? '#f59e0b' : '#a1a1aa'
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>{isLoading ? 'Scanning...' : `${issues.length} Flags`}</span>
                        {isLoading && (
                            <div className="spinner-border" style={{
                                width: '12px',
                                height: '12px',
                                border: '2px solid #f59e0b',
                                borderRightColor: 'transparent',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite'
                            }} />
                        )}
                    </div>
                    <span style={{
                        transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.2s'
                    }}>
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor">
                            <path d="M2 4L6 8L10 4" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </span>
                </div>

                {isExpanded && (
                    <div style={{ borderTop: '1px solid #27272a' }}>
                        {issues.map((issue, index) => {
                            const isInvestigate = issue.category === 'investigation' || issue.severity === 'high' || issue.severity === 'critical'
                            const iconColor = isInvestigate ? '#f59e0b' : '#a1a1aa'

                            // Format location
                            const citation = issue.citations[0]
                            const location = citation ? `${citation.path.split('/').pop()}:${citation.startLine}${citation.endLine !== citation.startLine ? `-${citation.endLine}` : ''}` : ''

                            return (
                                <div
                                    key={index}
                                    onClick={() => onIssueClick(issue)}
                                    style={{
                                        padding: '12px',
                                        borderBottom: index < issues.length - 1 ? '1px solid #27272a' : 'none',
                                        cursor: 'pointer',
                                        transition: 'background-color 0.2s',
                                        display: 'flex',
                                        gap: '12px'
                                    }}
                                    className="flag-item"
                                >
                                    <div style={{ marginTop: '2px', color: iconColor }}>
                                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M2 2v11h2V9h8V2H2z" fill={iconColor} />
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
                                            {isInvestigate && (
                                                <span style={{ color: '#f59e0b', fontWeight: 500 }}>Investigate</span>
                                            )}
                                            <span style={{ color: '#71717a' }}>{location}</span>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}

export const FlagsPanel = React.memo(FlagsPanelComponent)
