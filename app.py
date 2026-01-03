import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from config.news_sources import CHILEAN_SOURCES, INTERNATIONAL_SOURCES, GOOGLE_NEWS_CATEGORIES
from modules.free_news_aggregator import FreeNewsAggregator
from modules.deepseek_analyzer import DeepSeekAnalyzer
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# Configuración de email
EMAIL_SENDER = st.secrets.get("email_sender", "")
EMAIL_PASSWORD = st.secrets.get("email_password", "")

# Configuración de página
st.set_page_config(
    page_title="Monitor de Noticias Chile",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main {padding: 0rem 1rem;}
    .search-box {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .stAlert {padding: 0.5rem;}
    </style>
    """, unsafe_allow_html=True)

# Inicializar componentes
@st.cache_resource
def init_components():
    all_sources = {**CHILEAN_SOURCES, **INTERNATIONAL_SOURCES}
    aggregator = FreeNewsAggregator()
    analyzer = DeepSeekAnalyzer()
    return aggregator, analyzer, all_sources

aggregator, analyzer, all_sources = init_components()

# Session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

if 'current_results' not in st.session_state:
    st.session_state.current_results = pd.DataFrame()

# Sidebar
st.sidebar.title("🔍 Monitor de Noticias")
st.sidebar.markdown("---")

# Historial
st.sidebar.subheader("📚 Historial")
if st.session_state.search_history:
    for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
        if st.sidebar.button(
            f"🔄 {search['keyword']} ({search['count']} noticias)", 
            key=f"history_{i}"
        ):
            st.session_state.current_keyword = search['keyword']
            st.rerun()

# Configuración
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Configuración")

days_back = st.sidebar.slider(
    "Días hacia atrás",
    min_value=1,
    max_value=30,
    value=7
)

categories_filter = st.sidebar.multiselect(
    "Categorías",
    ["nacional", "economia", "regional", "global"],
    default=["nacional", "economia", "regional"]
)

use_google_news = st.sidebar.checkbox(
    "Incluir Google News",
    value=True,
    help="Amplía la búsqueda usando Google News RSS (gratis)"
)

use_bing_news = st.sidebar.checkbox(
    "Incluir Bing News",
    value=False,
    help="Agrega resultados de Bing News RSS (gratis)"
)

min_matches = st.sidebar.number_input(
    "Mínimo de menciones",
    min_value=1,
    max_value=10,
    value=1
)

# Header
st.title("🔍 Monitor de Noticias Chile")
st.markdown("**Busca términos específicos en medios chilenos e internacionales**")

# Caja de búsqueda
with st.container():
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        keyword = st.text_input(
            "**Ingresa el término a buscar:**",
            placeholder="Ej: reforma tributaria, sequía, Gabriel Boric...",
            key="keyword_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button("🔎 Buscar", type="primary", use_container_width=True)
    
    st.markdown("**💡 Sugerencias:** reforma constitucional | inflación | sequía | minería | educación | pensiones")
    st.markdown('</div>', unsafe_allow_html=True)

# Nueva función para análisis de emociones
def analyze_emotion_with_deepseek(text):
    """
    Analiza las emociones de un texto usando DeepSeek API
    """
    try:
        prompt = f"""Analiza las emociones del siguiente texto y responde SOLO con UNA palabra de estas opciones: RISA, IRA, MIEDO, TRISTEZA, DISGUSTO, SORPRESA, NEUTRAL.

Texto: {text[:500]}

Emoción:"""

        response = analyzer.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Eres un experto en análisis de emociones. Responde siempre con una sola palabra en mayúsculas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        emotion = response.choices[0].message.content.strip().upper()
        valid_emotions = ["RISA", "IRA", "MIEDO", "TRISTEZA", "DISGUSTO", "SORPRESA", "NEUTRAL"]
        if emotion in valid_emotions:
            return emotion
        else:
            return 'NEUTRAL'
    except Exception as e:
        print(f"Error en análisis de emociones: {e}")
        return 'DESCONOCIDO'

# Nueva función para generar resumen
def generate_analysis_summary(df, keyword):
    """
    Genera un resumen consolidado
    """
    if df.empty:
        return "No hay datos para generar el resumen."
    
    summary_parts = []
    summary_parts.append(f"📊 RESUMEN DE ANÁLISIS: '{keyword}'")
    summary_parts.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    summary_parts.append(f"Total de noticias analizadas: {len(df)}\n")
    
    if 'sentiment' in df.columns:
        sentiment_counts = df['sentiment'].value_counts()
        summary_parts.append("🎭 ANÁLISIS DE SENTIMIENTOS:")
        for sentiment, count in sentiment_counts.items():
            percentage = (count / len(df)) * 100
            summary_parts.append(f"  • {sentiment}: {count} ({percentage:.1f}%)")
        summary_parts.append("")
    
    if 'emotion' in df.columns:
        emotion_counts = df['emotion'].value_counts()
        summary_parts.append("😊 ANÁLISIS DE EMOCIONES:")
        for emotion, count in emotion_counts.items():
            percentage = (count / len(df)) * 100
            summary_parts.append(f"  • {emotion}: {count} ({percentage:.1f}%)")
        summary_parts.append("")
    
    summary_parts.append("📰 DETALLE DE NOTICIAS:\n")
    
    for idx, row in df.iterrows():
        title = row.get('title', 'Sin título')
        source = row.get('source', 'Fuente desconocida')
        link = row.get('link', 'Sin enlace')
        sentiment = row.get('sentiment', 'N/A')
        emotion = row.get('emotion', 'N/A')
        
        summary_parts.append(f"{'='*80}")
        summary_parts.append(f"Noticia #{idx + 1}")
        summary_parts.append(f"Titular: {title}")
        summary_parts.append(f"Medio: {source}")
        summary_parts.append(f"Sentimiento: {sentiment}")
        summary_parts.append(f"Emoción: {emotion}")
        summary_parts.append(f"Link: {link}")
        summary_parts.append("")
    
    return "\n".join(summary_parts)

# Nueva función para enviar email
def send_email_summary(recipient_email, subject, summary_content):
    """
    Envía el resumen por email
    """
    try:
        message = MIMEMultipart()
        message["From"] = EMAIL_SENDER
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(summary_content, "plain", "utf-8"))
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipient_email, message.as_string())
        server.quit()
        
        return True, "Email enviado exitosamente ✅"
    except Exception as e:
        return False, f"Error al enviar email: {str(e)}"

# Función de búsqueda MODIFICADA
def perform_search(keyword_to_search, days, categories, use_google, use_bing):
    with st.spinner(f"🔍 Buscando '{keyword_to_search}' en múltiples fuentes..."):
        
        # Filtrar fuentes
        filtered_sources = {cat: sources for cat, sources in all_sources.items() if cat in categories}
        
        # Realizar búsqueda
        df = aggregator.aggregate_all_free(
            keyword_to_search, 
            filtered_sources,
            use_google_news=use_google,
            use_bing_news=use_bing
        )
        
        if df.empty:
            return df
        
        # Filtrar por menciones mínimas
        if 'keyword_matches' in df.columns:
            df = df[df['keyword_matches'] >= min_matches]
        
        if df.empty:
            return df
        
        # Análisis de sentimiento y emociones
        with st.spinner("Analizando sentimientos y emociones..."):
            sentiments = []
            emotions = []
            
            if len(df) > 0:
                progress_bar = st.progress(0)
                for idx, row in df.iterrows():
                    text = f"{row['title']} {row.get('summary', '')}"
                    
                    # Análisis de sentimiento
                    sentiment_result = analyzer.analyze_sentiment(text)
                    sentiments.append(sentiment_result['sentiment'])
                    
                    # Análisis de emociones
                    emotion = analyze_emotion_with_deepseek(text)
                    emotions.append(emotion)
                    
                    progress_bar.progress((idx + 1) / len(df))
                
                df['sentiment'] = sentiments
                df['emotion'] = emotions
                progress_bar.empty()
            else:
                df['sentiment'] = []
                df['emotion'] = []

        # Resúmenes con IA (primeros 5)
        with st.spinner("Generando resúmenes con IA..."):
            df['summary_ai'] = df.get('summary', '')
            if len(df) > 0:
                for idx in range(min(5, len(df))):
                    row = df.iloc[idx]
                    summary = analyzer.summarize_article(row['title'], row.get('summary', ''))
                    df.at[df.index[idx], 'summary_ai'] = summary
        
        return df

# Ejecutar búsqueda
if search_button and keyword:
    st.session_state.current_results = perform_search(
        keyword, 
        days_back, 
        categories_filter,
        use_google_news,
        use_bing_news
    )
    st.session_state.current_keyword = keyword
    
    # Guardar en historial
    if not st.session_state.current_results.empty:
        st.session_state.search_history.append({
            'keyword': keyword,
            'count': len(st.session_state.current_results),
            'timestamp': datetime.now()
        })

# Mostrar resultados
df = st.session_state.current_results
if not df.empty and 'current_keyword' in st.session_state:
    keyword_searched = st.session_state.current_keyword
    
    st.markdown("---")
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📰 Noticias", len(df))
    with col2:
        st.metric("📡 Fuentes", df['source'].nunique())
    with col3:
        total_mentions = int(df['keyword_matches'].sum()) if 'keyword_matches' in df.columns else len(df)
        st.metric("📊 Menciones", total_mentions)
    with col4:
        avg_mentions = df['keyword_matches'].mean() if 'keyword_matches' in df.columns else 1.0
        st.metric("📈 Promedio", f"{avg_mentions:.1f}")
    
    # Análisis de Crisis
    st.markdown("---")
    st.header(f"🚨 Análisis de Riesgo: '{keyword_searched}'")
    
    crisis_data = analyzer.detect_crisis_signals(df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        color_map = {"BAJO": "🟢", "MEDIO": "🟡", "ALTO": "🟠", "CRÍTICO": "🔴"}
        st.metric("Nivel", f"{color_map.get(crisis_data['risk_level'], '⚪')} {crisis_data['risk_level']}")
    with col2:
        st.metric("Score", f"{crisis_data.get('score', 0):.1f}%")
    with col3:
        negative_pct = (crisis_data.get('negative_news', 0) / len(df) * 100) if len(df) > 0 else 0
        st.metric("% Negativas", f"{negative_pct:.1f}%")
    with col4:
        positive_count = len(df[df['sentiment'] == 'POSITIVO'])
        st.metric("Positivas", positive_count)
    
    if crisis_data.get('analysis'):
        st.info(f"**💡 Análisis:** {crisis_data['analysis']}")
    
    # Visualizaciones
       # Visualizaciones
    st.markdown("---")
    st.header("📊 Análisis de Cobertura")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución de Sentimiento")
        sentiment_counts = df['sentiment'].value_counts()
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            color=sentiment_counts.index,
            color_discrete_map={
                'POSITIVO': '#00CC96', 
                'NEUTRAL': '#636EFA', 
                'NEGATIVO': '#EF553B'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Medios")
        source_counts = df['source'].value_counts().head(10)
        fig = px.bar(
            x=source_counts.values,
            y=source_counts.index,
            orientation='h',
            labels={'x': 'Cantidad', 'y': 'Medio'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
      
    # AGREGAR ESTE BLOQUE AQUÍ - Gráfico de Emociones
    st.subheader("😊 Distribución de Emociones")
    if 'emotion' in df.columns:
        emotion_counts = df['emotion'].value_counts()
        
        # Usar colores específicos para cada emoción
        emotion_colors = {
            'RISA': '#FFD700',
            'IRA': '#FF4500',
            'MIEDO': '#8B008B',
            'TRISTEZA': '#4169E1',
            'DISGUSTO': '#228B22',
            'SORPRESA': '#FF69B4',
            'NEUTRAL': '#808080',
            'DESCONOCIDO': '#A9A9A9'
        }
        
        colors = [emotion_colors.get(emotion, '#636EFA') for emotion in emotion_counts.index]
        
        fig = px.bar(
            x=emotion_counts.values,
            y=emotion_counts.index,
            orientation='h',
            labels={'x': 'Cantidad', 'y': 'Emoción'},
            title="Emociones Detectadas en las Noticias"
        )
        fig.update_traces(marker_color=colors)
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos de emociones disponibles")
    
    # Timeline (continúa con el código que ya tienes)
    st.subheader("📅 Evolución Temporal")
    df['date'] = pd.to_datetime(df['published'], errors='coerce')
    st.markdown("---")
    st.header("📊 Análisis de Cobertura")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución de Sentimiento")
        sentiment_counts = df['sentiment'].value_counts()
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            color=sentiment_counts.index,
            color_discrete_map={
                'POSITIVO': '#00CC96', 
                'NEUTRAL': '#636EFA', 
                'NEGATIVO': '#EF553B'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Medios")
        source_counts = df['source'].value_counts().head(10)
        fig = px.bar(
            x=source_counts.values,
            y=source_counts.index,
            orientation='h',
            labels={'x': 'Cantidad', 'y': 'Medio'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        # Nueva visualización de emociones (DEBE ESTAR DESPUÉS DEL GRÁFICO DE TOP MEDIOS)
    if 'emotion' in df.columns:
        st.subheader("😊 Distribución de Emociones")
        emotion_counts = df['emotion'].value_counts()
        fig = px.bar(
            x=emotion_counts.values,
            y=emotion_counts.index,
            orientation='h',
            labels={'x': 'Cantidad', 'y': 'Emoción'},
            color=emotion_counts.values,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Timeline
    st.subheader("📅 Evolución Temporal")
    df['date'] = pd.to_datetime(df['published'], errors='coerce')
    df['date_only'] = df['date'].dt.date
    
    if df['date_only'].notna().any():
        timeline = df.groupby(['date_only', 'sentiment']).size().unstack(fill_value=0)
        
        fig = go.Figure()
        color_map = {'POSITIVO': '#00CC96', 'NEUTRAL': '#636EFA', 'NEGATIVO': '#EF553B'}
        for sentiment in timeline.columns:
            fig.add_trace(go.Scatter(
                x=timeline.index,
                y=timeline[sentiment],
                name=sentiment,
                mode='lines+markers',
                line=dict(color=color_map.get(sentiment, '#636EFA'))
            ))
        fig.update_layout(xaxis_title="Fecha", yaxis_title="Cantidad")
        st.plotly_chart(fig, use_container_width=True)
    
    # Lista de noticias
    st.markdown("---")
    st.header(f"📋 Noticias sobre '{keyword_searched}'")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        sentiment_filter = st.multiselect(
            "Sentimiento",
            ["POSITIVO", "NEGATIVO", "NEUTRAL"],
            default=["POSITIVO", "NEGATIVO", "NEUTRAL"]
        )
    with col2:
        sources_available = df['source'].unique().tolist()
        sources_filter = st.multiselect(
            "Medio",
            sources_available,
            default=sources_available[:10] if len(sources_available) > 10 else sources_available
        )
    with col3:
        sort_by = st.selectbox(
            "Ordenar por",
            ["Fecha (reciente)", "Menciones (mayor)", "Relevancia"]
        )
    
    # Aplicar filtros
    filtered_df = df[
        (df['sentiment'].isin(sentiment_filter)) &
        (df['source'].isin(sources_filter))
    ]
    
    if sort_by == "Fecha (reciente)":
        filtered_df = filtered_df.sort_values('date', ascending=False)
    elif sort_by == "Menciones (mayor)":
        if 'keyword_matches' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('keyword_matches', ascending=False)
    else:
        if 'relevance_score' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('relevance_score', ascending=False)
    
    st.markdown(f"**Mostrando {len(filtered_df)} de {len(df)} noticias**")
    
    # Mostrar noticias
    for idx, row in filtered_df.head(50).iterrows():
        sentiment_emoji = {"POSITIVO": "😊", "NEGATIVO": "😟", "NEUTRAL": "😐"}
        emotion_emoji = {"RISA": "😂", "IRA": "😠", "MIEDO": "😨", "TRISTEZA": "😢", 
                        "DISGUSTO": "🤢", "SORPRESA": "😲", "NEUTRAL": "😐"}
        
        title_display = row['title'].replace(keyword_searched, f"**{keyword_searched}**")
        
        matches_info = ""
        if 'keyword_matches' in row and row['keyword_matches'] > 0:
            matches_info = f" | {int(row['keyword_matches'])} menciones"
        
        emotion_info = ""
        if 'emotion' in row:
            emotion_info = f" | {emotion_emoji.get(row['emotion'], '😐')} {row['emotion']}"
        
        with st.expander(
            f"{sentiment_emoji.get(row['sentiment'], '📰')} {row['source']} | "
            f"{row['sentiment']}{emotion_info}{matches_info}"
        ):
            st.markdown(f"### {title_display}")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if row.get('summary'):
                    st.markdown("**Resumen:**")
                    summary_display = row['summary'].replace(keyword_searched, f"**{keyword_searched}**")
                    st.markdown(summary_display)
                
                if row.get('summary_ai') and row['summary_ai'] != row.get('summary'):
                    st.markdown("**Análisis IA:**")
                    st.info(row['summary_ai'])
                
                st.markdown(f"🔗 [Leer noticia completa]({row['link']})")
            
            with col2:
                st.metric("Sentimiento", row['sentiment'])
                if 'emotion' in row:
                    st.metric("Emoción", row['emotion'])
                if 'keyword_matches' in row:
                    st.metric("Menciones", int(row['keyword_matches']))
                if pd.notna(row.get('date')):
                    st.caption(f"📅 {row['date'].strftime('%Y-%m-%d %H:%M')}")
                if 'category' in row:
                    st.caption(f"🏷️ {row['category']}")
    
    # Sección de Resumen y Email
       # Exportar y Resumen
    st.markdown("---")
    st.header("📊 Resumen y Exportación")
    
    # Botón para generar resumen
    if st.button("📋 Generar Resumen Consolidado", type="primary", use_container_width=True):
        summary_text = generate_analysis_summary(df, keyword_searched)
        st.session_state.summary_text = summary_text
        
        with st.expander("📊 Ver Resumen Completo", expanded=True):
            st.text(summary_text)
    
    # Botones de descarga
    col1, col2 = st.columns(2)
    with col1:
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"noticias_{keyword_searched}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        if hasattr(st.session_state, 'summary_text'):
            st.download_button(
                label="⬇️ Descargar Resumen",
                data=st.session_state.summary_text,
                file_name=f"resumen_{keyword_searched}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # Sección de envío por email
    if hasattr(st.session_state, 'summary_text'):
        st.markdown("---")
        st.subheader("📧 Enviar Resumen por Email")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            recipient_email = st.text_input(
                "Email del destinatario:",
                placeholder="ejemplo@email.com",
                key="recipient_email_input"
            )
        with col2:
            st.write("")
            st.write("")
            send_button = st.button("📤 Enviar Email", type="primary", use_container_width=True)
        
        if send_button:
            if not recipient_email:
                st.error("❌ Por favor ingresa un email válido")
            elif not EMAIL_SENDER or not EMAIL_PASSWORD:
                st.error("❌ Configura las credenciales de email en secrets")
                st.info("💡 Crea un archivo .streamlit/secrets.toml con:\nemail_sender = \"tu_email@gmail.com\"\nemail_password = \"tu_app_password\"")
            else:
                with st.spinner("Enviando email..."):
                    subject = f"Resumen de Análisis de Noticias: {keyword_searched}"
                    success, message = send_email_summary(
                        recipient_email,
                        subject,
                        st.session_state.summary_text
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)

elif keyword and search_button:
    st.warning(f"⚠️ No se encontraron noticias para '{keyword}'")
    st.info("💡 Intenta con términos más generales o amplía el rango de días")

else:
    st.info("👆 Ingresa un término en el buscador para comenzar")
    
    st.markdown("---")
    st.subheader("📚 Ejemplos de Búsquedas")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🏛️ Política**")
        st.markdown("- Gabriel Boric\n- Congreso\n- Constitución")
    with col2:
        st.markdown("**💰 Economía**")
        st.markdown("- Inflación\n- Banco Central\n- Pensiones")
    with col3:
        st.markdown("**🌍 Social**")
        st.markdown("- Sequía\n- Educación\n- Salud")

# Footer
st.markdown("---")
st.caption(
    f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Powered by DeepSeek AI | 100% Gratuito"
)

