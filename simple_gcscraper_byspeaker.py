import requests
from bs4 import BeautifulSoup
import json
import time

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

def fetch_all_talks_to_json_and_txt(speaker_url, json_filename, txt_filename):
    try:
        response = requests.get(speaker_url)
        if response.status_code != 200:
            print(f"Error fetching speaker's page: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        talk_links = soup.find_all('a', href=True)
        talks = []
        all_talks_text = ""
        for link in talk_links:
            href = link['href']
            if "/study/general-conference/" in href:
                talk_url = f"https://www.churchofjesuschrist.org{href}"
                print(f"Fetching talk: {talk_url}")
                talk_data = fetch_conference_talk(talk_url)
                if talk_data:
                    talks.append(talk_data)
                    
                    # Add talk to the text file content
                    all_talks_text += f"Title: {talk_data['title']}\n"
                    all_talks_text += f"Author: {talk_data['author_name']}\n"
                    all_talks_text += f"Role: {talk_data['author_role']}\n"
                    all_talks_text += f"Period: {talk_data['period']}\n\n"
                    all_talks_text += f"{talk_data['body']}\n\n"
                    all_talks_text += "=" * 80 + "\n\n"  # Separator between talks
                
                time.sleep(1)  # 1-second delay between requests

        if talks:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(talks, f, ensure_ascii=False, indent=2)
            print(f"All talks saved to {json_filename}")

            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(all_talks_text)
            print(f"All talks saved to {txt_filename}")
        else:
            print("No talks found or fetched, not saving files.")

        return talks

    except Exception as e:
        print(f"Error in fetch_all_talks_to_json_and_txt: {str(e)}")
        return []

def generate_filename_from_url(url, extension):
    # Extract speaker's name from the URL
    speaker_name = url.split("/speakers/")[1].split("?")[0].replace("-", "_")
    return f"{speaker_name}_general_conference_talks.{extension}"

def process_conference_talks(speaker_url):
    # Generate filenames based on the URL
    json_filename = generate_filename_from_url(speaker_url, 'json')
    txt_filename = generate_filename_from_url(speaker_url, 'txt')

    # Fetch all talks and save to JSON and TXT files
    fetch_all_talks_to_json_and_txt(speaker_url, json_filename, txt_filename)

    print(f"Processing complete! JSON saved as {json_filename}, TXT saved as {txt_filename}")

# Dynamic user input for speaker URL
speaker_url = input("Enter the speaker's general conference URL: ").strip()

# Process the conference talks
process_conference_talks(speaker_url)