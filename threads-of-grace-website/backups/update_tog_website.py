#!/usr/bin/env python3
"""
Threads of Grace Website Update Script

This script makes two updates to the website:
1. Reformats meditation displays to show title first:
   - Title (title case)
   - Date + Occasion (on one line)
   - Scripture readings

2. Updates meditation counts on by-season.html

Usage:
    python update_tog_website.py /Users/larry/Desktop/TOG/threads-of-grace-website
    python update_tog_website.py /Users/larry/Desktop/TOG/threads-of-grace-website --analyze
    
Options:
    --analyze    Only analyze the structure, don't make changes
    --backup     Create backup files before modifying (default: yes)
"""

import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Check for BeautifulSoup
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: BeautifulSoup not found. Install with:")
    print("  pip install beautifulsoup4")
    sys.exit(1)


def title_case_smart(text):
    """Convert to title case, handling special cases."""
    if not text:
        return text
    
    # Words that should stay lowercase (unless first word)
    lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 
                       'on', 'at', 'to', 'from', 'by', 'in', 'of', 'with'}
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # First word is always capitalized
        if i == 0:
            result.append(word.capitalize())
        elif word.lower() in lowercase_words:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def analyze_html_structure(filepath):
    """Analyze the HTML structure and report what we find."""
    print(f"\n=== Analyzing: {filepath.name} ===")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Look for meditation lists
    meditation_lists = soup.find_all('ul', class_=re.compile(r'meditation'))
    print(f"  Found {len(meditation_lists)} meditation list(s)")
    
    # Look for meditation entries
    meditation_entries = soup.find_all('li', class_=re.compile(r'meditation'))
    print(f"  Found {len(meditation_entries)} meditation entries")
    
    # Analyze first few entries
    if meditation_entries:
        print("\n  Sample entry structure:")
        entry = meditation_entries[0]
        print(f"    Classes: {entry.get('class')}")
        
        link = entry.find('a')
        if link:
            print(f"    Link href: {link.get('href', 'N/A')[:50]}...")
            
            # Show the inner HTML structure
            inner_html = str(link)[:500]
            print(f"    Inner HTML preview:\n      {inner_html[:200]}...")
            
            # Get text content with line breaks preserved
            full_text = link.get_text(separator='|').strip()
            parts = [p.strip() for p in full_text.split('|') if p.strip()]
            print(f"    Text parts ({len(parts)}):")
            for i, part in enumerate(parts[:5]):
                print(f"      [{i}] {part[:60]}{'...' if len(part) > 60 else ''}")
    
    return len(meditation_entries)


def backup_file(filepath):
    """Create a backup of the file."""
    backup_dir = filepath.parent / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"{filepath.stem}_{timestamp}{filepath.suffix}"
    shutil.copy2(filepath, backup_path)
    return backup_path


