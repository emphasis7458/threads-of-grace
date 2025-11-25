#!/usr/bin/env python3
"""
Threads of Grace - Index Generator
Generates three new pages for the website:
1. Index by Title (alphabetical)
2. Index by Scripture Reference  
3. Appendix A - Collection Statistics & Repeated Essays

Usage:
    python generate_indexes.py /path/to/website

The script expects to find:
    - /path/to/website/meditations/*.html (the meditation files)
    - /path/to/website/styles.css (existing stylesheet)

It will create:
    - /path/to/website/title-index.html
    - /path/to/website/scripture-index.html
    - /path/to/website/appendix-statistics.html
"""

import os
import sys
import re
import hashlib
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from html.parser import HTMLParser

# ============================================================================
# CONFIGURATION
# ============================================================================

# Book order for Bible (for sorting scripture references)
BOOK_ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalm",
    "Proverbs", "Ecclesiastes", "Song of Solomon", "Song of Songs",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation"
]

# ============================================================================
# HTML PARSER
# ============================================================================

class MeditationParser(HTMLParser):
    """Parse a meditation HTML file to extract metadata."""
    
    def __init__(self):
        super().__init__()
        self.current_tag = None
        self.current_class = None
        self.data = {
            'title': '',
            'date_display': '',
            'occasion': '',
            'readings': '',
            'content_paragraphs': []
        }
        self.in_content = False
        self.current_content_class = None
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)
        self.current_class = attrs_dict.get('class', '')
        
        if 'meditation-content' in self.current_class:
            self.in_content = True
        if self.in_content and tag == 'p':
            self.current_content_class = self.current_class
    
    def handle_endtag(self, tag):
        if tag == 'div' and self.in_content:
            self.in_content = False
        self.current_tag = None
        self.current_class = None
    
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        
        if self.current_class == 'meditation-title-display':
            self.data['title'] = data
        elif self.current_class == 'meditation-date-display':
            self.data['date_display'] = data
        elif self.current_class == 'meditation-occasion':
            self.data['occasion'] = data
        elif self.current_class == 'meditation-readings':
            self.data['readings'] = data
        elif self.in_content and self.current_tag == 'p' and 'meditation-author' not in (self.current_content_class or ''):
            self.data['content_paragraphs'].append(data)


