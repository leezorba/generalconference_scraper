import requests
from bs4 import BeautifulSoup
import json
import time

EXCLUDED_WORDS = ["Session", "Sustaining of", "Church Auditing"]
UNKNOWN_TITLE = "Unknown Title"

# Function to fetch and clean the body content
def get_cleaned_body_content(body_div):
    for footnote_link in body_div.find_all('a', class_='note-ref'):
        footnote_link.decompose()

    paragraphs = body_div.find_all(['p', 'div'])
    cleaned_paragraphs = [para.get_text(separator=' ', strip=True) for para in paragraphs if para.get_text(strip=True)]

    return '\n\n'.join(cleaned_paragraphs)

# Function to fetch the details of each talk
def fetch_conference_talk(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: Unable to fetch the webpage {url}. Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('h1', id="title1")
        title = title_tag.get_text(strip=True) if title_tag else UNKNOWN_TITLE

        if title == UNKNOWN_TITLE or any(word in title for word in EXCLUDED_WORDS):
            print(f"Skipping talk: {title} (Excluded or Unknown Title)")
            return None

        period_tag = soup.find('div', class_='itemTitle-MXhtV')
        period = period_tag.get_text(strip=True) if period_tag else "Unknown Period"

        speaker_tag = soup.find('p', class_='author-name')
        speaker = speaker_tag.get_text(strip=True) if speaker_tag else "Unknown Speaker"
        if speaker.startswith("By "):
            speaker = speaker[3:]

        author_role_tag = soup.find('p', class_='author-role')
        author_role = author_role_tag.get_text(strip=True) if author_role_tag else "Unknown Role"

        body_div = soup.find('div', class_='body-block')
        body_content = get_cleaned_body_content(body_div) if body_div else ""

        talk_data = {
            "title": title,
            "period": period,
            "speaker": speaker,
            "author_role": author_role,
            "body": body_content
        }

        return talk_data

    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None

# Function to fetch all talks from a period URL and save to JSON and TXT
def fetch_all_talks_from_period(period_url, json_filename, txt_filename):
    try:
        response = requests.get(period_url)
        if response.status_code != 200:
            print(f"Error fetching period page: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        talk_links = soup.find_all('a', href=True)

        talks = []
        all_talks_text = ""
        for link in talk_links:
            href = link['href']
            if "/study/general-conference/" in href and "lang=eng" in href:
                talk_url = f"https://www.churchofjesuschrist.org{href}"
                print(f"Fetching talk: {talk_url}")
                talk_data = fetch_conference_talk(talk_url)
                if talk_data:
                    talks.append(talk_data)
                    print(f"Talk fetched: {talk_data['title']} by {talk_data['speaker']}")
                    
                    # Add talk to the text file content
                    all_talks_text += f"Title: {talk_data['title']}\n"
                    all_talks_text += f"Speaker: {talk_data['speaker']}\n"
                    all_talks_text += f"Role: {talk_data['author_role']}\n"
                    all_talks_text += f"Period: {talk_data['period']}\n\n"
                    all_talks_text += f"{talk_data['body']}\n\n"
                    all_talks_text += "=" * 80 + "\n\n"  # Separator between talks
                
                time.sleep(1)

        if talks:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(talks, f, ensure_ascii=False, indent=2)
            print(f"All talks saved to {json_filename}")

            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(all_talks_text)
            print(f"All talks saved to {txt_filename}")
        else:
            print("No talks found or fetched, not saving files.")

    except Exception as e:
        print(f"Error in fetch_all_talks_from_period: {str(e)}")

# Function to generate the output filename based on the URL
def generate_filename_from_period_url(url, extension):
    period = url.split("/study/general-conference/")[1].split("?")[0].replace("/", "_")
    return f"general_conference_{period}_talks.{extension}"

# Main function to handle JSON and TXT file generation
def process_conference_talks(url):
    # Generate output filenames
    json_filename = generate_filename_from_period_url(url, 'json')
    txt_filename = generate_filename_from_period_url(url, 'txt')

    # Fetch talks and save to JSON and TXT
    fetch_all_talks_from_period(url, json_filename, txt_filename)

    print(f"Processing complete! JSON saved as {json_filename}, TXT saved as {txt_filename}")

# Dynamic user input for period URL
period_url = input("Enter the general conference period URL: ").strip()

# Process the conference talks
process_conference_talks(period_url)