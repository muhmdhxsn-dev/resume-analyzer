import re


def clean_text(raw_text: str) -> str:
    """
    Performs conservative text cleaning on extracted resume text:
    - Normalizes line endings (\r\n and \r to \n).
    - Removes trailing spaces from each line.
    - Normalizes excessive horizontal whitespace (tabs and multiple spaces into single spaces).
    - Reduces 3+ consecutive blank lines down to 2 newlines (\n\n) to preserve paragraph/section structure.
    - Strips leading and trailing overall whitespace.
    
    Args:
        raw_text (str): Uncleaned extracted document text.
        
    Returns:
        str: Cleaned and normalized text.
    """
    if not raw_text:
        return ""

    # 1. Normalize line endings to \n
    text = raw_text.replace('\r\n', '\n').replace('\r', '\n')

    # 2. Split lines, normalize inline horizontal whitespace, strip trailing space per line
    lines = []
    for line in text.split('\n'):
        # Replace horizontal whitespace (spaces, tabs) with a single space
        normalized_line = re.sub(r'[ \t]+', ' ', line).strip()
        lines.append(normalized_line)

    text = '\n'.join(lines)

    # 3. Collapse 3 or more consecutive newlines down to 2 newlines (\n\n)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 4. Strip overall leading and trailing whitespace
    return text.strip()
