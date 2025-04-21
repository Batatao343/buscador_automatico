import streamlit as st
import requests
import pandas as pd
import time
import io

# ----------------------------------------------------------------------
# 1) Mapeamento inglês → português  (use para exibir e converter)
# ----------------------------------------------------------------------
TIPOS_PT = {
    "accounting": "Contabilidade",
    "airport": "Aeroporto",
    "amusement_park": "Parque de diversões",
    "aquarium": "Aquário",
    "art_gallery": "Galeria de arte",
    "atm": "Caixa eletrônico",
    "bakery": "Padaria",
    "bank": "Banco",
    "bar": "Bar",
    "beauty_salon": "Salão de beleza",
    "bicycle_store": "Loja de bicicletas",
    "book_store": "Livraria",
    "bowling_alley": "Boliche",
    "bus_station": "Estação de ônibus",
    "cafe": "Café",
    "campground": "Camping",
    "car_dealer": "Concessionária",
    "car_rental": "Locadora de veículos",
    "car_repair": "Oficina mecânica",
    "car_wash": "Lava‑jato",
    "casino": "Cassino",
    "cemetery": "Cemitério",
    "church": "Igreja",
    "city_hall": "Prefeitura",
    "clothing_store": "Loja de roupas",
    "convenience_store": "Loja de conveniência",
    "courthouse": "Fórum",
    "dentist": "Dentista",
    "department_store": "Loja de departamentos",
    "doctor": "Médico",
    "drugstore": "Drogaria",
    "electrician": "Eletricista",
    "electronics_store": "Loja de eletrônicos",
    "embassy": "Embaixada",
    "establishment": "Estabelecimento",
    "finance": "Finanças",
    "fire_station": "Corpo de bombeiros",
    "florist": "Floricultura",
    "food": "Alimentação",
    "funeral_home": "Funerária",
    "furniture_store": "Loja de móveis",
    "gas_station": "Posto de gasolina",
    "gym": "Academia",
    "hair_care": "Cabeleireiro",
    "hardware_store": "Loja de ferragens",
    "health": "Saúde",
    "hindu_temple": "Templo hindu",
    "home_goods_store": "Utilidades domésticas",
    "hospital": "Hospital",
    "insurance_agency": "Seguradora",
    "jewelry_store": "Joalheria",
    "laundry": "Lavanderia",
    "lawyer": "Advogado",
    "library": "Biblioteca",
    "liquor_store": "Loja de bebidas",
    "local_government_office": "Órgão público",
    "locksmith": "Chaveiro",
    "lodging": "Hospedagem",
    "meal_delivery": "Entrega de refeição",
    "meal_takeaway": "Comida para viagem",
    "mosque": "Mesquita",
    "movie_rental": "Locadora de filmes",
    "movie_theater": "Cinema",
    "moving_company": "Empresa de mudanças",
    "museum": "Museu",
    "night_club": "Casa noturna",
    "painter": "Pintor",
    "park": "Parque",
    "parking": "Estacionamento",
    "pet_store": "Pet shop",
    "pharmacy": "Farmácia",
    "physiotherapist": "Fisioterapeuta",
    "plumber": "Encanador",
    "police": "Polícia",
    "post_office": "Correios",
    "real_estate_agency": "Imobiliária",
    "restaurant": "Restaurante",
    "roofing_contractor": "Telhadista",
    "rv_park": "Parque de trailers",
    "school": "Escola",
    "shoe_store": "Loja de calçados",
    "shopping_mall": "Shopping",
    "spa": "Spa",
    "stadium": "Estádio",
    "storage": "Depósito",
    "store": "Loja",
    "subway_station": "Estação de metrô",
    "supermarket": "Supermercado",
    "synagogue": "Sinagoga",
    "taxi_stand": "Ponto de táxi",
    "tourist_attraction": "Ponto turístico",
    "train_station": "Estação de trem",
    "transit_station": "Estação de transporte",
    "travel_agency": "Agência de viagens",
    "university": "Universidade",
    "veterinary_care": "Veterinário",
    "zoo": "Zoológico",
}

# ----------------------------------------------------------------------
# 2) Função para pegar telefone e site (igual à versão anterior)
# ----------------------------------------------------------------------
def obter_detalhes(place_id: str, api_key: str) -> dict:
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,international_phone_number,website",
        "key": api_key,
    }
    data = requests.get(url, params=params).json()
    if data.get("status") != "OK":
        return {"telefone": None, "site": None}
    res = data.get("result", {})
    telefone = res.get("international_phone_number") or res.get("formatted_phone_number")
    return {"telefone": telefone, "site": res.get("website")}


def buscar_locais(municipio: str, place_type_en: str, api_key: str) -> list:
    query = f"{place_type_en} em {municipio}"
    base = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    resultados = []
    params = {"query": query, "key": api_key}

    while True:
        data = requests.get(base, params=params).json()
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            st.error(f"Erro: {data.get('status')} - {data.get('error_message')}")
            break

        for r in data.get("results", []):
            detalhes = obter_detalhes(r["place_id"], api_key)
            resultados.append(
                {
                    "municipio": municipio,
                    "nome": r.get("name", ""),
                    "endereco": r.get("formatted_address", ""),
                    "rating": r.get("rating"),
                    "categoria": TIPOS_PT[place_type_en],  # PT no resultado
                    "telefone": detalhes["telefone"],
                    "site": detalhes["site"],
                    "link_google_maps": f"https://www.google.com/maps/place/?q=place_id:{r['place_id']}",
                }
            )

        nxt = data.get("next_page_token")
        if not nxt:
            break
        time.sleep(2)
        params = {"pagetoken": nxt, "key": api_key}

    return resultados


# ----------------------------------------------------------------------
# 3) Interface Streamlit
# ----------------------------------------------------------------------
st.title("Buscador de Locais no Google Maps")

api_key = st.text_input("Google API Key")
municipios_input = st.text_input("Municípios (separados por vírgula)", placeholder="Ex: São Paulo, Rio de Janeiro")
executivo_comercial = st.text_input("Nome de quem está buscando")

# Multiselect sem seleção inicial  👇
opcoes_pt = list(TIPOS_PT.values())
labels_escolhidos = st.multiselect("Selecione os tipos de locais", options=opcoes_pt)

if st.button("Buscar"):
    if not api_key or not municipios_input:
        st.error("Preencha Google API Key e Municípios.")
    elif not labels_escolhidos:
        st.error("Escolha pelo menos uma categoria.")
    else:
        tipos_selecionados_en = [
            en for en, pt in TIPOS_PT.items() if pt in labels_escolhidos
        ]
        municipios = [m.strip() for m in municipios_input.split(",") if m.strip()]
        df = pd.DataFrame(
            columns=["municipio", "nome", "endereco", "rating", "categoria", "telefone", "site", "link_google_maps"]
        )

        with st.spinner("Buscando..."):
            for mun in municipios:
                for tipo_en in tipos_selecionados_en:
                    st.write(f"Buscando '{TIPOS_PT[tipo_en]}' em {mun}...")
                    df = pd.concat(
                        [df, pd.DataFrame(buscar_locais(mun, tipo_en, api_key))],
                        ignore_index=True,
                    )

        st.success("Busca concluída!")
        st.write(df)

        # Exporta Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Resultados")
        buffer.seek(0)

        st.download_button(
            "Baixar Excel",
            data=buffer,
            file_name=f"resultado_{executivo_comercial}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

