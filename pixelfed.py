import feedparser
from datetime import datetime
import time
import random

# Function to filter entries based on the name list
def filter_entries(entries, name_list):
    return [entry for entry in entries if entry.title not in name_list]

def get_already_uploaded_items():
    return ['Caterpillar.JPG', 'name2', 'name3']

def published_entry(entry_name):
    print("todo")

def publish_entry(entry):
    published_entry(entry.title)

# Parse the RSS feed
feed_url = 'http://localhost:1313/index.xml'
feed = feedparser.parse(feed_url)

# Filter out entries with specific names
specific_names = get_already_uploaded_items()
filtered_entries = filter_entries(feed.entries, specific_names)

if not filtered_entries:
    print("No entries available after filtering.")
else:
    # Calculate time differences considering only month, day, hour, minute, and second
    current_time = datetime.now()
    closest_entry = None
    skipped_entries = []
    min_difference = None
    for entry in filtered_entries:
        if entry.published_parsed.tm_year == 0 or entry.published_parsed.tm_year == 1:
            skipped_entries.append(entry)
            continue  # Skip entries with invalid year
        temp = time.mktime(entry.published_parsed)
        published_time = datetime.fromtimestamp(temp)
        difference = abs(current_time.replace(year=published_time.year, tzinfo=None) - published_time)
        if min_difference is None or difference < min_difference:
            min_difference = difference
            closest_entry = entry

    if closest_entry is None:
        print("No valid entries available after filtering.")
    else:
        # Get all entries published at the same time as the closest entry
        closest_entries = [entry for entry in filtered_entries if entry.published == closest_entry.published]
        for element in skipped_entries:
            closest_entries.append(element)

        # Select a random entry from the closest entries
        random_entry = random.choice(closest_entries)

        # Print the selected entry
        print("Random entry closest to the current date/time (ignoring year):")
        print("Title:", random_entry.title)
        print("URL:", random_entry.link)
        print("Published Date:", random_entry.published)

        publish_entry(random_entry)
