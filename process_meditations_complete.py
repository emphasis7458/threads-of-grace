#!/usr/bin/env python3
"""
Threads of Grace - Complete Meditation Processor
================================================

A standalone script to process meditation text files and update the website.
Run this locally - no Claude interaction needed for routine batches.

Usage:
    python process_meditations_complete.py <input_folder> <website_folder> [--liturgical-db <path>]

Example:
    python process_meditations_complete.py ./Year_C_2013 ./threads-of-grace-website --liturgical-db ./liturgical_database.json

The script will:
1. Process all .txt files in the input folder
2. Generate HTML pages for new meditations
3. Update meditations-data.json
4. Regenerate all index pages (chronological.html, season pages)
5. Report what was added
"""

import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path


# =============================================================================
# TEXT CLEANING FUNCTIONS
# =============================================================================

def clean_author_lines(text):
    """Remove author signatures and other unwanted content from the end of text."""
    lines = text.strip().split('\n')
    
    # Patterns to remove from the end
    author_patterns = [
        r'^Pat\s*Horn\s*$',
        r'^Audrey\s*(Bruno\s*)?Horn\s*$',
        r'^Audry\s*Horn\s*Bruno\s*$',
        r'^Elizabeth\s*(Templeton\s*)?Horn\s*$',
        r'^Elizabeth\s*Horn\s*Templeton\s*$',
        r'^Author\s*$',
        r'^Photographer\s*$',
        r'^\[.*\]\s*$',  # Lines that are just brackets with content
        r'^\[.*photo.*\].*$',  # Photo credit lines
    ]
    
    # Remove trailing empty lines and author lines
    while lines:
        last_line = lines[-1].strip()
        if not last_line:
            lines.pop()
            continue
        
        matched = False
        for pattern in author_patterns:
            if re.match(pattern, last_line, re.IGNORECASE):
                lines.pop()
                matched = True
                break
        
        if not matched:
            break
    
    return '\n'.join(lines)


def fix_roman_numerals(text):
    """Fix lowercase Roman numerals in book names."""
    book_patterns = [
        (r'\bIi\s+', 'II '),
        (r'\bIii\s+', 'III '),
        (r'\bi\s+Corinthians', 'I Corinthians'),
        (r'\bii\s+Corinthians', 'II Corinthians'),
        (r'\bi\s+Thessalonians', 'I Thessalonians'),
        (r'\bii\s+Thessalonians', 'II Thessalonians'),
        (r'\bi\s+Timothy', 'I Timothy'),
        (r'\bii\s+Timothy', 'II Timothy'),
        (r'\bi\s+Peter', 'I Peter'),
        (r'\bii\s+Peter', 'II Peter'),
        (r'\bi\s+John', 'I John'),
        (r'\bii\s+John', 'II John'),
        (r'\biii\s+John', 'III John'),
        (r'\bi\s+Kings', 'I Kings'),
        (r'\bii\s+Kings', 'II Kings'),
        (r'\bi\s+Samuel', 'I Samuel'),
        (r'\bii\s+Samuel', 'II Samuel'),
        (r'\bi\s+Chronicles', 'I Chronicles'),
        (r'\bii\s+Chronicles', 'II Chronicles'),
    ]
    
    for pattern, replacement in book_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def fix_year_designation(text):
    """Remove 'R' from Year designations like 'Year R C' -> 'Year C'."""
    return re.sub(r'Year\s*R\s*([ABC])', r'Year \1', text)


# =============================================================================
# FILE PARSING
# =============================================================================

def parse_filename(filename):
    """Extract date from filename. Returns date string or None."""
    match = re.match(r'(\d{4}-\d{2}-\d{2})_', filename)
    if match:
        return match.group(1)
    return None


