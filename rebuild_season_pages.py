#!/usr/bin/env python3
"""
Rebuild Threads of Grace season pages with correct meditation titles.
This script extracts titles from the actual meditation HTML files and rebuilds
all season pages (advent.html, lent.html, etc.) with proper titles.
"""

import os
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

def extract_title_from_meditation(filepath):
    """Extract the title from a meditation HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Look for title in <h1 class="meditation-title-display">
        h1 = soup.find('h1', class_='meditation-title-display')
        if h1:
            title = h1.get_text(strip=True)
            # Clean up the title
            title = re.sub(r'\s+', ' ', title)
            return title if title else None
        
        return None
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return None

def load_liturgical_database(db_path):
    """Load the liturgical database."""
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def collect_meditation_data(meditations_dir, liturgical_db):
    """Collect data about all meditations."""
    meditation_data = []
    
    # Get all HTML files
    html_files = sorted([f for f in os.listdir(meditations_dir) if f.endswith('.html')])
    
    print(f"Processing {len(html_files)} meditation files...")
    
    for filename in html_files:
        filepath = os.path.join(meditations_dir, filename)
        date_str = filename.replace('.html', '')
        
        # Get liturgical info
        lit_info = liturgical_db.get(date_str, {})
        
        # Extract title
        title = extract_title_from_meditation(filepath)
        
        if not title:
            print(f"  Warning: No title found for {filename}")
            continue
        
        # Parse date
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            date_display = date_obj.strftime('%B %d, %Y')
        except:
            date_display = date_str
        
        meditation_data.append({
            'date': date_str,
            'date_display': date_display,
            'filename': filename,
            'title': title,
            'occasion': lit_info.get('occasion', ''),
            'year': lit_info.get('lectionary_year', '?'),
            'season': lit_info.get('season', 'Ordinary Time'),
            'proper': lit_info.get('proper')
        })
    
    print(f"  Collected {len(meditation_data)} meditations with titles")
    return meditation_data

def format_occasion_with_year(occasion, year, proper_num):
    """Format the occasion text with year designation."""
    if not occasion:
        return ""
    
    # Handle special cases
    if year == "?" or not year:
        return occasion
    
    # If year is already in the occasion, return as-is
    if f"Year {year}" in occasion:
        return occasion
    
    # Add year designation
    return f"{occasion} (Year {year})"

def generate_season_html(season_name, meditations, season_slug):
    """Generate HTML for a season page."""
    
    # Sort meditations by date (newest first)
    sorted_meds = sorted(meditations, key=lambda m: m['date'], reverse=True)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{season_name} Meditations | Threads of Grace</title>
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
            <h2 class="page-title">{season_name} Meditations</h2>
            <p class="meditation-count">{len(sorted_meds)} meditation{"s" if len(sorted_meds) != 1 else ""}</p>
        </div>

        <div class="meditation-listing">
'''
    
    # Add meditation entries
    for med in sorted_meds:
        occasion_text = format_occasion_with_year(
            med['occasion'], 
            med['year'], 
            med['proper']
        )
        
        html += f'''            <article class="meditation-item">
                <a href="meditations/{med['filename']}" class="meditation-link">
                    <h3 class="meditation-title">{med['title']}</h3>
                    <div class="meditation-meta">
                        <span class="meditation-date">{med['date_display']}</span>
                        <span class="meditation-occasion">{occasion_text}</span>
                    </div>
                </a>
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

def rebuild_season_pages(website_dir, liturgical_db_path):
    """Rebuild all season pages with correct titles."""
    
    # Define seasons and their file mappings
    seasons = {
        'Advent': 'advent.html',
        'Christmas': 'christmas.html',
        'Epiphany': 'epiphany.html',
        'Lent': 'lent.html',
        'Easter': 'easter.html',
        'Ordinary Time': 'ordinary-time.html',
        'Special': 'special.html'
    }
    
    meditations_dir = os.path.join(website_dir, 'meditations')
    
    # Load liturgical database
    print("Loading liturgical database...")
    liturgical_db = load_liturgical_database(liturgical_db_path)
    
    # Collect meditation data
    print("\nCollecting meditation data...")
    meditation_data = collect_meditation_data(meditations_dir, liturgical_db)
    
    # Group by season
    print("\nGrouping meditations by season...")
    by_season = {}
    for med in meditation_data:
        season = med['season']
        if season not in by_season:
            by_season[season] = []
        by_season[season].append(med)
    
    # Print season counts
    print("\nSeason counts:")
    for season in sorted(by_season.keys()):
        print(f"  {season}: {len(by_season[season])} meditations")
    
    # Rebuild each season page
    print("\nRebuilding season pages...")
    for season_name, filename in seasons.items():
        meditations = by_season.get(season_name, [])
        
        if not meditations:
            print(f"  Skipping {filename} (no meditations)")
            continue
        
        print(f"  Generating {filename} ({len(meditations)} meditations)...")
        
        # Generate HTML
        html = generate_season_html(season_name, meditations, filename.replace('.html', ''))
        
        # Write file
        output_path = os.path.join(website_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"    ✓ Wrote {filename}")
    
    print("\n✅ Season pages rebuilt successfully!")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rebuild_season_pages.py <website_directory>")
        print("\nExample:")
        print("  python rebuild_season_pages.py /path/to/threads-of-grace-website")
        sys.exit(1)
    
    website_dir = sys.argv[1]
    
    if not os.path.isdir(website_dir):
        print(f"Error: Directory not found: {website_dir}")
        sys.exit(1)
    
    # Look for liturgical database
    liturgical_db_path = os.path.join(os.path.dirname(__file__), 'liturgical_database.json')
    if not os.path.exists(liturgical_db_path):
        # Try project directory
        liturgical_db_path = '/mnt/project/liturgical_database.json'
    
    if not os.path.exists(liturgical_db_path):
        print(f"Error: liturgical_database.json not found")
        print(f"  Looked in: {os.path.dirname(__file__)}")
        print(f"  And: /mnt/project/")
        sys.exit(1)
    
    print(f"Website directory: {website_dir}")
    print(f"Liturgical database: {liturgical_db_path}")
    print("=" * 60)
    
    rebuild_season_pages(website_dir, liturgical_db_path)

if __name__ == '__main__':
    main()
