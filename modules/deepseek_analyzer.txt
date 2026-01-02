from openai import OpenAI
import os
from typing import Dict, List
import json

class DeepSeekAnalyzer:
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY no encontrada en variables de entorno")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
    
    def summarize_article(self, title: str, content: str) -> str:
        """Resume un artículo usando DeepSeek"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un periodista experto. Resume noticias en máximo 3 oraciones concisas y objetivas en español."
                    },
                    {
                        "role": "user", 
                        "content": f"Resume:\n\nTítulo: {title}\n\nContenido: {content}"
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error al resumir: {str(e)}"
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analiza el sentimiento de un texto"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un analista de sentimiento. Responde SOLO con una palabra: POSITIVO, NEGATIVO o NEUTRAL"
                    },
                    {
                        "role": "user", 
                        "content": f"Sentimiento del texto:\n{text}"
                    }
                ],
                max_tokens=10,
                temperature=0.1
            )
            sentiment = response.choices[0].message.content.strip().upper()
            
            # Validar respuesta
            if sentiment not in ['POSITIVO', 'NEGATIVO', 'NEUTRAL']:
                sentiment = 'NEUTRAL'
            
            return {"sentiment": sentiment, "confidence": 0.85}
        except Exception as e:
            print(f"Error en análisis de sentimiento: {e}")
            return {"sentiment": "NEUTRAL", "confidence": 0.0}
    
    def find_connections(self, articles: List[Dict]) -> str:
        """Encuentra conexiones temáticas entre noticias"""
        if len(articles) < 2:
            return "No hay suficientes noticias para analizar conexiones"
        
        titles = "\n".join([f"{i+1}. {art['title']}" for i, art in enumerate(articles[:10])])
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un analista que identifica patrones y conexiones temáticas en noticias. Sé conciso."
                    },
                    {
                        "role": "user", 
                        "content": f"Identifica las principales conexiones temáticas entre estas noticias:\n{titles}"
                    }
                ],
                max_tokens=300,
                temperature=0.4
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error al analizar conexiones: {str(e)}"
    
    def detect_crisis_signals(self, df) -> Dict:
        """Detecta señales de posibles crisis"""
        if df.empty:
            return {"risk_level": "BAJO", "score": 0, "analysis": "No hay datos suficientes"}
        
        negative_count = len(df[df['sentiment'] == 'NEGATIVO'])
        total = len(df)
        negative_ratio = negative_count / total if total > 0 else 0
        
        # Análisis contextual con DeepSeek
        recent_headlines = "\n".join(df.head(15)['title'].tolist())
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un analista de riesgos. Evalúa el riesgo de crisis (social/económica/política) basado en titulares. Responde con: BAJO, MEDIO, ALTO o CRÍTICO, seguido de 1-2 oraciones explicando por qué."
                    },
                    {
                        "role": "user", 
                        "content": f"Evalúa el riesgo de crisis:\n\n{recent_headlines}"
                    }
                ],
                max_tokens=150,
                temperature=0.2
            )
            
            analysis = response.choices[0].message.content
            
            # Determinar nivel de riesgo
            if "CRÍTICO" in analysis.upper():
                risk_level = "CRÍTICO"
            elif "ALTO" in analysis.upper():
                risk_level = "ALTO"
            elif "MEDIO" in analysis.upper():
                risk_level = "MEDIO"
            else:
                risk_level = "BAJO"
            
            return {
                "risk_level": risk_level,
                "score": negative_ratio * 100,
                "analysis": analysis,
                "negative_news": negative_count,
                "total_news": total
            }
        except Exception as e:
            print(f"Error en detección de crisis: {e}")
            return {
                "risk_level": "ERROR",
                "score": negative_ratio * 100,
                "analysis": f"Error al analizar: {str(e)}",
                "negative_news": negative_count,
                "total_news": total
            }
