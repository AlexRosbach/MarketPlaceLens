

<div align="center">

<img src="app/static/assets/marketplacelens-logo.png" alt="MarketPlaceLens logo" width="96" height="96">

# MarketPlaceLens

**Monitor de mercados autoalojado para Kleinanzeigen y otras búsquedas públicas de mercados.**

[![Version](https://img.shields.io/badge/version-0.4.1-24745a)](https://github.com/AlexRosbach/MarketPlaceLens)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)
[![Docker Hub](https://img.shields.io/docker/pulls/alexrosbach/marketplacelens?color=0ea5e9)](https://hub.docker.com/r/alexrosbach/marketplacelens)

MarketPlaceLens ejecuta trabajos de búsqueda recurrentes en mercados, recopila anuncios coincidentes y te proporciona un panel local para revisar, ocultar, guardar, contactar y supervisar artículos interesantes.

[Documentación](docs/documentation.md) · [Borrador de wiki](docs/wiki/Home.md) · [Registro de cambios](CHANGELOG.md) · [Docker Hub](https://hub.docker.com/r/alexrosbach/marketplacelens)

</div>

## Por qué es diferente

La mayoría de los proveedores de mercados están optimizados para navegar dentro de una sola plataforma. MarketPlaceLens está diseñado para investigación de compras enfocada a través de búsquedas guardadas:

- Control de búsqueda más granular: combina URLs de búsqueda del proveedor con filtros locales de incluir, excluir, palabras clave obligatorias, categoría, precio, antigüedad, ubicación, radio, estado y listas de seguimiento.
- Flujo de trabajo de coincidencias mejorado: normaliza los anuncios en una sola cola de revisión local, oculta el ruido, conserva los artículos contactados y guarda los elementos prometedores en listas de seguimiento en lugar de repetir las mismas búsquedas del proveedor.
- Asistencia con IA integrada: convierte la intención de compra en lenguaje natural en borradores de trabajos rápidos, genera mensajes para compradores y añade evaluaciones de anuncios que destacan la adecuación, la viabilidad del precio, los detalles faltantes y los signos de riesgo visibles.
- Propiedad autoalojada: los datos, la configuración, las cookies, las claves API, las listas de seguimiento y el historial de revisiones se mantienen en el servidor del operador.
- Sin dependencia de una sola interfaz de mercado: las fuentes compatibles pueden evolucionar de forma independiente mientras el flujo de trabajo de revisión, notificación e IA se mantiene igual.

## Soporte y Aspectos Legales

MarketPlaceLens es gratuito y de código abierto. Si te ayuda o te ahorra tiempo, puedes apoyar el desarrollo continuo de forma voluntaria. El apoyo no concede prioridad en el soporte, funciones ni acceso.

<a href="https://www.buymeacoffee.com/alexrosbaci" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me a Coffee" height="42"></a>

MarketPlaceLens es una aplicación de Alex Rosbach. La información legal y de contacto del proyecto se mantiene en [lanlens.org/privacy.html](https://lanlens.org/privacy.html).

## Estado

| Fuente | Estado | Notas |
|---|---|---|
| Kleinanzeigen | Estable | Conector principal soportado para URLs públicas de búsqueda/categoría |
| Facebook Marketplace | **En pruebas** | A menudo devuelve páginas de inicio de sesión, consentimiento, ubicación o solo JavaScript |
| mobile.de | **En pruebas** | El soporte de HTML público es limitado; el acceso a la API oficial es independiente |
| HTML genérico | Experimental | Analizador básico para páginas de resultados simples |

## Capturas de pantalla

Datos de demostración, no hay anuncios reales.

| Panel | Trabajos |
|---|---|
| ![Panel](docs/screenshots/marketplacelens-dashboard.png) | ![Trabajos](docs/screenshots/marketplacelens-jobs.png) |

| Anuncios | Revisión en móvil |
|---|---|
| ![Anuncios](docs/screenshots/marketplacelens-listings.png) | ![Revisión en móvil](docs/screenshots/marketplacelens-mobile-review.png) |

## Características

- Trabajos de búsqueda recurrentes en mercados con filtros de precio, palabras clave, antigüedad, tipo de anuncio, código postal/lugar y radio
- Navegador de anuncios, revisión deslizable, listas de seguimiento, estados de visto/ocultado/contactado
- Marcar un anuncio como contactado lo guarda automáticamente en la lista de seguimiento predeterminada del usuario
- Acción de mapa de código postal/lugar con enlace para las ubicaciones de los anuncios
- Notificaciones opcionales por Telegram y webhooks
- Texto de comprador con IA, borradores de trabajos rápidos y evaluaciones de anuncios opcionales
- Inicio de sesión multiusuario con configuración de administrador y trabajos propiedad del usuario
- Interfaz en alemán/inglés, modo oscuro/claro y diseños para móvil
- La validación defensiva de URLs evita que los trabajos guardados y las solicitudes del proxy de imágenes apunten a hosts de redes locales o privadas

## Inicio rápido

```bash
mkdir -p marketplacelens && cd marketplacelens
curl -fsSL https://raw.githubusercontent.com/AlexRosbach/MarketPlaceLens/main/docker-compose.install.yml -o docker-compose.yml
docker compose up -d
```

Abrir:

```text
http://<your-host-ip>:8091
```

En el primer inicio, MarketPlaceLens te pedirá que crees la primera cuenta de administrador.

## Imágenes de Docker

```bash
docker pull alexrosbach/marketplacelens:0.4.1
docker pull alexrosbach/marketplacelens:latest
docker pull alexrosbach/marketplacelens:dev
```

- `0.4.1` es la versión actual
- `latest` sigue la última versión estable
- `dev` sigue la versión de desarrollo actual

## Documentación

- [Documentación completa](docs/documentation.md)
- [Borrador de wiki](docs/wiki/Home.md)
- [Instalación](docs/wiki/Installation.md)
- [Trabajos y fuentes](docs/wiki/Jobs-and-Sources.md)
- [Anuncios y listas de seguimiento](docs/wiki/Listings-and-Watchlists.md)
- [IA y automatización](docs/wiki/AI-and-Automation.md)
- [Solución de problemas](docs/wiki/Troubleshooting.md)

## Uso Responsable

MarketPlaceLens está diseñado para un uso privado autoalojado con URLs de mercados a los que tienes permiso para acceder. No elude inicios de sesión, CAPTCHAs, protecciones contra bots, APIs privadas, límites de tasa ni controles de acceso de la plataforma.

## Licencia

Licencia MIT, consulta [LICENSE](LICENSE).