def parse_meditation_file(filepath):
    """
    Parse a meditation text file and extract its components.
    
    Expected format:
        Line 1: Date (e.g., "December 16, 2007")
        Line 2: Occasion (e.g., "Third Sunday of Advent, Year A")
        Line 3: Scripture readings
        Line 4: [blank]
        Line 5: TITLE
        Line 6+: Body paragraphs
    
    Returns dict with: date_line, occasion_line, readings, title, paragraphs
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return None
    
    # Clean the content
    content = clean_author_lines(content)
    content = fix_roman_numerals(content)
    
    lines = content.strip().split('\n')
    
    if len(lines) < 4:
        return None
    
    # First line: Date
    date_line = lines[0].strip()
    
    # Second line: Occasion
    occasion_line = fix_year_designation(lines[1].strip())
    
    # Third line: Scripture readings
    readings_line = fix_roman_numerals(lines[2].strip())
    
    # Find title (skip blank lines after readings)
    title_idx = 3
    while title_idx < len(lines) and not lines[title_idx].strip():
        title_idx += 1
    
    if title_idx >= len(lines):
        return None
    
    title = lines[title_idx].strip()
    
    # Rest: Body paragraphs
    body_start = title_idx + 1
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    
    # Collect paragraphs (blank lines separate paragraphs)
    paragraphs = []
    current_para = []
    
    for line in lines[body_start:]:
        if line.strip():
            current_para.append(line.strip())
        else:
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
    
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    return {
        'date_line': date_line,
        'occasion_line': occasion_line,
        'readings': readings_line,
        'title': title,
        'paragraphs': paragraphs
    }


# =============================================================================
# LITURGICAL DATABASE
# =============================================================================

def load_liturgical_db(path):
    """Load the liturgical database from JSON file."""
    if not path or not Path(path).exists():
        print(f"  Warning: Liturgical database not found at {path}")
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)


def get_liturgical_info(date_str, liturgical_db):
    """Get liturgical information from the database."""
    if date_str in liturgical_db:
        entry = liturgical_db[date_str]
        return {
            'occasion': entry.get('occasion', ''),
            'season': entry.get('season', ''),
            'year': entry.get('lectionary_year', ''),
            'proper': entry.get('proper')
        }
    return None


# =============================================================================
# HTML GENERATION
# =============================================================================

def format_date_display(date_str):
    """Format date for display (e.g., '2008-11-02' -> 'November 02, 2008')."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%B %d, %Y')
    except:
        return date_str


def escape_html(text):
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def generate_meditation_html(meditation_data, date_str, liturgical_info):
    """Generate HTML page for a single meditation."""
    
    title = meditation_data['title']
    title_display = title.upper() if title.isupper() else title
    
    occasion = liturgical_info['occasion'] if liturgical_info else meditation_data['occasion_line']
    season = liturgical_info['season'] if liturgical_info else ''
    year = liturgical_info['year'] if liturgical_info else ''
    
    # Build occasion display
    occasion_display = occasion
    if year and year != '?':
        occasion_display += f", Year {year}"
    if season:
        occasion_display += f" • {season}"
    
    # Generate paragraphs HTML
    paragraphs_html = '\n'.join([
        f'            <p>{escape_html(p)}</p>' for p in meditation_data['paragraphs']
    ])
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(title_display)} | Threads of Grace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css">
    <link rel="stylesheet" href="../meditation.css">
</head>
<body>
    <div class="grain-overlay"></div>
    
    <header class="site-header">
        <div class="container">
            <h1 class="site-title"><a href="../index.html">Threads of Grace</a></h1>
            <p class="site-subtitle">Meditations on Scripture and the Spiritual Life</p>
        </div>
    </header>

    <main class="container">
        <article class="meditation-header">
            <div class="meditation-date-display">{format_date_display(date_str)}</div>
            <h1 class="meditation-title-display">{escape_html(title_display)}</h1>
            <div class="meditation-occasion">{escape_html(occasion_display)}</div>
            <div class="meditation-readings">{escape_html(meditation_data['readings'])}</div>
        </article>

        <div class="meditation-content">
{paragraphs_html}
            
            <div class="meditation-author">
                Pat Horn
            </div>
        </div>

        <nav class="meditation-nav">
            <span></span>
            <a href="../chronological.html" class="back-to-list">All Meditations</a>
            <span></span>
        </nav>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="../index.html">Return to Home</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="../script.js"></script>
