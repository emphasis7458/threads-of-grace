#!/usr/bin/env python3
"""
Fix meditation HTML files where the readings field shows occasion instead of scripture.

Strategy:
1. Check if the <title> tag contains scripture references (book names like Genesis, Psalm, etc.)
2. If yes, extract those readings and put them in the meditation-readings div
3. Also fix the <title> to show the meditation title instead of readings

Special cases:
- Palm Sunday: has "Liturgy of the Palms" and "Liturgy of the Word" sections
- Some files have readings in the first <p> of content instead
- Empty readings: leave as-is if no scripture found
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

# Scripture book names for detecting readings (actual Bible books only)
SCRIPTURE_BOOKS = [
    'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
    'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', 'I Samuel', 'II Samuel',
    '1 Kings', '2 Kings', 'I Kings', 'II Kings',
    '1 Chronicles', '2 Chronicles', 'I Chronicles', 'II Chronicles',
    'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Psalms', 'Proverbs',
    'Ecclesiastes', 'Song of Solomon', 'Song of Songs', 'Canticle',
    'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel',
    'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah',
    'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
    'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
    '1 Corinthians', '2 Corinthians', 'I Corinthians', 'II Corinthians',
    'Galatians', 'Ephesians', 'Philippians', 'Colossians',
    '1 Thessalonians', '2 Thessalonians', 'I Thessalonians', 'II Thessalonians',
    '1 Timothy', '2 Timothy', 'I Timothy', 'II Timothy',
    'Titus', 'Philemon', 'Hebrews', 'James',
    '1 Peter', '2 Peter', 'I Peter', 'II Peter',
    '1 John', '2 John', '3 John', 'I John', 'II John', 'III John',
    'Jude', 'Revelation', 'Sirach', 'Wisdom', 'Baruch'
    # Note: "Liturgy of the Palms/Word" is NOT scripture - it's a header
]

# Create regex pattern for scripture detection
SCRIPTURE_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(book) for book in SCRIPTURE_BOOKS) + r')\b',
    re.IGNORECASE
)


def contains_scripture(text):
    """Check if text contains scripture references."""
    if not text:
        return False
    return bool(SCRIPTURE_PATTERN.search(text))


def extract_readings_from_title(title_text):
    """
    Extract scripture readings from a title string.
    Title format is usually: "Scripture References | Threads of Grace"
    """
    if not title_text:
        return None

    # Remove " | Threads of Grace" suffix
    if '|' in title_text:
        readings = title_text.split('|')[0].strip()
    else:
        readings = title_text.replace(' | Threads of Grace', '').strip()

    # Check if what remains looks like scripture
    if contains_scripture(readings):
        return readings

    return None


def extract_readings_from_content(soup):
    """
    Try to extract scripture readings from the first paragraph of content.
    Some meditations have the readings as the first <p> in meditation-content.
    """
    content_div = soup.find('div', class_='meditation-content')
    if not content_div:
        return None

    # Get first paragraph
    first_p = content_div.find('p')
    if not first_p:
        return None

    text = first_p.get_text().strip()

    # Check if it looks like scripture references (short, contains book names)
    # Scripture lines are typically short and contain commas separating references
    if len(text) < 200 and contains_scripture(text):
        # Make sure it's not the start of the meditation text
        # Scripture lines usually don't have common English words like "The", "In", "When"
        if not re.match(r'^(The|In|When|As|Our|Today|This|It|We|He|She|They)\s', text):
            return text

    return None


def get_meditation_title(soup):
    """Get the meditation title from the h1.meditation-title-display element."""
    title_elem = soup.find('h1', class_='meditation-title-display')
    if title_elem:
        return title_elem.get_text().strip()
    return None


def fix_meditation_file(filepath, dry_run=True):
    """
    Fix a single meditation file.
    Returns: (changed, message)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Get current values
    title_tag = soup.find('title')
    readings_div = soup.find('div', class_='meditation-readings')
    meditation_title = get_meditation_title(soup)

    if not title_tag or not readings_div:
        return False, "Missing title or readings div"

    title_text = title_tag.get_text().strip()
    current_readings = readings_div.get_text().strip()

    # Check if readings already look correct (contain scripture)
    if contains_scripture(current_readings):
        return False, "Readings already contain scripture"

    # Try to extract readings from title
    new_readings = extract_readings_from_title(title_text)

    # If not in title, try first paragraph of content
    if not new_readings:
        new_readings = extract_readings_from_content(soup)

    if not new_readings:
        return False, "Could not find scripture readings"

    # Check if title needs fixing (has readings instead of meditation title)
    title_needs_fix = contains_scripture(title_text) and meditation_title

    changes = []

    # Fix the readings div
    if new_readings != current_readings:
        changes.append(f"readings: '{current_readings}' -> '{new_readings}'")
        if not dry_run:
            readings_div.string = new_readings

    # Fix the title tag if needed
    if title_needs_fix:
        new_title = f"{meditation_title} | Threads of Grace"
        if title_text != new_title:
            changes.append(f"title: '{title_text}' -> '{new_title}'")
            if not dry_run:
                title_tag.string = new_title

    if not changes:
        return False, "No changes needed"

    if not dry_run:
        # Write the file back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))

    return True, "; ".join(changes)


def main():
    import sys

    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    meditations_dir = Path(__file__).parent.parent / 'meditations'

    if not meditations_dir.exists():
        print(f"Error: meditations directory not found: {meditations_dir}")
        sys.exit(1)

    print(f"{'DRY RUN - ' if dry_run else ''}Fixing meditation readings...")
    print(f"Scanning: {meditations_dir}")
    print()

    html_files = sorted(meditations_dir.glob('*.html'))

    fixed_count = 0
    error_count = 0
    skipped_count = 0

    for filepath in html_files:
        try:
            changed, message = fix_meditation_file(filepath, dry_run=dry_run)

            if changed:
                fixed_count += 1
                print(f"{'Would fix' if dry_run else 'Fixed'}: {filepath.name}")
                if verbose:
                    print(f"  {message}")
            else:
                skipped_count += 1
                if verbose:
                    print(f"Skipped: {filepath.name} - {message}")

        except Exception as e:
            error_count += 1
            print(f"Error processing {filepath.name}: {e}")

    print()
    print(f"Summary:")
    print(f"  {'Would fix' if dry_run else 'Fixed'}: {fixed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")

    if dry_run:
        print()
        print("Run without --dry-run to apply changes.")


if __name__ == '__main__':
    main()
