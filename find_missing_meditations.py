#!/usr/bin/env python3
"""
Find meditations that exist as HTML files but are missing from chronological.html
"""

import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup


def main():
    if len(sys.argv) < 2:
        print("Usage: python find_missing_meditations.py /path/to/website")
        sys.exit(1)
    
    website_dir = Path(sys.argv[1])
    meditations_dir = website_dir / 'meditations'
    chrono_path = website_dir / 'chronological.html'
    
    # Get all meditation file dates
    file_dates = set()
    for html_file in meditations_dir.glob('*.html'):
        date_str = html_file.stem  # e.g., "2024-03-31"
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            file_dates.add(date_str)
    
    print(f"Meditation files found: {len(file_dates)}")
    
    # Get all dates referenced in chronological.html
    chrono_dates = set()
    with open(chrono_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        match = re.search(r'(\d{4}-\d{2}-\d{2})', href)
        if match:
            chrono_dates.add(match.group(1))
    
    print(f"Entries in chronological.html: {len(chrono_dates)}")
    
    # Find differences
    missing_from_chrono = file_dates - chrono_dates
    in_chrono_but_no_file = chrono_dates - file_dates
    
    print(f"\nMissing from chronological.html: {len(missing_from_chrono)}")
    print(f"In chrono but no file: {len(in_chrono_but_no_file)}")
    
    if missing_from_chrono:
        print("\n" + "=" * 60)
        print("MEDITATIONS MISSING FROM CHRONOLOGICAL.HTML:")
        print("=" * 60)
        
        # Group by year
        by_year = {}
        for date in sorted(missing_from_chrono):
            year = date[:4]
            if year not in by_year:
                by_year[year] = []
            by_year[year].append(date)
        
        for year in sorted(by_year.keys()):
            dates = by_year[year]
            print(f"\n{year} ({len(dates)} missing):")
            for date in dates:
                # Get the title from the meditation file
                filepath = meditations_dir / f"{date}.html"
                title = "?"
                occasion = "?"
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                    h1 = soup.find('h1', class_='meditation-title-display')
                    if h1:
                        title = h1.get_text(strip=True)[:40]
                    occ_div = soup.find('div', class_='meditation-occasion')
                    if occ_div:
                        occasion = occ_div.get_text(strip=True)[:50]
                except:
                    pass
                print(f"  {date}: {title}")
                print(f"           {occasion}")
    
    if in_chrono_but_no_file:
        print("\n" + "=" * 60)
        print("IN CHRONOLOGICAL.HTML BUT NO FILE:")
        print("=" * 60)
        for date in sorted(in_chrono_but_no_file):
            print(f"  {date}")


if __name__ == '__main__':
    main()
