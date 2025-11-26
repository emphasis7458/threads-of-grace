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

    return {
        'filename': filename,
        'date': date,
        'title': title,
        'date_display': date_display,
        'occasion': occasion,
        'occasion_full': occasion_full,
        'season': season,
        'readings': readings,
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
        .meditation-scripture {{
            font-family: 'Crimson Pro', serif;
            font-size: 0.9rem;
            color: var(--color-text-light);
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
            <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; color: var(--color-burgundy); margin-bottom: 1rem;">All Meditations</h2>
            <p>A chronological collection of weekly meditations following the rhythms of the church year.</p>
            <p class="meditation-count">{total} meditations from {date_range}</p>
        </div>

'''

    for year in years:
        entries = sorted(by_year[year], key=lambda x: x['date'], reverse=True)

        html += f'''        <section class="year-section">
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
    """Generate a season index page."""

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
            <h2 class="page-title">{page_title}</h2>
            <p class="meditation-count">{total} meditations</p>
        </div>

        <div class="meditation-listing">
'''

    for entry in season_entries:
        title = escape_html(entry['title'])
        html += f'''            <article class="meditation-item">
                <a class="meditation-link" href="meditations/{entry['filename']}">{title}</a>
            </article>
'''

    html += '''        </div>
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
    """Generate by-year.html with meditations organized by year."""

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
            <h2 class="page-title">Meditations by Year</h2>
            <p class="meditation-count">{total} meditations</p>
        </div>

'''

    for year in years:
        entries = sorted(by_year[year], key=lambda x: x['date'], reverse=True)
        count = len(entries)

        html += f'''        <section class="year-section">
            <h3 class="year-heading">{year} ({count} meditations)</h3>
            <div class="meditation-listing">
'''

        for entry in entries:
            title = escape_html(entry['title'])
            html += f'''                <article class="meditation-item">
                    <a class="meditation-link" href="meditations/{entry['filename']}">{title}</a>
                </article>
'''

        html += '''            </div>
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
