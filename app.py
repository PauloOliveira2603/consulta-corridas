import os
import pandas as pd
import streamlit as st
from fpdf import FPDF

# 1. Configurações Visuais para Celular
st.set_page_config(page_title="Consulta de Dados", layout="centered")

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
NOME_LOGOTIPO = "logotipo.png"

# 2. Função para carregar a base de dados
@st.cache_data(ttl=30)
def carregar_dados_do_excel():
    if not os.path.exists(NOME_ARQUIVO_EXCEL):
        return pd.DataFrame()
    try:
        df = pd.read_excel(NOME_ARQUIVO_EXCEL, sheet_name="Base")
        df["Rua"] = df["Rua"].astype(str).str.strip()
        df["Bairro"] = df["Bairro"].astype(str).str.strip()
        df["CEP"] = df["CEP"].astype(str).str.strip()
        df["KM"] = df["KM"].astype(str).str.replace('"', '', regex=False).str.replace('.', ',', regex=False)
        # Mantém uma coluna numérica oculta para o PDF e cria a versão formatada para a tela
        df["Valor_Num"] = pd.to_numeric(df["Valor"], errors='coerce').fillna(0.0)
        df["Valor_Tela"] = df["Valor_Num"].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return df
    except:
        return pd.DataFrame()

df_base = carregar_dados_do_excel()

# 3. Função Inteligente para Gerar o Relatório PDF
def gerar_pdf(dados_df):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Adiciona o Logotipo no Canto Esquerdo se o arquivo existir
    if os.path.exists(NOME_LOGOTIPO):
        pdf.image(NOME_LOGOTIPO, x=10, y=10, w=30) # Posição X=10, Y=10, Largura=30mm
        pdf.set_y(45) # Joga o texto abaixo do logotipo para não encavalar
    else:
        pdf.set_y(15)
        
    # Cabeçalho do Relatório
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RELATÓRIO GERAL DE CORRIDAS", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "Documento gerado automaticamente pelo aplicativo de busca.", ln=True, align="C")
    pdf.ln(10)
    
    # Títulos da Tabela do PDF
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(15, 8, "Grupo", border=1, align="C", fill=True)
    pdf.cell(75, 8, "Rua / Destino", border=1, fill=True)
    pdf.cell(25, 8, "Valor", border=1, align="C", fill=True)
    pdf.cell(20, 8, "KM", border=1, align="C", fill=True)
    pdf.cell(30, 8, "Bairro", border=1, fill=True)
    pdf.cell(25, 8, "CEP", border=1, align="C", fill=True)
    pdf.ln()
    
    # Linhas da Tabela
    pdf.set_font("Arial", "", 9)
    for _, row in dados_df.iterrows():
        # Formata o valor monetário para o padrão brasileiro dentro do PDF
        valor_formatado = f"R$ {row['Valor_Num']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        pdf.cell(15, 7, str(row['Grupo']), border=1, align="C")
        pdf.cell(75, 7, str(row['Rua'])[:38], border=1) # Limita caracteres para não estourar a folha
        pdf.cell(25, 7, valor_formatado, border=1, align="C")
        pdf.cell(20, 7, str(row['KM']), border=1, align="C")
        pdf.cell(30, 7, str(row['Bairro'])[:15], border=1)
        pdf.cell(25, 7, str(row['CEP']), border=1, align="C")
        pdf.ln()
        
    return pdf.output()

# 4. Desenho da Tela do Aplicativo (Com Logotipo Superior)
col1, col2 = st.columns([1, 3])
with col1:
    if os.path.exists(NOME_LOGOTIPO):
        st.image(NOME_LOGOTIPO, width=90)
with col2:
    st.title("Consulta de Corridas")

# Botão de Download do PDF (Custo Zero e Ilimitado)
if not df_base.empty:
    pdf_bytes = gerar_pdf(df_base)
    st.download_button(
        label="📥 Baixar Relatório Completo em PDF",
        data=pdf_bytes,
        file_name="relatorio_corridas_base.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.write("---")

# Campo de busca interativo
busca = st.text_input("Digite sua busca aqui:", value="", placeholder="Ex: lig, realengo...")

if busca.strip() != "" and not df_base.empty:
    termo = busca.lower()
    resultado = df_base[
        df_base["Rua"].str.lower().str.contains(termo, na=False) |
        df_base["Bairro"].str.lower().str.contains(termo, na=False) |
        df_base["CEP"].str.lower().str.contains(termo, na=False)
    ]
    
    if resultado.empty:
        st.error("❌ Dados não encontrados")
    else:
        st.success(f"✅ {len(resultado)} resultados encontrados:")
        for idx, row in resultado.iterrows():
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: #f1f3f6; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 6px solid #2e7d32;">
                        <h3 style="margin: 0; font-size: 18px; color: #1a1a1a;">🗺️ {row['Rua']}</h3>
                        <p style="margin: 5px 0 0 0; font-size: 15px; color: #555;"><b>Bairro:</b> {row['Bairro']} | <b>CEP:</b> {row['CEP']}</p>
                        <hr style="margin: 8px 0; border: 0; border-top: 1px solid #ddd;">
                        <span style="font-size: 20px; font-weight: bold; color: #2e7d32; background-color: #e8f5e9; padding: 3px 8px; border-radius: 5px;">💰 {row['Valor_Tela']}</span>
                        <span style="font-size: 16px; font-weight: bold; color: #1565c0; background-color: #e3f2fd; padding: 3px 8px; border-radius: 5px; margin-left: 10px;">📏 {row['KM']} KM</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
elif df_base.empty:
    st.warning("⚠️ Insira a planilha Excel para ativar o sistema.")
else:
    st.info("💡 Aguardando digitação...")
