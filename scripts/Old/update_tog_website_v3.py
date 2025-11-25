#!/usr/bin/env python3
"""
Threads of Grace Website Update Script v3

Fixes:
1. Extracts title from first <p> in meditation-content div
2. Updates index pages: Title → Date + Occasion → Scripture
3. Updates meditation counts in by-season.html

Usage:
    python update_tog_website_v3.py /Users/larry/Desktop/TOG/threads-of-grace-website --analyze
    python update_tog_website_v3.py /Users/larry/Desktop/TOG/threads-of-grace-website
"""

import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: BeautifulSoup not found. Install with:")
    print("  pip install beautifulsoup4")
    sys.exit(1)


def title_case_smart(text):
    """Convert ALL CAPS to Title Case, handling special cases."""
    if not text:
        return text
    
    # Only convert if mostly uppercase
    if not text.isupper():
        return text
    
    # Words that should stay lowercase (unless first word)
    lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 
                       'on', 'at', 'to', 'from', 'by', 'in', 'of', 'with', 'as'}
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        if i == 0:
            result.append(word.capitalize())
        elif word.lower() in lowercase_words:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def extract_title_from_meditation(filepath):
    """Extract the title from first <p> in meditation-content div."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # The title is the first <p> inside the meditation-content div
        content_div = soup.find('div', class_='meditation-content')
        if content_div:
            first_p = content_div.find('p')
            if first_p:
                title = first_p.get_text(strip=True)
                # Titles are typically ALL CAPS and short
                # Skip if it looks like body text (too long or has periods mid-text)
                if len(title) < 100 and not re.search(r'\.\s+[A-Z]', title):
                    return title
        
        return None
    except Exception as e:
        return None


def extract_scripture_from_meditation(filepath):
    """Extract scripture from meditation-title-display h1."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        title_h1 = soup.find('h1', class_='meditation-title-display')
        if title_h1:
            return title_h1.get_text(strip=True)
        
        return None
    except:
        return None


def build_meditation_data(meditations_dir):
    """Build a dictionary of meditation data from individual files."""
    print(f"Reading meditation files from {meditations_dir}...")
    
    data = {}
    found_titles = 0
    missing_titles = []
    
    for html_file in sorted(Path(meditations_dir).glob('*.html')):
        date_str = html_file.stem  # e.g., "2024-03-31"
        
        title = extract_title_from_meditation(html_file)
        scripture = extract_scripture_from_meditation(html_file)
        
        data[date_str] = {
            'title': title,
            'scripture': scripture,
            'file': html_file.name
        }
        
        if title:
            found_titles += 1
        else:
            missing_titles.append(date_str)
    
    print(f"  Found {found_titles} titles out of {len(data)} meditation files")
    if missing_titles and len(missing_titles) <= 10:
        print(f"  Missing titles for: {', '.join(missing_titles[:10])}")
    elif missing_titles:
        print(f"  Missing titles for {len(missing_titles)} files")
    
    return data


def backup_file(filepath):
    """Create a backup of the file."""
    backup_dir = filepath.parent / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"{filepath.stem}_{timestamp}{filepath.suffix}"
    shutil.copy2(filepath, backup_path)
    return backup_path


