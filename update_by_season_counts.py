#!/usr/bin/env python3
"""
Update by-season.html with correct meditation counts.
"""

import os
import json
import re
from bs4 import BeautifulSoup

def load_liturgical_database(db_path):
    """Load the liturgical database."""
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def count_meditations_by_season(meditations_dir, liturgical_db):
    """Count meditations in each season."""
    html_files = [f for f in os.listdir(meditations_dir) if f.endswith('.html')]
    
    season_counts = {
        'Advent': 0,
        'Christmas': 0,
        'Epiphany': 0,
        'Lent': 0,
        'Easter': 0,
        'Ordinary Time': 0,
        'Special': 0
    }
    
    for filename in html_files:
        date_str = filename.replace('.html', '')
        lit_info = liturgical_db.get(date_str, {})
        season = lit_info.get('season', 'Ordinary Time')
        
        if season in season_counts:
            season_counts[season] += 1
    
    return season_counts

def update_by_season_html(website_dir, season_counts):
    """Update by-season.html with correct counts."""
    filepath = os.path.join(website_dir, 'by-season.html')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all season cards
    season_cards = soup.find_all('a', class_='season-card')
    
    for card in season_cards:
        h3 = card.find('h3')
        p = card.find('p')
        
        if not h3 or not p:
            continue
        
        season_name = h3.get_text(strip=True)
        
        # Map display names to internal names
        season_map = {
            'Advent': 'Advent',
            'Christmas': 'Christmas',
            'Epiphany': 'Epiphany',
            'Lent': 'Lent',
            'Easter': 'Easter',
            'Ordinary Time': 'Ordinary Time',
            'Special Occasions': 'Special'
        }
        
        internal_name = season_map.get(season_name)
        
        if internal_name and internal_name in season_counts:
            count = season_counts[internal_name]
            new_text = f"{count} meditation{'s' if count != 1 else ''}"
            p.string = new_text
            print(f"  Updated {season_name}: {new_text}")
    
    # Write updated HTML
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))
    
    print(f"\n✅ Updated {filepath}")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python update_by_season_counts.py <website_directory>")
        print("\nExample:")
        print("  python update_by_season_counts.py /path/to/threads-of-grace-website")
        sys.exit(1)
    
    website_dir = sys.argv[1]
    
    if not os.path.isdir(website_dir):
        print(f"Error: Directory not found: {website_dir}")
        sys.exit(1)
    
    meditations_dir = os.path.join(website_dir, 'meditations')
    
    # Look for liturgical database
    liturgical_db_path = os.path.join(os.path.dirname(__file__), 'liturgical_database.json')
    if not os.path.exists(liturgical_db_path):
        liturgical_db_path = '/mnt/project/liturgical_database.json'
    
    if not os.path.exists(liturgical_db_path):
        print(f"Error: liturgical_database.json not found")
        sys.exit(1)
    
    print(f"Website directory: {website_dir}")
    print(f"Liturgical database: {liturgical_db_path}")
    print("=" * 60)
    
    # Load database and count meditations
    print("\nCounting meditations by season...")
    liturgical_db = load_liturgical_database(liturgical_db_path)
    season_counts = count_meditations_by_season(meditations_dir, liturgical_db)
    
    print("\nCurrent counts:")
    for season, count in sorted(season_counts.items()):
        print(f"  {season}: {count}")
    
    print("\nUpdating by-season.html...")
    update_by_season_html(website_dir, season_counts)

if __name__ == '__main__':
    main()
