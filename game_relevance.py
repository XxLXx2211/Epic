import requests
import logging
from typing import Dict, Optional
from config import RAWG_API_KEY, STEAM_API_KEY, HEADERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameRelevanceEvaluator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def evaluate_game_relevance(self, game_title: str) -> Dict:
        """Evalúa la relevancia de un juego basado en múltiples fuentes"""
        relevance_data = {
            'title': game_title,
            'rating': 0.0,
            'popularity_score': 0,
            'review_count': 0,
            'relevance_level': 'Desconocida',
            'sources': []
        }
        
        # Intentar obtener datos de RAWG
        rawg_data = self._get_rawg_data(game_title)
        if rawg_data:
            relevance_data.update(rawg_data)
            relevance_data['sources'].append('RAWG')
        
        # Intentar obtener datos de Steam (método alternativo)
        steam_data = self._get_steam_data(game_title)
        if steam_data:
            # Combinar datos de Steam con los existentes
            if steam_data.get('rating', 0) > relevance_data.get('rating', 0):
                relevance_data.update(steam_data)
            relevance_data['sources'].append('Steam')
        
        # Si no hay datos de APIs, usar evaluación básica
        if not relevance_data['sources']:
            relevance_data = self._basic_relevance_evaluation(game_title)
        
        # Calcular nivel de relevancia final
        relevance_data['relevance_level'] = self._calculate_relevance_level(relevance_data)
        
        return relevance_data
    
    def _get_rawg_data(self, game_title: str) -> Optional[Dict]:
        """Obtiene datos del juego desde RAWG API"""
        if not RAWG_API_KEY:
            return None
        
        try:
            # Buscar el juego
            search_url = "https://api.rawg.io/api/games"
            params = {
                'key': RAWG_API_KEY,
                'search': game_title,
                'page_size': 1
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                return None
            
            game = results[0]
            
            return {
                'rating': game.get('rating', 0.0),
                'popularity_score': game.get('ratings_count', 0),
                'review_count': game.get('reviews_count', 0),
                'metacritic_score': game.get('metacritic', 0),
                'released': game.get('released'),
                'genres': [genre['name'] for genre in game.get('genres', [])],
                'platforms': [platform['platform']['name'] for platform in game.get('platforms', [])]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de RAWG para {game_title}: {e}")
            return None
    
    def _get_steam_data(self, game_title: str) -> Optional[Dict]:
        """Obtiene datos del juego desde Steam (método simplificado)"""
        try:
            # Buscar en Steam usando web scraping básico
            search_url = "https://store.steampowered.com/search/"
            params = {
                'term': game_title,
                'category1': 998  # Juegos
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            # Análisis básico del HTML de Steam
            if "search_result_row" in response.text:
                # Si encontramos resultados, asignar una puntuación básica
                return {
                    'rating': 3.5,  # Puntuación promedio
                    'popularity_score': 100,  # Puntuación básica
                    'review_count': 50,
                    'platform': 'Steam'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de Steam para {game_title}: {e}")
            return None
    
    def _basic_relevance_evaluation(self, game_title: str) -> Dict:
        """Evaluación básica de relevancia basada en el título"""
        relevance_data = {
            'title': game_title,
            'rating': 3.0,  # Puntuación neutral
            'popularity_score': 50,
            'review_count': 0,
            'sources': ['Evaluación básica']
        }
        
        # Palabras clave que indican juegos populares/relevantes
        popular_keywords = [
            'AAA', 'indie', 'multiplayer', 'online', 'battle', 'royale',
            'RPG', 'action', 'adventure', 'strategy', 'simulation',
            'horror', 'survival', 'racing', 'sports', 'puzzle'
        ]
        
        title_lower = game_title.lower()
        keyword_matches = sum(1 for keyword in popular_keywords if keyword.lower() in title_lower)
        
        # Ajustar puntuación basada en palabras clave
        if keyword_matches > 0:
            relevance_data['rating'] = min(4.0, 3.0 + (keyword_matches * 0.2))
            relevance_data['popularity_score'] = min(200, 50 + (keyword_matches * 25))
        
        # Juegos con nombres conocidos o franquicias
        known_franchises = [
            'assassin', 'call of duty', 'battlefield', 'fifa', 'nba',
            'grand theft', 'elder scrolls', 'fallout', 'witcher',
            'minecraft', 'fortnite', 'apex', 'valorant', 'overwatch'
        ]
        
        for franchise in known_franchises:
            if franchise in title_lower:
                relevance_data['rating'] = 4.5
                relevance_data['popularity_score'] = 500
                break
        
        return relevance_data
    
    def _calculate_relevance_level(self, relevance_data: Dict) -> str:
        """Calcula el nivel de relevancia basado en los datos disponibles"""
        rating = relevance_data.get('rating', 0)
        popularity = relevance_data.get('popularity_score', 0)
        
        # Calcular puntuación combinada
        combined_score = (rating * 20) + (min(popularity, 1000) / 10)
        
        if combined_score >= 150:
            return "🔥 MUY ALTA - Juego muy popular y bien valorado"
        elif combined_score >= 100:
            return "⭐ ALTA - Juego popular con buenas valoraciones"
        elif combined_score >= 70:
            return "👍 MEDIA - Juego decente, vale la pena probarlo"
        elif combined_score >= 40:
            return "🤔 BAJA - Juego de nicho o valoraciones mixtas"
        else:
            return "❓ DESCONOCIDA - Información limitada disponible"
    
    def get_relevance_summary(self, relevance_data: Dict) -> str:
        """Genera un resumen de la relevancia para el email"""
        rating = relevance_data.get('rating', 0)
        popularity = relevance_data.get('popularity_score', 0)
        review_count = relevance_data.get('review_count', 0)
        sources = relevance_data.get('sources', [])
        
        summary = f"**Relevancia:** {relevance_data.get('relevance_level', 'Desconocida')}\n"
        
        if rating > 0:
            summary += f"**Puntuación:** {rating:.1f}/5.0\n"
        
        if popularity > 0:
            summary += f"**Popularidad:** {popularity:,} puntos\n"
        
        if review_count > 0:
            summary += f"**Reseñas:** {review_count:,}\n"
        
        if sources:
            summary += f"**Fuentes:** {', '.join(sources)}\n"
        
        return summary
