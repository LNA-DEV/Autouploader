from io import BytesIO
import os
import re
import sys
import feedparser
from datetime import datetime
import time
import random
import requests
from atproto import Client
from atproto import client_utils

BLUESKY_PAT = 'BLUESKY_PAT'
API_KEY = 'API_KEY'

bsClient = Client()
bsClient.login(
    login="bluesky@lna-dev.net",
    password=BLUESKY_PAT,
)

# Function to filter entries based on the name list
def filter_entries(entries, name_list):

    # Temp skips (for example if this image does not fit currently)
    # name_list.append("P1002496.JPG")

    return [entry for entry in entries if entry.title not in name_list]

def get_already_uploaded_items():
    try:
        response = requests.get("https://api.lna-dev.net/autouploader/bluesky")
        if response.status_code == 200:
            string_list = response.json()
            return string_list
        else:
            print(f"Failed to fetch data from API. Status code: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def published_entry(entry_name):
    requests.post(f"https://api.lna-dev.net/autouploader/bluesky?item={entry_name}", headers={"Authorization": f"ApiKey {API_KEY}"})

def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        print("Failed to download image!")
        sys.exit(1)

def publish_entry(entry):
    caption = client_utils.TextBuilder()
    caption.text("More at ")
    caption.link(text="https://lna-dev.net/en/gallery", url="https://lna-dev.net/en/gallery")
    caption.text("\n\n")

    for element in entry.tags:
        caption.tag("#" + element.term, element.term)
        caption.text(" ")

    media_url = entry.media_content[0]["url"]
    alt_text = re.search('alt="(.*?)"', entry.summary)
    alt_text = alt_text.group(1) if alt_text else "Alt not found"

    bsClient.send_image(
        text=caption,
        image=download_image(media_url),
        image_alt=alt_text,
    )

    published_entry(entry.title)

# Parse the RSS feed
feed_url = 'https://lna-dev.net/en/gallery/index.xml'
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
