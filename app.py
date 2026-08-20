import os
import pandas as pd
import streamlit as st

# 1. Configura a página para se adaptar ao celular e remove margens excessivas
st.set_page_config(page_title="Consulta de Dados", layout="centered")

# CSS nativo para forçar o aplicativo a usar 100% da tela do celular sem barras laterais brancas
st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 1rem; padding-right: 1rem; }
    div[data-testid="stTextInput"] input { font-size: 18px !important; height: 45px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

NOME_ARQUIVO_EXCEL = "Controle corridas NOVO.xlsx"


@st.cache_data(ttl=30)
def carregar_dados_do_excel():
    if not os.path.exists(NOME_ARQUIVO_EXCEL):
        st.error(f"❌ Arquivo '{NOME_ARQUIVO_EXCEL}' não encontrado.")
        return pd.DataFrame()
    try:
        df = pd.read_excel(NOME_ARQUIVO_EXCEL, sheet_name="Base")
        df["Rua"] = df["Rua"].astype(str).str.strip()
        df["Bairro"] = df["Bairro"].astype(str).str.strip()
        df["CEP"] = df["CEP"].astype(str).str.strip()
        df["KM"] = (
            df["KM"]
            .astype(str)
            .str.replace('"', "", regex=False)
            .str.replace(".", ",", regex=False)
        )
        df["Valor"] = df["Valor"].map(
            lambda x: f"R$ {x:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()


df_base = carregar_dados_do_excel()

st.title("🔍 Consulta de Corridas")
st.write("Digite qualquer parte da Rua, Bairro ou CEP.")

# Campo de busca maior, fácil de clicar com o dedão
busca = st.text_input(
    "Digite sua busca aqui:", value="", placeholder="Ex: lig, realengo..."
)

if busca.strip() != "" and not df_base.empty:
    termo = busca.lower()
    resultado = df_base[
        df_base["Rua"].str.lower().str.contains(termo, na=False)
        | df_base["Bairro"].str.lower().str.contains(termo, na=False)
        | df_base["CEP"].str.lower().str.contains(termo, na=False)
    ]

    if resultado.empty:
        st.error("❌ Dados não encontrados")
    else:
        st.success(f"✅ {len(resultado)} resultados encontrados:")

        # Exibe os resultados em formato de "blocos/cartões", ideal para qualquer tela de celular
        for idx, row in resultado.iterrows():
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: #f1f3f6; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 6px solid #2e7d32;">
                        <h3 style="margin: 0; font-size: 18px; color: #1a1a1a;">🗺️ {row['Rua']}</h3>
                        <p style="margin: 5px 0 0 0; font-size: 15px; color: #555;"><b>Bairro:</b> {row['Bairro']} | <b>CEP:</b> {row['CEP']}</p>
                        <hr style="margin: 8px 0; border: 0; border-top: 1px solid #ddd;">
                        <span style="font-size: 20px; font-weight: bold; color: #2e7d32; background-color: #e8f5e9; padding: 3px 8px; border-radius: 5px;">💰 {row['Valor']}</span>
                        <span style="font-size: 16px; font-weight: bold; color: #1565c0; background-color: #e3f2fd; padding: 3px 8px; border-radius: 5px; margin-left: 10px;">📏 {row['KM']} KM</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
elif df_base.empty:
    st.warning("⚠️ Insira a planilha Excel na pasta para ativar as buscas.")
else:
    st.info("💡 Aguardando digitação...")
