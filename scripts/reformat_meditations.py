#!/usr/bin/env python3
"""
Reformat meditation HTML files to match the proper indented structure.

BeautifulSoup reformatted some files when we edited them, removing indentation
and changing attribute order. This script extracts the data and rewrites
the files in the proper format.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup


def needs_reformatting(filepath):
    """Check if a file needs reformatting (has BeautifulSoup minified format)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Check for the minified format (no indentation before <meta charset)
    return '<meta charset="utf-8"/>' in content or '\n<meta charset=' in content


def extract_data(filepath):
    """Extract all the variable data from a meditation file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Extract title (meditation title | Threads of Grace)
    title_tag = soup.find('title')
    title = title_tag.get_text().strip() if title_tag else ''

    # Extract meditation title from h1
    title_h1 = soup.find('h1', class_='meditation-title-display')
    meditation_title = title_h1.get_text().strip() if title_h1 else ''

    # Extract date
    date_div = soup.find('div', class_='meditation-date-display')
    date = date_div.get_text().strip() if date_div else ''

    # Extract occasion
    occasion_div = soup.find('div', class_='meditation-occasion')
    occasion = occasion_div.get_text().strip() if occasion_div else ''

    # Extract readings
    readings_div = soup.find('div', class_='meditation-readings')
    readings = readings_div.get_text().strip() if readings_div else ''

    # Extract content paragraphs
    content_div = soup.find('div', class_='meditation-content')
    paragraphs = []
    if content_div:
        for p in content_div.find_all('p'):
            paragraphs.append(p.get_text().strip())

    # Extract navigation links
    nav = soup.find('nav', class_='meditation-nav')
    prev_link = None
    next_link = None
    if nav:
        links = nav.find_all('a')
        for link in links:
            href = link.get('href', '')
            if 'prev' in link.get('class', []):
                prev_link = {'href': href, 'text': link.get_text().strip()}
            elif 'next' in link.get('class', []):
                next_link = {'href': href, 'text': link.get_text().strip()}

    return {
        'title': title,
        'meditation_title': meditation_title,
        'date': date,
        'occasion': occasion,
        'readings': readings,
        'paragraphs': paragraphs,
        'prev_link': prev_link,
        'next_link': next_link,
    }


def escape_html(text):
    """Escape HTML special characters in text."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def generate_html(data):
    """Generate properly formatted HTML from extracted data."""
    # Build content paragraphs
    content_paragraphs = '\n'.join(f'            <p>{p}</p>' for p in data['paragraphs'])

    # Build navigation
    if data['prev_link']:
        prev_nav = f'<a href="{data["prev_link"]["href"]}" class="prev">{data["prev_link"]["text"]}</a>'
    else:
        prev_nav = '<span></span>'

    if data['next_link']:
        next_nav = f'<a href="{data["next_link"]["href"]}" class="next">{data["next_link"]["text"]}</a>'
    else:
        next_nav = '<span></span>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['title']}</title>
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
            <div class="meditation-date-display">{data['date']}</div>
            <h1 class="meditation-title-display">{data['meditation_title']}</h1>
            <div class="meditation-occasion">{data['occasion']}</div>
            <div class="meditation-readings">{data['readings']}</div>
        </article>

        <div class="meditation-content">
{content_paragraphs}

            <div class="meditation-author">
                Pat Horn
            </div>
        </div>

        <nav class="meditation-nav">
            {prev_nav}
            <a href="../chronological.html" class="back-to-list">All Meditations</a>
            {next_nav}
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
</html>
'''
    return html


def reformat_file(filepath, dry_run=True):
    """Reformat a single meditation file."""
    if not needs_reformatting(filepath):
        return False, "Already properly formatted"

    try:
        data = extract_data(filepath)

        if not data['meditation_title'] or not data['date']:
            return False, "Missing required data"

        new_html = generate_html(data)

        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_html)

        return True, "Reformatted"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    import sys

    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    meditations_dir = Path(__file__).parent.parent / 'meditations'

    if not meditations_dir.exists():
        print(f"Error: meditations directory not found: {meditations_dir}")
        sys.exit(1)

    print(f"{'DRY RUN - ' if dry_run else ''}Reformatting meditation files...")
    print(f"Scanning: {meditations_dir}")
    print()

    html_files = sorted(meditations_dir.glob('*.html'))

    reformatted_count = 0
    skipped_count = 0
    error_count = 0

    for filepath in html_files:
        changed, message = reformat_file(filepath, dry_run=dry_run)

        if changed:
            reformatted_count += 1
            if verbose:
                print(f"{'Would reformat' if dry_run else 'Reformatted'}: {filepath.name}")
        elif 'Error' in message:
            error_count += 1
            print(f"Error: {filepath.name} - {message}")
        else:
            skipped_count += 1
            if verbose:
                print(f"Skipped: {filepath.name} - {message}")

    print()
    print(f"Summary:")
    print(f"  {'Would reformat' if dry_run else 'Reformatted'}: {reformatted_count}")
    print(f"  Already formatted: {skipped_count}")
    print(f"  Errors: {error_count}")

    if dry_run:
        print()
        print("Run without --dry-run to apply changes.")


if __name__ == '__main__':
    main()