def parse_meditation_html(filepath):
    """Parse a meditation HTML file and return metadata."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None
    
    # Extract date from filename
    filename = os.path.basename(filepath)
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})\.html', filename)
    if not date_match:
        return None
    
    date_str = date_match.group(1)
    
    # Parse HTML
    parser = MeditationParser()
    try:
        parser.feed(content)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None
    
    # Create content hash for detecting duplicates
    content_text = '\n'.join(parser.data['content_paragraphs'])
    content_hash = hashlib.md5(content_text.encode()).hexdigest()
    
    return {
        'date': date_str,
        'date_display': parser.data['date_display'],
        'title': parser.data['title'],
        'occasion': parser.data['occasion'],
        'readings': parser.data['readings'],
        'content_hash': content_hash,
        'filename': filename
    }


# ============================================================================
# SCRIPTURE PARSING
# ============================================================================

def normalize_book_name(book):
    """Normalize book name for consistent sorting."""
    book = book.strip()
    # Handle Psalms -> Psalm
    book = re.sub(r'^Psalms$', 'Psalm', book)
    # Handle spacing in numbered books
    book = re.sub(r'^(\d)\s*([A-Za-z])', r'\1 \2', book)
    return book


def get_book_sort_key(book_name):
    """Return sort key for a book name."""
    normalized = normalize_book_name(book_name)
    try:
        idx = BOOK_ORDER.index(normalized)
        return (idx, normalized)
    except ValueError:
        # Try partial match
        for i, b in enumerate(BOOK_ORDER):
            if normalized.lower().startswith(b.lower()):
                return (i, normalized)
        return (999, normalized)


def parse_scripture_references(readings_str):
    """
    Parse scripture references from a readings string.
    Example: "Genesis 21:8-21, Psalm 86:1-10, 16-17, Romans 6:1b-11, Matthew 10:24-39"
    """
    if not readings_str:
        return []
    
    references = []
    
    # Pattern to match book+verse patterns
    # Matches: "Genesis 21:8-21" or "Psalm 86:1-10, 16-17" or "1 John 3:1-7"
    pattern = r'(\d?\s*[A-Z][a-z]+(?:\s+of\s+[A-Z][a-z]+)?)\s+([\d:,\-\s]+?)(?=\s*\d?\s*[A-Z][a-z]|$)'
    
    matches = re.findall(pattern, readings_str)
    
    for book, verses in matches:
        book = normalize_book_name(book)
        verses = verses.strip().rstrip(',')
        references.append({
            'book': book,
            'verses': verses,
            'full': f"{book} {verses}"
        })
    
    return references


# ============================================================================
# SEASON HELPERS
# ============================================================================

def get_season_from_occasion(occasion):
    """Extract season from occasion string."""
    occasion_lower = occasion.lower()
    
    if 'advent' in occasion_lower:
        return 'Advent'
    elif 'christmas' in occasion_lower:
        return 'Christmas'
    elif 'epiphany' in occasion_lower:
        return 'Epiphany'
    elif 'lent' in occasion_lower or 'ash wednesday' in occasion_lower:
        return 'Lent'
    elif 'palm' in occasion_lower:
        return 'Holy Week'
    elif 'easter' in occasion_lower:
        return 'Easter'
    elif 'pentecost' in occasion_lower and 'day of' in occasion_lower:
        return 'Pentecost'
    elif 'trinity' in occasion_lower:
        return 'Ordinary Time'
    elif 'pentecost' in occasion_lower or 'ordinary' in occasion_lower or 'proper' in occasion_lower:
        return 'Ordinary Time'
    elif 'all saints' in occasion_lower:
        return 'Special'
    elif 'christ the king' in occasion_lower:
        return 'Special'
    else:
        return 'Other'


def get_lectionary_year(occasion):
    """Extract lectionary year (A, B, C) from occasion string."""
    match = re.search(r'Year\s+([ABC])', occasion)
    if match:
        return match.group(1)
    return None


# ============================================================================
# HTML GENERATION - COMMON ELEMENTS
# ============================================================================

def get_html_header(title, extra_styles=""):
    """Generate common HTML header."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Threads of Grace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <style>
        .index-container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }}
        .index-header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--color-border);
        }}
        .index-header h1 {{
            font-family: var(--font-display);
            font-size: 2.5rem;
            color: var(--color-primary);
            margin-bottom: 0.5rem;
        }}
        .index-header p {{
            font-family: var(--font-body);
            color: var(--color-text-muted);
            font-size: 1.1rem;
        }}
        .index-section {{
            margin-bottom: 2.5rem;
        }}
        .index-section h2 {{
            font-family: var(--font-display);
            font-size: 1.5rem;
            color: var(--color-primary);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--color-border);
        }}
        .index-section h3 {{
            font-family: var(--font-display);
            font-size: 1.2rem;
            color: var(--color-secondary);
            margin: 1.5rem 0 0.75rem 0;
        }}
        .index-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .index-list li {{
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(139, 115, 85, 0.1);
        }}
        .index-list li:last-child {{
            border-bottom: none;
        }}
        .index-list a {{
            color: var(--color-text);
            text-decoration: none;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 1rem;
        }}
        .index-list a:hover {{
            color: var(--color-primary);
        }}
        .index-title {{
            font-family: var(--font-body);
            flex: 1;
        }}
        .index-date {{
            font-family: var(--font-body);
            color: var(--color-text-muted);
            font-size: 0.9rem;
            white-space: nowrap;
        }}
        .index-occasion {{
            font-size: 0.85rem;
            color: var(--color-text-muted);
            margin-left: 1rem;
        }}
        .letter-nav {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            justify-content: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--color-cream);
            border-radius: 4px;
        }}
        .letter-nav a {{
            padding: 0.25rem 0.5rem;
            color: var(--color-primary);
            text-decoration: none;
            font-family: var(--font-display);
        }}
        .letter-nav a:hover {{
            text-decoration: underline;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        .stat-card {{
            background: var(--color-cream);
            padding: 1.5rem;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-number {{
            font-family: var(--font-display);
            font-size: 2.5rem;
            color: var(--color-primary);
            display: block;
        }}
        .stat-label {{
            font-family: var(--font-body);
            color: var(--color-text-muted);
            font-size: 0.9rem;
        }}
        .reuse-group {{
            background: var(--color-cream);
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }}
        .reuse-title {{
            font-family: var(--font-display);
            font-size: 1.1rem;
            color: var(--color-primary);
            margin-bottom: 0.5rem;
        }}
        .reuse-dates {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .reuse-dates li {{
            padding: 0.25rem 0;
            font-size: 0.95rem;
        }}
        .reuse-dates a {{
            color: var(--color-text);
            text-decoration: none;
        }}
        .reuse-dates a:hover {{
            color: var(--color-primary);
        }}
        .scripture-book {{
            margin-bottom: 2rem;
        }}
        .scripture-ref {{
            font-style: italic;
            color: var(--color-secondary);
        }}
        {extra_styles}
    </style>
</head>
<body>
    <div class="grain-overlay"></div>
    
    <header class="site-header">
        <div class="container">
            <h1 class="site-title"><a href="index.html">Threads of Grace</a></h1>
            <p class="site-subtitle">Meditations on Scripture and the Spiritual Life</p>
        </div>
    </header>

    <main class="index-container">
'''


def get_html_footer():
    """Generate common HTML footer."""
    return '''
    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>
'''


# ============================================================================
# GENERATE TITLE INDEX
# ============================================================================

def normalize_title_for_grouping(title):
    """
    Normalize a title for grouping purposes.
    Strips trailing punctuation and normalizes case to find titles that are
    essentially the same but differ only in punctuation or case.
    """
    # Strip trailing punctuation (but keep internal punctuation like apostrophes)
    normalized = title.strip()
    while normalized and normalized[-1] in '!?.,:;':
        normalized = normalized[:-1]
    # Normalize to lowercase for comparison
    return normalized.lower().strip()

def generate_title_index(meditations, output_path):
    """Generate the alphabetical title index page with grouped repeated titles."""
    
    # Group meditations by normalized title
    title_groups = defaultdict(list)
    for med in meditations:
        norm_title = normalize_title_for_grouping(med['title'])
        title_groups[norm_title].append(med)
    
    # For each group, pick the "canonical" title (prefer one with punctuation, or most common)
    # and sort the meditations by date
    processed_groups = []
    for norm_title, meds in title_groups.items():
        # Sort meditations by date
        meds_sorted = sorted(meds, key=lambda m: m['date'])
        
        # Pick canonical title - prefer the version used most recently, or with punctuation
        # Actually, let's use the most common version, or first one if tie
        title_counts = defaultdict(int)
        for m in meds:
            title_counts[m['title']] += 1
        canonical_title = max(title_counts.keys(), key=lambda t: (title_counts[t], t))
        
        processed_groups.append({
            'canonical_title': canonical_title,
            'norm_title': norm_title,
            'meditations': meds_sorted,
            'count': len(meds_sorted)
        })
    
    # Sort groups by canonical title (case-insensitive)
    processed_groups.sort(key=lambda g: g['canonical_title'].upper())
    
    # Group by first letter
    by_letter = defaultdict(list)
    for group in processed_groups:
        title = group['canonical_title']
        first_char = title[0].upper() if title else '?'
        if first_char.isalpha():
            by_letter[first_char].append(group)
        else:
            by_letter['#'].append(group)
    
    # Count unique titles
    unique_count = len(processed_groups)
    
    # Build letter navigation
    letters = sorted(by_letter.keys())
    letter_nav = '<nav class="letter-nav">\n'
    for letter in letters:
        letter_nav += f'        <a href="#letter-{letter}">{letter}</a>\n'
    letter_nav += '    </nav>\n'
    
    # Build content
    content = f'''
        <div class="index-header">
            <h1>Index by Title</h1>
            <p>{unique_count} unique titles across {len(meditations)} meditations</p>
        </div>
        
        {letter_nav}
'''
    
    for letter in letters:
        content += f'''
        <section class="index-section" id="letter-{letter}">
            <h2>{letter}</h2>
            <ul class="index-list">
'''
        for group in by_letter[letter]:
            if group['count'] == 1:
                # Single meditation - simple format
                med = group['meditations'][0]
                date_formatted = format_date_short(med['date'])
                content += f'''                <li>
                    <a href="meditations/{med['filename']}">
                        <span class="index-title">{group['canonical_title']}</span>
                        <span class="index-date">{date_formatted}</span>
                    </a>
                </li>
'''
            else:
                # Multiple meditations with same title - group them
                content += f'''                <li class="grouped-title">
                    <div class="index-title">{group['canonical_title']}</div>
                    <ul class="title-dates">
'''
                for med in group['meditations']:
                    date_formatted = format_date_short(med['date'])
                    # Get short occasion
                    occasion = med.get('occasion', '')
                    occasion_short = occasion.split('•')[0].strip() if '•' in occasion else occasion
                    # Truncate if too long
                    if len(occasion_short) > 50:
                        occasion_short = occasion_short[:47] + '...'
                    content += f'''                        <li>
                            <a href="meditations/{med['filename']}">
                                <span class="grouped-date">{date_formatted}</span>
                                <span class="grouped-occasion">{occasion_short}</span>
                            </a>
                        </li>
'''
                content += '''                    </ul>
                </li>
'''
        content += '''            </ul>
        </section>
'''
    
    # Write file
    extra_styles = '''
        .grouped-title {
            padding: 0.75rem 0;
        }
        .grouped-title > .index-title {
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        .title-dates {
            list-style: none;
            padding: 0;
            margin: 0 0 0 1.5rem;
        }
        .title-dates li {
            padding: 0.25rem 0;
            border-bottom: none;
        }
        .title-dates a {
            display: flex;
            gap: 1rem;
            color: var(--color-text-muted);
            font-size: 0.9rem;
        }
        .title-dates a:hover {
            color: var(--color-primary);
        }
        .grouped-date {
            white-space: nowrap;
            min-width: 100px;
        }
        .grouped-occasion {
            color: var(--color-text-muted);
            font-style: italic;
        }
    '''
    html = get_html_header("Index by Title", extra_styles) + content + get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Generated: {output_path}")


# ============================================================================
# GENERATE SCRIPTURE INDEX
# ============================================================================

def generate_scripture_index(meditations, output_path):
    """Generate the scripture reference index page."""
    
    # Build index: book -> reference -> list of meditations
    scripture_index = defaultdict(lambda: defaultdict(list))
    
    for med in meditations:
        refs = parse_scripture_references(med['readings'])
        for ref in refs:
            book = ref['book']
            full_ref = ref['full']
            scripture_index[book][full_ref].append(med)
    
    # Sort books by biblical order
    sorted_books = sorted(scripture_index.keys(), key=get_book_sort_key)
    
    # Build book navigation
    book_nav = '<nav class="letter-nav">\n'
    for book in sorted_books:
        book_id = book.replace(' ', '-').lower()
        book_nav += f'        <a href="#book-{book_id}">{book}</a>\n'
    book_nav += '    </nav>\n'
    
    # Count total references
    total_refs = sum(len(refs) for refs in scripture_index.values())
    
    # Build content
    content = f'''
        <div class="index-header">
            <h1>Index by Scripture</h1>
            <p>Meditations organized by the {total_refs} scripture passages they reflect upon</p>
        </div>
        
        {book_nav}
'''
    
    for book in sorted_books:
        book_id = book.replace(' ', '-').lower()
        refs = scripture_index[book]
        
        # Sort references by verse number (roughly)
        def ref_sort_key(ref):
            # Extract first chapter:verse
            match = re.search(r'(\d+):?(\d*)', ref)
            if match:
                chap = int(match.group(1))
                verse = int(match.group(2)) if match.group(2) else 0
                return (chap, verse)
            return (999, 999)
        
        sorted_refs = sorted(refs.keys(), key=ref_sort_key)
        
        content += f'''
        <section class="index-section scripture-book" id="book-{book_id}">
            <h2>{book}</h2>
            <ul class="index-list">
'''
        for ref in sorted_refs:
            meds = refs[ref]
            # Sort meditations by date
            meds_sorted = sorted(meds, key=lambda m: m['date'])
            
            for med in meds_sorted:
                date_formatted = format_date_short(med['date'])
                # Extract just the verse part for display
                verse_part = ref.replace(book, '').strip()
                content += f'''                <li>
                    <a href="meditations/{med['filename']}">
                        <span class="index-title"><span class="scripture-ref">{verse_part}</span> — {med['title']}</span>
                        <span class="index-date">{date_formatted}</span>
                    </a>
                </li>
'''
        content += '''            </ul>
        </section>
'''
    
    # Write file
    html = get_html_header("Index by Scripture") + content + get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Generated: {output_path}")


# ============================================================================
# GENERATE STATISTICS APPENDIX
# ============================================================================

def generate_statistics_appendix(meditations, output_path):
    """Generate the collection statistics and repeated essays appendix."""
    
    # Calculate statistics
    total_meditations = len(meditations)
    
    # Find repeated essays (same content hash)
    by_hash = defaultdict(list)
    for med in meditations:
        by_hash[med['content_hash']].append(med)
    
    unique_essays = len(by_hash)
    reused_count = sum(1 for h, meds in by_hash.items() if len(meds) > 1)
    reuse_instances = total_meditations - unique_essays
    
    # Group repeated essays
    repeated_essays = [(meds[0]['title'], sorted(meds, key=lambda m: m['date'])) 
                       for h, meds in by_hash.items() if len(meds) > 1]
    repeated_essays.sort(key=lambda x: x[1][0]['date'])  # Sort by first use date
    
    # Statistics by year
    by_year = defaultdict(int)
    for med in meditations:
        year = med['date'][:4]
        by_year[year] += 1
    
    # Statistics by season
    by_season = defaultdict(int)
    for med in meditations:
        season = get_season_from_occasion(med['occasion'])
        by_season[season] += 1
    
    # Statistics by lectionary year
    by_lectionary = defaultdict(int)
    for med in meditations:
        ly = get_lectionary_year(med['occasion'])
        if ly:
            by_lectionary[ly] += 1
    
    # Build content
    content = f'''
        <div class="index-header">
            <h1>Appendix A: Collection Statistics</h1>
            <p>A detailed look at sixteen years of weekly meditations</p>
        </div>
        
        <section class="index-section">
            <h2>Overview</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number">{total_meditations}</span>
                    <span class="stat-label">Total Meditations</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{unique_essays}</span>
                    <span class="stat-label">Unique Essays</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{reuse_instances}</span>
                    <span class="stat-label">Thoughtful Reuses</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">16</span>
                    <span class="stat-label">Years (2007–2024)</span>
                </div>
            </div>
            
            <p style="margin-top: 1.5rem; font-style: italic; color: var(--color-text-muted);">
                The three-year lectionary cycle means the same liturgical occasions recur regularly. 
                Pat thoughtfully reused {reuse_instances} meditations when the same readings returned, 
                while also writing fresh reflections for many recurring occasions. This intentional 
                curation reflects her pastoral wisdom in knowing when a message bears repeating.
            </p>
        </section>
        
        <section class="index-section">
            <h2>By Calendar Year</h2>
            <ul class="index-list">
'''
    
    for year in sorted(by_year.keys()):
        count = by_year[year]
        content += f'''                <li>
                    <span class="index-title">{year}</span>
                    <span class="index-date">{count} meditations</span>
                </li>
'''
    
    content += '''            </ul>
        </section>
        
        <section class="index-section">
            <h2>By Liturgical Season</h2>
            <ul class="index-list">
'''
    
    season_order = ['Advent', 'Christmas', 'Epiphany', 'Lent', 'Holy Week', 'Easter', 'Pentecost', 'Ordinary Time', 'Special', 'Other']
    for season in season_order:
        if season in by_season:
            count = by_season[season]
            content += f'''                <li>
                    <span class="index-title">{season}</span>
                    <span class="index-date">{count} meditations</span>
                </li>
'''
    
    content += '''            </ul>
        </section>
        
        <section class="index-section">
            <h2>By Lectionary Year</h2>
            <ul class="index-list">
'''
    
    for ly in ['A', 'B', 'C']:
        if ly in by_lectionary:
            count = by_lectionary[ly]
            content += f'''                <li>
                    <span class="index-title">Year {ly}</span>
                    <span class="index-date">{count} meditations</span>
                </li>
'''
    
    content += f'''            </ul>
        </section>
        
        <section class="index-section">
            <h2>Repeated Essays</h2>
            <p style="margin-bottom: 1.5rem; color: var(--color-text-muted);">
                These {len(repeated_essays)} essays were used more than once across the collection, 
                typically when the same liturgical occasion returned in the three-year lectionary cycle.
            </p>
'''
    
    for title, meds in repeated_essays:
        content += f'''            <div class="reuse-group">
                <div class="reuse-title">{title}</div>
                <ul class="reuse-dates">
'''
        for med in meds:
            date_formatted = format_date_short(med['date'])
            occasion_short = med['occasion'].split('•')[0].strip() if '•' in med['occasion'] else med['occasion']
            content += f'''                    <li>
                        <a href="meditations/{med['filename']}">{date_formatted}</a>
                        <span class="index-occasion">{occasion_short}</span>
                    </li>
'''
        content += '''                </ul>
            </div>
'''
    
    content += '''        </section>
'''
    
    # Write file
    html = get_html_header("Collection Statistics") + content + get_html_footer()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Generated: {output_path}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_date_short(date_str):
    """Convert YYYY-MM-DD to shorter format like 'Jun 22, 2008'."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%b %d, %Y')
    except:
        return date_str


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_indexes.py /path/to/website")
        print("\nThe website folder should contain a 'meditations' subfolder with HTML files.")
        sys.exit(1)
    
    website_path = Path(sys.argv[1])
    meditations_path = website_path / 'meditations'
    
    if not meditations_path.exists():
        print(f"Error: Could not find meditations folder at {meditations_path}")
        sys.exit(1)
    
    # Parse all meditation files
    print(f"Scanning {meditations_path}...")
    meditations = []
    
    for filepath in sorted(meditations_path.glob('*.html')):
        med = parse_meditation_html(filepath)
        if med:
            meditations.append(med)
    
    print(f"Found {len(meditations)} meditations")
    
    if not meditations:
        print("No meditations found. Exiting.")
        sys.exit(1)
    
    # Generate the three index pages
    print("\nGenerating indexes...")
    
    generate_title_index(meditations, website_path / 'title-index.html')
    generate_scripture_index(meditations, website_path / 'scripture-index.html')
    generate_statistics_appendix(meditations, website_path / 'appendix-statistics.html')
    
    print("\nDone! Generated 3 new pages:")
    print("  - title-index.html")
    print("  - scripture-index.html") 
    print("  - appendix-statistics.html")
    print("\nRemember to add links to these pages from your main navigation!")


if __name__ == '__main__':
    main()
