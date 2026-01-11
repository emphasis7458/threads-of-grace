#!/usr/bin/env python3
"""
Generate search index for Threads of Grace website.

This script uses the existing meditations-data.json as a base and enriches it
with excerpts, keywords, and referenced spiritual teachers from the HTML files.

Usage:
    python generate_search_index.py

The script will create search-index.json in the website root.
"""

import os
import re
import json
from html.parser import HTMLParser
from collections import Counter
from datetime import datetime

# Get the project root (parent of scripts directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Spiritual teachers and authors Pat frequently references
KNOWN_TEACHERS = [
    "Julian of Norwich",
    "Thomas Keating",
    "Richard Rohr",
    "Meister Eckhart",
    "Teresa of Avila",
    "John of the Cross",
    "Hildegard of Bingen",
    "Thomas Merton",
    "Henri Nouwen",
    "Brother Lawrence",
    "Thérèse of Lisieux",
    "Therese of Lisieux",
    "Ignatius of Loyola",
    "Francis de Sales",
    "Evelyn Underhill",
    "Howard Thurman",
    "Cynthia Bourgeault",
    "Martin Smith",
    "Tilden Edwards",
    "Gerald May",
    "Augustine",
    "C.S. Lewis",
    "Frederick Buechner",
    "Barbara Brown Taylor",
    "James Finley",
    "Basil Pennington",
    "William Meninger",
    "Anthony de Mello",
    "Jan Karon",
    "Rumi",
    "Thich Nhat Hanh",
    "Dorothy Day",
    "Dietrich Bonhoeffer",
    "Simone Weil",
    "Flannery O'Connor",
    "Wendell Berry",
    "Mary Oliver",
    "Parker Palmer",
    "Joan Chittister",
    "Kathleen Norris",
    "Esther de Waal",
    "Roberta Bondi",
    "Margaret Silf",
    "Joyce Rupp",
]

# Key contemplative themes/keywords to look for
THEME_KEYWORDS = {
    "Centering Prayer": ["centering prayer"],
    "lectio divina": ["lectio divina", "lectio"],
    "transformation": ["transformation", "transform", "transformed"],
    "surrender": ["surrender", "surrendering"],
    "letting go": ["let go", "letting go"],
    "presence": ["presence", "present moment"],
    "silence": ["silence", "silent"],
    "stillness": ["stillness", "still point"],
    "contemplative": ["contemplative", "contemplation"],
    "healing": ["healing", "heal", "healed"],
    "grace": ["grace", "graced"],
    "faith": ["faith", "faithful"],
    "hope": ["hope", "hoping"],
    "trust": ["trust", "trusting"],
    "dark night": ["dark night", "darkness"],
    "light": ["light of Christ", "illumination"],
    "journey": ["spiritual journey", "pilgrimage"],
    "calling": ["call", "calling", "vocation"],
    "discernment": ["discern", "discernment"],
    "examen": ["examen", "examination of conscience"],
    "forgiveness": ["forgive", "forgiveness", "forgiving"],
    "compassion": ["compassion", "compassionate"],
    "mercy": ["mercy", "merciful"],
    "peace": ["peace", "peaceful"],
    "joy": ["joy", "joyful"],
    "gratitude": ["gratitude", "grateful", "thanksgiving"],
    "humility": ["humility", "humble"],
    "obedience": ["obedience", "obedient"],
    "patience": ["patience", "patient"],
    "simplicity": ["simplicity", "simple living"],
    "solitude": ["solitude"],
    "community": ["community", "communion"],
    "Eucharist": ["eucharist", "communion", "lord's supper"],
    "baptism": ["baptism", "baptized"],
    "repentance": ["repentance", "repent"],
    "conversion": ["conversion", "converted"],
    "resurrection": ["resurrection", "risen"],
    "incarnation": ["incarnation", "incarnate"],
    "Trinity": ["trinity", "triune"],
    "Holy Spirit": ["holy spirit", "spirit of god"],
    "kingdom of God": ["kingdom of god", "reign of god"],
}


class MeditationHTMLParser(HTMLParser):
    """Parse meditation HTML to extract content."""

    def __init__(self):
        super().__init__()
        self.in_content = False
        self.in_readings = False
        self.current_tag = None
        self.paragraphs = []
        self.current_text = ""
        self.scripture = ""

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)

        if tag == 'div' and attrs_dict.get('class') == 'meditation-content':
            self.in_content = True
        elif tag == 'div' and attrs_dict.get('class') == 'meditation-readings':
            self.in_readings = True

    def handle_endtag(self, tag):
        if tag == 'div':
            if self.in_content:
                self.in_content = False
            if self.in_readings:
                self.in_readings = False
        elif tag == 'p' and self.in_content and self.current_text:
            self.paragraphs.append(self.current_text.strip())
            self.current_text = ""

    def handle_data(self, data):
        if self.in_readings:
            self.scripture += data
        elif self.in_content and self.current_tag == 'p':
            self.current_text += data


