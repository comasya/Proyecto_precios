import google.generativeai as genai
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup # type: ignore

# Configura la API de Gemini con tu clave (debe estar en secrets.toml)
genai.configure(api_key=st.secrets["API_KEY_GEMINI"])

def obtener_respuesta_gemini(prompt):
    """Obtiene una respuesta de la API de Gemini."""
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.candidates[0].text if response.candidates else "No se obtuvo respuesta."

def obtener_precios_mercado_libre(articulo):
    """Obtiene precios de Mercado Libre para un artículo dado."""
    url = f"https://listado.mercadolibre.com.ar/{articulo}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer precios de Mercado Libre
        precios_elementos = soup.find_all('span', class_='andes-money-amount__fraction')
        precios = []

        for elemento in precios_elementos:
            precio_texto = elemento.text.replace('.', '').strip()
            if precio_texto.isdigit():
                precios.append(int(precio_texto))

        # Obtener el Top 10 de precios más bajos
        return sorted(precios)[:10] if precios else ["No se encontraron precios"]
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener precios de Mercado Libre: {e}")
        return []
    
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
        return []

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

                if precios_mercado_libre and isinstance(precios_mercado_libre[0], int):
                    prompt = generar_prompt(articulo, precios_mercado_libre)
                    respuesta = obtener_respuesta_gemini(prompt)

                    # Mostrar resultados
                    df = pd.DataFrame({"Top 10 Precios": precios_mercado_libre})
                    st.subheader("📊 Precios encontrados")
                    st.dataframe(df)

                    st.subheader("💡 Recomendación de Precios")
                    st.write(respuesta)
                else:
                    st.warning("No se encontraron precios válidos para este artículo.")
        else:
            st.warning("Por favor, ingrese un artículo.")

if __name__ == "__main__":
    main()
