import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import List, Dict
from config import EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.smtp_server = EMAIL_SMTP_SERVER
        self.smtp_port = EMAIL_SMTP_PORT
        self.from_email = EMAIL_FROM
        self.password = EMAIL_PASSWORD
        self.to_email = EMAIL_TO
    
    def send_games_notification(self, games: List[Dict], relevance_data: List[Dict]) -> bool:
        """Envía notificación por correo con los juegos gratuitos"""
        try:
            if not self._validate_config():
                logger.error("Configuración de email incompleta")
                return False

            subject = f"🎮 Nuevos Juegos Gratuitos en Epic Games - {datetime.now().strftime('%d/%m/%Y')}"
            html_body = self._create_html_email(games, relevance_data)
            text_body = self._create_text_email(games, relevance_data)

            return self._send_email(subject, html_body, text_body)

        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
            return False

    def send_combined_notification(self, epic_games: List[Dict], relevance_data: List[Dict], ggdeals_games: List[Dict]) -> bool:
        """Envía notificación combinada con Epic Games y GG.deals"""
        try:
            if not self._validate_config():
                logger.error("Configuración de email incompleta")
                return False

            # Determinar el asunto basado en el contenido
            if epic_games and ggdeals_games:
                subject = f"🎮🔥 Epic Games + Ofertas GG.deals - {datetime.now().strftime('%d/%m/%Y')}"
            elif epic_games:
                subject = f"🎮 Nuevos Juegos Gratuitos en Epic Games - {datetime.now().strftime('%d/%m/%Y')}"
            else:
                subject = f"🔥 Mejores Ofertas con Descuentos Altos - {datetime.now().strftime('%d/%m/%Y')}"

            html_body = self._create_combined_html_email(epic_games, relevance_data, ggdeals_games)
            text_body = self._create_combined_text_email(epic_games, relevance_data, ggdeals_games)

            return self._send_email(subject, html_body, text_body)

        except Exception as e:
            logger.error(f"Error enviando notificación combinada: {e}")
            return False
    
    def _validate_config(self) -> bool:
        """Valida que la configuración de email esté completa"""
        return all([
            self.from_email,
            self.password,
            self.to_email,
            self.smtp_server,
            self.smtp_port
        ])
    
    def _create_html_email(self, games: List[Dict], relevance_data: List[Dict]) -> str:
        """Crea el cuerpo HTML del correo"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
                .header h1 { margin: 0; font-size: 28px; }
                .header p { margin: 10px 0 0 0; opacity: 0.9; }
                .game-card { border-bottom: 1px solid #eee; padding: 25px; }
                .game-card:last-child { border-bottom: none; }
                .game-title { color: #333; font-size: 22px; font-weight: bold; margin: 0 0 10px 0; }
                .game-meta { display: flex; flex-wrap: wrap; gap: 15px; margin: 15px 0; }
                .meta-item { background: #f8f9fa; padding: 8px 12px; border-radius: 5px; font-size: 14px; }
                .relevance { background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 15px 0; border-radius: 0 5px 5px 0; }
                .description { color: #666; line-height: 1.6; margin: 15px 0; }
                .game-image { max-width: 100%; height: auto; border-radius: 8px; margin: 15px 0; }
                .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }
                .epic-link { display: inline-block; background: #0078f2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 0; }
                .epic-link:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎮 Epic Games - Juegos Gratuitos</h1>
                    <p>Nuevos juegos disponibles para reclamar</p>
                </div>
        """
        
        for i, game in enumerate(games):
            relevance = relevance_data[i] if i < len(relevance_data) else {}
            
            html += f"""
                <div class="game-card">
                    <h2 class="game-title">{game.get('title', 'Sin título')}</h2>
                    
                    <div class="game-meta">
                        <div class="meta-item">📅 Expira: {self._format_date(game.get('end_date'))}</div>
                        <div class="meta-item">🆓 Precio: GRATIS</div>
                        <div class="meta-item">🎯 Juego #{i+1}</div>
                    </div>
            """
            
            if game.get('image_url'):
                html += f'<img src="{game["image_url"]}" alt="{game.get("title", "")}" class="game-image">'
            
            if game.get('description'):
                html += f'<div class="description">{game["description"]}</div>'
            
            # Información de relevancia
            if relevance:
                html += f"""
                    <div class="relevance">
                        <strong>📊 Análisis de Relevancia:</strong><br>
                        <strong>Nivel:</strong> {relevance.get('relevance_level', 'Desconocida')}<br>
                """
                
                if relevance.get('rating', 0) > 0:
                    html += f"<strong>Puntuación:</strong> {relevance['rating']:.1f}/5.0<br>"
                
                if relevance.get('popularity_score', 0) > 0:
                    html += f"<strong>Popularidad:</strong> {relevance['popularity_score']:,} puntos<br>"
                
                if relevance.get('sources'):
                    html += f"<strong>Fuentes:</strong> {', '.join(relevance['sources'])}<br>"
                
                html += "</div>"
            
            html += """
                    <a href="https://store.epicgames.com/es-ES/free-games" class="epic-link" target="_blank">
                        🎮 Reclamar en Epic Games Store
                    </a>
                </div>
            """
        
        html += f"""
                <div class="footer">
                    <p>📧 Notificación automática generada el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</p>
                    <p>🔗 <a href="https://store.epicgames.com/es-ES/free-games" target="_blank">Visitar Epic Games Store</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def _create_combined_html_email(self, epic_games: List[Dict], relevance_data: List[Dict], ggdeals_games: List[Dict]) -> str:
        """Crea el cuerpo HTML del correo combinado"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
                .header h1 { margin: 0; font-size: 28px; }
                .header p { margin: 10px 0 0 0; opacity: 0.9; }
                .section-header { background: #f8f9fa; padding: 20px; border-bottom: 3px solid #667eea; margin: 0; }
                .section-header h2 { margin: 0; color: #333; font-size: 22px; }
                .game-card { border-bottom: 1px solid #eee; padding: 25px; }
                .game-card:last-child { border-bottom: none; }
                .game-title { color: #333; font-size: 22px; font-weight: bold; margin: 0 0 10px 0; }
                .game-meta { display: flex; flex-wrap: wrap; gap: 15px; margin: 15px 0; }
                .meta-item { background: #f8f9fa; padding: 8px 12px; border-radius: 5px; font-size: 14px; }
                .relevance { background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 15px 0; border-radius: 0 5px 5px 0; }
                .deal-info { background: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 15px 0; border-radius: 0 5px 5px 0; }
                .description { color: #666; line-height: 1.6; margin: 15px 0; }
                .game-image { max-width: 100%; height: auto; border-radius: 8px; margin: 15px 0; }
                .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }
                .epic-link { display: inline-block; background: #0078f2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
                .deal-link { display: inline-block; background: #ff9800; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
                .epic-link:hover { background: #0056b3; }
                .deal-link:hover { background: #f57c00; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎮🔥 Gaming Deals & Free Games</h1>
                    <p>Epic Games gratuitos y mejores ofertas con descuentos altos</p>
                </div>
        """

        # Sección de Epic Games
        if epic_games:
            html += """
                <div class="section-header">
                    <h2>🎮 Epic Games - Juegos Gratuitos</h2>
                </div>
            """

            for i, game in enumerate(epic_games):
                relevance = relevance_data[i] if i < len(relevance_data) else {}

                html += f"""
                    <div class="game-card">
                        <h3 class="game-title">{game.get('title', 'Sin título')}</h3>

                        <div class="game-meta">
                            <div class="meta-item">📅 Expira: {self._format_date(game.get('end_date'))}</div>
                            <div class="meta-item">🆓 Precio: GRATIS</div>
                            <div class="meta-item">🎯 Juego #{i+1}</div>
                        </div>
                """

                if game.get('image_url'):
                    html += f'<img src="{game["image_url"]}" alt="{game.get("title", "")}" class="game-image">'

                if game.get('description'):
                    html += f'<div class="description">{game["description"]}</div>'

                if relevance:
                    html += f"""
                        <div class="relevance">
                            <strong>📊 Análisis de Relevancia:</strong><br>
                            <strong>Nivel:</strong> {relevance.get('relevance_level', 'Desconocida')}<br>
                    """

                    if relevance.get('rating', 0) > 0:
                        html += f"<strong>Puntuación:</strong> {relevance['rating']:.1f}/5.0<br>"

                    if relevance.get('popularity_score', 0) > 0:
                        html += f"<strong>Popularidad:</strong> {relevance['popularity_score']:,} puntos<br>"

                    html += "</div>"

                html += """
                        <a href="https://store.epicgames.com/es-ES/free-games" class="epic-link" target="_blank">
                            🎮 Reclamar en Epic Games Store
                        </a>
                    </div>
                """

        # Sección de GG.deals
        if ggdeals_games:
            html += """
                <div class="section-header">
                    <h2>🔥 GG.deals - Ofertas con 80%+ de Descuento</h2>
                </div>
            """

            for i, game in enumerate(ggdeals_games):
                html += f"""
                    <div class="game-card">
                        <h3 class="game-title">{game.get('title', 'Sin título')}</h3>

                        <div class="game-meta">
                            <div class="meta-item">💰 Precio: ~${game.get('price_per_game', 0)} {game.get('currency', 'USD')}</div>
                            <div class="meta-item">🔥 Descuento: ~{game.get('estimated_discount', 0)}%</div>
                            <div class="meta-item">📅 Expira: {self._format_date(game.get('end_date'))}</div>
                        </div>

                        <div class="deal-info">
                            <strong>📦 Bundle:</strong> {game.get('bundle_title', 'Bundle desconocido')}<br>
                            <strong>🎮 Juegos en tier:</strong> {game.get('games_in_tier', 1)}<br>
                            <strong>💵 Precio total del bundle:</strong> ${game.get('price', 0)} {game.get('currency', 'USD')}
                        </div>
                """

                if game.get('url'):
                    html += f"""
                        <a href="{game['url']}" class="deal-link" target="_blank">
                            🔗 Ver en GG.deals
                        </a>
                    """

                if game.get('bundle_url'):
                    html += f"""
                        <a href="{game['bundle_url']}" class="deal-link" target="_blank">
                            📦 Ver Bundle Completo
                        </a>
                    """

                html += "</div>"

        html += f"""
                <div class="footer">
                    <p>📧 Notificación automática generada el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</p>
                    <p>🔗 <a href="https://store.epicgames.com/es-ES/free-games" target="_blank">Epic Games Store</a> |
                       <a href="https://gg.deals" target="_blank">GG.deals</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _create_combined_text_email(self, epic_games: List[Dict], relevance_data: List[Dict], ggdeals_games: List[Dict]) -> str:
        """Crea el cuerpo de texto plano del correo combinado"""
        text = f"🎮🔥 GAMING DEALS & FREE GAMES\n"
        text += f"Fecha: {datetime.now().strftime('%d/%m/%Y')}\n"
        text += "=" * 60 + "\n\n"

        # Sección Epic Games
        if epic_games:
            text += "🎮 EPIC GAMES - JUEGOS GRATUITOS\n"
            text += "-" * 40 + "\n\n"

            for i, game in enumerate(epic_games):
                relevance = relevance_data[i] if i < len(relevance_data) else {}

                text += f"JUEGO #{i+1}: {game.get('title', 'Sin título')}\n"
                text += "-" * 30 + "\n"

                if game.get('description'):
                    text += f"Descripción: {game['description']}\n"

                text += f"Expira: {self._format_date(game.get('end_date'))}\n"
                text += f"Precio: GRATIS\n"

                if relevance:
                    text += f"\n📊 RELEVANCIA:\n"
                    text += f"Nivel: {relevance.get('relevance_level', 'Desconocida')}\n"

                    if relevance.get('rating', 0) > 0:
                        text += f"Puntuación: {relevance['rating']:.1f}/5.0\n"

                    if relevance.get('popularity_score', 0) > 0:
                        text += f"Popularidad: {relevance['popularity_score']:,} puntos\n"

                text += f"\n🔗 Reclamar: https://store.epicgames.com/es-ES/free-games\n"
                text += "\n" + "=" * 40 + "\n\n"

        # Sección GG.deals
        if ggdeals_games:
            text += "🔥 GG.DEALS - OFERTAS CON 80%+ DE DESCUENTO\n"
            text += "-" * 50 + "\n\n"

            for i, game in enumerate(ggdeals_games):
                text += f"OFERTA #{i+1}: {game.get('title', 'Sin título')}\n"
                text += "-" * 30 + "\n"

                text += f"Precio: ~${game.get('price_per_game', 0)} {game.get('currency', 'USD')}\n"
                text += f"Descuento: ~{game.get('estimated_discount', 0)}%\n"
                text += f"Bundle: {game.get('bundle_title', 'Bundle desconocido')}\n"
                text += f"Juegos en tier: {game.get('games_in_tier', 1)}\n"
                text += f"Precio total bundle: ${game.get('price', 0)} {game.get('currency', 'USD')}\n"
                text += f"Expira: {self._format_date(game.get('end_date'))}\n"

                if game.get('url'):
                    text += f"Ver juego: {game['url']}\n"
                if game.get('bundle_url'):
                    text += f"Ver bundle: {game['bundle_url']}\n"

                text += "\n" + "=" * 40 + "\n\n"

        text += f"Notificación generada automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}\n"
        text += "Epic Games Store: https://store.epicgames.com/es-ES/free-games\n"
        text += "GG.deals: https://gg.deals\n"

        return text
    
    def _create_text_email(self, games: List[Dict], relevance_data: List[Dict]) -> str:
        """Crea el cuerpo de texto plano del correo"""
        text = f"🎮 EPIC GAMES - JUEGOS GRATUITOS\n"
        text += f"Fecha: {datetime.now().strftime('%d/%m/%Y')}\n"
        text += "=" * 50 + "\n\n"
        
        for i, game in enumerate(games):
            relevance = relevance_data[i] if i < len(relevance_data) else {}
            
            text += f"JUEGO #{i+1}: {game.get('title', 'Sin título')}\n"
            text += "-" * 30 + "\n"
            
            if game.get('description'):
                text += f"Descripción: {game['description']}\n"
            
            text += f"Expira: {self._format_date(game.get('end_date'))}\n"
            text += f"Precio: GRATIS\n"
            
            if relevance:
                text += f"\n📊 RELEVANCIA:\n"
                text += f"Nivel: {relevance.get('relevance_level', 'Desconocida')}\n"
                
                if relevance.get('rating', 0) > 0:
                    text += f"Puntuación: {relevance['rating']:.1f}/5.0\n"
                
                if relevance.get('popularity_score', 0) > 0:
                    text += f"Popularidad: {relevance['popularity_score']:,} puntos\n"
            
            text += f"\n🔗 Reclamar: https://store.epicgames.com/es-ES/free-games\n"
            text += "\n" + "=" * 50 + "\n\n"
        
        text += f"Notificación generada automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}\n"
        
        return text
    
    def _format_date(self, date_str: str) -> str:
        """Formatea una fecha para mostrar"""
        if not date_str:
            return "Fecha no disponible"
        
        try:
            # Intentar parsear diferentes formatos de fecha
            for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%d/%m/%Y')
                except ValueError:
                    continue
            
            return date_str  # Si no se puede parsear, devolver como está
            
        except Exception:
            return "Fecha no disponible"
    
    def _send_email(self, subject: str, html_body: str, text_body: str) -> bool:
        """Envía el correo electrónico"""
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            
            # Agregar partes del mensaje
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            html_part = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Enviar correo
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)
            
            logger.info(f"Correo enviado exitosamente a {self.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando correo: {e}")
            return False
