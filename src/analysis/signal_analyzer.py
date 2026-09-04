from src.signal_extractor import extract_signals


# =========================================================
# CONFIGURATION
# =========================================================

MIN_SIGNAL_LENGTH = 15


# =========================================================
# HELPERS
# =========================================================

def _clean_text(value) -> str:
    """Return normalized text."""

    if value is None:
        return ""

    return " ".join(str(value).split()).strip()


def _signal_key(signal: dict) -> str:
    """
    Create a lightweight fingerprint for duplicate detection.

    We intentionally use the semantic signal rather than the
    complete dictionary because scores and source metadata
    can differ while the underlying signal is identical.
    """

    signal_text = _clean_text(
        signal.get("signal", "")
    ).lower()

    behavior = _clean_text(
        signal.get("behavior_change", "")
    ).lower()

    return f"{signal_text}|{behavior}"


def _is_usable_signal(signal: dict) -> bool:
    """
    Check whether a signal contains enough intelligence
    to be passed to trend detection.
    """

    if not isinstance(signal, dict):
        return False

    # -----------------------------------------------------
    # Extractor explicitly marks invalid responses
    # -----------------------------------------------------

    if signal.get("valid") is False:
        return False

    # -----------------------------------------------------
    # Required intelligence fields
    # -----------------------------------------------------

    observation = _clean_text(
        signal.get("observation")
    )

    signal_text = _clean_text(
        signal.get("signal")
    )

    evidence = _clean_text(
        signal.get("evidence")
    )

    if len(observation) < MIN_SIGNAL_LENGTH:
        return False

    if len(signal_text) < MIN_SIGNAL_LENGTH:
        return False

    if len(evidence) < MIN_SIGNAL_LENGTH:
        return False

    return True


# =========================================================
# SIGNAL ANALYSIS
# =========================================================

def extract_signals_from_results(
    results: list[dict]
) -> list[dict]:
    """
    Convert multiple web research results into a clean,
    validated signal set.

    Pipeline:

        Web Results
             ↓
        Signal Extraction
             ↓
        Validation
             ↓
        Duplicate Removal
             ↓
        Clean Signals
             ↓
        Trend Detector
    """

    if not results:
        return []

    signals = []
    seen_signals = set()

    # =====================================================
    # PROCESS EACH SOURCE
    # =====================================================

    for result in results:

        if not isinstance(result, dict):
            continue

        source_title = _clean_text(
            result.get("title")
        )

        source_url = _clean_text(
            result.get("url")
        )

        source_image_url = _clean_text(
            result.get("source_image_url")
        )

        try:

            signal = extract_signals(result)

            # -------------------------------------------------
            # Invalid extraction
            # -------------------------------------------------

            if not _is_usable_signal(signal):
                continue

            # -------------------------------------------------
            # Restore authoritative source metadata
            # -------------------------------------------------

            signal["source_title"] = source_title
            signal["source_url"] = source_url
            signal["source_image_url"] = source_image_url

            # -------------------------------------------------
            # Duplicate detection
            # -------------------------------------------------

            key = _signal_key(signal)

            if not key or key in seen_signals:
                continue

            seen_signals.add(key)

            # -------------------------------------------------
            # Final clean marker
            # -------------------------------------------------

            signal["valid"] = True

            signals.append(signal)

        except Exception:
            # A failed source should NOT become a fake signal.
            #
            # We intentionally skip it instead of sending
            # error dictionaries to the trend detector.
            continue

    return signals