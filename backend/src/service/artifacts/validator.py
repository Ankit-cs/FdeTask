import re

def validate_ship_30_essay(content: str) -> list[str]:
    """
    Validates a generated Ship 30 essay against the required structural rules.
    Returns a list of missing constraints (empty list means valid).
    """
    errors = []
    
    # 1. Word count bounds (~1000-1500 words)
    words = content.split()
    word_count = len(words)
    # Give some leniency to the LLM
    if word_count < 800:
        errors.append(f"Word count is {word_count}. It must be at least 1000 words.")
    elif word_count > 1800:
        errors.append(f"Word count is {word_count}. It must be under 1500 words.")
        
    # 2. Contains at least 2 Markdown headers (##)
    # Using regex to find ^## or higher level headers
    headers = re.findall(r'^#{1,3}\s+.+', content, re.MULTILINE)
    if len(headers) < 2:
        errors.append("Must contain at least 2 Markdown headers for skimmability.")
        
    # 3. Contains bolded text (**)
    bolds = re.findall(r'\*\*.*?\*\*', content)
    if not bolds:
        errors.append("Must contain bolded text (**text**) for emphasis and skimmability.")
        
    # 4. Ends with a distinct takeaway section
    # Check if 'takeaway' appears in the last 20% of the text, often in a header or bold
    last_section = " ".join(words[-int(word_count * 0.2):]).lower()
    if "takeaway" not in last_section:
        errors.append("Must end with a distinct 'Takeaway' section or explicitly mention a takeaway at the end.")
        
    return errors
