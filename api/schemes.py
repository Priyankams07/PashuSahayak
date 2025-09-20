import requests
from bs4 import BeautifulSoup
import threading
import time
from flask import Blueprint, jsonify
from pymongo import MongoClient
import os

schemes_bp = Blueprint('schemes', __name__)

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = 'cattle-app-db'
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
schemes_collection = db['Schemes']


PMKISAN_URL = 'https://pmkisan.gov.in/'
NDDB_URL = 'https://www.nddb.coop/'
INDIAGOV_URL = 'https://www.india.gov.in/schemes'
DBTBHARAT_URL = 'https://dbtbharat.gov.in/'
NLM_URL = 'https://dahd.nic.in/national-livestock-mission'

# --- Scraper for PM Kisan Portal (example structure, may need adjustment) ---
def scrape_pmkisan():
    schemes = []
    try:
        resp = requests.get(PMKISAN_URL, timeout=20, verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Example: Find scheme cards or links (update selector as needed)
        for card in soup.select('.scheme-card, .some-scheme-class'):
            title = card.select_one('.scheme-title').get_text(strip=True)
            desc = card.select_one('.scheme-desc').get_text(strip=True)
            benefits = [li.get_text(strip=True) for li in card.select('.scheme-benefits li')]
            eligibility = card.select_one('.scheme-eligibility').get_text(strip=True)
            subsidy = card.select_one('.scheme-subsidy').get_text(strip=True)
            apply_link = card.select_one('a.apply-now')['href']
            schemes.append({
                'title': title,
                'description': desc,
                'benefits': benefits,
                'eligibility': eligibility,
                'subsidy': subsidy,
                'apply_link': apply_link,
                'source': 'pmkisan.gov.in'
            })
    except Exception as e:
        print('PM Kisan scrape error:', e)
    return schemes

def scrape_nddb():
    schemes = []
    try:
        resp = requests.get(NDDB_URL, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Example: Find scheme cards or links (update selector as needed)
        for card in soup.select('.scheme-card, .some-scheme-class'):
            title = card.select_one('.scheme-title').get_text(strip=True)
            desc = card.select_one('.scheme-desc').get_text(strip=True)
            benefits = [li.get_text(strip=True) for li in card.select('.scheme-benefits li')]
            eligibility = card.select_one('.scheme-eligibility').get_text(strip=True)
            subsidy = card.select_one('.scheme-subsidy').get_text(strip=True)
            apply_link = card.select_one('a.apply-now')['href']
            schemes.append({
                'title': title,
                'description': desc,
                'benefits': benefits,
                'eligibility': eligibility,
                'subsidy': subsidy,
                'apply_link': apply_link,
                'source': 'nddb.coop'
            })
    except Exception as e:
        print('NDDB scrape error:', e)
    return schemes

def scrape_indiagov():
    schemes = []
    try:
        # Try both English and Hindi versions
        urls = [INDIAGOV_URL, INDIAGOV_URL + '?lang=hi']
        for url in urls:
            try:
                resp = requests.get(url, timeout=20)
                soup = BeautifulSoup(resp.text, 'html.parser')
                for card in soup.select('.views-row'):
                    a_tag = card.select_one('h3 a')
                    title = a_tag.get_text(strip=True) if a_tag else 'National Portal of India'
                    link = a_tag['href'] if a_tag and a_tag.has_attr('href') else url
                    desc_div = card.select_one('.views-field-body .field-content')
                    desc = desc_div.get_text(strip=True) if desc_div else ''
                    schemes.append({
                        'title': title,
                        'description': desc,
                        'benefits': [],
                        'eligibility': '',
                        'subsidy': '',
                        'apply_link': link,
                        'source': 'india.gov.in'
                    })
            except Exception as e:
                print(f'India.gov.in scrape error for {url}:', e)
    except Exception as e:
        print('India.gov.in scrape error:', e)
    return schemes
def scrape_dahd_nic_in():
    schemes = []
    try:
        url = 'https://dahd.nic.in/schemes/programmes/nadcp'
        resp = requests.get(url, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for li in soup.select('li a.url_redirect, li a.anchorNoLink, li a.externalLink'):
            title = li.get_text(strip=True)
            link = li['href'] if li.has_attr('href') else url
            schemes.append({
                'title': title,
                'description': '',
                'benefits': [],
                'eligibility': '',
                'subsidy': '',
                'apply_link': link,
                'source': 'dahd.nic.in'
            })
    except Exception as e:
        print('dahd.nic.in scrape error:', e)
    return schemes

def scrape_nabard():
    schemes = []
    try:
        url = 'https://www.nabard.org/nabkisan.aspx'
        resp = requests.get(url, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for li in soup.select('.right_menu_panel ul.menu li a'):
            title = li.get_text(strip=True)
            link = li['href'] if li.has_attr('href') else url
            # Make link absolute if needed
            if link and not link.startswith('http'):
                link = 'https://www.nabard.org/' + link.lstrip('/')
            schemes.append({
                'title': title,
                'description': '',
                'benefits': [],
                'eligibility': '',
                'subsidy': '',
                'apply_link': link,
                'source': 'nabard.org'
            })
    except Exception as e:
        print('nabard.org scrape error:', e)
    return schemes

def scrape_dbtbharat():
    schemes = []
    try:
        resp = requests.get(DBTBHARAT_URL, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Example: dbtbharat.gov.in schemes in .scheme-list li or similar
        for card in soup.select('.scheme-list li, .scheme-card, .some-scheme-class'):
            title = card.select_one('a, .scheme-title')
            desc = card.select_one('.scheme-desc')
            link = title['href'] if title and title.has_attr('href') else DBTBHARAT_URL
            schemes.append({
                'title': title.get_text(strip=True) if title else 'Scheme',
                'description': desc.get_text(strip=True) if desc else '',
                'benefits': [],
                'eligibility': '',
                'subsidy': '',
                'apply_link': link,
                'source': 'dbtbharat.gov.in'
            })
    except Exception as e:
        print('DBT Bharat scrape error:', e)
    return schemes

def scrape_nlm():
    schemes = []
    try:
        resp = requests.get(NLM_URL, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Example: NLM schemes in .view-content .views-row or similar
        for card in soup.select('.view-content .views-row, .scheme-card, .some-scheme-class'):
            title = card.select_one('a, .scheme-title')
            desc = card.select_one('.scheme-desc, .field-content:last-child')
            link = title['href'] if title and title.has_attr('href') else NLM_URL
            schemes.append({
                'title': title.get_text(strip=True) if title else 'National Livestock Mission',
                'description': desc.get_text(strip=True) if desc else '',
                'benefits': [],
                'eligibility': '',
                'subsidy': '',
                'apply_link': link,
                'source': 'dahd.nic.in/nlm'
            })
    except Exception as e:
        print('NLM scrape error:', e)
    return schemes
    schemes = []
    try:
        resp = requests.get(NDDB_URL, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Example: Find scheme cards or links (update selector as needed)
        for card in soup.select('.scheme-card, .some-scheme-class'):
            title = card.select_one('.scheme-title').get_text(strip=True)
            desc = card.select_one('.scheme-desc').get_text(strip=True)
            benefits = [li.get_text(strip=True) for li in card.select('.scheme-benefits li')]
            eligibility = card.select_one('.scheme-eligibility').get_text(strip=True)
            subsidy = card.select_one('.scheme-subsidy').get_text(strip=True)
            apply_link = card.select_one('a.apply-now')['href']
            schemes.append({
                'title': title,
                'description': desc,
                'benefits': benefits,
                'eligibility': eligibility,
                'subsidy': subsidy,
                'apply_link': apply_link,
                'source': 'nddb.coop'
            })
    except Exception as e:
        print('NDDB scrape error:', e)
    return schemes


def fetch_and_store_schemes():
    while True:
        all_schemes = (
            scrape_pmkisan() +
            scrape_nddb() +
            scrape_indiagov() +
            scrape_dbtbharat() +
            scrape_nlm() +
            scrape_dahd_nic_in() +
            scrape_nabard()
        )
        for scheme in all_schemes:
            # Upsert by title+source
            schemes_collection.update_one(
                {'title': scheme['title'], 'source': scheme['source']},
                {'$set': scheme},
                upsert=True
            )
        time.sleep(86400)  # Refresh once per day

threading.Thread(target=fetch_and_store_schemes, daemon=True).start()

@schemes_bp.route('/api/schemes', methods=['GET'])
def get_schemes():
    schemes = list(schemes_collection.find({}))
    for s in schemes:
        s['_id'] = str(s['_id'])
    return jsonify({'schemes': schemes})
