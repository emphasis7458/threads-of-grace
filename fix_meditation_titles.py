#!/usr/bin/env python3
"""
Fix Meditation Titles Script

Identifies meditation HTML files where the title is embedded in the content
(in a <p> tag) rather than properly in the <h1 class="meditation-title-display">.

Usage:
    python fix_meditation_titles.py /path/to/meditations --analyze
    python fix_meditation_titles.py /path/to/meditations --fix
"""

import os
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup


def looks_like_scripture(text):
    """Determine if text looks like scripture readings."""
    if not text:
        return False
    
    colon_count = text.count(':')
    comma_count = text.count(',')
    
    if colon_count >= 2 and comma_count >= 2:
        return True
    
    scripture_pattern = r'\b(Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalm|Proverbs|Ecclesiastes|Song|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation)\s*\d+:\d+'
    
    if re.search(scripture_pattern, text, re.IGNORECASE):
        return True
    
    roman_scripture_pattern = r'\b[I]{1,3}\s*(Samuel|Kings|Chronicles|Corinthians|Thessalonians|Timothy|Peter|John)\s*\d*:?\d*'
    if re.search(roman_scripture_pattern, text, re.IGNORECASE):
        return True
    
    return False


def looks_like_occasion(text):
    """Determine if text looks like a liturgical occasion."""
    if not text:
        return False
    
    if text.isupper() and len(text) > 10:
        return False
    
    text_lower = text.lower()
    
    occasion_patterns = [
        r'year\s*[abc]',
        r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty.first|twenty.second|twenty.third|twenty.fourth|twenty.fifth|twenty.sixth|twenty.seventh|last)\s+sunday',
        r'\bsunday\s+(of|after|in)\s+',
        r'\badvent\s*\d',
        r'\blent\s*\d',
        r'\beaster\s*\d',
        r'\bproper\s*\d',
        r'\bliturgy\s+of\s+the\s+(palms|word)',
        r'\beaster\s+day',
        r'\bchristmas\s+day',
        r'\bpalm\s+sunday',
        r'\bash\s+wednesday',
        r'\bgood\s+friday',
        r'\btrinity\s+sunday',
        r'\bpentecost',
        r'\bthe\s+epiphany',
        r'\bchrist\s+the\s+king',
        r'\ball\s+saints',
        r'\bbaptism\s+of\s+(our\s+)?lord',
        r'\btransfiguration',
        r'\bholy\s+name',
    ]
    
    for pattern in occasion_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False


def is_valid_title(text):
    """Check if text looks like a valid meditation title."""
    if not text:
        return False
    
    if len(text) > 150:
        return False
    
    temp_text = text
    temp_text = re.sub(r'\.\s*\.\s*\.', '...', temp_text)
    temp_text = re.sub(r'\.\.\.', '', temp_text)
    temp_text = re.sub(r'\b(vs|Mr|Mrs|Ms|Dr|St|Rev|Jr|Sr|etc)\.\s', ' ', temp_text, flags=re.IGNORECASE)
    if re.search(r'\.\s+[A-Z]', temp_text):
        return False
    
    if looks_like_scripture(text):
        return False
    
    if looks_like_occasion(text):
        return False
    
    return True


def capitalize_word(word):
    """Capitalize a word, handling leading punctuation like quotes."""
    if not word:
        return word
    
    # Find the first letter
    for i, char in enumerate(word):
        if char.isalpha():
            # Capitalize at position i, lowercase the rest
            return word[:i] + word[i].upper() + word[i+1:].lower()
    
    # No letters found, return as-is
    return word.lower()


def title_case_smart(text):
    """Convert ALL CAPS to Title Case, handling special cases."""
    if not text:
        return text
    
    if not text.isupper():
        return text
    
    lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 
                       'on', 'at', 'to', 'from', 'by', 'in', 'of', 'with', 'as'}
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # Extract the core word without leading/trailing punctuation for checking
        core_word = word.strip('"\'.,;:!?()[]')
        
        if i == 0:
            # First word always capitalized
            result.append(capitalize_word(word))
        elif core_word.lower() in lowercase_words:
            result.append(word.lower())
        else:
            result.append(capitalize_word(word))
    
    return ' '.join(result)


