import google.generativeai as genai
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
import os

# Configura la API Key desde una variable de entorno
genai.configure(api_key=st.secrets["API_KEY_GEMINI"])
if not GENAI_API_KEY:
    st.error("Falta la API Key de Gemini. Defínela como una variable de entorno.")
else:
    genai.configure(api_key=GENAI_API_KEY)

def obtener_respuesta_gemini(prompt):
    """Obtiene una respuesta de la API de Gemini."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error al obtener respuesta de Gemini: {e}"

def leer_archivo_excel(ruta_archivo):
    """Lee un archivo Excel y devuelve un DataFrame de pandas."""
    try:
        df = pd.read_excel(ruta_archivo)
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        return None

def obtener_precios_mercado_libre(articulo):
    """Obtiene los 10 primeros precios y nombres de productos de Mercado Libre."""
    url = f"https://listado.mercadolibre.com.ar/{articulo.replace(' ', '-')}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer nombres y precios de los productos
        productos = soup.find_all('div', class_='ui-search-result__content')
        resultados = []

        for producto in productos:
            nombre_elem = producto.find('h2', class_='ui-search-item__title')
            precio_elem = producto.find('span', class_='price-tag-fraction')

            if nombre_elem and precio_elem:
                nombre = nombre_elem.text.strip()
                precio = int(precio_elem.text.replace('.', ''))
                resultados.append((nombre, precio))

        # Devolver los 10 primeros resultados ordenados por precio
        return sorted(resultados, key=lambda x: x[1])[:10]

    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener precios de Mercado Libre: {e}")
        return []
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar los datos de Mercado Libre: {e}")
        return []

def generar_prompt(articulo, precio_actual, precios_mercado_libre):
    """Genera un prompt para la API de Gemini."""
    prompt = f"""
    El artículo "{articulo}" tiene un precio actual de {precio_actual} en nuestra base de datos.
    Aquí están los 10 precios más relevantes de Mercado Libre junto con sus nombres:
    
    {precios_mercado_libre}

    Con base en esta información, ¿cuál sería un precio recomendado para este artículo?
    """
    return prompt

def main():
    """Función principal de la aplicación Streamlit."""
    st.title("Análisis de Precios de Artículos Electrónicos")

    ruta_archivo = st.file_uploader("Cargar archivo Excel", type=["xlsx"])

    if ruta_archivo is not None:
        df = leer_archivo_excel(ruta_archivo)
        if df is not None:
            resultados = []

            for index, row in df.iterrows():
                articulo = row['Artículo']
                precio_actual = row['Precio Actual']
                precios_mercado_libre = obtener_precios_mercado_libre(articulo)

                # Si se obtienen precios, generar el prompt
                if precios_mercado_libre:
                    prompt = generar_prompt(articulo, precio_actual, precios_mercado_libre)
                    respuesta = obtener_respuesta_gemini(prompt)
                else:
                    respuesta = "No se encontraron precios en Mercado Libre."

                resultados.append({
                    'Artículo': articulo,
                    'Precio Actual': precio_actual,
                    'Precios Mercado Libre': precios_mercado_libre,
                    'Rango de Precios Recomendado': respuesta
                })

            st.dataframe(pd.DataFrame(resultados))

if __name__ == "__main__":
    main()
