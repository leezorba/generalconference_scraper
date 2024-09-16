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

def fetch_conference_talk(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: Unable to fetch the webpage {url}. Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('h1', id="title1")
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        period_tag = soup.find('div', class_='itemTitle-MXhtV')
        period = period_tag.get_text(strip=True) if period_tag else "Unknown Period"

        author_name_tag = soup.find('p', class_='author-name')
        author_name = author_name_tag.get_text(strip=True) if author_name_tag else "Unknown Author"
        author_role_tag = soup.find('p', class_='author-role')
        author_role = author_role_tag.get_text(strip=True) if author_role_tag else "Unknown Role"

        body_div = soup.find('div', class_='body-block')
        if body_div:
            body_content = get_cleaned_body_content(body_div)
        else:
            body_content = ""

        talk_data = {
            "title": title,
            "period": period,
            "author_name": author_name,
            "author_role": author_role,
            "body": body_content
        }

        return talk_data

    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None


def get_cleaned_body_content(body_div):
    # Remove all footnote reference links and their contents
    for footnote_link in body_div.find_all('a', class_='note-ref'):
        footnote_link.decompose()

    # Extract text from the modified body_div and split by block-level tags like <p> and <div>
    paragraphs = body_div.find_all(['p', 'div'])

    cleaned_paragraphs = []
    for para in paragraphs:
        text = para.get_text(separator=' ', strip=True)  # Extract text with space separator for inline elements
        if text:
            cleaned_paragraphs.append(text)

    # Join paragraphs with \n\n to preserve the line breaks between them
    cleaned_text = '\n\n'.join(cleaned_paragraphs)

    return cleaned_text


def fetch_all_talks_to_json(speaker_url, output_filename):
    try:
        response = requests.get(speaker_url)
        if response.status_code != 200:
            print(f"Error fetching speaker's page: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        talk_links = soup.find_all('a', href=True)
        talks = []
        for link in talk_links:
            href = link['href']
            if "/study/general-conference/" in href:
                talk_url = f"https://www.churchofjesuschrist.org{href}"
                print(f"Fetching talk: {talk_url}")
                talk_data = fetch_conference_talk(talk_url)
                if talk_data:
                    talks.append(talk_data)
                time.sleep(1)  # 1-second delay between requests

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(talks, f, ensure_ascii=False, indent=2)

        print(f"All talks saved to {output_filename}")

    except Exception as e:
        print(f"Error in fetch_all_talks_to_json: {str(e)}")


def extract_main_themes(body_text):
    system_message = "You are an assistant that summarizes texts into main themes suitable for a prompt."
    user_message = (
        f"Given the following text from a conference talk, extract the main themes and topics discussed in a brief phrase suitable for completing the sentence 'focusing on...'\n\n"
        f"Text:\n{body_text}"
    )

    try:
        # Updated API method for gpt-4o model
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=100,
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


def convert_json_to_jsonl(input_filename, output_filename):
    with open(input_filename, 'r', encoding='utf-8') as f_in:
        talks = json.load(f_in)

    with open(output_filename, 'w', encoding='utf-8') as f_out:
        for idx, talk in enumerate(talks):
            completion_text = talk.get('body', '')
            print(f"Generating prompt for talk {idx+1}/{len(talks)}...")

            prompt = f"Write a general conference talk titled '{talk['title']}' by {talk['author_name']}, focusing on {talk['period']}."

            jsonl_obj = {
                "prompt": prompt,
                "completion": completion_text
            }
            json.dump(jsonl_obj, f_out, ensure_ascii=False)
            f_out.write('\n')
            time.sleep(1)

    print(f"Conversion to JSONL complete! JSONL saved as {output_filename}")


def generate_filename_from_url(url, extension):
    # Extract speaker's name from the URL
    speaker_name = url.split("/speakers/")[1].split("?")[0].replace("-", "_")
    return f"{speaker_name}_general_conference_talks.{extension}"

# Dynamic user input for speaker URL
speaker_url = input("Enter the speaker's general conference URL: ").strip()

# Generate filenames based on the URL
json_filename = generate_filename_from_url(speaker_url, 'json')
jsonl_filename = generate_filename_from_url(speaker_url, 'jsonl')

# Fetch all talks and save to JSON file
fetch_all_talks_to_json(speaker_url, json_filename)

# Convert JSON to JSONL
convert_json_to_jsonl(json_filename, jsonl_filename)