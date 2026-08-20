import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Consulta de Dados", layout="centered")
NOME_ARQUIVO_EXCEL = "Controle corridas NOVO.xlsx"


@st.cache_data(ttl=60)
def carregar_dados_do_excel():
    if not os.path.exists(NOME_ARQUIVO_EXCEL):
        st.error(
            f"❌ Arquivo '{NOME_ARQUIVO_EXCEL}' não encontrado na pasta do script."
        )
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
        colunas_validas = ["Grupo", "Rua", "Valor", "KM", "Bairro", "CEP"]
        df = df[[col for col in colunas_validas if col in df.columns]]
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()


df_base = carregar_dados_do_excel()

st.title("🔍 Consulta de Tabelas")
st.write("Digite qualquer parte da Rua, Bairro ou CEP para buscar.")

busca = st.text_input(
    "Digite sua busca aqui:", value="", placeholder="Ex: lig, realengo, 21740"
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
        st.success(f"✅ Resultados abaixo ({len(resultado)} encontrados):")
        st.dataframe(resultado, use_container_width=True, hide_index=True)
elif df_base.empty:
    st.warning("⚠️ Insira a planilha Excel na pasta para ativar as buscas.")
else:
    st.info("💡 Aguardando digitação para exibir os resultados...")
