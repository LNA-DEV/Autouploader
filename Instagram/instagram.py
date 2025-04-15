import os
import re
import sys
import feedparser
from datetime import datetime
import time
import random
import requests

INSTAGRAM_ACCESS_TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN')
INSTAGRAM_ACCOUNT_ID = os.environ.get('INSTAGRAM_ACCOUNT_ID')
API_KEY = os.environ.get('API_KEY')

graph_url = 'https://graph.instagram.com/v22.0/'

def post_image(caption='', image_url='', instagram_account_id='', access_token=''):
    url = graph_url + instagram_account_id + '/media'
    param = {
        'access_token': access_token,
        'caption': caption,
        'image_url': image_url,
    }
    response = requests.post(url, params=param)
    return response.json()

def publish_container(creation_id='', instagram_account_id='', access_token=''):
    url = graph_url + instagram_account_id + '/media_publish'
    param = {
        'access_token': access_token,
        'creation_id': creation_id,
    }
    response = requests.post(url, params=param)
    return response.json()

def check_media_status(creation_id, access_token):
    url = f"{graph_url}/{creation_id}?fields=status_code&access_token={access_token}"
    response = requests.get(url)
    return response.json()

# Function to filter entries based on the name list
def filter_entries(entries, name_list):

    # Temp skips (for example if this image does not fit currently)
    # name_list.append("P1002496.JPG")

    return [entry for entry in entries if entry.title not in name_list]

def get_already_uploaded_items():
    try:
        response = requests.get("https://api.lna-dev.net/autouploader/instagram")
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
    requests.post(
        f"https://api.lna-dev.net/autouploader/instagram?item={entry_name}",
        headers={"Authorization": f"ApiKey {API_KEY}"}
    )

def publish_entry(entry):
    # Create caption
    caption = "More at lna-dev.net or the link in my profile.\n\n"
    for tag in entry.tags:
        caption += f"#{tag.term} "

    # Get image and alt text
    media_url = entry.media_content[0]["url"]
    alt_text = re.search(r'alt="(.*?)"', entry.summary)
    alt_text = alt_text.group(1) if alt_text else "Alt not found"

    print("Posting to Instagram...")
    creation_response = post_image(
        caption=caption,
        image_url=media_url,
        instagram_account_id=INSTAGRAM_ACCOUNT_ID,
        access_token=INSTAGRAM_ACCESS_TOKEN
    )

    if "id" not in creation_response:
        print("Error creating media container:", creation_response)
        return

    creation_id = creation_response["id"]

    # Wait for the media to be processed
    max_retries = 10
    for attempt in range(max_retries):
        status_response = check_media_status(creation_id, INSTAGRAM_ACCESS_TOKEN)
        status = status_response.get("status_code")
        
        print(f"Attempt {attempt+1}: Status = {status}")
        
        if status == "FINISHED":
            break
        time.sleep(2)  # Wait 2 seconds before trying again
    else:
        print("Media was not ready after waiting. Exiting.")
        return

    publish_response = publish_container(
        creation_id=creation_id,
        instagram_account_id=INSTAGRAM_ACCOUNT_ID,
        access_token=INSTAGRAM_ACCESS_TOKEN
    )

    if "id" in publish_response:
        print("Published to Instagram:", publish_response["id"])
        published_entry(entry.title)
    else:
        print("Error publishing media:", publish_response)

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
