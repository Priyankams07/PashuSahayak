import feedparser
import threading
import time
from flask import Blueprint, jsonify, request
from pymongo import MongoClient
from datetime import datetime
import re
import os

news_bp = Blueprint('news', __name__)

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = 'cattle-app-db'
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
news_collection = db['NewsHub']

# RSS Feeds
RSS_FEEDS = [
    # Government Policy & Schemes
    ('policy', 'https://pib.gov.in/RssFeed.aspx?Type=RSS'),
    # Cattle Disease Outbreak News
    ('disease', 'https://www.nddb.coop/rss.xml'),
    ('disease', 'https://icar.org.in/rss.xml'),
    # Agriculture Market News
    ('market', 'https://agmarknet.gov.in/rssfeed.aspx'),
    ('market', 'https://www.thehindu.com/business/agri-business/feeder/default.rss'),
    # Weather & Alerts
    ('weather', 'https://mausam.imd.gov.in/rssfeed.xml'),
]

# Priority keywords
PRIORITY_KEYWORDS = {
    'high': [r'disease outbreak', r'epidemic', r'alert', r'cyclone', r'flood', r'earthquake', r'weather warning', r'heavy rain', r'heatwave'],
    'medium': [r'price change', r'market rate', r'procurement', r'export', r'import', r'policy update'],
    'low': [r'policy', r'scheme', r'initiative', r'update'],
}

def assign_priority(title, description):
    text = f"{title} {description}".lower()
    for level, patterns in PRIORITY_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, text):
                return level
    return 'low'

def fetch_and_store_news():
    while True:
        for category, url in RSS_FEEDS:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.get('title', '')
                    description = entry.get('description', '')
                    # Skip if description is mostly HTML, contains <img, or is a banner/image post
                    if (
                        '<img' in description or
                        description.strip().startswith('<div') or
                        'banner' in title.lower() or
                        'image' in title.lower() or
                        len(description.strip()) < 30
                    ):
                        continue
                    link = entry.get('link', '')
                    published = entry.get('published', '')
                    # Try to get source name from entry or fallback to url
                    source = entry.get('source', {}).get('title') if entry.get('source') else url
                    source_link = entry.get('source', {}).get('href') if entry.get('source') else url
                    priority = assign_priority(title, description)
                    # Avoid duplicates
                    if news_collection.find_one({'title': title, 'link': link}):
                        continue
                    news_doc = {
                        'title': title,
                        'description': description,
                        'category': category,
                        'priority': priority,
                        'source': source,
                        'source_link': source_link,
                        'publishedAt': published,
                        'link': link
                    }
                    result = news_collection.insert_one(news_doc)
                    print(f"Inserted news: {title} | {category} | {priority} | {result.inserted_id}")
            except Exception as e:
                print(f"Error fetching {url}: {e}")
        time.sleep(1800)  # Fetch every 30 minutes

# Start background thread
threading.Thread(target=fetch_and_store_news, daemon=True).start()

@news_bp.route('/api/news', methods=['GET'])
def get_news():
    category = request.args.get('category')
    priority = request.args.get('priority')
    lang = request.args.get('lang', 'en')
    query = {}
    if category:
        query['category'] = category
    if priority:
        query['priority'] = priority
    # Limit: 1 news per category per priority
    pipeline = []
    if category:
        pipeline.append({'$match': {'category': category}})
    if priority:
        pipeline.append({'$match': {'priority': priority}})
    pipeline.extend([
        {"$sort": {"publishedAt": -1}},
        {"$group": {
            "_id": {"category": "$category", "priority": "$priority"},
            "news": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$news"}},
        {"$sort": {"category": 1, "priority": 1}}
    ])
    news = list(news_collection.aggregate(pipeline))
    for n in news:
        n['_id'] = str(n['_id'])
        # TODO: Add translation for Hindi if lang == 'hi'
    return jsonify({'news': news})
