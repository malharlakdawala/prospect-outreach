"""GDPR compliance checks for generated emails."""

import re


def check_gdpr_compliance(email_body: str) -> dict:
    """Check email body for basic GDPR compliance indicators."""
    issues = []

    # Check for opt-out language
    opt_out_patterns = [
        r"unsubscribe",
        r"opt.?out",
        r"stop (receiving|sending|these)",
        r"remove (me|you)",
        r"no longer (wish|want)",
        r"don.?t (want|wish) to (receive|hear)",
    ]
    has_opt_out = any(
        re.search(pattern, email_body, re.IGNORECASE)
        for pattern in opt_out_patterns
    )
    if not has_opt_out:
        issues.append("No opt-out/unsubscribe language detected")

    # Check for deceptive subject patterns (checked separately)
    # Check for excessive claims
    deceptive_patterns = [
        r"guaranteed",
        r"100%",
        r"risk.?free",
        r"no obligation",
        r"act now",
        r"limited time",
        r"exclusive offer",
    ]
    for pattern in deceptive_patterns:
        if re.search(pattern, email_body, re.IGNORECASE):
            issues.append(f"Potentially deceptive language detected: '{pattern}'")

    return {
        "has_opt_out": has_opt_out,
        "issues": issues,
        "compliant": len(issues) == 0,
    }
