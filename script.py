import streamlit as st
import requests
import pandas as pd
import time
import io

# ---------------------------- CONFIGURAÇÕES ----------------------------
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

# ---------------------------- FUNÇÕES ----------------------------
def obter_detalhes(place_id: str, api_key: str) -> dict:
    """🔸 NOVO: busca telefone e site via Place Details API."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,international_phone_number,website",
        "key": api_key
    }
    r = requests.get(url, params=params)
    d = r.json()
    if d.get("status") != "OK":
        return {"telefone": None, "site": None}
    result = d.get("result", {})
    telefone = (
        result.get("international_phone_number")
        or result.get("formatted_phone_number")
    )
    site = result.get("website")
    return {"telefone": telefone, "site": site}


def buscar_locais(municipio: str, place_type: str, api_key: str) -> list:
    """Faz Text Search e depois obtém detalhes de cada place_id."""
    query = f"{place_type} em {municipio}"
    url_base = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    resultados = []
    params = {"query": query, "key": api_key}

    while True:
        data = requests.get(url_base, params=params).json()

        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            st.error(f"Erro na requisição: {data.get('status')} - {data.get('error_message')}")
            break

        for result in data.get("results", []):
            place_id = result.get("place_id", "")
            detalhes = obter_detalhes(place_id, api_key)  # 🔹 ALTERADO
            resultados.append(
                {
                    "municipio": municipio,
                    "nome": result.get("name", ""),
                    "endereco": result.get("formatted_address", ""),
                    "rating": result.get("rating"),
                    "categoria": place_type,
                    "telefone": detalhes["telefone"],  # 🔸 NOVO
                    "site": detalhes["site"],          # 🔸 NOVO
                    "link_google_maps": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                }
            )

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break
        time.sleep(2)  # espera o token ativar
        params = {"pagetoken": next_page_token, "key": api_key}

    return resultados

# ---------------------------- INTERFACE STREAMLIT ----------------------------
st.title("Buscador de Locais no Google Maps")
st.markdown("Insira sua Google API Key, os municípios, o nome e selecione os tipos de locais que deseja buscar.")

api_key = st.text_input("Google API Key")
municipios_input = st.text_input("Municípios (separados por vírgula)", placeholder="Ex: São Paulo, Rio de Janeiro")
executivo_comercial = st.text_input("Nome de quem está buscando")
tipos_selecionados = st.multiselect(
    "Selecione os tipos de locais (se vazio, usaremos todos)", options=TIPOS, default=TIPOS
)

if st.button("Buscar"):
    if not api_key or not municipios_input:
        st.error("Por favor, preencha os campos obrigatórios (Google API Key e Municípios).")
    else:
        municipios = [m.strip() for m in municipios_input.split(",") if m.strip()]
        colunas = [
            "municipio",
            "nome",
            "endereco",
            "rating",
            "categoria",
            "telefone",           # 🔸 NOVO
            "site",               # 🔸 NOVO
            "link_google_maps",
        ]
        df_final = pd.DataFrame(columns=colunas)

        with st.spinner("Realizando buscas..."):
            for municipio in municipios:
                for tipo in tipos_selecionados:
                    st.write(f"Buscando '{tipo}' em {municipio}...")
                    locais = buscar_locais(municipio, tipo, api_key)
                    df_final = pd.concat([df_final, pd.DataFrame(locais)], ignore_index=True)

        st.success("Busca concluída!")
        st.write("Resultados:", df_final)

        # Exporta para Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_final.to_excel(writer, index=False, sheet_name="Resultados")
        output.seek(0)

        st.download_button(
            label="Baixar Excel",
            data=output,
            file_name=f"resultado_{executivo_comercial}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
