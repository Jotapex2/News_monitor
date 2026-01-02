# Fuentes chilenas con RSS público
CHILEAN_SOURCES = {
    "nacional": [
        {"name": "Emol", "url": "https://www.emol.com/rss/rss.asp", "type": "rss"},
        {"name": "BioBioChile", "url": "https://www.biobiochile.cl/lista/rss", "type": "rss"},
        {"name": "La Tercera", "url": "https://www.latercera.com/arc/outboundfeeds/rss/", "type": "rss"},
        {"name": "T13", "url": "https://www.t13.cl/rss/rss.xml", "type": "rss"},
        {"name": "Mega", "url": "https://www.meganoticias.cl/rss/portada.xml", "type": "rss"},
        {"name": "CNN Chile", "url": "https://www.cnnchile.com/feed/", "type": "rss"},
        {"name": "La Nación", "url": "https://www.lanacion.cl/feed/", "type": "rss"},
        {"name": "El Mostrador", "url": "https://www.elmostrador.cl/noticias/feed/", "type": "rss"},
        {"name": "CIPER Chile", "url": "https://www.ciperchile.cl/feed/", "type": "rss"},
        {"name": "El Desconcierto", "url": "https://www.eldesconcierto.cl/feed/", "type": "rss"},
    ],
    "economia": [
        {"name": "Diario Financiero", "url": "https://www.df.cl/noticias/site/list/port/rss", "type": "rss"},
        {"name": "Pulso", "url": "https://www.pulso.cl/feed/", "type": "rss"},
    ],
    "regional": [
        {"name": "El Rancagüino", "url": "https://www.elrancaguino.cl/feed", "type": "rss"},
        {"name": "La Discusión", "url": "https://www.ladiscusion.cl/feed", "type": "rss"},
        {"name": "La Estrella Valpo", "url": "https://www.estrellavalpo.cl/feed", "type": "rss"},
        {"name": "El Austral", "url": "https://www.australvaldivia.cl/feed", "type": "rss"},
        {"name": "Diario Atacama", "url": "https://www.diarioatacama.cl/feed", "type": "rss"},
        {"name": "El Clarín", "url": "https://www.elclarin.cl/feed", "type": "rss"},
    ]
}

INTERNATIONAL_SOURCES = {
    "global": [
        {"name": "BBC Mundo", "url": "https://feeds.bbci.co.uk/mundo/rss.xml", "type": "rss"},
        {"name": "CNN Español", "url": "http://rss.cnn.com/rss/cnn_latest.rss", "type": "rss"},
        {"name": "Reuters", "url": "https://www.reutersagency.com/feed/", "type": "rss"},
        {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "type": "rss"},
    ]
}

# Google News feeds por categoría
GOOGLE_NEWS_CATEGORIES = {
    "chile_general": "https://news.google.com/rss/search?q=Chile&hl=es-CL&gl=CL&ceid=CL:es-419",
    "politica": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFZ4ZERBU0FtVnpLQUFQAQ?hl=es-CL&gl=CL&ceid=CL:es-419",
    "economia": "https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNR2RtY0hNekVnSmxjeWdBUAE?hl=es-CL&gl=CL&ceid=CL:es-419",
}
