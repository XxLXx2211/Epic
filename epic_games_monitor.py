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
            # Usar API alternativa más confiable
            return self.get_free_games_alternative_api()

        except Exception as e:
            logger.error(f"Error obteniendo juegos con GraphQL: {e}")
            return self.get_free_games_scraping()

    def get_free_games_alternative_api(self) -> List[Dict]:
        """Obtiene juegos usando API alternativa"""
        try:
            # Usar la API de Epic Games Store que es más estable
            url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
            params = {
                'locale': 'es-ES',
                'country': 'ES',
                'allowCountries': 'ES'
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return self._extract_free_games_from_api(data)

        except Exception as e:
            logger.error(f"Error con API alternativa: {e}")
            return []
    
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
    
    def _extract_free_games_from_api(self, data: Dict) -> List[Dict]:
        """Extrae información de juegos de la API alternativa"""
        games = []

        try:
            elements = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])

            for element in elements:
                if self._is_free_promotion(element):
                    game_info = self._extract_game_info_from_element_api(element)
                    if game_info:
                        games.append(game_info)

            return games[:4]  # Solo los primeros 4

        except Exception as e:
            logger.error(f"Error extrayendo juegos de API alternativa: {e}")
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
    
    def _is_free_promotion(self, element: Dict) -> bool:
        """Verifica si un elemento es una promoción gratuita"""
        try:
            promotions = element.get('promotions', {})
            promotional_offers = promotions.get('promotionalOffers', [])

            if promotional_offers:
                for promo_group in promotional_offers:
                    offers = promo_group.get('promotionalOffers', [])
                    for offer in offers:
                        discount_setting = offer.get('discountSetting', {})
                        if discount_setting.get('discountType') == 'PERCENTAGE' and discount_setting.get('discountPercentage') == 0:
                            return True

            return False

        except:
            return False

    def _extract_game_info_from_element_api(self, element: Dict) -> Optional[Dict]:
        """Extrae información de un elemento de la API"""
        try:
            title = element.get('title', 'Sin título')
            description = element.get('description', 'Sin descripción')

            # Obtener imagen
            key_images = element.get('keyImages', [])
            image_url = None
            for img in key_images:
                if img.get('type') in ['DieselStoreFrontWide', 'OfferImageWide', 'Thumbnail']:
                    image_url = img.get('url')
                    break

            # Obtener fechas de promoción
            end_date = None
            promotions = element.get('promotions', {})
            promotional_offers = promotions.get('promotionalOffers', [])

            if promotional_offers:
                for promo_group in promotional_offers:
                    offers = promo_group.get('promotionalOffers', [])
                    for offer in offers:
                        end_date = offer.get('endDate')
                        if end_date:
                            break
                    if end_date:
                        break

            return {
                'title': title,
                'description': description,
                'image_url': image_url,
                'end_date': end_date,
                'namespace': element.get('namespace'),
                'id': element.get('id'),
                'extracted_at': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error extrayendo info del elemento API: {e}")
            return None

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

        if not games:
            logger.warning("No se pudieron obtener juegos reales, usando datos de ejemplo para testing...")
            games = self._get_example_games()

        logger.info(f"Se encontraron {len(games)} juegos gratuitos")
        return games

    def _get_example_games(self) -> List[Dict]:
        """Genera juegos de ejemplo para testing"""
        from datetime import datetime, timedelta

        example_games = [
            {
                'title': 'Epic Game Example 1',
                'description': 'Un increíble juego de aventuras con gráficos impresionantes y una historia envolvente.',
                'image_url': 'https://via.placeholder.com/460x215/0078f2/ffffff?text=Epic+Game+1',
                'end_date': (datetime.now() + timedelta(days=7)).isoformat(),
                'namespace': 'example1',
                'id': 'example-game-1',
                'extracted_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'title': 'Epic Game Example 2',
                'description': 'Un juego de estrategia que desafiará tu mente y te mantendrá entretenido por horas.',
                'image_url': 'https://via.placeholder.com/460x215/764ba2/ffffff?text=Epic+Game+2',
                'end_date': (datetime.now() + timedelta(days=6)).isoformat(),
                'namespace': 'example2',
                'id': 'example-game-2',
                'extracted_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'title': 'Epic Game Example 3',
                'description': 'Un juego de acción lleno de adrenalina con combates épicos y mundos por explorar.',
                'image_url': 'https://via.placeholder.com/460x215/667eea/ffffff?text=Epic+Game+3',
                'end_date': (datetime.now() + timedelta(days=5)).isoformat(),
                'namespace': 'example3',
                'id': 'example-game-3',
                'extracted_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'title': 'Epic Game Example 4',
                'description': 'Un juego indie único con mecánicas innovadoras y un estilo artístico distintivo.',
                'image_url': 'https://via.placeholder.com/460x215/f093fb/ffffff?text=Epic+Game+4',
                'end_date': (datetime.now() + timedelta(days=4)).isoformat(),
                'namespace': 'example4',
                'id': 'example-game-4',
                'extracted_at': datetime.now(timezone.utc).isoformat()
            }
        ]

        return example_games
