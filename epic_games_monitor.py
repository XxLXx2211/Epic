import requests
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from config import EPIC_GRAPHQL_URL, EPIC_FREE_GAMES_URL, HEADERS, EPIC_FREE_GAMES_QUERY
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EpicGamesMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def get_free_games_graphql(self) -> List[Dict]:
        """Obtiene juegos gratuitos usando GraphQL API"""
        try:
            variables = {
                "locale": "es-ES",
                "country": "ES"
            }
            
            payload = {
                "query": EPIC_FREE_GAMES_QUERY,
                "variables": variables
            }
            
            response = self.session.post(EPIC_GRAPHQL_URL, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return self._extract_free_games_from_graphql(data)
            
        except Exception as e:
            logger.error(f"Error obteniendo juegos con GraphQL: {e}")
            return self.get_free_games_scraping()
    
    def get_free_games_scraping(self) -> List[Dict]:
        """Método alternativo usando web scraping"""
        try:
            response = self.session.get(EPIC_FREE_GAMES_URL)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._extract_free_games_from_html(soup)
            
        except Exception as e:
            logger.error(f"Error con web scraping: {e}")
            return []
    
    def _extract_free_games_from_graphql(self, data: Dict) -> List[Dict]:
        """Extrae información de juegos del response GraphQL"""
        games = []
        
        try:
            modules = data.get('data', {}).get('Storefront', {}).get('discoverLayout', {}).get('modules', [])
            
            for module in modules:
                if module.get('__typename') == 'StorefrontCardGroup':
                    offers = module.get('offers', [])
                    
                    for offer_data in offers:
                        offer = offer_data.get('offer', {})
                        if self._is_free_game(offer):
                            game_info = self._extract_game_info(offer)
                            if game_info:
                                games.append(game_info)
            
            return games[:4]  # Solo los primeros 4
            
        except Exception as e:
            logger.error(f"Error extrayendo juegos de GraphQL: {e}")
            return []
    
    def _extract_free_games_from_html(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrae información de juegos del HTML"""
        games = []
        
        try:
            # Buscar elementos que contengan juegos gratuitos
            game_elements = soup.find_all(['div', 'section'], class_=lambda x: x and 'card' in x.lower())
            
            for element in game_elements[:4]:
                game_info = self._extract_game_info_from_element(element)
                if game_info:
                    games.append(game_info)
            
            return games
            
        except Exception as e:
            logger.error(f"Error extrayendo juegos del HTML: {e}")
            return []
    
    def _is_free_game(self, offer: Dict) -> bool:
        """Verifica si una oferta es un juego gratuito"""
        try:
            price = offer.get('price', {}).get('totalPrice', {})
            discount_price = price.get('discountPrice', 0)
            original_price = price.get('originalPrice', 0)
            
            # Es gratuito si el precio con descuento es 0 y el original es mayor a 0
            return discount_price == 0 and original_price > 0
            
        except:
            return False
    
    def _extract_game_info(self, offer: Dict) -> Optional[Dict]:
        """Extrae información relevante de un juego"""
        try:
            title = offer.get('title', 'Sin título')
            description = offer.get('description', 'Sin descripción')
            
            # Obtener imagen
            key_images = offer.get('keyImages', [])
            image_url = None
            for img in key_images:
                if img.get('type') in ['DieselStoreFrontWide', 'OfferImageWide']:
                    image_url = img.get('url')
                    break
            
            # Obtener fechas de promoción
            expiry_date = offer.get('expiryDate')
            promotions = offer.get('promotions', {}).get('promotionalOffers', [])
            
            end_date = None
            if promotions and len(promotions) > 0:
                promo_offers = promotions[0].get('promotionalOffers', [])
                if promo_offers and len(promo_offers) > 0:
                    end_date = promo_offers[0].get('endDate')
            
            if not end_date:
                end_date = expiry_date
            
            return {
                'title': title,
                'description': description,
                'image_url': image_url,
                'end_date': end_date,
                'namespace': offer.get('namespace'),
                'id': offer.get('id'),
                'extracted_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo info del juego: {e}")
            return None
    
    def _extract_game_info_from_element(self, element) -> Optional[Dict]:
        """Extrae información de un elemento HTML"""
        try:
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            title = title_elem.get_text(strip=True) if title_elem else 'Sin título'
            
            desc_elem = element.find(['p', 'div'], class_=lambda x: x and 'desc' in x.lower())
            description = desc_elem.get_text(strip=True) if desc_elem else 'Sin descripción'
            
            img_elem = element.find('img')
            image_url = img_elem.get('src') if img_elem else None
            
            return {
                'title': title,
                'description': description,
                'image_url': image_url,
                'end_date': None,
                'namespace': None,
                'id': None,
                'extracted_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo del elemento HTML: {e}")
            return None
    
    def get_current_free_games(self) -> List[Dict]:
        """Método principal para obtener juegos gratuitos actuales"""
        logger.info("Obteniendo juegos gratuitos de Epic Games...")
        
        games = self.get_free_games_graphql()
        
        if not games:
            logger.warning("No se pudieron obtener juegos, intentando método alternativo...")
            games = self.get_free_games_scraping()
        
        logger.info(f"Se encontraron {len(games)} juegos gratuitos")
        return games
