#!/usr/bin/env python3
"""
Add missing meditations to chronological.html

Finds meditation HTML files that aren't in chronological.html and adds them.
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from collections import defaultdict


def get_meditation_info(filepath):
    """Extract info from a meditation HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    info = {
        'date': filepath.stem,
        'title': None,
        'occasion': None,
        'scripture': None,
        'season': None
    }
    
    # Get title
    h1 = soup.find('h1', class_='meditation-title-display')
    if h1:
        info['title'] = h1.get_text(strip=True)
    
    # Get occasion
    occ_div = soup.find('div', class_='meditation-occasion')
    if occ_div:
        info['occasion'] = occ_div.get_text(strip=True)
    
    # Get scripture readings
    readings_div = soup.find('div', class_='meditation-readings')
    if readings_div:
        info['scripture'] = readings_div.get_text(strip=True)
    
    # Determine season from occasion
    if info['occasion']:
        occ_lower = info['occasion'].lower()
        if 'advent' in occ_lower:
            info['season'] = 'Advent'
        elif 'christmas' in occ_lower:
            info['season'] = 'Christmas'
        elif 'epiphany' in occ_lower:
            info['season'] = 'Epiphany'
        elif 'lent' in occ_lower or 'palm sunday' in occ_lower or 'ash wednesday' in occ_lower:
            info['season'] = 'Lent'
        elif 'easter' in occ_lower:
            info['season'] = 'Easter'
        elif 'pentecost' in occ_lower and 'after' not in occ_lower:
            info['season'] = 'Pentecost'
        elif 'trinity' in occ_lower or 'after pentecost' in occ_lower or 'proper' in occ_lower:
            info['season'] = 'Ordinary Time'
        elif any(x in occ_lower for x in ['all saints', 'christ the king', 'holy name', 'transfiguration']):
            info['season'] = 'Special'
    
    return info


def format_date_display(date_str):
    """Convert 2012-01-15 to January 15, 2012"""
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return dt.strftime('%B %d, %Y').replace(' 0', ' ')  # Remove leading zero from day


def create_entry_html(info):
    """Create the HTML for a chronological.html entry."""
    date_display = format_date_display(info['date'])
    
    # Truncate scripture if too long
    scripture = info['scripture'] or ''
    if len(scripture) > 80:
        scripture = scripture[:77] + '...'
    
    html = f'''                <li>
                    <a href="meditations/{info['date']}.html" class="meditation-link">
                        {info['title'] or 'Untitled'}
                    </a>
                    <div class="meditation-meta">
                        {date_display} • {info['occasion'] or 'Unknown occasion'}
                    </div>
                    <div class="meditation-scripture">{scripture}</div>
                </li>'''
    return html


def find_year_section(soup, year):
    """Find the <ul> for a specific year in chronological.html."""
    # Look for h2 with the year (could be various formats)
    for h2 in soup.find_all('h2'):
        h2_text = h2.get_text()
        if str(year) in h2_text:
            # Find the next ul.meditation-list
            ul = h2.find_next('ul', class_='meditation-list')
            return h2, ul
    
    # Also check h3 tags
    for h3 in soup.find_all('h3'):
        h3_text = h3.get_text()
        if str(year) in h3_text:
            ul = h3.find_next('ul', class_='meditation-list')
            return h3, ul
    
    return None, None


def create_year_section(soup, year, main_container):
    """Create a new year section and insert it in the right place."""
    # Create the h2 and ul
    new_h2 = soup.new_tag('h2', attrs={'class': 'year-heading'})
    new_h2.string = str(year)
    
    new_ul = soup.new_tag('ul', attrs={'class': 'meditation-list'})
    
    # Find where to insert (years should be in descending order)
    # Look for the first year heading that is less than our year
    inserted = False
    for h2 in main_container.find_all(['h2', 'h3']):
        h2_text = h2.get_text()
        # Extract year from heading
        year_match = re.search(r'(20\d{2})', h2_text)
        if year_match:
            existing_year = int(year_match.group(1))
            if existing_year < year:
                # Insert before this heading
                h2.insert_before(new_h2)
                new_h2.insert_after(new_ul)
                inserted = True
                break
    
    if not inserted:
        # Add at the end
        main_container.append(new_h2)
        main_container.append(new_ul)
    
    return new_h2, new_ul


