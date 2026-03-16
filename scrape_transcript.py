import requests
from bs4 import BeautifulSoup
import re
import json
import csv
from urllib.parse import urlparse
import sys

def extract_mentions(text):
    """Extract book, movie, music, and product mentions from text"""
    mentions = []
    
    # Simple regex patterns for common formats
    patterns = {
        'books': r'\b(?:book|novel|read|author|written by)\b.*?(?:\.|\?|\!|(?=,))',
        'movies': r'\b(?:movie|film|watch|directed by|starring)\b.*?(?:\.|\?|\!|(?=,))',
        'music': r'\b(?:song|album|music|band|artist|listen to|released by)\b.*?(?:\.|\?|\!|(?=,))',
        'products': r'\b(?:product|buy|purchase|amazon|store|shop)\b.*?(?:\.|\?|\!|(?=,))'
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
        
        return {
            'url': url,
            'title': title,
            'transcript': transcript_text,
            'mentions': mentions,
            'source': 'podscripts.co'
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def save_to_excel(data, filename='mentions.xlsx'):
    """Save mentions to Excel"""
    try:
        import pandas as pd
        df = pd.DataFrame(data['mentions'])
        df.to_excel(filename, index=False)
        print(f"Saved {len(data['mentions'])} mentions to {filename}")
        return True
    except ImportError:
        print("Pandas not available. Skipping Excel export.")
        return False
    except Exception as e:
        print(f"Error saving Excel: {e}")
        return False

def save_to_html(data, filename='transcript.html'):
    """Save transcript and mentions to HTML"""
    try:
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .transcript {{ white-space: pre-wrap; margin-bottom: 20px; }}
        .mentions {{ margin-top: 20px; }}
        .mention {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .category-book {{ border-left-color: #3498db; }}
        .category-movie {{ border-left-color: #e74c3c; }}
        .category-music {{ border-left-color: #2ecc71; }}
        .category-product {{ border-left-color: #f39c12; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <h2>Transcript Source: {source}</h2>
    <div class="transcript">
        <h3>Transcript</h3>
        <p>{transcript}</p>
    </div>
    <div class="mentions">
        <h3>Extracted Mentions</h3>
        {mentions_html}
    </div>
</body>
</html>
"""
        
        # Build mentions HTML
        mentions_html = ""
        for mention in data['mentions']:
            mentions_html += '<div class="mention category-' + mention['category'] + '">
                <strong>' + mention['category'].title() + ':</strong> ' + mention['text'] + '
            </div>'
        
        # Format the HTML with actual data
        html_content = html_content.format(
            title=data['title'],
            source=data['source'],
            transcript=data['transcript'],
            mentions_html=mentions_html
        )
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Saved HTML to {filename}")
        return True
    except Exception as e:
        print(f"Error saving HTML: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python scrape_transcript.py <url>")
        return
    
    url = sys.argv[1]
    print(f"Scraping transcript from: {url}")
    
    data = scrape_transcript(url)
    if not data:
        print("Failed to scrape transcript.")
        return
    
    print(f"Found {len(data['mentions'])} mentions")
    
    # Save to Excel
    save_to_excel(data, 'mentions.xlsx')
    
    # Save to HTML
    save_to_html(data, 'transcript.html')
    
    # Show summary
    print("\nSummary:")
    for category in ['books', 'movies', 'music', 'products']:
        count = len([m for m in data['mentions'] if m['category'] == category])
        if count > 0:
            print(f"{category.title()}: {count} mentions")

def extract_amazon_links(data):
    """Extract Amazon links for products"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        amazon_links = []
        products = [m for m in data['mentions'] if m['category'] == 'products']
        
        for product in products:
            # Simple search on Amazon (this would need refinement)
            search_term = product['text']
            # Note: Amazon scraping is against their terms of service
            # This is just a placeholder
            amazon_links.append({
                'product': search_term,
                'url': f'https://www.amazon.com/s?k={search_term.replace(" ", "+")}',
                'found': False
            })
        
        return amazon_links
        
    except ImportError:
        return []
    except Exception as e:
        print(f"Error extracting Amazon links: {e}")
        return []

if __name__ == "__main__":
    main()