def extract_meditation_content(html_path):
    """Extract scripture and content from a meditation HTML file."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
    except Exception as e:
        print(f"Error reading {html_path}: {e}")
        return "", []

    parser = MeditationHTMLParser()
    parser.feed(html)

    return parser.scripture.strip(), parser.paragraphs


def find_teachers(text):
    """Find referenced spiritual teachers in the text."""
    found = []
    text_lower = text.lower()

    for teacher in KNOWN_TEACHERS:
        if teacher.lower() in text_lower:
            found.append(teacher)

    return found


def find_keywords(text):
    """Find contemplative theme keywords in the text."""
    found = []
    text_lower = text.lower()

    for theme, patterns in THEME_KEYWORDS.items():
        for pattern in patterns:
            if pattern in text_lower:
                found.append(theme)
                break

    return found


def create_excerpt(paragraphs, max_length=300):
    """Create a search excerpt from paragraphs."""
    if not paragraphs:
        return ""

    # Use first substantial paragraph
    for para in paragraphs:
        # Skip very short paragraphs or author attribution
        if len(para) > 50 and not para.startswith("Pat"):
            if len(para) > max_length:
                # Truncate at word boundary
                truncated = para[:max_length].rsplit(' ', 1)[0]
                return truncated + "..."
            return para

    return paragraphs[0][:max_length] if paragraphs else ""


def format_display_date(date_str):
    """Convert YYYY-MM-DD to readable format like 'December 16, 2007'."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        # Format without leading zero on day
        return dt.strftime('%B %-d, %Y') if os.name != 'nt' else dt.strftime('%B %d, %Y').replace(' 0', ' ')
    except:
        return date_str


def generate_search_index():
    """Generate the complete search index."""
    # Load existing meditations data
    data_path = os.path.join(PROJECT_ROOT, 'meditations-data.json')

    if not os.path.exists(data_path):
        print(f"Meditations data not found: {data_path}")
        return []

    with open(data_path, 'r', encoding='utf-8') as f:
        meditations_data = json.load(f)

    meditations_dir = os.path.join(PROJECT_ROOT, 'meditations')

    if not os.path.exists(meditations_dir):
        print(f"Meditations directory not found: {meditations_dir}")
        return []

    print(f"Processing {len(meditations_data)} meditations...")

    index = []

    for i, med in enumerate(meditations_data):
        html_path = os.path.join(meditations_dir, med['filename'])

        if not os.path.exists(html_path):
            print(f"  Skipping missing file: {med['filename']}")
            continue

        # Extract content from HTML
        scripture, paragraphs = extract_meditation_content(html_path)

        # Combine all text for keyword/teacher searching
        full_text = med.get('title', '') + " " + " ".join(paragraphs)

        # Find teachers and keywords
        teachers = find_teachers(full_text)
        keywords = find_keywords(full_text)

        # Create excerpt
        excerpt = create_excerpt(paragraphs)

        # Build the search index entry
        entry = {
            'date': med['date'],
            'year': int(med['date'][:4]),
            'displayDate': format_display_date(med['date']),
            'title': med['title'].title() if med['title'].isupper() else med['title'],
            'occasion': med['occasion'],
            'season': med['season'],
            'lectYear': med.get('year', ''),
            'scripture': scripture,
            'excerpt': excerpt,
            'keywords': keywords,
            'teachers': teachers
        }

        index.append(entry)

        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(meditations_data)}...")

    # Sort by date descending (newest first)
    index.sort(key=lambda x: x['date'], reverse=True)

    return index


def main():
    print("Generating search index for Threads of Grace...")
    print(f"Project root: {PROJECT_ROOT}")

    index = generate_search_index()

    if index:
        output_path = os.path.join(PROJECT_ROOT, 'search-index.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        print(f"\nCreated search index with {len(index)} meditations")
        print(f"Output: {output_path}")

        # Print some stats
        all_teachers = []
        all_keywords = []
        for entry in index:
            all_teachers.extend(entry.get('teachers', []))
            all_keywords.extend(entry.get('keywords', []))

        print(f"\nTop referenced teachers:")
        for teacher, count in Counter(all_teachers).most_common(10):
            print(f"  {teacher}: {count}")

        print(f"\nTop themes/keywords:")
        for keyword, count in Counter(all_keywords).most_common(10):
            print(f"  {keyword}: {count}")
    else:
        print("No meditations found to index.")


if __name__ == '__main__':
    main()
