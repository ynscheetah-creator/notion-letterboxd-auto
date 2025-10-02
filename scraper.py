import os
import re
import requests
from datetime import datetime

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
FILMS_DB_ID = os.environ.get('FILMS_DB_ID')

NOTION_HEADERS = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

def get_updated_pages():
    url = f'https://api.notion.com/v1/databases/{FILMS_DB_ID}/query'
    response = requests.post(url, headers=NOTION_HEADERS, json={
        "filter": {
            "and": [
                {
                    "property": "Letterboxd URI",
                    "url": {"is_not_empty": True}
                },
                {
                    "or": [
                        {"property": "Poster", "url": {"is_empty": True}},
                        {"property": "Runtime (min)", "number": {"is_empty": True}}
                    ]
                }
            ]
        }
    })
    return response.json().get('results', [])

def resolve_boxd_url(url):
    """boxd.it linklerini letterboxd.com'a çevirir"""
    try:
        if 'boxd.it' in url:
            response = requests.get(url, allow_redirects=True, timeout=10)
            return response.url
        return url
    except Exception as e:
        print(f"Error resolving URL {url}: {e}")
        return url

def scrape_letterboxd(url):
    try:
        # boxd.it ise letterboxd.com'a çevir
        full_url = resolve_boxd_url(url)
        print(f"Resolved URL: {full_url}")
        
        response = requests.get(full_url, timeout=10)
        html = response.text
        
        poster_match = re.search(r'<meta property="og:image" content="(https://[^"]+)"', html)
        runtime_match = re.search(r'(\d+)\s*mins', html)
        year_match = re.search(r'<meta property="og:title" content="[^(]*\((\d{4})\)"', html)
        director_match = re.search(r'<meta name="twitter:data1" content="([^"]+)"', html)
        cinematography_match = re.search(r'Cinematography[\s\S]+?text-slug">([^<]+)', html)
        writer_match = re.search(r'>Writer</span>[\s\S]{1,200}?text-slug">([^<]+)</a>', html)
        
        return {
            'poster': poster_match.group(1) if poster_match else None,
            'runtime': int(runtime_match.group(1)) if runtime_match else None,
            'year': int(year_match.group(1)) if year_match else None,
            'director': director_match.group(1) if director_match else None,
            'cinematography': cinematography_match.group(1) if cinematography_match else None,
            'writer': writer_match.group(1) if writer_match else None
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def update_notion_page(page_id, data):
    url = f'https://api.notion.com/v1/pages/{page_id}'
    properties = {}
    
    if data.get('poster'):
        properties['Poster'] = {'url': data['poster']}
    if data.get('runtime'):
        properties['Runtime (min)'] = {'number': data['runtime']}
    if data.get('year'):
        properties['Year'] = {'number': data['year']}
    if data.get('director'):
        properties['Director'] = {'rich_text': [{'text': {'content': data['director']}}]}
    if data.get('cinematography'):
        properties['Cinematography'] = {'rich_text': [{'text': {'content': data['cinematography']}}]}
    if data.get('writer'):
        properties['Writer'] = {'rich_text': [{'text': {'content': data['writer']}}]}
    
    response = requests.patch(url, headers=NOTION_HEADERS, json={'properties': properties})
    return response.status_code == 200

def main():
    print(f"Starting scraper at {datetime.now()}")
    pages = get_updated_pages()
    print(f"Found {len(pages)} pages to update")
    
    for page in pages:
        try:
            letterboxd_url = page['properties']['Letterboxd URI']['url']
            print(f"Processing: {letterboxd_url}")
            
            data = scrape_letterboxd(letterboxd_url)
            if data:
                success = update_notion_page(page['id'], data)
                print(f"Updated: {'Success' if success else 'Failed'}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("Scraper finished")

if __name__ == '__main__':
    main()
