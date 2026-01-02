import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
import urllib.parse
import time
import re

class FreeNewsAggregator:
    """Agregador de noticias 100% gratuito usando RSS y scraping ético"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; NewsMonitorBot/1.0)'
        })
    
    def search_google_news_rss(self, keyword: str, country: str = "CL", language: str = "es-419") -> List[Dict]:
        """Busca en Google News usando RSS (GRATIS)"""
        try:
            query = urllib.parse.quote(f"{keyword} Chile")
            url = f"https://news.google.com/rss/search?q={query}&hl=es-{country}&gl={country}&ceid={country}:{language}"
            
            feed = feedparser.parse(url)
            results = []
            
            for entry in feed.entries[:50]:
                results.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', ''),
                    'source': entry.get('source', {}).get('title', 'Google News') if isinstance(entry.get('source'), dict) else 'Google News',
                    'keyword': keyword,
                    'keyword_matches': 1
                })
            
            return results
        except Exception as e:
            print(f"Error en Google News RSS: {e}")
            return []
    
    def search_bing_news_rss(self, keyword: str) -> List[Dict]:
        """Busca en Bing News usando RSS (GRATIS)"""
        try:
            query = urllib.parse.quote(keyword)
            url = f"https://www.bing.com/news/search?q={query}&format=rss"
            
            feed = feedparser.parse(url)
            results = []
            
            for entry in feed.entries[:30]:
                results.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('description', ''),
                    'source': 'Bing News',
                    'keyword': keyword,
                    'keyword_matches': 1
                })
            
            return results
        except Exception as e:
            print(f"Error en Bing News: {e}")
            return []
    
    def search_chilean_rss_with_keyword(self, sources: Dict, keyword: str) -> List[Dict]:
        """Busca keyword en feeds RSS chilenos directos (GRATIS)"""
        results = []
        
        for category, source_list in sources.items():
            for source in source_list:
                if source['type'] == 'rss':
                    try:
                        feed = feedparser.parse(source['url'])
                        
                        for entry in feed.entries:
                            title = entry.get('title', '').lower()
                            summary = entry.get('summary', '').lower()
                            
                            # Buscar keyword (case insensitive)
                            if keyword.lower() in title or keyword.lower() in summary:
                                keyword_count = title.count(keyword.lower()) + summary.count(keyword.lower())
                                
                                results.append({
                                    'title': entry.get('title', ''),
                                    'link': entry.get('link', ''),
                                    'published': entry.get('published', ''),
                                    'summary': entry.get('summary', ''),
                                    'source': source['name'],
                                    'category': category,
                                    'keyword': keyword,
                                    'keyword_matches': keyword_count
                                })
                        
                        time.sleep(0.3)  # Ser respetuoso
                    except Exception as e:
                        print(f"Error en {source['name']}: {e}")
        
        return results
    
    def aggregate_all_free(self, keyword: str, sources: Dict, 
                          use_google_news: bool = True, 
                          use_bing_news: bool = False) -> pd.DataFrame:
        """Agrega noticias de TODAS las fuentes gratuitas"""
        all_results = []
        
        # Google News
        if use_google_news:
            print(f"🔍 Buscando en Google News...")
            google_results = self.search_google_news_rss(keyword)
            all_results.extend(google_results)
        
        # Bing News
        if use_bing_news:
            print(f"🔍 Buscando en Bing News...")
            bing_results = self.search_bing_news_rss(keyword)
            all_results.extend(bing_results)
        
        # Medios chilenos directos
        print(f"🔍 Buscando en medios chilenos...")
        chilean_results = self.search_chilean_rss_with_keyword(sources, keyword)
        all_results.extend(chilean_results)
        
        if not all_results:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_results)
        df['fetched_at'] = datetime.now()
        
        # Eliminar duplicados
        df = df.drop_duplicates(subset=['title'], keep='first')
        
        # Calcular relevancia
        df['relevance_score'] = df.get('keyword_matches', 1)
        df = df.sort_values('relevance_score', ascending=False)
        
        return df
    
    def highlight_keyword(self, text: str, keyword: str) -> str:
        """Resalta el keyword en el texto"""
        if not text:
            return text
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(lambda m: f"**{m.group()}**", text)
