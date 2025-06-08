import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Epic Games
EPIC_GRAPHQL_URL = "https://store.epicgames.com/graphql"
EPIC_FREE_GAMES_URL = "https://store.epicgames.com/es-ES/free-games"

# Configuración de email
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

# Configuración de APIs externas para relevancia
RAWG_API_KEY = os.getenv("RAWG_API_KEY", "")
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "")

# Configuración de GG.deals API
GGDEALS_API_KEY = os.getenv("GGDEALS_API_KEY", "")
GGDEALS_BASE_URL = "https://api.gg.deals/v1"

# Configuración general
MAX_GAMES_TO_PROCESS = 4
DATABASE_FILE = "last_games.json"

# Headers para requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Query GraphQL para obtener juegos gratuitos
EPIC_FREE_GAMES_QUERY = """
query storefrontDiscover($locale: String!, $country: String!) {
  Storefront {
    discoverLayout(locale: $locale) {
      modules {
        ... on StorefrontFreeGames {
          __typename
          type
          title
        }
        ... on StorefrontCardGroup {
          __typename
          type
          title
          offers {
            namespace
            id
            offer {
              title
              id
              namespace
              description
              keyImages {
                type
                url
              }
              effectiveDate
              expiryDate
              price(country: $country) {
                totalPrice {
                  discountPrice
                  originalPrice
                  currencyCode
                }
              }
              promotions {
                promotionalOffers {
                  promotionalOffers {
                    startDate
                    endDate
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""
