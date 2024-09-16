import requests
from bs4 import BeautifulSoup
import json
import time
import openai
import os
from dotenv import load_dotenv
from openai import RateLimitError, APIConnectionError, APIError

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

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

# Function to fetch all talks from a period URL and save to JSON
def fetch_all_talks_from_period(period_url, output_filename):
    try:
        response = requests.get(period_url)
        if response.status_code != 200:
            print(f"Error fetching period page: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        talk_links = soup.find_all('a', href=True)

        talks = []
        for link in talk_links:
            href = link['href']
            if "/study/general-conference/" in href and "lang=eng" in href:
                talk_url = f"https://www.churchofjesuschrist.org{href}"
                print(f"Fetching talk: {talk_url}")
                talk_data = fetch_conference_talk(talk_url)
                if talk_data:
                    talks.append(talk_data)
                    print(f"Talk fetched: {talk_data['title']} by {talk_data['speaker']}")
                time.sleep(1)

        if talks:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(talks, f, ensure_ascii=False, indent=2)
            print(f"All talks saved to {output_filename}")
        else:
            print("No talks found or fetched, not saving file.")

    except Exception as e:
        print(f"Error in fetch_all_talks_from_period: {str(e)}")

# Function to extract main themes from talk body using OpenAI
def extract_main_themes(body_text):
    system_message = "You are an assistant that summarizes texts into main themes suitable for a prompt."
    user_message = f"Given the following text from a conference talk, extract the main themes in no more than 70 words and avoid lengthy descriptions:\n\nText:\n{body_text}"

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            temperature=0.5
        )
        themes = response.choices[0].message.content.strip()
        return themes

    except RateLimitError:
        print("Rate limit reached. Please wait before retrying.")
        time.sleep(5)
        return extract_main_themes(body_text)
    except APIConnectionError as e:
        print(f"Connection error: {e}")
        return "the main themes and topics discussed"
    except APIError as e:
        print(f"API returned an error: {e}")
        return "the main themes and topics discussed"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "the main themes and topics discussed"

# Function to generate the prompt for each talk
def generate_prompt(talk):
    title = talk.get('title', 'Untitled Talk')
    main_themes = extract_main_themes(talk.get('body', ''))
    prompt = f"Write a general conference talk titled '{title}' focusing on {main_themes}"
    return prompt

# Function to convert JSON to JSONL
def convert_json_to_jsonl(input_filename, output_filename):
    with open(input_filename, 'r', encoding='utf-8') as f_in:
        talks = json.load(f_in)

    with open(output_filename, 'w', encoding='utf-8') as f_out:
        for idx, talk in enumerate(talks):
            completion_text = talk.get('body', '')
            print(f"Generating prompt for talk {idx+1}/{len(talks)}...")

            prompt = generate_prompt(talk)
            if not prompt:
                print("Failed to generate prompt, skipping this talk.")
                continue

            speaker_name = talk.get('speaker', 'Unknown Speaker')

            jsonl_obj = {
                "prompt": prompt,
                "speaker": speaker_name,
                "completion": completion_text
            }
            json.dump(jsonl_obj, f_out, ensure_ascii=False)
            f_out.write('\n')
            time.sleep(1)

# Function to generate the output filename based on the URL
def generate_filename_from_period_url(url, extension):
    period = url.split("/study/general-conference/")[1].split("?")[0].replace("/", "_")
    return f"general_conference_{period}_talks.{extension}"

# Main function to handle both JSON and JSONL creation
def process_conference_talks(url):
    # Generate output filenames
    json_filename = generate_filename_from_period_url(url, 'json')
    jsonl_filename = generate_filename_from_period_url(url, 'jsonl')

    # Fetch talks and save to JSON
    fetch_all_talks_from_period(url, json_filename)

    # Convert JSON to JSONL
    convert_json_to_jsonl(json_filename, jsonl_filename)

    print(f"Conversion complete! JSON saved as {json_filename}, JSONL saved as {jsonl_filename}")

# Dynamic user input for period URL
period_url = input("Enter the general conference period URL: ").strip()

# Process the conference talks
process_conference_talks(period_url)