def update_chronological_html(filepath, analyze_only=False):
    """Update chronological.html to show title first."""
    print(f"\nProcessing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
    
    # Find all meditation entries
    entries = soup.find_all('li', class_=re.compile(r'meditation'))
    print(f"  Found {len(entries)} meditation entries")
    
    if analyze_only:
        if entries:
            analyze_html_structure(filepath)
        return len(entries)
    
    entries_updated = 0
    errors = []
    
    for li in entries:
        link = li.find('a')
        if not link:
            continue
        
        try:
            # Get text content - split by <br> tags
            # The format appears to be:
            # Date (in <strong>)
            # Occasion
            # alternate occasion line (sometimes)
            # Scripture (in <em>)
            # TITLE (all caps)
            
            strong = link.find('strong')
            em = link.find('em')
            
            # Get all text parts
            full_text = link.get_text(separator='\n').strip()
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            
            if len(lines) < 3:
                continue
            
            # Identify components
            date = lines[0] if strong else None
            scripture = em.get_text(strip=True) if em else None
            
            # Find title (usually ALL CAPS at the end)
            title = None
            occasion_lines = []
            
            for i, line in enumerate(lines):
                # Skip date
                if i == 0 and date and line == date:
                    continue
                # Skip scripture
                if scripture and line == scripture:
                    continue
                # Check if this looks like a title (all caps or mostly caps)
                if line.isupper() or (len([c for c in line if c.isupper()]) > len(line) * 0.7):
                    title = line
                else:
                    occasion_lines.append(line)
            
            if not title:
                # Title might be last line even if not all caps
                title = lines[-1]
                occasion_lines = [l for l in lines[1:-1] if l != scripture]
            
            if not date or not title:
                continue
            
            # Format title in title case
            title_formatted = title_case_smart(title)
            
            # Combine occasion lines
            occasion = ' — '.join(occasion_lines) if occasion_lines else ""
            
            # Rebuild the link content
            href = link.get('href', '')
            link.clear()
            
            # New format: Title first
            title_strong = soup.new_tag('strong')
            title_strong.string = title_formatted
            link.append(title_strong)
            link.append(soup.new_tag('br'))
            
            # Date and occasion on one line
            if occasion:
                date_occasion = f"{date} — {occasion}"
            else:
                date_occasion = date
            link.append(date_occasion)
            link.append(soup.new_tag('br'))
            
            # Scripture in em
            if scripture:
                scripture_em = soup.new_tag('em')
                scripture_em.string = scripture
                link.append(scripture_em)
            
            entries_updated += 1
            
        except Exception as e:
            errors.append(f"Entry error: {e}")
    
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors[:3]:
            print(f"    - {err}")
    
    # Write back
    backup_path = backup_file(filepath)
    print(f"  Backup created: {backup_path.name}")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"  ✓ Updated {entries_updated} entries")
    return entries_updated