def update_chronological_html(filepath, meditation_data, analyze_only=False):
    """Update chronological.html to show title first."""
    print(f"\nProcessing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Find all meditation lists
    meditation_lists = soup.find_all('ul', class_='meditation-list')
    print(f"  Found {len(meditation_lists)} meditation list(s)")
    
    entries_updated = 0
    entries_total = 0
    
    for ul in meditation_lists:
        for li in ul.find_all('li', recursive=False):
            entries_total += 1
            
            link = li.find('a', class_='meditation-link')
            meta = li.find('div', class_='meditation-meta')
            
            if not link:
                continue
            
            # Get date from href
            href = link.get('href', '')
            match = re.search(r'(\d{4}-\d{2}-\d{2})', href)
            if not match:
                continue
            
            date_str = match.group(1)
            
            # Get current link text (scripture readings)
            current_scripture = link.get_text(strip=True)
            
            # Get title from meditation data
            if date_str not in meditation_data:
                continue
            
            med_data = meditation_data[date_str]
            title = med_data.get('title')
            
            if not title:
                # Use scripture as fallback
                continue
            
            title_formatted = title_case_smart(title)
            
            if analyze_only:
                if entries_updated < 5:
                    print(f"\n  Sample: {date_str}")
                    print(f"    Title: {title_formatted}")
                    print(f"    Scripture: {current_scripture[:60]}...")
                entries_updated += 1
                continue
            
            # Update the link text to be the title
            link.string = title_formatted
            
            # Add scripture as a new div after meta
            scripture_div = li.find('div', class_='meditation-scripture')
            if not scripture_div and meta:
                scripture_div = soup.new_tag('div')
                scripture_div['class'] = 'meditation-scripture'
                scripture_div.string = current_scripture
                meta.insert_after(scripture_div)
            
            entries_updated += 1
    
    print(f"  Entries found: {entries_total}")
    
    if analyze_only:
        print(f"  Entries with titles: {entries_updated}")
        return entries_updated
    
    # Add CSS for scripture div
    style_tag = soup.find('style')
    if style_tag:
        style_content = style_tag.string or ""
        if 'meditation-scripture' not in style_content:
            additional_css = """
        .meditation-scripture {
            font-family: 'Crimson Pro', serif;
            font-size: 0.9rem;
            color: var(--color-text-light);
            font-style: italic;
            margin-top: 0.25rem;
        }
"""
            style_tag.string = style_content + additional_css
    
    # Update total count in page intro
    count_elem = soup.find('p', class_='meditation-count')
    if count_elem:
        total = len(meditation_data)
        text = count_elem.get_text()
        new_text = re.sub(r'\d+\s*meditations', f'{total} meditations', text)
        count_elem.string = new_text
    
    # Backup and write
    backup_path = backup_file(filepath)
    print(f"  Backup: {backup_path.name}")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"  ✓ Updated {entries_updated} entries")
    return entries_updated