</body>
</html>'''
    
    return html


def generate_chronological_html(all_data):
    """Generate the chronological index page."""
    
    # Sort by date descending
    sorted_data = sorted(all_data, key=lambda x: x['date'], reverse=True)
    
    # Group by year
    by_year = {}
    for entry in sorted_data:
        year = entry['date'][:4]
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(entry)
    
    years = sorted(by_year.keys(), reverse=True)
    total = len(sorted_data)
    
    if sorted_data:
        first_date = sorted_data[-1]['date']
        last_date = sorted_data[0]['date']
        first_year = datetime.strptime(first_date, '%Y-%m-%d').strftime('%B %Y')
        last_year = datetime.strptime(last_date, '%Y-%m-%d').strftime('%B %Y')
        date_range = f"{first_year} – {last_year}"
    else:
        date_range = ""
    
    html_parts = [f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All Meditations | Threads of Grace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <style>
        .year-section {{
            margin-bottom: 3rem;
        }}
        .year-heading {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.8rem;
            color: var(--color-burgundy);
            border-bottom: 2px solid var(--color-gold);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        .meditation-list {{
            list-style: none;
            padding: 0;
        }}
        .meditation-list li {{
            padding: 1rem 0;
            border-bottom: 1px solid var(--color-cream-dark);
        }}
        .meditation-link {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--color-burgundy);
            text-decoration: none;
        }}
        .meditation-link:hover {{
            color: var(--color-gold);
        }}
        .meditation-meta {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.95rem;
            color: var(--color-text-light);
            margin-top: 0.25rem;
        }}
        .meditation-occasion {{
            font-style: italic;
        }}
        .page-intro {{
            text-align: center;
            margin-bottom: 3rem;
        }}
        .page-intro p {{
            font-family: 'Crimson Pro', serif;
            font-size: 1.1rem;
            color: var(--color-text-light);
        }}
        .meditation-count {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            color: var(--color-burgundy);
            margin-top: 1rem;
        }}
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

    <main class="container">
        <div class="page-intro">
            <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; color: var(--color-burgundy); margin-bottom: 1rem;">All Meditations</h2>
            <p>A chronological collection of weekly meditations following the rhythms of the church year.</p>
            <p class="meditation-count">{total} meditations from {date_range}</p>
        </div>

''']
    
    for year in years:
        entries = sorted(by_year[year], key=lambda x: x['date'], reverse=True)
        
        html_parts.append(f'''        <section class="year-section">
            <h3 class="year-heading">{year}</h3>
            <ul class="meditation-list">
''')
        
        for entry in entries:
            dt = datetime.strptime(entry['date'], '%Y-%m-%d')
            date_display = dt.strftime('%B %d, %Y')
            title = escape_html(entry['title'])
            occasion = escape_html(entry['occasion'])
            
            html_parts.append(f'''                <li>
                    <a href="meditations/{entry['filename']}" class="meditation-link">{title}</a>
                    <div class="meditation-meta">
                        <span class="meditation-date">{date_display}</span> • 
                        <span class="meditation-occasion">{occasion}</span>
                    </div>
                </li>
''')
        
        html_parts.append('''            </ul>
        </section>

''')
    
    html_parts.append('''    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>''')
    
    return ''.join(html_parts)


