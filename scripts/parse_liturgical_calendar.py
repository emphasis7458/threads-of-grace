#!/usr/bin/env python3
"""
Parse the liturgical calendar CSV and convert to a structured JSON format.

The CSV has all data in column A with row types:
- year_header: "For the Year YYYY"
- serial_date: Excel serial date (like "39417")
- month_header: "Month YYYY" (like "January 2008", "February 2009")
- day: Just a number 1-31
- occasion: Liturgical occasion name
- service_type: "Early", "Principal", "Evening"
- proper: "Proper N"
- note: Lines with "Note:", "(white)", parentheses, etc.
- blank: Empty lines

Output: JSON with structure:
{
    "2008-01-06": {
        "date": "2008-01-06",
        "occasion": "The Epiphany",
        "proper": null,
        "service_type": null,
        "year": "A"  # Lectionary year
    },
    ...
}
"""

import csv
import json
import re
from datetime import datetime, timedelta
from pathlib import Path


def excel_serial_to_date(serial):
    """Convert Excel serial date to Python date."""
    # Excel's epoch is December 30, 1899
    # But there's a bug where Excel thinks 1900 was a leap year
    excel_epoch = datetime(1899, 12, 30)
    return excel_epoch + timedelta(days=serial)


def classify_row(text):
    """Classify a row based on its content."""
    text = text.strip()

    if not text:
        return 'blank', None

    # Year header
    if 'For the Year' in text:
        match = re.search(r'(\d{4})', text)
        if match:
            return 'year_header', int(match.group(1))
        return 'year_header', None

    # Month header (e.g., "January 2008", "February 2009")
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    for month in months:
        if text.startswith(month) or text.lstrip().startswith(month):
            match = re.search(rf'{month}\s+(\d{{4}})', text)
            if match:
                month_num = months.index(month) + 1
                year = int(match.group(1))
                return 'month_header', (year, month_num)

    # Serial date (Excel serial number like "39,417" or "39417")
    clean_text = text.replace(',', '').replace('"', '').strip()
    try:
        num = int(clean_text)
        if num > 35000 and num < 50000:  # Reasonable Excel date range for 1995-2036
            date = excel_serial_to_date(num)
            return 'serial_date', (date.year, date.month)
    except ValueError:
        pass

    # Day number (1-31)
    try:
        num = int(text)
        if 1 <= num <= 31:
            return 'day', num
    except ValueError:
        pass

    # Service type
    if text in ['Early', 'Principal', 'Evening'] or 'Service' in text:
        return 'service_type', text

    # Day of week
    if text in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
        return 'day_of_week', text

    # Proper
    if text.startswith('Proper'):
        match = re.search(r'Proper\s*(\d+)', text)
        if match:
            return 'proper', int(match.group(1))
        return 'proper', text

    # Note
    if ('Note:' in text or '(white)' in text or '(White' in text or
        text.startswith('(') or 'may be celebrated' in text or
        'may always be' in text or 'Christmas I' in text):
        return 'note', text

    # Otherwise it's an occasion
    return 'occasion', text


def get_lectionary_year(advent_year):
    """
    Determine the lectionary year (A, B, or C) for a given Advent year.
    The lectionary year starts on the first Sunday of Advent.

    Based on the Episcopal Church lectionary cycle:
    - Advent 2007 begins Year A
    - Advent 2008 begins Year B
    - Advent 2009 begins Year C
    - Advent 2010 begins Year A (cycle repeats)
    ... and so on

    The pattern is: (advent_year - 2007) % 3
    - 0 = Year A
    - 1 = Year B
    - 2 = Year C
    """
    offset = (advent_year - 2007) % 3
    if offset == 0:
        return 'A'
    elif offset == 1:
        return 'B'
    else:
        return 'C'