def update_season_page(filepath, meditation_data, analyze_only=False):
    """Update a season index page."""
    if not filepath.exists():
        return 0
    
    print(f"\nProcessing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    meditation_lists = soup.find_all('ul', class_='meditation-list')
    if not meditation_lists:
        print("  No meditation-list found")
        return 0
    
    entries_updated = 0
    
    for ul in meditation_lists:
        for li in ul.find_all('li', recursive=False):
            link = li.find('a', class_='meditation-link')
            meta = li.find('div', class_='meditation-meta')
            
            if not link:
                continue
            
            href = link.get('href', '')
            match = re.search(r'(\d{4}-\d{2}-\d{2})', href)
            if not match:
                continue
            
            date_str = match.group(1)
            
            if date_str not in meditation_data:
                continue
            
            med_data = meditation_data[date_str]
            title = med_data.get('title')
            
            if not title:
                continue
            
            current_scripture = link.get_text(strip=True)
            title_formatted = title_case_smart(title)
            
            if analyze_only:
                entries_updated += 1
                continue
            
            link.string = title_formatted
            
            scripture_div = li.find('div', class_='meditation-scripture')
            if not scripture_div and meta:
                scripture_div = soup.new_tag('div')
                scripture_div['class'] = 'meditation-scripture'
                scripture_div.string = current_scripture
                meta.insert_after(scripture_div)
            
            entries_updated += 1
    
    if analyze_only:
        print(f"  Found {entries_updated} entries with titles")
        return entries_updated
    
    if entries_updated > 0:
        style_tag = soup.find('style')
        if style_tag:
            style_content = style_tag.string or ""
            if 'meditation-scripture' not in style_content:
                additional_css = """
        .meditation-scripture {
            font-family: 'Crimson Pro', serif;
            font-size: 0.9rem;
            color: var(--color-text-light);
            font-style: italic;
            margin-top: 0.25rem;
        }
"""
                style_tag.string = style_content + additional_css
        
        backup_path = backup_file(filepath)
        print(f"  Backup: {backup_path.name}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    
    print(f"  ✓ Updated {entries_updated} entries")
    return entries_updated


def count_meditations_by_season(meditations_dir):
    """Count meditations in each season."""
    season_counts = defaultdict(int)
    
    for html_file in Path(meditations_dir).glob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Check occasion div for season
        if 'advent' in content and ('first sunday of advent' in content or 
            'second sunday of advent' in content or 
            'third sunday of advent' in content or 
            'fourth sunday of advent' in content):
            season_counts['Advent'] += 1
        elif 'christmas' in content:
            season_counts['Christmas'] += 1
        elif 'epiphany' in content:
            season_counts['Epiphany'] += 1
        elif any(x in content for x in ['in lent', 'palm sunday', 'ash wednesday']):
            season_counts['Lent'] += 1
        elif 'easter' in content:
            season_counts['Easter'] += 1
        elif 'day of pentecost' in content:
            season_counts['Pentecost'] += 1
        elif 'trinity sunday' in content or 'after pentecost' in content:
            season_counts['Ordinary Time'] += 1
        elif any(x in content for x in ['all saints', 'christ the king', 'transfiguration', 'holy name', 'presentation']):
            season_counts['Special'] += 1
        else:
            season_counts['Other'] += 1
    
    return dict(season_counts)


def update_by_season_html(filepath, season_counts, analyze_only=False):
    """Update by-season.html with correct counts."""
    print(f"\nProcessing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
    
    # Find all season cards
    season_cards = soup.find_all('a', class_='season-card')
    print(f"  Found {len(season_cards)} season cards")
    
    updates = 0
    
    # Map card names to our count keys
    season_map = {
        'advent': 'Advent',
        'christmas': 'Christmas',
        'epiphany': 'Epiphany',
        'lent': 'Lent',
        'easter': 'Easter',
        'pentecost': 'Pentecost',
        'ordinary time': 'Ordinary Time',
        'special': 'Special'
    }
    
    for card in season_cards:
        h3 = card.find('h3')
        p = card.find('p')
        
        if not h3 or not p:
            continue
        
        card_name = h3.get_text(strip=True).lower()
        
        for key, season in season_map.items():
            if key in card_name:
                count = season_counts.get(season, 0)
                current_text = p.get_text(strip=True)
                new_text = f"{count} meditations"
                
                if analyze_only:
                    print(f"    {season}: {current_text} → {new_text}")
                else:
                    p.string = new_text
                
                updates += 1
                break
    
    if analyze_only:
        return
    
    if updates > 0:
        backup_path = backup_file(filepath)
        print(f"  Backup: {backup_path.name}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"  ✓ Updated {updates} season counts")
    else:
        print("  No season cards updated")


def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)
    
    analyze_only = '--analyze' in args
    args = [a for a in args if not a.startswith('--')]
    
    if not args:
        print("Error: Please provide the website directory path")
        sys.exit(1)
    
    website_dir = Path(args[0])
    
    if not website_dir.exists():
        print(f"Error: Directory not found: {website_dir}")
        sys.exit(1)
    
    print(f"{'Analyzing' if analyze_only else 'Updating'} Threads of Grace website")
    print(f"Directory: {website_dir}")
    print("=" * 60)
    
    # Build meditation data
    meditations_dir = website_dir / 'meditations'
    if not meditations_dir.exists():
        print(f"Error: meditations directory not found")
        sys.exit(1)
    
    meditation_data = build_meditation_data(meditations_dir)
    
    # Show samples
    print("\nSample titles extracted:")
    samples = [(d, m) for d, m in sorted(meditation_data.items(), reverse=True) if m.get('title')]
    for i, (date, data) in enumerate(samples[:5]):
        title = title_case_smart(data['title'])
        print(f"  {date}: {title}")
    
    # Update chronological.html
    chrono_path = website_dir / 'chronological.html'
    if chrono_path.exists():
        update_chronological_html(chrono_path, meditation_data, analyze_only)
    
    # Update season pages
    season_pages = ['advent.html', 'christmas.html', 'epiphany.html',
                    'lent.html', 'easter.html', 'pentecost.html',
                    'ordinary-time.html', 'special.html']
    
    for page in season_pages:
        page_path = website_dir / page
        update_season_page(page_path, meditation_data, analyze_only)
    
    # Count and update by-season.html
    print("\n" + "=" * 60)
    season_counts = count_meditations_by_season(meditations_dir)
    print("SEASON COUNTS:")
    total = 0
    for season, count in sorted(season_counts.items()):
        print(f"  {season}: {count}")
        total += count
    print(f"  TOTAL: {total}")
    
    by_season_path = website_dir / 'by-season.html'
    if by_season_path.exists():
        update_by_season_html(by_season_path, season_counts, analyze_only)
    
    print("\n" + "=" * 60)
    if analyze_only:
        print("Analysis complete. Run without --analyze to make changes.")
    else:
        print("✓ Update complete!")
        print("\nBackups in: backups/ directory")
        print("Review changes and test locally.")


if __name__ == '__main__':
    main()
