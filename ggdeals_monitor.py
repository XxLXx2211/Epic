import requests
import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from config import GGDEALS_API_KEY, GGDEALS_BASE_URL, HEADERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GGDealsMonitor:
    def __init__(self):
        self.session = requests.Session()
        # Headers específicos para GG.deals API
        ggdeals_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
        self.session.headers.update(ggdeals_headers)
        self.api_key = GGDEALS_API_KEY
        self.base_url = GGDEALS_BASE_URL

    def get_high_discount_games(self, min_discount_percent: int = 80, max_games: int = 4) -> List[Dict]:
        """Obtiene juegos con alto descuento desde GG.deals usando la API oficial"""
        if not self.api_key:
            logger.warning("GG.deals API key no configurada")
            return []

        logger.info(f"Usando API key: {self.api_key[:10]}..." if len(self.api_key) > 10 else "API key muy corta")

        logger.info(f"Buscando juegos con {min_discount_percent}%+ de descuento en GG.deals...")

        try:
            # Obtener bundles activos usando la API oficial
            bundles = self._get_active_bundles()

            if not bundles:
                logger.warning("No se pudieron obtener bundles de GG.deals")
                return []

            # Filtrar y evaluar juegos con alto descuento
            high_discount_games = self._filter_high_discount_games(bundles, min_discount_percent)

            if not high_discount_games:
                logger.info("No se encontraron juegos con descuentos altos en GG.deals")
                return []

            # Ordenar por calidad/relevancia y limitar cantidad
            sorted_games = self._sort_games_by_quality(high_discount_games)

            result = sorted_games[:max_games]
            logger.info(f"Se encontraron {len(result)} juegos reales con {min_discount_percent}%+ de descuento")

            return result

        except Exception as e:
            logger.error(f"Error obteniendo juegos de GG.deals: {e}")
            return []





    def _get_active_bundles(self) -> List[Dict]:
        """Obtiene bundles activos de GG.deals usando la API oficial"""
        try:
            url = f"{self.base_url}/bundles/active/"
            params = {
                'key': self.api_key,
                'region': 'us'  # Usar región US por defecto
            }

            logger.info(f"Obteniendo bundles activos de GG.deals...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            logger.info(f"API Response success: {data.get('success', False)}")

            if not data.get('success', False):
                error_info = data.get('data', {})
                logger.error(f"GG.deals API error: {error_info}")
                return []

            # Extraer bundles según la documentación oficial
            bundles_data = data.get('data', {})
            bundles = bundles_data.get('bundles', [])
            total_count = bundles_data.get('totalCount', 0)

            logger.info(f"Obtenidos {len(bundles)} bundles de {total_count} totales")
            return bundles

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON de GG.deals: {e}")
            logger.error(f"Status code: {response.status_code}")
            logger.error(f"Response headers: {dict(response.headers)}")
            logger.error(f"Response content: {response.text[:1000]}")
            logger.error(f"Response length: {len(response.content)} bytes")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con GG.deals API: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado obteniendo bundles: {e}")
            if 'response' in locals():
                logger.error(f"Status code: {getattr(response, 'status_code', 'N/A')}")
                logger.error(f"Response content: {getattr(response, 'text', 'N/A')[:1000]}")
            return []

    def _filter_high_discount_games(self, bundles: List[Dict], min_discount: int) -> List[Dict]:
        """Filtra juegos con alto descuento de los bundles"""
        high_discount_games = []

        for bundle in bundles:
            try:
                bundle_title = bundle.get('title', '')
                bundle_url = bundle.get('url', '')
                date_to = bundle.get('dateTo')

                for tier in bundle.get('tiers', []):
                    price = float(tier.get('price', '0'))
                    currency = tier.get('currency', 'USD')
                    games = tier.get('games', [])

                    if len(games) > 0 and price > 0:
                        # Manejar "Build your own" bundles correctamente
                        games_count = tier.get('gamesCount')
                        if games_count is not None:  # Build your own bundle
                            price_per_game = price / games_count if games_count > 0 else price
                            effective_games = games_count
                        else:  # Bundle estándar
                            price_per_game = price / len(games)
                            effective_games = len(games)

                        # Estimar descuento más realista basado en precio por juego
                        estimated_discount = self._estimate_discount_by_price(price_per_game)

                        if estimated_discount >= min_discount:
                            for game in games:
                                game_info = {
                                    'title': game.get('title', 'Sin título'),
                                    'url': game.get('url', ''),
                                    'bundle_title': bundle_title,
                                    'bundle_url': bundle_url,
                                    'price': price,
                                    'currency': currency,
                                    'price_per_game': round(price_per_game, 2),
                                    'estimated_discount': round(estimated_discount, 1),
                                    'games_in_tier': len(games),
                                    'end_date': date_to,
                                    'extracted_at': datetime.now(timezone.utc).isoformat()
                                }
                                high_discount_games.append(game_info)

            except Exception as e:
                logger.error(f"Error procesando bundle: {e}")
                continue

        return high_discount_games

    def _estimate_discount_by_price(self, price_per_game: float) -> float:
        """Estima el porcentaje de descuento basado en el precio por juego"""
        # Estimaciones más realistas basadas en precios típicos de juegos
        if price_per_game <= 1.0:
            return 95.0  # Precio muy bajo, descuento muy alto
        elif price_per_game <= 2.0:
            return 90.0  # Precio bajo, descuento alto
        elif price_per_game <= 5.0:
            return 85.0  # Precio moderado, buen descuento
        elif price_per_game <= 10.0:
            return 80.0  # Precio razonable, descuento decente
        elif price_per_game <= 15.0:
            return 75.0  # Precio medio, descuento moderado
        else:
            return 70.0  # Precio alto, descuento menor

    def _sort_games_by_quality(self, games: List[Dict]) -> List[Dict]:
        """Ordena juegos por calidad/relevancia"""
        def quality_score(game):
            score = 0
            title = game.get('title', '').lower()

            quality_keywords = [
                'goty', 'edition', 'deluxe', 'ultimate', 'complete', 'definitive',
                'remastered', 'enhanced', 'director', 'special', 'premium'
            ]

            for keyword in quality_keywords:
                if keyword in title:
                    score += 10

            known_franchises = [
                'assassin', 'call of duty', 'battlefield', 'fifa', 'nba',
                'grand theft', 'elder scrolls', 'fallout', 'witcher',
                'tomb raider', 'far cry', 'bioshock', 'borderlands',
                'civilization', 'total war', 'dark souls', 'sekiro',
                'resident evil', 'final fantasy', 'metal gear'
            ]

            for franchise in known_franchises:
                if franchise in title:
                    score += 20

            discount = game.get('estimated_discount', 0)
            if discount >= 90:
                score += 15
            elif discount >= 85:
                score += 10
            elif discount >= 80:
                score += 5

            price_per_game = game.get('price_per_game', 0)
            if price_per_game > 10:
                score -= 5
            elif price_per_game > 5:
                score -= 2

            return score

        return sorted(games, key=quality_score, reverse=True)

    def _format_date(self, date_str: str) -> str:
        """Formatea una fecha para mostrar"""
        if not date_str:
            return "Sin fecha límite"

        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d/%m/%Y')
        except Exception:
            return date_str

    def get_deals_summary(self, games: List[Dict]) -> str:
        """Genera un resumen de las ofertas para el email"""
        if not games:
            return "No se encontraron ofertas con descuentos altos."

        summary = f"🔥 **{len(games)} Mejores Ofertas con 80%+ de Descuento:**\n\n"

        for i, game in enumerate(games, 1):
            title = game.get('title', 'Sin título')
            bundle_title = game.get('bundle_title', 'Bundle desconocido')
            price_per_game = game.get('price_per_game', 0)
            currency = game.get('currency', 'USD')
            discount = game.get('estimated_discount', 0)
            end_date = self._format_date(game.get('end_date'))

            summary += f"**{i}. {title}**\n"
            summary += f"   💰 Precio: ~${price_per_game} {currency}\n"
            summary += f"   🔥 Descuento: ~{discount}%\n"
            summary += f"   📦 Bundle: {bundle_title}\n"
            summary += f"   📅 Expira: {end_date}\n\n"

        return summary