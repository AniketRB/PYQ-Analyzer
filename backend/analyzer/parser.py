import fitz  # PyMuPDF
import re

def clean_question_text(text):
    """Remove common sub-instructions and metadata from question text"""
    
    # Patterns to remove
    remove_patterns = [
        r'\(Level/CO\)',
        r'Marks\s*:?\s*\d+',
        r'Remember\s*\d*',
        r'Understand\s*\d*',
        r'Apply\s*\d*',
        r'Analyze\s*\d*',
        r'Analysis\s*\d*',
        r'Evaluate\s*\d*',
        r'Create\s*\d*',
        r'\(Remember\)',
        r'\(Understand\)',
        r'\(Apply\)',
        r'\(Analyze\)',
        r'\(Analysis\)',
        r'\(Evaluate\)',
        r'\(Create\)',
        r'\(CO\d+\)',
        r'\[Marks?\s*:?\s*\d+\]',
        r'\(\s*\d+\s*marks?\s*\)',
    ]
    
    cleaned = text
    for pattern in remove_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove multiple spaces and trim
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove trailing numbers (usually marks)
    cleaned = re.sub(r'\s+\d+\s*$', '', cleaned)
    
    return cleaned


def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def parse_questions(text):
    """
    Universal parser for question papers.
    Handles both main questions (Q.1, Q.2) and sub-questions (A), B), C))
    """
    
    # Step 1: Find where actual questions start (skip header/instructions)
    start_patterns = [
        r"\bQ\.?\s*1[\.\):\s]",       # Q.1 or Q1. or Q1:
        r"\bQuestion\s+1\b",           # Question 1
    ]
    
    start_index = 0
    for pattern in start_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start_index = match.start()
            print(f"✓ Found questions starting at position {start_index}")
            break
    
    if start_index > 0:
        text = text[start_index:]
        print(f"✓ Trimmed {start_index} chars of header/instructions")
    
    # Normalize whitespace
    text = re.sub(r'\n{2,}', '\n', text).strip()
    
    # Step 2: Extract ALL sub-questions (A), B), C), etc.)
    # This is the actual content we want
    
    # Pattern matches: A), B), C) or a), b), c) at start of line
    subquestion_pattern = r'\n\s*([A-Za-z])\)\s+'
    
    parts = re.split(subquestion_pattern, text)
    
    questions = []
    
    # parts will be: ['before A)', 'A', 'content of A', 'B', 'content of B', ...]
    # We skip the first part (before any letter) and process pairs
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            letter = parts[i]
            content = parts[i + 1].strip()
            
            # Take only the first line or first sentence (the actual question)
            # Stop at newline or when we see common endings
            lines = content.split('\n')
            question_text = lines[0].strip()
            
            # If first line is very short, take up to 2 lines
            if len(question_text) < 40 and len(lines) > 1:
                question_text = (lines[0] + ' ' + lines[1]).strip()
            
            # Clean metadata
            question_text = clean_question_text(question_text)
            
            # Only keep if it's a real question
            if len(question_text) > 25 and not is_noise(question_text):
                questions.append(question_text)
    
    print(f"✓ Found {len(questions)} valid questions")
    
    # If no sub-questions found, try main question pattern
    if not questions:
        print("! No sub-questions found, trying main question pattern...")
        questions = parse_main_questions(text)
    
    return questions


def parse_main_questions(text):
    """Fallback: parse main questions Q.1, Q.2, etc. if no sub-questions exist"""
    
    pattern = r'\n\s*Q\.?\s*\d+[\.\):\s]+'
    parts = re.split(pattern, text)
    
    questions = []
    for part in parts[1:]:  # Skip first empty part
        lines = part.split('\n')
        question_text = lines[0].strip()
        
        # Skip "Solve Any Two" type instructions
        if 'solve any' in question_text.lower() or 'attempt any' in question_text.lower():
            if len(lines) > 1:
                question_text = lines[1].strip()
        
        question_text = clean_question_text(question_text)
        
        if len(question_text) > 25 and not is_noise(question_text):
            questions.append(question_text)
    
    print(f"✓ Main question pattern found {len(questions)} questions")
    return questions


def is_noise(text):
    """Check if text is noise/instructions rather than a real question"""
    
    text_lower = text.lower()
    
    noise_phrases = [
        'all questions are compulsory',
        'instructions to',
        'max marks',
        'duration:',
        'assume suitable',
        'use of calculator',
        'course outcome',
        'the level of',
        'solve any two',
        'solve any one',
        'attempt any',
        'answer any',
        'end of paper',
        '***',
        'rough work',
    ]
    
    return any(phrase in text_lower for phrase in noise_phrases)
