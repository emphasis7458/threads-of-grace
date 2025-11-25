#!/usr/bin/env python3
"""
Fix title issues in Threads of Grace meditation HTML files.

Fixes applied:
1. Convert ALL CAPS to Title Case
2. Remove space before ! and ? punctuation
3. Fix multiple consecutive spaces
4. Fix trailing/leading whitespace in titles
5. Fix underscore separators

Usage:
    python fix_titles.py /path/to/meditations [--dry-run]
    
    --dry-run: Show what would be changed without modifying files
"""

import os
import sys
import re
from pathlib import Path
from collections import defaultdict

# Words that should remain lowercase in titles (unless first word)
LOWERCASE_WORDS = {
    'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 
    'from', 'by', 'of', 'in', 'with', 'as', 'is', 'it', 'vs', 'yet', 'so'
}

def smart_title_case(title):
    """
    Convert a title to proper Title Case with smart handling of:
    - Lowercase words (a, an, the, etc.)
    - Roman numerals
    - Words in quotes
    - Contractions and possessives
    """
    # First, handle the underscore separator issue
    if '_____' in title:
        title = re.sub(r'_+', ' / ', title)
    
    # Remove space before punctuation
    title = re.sub(r'\s+!', '!', title)
    title = re.sub(r'\s+\?', '?', title)
    
    # Fix multiple spaces
    title = re.sub(r'\s{2,}', ' ', title)
    
    # Strip whitespace
    title = title.strip()
    
    # Split into words while preserving punctuation
    words = title.split()
    result = []
    
    for i, word in enumerate(words):
        # Extract any leading punctuation
        leading_punct = ''
        core_word = word
        while core_word and core_word[0] in '"\'""''(':
            leading_punct += core_word[0]
            core_word = core_word[1:]
        
        # Extract any trailing punctuation
        trailing_punct = ''
        while core_word and core_word[-1] in '"\'""'').,!?;:':
            trailing_punct = core_word[-1] + trailing_punct
            core_word = core_word[:-1]
        
        if not core_word:
            result.append(word)
            continue
        
        # Check for Roman numerals
        if core_word.upper() in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']:
            # But "I" alone as pronoun should be capitalized, not treated as Roman numeral
            # Context: if surrounded by other words, likely pronoun
            if core_word.upper() == 'I' and len(words) > 1:
                core_word = 'I'  # Pronoun
            else:
                core_word = core_word.upper()
        # Check for lowercase words (not first word, not after colon/em-dash)
        elif i > 0 and core_word.lower() in LOWERCASE_WORDS:
            # Check if previous word ended with colon or em-dash
            if result and not result[-1].rstrip().endswith((':','—', '–')):
                core_word = core_word.lower()
            else:
                core_word = core_word.capitalize()
        # Check for contractions and possessives
        elif "'" in core_word or "'" in core_word:
            # Handle contractions like "God's", "Don't", "It's"
            parts = re.split(r"(['']\w*)", core_word)
            core_word = ''
            for j, part in enumerate(parts):
                if part.startswith("'") or part.startswith("'"):
                    core_word += part.lower()
                elif j == 0:
                    core_word += part.capitalize()
                else:
                    core_word += part.lower()
        # Handle hyphenated words
        elif '-' in core_word or '–' in core_word or '—' in core_word:
            # Split on any dash type
            parts = re.split(r'([-–—])', core_word)
            core_word = ''
            for part in parts:
                if part in ['-', '–', '—']:
                    core_word += part
                else:
                    core_word += part.capitalize()
        else:
            # Standard capitalization
            core_word = core_word.capitalize()
        
        result.append(leading_punct + core_word + trailing_punct)
    
    return ' '.join(result)

