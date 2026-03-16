import requests
from bs4 import BeautifulSoup
import re
import json
import csv
from urllib.parse import urlparse
import sys
import time
from datetime import datetime

def extract_mentions(text):
    """Extract book, movie, music, and product mentions from text"""
    mentions = []
    
    # Simple regex patterns for common formats
    patterns = {
        'books': r'\b(?:book|novel|read|author|written by|reading)\b.*?(?:\.|\?|\!|(?=,))',
        'movies': r'\b(?:movie|film|watch|directed by|starring|episode|season|series)\b.*?(?:\.|\?|\!|(?=,))',
        'music': r'\b(?:song|album|music|band|artist|listen to|track|released by)\b.*?(?:\.|\?|\!|(?=,))',
        'products': r'\b(?:product|buy|purchase|amazon|store|shop|app|software|device|headphones|camera|tech|tool)\b.*?(?:\.|\?|\!|(?=,))'
    }
    
    for category, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            mentions.append({
                'category': category,
                'text': match.strip(),
                'source': 'transcript'
            })
    
    return mentions

def scrape_transcript(url):
    """Scrape transcript from podscripts.co"""
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: Unable to fetch {url}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.text if title_tag else 'Unknown'
        
        # Extract transcript content
        transcript_div = soup.find('div', {'class': 'transcript'})  # Adjust class if needed
        if not transcript_div:
            transcript_div = soup.find('div', {'id': 'transcript'})
        
        if transcript_div:
            transcript_text = transcript_div.get_text(separator=' ').strip()
        else:
            # Fallback: get all text
            transcript_text = soup.get_text(separator=' ').strip()
        
        # Extract mentions
        mentions = extract_mentions(transcript_text)
        
        # Extract episode info from URL
        path = urlparse(url).path
        parts = path.split('/')
        episode_info = None
        for i, part in enumerate(parts):
            if part == 'podcasts' and i+2 < len(parts):
                episode_info = parts[i+2]
                break
        
        return {
            'url': url,
            'title': title,
            'transcript': transcript_text,
            'mentions': mentions,
            'source': 'podscripts.co',
            'episode_info': episode_info
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def save_to_csv(data, filename='mentions.csv'):
    """Save mentions to CSV"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Episode', 'Category', 'Text', 'Source', 'URL'])
            
            for mention in data['mentions']:
                writer.writerow([
                    data['episode_info'],
                    mention['category'],
                    mention['text'],
                    data['source'],
                    data['url']
                ])
        
        print(f"Saved {len(data['mentions'])} mentions to {filename}")
        return True
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python scrape_jre.py <url1> <url2> ... <url10>")
        return
    
    urls = sys.argv[1:11]  # Take first 10 URLs
    
    all_mentions = []
    
    for i, url in enumerate(urls, 1):
        print(f"Scraping {i}/{len(urls)}: {url}")
        data = scrape_transcript(url)
        if data:
            all_mentions.extend(data['mentions'])
            # Save individual CSV for each episode
            episode_csv = f'episode_{i}.csv'
            save_to_csv(data, episode_csv)
        
        # Be respectful - add delay between requests
        if i < len(urls):
            time.sleep(2)  # 2 seconds between requests
    
    # Create master CSV
    if all_mentions:
        with open('jre_mentions_master.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Episode', 'Category', 'Text', 'Source', 'URL'])
            
            for mention in all_mentions:
                # We don't have episode info for all, so leave blank
                writer.writerow(['', mention['category'], mention['text'], mention['source'], ''])
        
        print(f"\nSummary:")
        for category in ['books', 'movies', 'music', 'products']:
            count = len([m for m in all_mentions if m['category'] == category])
            if count > 0:
                print(f"{category.title()}: {count} mentions")
    
    print(f"\nTotal mentions across all episodes: {len(all_mentions)}")

if __name__ == "__main__":
    main()