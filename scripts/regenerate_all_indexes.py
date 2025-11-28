#!/usr/bin/env python3
"""
Regenerate all index pages from the meditation HTML files.

This script reads data from the meditation files and regenerates:
- chronological.html (all meditations by date with scripture readings)
- Season pages: advent.html, christmas.html, easter.html, epiphany.html, lent.html, ordinary-time.html, special.html
- by-year.html (meditations organized by year)
- by-season.html (navigation page to season pages)

It extracts data from the meditation files' HTML structure:
- meditation-title-display: The meditation title
- meditation-date-display: The display date
- meditation-occasion: The liturgical occasion
- meditation-readings: The scripture readings
"""

import re
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from bs4 import BeautifulSoup


def extract_meditation_data(filepath):
    """Extract metadata from a meditation HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Get filename for the link
    filename = filepath.name

    # Extract date from filename (YYYY-MM-DD.html)
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})\.html', filename)
    date = date_match.group(1) if date_match else None

    # Extract title
    title_elem = soup.find('h1', class_='meditation-title-display')
    title = title_elem.get_text().strip() if title_elem else ''

    # Extract date display
    date_elem = soup.find('div', class_='meditation-date-display')
    date_display = date_elem.get_text().strip() if date_elem else ''

    # Extract occasion
    occasion_elem = soup.find('div', class_='meditation-occasion')
    occasion_full = occasion_elem.get_text().strip() if occasion_elem else ''

    # Parse occasion to get the name and season
    # Format: "Occasion Name, Year X • Season" or "Occasion Name • Season"
    occasion = occasion_full
    season = ''
    if '•' in occasion_full:
        parts = occasion_full.split('•')
        occasion = parts[0].strip()
        season = parts[1].strip() if len(parts) > 1 else ''
        # Remove ", Year X" from occasion for cleaner display
        occasion = re.sub(r',\s*Year\s+[ABC]$', '', occasion).strip()

    # Extract readings
    readings_elem = soup.find('div', class_='meditation-readings')
    readings = readings_elem.get_text().strip() if readings_elem else ''

    # Extract meditation content and compute hash for duplicate detection
    content_div = soup.find('div', class_='meditation-content')
    content_paragraphs = []
    if content_div:
        for p in content_div.find_all('p'):
            text = p.get_text().strip()
            if text:
                content_paragraphs.append(text)
    content_text = '\n'.join(content_paragraphs)
    content_hash = hashlib.md5(content_text.encode()).hexdigest()

    return {
        'filename': filename,
        'date': date,
        'title': title,
        'date_display': date_display,
        'occasion': occasion,
        'occasion_full': occasion_full,
        'season': season,
        'readings': readings,
        'content_hash': content_hash,
    }


def escape_html(text):
    """Escape HTML special characters."""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;'))


def generate_chronological_html(all_data):
    """Generate chronological.html with scripture readings."""

    # Sort by date descending
    sorted_data = sorted(all_data, key=lambda x: x['date'] or '', reverse=True)

    # Group by year
    by_year = defaultdict(list)
    for entry in sorted_data:
        if entry['date']:
            year = entry['date'][:4]
            by_year[year].append(entry)

    years = sorted(by_year.keys(), reverse=True)
    total = len(sorted_data)

    # Get date range
    if sorted_data:
        first_date = sorted_data[-1]['date']
        last_date = sorted_data[0]['date']
        first_dt = datetime.strptime(first_date, '%Y-%m-%d')
        last_dt = datetime.strptime(last_date, '%Y-%m-%d')
        date_range = f"{first_dt.strftime('%B %Y')} – {last_dt.strftime('%B %Y')}"
    else:
        date_range = ""

    html = f'''<!DOCTYPE html>
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
            color: var(--deep-brown);
            border-bottom: 2px solid var(--accent-gold);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        .meditation-list {{
            list-style: none;
            padding: 0;
        }}
        .meditation-list li {{
            padding: 1rem 0;
            border-bottom: 1px solid var(--soft-gray);
        }}
        .meditation-link {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--deep-brown);
            text-decoration: none;
        }}
        .meditation-link:hover {{
            color: var(--accent-gold);
        }}
        .meditation-meta {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.95rem;
            color: var(--medium-gray);
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
            color: var(--medium-gray);
        }}
        .meditation-count {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            color: var(--deep-brown);
            margin-top: 1rem;
        }}
        .meditation-scripture {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.9rem;
            color: var(--medium-gray);
            font-style: italic;
            margin-top: 0.25rem;
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
            <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; color: var(--deep-brown); margin-bottom: 1rem;">All Meditations</h2>
            <p>A chronological collection of weekly meditations following the rhythms of the church year.</p>
            <p class="meditation-count">{total} meditations from {date_range}</p>
        </div>

'''

    for year in years:
        entries = sorted(by_year[year], key=lambda x: x['date'], reverse=True)

        html += f'''        <section class="year-section" id="{year}">
            <h3 class="year-heading">{year}</h3>
            <ul class="meditation-list">
'''

        for entry in entries:
            title = escape_html(entry['title'])
            occasion = escape_html(entry['occasion'])
            readings = escape_html(entry['readings'])
            date_display = entry['date_display']

            html += f'''                <li>
                    <a href="meditations/{entry['filename']}" class="meditation-link">{title}</a>
                    <div class="meditation-meta">
                        <span class="meditation-date">{date_display}</span> •
                        <span class="meditation-occasion">{occasion}</span>
                    </div>
                    <div class="meditation-scripture">{readings}</div>
                </li>
'''

        html += '''            </ul>
        </section>

'''

    html += '''    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p><a href="by-season.html">Browse by Season</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''

    return html


def generate_season_html(all_data, season, page_title):
    """Generate a season index page with full meditation details."""

    # Filter by season (case-insensitive)
    season_lower = season.lower()
    season_entries = [e for e in all_data if e.get('season', '').lower() == season_lower]

    # Sort by date descending
    season_entries.sort(key=lambda x: x['date'] or '', reverse=True)

    total = len(season_entries)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title} | Threads of Grace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <style>
        .meditation-list {{
            list-style: none;
            padding: 0;
        }}
        .meditation-list li {{
            padding: 1rem 0;
            border-bottom: 1px solid var(--soft-gray);
        }}
        .meditation-link {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--deep-brown);
            text-decoration: none;
        }}
        .meditation-link:hover {{
            color: var(--accent-gold);
        }}
        .meditation-meta {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.95rem;
            color: var(--medium-gray);
            margin-top: 0.25rem;
        }}
        .meditation-occasion {{
            font-style: italic;
        }}
        .page-intro {{
            text-align: center;
            margin-bottom: 3rem;
        }}
        .page-title {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.2rem;
            color: var(--deep-brown);
            margin-bottom: 1rem;
        }}
        .meditation-count {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            color: var(--deep-brown);
        }}
        .meditation-scripture {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.9rem;
            color: var(--medium-gray);
            font-style: italic;
            margin-top: 0.25rem;
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
            <h2 class="page-title">{page_title}</h2>
            <p class="meditation-count">{total} meditations</p>
        </div>

        <ul class="meditation-list">
'''

    for entry in season_entries:
        title = escape_html(entry['title'])
        occasion = escape_html(entry['occasion'])
        readings = escape_html(entry['readings'])
        date_display = entry['date_display']

        html += f'''            <li>
                <a href="meditations/{entry['filename']}" class="meditation-link">{title}</a>
                <div class="meditation-meta">
                    <span class="meditation-date">{date_display}</span> •
                    <span class="meditation-occasion">{occasion}</span>
                </div>
                <div class="meditation-scripture">{readings}</div>
            </li>
'''

    html += '''        </ul>
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
</html>'''

    return html


def generate_by_year_html(all_data):
    """Generate by-year.html with meditations organized by year, with full details."""

    # Sort by date descending
    sorted_data = sorted(all_data, key=lambda x: x['date'] or '', reverse=True)

    # Group by year
    by_year = defaultdict(list)
    for entry in sorted_data:
        if entry['date']:
            year = entry['date'][:4]
            by_year[year].append(entry)

    years = sorted(by_year.keys(), reverse=True)
    total = len(sorted_data)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meditations by Year | Threads of Grace</title>
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
            color: var(--deep-brown);
            border-bottom: 2px solid var(--accent-gold);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        .meditation-list {{
            list-style: none;
            padding: 0;
        }}
        .meditation-list li {{
            padding: 1rem 0;
            border-bottom: 1px solid var(--soft-gray);
        }}
        .meditation-link {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--deep-brown);
            text-decoration: none;
        }}
        .meditation-link:hover {{
            color: var(--accent-gold);
        }}
        .meditation-meta {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.95rem;
            color: var(--medium-gray);
            margin-top: 0.25rem;
        }}
        .meditation-occasion {{
            font-style: italic;
        }}
        .page-intro {{
            text-align: center;
            margin-bottom: 3rem;
        }}
        .page-title {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.2rem;
            color: var(--deep-brown);
            margin-bottom: 1rem;
        }}
        .meditation-count {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            color: var(--deep-brown);
        }}
        .meditation-scripture {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.9rem;
            color: var(--medium-gray);
            font-style: italic;
            margin-top: 0.25rem;
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
            <h2 class="page-title">Meditations by Year</h2>
            <p class="meditation-count">{total} meditations</p>
        </div>

'''

    for year in years:
        entries = sorted(by_year[year], key=lambda x: x['date'], reverse=True)
        count = len(entries)

        html += f'''        <section class="year-section">
            <h3 class="year-heading">{year} ({count} meditations)</h3>
            <ul class="meditation-list">
'''

        for entry in entries:
            title = escape_html(entry['title'])
            occasion = escape_html(entry['occasion'])
            readings = escape_html(entry['readings'])
            date_display = entry['date_display']

            html += f'''                <li>
                    <a href="meditations/{entry['filename']}" class="meditation-link">{title}</a>
                    <div class="meditation-meta">
                        <span class="meditation-date">{date_display}</span> •
                        <span class="meditation-occasion">{occasion}</span>
                    </div>
                    <div class="meditation-scripture">{readings}</div>
                </li>
'''

        html += '''            </ul>
        </section>

'''

    html += '''    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p><a href="by-season.html">Browse by Season</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''

    return html


def generate_lectionary_year_html(all_data):
    """Generate lectionary-year.html organized by Year A/B/C with occasions."""
    import json

    # Load liturgical database for canonical occasion names and ordering
    script_dir = Path(__file__).parent
    db_path = script_dir / 'liturgical_database.json'
    with open(db_path, 'r', encoding='utf-8') as f:
        liturgical_db = json.load(f)

    def normalize_occasion(occasion):
        """Normalize occasion name to a canonical key for grouping."""
        import re
        # Remove Year designation
        occ = re.sub(r',?\s*Year\s+[ABC]$', '', occasion).strip()

        # Clean up common issues first
        occ = occ.rstrip('\\').strip()  # Remove trailing backslash
        occ = re.sub(r'\s+', ' ', occ)  # collapse whitespace
        occ = re.sub(r'["""]', '', occ)  # remove quotes

        # Extract Proper number if present - this is the most reliable grouping
        # Handle both "Proper 26" and "Proper26" (no space)
        proper_match = re.search(r'Proper\s*(\d+)', occ)
        if proper_match:
            return f"Proper {int(proper_match.group(1)):02d}"

        # Remove parenthetical notes like "(Note: Episcopal readings...)"
        # Handle both regular quotes and escaped quotes
        occ = re.sub(r'\s*[\("]?\(?Note:.*$', '', occ).strip()

        # Handle compound occasions - extract the primary occasion
        # "First Sunday after the Epiphany The Baptism of Our Lord" -> "First Sunday after the Epiphany"
        if 'The Baptism of Our Lord' in occ:
            occ = re.sub(r'\s*The Baptism of Our Lord.*', '', occ).strip()

        # "Fourth Sunday of Advent Christmas Eve" -> "Fourth Sunday of Advent"
        if 'Christmas Eve' in occ and 'Advent' in occ:
            occ = re.sub(r'\s*Christmas Eve.*', '', occ).strip()

        # Normalize common variations
        occ = occ.replace('after Epiphany', 'after the Epiphany')
        occ = occ.replace("All Saints'", 'All Saints')
        occ = occ.replace('Twenty First', 'Twenty-First')
        occ = occ.replace('Twenty Second', 'Twenty-Second')
        occ = occ.replace('Twenty Third', 'Twenty-Third')
        occ = occ.replace('Twenty Fourth', 'Twenty-Fourth')
        occ = occ.replace('Twenty Fifth', 'Twenty-Fifth')
        occ = occ.replace('Twenty Sixth', 'Twenty-Sixth')
        occ = occ.replace('Twenty Seventh', 'Twenty-Seventh')

        # Handle Easter Day and Christmas Day variations first (they have many forms)
        if occ.startswith('Easter Day'):
            return 'Easter Day'
        if occ.startswith('Christmas Day'):
            return 'Christmas Day'

        # Map to canonical names
        canonical_map = {
            'Last Sunday after Epiphany': 'Last Sunday after the Epiphany',
            'The Epiphany': 'Epiphany',
            'The Holy Name': 'Holy Name',
            'First Sunday after Christmas Day': 'First Sunday after Christmas',
            'The Transfiguration': 'Last Sunday after the Epiphany',
            'Presentation of Jesus in the Temple': 'Fourth Sunday after the Epiphany',
            'All Saints RCL All Saints BCP (1) All Saints BCP (2)': 'All Saints',
            'All Saints Sunday': 'All Saints',
        }

        for old, new in canonical_map.items():
            if old in occ:
                occ = new
                break

        # Handle compound occasions - take first meaningful part
        if ' All Saints' in occ and occ.startswith(('Twenty', 'Nineteenth', 'Eighteenth')):
            # e.g., "All Saints (white) Twenty First Sunday after Pentecost Proper 26"
            occ = 'All Saints'

        return occ

    def get_liturgical_order():
        """Build liturgical order from database - each Year A cycle gives us the order."""
        # Define the canonical liturgical year order
        order = [
            'First Sunday of Advent',
            'Second Sunday of Advent',
            'Third Sunday of Advent',
            'Fourth Sunday of Advent',
            'Christmas Day',
            'First Sunday after Christmas',
            'Second Sunday after Christmas',
            'Holy Name',
            'Epiphany',
            'First Sunday after the Epiphany',
            'Second Sunday after the Epiphany',
            'Third Sunday after the Epiphany',
            'Fourth Sunday after the Epiphany',
            'Fifth Sunday after the Epiphany',
            'Sixth Sunday after the Epiphany',
            'Seventh Sunday after the Epiphany',
            'Eighth Sunday after the Epiphany',
            'Last Sunday after the Epiphany',
            'Ash Wednesday',
            'First Sunday in Lent',
            'Second Sunday in Lent',
            'Third Sunday in Lent',
            'Fourth Sunday in Lent',
            'Fifth Sunday in Lent',
            'Palm Sunday',
            'Easter Day',
            'Second Sunday of Easter',
            'Third Sunday of Easter',
            'Fourth Sunday of Easter',
            'Fifth Sunday of Easter',
            'Sixth Sunday of Easter',
            'Seventh Sunday of Easter',
            'Day of Pentecost',
            'Trinity Sunday',
        ]
        # Add Propers 3-29
        for i in range(3, 30):
            order.append(f'Proper {i:02d}')
        order.append('All Saints')
        order.append('Christ the King')
        return order

    def get_occasion_sort_key(normalized_occasion):
        """Get sort index for a normalized occasion."""
        order = get_liturgical_order()
        try:
            return order.index(normalized_occasion)
        except ValueError:
            # Not found - put at end
            return 999

    # Extract lectionary year from occasion_full
    def get_lectionary_year(occasion_full):
        match = re.search(r'Year ([ABC])', occasion_full)
        return match.group(1) if match else None

    # Group by lectionary year, then by normalized occasion
    # Store: { 'A': { 'normalized_occ': {'entries': [...], 'display_names': set(), 'readings': set()} } }
    by_year = {'A': defaultdict(lambda: {'entries': [], 'display_names': set(), 'readings': set()}),
               'B': defaultdict(lambda: {'entries': [], 'display_names': set(), 'readings': set()}),
               'C': defaultdict(lambda: {'entries': [], 'display_names': set(), 'readings': set()})}
    year_counts = {'A': 0, 'B': 0, 'C': 0}

    for entry in all_data:
        lect_year = get_lectionary_year(entry.get('occasion_full', ''))
        if lect_year:
            occasion = entry.get('occasion', '')
            normalized = normalize_occasion(occasion)
            by_year[lect_year][normalized]['entries'].append(entry)
            by_year[lect_year][normalized]['display_names'].add(occasion)
            if entry.get('readings'):
                by_year[lect_year][normalized]['readings'].add(entry.get('readings'))
            year_counts[lect_year] += 1

    total = sum(year_counts.values())

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lectionary Year Index | Threads of Grace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <style>
        main.container {{
            padding-top: 2rem;
        }}
        main.container section {{
            border-bottom: none;
            padding: 0;
        }}
        .year-nav {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--warm-white);
            border-radius: 4px;
        }}
        .year-nav a {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--deep-brown);
            text-decoration: none;
            padding: 0.5rem 1.5rem;
        }}
        .year-nav a:hover {{
            color: var(--accent-gold);
        }}
        .year-section {{
            margin-bottom: 4rem;
        }}
        .year-heading {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2rem;
            color: var(--deep-brown);
            border-bottom: 3px solid var(--accent-gold);
            padding-bottom: 0.5rem;
            margin-bottom: 2rem;
        }}
        .occasion-group {{
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--warm-white);
            border-radius: 4px;
        }}
        .occasion-heading {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--deep-brown);
            margin-bottom: 0.25rem;
        }}
        .occasion-readings {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.95rem;
            color: var(--medium-gray);
            font-style: italic;
            margin-bottom: 0.75rem;
        }}
        .meditation-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .meditation-list li {{
            padding: 0.35rem 0;
        }}
        .meditation-link {{
            font-family: 'Crimson Pro', serif;
            color: var(--dark-gray);
            text-decoration: none;
        }}
        .meditation-link:hover {{
            color: var(--deep-brown);
        }}
        .special-feast-note {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.85rem;
            color: var(--accent-sage);
            font-style: italic;
            margin-left: 1rem;
            margin-top: 0.15rem;
        }}
        .meditation-date {{
            color: var(--medium-gray);
            font-size: 0.9rem;
        }}
        .page-intro {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        .page-title {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.2rem;
            color: var(--deep-brown);
            margin-bottom: 0.5rem;
        }}
        .meditation-count {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            color: var(--deep-brown);
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
            <h2 class="page-title">Lectionary Year Index</h2>
            <p class="meditation-count">{total} meditations across the three-year lectionary cycle</p>
        </div>

        <nav class="year-nav">
            <a href="#year-a">Year A ({year_counts['A']})</a>
            <a href="#year-b">Year B ({year_counts['B']})</a>
            <a href="#year-c">Year C ({year_counts['C']})</a>
        </nav>

'''

    for year in ['A', 'B', 'C']:
        year_data = by_year[year]

        # Sort occasions by liturgical order using normalized keys
        sorted_occasions = sorted(year_data.keys(), key=get_occasion_sort_key)

        html += f'''        <section class="year-section" id="year-{year.lower()}">
            <h2 class="year-heading">Year {year}</h2>

'''

        for normalized_occasion in sorted_occasions:
            occasion_data = year_data[normalized_occasion]
            entries = occasion_data['entries']
            display_names = occasion_data['display_names']
            readings_set = occasion_data['readings']

            # Sort entries by date descending (most recent first)
            entries = sorted(entries, key=lambda x: x['date'] or '', reverse=True)

            # Determine display name
            # For Proper occasions, use "Ordinary Time – Proper X" format
            proper_match = re.match(r'Proper (\d+)', normalized_occasion)
            if proper_match:
                proper_num = int(proper_match.group(1))
                occasion_display = f"Ordinary Time – Proper {proper_num}"
            else:
                # Clean up display names before choosing
                def clean_display_name(name):
                    # Remove notes, trailing backslashes, compound suffixes
                    name = re.sub(r'\s*[\("]?\(?Note:.*$', '', name).strip()
                    name = name.rstrip('\\').strip()
                    name = re.sub(r'\s*The Baptism of Our Lord.*', '', name).strip()
                    name = re.sub(r'\s*Christmas Eve.*', '', name).strip() if 'Advent' in name else name
                    # Normalize All Saints variations
                    if 'All Saints' in name:
                        name = 'All Saints'
                    # Normalize Christmas Day variations
                    if name.startswith('Christmas Day'):
                        name = 'Christmas Day'
                    # Normalize Easter Day variations
                    if name.startswith('Easter Day'):
                        name = 'Easter Day'
                    # Presentation should display as Fourth Sunday after the Epiphany
                    if 'Presentation' in name:
                        name = 'Fourth Sunday after the Epiphany'
                    return name

                cleaned_names = [clean_display_name(n) for n in display_names]
                # Use the longest cleaned display name (most elegant/complete)
                occasion_display = max(cleaned_names, key=len) if cleaned_names else normalized_occasion

            # Use the longest readings (most complete)
            readings = max(readings_set, key=len) if readings_set else ''

            occasion_display = escape_html(occasion_display)
            readings_display = escape_html(readings)

            html += f'''            <div class="occasion-group">
                <div class="occasion-heading">{occasion_display}</div>
                <div class="occasion-readings">{readings_display}</div>
                <ul class="meditation-list">
'''

            for entry in entries:
                title = escape_html(entry['title'])
                date_display = entry['date_display']
                original_occasion = entry.get('occasion', '')

                # Check if this entry has a special feast day note
                special_note = ''
                if 'Presentation' in original_occasion:
                    special_note = '<div class="special-feast-note">Presentation of Jesus in the Temple</div>'

                html += f'''                    <li>
                        <a href="meditations/{entry['filename']}" class="meditation-link">
                            {title} <span class="meditation-date">• {date_display}</span>
                        </a>
                        {special_note}
                    </li>
'''

            html += '''                </ul>
            </div>

'''

        html += '''        </section>

'''

    html += '''    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p><a href="chronological.html">View All Meditations</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>'''

    return html


def generate_title_index_html(all_data):
    """Generate title-index.html with meditations grouped alphabetically by title."""

    from collections import defaultdict
    import re

    # Group by title, then by first letter
    by_title = defaultdict(list)
    for entry in all_data:
        title = entry.get('title', '').strip()
        if title:
            by_title[title].append(entry)

    def get_sort_key(title):
        """Get sort key that ignores leading quotes/punctuation."""
        # Strip leading quotes and punctuation for sorting
        # Include straight quotes, curly quotes, ellipsis, spaces, and other common punctuation
        strip_chars = '"\'\u201c\u201d\u2018\u2019.\u2026 '  # " ' " " ' ' . … and space
        stripped = title.lstrip(strip_chars)
        return stripped.lower()

    def get_first_letter(title):
        """Get first alphabetic letter for grouping."""
        # Strip leading quotes and punctuation
        strip_chars = '"\'\u201c\u201d\u2018\u2019.\u2026 '  # " ' " " ' ' . … and space
        stripped = title.lstrip(strip_chars)
        if stripped and stripped[0].isalpha():
            return stripped[0].upper()
        return '#'

    # Group titles by first letter
    by_letter = defaultdict(list)
    for title in sorted(by_title.keys(), key=get_sort_key):
        first_char = get_first_letter(title)
        by_letter[first_char].append((title, by_title[title]))

    # Get all letters present
    letters = sorted(by_letter.keys(), key=lambda x: (x != '#', x))

    total_meditations = len(all_data)
    unique_titles = len(by_title)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index by Title | Threads of Grace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <style>
        .letter-nav {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            justify-content: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--warm-white);
            border-radius: 4px;
        }}
        .letter-nav a {{
            padding: 0.25rem 0.5rem;
            color: var(--deep-brown);
            text-decoration: none;
            font-family: 'Cormorant Garamond', serif;
            font-weight: 600;
        }}
        .letter-nav a:hover {{
            color: var(--accent-gold);
        }}
        .letter-section {{
            margin-bottom: 2rem;
        }}
        .letter-heading {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.8rem;
            color: var(--deep-brown);
            border-bottom: 2px solid var(--accent-gold);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }}
        .title-group {{
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            background: var(--warm-white);
            border-radius: 4px;
        }}
        .title-heading {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--deep-brown);
            margin-bottom: 0.5rem;
        }}
        .title-heading a {{
            color: inherit;
            text-decoration: none;
        }}
        .title-heading a:hover {{
            color: var(--accent-gold);
        }}
        .meditation-entries {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .meditation-entries li {{
            padding: 0.25rem 0;
        }}
        .meditation-entries a {{
            font-family: 'Crimson Pro', serif;
            color: var(--dark-gray);
            text-decoration: none;
            font-size: 0.95rem;
        }}
        .meditation-entries a:hover {{
            color: var(--deep-brown);
        }}
        .entry-date {{
            color: var(--medium-gray);
        }}
        .entry-occasion {{
            color: var(--medium-gray);
            font-style: italic;
        }}
        .page-intro {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        .page-title {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.2rem;
            color: var(--deep-brown);
            margin-bottom: 0.5rem;
        }}
        .meditation-count {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            color: var(--deep-brown);
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
            <h2 class="page-title">Index by Title</h2>
            <p class="meditation-count">{total_meditations} meditations</p>
        </div>

        <nav class="letter-nav">
'''

    for letter in letters:
        html += f'            <a href="#letter-{letter}">{letter}</a>\n'

    html += '''        </nav>

'''

    for letter in letters:
        titles_in_letter = by_letter[letter]

        html += f'''        <section class="letter-section" id="letter-{letter}">
            <h2 class="letter-heading">{letter}</h2>

'''

        for title, entries in titles_in_letter:
            title_display = escape_html(title)
            entries = sorted(entries, key=lambda x: x['date'] or '', reverse=True)

            if len(entries) == 1:
                # Single meditation - link directly
                entry = entries[0]
                html += f'''            <div class="title-group">
                <div class="title-heading">
                    <a href="meditations/{entry['filename']}">{title_display}</a>
                    <span class="entry-date"> • {entry['date_display']}</span>
                    <span class="entry-occasion"> • {escape_html(entry['occasion'])}</span>
                </div>
            </div>

'''
            else:
                # Multiple meditations with same title
                html += f'''            <div class="title-group">
                <div class="title-heading">{title_display}</div>
                <ul class="meditation-entries">
'''
                for entry in entries:
                    html += f'''                    <li>
                        <a href="meditations/{entry['filename']}">
                            <span class="entry-date">{entry['date_display']}</span>
                            <span class="entry-occasion"> • {escape_html(entry['occasion'])}</span>
                        </a>
                    </li>
'''
                html += '''                </ul>
            </div>

'''

        html += '''        </section>

'''

    html += '''    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p><a href="chronological.html">View All Meditations</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''

    return html


def generate_scripture_index_html(all_data):
    """Generate scripture-index.html with meditations organized by scripture reference."""

    import re
    from collections import defaultdict

    # Define canonical book order
    book_order = [
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', 'I Samuel', 'II Samuel',
        '1 Kings', '2 Kings', 'I Kings', 'II Kings',
        '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther',
        'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Song of Songs',
        'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel',
        'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah',
        'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
        'Sirach', 'Wisdom', 'Wisdom of Solomon', 'Baruch', 'Canticle',
        'Matthew', 'Mark', 'Luke', 'John', 'Acts',
        'Romans', '1 Corinthians', '2 Corinthians', 'I Corinthians', 'II Corinthians',
        'Galatians', 'Ephesians', 'Philippians', 'Colossians',
        '1 Thessalonians', '2 Thessalonians', 'I Thessalonians', 'II Thessalonians',
        '1 Timothy', '2 Timothy', 'I Timothy', 'II Timothy',
        'Titus', 'Philemon', 'Hebrews', 'James',
        '1 Peter', '2 Peter', 'I Peter', 'II Peter',
        '1 John', '2 John', '3 John', 'I John', 'II John', 'III John',
        'Jude', 'Revelation'
    ]

    def normalize_book(book):
        """Normalize book name for grouping."""
        # Handle Roman numerals and numbered books
        book = book.strip()
        book = re.sub(r'^(\d)\s+', r'\1 ', book)  # "1Samuel" -> "1 Samuel"
        book = re.sub(r'^I\s+', '1 ', book)
        book = re.sub(r'^II\s+', '2 ', book)
        book = re.sub(r'^III\s+', '3 ', book)
        return book

    def get_book_key(book):
        """Get sort order for a book."""
        normalized = normalize_book(book)
        for i, b in enumerate(book_order):
            if normalized.lower() == b.lower() or book.lower() == b.lower():
                return (0, i)
        return (1, book.lower())

    def parse_chapter_verse(ref, book):
        """Extract chapter and verse from a reference for sorting."""
        # Remove the book name from the reference
        rest = ref[len(book):].strip()
        # Remove leading colon or period if present
        rest = rest.lstrip(':.')

        # Try to extract chapter and verse numbers
        # Handles formats like "1:1-10", "15:1-12, 17-18", "3:1-7", etc.
        match = re.match(r'(\d+)(?::(\d+))?', rest)
        if match:
            chapter = int(match.group(1))
            verse = int(match.group(2)) if match.group(2) else 0
            return (chapter, verse, rest)
        return (999, 999, rest)  # Put unparseable refs at the end

    # Parse readings and group by book
    by_book = defaultdict(list)
    total_refs = 0

    for entry in all_data:
        readings = entry.get('readings', '')
        if readings:
            # Split by comma but handle ranges
            refs = re.split(r',\s*(?=[A-Z1-3I])', readings)
            for ref in refs:
                ref = ref.strip()
                if ref:
                    # Extract book name
                    match = re.match(r'^([1-3I]*\s*[A-Za-z]+(?:\s+of\s+[A-Za-z]+)?)', ref)
                    if match:
                        book = match.group(1).strip()
                        # Skip non-book entries (liturgical labels, verse numbers, abbreviations)
                        skip_patterns = ['Liturgy of the', 'Proper', 'Year', 'Col', 'Lk', 'Ps', 'Psalms']
                        # Also skip entries that are just numbers/verse refs (like "21c", "11b")
                        if (any(book.lower() == skip.lower() or book == skip for skip in skip_patterns)
                            or re.match(r'^\d+[a-z]?$', book)):
                            continue
                        by_book[book].append({
                            'ref': ref,
                            'entry': entry
                        })
                        total_refs += 1

    # Sort books
    sorted_books = sorted(by_book.keys(), key=get_book_key)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index by Scripture | Threads of Grace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <style>
        .book-nav {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            justify-content: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--warm-white);
            border-radius: 4px;
        }}
        .book-nav a {{
            padding: 0.25rem 0.5rem;
            color: var(--deep-brown);
            text-decoration: none;
            font-family: 'Crimson Pro', serif;
            font-size: 0.9rem;
        }}
        .book-nav a:hover {{
            color: var(--accent-gold);
        }}
        .book-section {{
            margin-bottom: 2rem;
        }}
        .book-heading {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.5rem;
            color: var(--deep-brown);
            border-bottom: 2px solid var(--accent-gold);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }}
        .scripture-list {{
            list-style: none;
            padding: 0;
        }}
        .scripture-list li {{
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(139, 115, 85, 0.1);
        }}
        .scripture-link {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--deep-brown);
            text-decoration: none;
        }}
        .scripture-link:hover {{
            color: var(--accent-gold);
        }}
        .scripture-meta {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.9rem;
            color: var(--medium-gray);
            margin-top: 0.25rem;
        }}
        .scripture-occasion {{
            font-style: italic;
        }}
        .chapter-verse-heading {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.15rem;
            color: var(--accent-sage);
            margin-top: 1.25rem;
            margin-bottom: 0.5rem;
            padding-left: 0.5rem;
            border-left: 3px solid var(--accent-gold);
        }}
        .chapter-verse-heading:first-of-type {{
            margin-top: 0;
        }}
        .page-intro {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        .page-title {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.2rem;
            color: var(--deep-brown);
            margin-bottom: 0.5rem;
        }}
        .meditation-count {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            color: var(--deep-brown);
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
            <h2 class="page-title">Index by Scripture</h2>
            <p class="meditation-count">Meditations organized by scripture passages</p>
        </div>

        <nav class="book-nav">
'''

    for book in sorted_books:
        book_id = book.lower().replace(' ', '-')
        html += f'            <a href="#book-{book_id}">{escape_html(book)}</a>\n'

    html += '''        </nav>

'''

    for book in sorted_books:
        book_id = book.lower().replace(' ', '-')
        items = by_book[book]

        html += f'''        <section class="book-section" id="book-{book_id}">
            <h2 class="book-heading">{escape_html(book)}</h2>
'''

        # Sort by chapter:verse, then by date
        items.sort(key=lambda x: (
            parse_chapter_verse(x['ref'], book),
            x['entry'].get('date', '')
        ))

        # Group by reference (chapter:verse)
        current_ref = None
        for item in items:
            ref = item['ref']
            entry = item['entry']
            title = escape_html(entry['title'])
            date_display = entry['date_display']
            occasion = escape_html(entry['occasion'])

            # Add chapter:verse heading when reference changes
            if ref != current_ref:
                if current_ref is not None:
                    html += '''            </ul>
'''
                # Extract the chapter:verse part (everything after the book name)
                cv_part = ref[len(book):].strip()
                html += f'''            <h3 class="chapter-verse-heading">{escape_html(book)} {escape_html(cv_part)}</h3>
            <ul class="scripture-list">
'''
                current_ref = ref

            html += f'''                <li>
                    <a href="meditations/{entry['filename']}" class="scripture-link">{title}</a>
                    <div class="scripture-meta">
                        <span class="scripture-date">{date_display}</span> •
                        <span class="scripture-occasion">{occasion}</span>
                    </div>
                </li>
'''

        if current_ref is not None:
            html += '''            </ul>
'''
        html += '''        </section>

'''

    html += '''    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p><a href="chronological.html">View All Meditations</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''

    return html


def generate_appendix_statistics_html(all_data):
    """Generate appendix-statistics.html with clickable links."""

    from collections import defaultdict
    import re

    # Count by year
    by_year = defaultdict(int)
    for entry in all_data:
        if entry.get('date'):
            year = entry['date'][:4]
            by_year[year] += 1

    # Count by season
    by_season = defaultdict(int)
    for entry in all_data:
        season = entry.get('season', '').lower()
        if season:
            by_season[season] += 1

    # Count by lectionary year
    def get_lectionary_year(occasion_full):
        match = re.search(r'Year ([ABC])', occasion_full)
        return match.group(1) if match else None

    by_lect_year = defaultdict(int)
    for entry in all_data:
        lect_year = get_lectionary_year(entry.get('occasion_full', ''))
        if lect_year:
            by_lect_year[lect_year] += 1

    # Find repeated essays by content hash (identical content = same essay)
    by_hash = defaultdict(list)
    for entry in all_data:
        content_hash = entry.get('content_hash', '')
        if content_hash:
            by_hash[content_hash].append(entry)

    # Essays that appear more than once (identical content)
    repeated_essays = {h: entries for h, entries in by_hash.items() if len(entries) > 1}
    unique_essays = len(by_hash)

    total = len(all_data)
    reuse_instances = total - unique_essays  # How many times content was reused
    years_list = sorted(by_year.keys())

    # Season mapping for links
    season_links = {
        'advent': 'advent.html',
        'christmas': 'christmas.html',
        'epiphany': 'epiphany.html',
        'lent': 'lent.html',
        'easter': 'easter.html',
        'ordinary time': 'ordinary-time.html',
        'special': 'special.html',
    }

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Collection Statistics | Threads of Grace</title>
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
            border-bottom: 1px solid var(--soft-gray);
        }}
        .index-header h1 {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.5rem;
            color: var(--deep-brown);
            margin-bottom: 0.5rem;
        }}
        .index-header p {{
            font-family: 'Crimson Pro', serif;
            color: var(--medium-gray);
            font-size: 1.1rem;
        }}
        .index-section {{
            margin-bottom: 2.5rem;
        }}
        .index-section h2 {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.5rem;
            color: var(--deep-brown);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--soft-gray);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        .stat-card {{
            background: var(--warm-white);
            padding: 1.5rem;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-number {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.5rem;
            color: var(--deep-brown);
            display: block;
        }}
        .stat-label {{
            font-family: 'Crimson Pro', serif;
            color: var(--medium-gray);
            font-size: 0.9rem;
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
            color: var(--deep-brown);
            text-decoration: none;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 1rem;
        }}
        .index-list a:hover {{
            color: var(--accent-gold);
        }}
        .index-title {{
            font-family: 'Crimson Pro', serif;
            flex: 1;
        }}
        .index-date {{
            font-family: 'Crimson Pro', serif;
            color: var(--medium-gray);
            font-size: 0.9rem;
            white-space: nowrap;
        }}
        .reuse-group {{
            background: var(--warm-white);
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }}
        .reuse-title {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            color: var(--deep-brown);
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
            color: var(--dark-gray);
            text-decoration: none;
        }}
        .reuse-dates a:hover {{
            color: var(--deep-brown);
        }}
        .index-occasion {{
            font-size: 0.85rem;
            color: var(--medium-gray);
            margin-left: 1rem;
            font-style: italic;
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

    <main class="index-container">
        <div class="index-header">
            <h1>Appendix A: Collection Statistics</h1>
            <p>A detailed look at sixteen years of weekly meditations</p>
        </div>

        <section class="index-section">
            <h2>Overview</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number">{total}</span>
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
                    <span class="stat-number">17</span>
                    <span class="stat-label">Years ({years_list[0]}–{years_list[-1]})</span>
                </div>
            </div>
            <p style="margin-top: 1.5rem; font-style: italic; color: var(--medium-gray);">
                The three-year lectionary cycle means the same liturgical occasions recur regularly.
                Pat thoughtfully reused {len(repeated_essays)} essays a total of {reuse_instances} times when the same readings returned,
                while also writing fresh reflections for many recurring occasions. This intentional
                curation reflects her pastoral wisdom in knowing when a message bears repeating.
            </p>
        </section>

        <section class="index-section">
            <h2>By Calendar Year</h2>
            <ul class="index-list">
'''

    for year in sorted(years_list, reverse=True):
        count = by_year[year]
        html += f'''                <li>
                    <a href="chronological.html#{year}">
                        <span class="index-title">{year}</span>
                        <span class="index-date">{count} meditations</span>
                    </a>
                </li>
'''

    html += '''            </ul>
        </section>

        <section class="index-section">
            <h2>By Liturgical Season</h2>
            <ul class="index-list">
'''

    # Season display order
    season_order = ['advent', 'christmas', 'epiphany', 'lent', 'easter', 'ordinary time', 'special']
    for season_key in season_order:
        count = by_season.get(season_key, 0)
        if count > 0:
            season_display = season_key.title()
            link = season_links.get(season_key, '#')
            html += f'''                <li>
                    <a href="{link}">
                        <span class="index-title">{season_display}</span>
                        <span class="index-date">{count} meditations</span>
                    </a>
                </li>
'''

    html += '''            </ul>
        </section>

        <section class="index-section">
            <h2>By Lectionary Year</h2>
            <ul class="index-list">
'''

    for year_letter in ['A', 'B', 'C']:
        count = by_lect_year.get(year_letter, 0)
        html += f'''                <li>
                    <a href="lectionary-year.html#year-{year_letter.lower()}">
                        <span class="index-title">Year {year_letter}</span>
                        <span class="index-date">{count} meditations</span>
                    </a>
                </li>
'''

    html += '''            </ul>
        </section>

        <section class="index-section">
            <h2>Repeated Essays</h2>
            <p style="margin-bottom: 1.5rem; color: var(--medium-gray);">
                These essays were used more than once across the collection,
                typically when the same liturgical occasion returned in the three-year lectionary cycle.
            </p>
'''

    # Sort repeated essays alphabetically by title (use first entry's title)
    repeated_list = [(entries[0]['title'], entries) for h, entries in repeated_essays.items()]
    repeated_list.sort(key=lambda x: x[0].lower().lstrip('"').lstrip("'"))

    for title, entries in repeated_list:
        entries = sorted(entries, key=lambda x: x['date'] or '')
        title_display = escape_html(title)

        html += f'''            <div class="reuse-group">
                <div class="reuse-title">{title_display}</div>
                <ul class="reuse-dates">
'''

        for entry in entries:
            occasion = escape_html(entry['occasion'])
            html += f'''                    <li>
                        <a href="meditations/{entry['filename']}">{entry['date_display']}</a>
                        <span class="index-occasion">{occasion}</span>
                    </li>
'''

        html += '''                </ul>
            </div>
'''

    html += '''        </section>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''

    return html


def generate_by_season_html(all_data):
    """Generate by-season.html navigation page."""

    # Count meditations per season
    season_counts = defaultdict(int)
    for entry in all_data:
        season = entry.get('season', '').lower()
        if season:
            season_counts[season] += 1

    total = len(all_data)

    # Define season order and display names
    seasons = [
        ('advent', 'Advent', 'advent.html'),
        ('christmas', 'Christmas', 'christmas.html'),
        ('epiphany', 'Epiphany', 'epiphany.html'),
        ('lent', 'Lent', 'lent.html'),
        ('easter', 'Easter', 'easter.html'),
        ('ordinary time', 'Ordinary Time', 'ordinary-time.html'),
        ('special', 'Special', 'special.html'),
    ]

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browse by Season | Threads of Grace</title>
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
            <h2 class="page-title">Browse by Season</h2>
            <p class="meditation-count">{total} meditations across the liturgical year</p>
        </div>

        <div class="season-grid">
'''

    for season_key, season_name, filename in seasons:
        count = season_counts.get(season_key, 0)
        html += f'''            <a href="{filename}" class="season-card">
                <h3>{season_name}</h3>
                <p>{count} meditations</p>
            </a>
'''

    html += '''        </div>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p><a href="index.html">Return to Home</a></p>
            <p><a href="chronological.html">View All Meditations</a></p>
            <p class="copyright">© 2007–2025 Pat Horn. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''

    return html


def main():
    import sys

    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    # Get the website directory
    script_dir = Path(__file__).parent
    website_dir = script_dir.parent
    meditations_dir = website_dir / 'meditations'

    if not meditations_dir.exists():
        print(f"Error: meditations directory not found: {meditations_dir}")
        sys.exit(1)

    print(f"{'DRY RUN - ' if dry_run else ''}Regenerating index pages...")
    print(f"Reading meditation files from: {meditations_dir}")
    print()

    # Read all meditation files
    html_files = sorted(meditations_dir.glob('*.html'))
    all_data = []

    for filepath in html_files:
        try:
            data = extract_meditation_data(filepath)
            all_data.append(data)
        except Exception as e:
            print(f"Error reading {filepath.name}: {e}")

    print(f"Read {len(all_data)} meditation files")
    print()

    # Generate and write each index page
    pages = [
        ('chronological.html', generate_chronological_html(all_data)),
        ('advent.html', generate_season_html(all_data, 'Advent', 'Advent Meditations')),
        ('christmas.html', generate_season_html(all_data, 'Christmas', 'Christmas Meditations')),
        ('epiphany.html', generate_season_html(all_data, 'Epiphany', 'Epiphany Meditations')),
        ('lent.html', generate_season_html(all_data, 'Lent', 'Lent Meditations')),
        ('easter.html', generate_season_html(all_data, 'Easter', 'Easter Meditations')),
        ('ordinary-time.html', generate_season_html(all_data, 'Ordinary Time', 'Ordinary Time Meditations')),
        ('special.html', generate_season_html(all_data, 'Special', 'Special Meditations')),
        ('by-year.html', generate_by_year_html(all_data)),
        ('by-season.html', generate_by_season_html(all_data)),
        ('lectionary-year.html', generate_lectionary_year_html(all_data)),
        ('title-index.html', generate_title_index_html(all_data)),
        ('scripture-index.html', generate_scripture_index_html(all_data)),
        ('appendix-statistics.html', generate_appendix_statistics_html(all_data)),
    ]

    for filename, content in pages:
        filepath = website_dir / filename
        if dry_run:
            print(f"Would write: {filename} ({len(content)} bytes)")
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Wrote: {filename} ({len(content)} bytes)")

    print()
    print("Done!")

    if dry_run:
        print()
        print("Run without --dry-run to write files.")


if __name__ == '__main__':
    main()
