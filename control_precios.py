import google.generativeai as genai
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup

# Configura la API de Gemini con tu clave (debe estar en secrets.toml)
genai.configure(api_key=st.secrets["API_KEY_GEMINI"])

def obtener_respuesta_gemini(prompt):
    """Obtiene una respuesta de la API de Gemini."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.candidates[0].text if response.candidates else "No se obtuvo respuesta."
    except Exception as e:
        st.error(f"Error al inicializar el modelo Gemini: {e}")
        return "No se pudo obtener respuesta debido a un error."

def obtener_precios_mercado_libre(articulo):
    """Obtiene precios de Mercado Libre para un artículo dado."""
    url = f"https://listado.mercadolibre.com.ar/{articulo}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer información de los productos
        productos = soup.find_all('li', class_='ui-search-layout__item')
        resultados = []

        for producto in productos:
            # Extraer el precio
            precio_elemento = producto.find('span', class_='andes-money-amount__fraction')
            precio_texto = precio_elemento.text.replace('.', '').strip() if precio_elemento else None
            precio = int(precio_texto) if precio_texto and precio_texto.isdigit() else None

            # Extraer el nombre del artículo
            nombre_elemento = producto.find('h2', class_='ui-search-item__title')
            nombre = nombre_elemento.text.strip() if nombre_elemento else None

            # Extraer la URL del producto
            url_elemento = producto.find('a', class_='ui-search-item__group__element')
            url = url_elemento['href'] if url_elemento else None

            if precio and nombre and url:
                resultados.append({'nombre': nombre, 'precio': precio, 'url': url})

        # Ordenar por precio y obtener el Top 10
        resultados_ordenados = sorted(resultados, key=lambda x: x['precio'])[:10]
        return resultados_ordenados if resultados_ordenados else ["No se encontraron precios"]
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener precios de Mercado Libre: {e}")
        return None
    
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
        return None

def generar_prompt(articulo, precios_mercado_libre):
    """Genera un prompt para la API de Gemini."""
    precios_str = ", ".join(map(str, precios_mercado_libre))
    return (
        f"El artículo '{articulo}' tiene los siguientes precios en Mercado Libre: {precios_str}.\n"
        "Basado en esta información, proporciona un análisis y recomienda un rango de precios óptimo."
    )

def main():
    """Función principal de la aplicación Streamlit."""
    st.title("🔍 Análisis de Precios en Mercado Libre")

    articulo = st.text_input("Ingrese el nombre del artículo a buscar:", "")

    if st.button("Buscar Precios"):
        if articulo:
            with st.spinner("Buscando precios..."):
                precios_mercado_libre = obtener_precios_mercado_libre(articulo)

                if precios_mercado_libre:
                    if isinstance(precios_mercado_libre[0], int):
                        prompt = generar_prompt(articulo, precios_mercado_libre)
                        respuesta = obtener_respuesta_gemini(prompt)

                        # Mostrar resultados
                        st.subheader("📊 Precios encontrados")
                        for producto in precios_mercado_libre:
                            st.write(f"**Nombre:** {producto['nombre']}")
                            st.write(f"**Precio:** {producto['precio']}")
                            st.write(f"[Ver en Mercado Libre]({producto['url']})")
                            st.write("---")

                        st.subheader("💡 Recomendación de Precios")
                        st.write(respuesta)
                    else:
                        st.warning("No se encontraron precios válidos para este artículo.")
                else:
                    st.warning("No se encontraron precios para este artículo.")
        else:
            st.warning("Por favor, ingrese un artículo.")

if __name__ == "__main__":
    main()