def update_season_index(filepath, analyze_only=False):
    """Update a season index page to show title first."""
    if not filepath.exists():
        return 0
        
    print(f"\nProcessing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    entries = soup.find_all('li', class_=re.compile(r'meditation'))
    print(f"  Found {len(entries)} meditation entries")
    
    if analyze_only or len(entries) == 0:
        return len(entries)
    
    entries_updated = 0
    
    for li in entries:
        link = li.find('a')
        if not link:
            continue
        
        try:
            strong = link.find('strong')
            em = link.find('em')
            
            full_text = link.get_text(separator='\n').strip()
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            
            if len(lines) < 3:
                continue
            
            date = lines[0] if strong else lines[0]
            scripture = em.get_text(strip=True) if em else None
            
            # Find title and occasion
            title = None
            occasion_lines = []
            
            for i, line in enumerate(lines):
                if i == 0:
                    continue
                if scripture and line == scripture:
                    continue
                if line.isupper() or (len(line) > 3 and sum(1 for c in line if c.isupper()) > len(line) * 0.6):
                    title = line
                else:
                    occasion_lines.append(line)
            
            if not title:
                title = lines[-1]
                occasion_lines = [l for l in lines[1:-1] if l != scripture]
            
            title_formatted = title_case_smart(title)
            occasion = ' — '.join(occasion_lines) if occasion_lines else ""
            
            link.clear()
            
            title_strong = soup.new_tag('strong')
            title_strong.string = title_formatted
            link.append(title_strong)
            link.append(soup.new_tag('br'))
            
            if occasion:
                link.append(f"{date} — {occasion}")
            else:
                link.append(date)
            link.append(soup.new_tag('br'))
            
            if scripture:
                scripture_em = soup.new_tag('em')
                scripture_em.string = scripture
                link.append(scripture_em)
            
            entries_updated += 1
            
        except Exception as e:
            pass
    
    if entries_updated > 0:
        backup_path = backup_file(filepath)
        print(f"  Backup created: {backup_path.name}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    
    print(f"  ✓ Updated {entries_updated} entries")
    return entries_updated


def count_meditations_by_season(meditations_dir):
    """Count meditations in each season by examining the HTML files."""
    print(f"\nCounting meditations in {meditations_dir}...")
    
    season_counts = defaultdict(int)
    total = 0
    
    for html_file in sorted(Path(meditations_dir).glob('*.html')):
        total += 1
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Determine season from content
        if 'advent' in content and 'sunday' in content:
            season_counts['Advent'] += 1
        elif 'christmas' in content:
            season_counts['Christmas'] += 1
        elif 'epiphany' in content:
            season_counts['Epiphany'] += 1
        elif any(x in content for x in ['lent', 'palm sunday', 'ash wednesday']):
            season_counts['Lent'] += 1
        elif 'easter' in content:
            season_counts['Easter'] += 1
        elif 'pentecost' in content:
            if 'day of pentecost' in content:
                season_counts['Pentecost'] += 1
            else:
                season_counts['Ordinary Time'] += 1
        elif 'trinity sunday' in content:
            season_counts['Ordinary Time'] += 1
        elif 'proper' in content:
            season_counts['Ordinary Time'] += 1
        elif any(x in content for x in ['all saints', 'christ the king', 'transfiguration', 'holy name', 'presentation']):
            season_counts['Special'] += 1
        else:
            season_counts['Other'] += 1
    
    print(f"  Total meditation files: {total}")
    return dict(season_counts)


def update_by_season_counts(filepath, season_counts, analyze_only=False):
    """Update the meditation counts on by-season.html."""
    print(f"\nProcessing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if analyze_only:
        # Just show what we'd update
        print("  Current counts in file vs actual:")
        for season, count in sorted(season_counts.items()):
            # Find current count in file
            pattern = rf'{season}[^0-9]*(\d+)\s*meditation'
            match = re.search(pattern, content, re.IGNORECASE)
            current = match.group(1) if match else "?"
            print(f"    {season}: {current} → {count}")
        return
    
    # Update counts using regex
    updates = 0
    
    for season, count in season_counts.items():
        # Pattern to find "Season ... X meditations"
        pattern = rf'({season}[^0-9]*)(\d+)(\s*meditation)'
        
        def replacer(m):
            nonlocal updates
            updates += 1
            return f'{m.group(1)}{count}{m.group(3)}'
        
        content = re.sub(pattern, replacer, content, flags=re.IGNORECASE)
    
    if updates > 0:
        backup_path = backup_file(filepath)
        print(f"  Backup created: {backup_path.name}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ Updated {updates} count(s)")
    else:
        print("  No count patterns found to update")
        print("  You may need to manually update the counts:")
        for season, count in sorted(season_counts.items()):
            print(f"    {season}: {count} meditations")


def main():
    # Parse arguments
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
    
    # 1. Process chronological.html
    chrono_path = website_dir / 'chronological.html'
    if chrono_path.exists():
        update_chronological_html(chrono_path, analyze_only)
    else:
        print(f"\nWarning: {chrono_path} not found")
    
    # 2. Process season index pages
    season_pages = [
        'advent.html', 'christmas.html', 'epiphany.html',
        'lent.html', 'easter.html', 'pentecost.html',
        'ordinary-time.html', 'special.html'
    ]
    
    for page in season_pages:
        page_path = website_dir / page
        if page_path.exists():
            update_season_index(page_path, analyze_only)
    
    # 3. Count meditations and update by-season.html
    meditations_dir = website_dir / 'meditations'
    if meditations_dir.exists():
        season_counts = count_meditations_by_season(meditations_dir)
        
        print("\n" + "=" * 60)
        print("SEASON COUNTS:")
        for season, count in sorted(season_counts.items()):
            print(f"  {season}: {count}")
        print(f"  TOTAL: {sum(season_counts.values())}")
        
        by_season_path = website_dir / 'by-season.html'
        if by_season_path.exists():
            update_by_season_counts(by_season_path, season_counts, analyze_only)
    
    print("\n" + "=" * 60)
    if analyze_only:
        print("Analysis complete. Run without --analyze to make changes.")
    else:
        print("✓ Update complete!")
        print("\nBackups saved to: backups/ directory")
        print("Please review the changes and test the website locally.")


if __name__ == '__main__':
    main()