def save_entry(entries, current_year, current_month, current_day, current_occasion, current_proper, current_service_types):
    """Save an entry to the entries dict."""
    if current_day and current_occasion and current_year and current_month:
        date_str = f"{current_year}-{current_month:02d}-{current_day:02d}"

        # Determine the Advent year this date belongs to.
        # The lectionary year runs from Advent (late Nov/early Dec) through
        # Christ the King Sunday (late Nov the following year).
        #
        # For dates Jan 1 through late November (before Advent), the Advent year
        # is the PREVIOUS calendar year (e.g., Feb 2008 is part of Advent 2007 cycle).
        #
        # For dates from Advent through Dec 31, the Advent year is the CURRENT
        # calendar year (e.g., Dec 2007 Advent dates are part of Advent 2007 cycle).

        advent_year = current_year
        occasion_lower = (current_occasion or '').lower()

        if current_month <= 10:  # January through October - always previous Advent
            advent_year = current_year - 1
        elif current_month == 11:  # November - depends on whether it's Advent or before
            if 'advent' in occasion_lower:
                advent_year = current_year  # Advent starts new cycle
            else:
                advent_year = current_year - 1  # Before Advent, still old cycle
        else:  # December - always current Advent year
            advent_year = current_year

        entries[date_str] = {
            'date': date_str,
            'occasion': current_occasion,
            'proper': current_proper,
            'service_types': current_service_types if current_service_types else None,
            'lectionary_year': get_lectionary_year(advent_year)
        }


def parse_liturgical_calendar(csv_path):
    """Parse the liturgical calendar CSV file."""
    entries = {}

    current_year = None
    current_month = None
    current_day = None
    current_occasion = None
    current_proper = None
    current_service_types = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)

        for row in reader:
            if not row:
                continue

            text = row[0].strip()
            row_type, value = classify_row(text)

            if row_type == 'blank':
                continue

            elif row_type == 'year_header':
                # Save any pending entry before changing year
                save_entry(entries, current_year, current_month, current_day,
                          current_occasion, current_proper, current_service_types)
                current_day = None
                current_occasion = None
                current_proper = None
                current_service_types = []

                if value:
                    current_year = value
                    # For year headers without a following month header,
                    # assume December (for Advent start)
                    current_month = 12

            elif row_type == 'month_header':
                current_year, current_month = value

            elif row_type == 'serial_date':
                year, month = value
                current_year = year
                current_month = month

            elif row_type == 'day_of_week':
                # Just skip day of week rows
                pass

            elif row_type == 'day':
                # Save previous entry if we have one
                save_entry(entries, current_year, current_month, current_day,
                          current_occasion, current_proper, current_service_types)

                # Start new entry
                current_day = value
                current_occasion = None
                current_proper = None
                current_service_types = []

            elif row_type == 'occasion':
                if current_occasion:
                    # Append to existing occasion (multi-line occasions)
                    current_occasion = f"{current_occasion}: {value}"
                else:
                    current_occasion = value

            elif row_type == 'proper':
                current_proper = value

            elif row_type == 'service_type':
                current_service_types.append(value)

            elif row_type == 'note':
                # Skip notes for now
                pass

        # Don't forget the last entry
        save_entry(entries, current_year, current_month, current_day,
                  current_occasion, current_proper, current_service_types)

    return entries


def main():
    import sys

    if len(sys.argv) < 2:
        # Default path
        csv_path = Path(__file__).parent.parent / 'text' / '2007-2024_liturgical_calendar.csv'
    else:
        csv_path = Path(sys.argv[1])

    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    print(f"Parsing: {csv_path}")
    entries = parse_liturgical_calendar(csv_path)

    # Sort by date
    sorted_entries = dict(sorted(entries.items()))

    # Output path
    output_path = csv_path.parent.parent / 'scripts' / 'liturgical_calendar_parsed.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_entries, f, indent=2)

    print(f"Wrote {len(sorted_entries)} entries to: {output_path}")

    # Print some samples
    print("\nSample entries:")
    count = 0
    for date, entry in sorted_entries.items():
        if count < 10:
            print(f"  {date}: {entry['occasion']} (Year {entry['lectionary_year']})")
            count += 1
        else:
            break

    # Print date range
    dates = list(sorted_entries.keys())
    print(f"\nDate range: {dates[0]} to {dates[-1]}")


if __name__ == '__main__':
    main()