def main():
    if len(sys.argv) < 2:
        print("Usage: python add_missing_to_chrono.py /path/to/website [--dry-run]")
        sys.exit(1)
    
    dry_run = '--dry-run' in sys.argv
    website_dir = Path(sys.argv[1])
    meditations_dir = website_dir / 'meditations'
    chrono_path = website_dir / 'chronological.html'
    
    # Get all meditation file dates
    file_dates = set()
    for html_file in meditations_dir.glob('*.html'):
        date_str = html_file.stem
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            file_dates.add(date_str)
    
    # Get all dates in chronological.html
    with open(chrono_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    chrono_dates = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        match = re.search(r'(\d{4}-\d{2}-\d{2})', href)
        if match:
            chrono_dates.add(match.group(1))
    
    # Find missing
    missing = file_dates - chrono_dates
    
    print(f"Meditation files: {len(file_dates)}")
    print(f"In chronological.html: {len(chrono_dates)}")
    print(f"Missing: {len(missing)}")
    
    # Debug: show existing year headings
    print(f"\nExisting year headings in chronological.html:")
    for h2 in soup.find_all(['h2', 'h3']):
        text = h2.get_text(strip=True)
        if re.search(r'20\d{2}', text):
            print(f"  {h2.name}: '{text}'")
    
    if not missing:
        print("\nNo missing entries!")
        return
    
    # Group missing by year
    by_year = defaultdict(list)
    for date in sorted(missing):
        year = int(date[:4])
        by_year[year].append(date)
    
    print(f"\nMissing entries by year:")
    for year in sorted(by_year.keys()):
        print(f"  {year}: {len(by_year[year])} entries")
    
    if dry_run:
        print("\n[DRY RUN] Would add these entries:")
        for year in sorted(by_year.keys()):
            print(f"\n--- {year} ---")
            for date in by_year[year][:3]:  # Show first 3
                info = get_meditation_info(meditations_dir / f"{date}.html")
                print(f"  {date}: {info['title']}")
            if len(by_year[year]) > 3:
                print(f"  ... and {len(by_year[year]) - 3} more")
        print("\nRun without --dry-run to apply changes.")
        return
    
    # Add entries to chronological.html
    print("\nAdding entries...")
    
    # Find the main container for year sections
    # Usually it's a main tag, article, or specific div
    main_container = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
    if not main_container:
        # Fall back to body
        main_container = soup.find('body')
    
    added = 0
    for year in sorted(by_year.keys(), reverse=True):
        dates = sorted(by_year[year], reverse=True)  # Most recent first within year
        
        h2, ul = find_year_section(soup, year)
        
        if not ul:
            print(f"  Creating section for {year}...")
            h2, ul = create_year_section(soup, year, main_container)
            if not ul:
                print(f"  ERROR: Could not create section for {year}")
                continue
        
        # Get existing dates in this section to find insertion point
        existing_in_section = []
        for li in ul.find_all('li', recursive=False):
            link = li.find('a', href=True)
            if link:
                match = re.search(r'(\d{4}-\d{2}-\d{2})', link['href'])
                if match:
                    existing_in_section.append((match.group(1), li))
        
        existing_in_section.sort(key=lambda x: x[0], reverse=True)
        
        for date in dates:
            info = get_meditation_info(meditations_dir / f"{date}.html")
            entry_html = create_entry_html(info)
            new_li = BeautifulSoup(entry_html, 'html.parser').li
            
            # Find where to insert (maintain reverse chronological order)
            inserted = False
            for existing_date, existing_li in existing_in_section:
                if date > existing_date:
                    existing_li.insert_before(new_li)
                    inserted = True
                    break
            
            if not inserted:
                # Add at the end of the list
                ul.append(new_li)
            
            # Update our tracking
            existing_in_section.append((date, new_li))
            existing_in_section.sort(key=lambda x: x[0], reverse=True)
            
            added += 1
            print(f"  Added: {date} - {info['title']}")
    
    # Save
    if added > 0:
        # Create backup
        backup_path = chrono_path.with_suffix('.html.bak')
        import shutil
        shutil.copy2(chrono_path, backup_path)
        print(f"\nBackup saved to: {backup_path}")
        
        with open(chrono_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"\n✓ Added {added} entries to chronological.html")
    else:
        print("\nNo entries added.")


if __name__ == '__main__':
    main()
