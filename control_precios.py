import google.generativeai as genai
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
import os

# Configura la API Key desde una variable de entorno
genai.configure(api_key=st.secrets["API_KEY_GEMINI"])

def obtener_precios_mercado_libre(articulo):
    """Obtiene los nombres, precios y URLs de Mercado Libre para un artículo dado."""
    url = f"https://listado.mercadolibre.com.ar/{articulo}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print(response.content)
        soup = BeautifulSoup(response.content, 'html.parser')

        productos = soup.find_all('li', class_='ui-search-layout__item')
        resultados = []

        for producto in productos:
            nombre = producto.find('h2', class_='ui-search-item__title')
            precio = producto.find('span', class_='andes-money-amount__fraction')
            url_elemento = producto.find('a', class_='ui-search-item__group__element')
            
            if nombre and precio and url_elemento:
                nombre_texto = nombre.text.strip()
                precio_texto = precio.text.replace('.', '').strip()
                precio_valor = int(precio_texto) if precio_texto.isdigit() else None
                url_producto = url_elemento['href']
                print(f"Nombre: {nombre_texto}, Precio: {precio_texto}")
                
                if precio_valor:
                    resultados.append({'Nombre': nombre_texto, 'Precio': precio_valor, 'URL': url_producto})

        return sorted(resultados, key=lambda x: x['Precio'])[:10] if resultados else []
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener precios de Mercado Libre: {e}")
        return []

def generar_prompt(articulo, precios):
    """Genera un prompt para la API de Gemini basado en los precios obtenidos."""
    precios_str = ", ".join([f"{p['Nombre']}: ${p['Precio']}" for p in precios])
    return (
        f"""El artículo '{articulo}' tiene los siguientes precios en Mercado Libre: {precios_str}
        Proporciona un análisis de estos precios y recomienda un rango óptimo.""" )

def obtener_respuesta_gemini(prompt):
    """Obtiene una respuesta de la API de Gemini."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.candidates[0].text if response.candidates else "No se obtuvo respuesta."
    except Exception as e:
        st.error(f"Error al obtener respuesta de Gemini: {e}")
        return "No se pudo obtener respuesta debido a un error."

def main():
    """Aplicación principal en Streamlit."""
    st.title("🔍 Comparador de Precios en Mercado Libre")
    articulo = st.text_input("Ingrese el nombre del artículo a buscar:")

    if st.button("🔎 Buscar Precios"):
        if articulo:
            with st.spinner("Buscando precios..."):
                precios_mercado_libre = obtener_precios_mercado_libre(articulo)
                if precios_mercado_libre:
                    st.subheader("📊 Precios Encontrados")
                    df = pd.DataFrame(precios_mercado_libre)
                    st.table(df)

                    # Generar y obtener respuesta de Gemini
                    prompt = generar_prompt(articulo, precios_mercado_libre)
                    respuesta = obtener_respuesta_gemini(prompt)
                    
                    st.subheader("💡 Recomendación de Precios")
                    st.write(respuesta)
                else:
                    st.warning("No se encontraron precios para este artículo.")
        else:
            st.warning("Por favor, ingrese un artículo.")

if __name__ == "__main__":
    main()
