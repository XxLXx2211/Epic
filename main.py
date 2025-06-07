#!/usr/bin/env python3
"""
Epic Games Free Games Monitor
Monitorea automáticamente los juegos gratuitos de Epic Games Store
y envía notificaciones por correo cuando hay nuevos juegos disponibles.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Optional

from epic_games_monitor import EpicGamesMonitor
from email_sender import EmailSender
from game_relevance import GameRelevanceEvaluator
from config import DATABASE_FILE, MAX_GAMES_TO_PROCESS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('epic_games_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class EpicGamesNotifier:
    def __init__(self):
        self.monitor = EpicGamesMonitor()
        self.email_sender = EmailSender()
        self.relevance_evaluator = GameRelevanceEvaluator()
        self.database_file = DATABASE_FILE
    
    def run(self):
        """Ejecuta el proceso completo de monitoreo y notificación"""
        logger.info("🚀 Iniciando Epic Games Monitor...")
        
        try:
            # Obtener juegos actuales
            current_games = self.monitor.get_current_free_games()
            
            if not current_games:
                logger.warning("⚠️ No se pudieron obtener juegos gratuitos")
                return
            
            # Limitar a los primeros 4 juegos
            current_games = current_games[:MAX_GAMES_TO_PROCESS]
            logger.info(f"📋 Se encontraron {len(current_games)} juegos gratuitos")
            
            # Cargar juegos anteriores
            previous_games = self.load_previous_games()
            
            # Verificar si hay cambios
            if self.games_have_changed(current_games, previous_games):
                logger.info("🆕 Se detectaron cambios en los juegos gratuitos")
                
                # Evaluar relevancia de los juegos
                relevance_data = self.evaluate_games_relevance(current_games)
                
                # Enviar notificación
                if self.send_notification(current_games, relevance_data):
                    logger.info("📧 Notificación enviada exitosamente")
                    
                    # Guardar juegos actuales
                    self.save_current_games(current_games)
                    logger.info("💾 Base de datos actualizada")
                else:
                    logger.error("❌ Error enviando notificación")
            else:
                logger.info("✅ No hay cambios en los juegos gratuitos")
            
            logger.info("🏁 Proceso completado exitosamente")
            
        except Exception as e:
            logger.error(f"💥 Error en el proceso principal: {e}")
            raise
    
    def load_previous_games(self) -> List[Dict]:
        """Carga los juegos del día anterior desde la base de datos"""
        try:
            if os.path.exists(self.database_file):
                with open(self.database_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('games', [])
            return []
        except Exception as e:
            logger.error(f"Error cargando juegos anteriores: {e}")
            return []
    
    def save_current_games(self, games: List[Dict]):
        """Guarda los juegos actuales en la base de datos"""
        try:
            data = {
                'last_update': datetime.now(timezone.utc).isoformat(),
                'games': games,
                'total_games': len(games)
            }
            
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error guardando juegos actuales: {e}")
    
    def games_have_changed(self, current_games: List[Dict], previous_games: List[Dict]) -> bool:
        """Verifica si los juegos han cambiado desde la última ejecución"""
        if len(current_games) != len(previous_games):
            logger.info(f"📊 Cambio en cantidad: {len(previous_games)} -> {len(current_games)}")
            return True
        
        # Crear sets de títulos para comparación
        current_titles = {self.normalize_title(game.get('title', '')) for game in current_games}
        previous_titles = {self.normalize_title(game.get('title', '')) for game in previous_games}
        
        if current_titles != previous_titles:
            new_games = current_titles - previous_titles
            removed_games = previous_titles - current_titles
            
            if new_games:
                logger.info(f"🆕 Juegos nuevos: {', '.join(new_games)}")
            if removed_games:
                logger.info(f"🗑️ Juegos removidos: {', '.join(removed_games)}")
            
            return True
        
        logger.info("🔄 Los juegos son los mismos que el día anterior")
        return False
    
    def normalize_title(self, title: str) -> str:
        """Normaliza un título para comparación"""
        return title.lower().strip()
    
    def evaluate_games_relevance(self, games: List[Dict]) -> List[Dict]:
        """Evalúa la relevancia de cada juego"""
        logger.info("🔍 Evaluando relevancia de los juegos...")
        relevance_data = []
        
        for i, game in enumerate(games):
            title = game.get('title', '')
            logger.info(f"📊 Evaluando juego {i+1}/{len(games)}: {title}")
            
            try:
                relevance = self.relevance_evaluator.evaluate_game_relevance(title)
                relevance_data.append(relevance)
                
                level = relevance.get('relevance_level', 'Desconocida')
                logger.info(f"✅ {title}: {level}")
                
            except Exception as e:
                logger.error(f"❌ Error evaluando {title}: {e}")
                # Agregar datos básicos en caso de error
                relevance_data.append({
                    'title': title,
                    'relevance_level': 'Error en evaluación',
                    'rating': 0,
                    'popularity_score': 0,
                    'sources': []
                })
        
        return relevance_data
    
    def send_notification(self, games: List[Dict], relevance_data: List[Dict]) -> bool:
        """Envía la notificación por correo electrónico"""
        logger.info("📧 Enviando notificación por correo...")
        
        try:
            return self.email_sender.send_games_notification(games, relevance_data)
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
            return False
    
    def print_games_summary(self, games: List[Dict], relevance_data: List[Dict]):
        """Imprime un resumen de los juegos encontrados"""
        print("\n" + "="*60)
        print("🎮 EPIC GAMES - JUEGOS GRATUITOS")
        print("="*60)
        
        for i, game in enumerate(games):
            relevance = relevance_data[i] if i < len(relevance_data) else {}
            
            print(f"\n🎯 JUEGO #{i+1}")
            print(f"📝 Título: {game.get('title', 'Sin título')}")
            
            if game.get('description'):
                desc = game['description'][:100] + "..." if len(game['description']) > 100 else game['description']
                print(f"📄 Descripción: {desc}")
            
            if game.get('end_date'):
                print(f"📅 Expira: {game['end_date']}")
            
            if relevance:
                print(f"⭐ Relevancia: {relevance.get('relevance_level', 'Desconocida')}")
                if relevance.get('rating', 0) > 0:
                    print(f"📊 Puntuación: {relevance['rating']:.1f}/5.0")
        
        print("\n" + "="*60)

def main():
    """Función principal"""
    try:
        notifier = EpicGamesNotifier()
        notifier.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
