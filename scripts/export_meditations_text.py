#!/usr/bin/env python3
"""
Export all meditations to a single text file.

Format for each meditation:
Line 1: Date
Line 2: Occasion
Line 3: Readings
Line 4: (blank)
Line 5: Title
Line 6: (blank)
Line 7+: Meditation paragraphs (separated by blank lines)

Meditations are separated by a clear divider line.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup


def extract_meditation_full(filepath):
    """Extract all data from a meditation HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Get filename for sorting
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

    # Extract occasion (full, including Year and Season)
    occasion_elem = soup.find('div', class_='meditation-occasion')
    occasion = occasion_elem.get_text().strip() if occasion_elem else ''

    # Extract readings
    readings_elem = soup.find('div', class_='meditation-readings')
    readings = readings_elem.get_text().strip() if readings_elem else ''

    # Extract content paragraphs
    content_div = soup.find('div', class_='meditation-content')
    paragraphs = []
    if content_div:
        for p in content_div.find_all('p'):
            text = p.get_text().strip()
            if text:
                paragraphs.append(text)

    return {
        'filename': filename,
        'date': date,
        'date_display': date_display,
        'title': title,
        'occasion': occasion,
        'readings': readings,
        'paragraphs': paragraphs,
    }


def format_meditation(data):
    """Format a single meditation as text."""
    lines = []

    # Line 1: Date
    lines.append(data['date_display'])

    # Line 2: Occasion
    lines.append(data['occasion'])

    # Line 3: Readings
    lines.append(data['readings'])

    # Line 4: blank
    lines.append('')

    # Line 5: Title
    lines.append(data['title'])

    # Line 6: blank
    lines.append('')

    # Paragraphs separated by blank lines
    for i, para in enumerate(data['paragraphs']):
        lines.append(para)
        if i < len(data['paragraphs']) - 1:
            lines.append('')  # Blank line between paragraphs

    return '\n'.join(lines)


def main():
    import sys

    # Get the website directory
    script_dir = Path(__file__).parent
    website_dir = script_dir.parent
    meditations_dir = website_dir / 'meditations'

    if not meditations_dir.exists():
        print(f"Error: meditations directory not found: {meditations_dir}")
        sys.exit(1)

    # Output file
    output_file = website_dir / 'all_meditations.txt'

    print(f"Reading meditation files from: {meditations_dir}")

    # Read all meditation files
    html_files = sorted(meditations_dir.glob('*.html'))
    all_meditations = []

    for filepath in html_files:
        try:
            data = extract_meditation_full(filepath)
            all_meditations.append(data)
        except Exception as e:
            print(f"Error reading {filepath.name}: {e}")

    # Sort by date (oldest first)
    all_meditations.sort(key=lambda x: x['date'] or '')

    print(f"Read {len(all_meditations)} meditation files")

    # Create the divider
    divider = '\n' + '=' * 80 + '\n\n'

    # Build the output
    output_parts = []
    for data in all_meditations:
        output_parts.append(format_meditation(data))

    output_text = divider.join(output_parts)

    # Add a header
    header = f"""THREADS OF GRACE
Meditations on Scripture and the Spiritual Life
by Pat Horn

{len(all_meditations)} meditations from {all_meditations[0]['date_display']} to {all_meditations[-1]['date_display']}

"""
    header += '=' * 80 + '\n\n'

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header + output_text)

    print(f"Wrote: {output_file}")
    print(f"File size: {output_file.stat().st_size:,} bytes")


if __name__ == '__main__':
    main()
