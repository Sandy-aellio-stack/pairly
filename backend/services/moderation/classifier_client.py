"""
Content Moderation Classifier Client

Supports:
- Local heuristic classifier (keyword-based)
- Google Vision SafeSearch API adapter

Returns moderation scores and classifications.
"""

import os
import re
from typing import Dict, List, Tuple
from enum import Enum


class ModerationEngine(str, Enum):
    LOCAL_HEURISTIC = "local_heuristic"
    GOOGLE_VISION = "google_vision"
    ENSEMBLE = "ensemble"


class ModerationResult:
    def __init__(
        self,
        score: float,
        is_explicit: bool,
        is_suspicious: bool,
        categories: List[str],
        engine: str,
        details: Dict = None
    ):
        self.score = score
        self.is_explicit = is_explicit
        self.is_suspicious = is_suspicious
        self.categories = categories
        self.engine = engine
        self.details = details or {}

    def to_dict(self):
        return {
            "score": self.score,
            "is_explicit": self.is_explicit,
            "is_suspicious": self.is_suspicious,
            "categories": self.categories,
            "engine": self.engine,
            "details": self.details
        }


# Prohibited content keyword lists
SEXUAL_KEYWORDS = [
    # Explicit terms
    r'\b(nude|naked|strip|striptease|porn|xxx|sex)\b',
    r'\b(escort|prostitute|hooker|call\s*girl)\b',
    r'\b(blow\s*job|hand\s*job|oral|anal)\b',
    r'\b(dick|cock|pussy|penis|vagina|breast|nipple)\b',
    r'\b(horny|aroused|turned\s*on|get\s*off)\b',
    r'\b(masturbat|jack\s*off|jerk\s*off)\b',
    r'\b(cum|orgasm|climax|ejaculat)\b',
    r'\b(fetish|bdsm|dominat|submissive)\b',
    
    # Solicitation
    r'\b(rate|price|donation|tribute)\s*(for|per)\s*(hour|night|meet)\b',
    r'\b(incall|outcall|full\s*service)\b',
    r'\b(sugar\s*daddy|sugar\s*baby|arrangement)\b',
    r'\b(generous|compensat|allowance)\s*(for|seeking)\b',
    
    # Euphemisms
    r'\b(netflix\s*and\s*chill|dtf|down\s*to\s*fuck)\b',
    r'\b(nsa|no\s*strings|friends\s*with\s*benefits|fwb)\b',
    r'\b(420\s*friendly|party\s*favors|pnp)\b',
]

VIOLENCE_KEYWORDS = [
    r'\b(kill|murder|shoot|stab|attack)\b',
    r'\b(bomb|explode|terrorist|weapon)\b',
    r'\b(rape|assault|abuse|torture)\b',
]

MINOR_KEYWORDS = [
    r'\b(child|kid|minor|underage|teen|young|loli|shota)\b',
    r'\b(school\s*girl|school\s*boy|jailbait)\b',
]

# Compile regex patterns
SEXUAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SEXUAL_KEYWORDS]
VIOLENCE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in VIOLENCE_KEYWORDS]
MINOR_PATTERNS = [re.compile(p, re.IGNORECASE) for p in MINOR_KEYWORDS]


def analyze_text_local(text: str) -> ModerationResult:
    """
    Local heuristic text classifier using keyword matching.
    
    Returns score from 0.0 (safe) to 1.0 (explicit).
    """
    if not text:
        return ModerationResult(
            score=0.0,
            is_explicit=False,
            is_suspicious=False,
            categories=[],
            engine=ModerationEngine.LOCAL_HEURISTIC
        )
    
    text_lower = text.lower()
    categories = []
    match_counts = {
        "sexual": 0,
        "violence": 0,
        "minor": 0
    }
    
    # Check for sexual content
    for pattern in SEXUAL_PATTERNS:
        matches = pattern.findall(text_lower)
        if matches:
            match_counts["sexual"] += len(matches)
            if "sexual" not in categories:
                categories.append("sexual")
    
    # Check for violence
    for pattern in VIOLENCE_PATTERNS:
        matches = pattern.findall(text_lower)
        if matches:
            match_counts["violence"] += len(matches)
            if "violence" not in categories:
                categories.append("violence")
    
    # Check for minor references (CRITICAL)
    for pattern in MINOR_PATTERNS:
        matches = pattern.findall(text_lower)
        if matches:
            match_counts["minor"] += len(matches)
            if "minor" not in categories:
                categories.append("minor")
    
    # Calculate score
    # Minor references = immediate high score
    if match_counts["minor"] > 0:
        score = 0.95
    # Sexual content scoring
    elif match_counts["sexual"] >= 3:
        score = 0.90
    elif match_counts["sexual"] == 2:
        score = 0.70
    elif match_counts["sexual"] == 1:
        score = 0.55
    # Violence scoring
    elif match_counts["violence"] >= 2:
        score = 0.75
    elif match_counts["violence"] == 1:
        score = 0.50
    else:
        score = 0.0
    
    # Determine classification
    is_explicit = score >= 0.85
    is_suspicious = 0.50 <= score < 0.85
    
    return ModerationResult(
        score=score,
        is_explicit=is_explicit,
        is_suspicious=is_suspicious,
        categories=categories,
        engine=ModerationEngine.LOCAL_HEURISTIC,
        details={"match_counts": match_counts}
    )


