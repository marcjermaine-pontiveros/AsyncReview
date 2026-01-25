export function PRSummarySkeleton() {
    return (
        <div className="pr-summary-skeleton">
            <div className="pr-header">
                <div className="pr-meta-top">
                    <div className="skeleton-item skeleton-badge"></div>
                    <div className="skeleton-item skeleton-text-short opacity-50"></div>
                </div>

                <div className="skeleton-item skeleton-title"></div>

                <div className="pr-meta-row">
                    <div className="skeleton-item skeleton-avatar-circle"></div>
                    <div className="skeleton-item skeleton-text-medium opacity-70"></div>
                    <div className="skeleton-item skeleton-text-medium opacity-40"></div>
                </div>
            </div>

            <div className="pr-tabs">
                <div className="skeleton-item skeleton-tab"></div>
                <div className="skeleton-item skeleton-tab opacity-50"></div>
                <div className="skeleton-item skeleton-tab opacity-30"></div>
            </div>

            <div className="pr-tab-content">
                <div className="skeleton-lines">
                    <div className="skeleton-item skeleton-line-full"></div>
                    <div className="skeleton-item skeleton-line-full opacity-80"></div>
                    <div className="skeleton-item skeleton-line-full opacity-60"></div>
                    <div className="skeleton-item skeleton-line-medium opacity-40"></div>
                    <div className="skeleton-item skeleton-line-full opacity-30"></div>
                    <div className="skeleton-item skeleton-line-short opacity-20"></div>
                </div>
            </div>
        </div>
    )
}