def extract_title(html_content):
    """Extract the title from the meditation HTML."""
    match = re.search(r'<h1 class="meditation-title-display">(.*?)</h1>', html_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def fix_title(title):
    """Apply fixes to a title and return (fixed_title, list_of_changes)."""
    changes = []
    original = title
    
    # Apply smart title case (this also handles spacing/punctuation fixes)
    fixed = smart_title_case(title)
    
    # Determine what changed
    if title != fixed:
        if title.isupper() or sum(1 for c in title if c.isupper()) > len(title) * 0.6:
            changes.append("Converted from ALL CAPS to Title Case")
        if re.search(r'\s+[!?]', title):
            changes.append("Removed space before punctuation")
        if '  ' in title:
            changes.append("Fixed multiple spaces")
        if '_____' in title:
            changes.append("Replaced underscore line with ' / '")
        if title.strip() != title:
            changes.append("Removed leading/trailing whitespace")
        if not changes:
            changes.append("Adjusted capitalization")
    
    return fixed, changes

def check_for_issues(title, filename):
    """Check for issues that need manual review."""
    issues = []
    
    # Check for EMBED or other Word artifacts
    if 'EMBED' in title.upper() or 'Word.' in title or 'Picture.' in title:
        issues.append("Contains Word embedding artifact")
    
    # Check for unusual characters
    unusual = re.findall(r'[^\w\s\'"".,,!?;:\-–—/()&''"]', title)
    if unusual:
        issues.append(f"Contains unusual characters: {set(unusual)}")
    
    # Check for very long titles (might indicate a problem)
    if len(title) > 80:
        issues.append(f"Very long title ({len(title)} chars)")
    
    # Check for paths or file-like patterns
    if '\\' in title or re.search(r'[A-Z]:', title):
        issues.append("Contains path-like characters")
    
    return issues

def process_file(filepath, dry_run=False):
    """Process a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    title = extract_title(content)
    if not title:
        return None, None, ["Could not extract title"]
    
    fixed_title, changes = fix_title(title)
    issues = check_for_issues(fixed_title, filepath.name)
    
    if changes and not dry_run:
        # Replace the title in the h1 tag
        old_h1 = f'<h1 class="meditation-title-display">{title}</h1>'
        new_h1 = f'<h1 class="meditation-title-display">{fixed_title}</h1>'
        content = content.replace(old_h1, new_h1)
        
        # Also update the <title> tag
        old_title_match = re.search(r'<title>(.*?)</title>', content)
        if old_title_match and title in old_title_match.group(1):
            old_tag = old_title_match.group(0)
            new_tag = old_tag.replace(title, fixed_title)
            content = content.replace(old_tag, new_tag)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return title, fixed_title if changes else None, changes + issues

def normalize_for_grouping(title):
    """
    Normalize a title for grouping comparison.
    Strips trailing punctuation and normalizes case.
    """
    normalized = title.strip()
    while normalized and normalized[-1] in '!?.,:;':
        normalized = normalized[:-1]
    return normalized.lower().strip()


def find_near_match_titles(all_titles):
    """
    Find titles that would be grouped together due to punctuation differences.
    Returns dict: normalized_title -> list of (filename, actual_title) tuples
    """
    groups = defaultdict(list)
    for filename, title in all_titles:
        norm = normalize_for_grouping(title)
        groups[norm].append((filename, title))
    
    # Only return groups with multiple DIFFERENT titles
    near_matches = {}
    for norm, items in groups.items():
        unique_titles = set(title for _, title in items)
        if len(unique_titles) > 1:
            near_matches[norm] = items
    
    return near_matches


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_titles.py /path/to/meditations [--dry-run]")
        sys.exit(1)
    
    meditations_dir = Path(sys.argv[1])
    dry_run = '--dry-run' in sys.argv
    
    if not meditations_dir.exists():
        print(f"Error: Directory not found: {meditations_dir}")
        sys.exit(1)
    
    if dry_run:
        print("=" * 70)
        print("DRY RUN - No files will be modified")
        print("=" * 70)
    
    html_files = sorted(meditations_dir.glob('*.html'))
    
    files_fixed = 0
    files_with_issues = 0
    
    print(f"\nProcessing {len(html_files)} files...\n")
    
    # Track issues for summary
    issues_found = []
    
    # Collect all titles for near-match analysis
    all_titles = []
    
    for filepath in html_files:
        original, fixed, notes = process_file(filepath, dry_run)
        
        if original is None:
            issues_found.append((filepath.name, None, notes))
            continue
        
        # Track the final title for near-match analysis
        final_title = fixed if fixed else original
        all_titles.append((filepath.name, final_title))
        
        # Separate fixes from manual issues
        fix_notes = [n for n in notes if any(keyword in n for keyword in [
            "Converted", "Removed space", "Fixed multiple", "Replaced underscore",
            "whitespace", "capitalization"
        ])]
        manual_notes = [n for n in notes if n not in fix_notes]
        
        # Report fixes
        if fixed:
            files_fixed += 1
            action = "Would fix" if dry_run else "Fixed"
            print(f"{action}: {filepath.name}")
            print(f"  Before: {original}")
            print(f"  After:  {fixed}")
            print()
        
        # Track issues needing manual review
        if manual_notes:
            files_with_issues += 1
            issues_found.append((filepath.name, original or fixed, manual_notes))
    
    # Find near-match titles (differ only by punctuation)
    near_matches = find_near_match_titles(all_titles)
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total files processed: {len(html_files)}")
    print(f"Files {'that would be' if dry_run else ''} fixed: {files_fixed}")
    print(f"Files needing manual review: {files_with_issues}")
    print(f"Title groups differing only by punctuation: {len(near_matches)}")
    
    if issues_found:
        print()
        print("=" * 70)
        print("FILES NEEDING MANUAL REVIEW")
        print("=" * 70)
        for filename, title, notes in issues_found:
            print(f"\n{filename}:")
            if title:
                print(f"  Title: {title}")
            for note in notes:
                print(f"  - {note}")
    
    if near_matches:
        print()
        print("=" * 70)
        print("TITLES DIFFERING ONLY BY PUNCTUATION")
        print("(Review these - they may be DIFFERENT essays that should NOT be grouped)")
        print("=" * 70)
        
        for norm_title, items in sorted(near_matches.items()):
            print(f"\nBase title: \"{norm_title}\"")
            # Group by actual title
            by_title = defaultdict(list)
            for filename, title in items:
                by_title[title].append(filename)
            
            for title, filenames in sorted(by_title.items()):
                print(f"  \"{title}\" ({len(filenames)} uses)")
                for fn in sorted(filenames)[:3]:  # Show first 3 dates
                    print(f"    - {fn}")
                if len(filenames) > 3:
                    print(f"    ... and {len(filenames) - 3} more")
    
    if dry_run and files_fixed > 0:
        print()
        print("=" * 70)
        print("Run without --dry-run to apply these fixes")
        print("=" * 70)


if __name__ == '__main__':
    main()