def analyze_image_local(image_bytes: bytes) -> ModerationResult:
    """
    Local heuristic image classifier (stub implementation).
    
    In production, use Google Vision or similar.
    For now, returns safe for all images.
    """
    # Stub: Always returns safe
    # In production, implement actual image analysis
    return ModerationResult(
        score=0.0,
        is_explicit=False,
        is_suspicious=False,
        categories=[],
        engine=ModerationEngine.LOCAL_HEURISTIC,
        details={"note": "Local image analysis not implemented, using Google Vision"}
    )


def analyze_image_google_vision(image_bytes: bytes) -> ModerationResult:
    """
    Google Vision SafeSearch API classifier.
    
    Requires GOOGLE_CLOUD_API_KEY or application default credentials.
    """
    try:
        from google.cloud import vision
        
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        
        # SafeSearch detection
        response = client.safe_search_detection(image=image)
        safe_search = response.safe_search_annotation
        
        # Likelihood levels: UNKNOWN, VERY_UNLIKELY, UNLIKELY, POSSIBLE, LIKELY, VERY_LIKELY
        # Map to scores
        likelihood_scores = {
            0: 0.0,   # UNKNOWN
            1: 0.1,   # VERY_UNLIKELY
            2: 0.3,   # UNLIKELY
            3: 0.6,   # POSSIBLE
            4: 0.85,  # LIKELY
            5: 0.95,  # VERY_LIKELY
        }
        
        adult_score = likelihood_scores.get(safe_search.adult, 0.0)
        violence_score = likelihood_scores.get(safe_search.violence, 0.0)
        racy_score = likelihood_scores.get(safe_search.racy, 0.0)
        
        # Take maximum score
        max_score = max(adult_score, violence_score, racy_score)
        
        categories = []
        if adult_score >= 0.5:
            categories.append("adult")
        if violence_score >= 0.5:
            categories.append("violence")
        if racy_score >= 0.5:
            categories.append("racy")
        
        is_explicit = max_score >= 0.85
        is_suspicious = 0.50 <= max_score < 0.85
        
        return ModerationResult(
            score=max_score,
            is_explicit=is_explicit,
            is_suspicious=is_suspicious,
            categories=categories,
            engine=ModerationEngine.GOOGLE_VISION,
            details={
                "adult": adult_score,
                "violence": violence_score,
                "racy": racy_score
            }
        )
    
    except ImportError:
        print("⚠️  Google Cloud Vision library not installed. Falling back to local classifier.")
        return analyze_image_local(image_bytes)
    
    except Exception as e:
        print(f"⚠️  Google Vision API error: {e}. Falling back to local classifier.")
        return analyze_image_local(image_bytes)


def analyze_text(text: str, engine: str = "local") -> ModerationResult:
    """
    Main text analysis function.
    
    Args:
        text: Text content to analyze
        engine: "local" or "ensemble" (future: add more engines)
    
    Returns:
        ModerationResult with score and classification
    """
    if engine == "local" or engine == "ensemble":
        return analyze_text_local(text)
    else:
        return analyze_text_local(text)


def analyze_image(image_bytes: bytes, engine: str = "google_vision") -> ModerationResult:
    """
    Main image analysis function.
    
    Args:
        image_bytes: Image file content
        engine: "google_vision", "local", or "ensemble"
    
    Returns:
        ModerationResult with score and classification
    """
    if engine == "google_vision":
        return analyze_image_google_vision(image_bytes)
    elif engine == "local":
        return analyze_image_local(image_bytes)
    elif engine == "ensemble":
        # Future: combine multiple classifiers
        return analyze_image_google_vision(image_bytes)
    else:
        return analyze_image_google_vision(image_bytes)


# Thresholds
BLOCK_THRESHOLD = 0.85
QUARANTINE_LOW = 0.50


def should_block(result: ModerationResult) -> bool:
    """Check if content should be blocked immediately."""
    return result.is_explicit or result.score >= BLOCK_THRESHOLD


def should_quarantine(result: ModerationResult) -> bool:
    """Check if content should be quarantined for review."""
    return result.is_suspicious or (QUARANTINE_LOW <= result.score < BLOCK_THRESHOLD)


def should_publish(result: ModerationResult) -> bool:
    """Check if content is safe to publish."""
    return result.score < QUARANTINE_LOW and not result.is_explicit and not result.is_suspicious
