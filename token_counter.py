try:
    import tiktoken
    _encoding = tiktoken.get_encoding("cl100k_base")
except Exception:
    _encoding = None


def count_token(text):
    """Return token count. Use tiktoken if available, otherwise fall back to simple split."""
    if _encoding:
        return len(_encoding.encode(text))
    # Fallback: approximate tokens by splitting on whitespace
    if not text:
        return 0
    return len(text.split())