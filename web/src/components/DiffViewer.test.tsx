import { render, screen, act, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'
import { DiffViewer } from './DiffViewer' // Use the memoized export
import type { ReviewIssue, PRInfo } from '../types'

// Extend vitest expect with jest-dom matchers
expect.extend(matchers)

// Mock fetching
const fetchMock = vi.fn()
vi.stubGlobal('fetch', fetchMock)

// Mock default props
const mockPRInfo: PRInfo = {
    reviewId: 'test-review-id',
    title: 'Test PR',
    body: 'Body',
    repo: { owner: 'owner', repo: 'repo' },
    number: 1,
    baseSha: 'base',
    headSha: 'head',
    files: [{ path: 'test.ts', status: 'modified' }]
}

const mockIssue: ReviewIssue = {
    title: 'Test Flag',
    severity: 'high',
    category: 'investigation',
    explanationMarkdown: 'Explain',
    citations: [{ path: 'test.ts', startLine: 5, endLine: 5, side: 'additions' }]
}

// Mock DOM methods
Element.prototype.scrollIntoView = vi.fn()
Element.prototype.getBoundingClientRect = vi.fn(() => ({
    top: 100,
    left: 100,
    right: 120,
    bottom: 120,
    width: 20,
    height: 20,
    x: 100,
    y: 100,
    toJSON: () => { }
}))

// Mock CSSStyleSheet for jsdom (needed for @pierre/diffs web components)
class MockCSSStyleSheet {
    replaceSync() { }
}
vi.stubGlobal('CSSStyleSheet', MockCSSStyleSheet)

describe('DiffViewer Jump to Flag', () => {
    beforeEach(() => {
        vi.resetAllMocks()
        // Do not verify timers here yet
    })

    afterEach(() => {
        vi.useRealTimers()
    })

    it('scolls to focused issue when loaded', async () => {
        // Mock file response
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({
                oldFile: { name: 'test.ts', contents: 'line1\nline2\nline3\nline4\nline5' },
                newFile: { name: 'test.ts', contents: 'line1\nline2\nline3\nline4\nline5' }
            })
        })

        const { rerender } = render(
            <DiffViewer
                prInfo={mockPRInfo}
                selectedFilePath="test.ts"
                issues={[mockIssue]}
                focusedIssue={null}
            />
        )

        // Wait for loading with real timers
        await waitFor(() => expect(fetchMock).toHaveBeenCalled())
        // Wait for diff to render (simplified mock check)
        // In real env we'd wait for text content or similar

        // NOW enable fake timers for the scroll timeout
        vi.useFakeTimers()

        // Update prop to focus issue
        rerender(
            <DiffViewer
                prInfo={mockPRInfo}
                selectedFilePath="test.ts"
                issues={[mockIssue]}
                focusedIssue={mockIssue}
            />
        )

        // Run timers for the effect timeout (100ms) + polling (needs at least 2 checks = 200ms)
        // Total wait: 100 (initial) + 100 (first check) + 100 (second stable check) = 300ms minimum
        // Let's advance sufficiently
        act(() => {
            vi.advanceTimersByTime(500)
        })

        // Check if querySelector was called with correct key
        const key = `${mockIssue.title}-${mockIssue.citations[0].startLine}`
        const element = document.querySelector(`[data-issue-key="${key}"]`)

        // Since we mocked scrollIntoView prototype, checking if the element's method was called rely on the element existing
        // We rendered DiffViewer, assuming MultiFileDiff renders renderAnnotation result:
        expect(element).toBeInTheDocument()

        // In JSDOM, scrollIntoView is a stub, but we spied on prototype
        // If element is found, our effect calls it.
        expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({ block: 'center', behavior: 'smooth' })

        // Check popover state - activeIssue would trigger IssuePopover
        // IssuePopover renders if activeIssue is set.
        // We can check if text is in document
        expect(screen.getByText('Test Flag')).toBeInTheDocument()
    })
})
