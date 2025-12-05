"""
Prometheus metrics for content moderation.
"""

from prometheus_client import Counter, Gauge

# Moderation action counters
moderation_quarantined_total = Counter(
    "moderation_quarantined_total",
    "Total content quarantined for review",
    ["type"]
)

moderation_removed_total = Counter(
    "moderation_removed_total",
    "Total content removed for policy violation",
    ["type", "category"]
)

moderation_published_total = Counter(
    "moderation_published_total",
    "Total content published after review"
)

moderation_blocked_total = Counter(
    "moderation_blocked_total",
    "Total content blocked at submission",
    ["type"]
)

# Queue metrics
moderation_quarantine_queue_length = Gauge(
    "moderation_quarantine_queue_length",
    "Current length of quarantine review queue"
)

# Report metrics
reports_submitted_total = Counter(
    "reports_submitted_total",
    "Total user reports submitted",
    ["reason"]
)

reports_resolved_total = Counter(
    "reports_resolved_total",
    "Total reports resolved by moderators",
    ["action"]
)


def track_quarantine(content_type: str):
    """Track content entering quarantine."""
    moderation_quarantined_total.labels(type=content_type).inc()


def track_removal(content_type: str, category: str = "unknown"):
    """Track content removal."""
    moderation_removed_total.labels(type=content_type, category=category).inc()


def track_publish():
    """Track content published after review."""
    moderation_published_total.inc()


def track_block(content_type: str):
    """Track content blocked at submission."""
    moderation_blocked_total.labels(type=content_type).inc()


def update_queue_length(length: int):
    """Update quarantine queue length."""
    moderation_quarantine_queue_length.set(length)


def track_report(reason: str):
    """Track user report submission."""
    reports_submitted_total.labels(reason=reason).inc()


def track_report_resolution(action: str):
    """Track report resolution."""
    reports_resolved_total.labels(action=action).inc()
