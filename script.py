import streamlit as st
import requests
import pandas as pd
import time
import io

# Define the full list of place types
TIPOS = [
    "accounting", "airport", "amusement_park", "aquarium", "art_gallery",
    "atm", "bakery", "bank", "bar", "beauty_salon", "bicycle_store", "book_store",
    "bowling_alley", "bus_station", "cafe", "campground", "car_dealer", "car_rental",
    "car_repair", "car_wash", "casino", "cemetery", "church", "city_hall",
    "clothing_store", "convenience_store", "courthouse", "dentist", "department_store",
    "doctor", "drugstore", "electrician", "electronics_store", "embassy", "establishment",
    "finance", "fire_station", "florist", "food", "funeral_home", "furniture_store",
    "gas_station", "gym", "hair_care", "hardware_store", "health", "hindu_temple",
    "home_goods_store", "hospital", "insurance_agency", "jewelry_store", "laundry",
    "lawyer", "library", "liquor_store", "local_government_office", "locksmith",
    "lodging", "meal_delivery", "meal_takeaway", "mosque", "movie_rental", "movie_theater",
    "moving_company", "museum", "night_club", "painter", "park", "parking", "pet_store",
    "pharmacy", "physiotherapist", "plumber", "police", "post_office", "real_estate_agency",
    "restaurant", "roofing_contractor", "rv_park", "school", "shoe_store", "shopping_mall",
    "spa", "stadium", "storage", "store", "subway_station", "supermarket", "synagogue",
    "taxi_stand", "tourist_attraction", "train_station", "transit_station", "travel_agency",
    "university", "veterinary_care", "zoo"
]

# Function to perform a search via Google Places Text Search API
def buscar_locais(municipio, place_type, api_key):
    query = f"{place_type} em {municipio}"
    url_base = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    resultados = []
    params = {
        "query": query,
        "key": api_key
    }
    
    while True:
        response = requests.get(url_base, params=params)
        data = response.json()
        
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            st.error(f"Erro na requisição: {data.get('status')} - {data.get('error_message')}")
            break
        
        for result in data.get("results", []):
            place_id = result.get("place_id", "")
            nome = result.get("name", "")
            endereco = result.get("formatted_address", "")
            rating = result.get("rating", None)
            link_maps = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            
            resultados.append({
                "municipio": municipio,
                "nome": nome,
                "endereco": endereco,
                "rating": rating,
                "categoria": place_type,
                "link_google_maps": link_maps
            })
        
        next_page_token = data.get("next_page_token")
        if next_page_token:
            time.sleep(2)  # Wait for token activation
            params = {
                "pagetoken": next_page_token,
                "key": api_key
            }
        else:
            break
    
    return resultados

# Streamlit UI
st.title("Buscador de Locais no Google Maps")
st.markdown("Insira sua Google API Key, os municípios, o nome do executivo e selecione os tipos de locais que deseja buscar.")

# Inputs
api_key = st.text_input("Google API Key", type="password")
municipios_input = st.text_input("Municípios (separados por vírgula)", placeholder="Ex: São Paulo, Rio de Janeiro")
executivo_comercial = st.text_input("Nome de quem está buscando")
tipos_selecionados = st.multiselect("Selecione os tipos de locais (se vazio, usaremos todos)", options=TIPOS, default=TIPOS)

if st.button("Buscar"):
    if not api_key or not municipios_input:
        st.error("Por favor, preencha os campos obrigatórios (Google API Key e Municípios).")
    else:
        municipios = [m.strip() for m in municipios_input.split(",") if m.strip()]
        df_final = pd.DataFrame(columns=["municipio", "nome", "endereco", "rating", "categoria", "link_google_maps"])
        
        with st.spinner("Realizando buscas..."):
            for municipio in municipios:
                for tipo in tipos_selecionados:
                    st.write(f"Buscando '{tipo}' em {municipio}...")
                    locais = buscar_locais(municipio, tipo, api_key)
                    df_temp = pd.DataFrame(locais)
                    df_final = pd.concat([df_final, df_temp], ignore_index=True)
        
        st.success("Busca concluída!")
        st.write("Resultados:", df_final)
        
        # Convert DataFrame to Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_final.to_excel(writer, index=False, sheet_name="Resultados")
        output.seek(0)
        
        st.download_button(
            label="Baixar Excel",
            data=output,
            file_name=f"resultado_{executivo_comercial}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