def generate_season_html(all_data, season, title):
    """Generate a season index page."""
    
    # Filter by season
    season_entries = [e for e in all_data if e.get('season', '').lower() == season.lower()]
    
    # Sort by date descending
    season_entries.sort(key=lambda x: x['date'], reverse=True)
    
    total = len(season_entries)
    
    html_parts = [f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Threads of Grace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="listing.css">
</head>
<body>
    <div class="grain-overlay"></div>
    
    <header class="site-header">
        <div class="container">
            <h1 class="site-title"><a href="index.html">Threads of Grace</a></h1>
            <p class="site-subtitle">Meditations on Scripture and the Spiritual Life</p>
        </div>
    </header>

    <main class="container">
        <div class="page-intro">
            <h2 class="page-title">{title}</h2>
            <p class="meditation-count">{total} meditations</p>
        </div>

        <div class="meditation-listing">
''']
    
    for entry in season_entries:
        dt = datetime.strptime(entry['date'], '%Y-%m-%d')
        date_display = dt.strftime('%B %d, %Y')
        title_text = escape_html(entry['title'])
        occasion = escape_html(entry['occasion'])
        year_letter = entry.get('year', '')
        if year_letter and year_letter != '?':
            occasion += f" (Year {year_letter})"
        
        html_parts.append(f'''            <article class="meditation-item">
                <a href="meditations/{entry['filename']}" class="meditation-link">
                    <h3 class="meditation-title">{title_text}</h3>
                    <div class="meditation-meta">
                        <span class="meditation-date">{date_display}</span>
                        <span class="meditation-occasion">{occasion}</span>
                    </div>
                </a>
            </article>
''')
    
    html_parts.append('''        </div>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p><a href="by-season.html">Browse by Season</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>''')
    
    return ''.join(html_parts)


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def get_existing_dates(website_dir):
    """Get set of dates already in the website."""
    meditations_dir = Path(website_dir) / 'meditations'
    existing = set()
    for f in meditations_dir.glob('*.html'):
        existing.add(f.stem)
    return existing


def load_meditations_data(website_dir):
    """Load existing meditations data from JSON."""
    data_path = Path(website_dir) / 'meditations-data.json'
    if data_path.exists():
        with open(data_path, 'r') as f:
            return json.load(f)
    return []


def save_meditations_data(website_dir, data):
    """Save meditations data to JSON."""
    data_path = Path(website_dir) / 'meditations-data.json'
    # Sort by date
    sorted_data = sorted(data, key=lambda x: x['date'])
    with open(data_path, 'w') as f:
        json.dump(sorted_data, f, indent=2)


def process_files(input_dir, website_dir, liturgical_db):
    """Process all meditation files and update the website."""
    
    input_path = Path(input_dir)
    website_path = Path(website_dir)
    meditations_dir = website_path / 'meditations'
    
    # Ensure meditations directory exists
    meditations_dir.mkdir(exist_ok=True)
    
    # Get existing dates
    existing_dates = get_existing_dates(website_dir)
    print(f"Found {len(existing_dates)} existing meditations in website")
    
    # Load existing data
    all_data = load_meditations_data(website_dir)
    existing_data_dates = {e['date'] for e in all_data}
    
    # Process input files
    txt_files = sorted(input_path.glob('*.txt'))
    print(f"Found {len(txt_files)} .txt files in input folder")
    print()
    
    processed = []
    skipped = []
    errors = []
    
    for filepath in txt_files:
        filename = filepath.name
        date_str = parse_filename(filename)
        
        if not date_str:
            errors.append(f"Could not parse filename: {filename}")
            continue
        
        # Skip existing
        if date_str in existing_dates:
            skipped.append(f"{date_str} - already in website")
            continue
        
        # Parse file
        meditation_data = parse_meditation_file(filepath)
        if not meditation_data:
            errors.append(f"Could not parse content: {filename}")
            continue
        
        # Get liturgical info
        liturgical_info = get_liturgical_info(date_str, liturgical_db)
        
        # Generate HTML
        html = generate_meditation_html(meditation_data, date_str, liturgical_info)
        
        # Write HTML file
        output_path = meditations_dir / f"{date_str}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Prepare data entry
        entry = {
            'date': date_str,
            'title': meditation_data['title'],
            'filename': f"{date_str}.html",
            'occasion': liturgical_info['occasion'] if liturgical_info else meditation_data['occasion_line'],
            'season': liturgical_info['season'] if liturgical_info else '',
            'year': liturgical_info['year'] if liturgical_info else '',
            'proper': liturgical_info['proper'] if liturgical_info else None
        }
        
        processed.append(entry)
        
        # Add to all_data if not already there
        if date_str not in existing_data_dates:
            all_data.append(entry)
            existing_data_dates.add(date_str)
        
        print(f"  ✓ {date_str}: {meditation_data['title']}")
    
    return processed, skipped, errors, all_data


def main():
    parser = argparse.ArgumentParser(
        description='Process meditation files and update Threads of Grace website'
    )
    parser.add_argument('input_dir', help='Directory containing .txt meditation files')
    parser.add_argument('website_dir', help='Directory containing the website')
    parser.add_argument('--liturgical-db', '-l', default=None,
                       help='Path to liturgical_database.json')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Validate paths
    if not Path(args.input_dir).exists():
        print(f"ERROR: Input directory not found: {args.input_dir}")
        return 1
    
    if not Path(args.website_dir).exists():
        print(f"ERROR: Website directory not found: {args.website_dir}")
        return 1
    
    print("=" * 60)
    print("Threads of Grace - Meditation Processor")
    print("=" * 60)
    print(f"Input:   {args.input_dir}")
    print(f"Website: {args.website_dir}")
    print(f"Liturgical DB: {args.liturgical_db or '(not specified)'}")
    print()
    
    # Load liturgical database
    liturgical_db = load_liturgical_db(args.liturgical_db) if args.liturgical_db else {}
    if liturgical_db:
        print(f"Loaded {len(liturgical_db)} entries from liturgical database")
    
    print()
    print("Processing files...")
    print("-" * 40)
    
    # Process files
    processed, skipped, errors, all_data = process_files(
        args.input_dir, args.website_dir, liturgical_db
    )
    
    print()
    print("-" * 40)
    print(f"Processed: {len(processed)} new meditations")
    print(f"Skipped:   {len(skipped)} (already exist)")
    print(f"Errors:    {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  ✗ {e}")
    
    if not processed:
        print("\nNo new meditations to add.")
        return 0
    
    if args.dry_run:
        print("\n[DRY RUN - no changes made]")
        return 0
    
    # Update meditations-data.json
    print("\nUpdating meditations-data.json...")
    save_meditations_data(args.website_dir, all_data)
    print(f"  Total entries: {len(all_data)}")
    
    # Regenerate chronological.html
    print("Regenerating chronological.html...")
    chrono_html = generate_chronological_html(all_data)
    with open(Path(args.website_dir) / 'chronological.html', 'w') as f:
        f.write(chrono_html)
    
    # Regenerate season pages
    seasons = [
        ('Advent', 'Advent Meditations', 'advent.html'),
        ('Christmas', 'Christmas Meditations', 'christmas.html'),
        ('Epiphany', 'Epiphany Meditations', 'epiphany.html'),
        ('Lent', 'Lent Meditations', 'lent.html'),
        ('Easter', 'Easter Meditations', 'easter.html'),
        ('Ordinary Time', 'Ordinary Time Meditations', 'ordinary-time.html'),
        ('Special', 'Special Occasions', 'special.html'),
    ]
    
    print("Regenerating season pages...")
    for season, title, filename in seasons:
        season_html = generate_season_html(all_data, season, title)
        with open(Path(args.website_dir) / filename, 'w') as f:
            f.write(season_html)
        # Count for this season
        count = len([e for e in all_data if e.get('season', '').lower() == season.lower()])
        print(f"  {filename}: {count} meditations")
    
    print()
    print("=" * 60)
    print("DONE!")
    print(f"Website now contains {len(all_data)} meditations.")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    exit(main())
