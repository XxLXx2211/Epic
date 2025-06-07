# 🎮 Epic Games Free Games Monitor

Monitor automático de juegos gratuitos de Epic Games Store que envía notificaciones por correo electrónico cuando hay nuevos juegos disponibles.

## ✨ Características

- 🔄 **Monitoreo automático diario** usando GitHub Actions
- 📧 **Notificaciones por email** con información detallada
- 🎯 **Análisis de relevancia** de cada juego
- 🚫 **Detección de duplicados** - no envía el mismo juego dos veces
- 🌐 **Completamente automatizado** - no requiere PC encendida
- 📊 **Información completa**: nombres, fechas de expiración, relevancia

## 🚀 Configuración Rápida

### 1. Configurar Variables de Entorno en GitHub

Ve a tu repositorio → Settings → Secrets and variables → Actions → New repository secret

Agrega estos secrets:

```
EMAIL_FROM: tu_email@gmail.com
EMAIL_PASSWORD: tu_contraseña_de_aplicacion_gmail
EMAIL_TO: destinatario@gmail.com
```

### 2. Configurar Gmail (Requerido)

Para usar Gmail necesitas una **contraseña de aplicación**:

1. Ve a tu cuenta de Google → Seguridad
2. Activa la verificación en 2 pasos
3. Ve a "Contraseñas de aplicaciones"
4. Genera una nueva contraseña para "Correo"
5. Usa esa contraseña en `EMAIL_PASSWORD`

### 3. APIs Opcionales para Relevancia

Para mejor análisis de relevancia (opcional):

```
RAWG_API_KEY: tu_api_key_de_rawg
STEAM_API_KEY: tu_api_key_de_steam
```

- **RAWG API**: Gratis en https://rawg.io/apidocs
- **Steam API**: Gratis en https://steamcommunity.com/dev/apikey

## 📅 Programación

El monitor se ejecuta automáticamente:
- **Todos los días a las 10:00 AM UTC** (11:00 AM CET)
- También puedes ejecutarlo manualmente desde GitHub Actions

## 📧 Formato del Email

Recibirás un email HTML con:

- 🎮 **Título del juego**
- 📅 **Fecha de expiración**
- 📝 **Descripción**
- 🖼️ **Imagen del juego**
- ⭐ **Análisis de relevancia**:
  - Nivel de relevancia (Muy Alta, Alta, Media, Baja)
  - Puntuación (si disponible)
  - Popularidad
  - Fuentes de datos
- 🔗 **Link directo a Epic Games Store**

## 🔧 Ejecución Local (Opcional)

Si quieres probarlo localmente:

```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/Epic.git
cd Epic

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env con tus credenciales
cp .env.example .env
# Editar .env con tus datos

# Ejecutar
python main.py
```

## 📁 Estructura del Proyecto

```
Epic/
├── main.py                    # Script principal
├── epic_games_monitor.py      # Monitor de Epic Games
├── email_sender.py           # Envío de correos
├── game_relevance.py         # Evaluación de relevancia
├── config.py                 # Configuración
├── requirements.txt          # Dependencias
├── last_games.json          # Base de datos de juegos
├── .github/workflows/       # Automatización GitHub Actions
│   └── daily-check.yml
├── .env.example             # Ejemplo de variables
└── README.md               # Este archivo
```

## 🛠️ Cómo Funciona

1. **Monitoreo**: Se conecta a Epic Games Store usando GraphQL API
2. **Comparación**: Compara con los juegos del día anterior
3. **Detección**: Si hay cambios, evalúa la relevancia de cada juego
4. **Notificación**: Envía email solo si hay juegos nuevos o diferentes
5. **Actualización**: Guarda los juegos actuales para la próxima comparación

## 🔍 Evaluación de Relevancia

El sistema evalúa cada juego usando:

- **RAWG Database**: Puntuaciones y popularidad
- **Steam Data**: Información adicional
- **Análisis de palabras clave**: Para juegos sin datos
- **Franquicias conocidas**: Detección de series populares

Niveles de relevancia:
- 🔥 **MUY ALTA**: Juegos muy populares y bien valorados
- ⭐ **ALTA**: Juegos populares con buenas valoraciones  
- 👍 **MEDIA**: Juegos decentes, vale la pena probarlos
- 🤔 **BAJA**: Juegos de nicho o valoraciones mixtas
- ❓ **DESCONOCIDA**: Información limitada disponible

## 🚫 Prevención de Duplicados

- Compara títulos de juegos normalizados
- Solo envía email si hay cambios reales
- Mantiene historial en `last_games.json`
- Actualiza automáticamente la base de datos

## 📝 Logs

Los logs se guardan en:
- GitHub Actions: Ve a la pestaña "Actions" de tu repo
- Local: archivo `epic_games_monitor.log`

## ❓ Solución de Problemas

### No recibo emails
1. Verifica que las variables de entorno estén configuradas
2. Asegúrate de usar contraseña de aplicación de Gmail
3. Revisa los logs en GitHub Actions

### Error de autenticación Gmail
1. Activa verificación en 2 pasos
2. Genera nueva contraseña de aplicación
3. Usa la contraseña de aplicación, no tu contraseña normal

### No detecta juegos nuevos
1. Puede que no haya juegos nuevos ese día
2. Epic Games puede haber cambiado su estructura
3. Revisa los logs para más detalles

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si encuentras bugs o tienes ideas de mejora:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Haz commit de tus cambios
4. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto. Úsalo libremente para tus propios proyectos.

## ⚠️ Disclaimer

Este proyecto es para uso educativo y personal. No está afiliado con Epic Games. Respeta los términos de servicio de Epic Games Store.
