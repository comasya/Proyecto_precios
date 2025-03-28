import google.generativeai as genai
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup

# Configura la API de Gemini con tu clave
genai.configure(api_key=st.secrets["API_KEY_GEMINI"])

def obtener_precios_mercado_libre(articulo):
    """Obtiene los nombres, precios y URLs de Mercado Libre para un artículo."""
    url = f"https://listado.mercadolibre.com.ar/{articulo.replace(' ', '-')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Depuración: Ver el HTML
        st.write("HTML obtenido:", soup.prettify()[:1000])  # Muestra los primeros 1000 caracteres

        resultados = []
        productos = soup.find_all('li', class_='ui-search-layout__item')  # Ajustado

        for producto in productos:
            nombre_elemento = producto.find('h2', class_='ui-search-item__title')
            precio_elemento = producto.find('span', class_='andes-money-amount__fraction')
            url_elemento = producto.find('a', class_='ui-search-item__group__element')

            # Depuración: Verificar si encuentra los elementos
            st.write("Producto encontrado:", nombre_elemento, precio_elemento)

            if nombre_elemento and precio_elemento:
                nombre = nombre_elemento.text.strip()
                precio_texto = precio_elemento.text.replace('.', '').strip()
                precio = int(precio_texto) if precio_texto.isdigit() else None
                

                if precio:
                    resultados.append({'Nombre': nombre, 'Precio': precio, 'URL': url_producto})

        return sorted(resultados, key=lambda x: x['Precio'])[:10] if resultados else []
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener precios de Mercado Libre: {e}")
        return []
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
        return []

def main():
    """Aplicación principal en Streamlit."""
    st.title("🔍 Comparador de Precios en Mercado Libre")
    articulo = st.text_input("Ingrese el nombre del artículo a buscar:")

    if st.button("🔎 Buscar Precios"):
        if articulo:
            with st.spinner("Buscando precios..."):
                precios_mercado_libre = obtener_precios_mercado_libre(articulo)
                
                # Depuración: Ver resultados
                st.write("Resultados obtenidos:", precios_mercado_libre)

                if precios_mercado_libre:
                    st.subheader("📊 Precios Encontrados")
                    df = pd.DataFrame(precios_mercado_libre)
                    st.table(df)
                else:
                    st.warning("No se encontraron precios para este artículo.")
        else:
            st.warning("Por favor, ingrese un artículo.")

if __name__ == "__main__":
    main()