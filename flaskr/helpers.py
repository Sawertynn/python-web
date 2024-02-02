def abbreviate(text: str, max_length: int = 100):
    if len(text) <= max_length:
        return text
    
    # get whole words that fit into max_length cap
    capped = text[:max_length].rsplit(' ', 1)[0]

    return capped + '...'