def analyze_meditation_file(filepath):
    """
    Analyze a meditation file to determine if it needs fixing.
    
    Returns:
        dict with keys:
            - needs_fix: bool
            - h1_text: current h1 content
            - title_in_p: title found in <p> tag (if any)
            - p_index: which <p> tag (1-indexed)
            - title_case: title converted to title case
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        result = {
            'needs_fix': False,
            'h1_text': None,
            'title_in_p': None,
            'p_index': None,
            'title_case': None,
            'p_element': None
        }
        
        # Check the h1 title display element
        title_h1 = soup.find('h1', class_='meditation-title-display')
        if title_h1:
            h1_text = title_h1.get_text(strip=True)
            result['h1_text'] = h1_text
            
            # If h1 has a valid title, no fix needed
            if is_valid_title(h1_text):
                return result
        
        # h1 doesn't have valid title - check <p> tags in meditation-content
        content_div = soup.find('div', class_='meditation-content')
        if content_div:
            paragraphs = content_div.find_all('p')
            for i, p in enumerate(paragraphs[:5]):
                p_text = p.get_text(strip=True)
                
                if not p_text:
                    continue
                
                if looks_like_scripture(p_text):
                    continue
                
                if looks_like_occasion(p_text):
                    continue
                
                if is_valid_title(p_text):
                    result['needs_fix'] = True
                    result['title_in_p'] = p_text
                    result['p_index'] = i + 1
                    result['title_case'] = title_case_smart(p_text)
                    result['p_element'] = p
                    return result
        
        return result
    
    except Exception as e:
        return {'needs_fix': False, 'error': str(e)}


def fix_meditation_file(filepath, dry_run=True):
    """
    Fix a meditation file by moving the title from <p> to <h1>.
    
    Returns description of changes made.
    """
    analysis = analyze_meditation_file(filepath)
    
    if not analysis.get('needs_fix'):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Find the h1 and update it
    title_h1 = soup.find('h1', class_='meditation-title-display')
    if not title_h1:
        return {'error': 'No h1.meditation-title-display found'}
    
    # Find the <p> with the title
    content_div = soup.find('div', class_='meditation-content')
    if not content_div:
        return {'error': 'No div.meditation-content found'}
    
    paragraphs = content_div.find_all('p')
    p_index = analysis['p_index'] - 1  # Convert to 0-indexed
    
    if p_index >= len(paragraphs):
        return {'error': f'p_index {p_index} out of range'}
    
    target_p = paragraphs[p_index]
    title_text = target_p.get_text(strip=True)
    
    # Verify this is the right paragraph
    if title_text != analysis['title_in_p']:
        return {'error': f'Title mismatch: expected "{analysis["title_in_p"]}", found "{title_text}"'}
    
    old_h1 = title_h1.get_text(strip=True)
    new_title = analysis['title_case']
    
    changes = {
        'file': filepath.name,
        'old_h1': old_h1,
        'new_h1': new_title,
        'removed_p': analysis['title_in_p'],
        'p_index': analysis['p_index']
    }
    
    if not dry_run:
        # Update h1
        title_h1.string = new_title
        
        # Remove the <p> with the title
        target_p.decompose()
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    
    return changes


def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)
    
    analyze_only = '--analyze' in args
    do_fix = '--fix' in args
    args = [a for a in args if not a.startswith('--')]
    
    if not args:
        print("Error: Please provide the meditations directory path")
        sys.exit(1)
    
    meditations_dir = Path(args[0])
    
    if not meditations_dir.exists():
        print(f"Error: Directory not found: {meditations_dir}")
        sys.exit(1)
    
    print(f"Scanning meditation files in: {meditations_dir}")
    print("=" * 70)
    
    files_needing_fix = []
    files_ok = []
    
    for html_file in sorted(meditations_dir.glob('*.html')):
        analysis = analyze_meditation_file(html_file)
        
        if analysis.get('needs_fix'):
            files_needing_fix.append({
                'file': html_file,
                'analysis': analysis
            })
        else:
            files_ok.append(html_file)
    
    print(f"\nFiles with title properly in <h1>: {len(files_ok)}")
    print(f"Files needing fix (title in <p>):  {len(files_needing_fix)}")
    print("=" * 70)
    
    if not files_needing_fix:
        print("\nNo files need fixing!")
        return
    
    # Show details of files needing fix
    print(f"\nFiles needing fix:\n")
    
    for i, item in enumerate(files_needing_fix):
        filepath = item['file']
        analysis = item['analysis']
        
        print(f"{filepath.stem}:")
        print(f"  Current <h1>: {analysis['h1_text'][:60]}..." if analysis['h1_text'] and len(analysis['h1_text']) > 60 else f"  Current <h1>: {analysis['h1_text']}")
        print(f"  Title in <p{analysis['p_index']}>: {analysis['title_in_p']}")
        print(f"  → New <h1>: {analysis['title_case']}")
        print()
        
        # Limit output in analyze mode
        if analyze_only and i >= 19:
            remaining = len(files_needing_fix) - 20
            print(f"  ... and {remaining} more files\n")
            break
    
    if do_fix:
        print("\n" + "=" * 70)
        print("APPLYING FIXES...")
        print("=" * 70 + "\n")
        
        fixed = 0
        errors = []
        
        for item in files_needing_fix:
            filepath = item['file']
            result = fix_meditation_file(filepath, dry_run=False)
            
            if result and 'error' not in result:
                fixed += 1
                print(f"✓ Fixed: {filepath.stem}")
            elif result and 'error' in result:
                errors.append((filepath.stem, result['error']))
                print(f"✗ Error: {filepath.stem} - {result['error']}")
        
        print(f"\n{'=' * 70}")
        print(f"Fixed {fixed} of {len(files_needing_fix)} files")
        if errors:
            print(f"Errors: {len(errors)}")
    else:
        print("\n" + "=" * 70)
        print("To apply fixes, run with --fix flag")
        print("=" * 70)


if __name__ == '__main__':
    main()
