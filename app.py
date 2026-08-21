import os
import io
import base64
import pandas as pd
import streamlit as st
from fpdf import FPDF
from PIL import Image

# 1. Configurações Visuais para Celular
st.set_page_config(page_title="Consulta de Dados", layout="centered")

st.markdown(
    """
    <style>
    .block-container { padding-top: 0.2rem !important; padding-bottom: 0.5rem !important; padding-left: 1rem; padding-right: 1rem; }
    .custom-title { font-size: 26px !important; font-weight: bold !important; color: #0f4c81 !important; text-align: center !important; margin-top: 2px !important; margin-bottom: 2px !important; padding: 0px !important; }
    .custom-text { text-align: left !important; font-size: 14px !important; margin-top: 0px !important; margin-bottom: 2px !important; color: #444444 !important; font-weight: 500; }
    div[data-testid="stTextInput"] input { font-size: 18px !important; height: 45px !important; }
    div.stDownloadButton { margin-bottom: 4px !important; margin-top: 2px !important; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 5px; }
    hr { margin-top: 4px !important; margin-bottom: 6px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

NOME_ARQUIVO_EXCEL = "Controle corridas NOVO.xlsx"
NOME_LOGOTIPO = "logotipo.png"

# 2. Função para carregar e limpar a base de dados
@st.cache_data(ttl=30)
def carregar_dados_do_excel():
    if not os.path.exists(NOME_ARQUIVO_EXCEL):
        return pd.DataFrame()
    try:
        df = pd.read_excel(NOME_ARQUIVO_EXCEL, sheet_name="Base")
        df.columns = [c.strip().title() for c in df.columns]
        df = df.dropna(subset=["Rua"])
        
        df["Rua"] = df["Rua"].astype(str).str.strip()
        df["Bairro"] = df["Bairro"].astype(str).str.strip()
        df["Cep"] = df["Cep"].astype(str).str.strip()
        df["Km"] = df["Km"].astype(str).str.replace('"', '', regex=False).str.replace('.', ',', regex=False)
        
        df["Valor_Num"] = pd.to_numeric(df["Valor"], errors='coerce').fillna(0.0)
        df["Valor_Tela"] = df["Valor_Num"].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return df
    except:
        return pd.DataFrame()

df_base = carregar_dados_do_excel()

# 3. Classe do PDF Ajustada com Textos Centralizados à Direita da Logo
class PDF_Relatorio(FPDF):
    def header(self):
        if os.path.exists(NOME_LOGOTIPO):
            # Posiciona a imagem à esquerda
            self.image(NOME_LOGOTIPO, x=10, y=10, w=30)
            # Define o início do texto após a imagem (X=45) e alinha verticalmente
            self.set_xy(42, 16)
            largura_texto = 158
        else:
            self.set_xy(10, 15)
            largura_texto = 190
            
        # Título principal centralizado no bloco da direita
        self.set_font("Arial", "B", 15)
        self.cell(largura_texto, 8, "RELATÓRIO GERAL DE CORRIDAS", ln=True, align="C")
        
        if os.path.exists(NOME_LOGOTIPO):
            self.set_x(42)
        else:
            self.set_x(10)
            
        # Subtítulo explicativo centralizado no bloco da direita
        self.set_font("Arial", "", 9)
        self.cell(largura_texto, 5, "Documento gerado automaticamente pelo aplicativo de busca.", ln=True, align="C")
        
        # Margem fixa segura para iniciar a tabela de dados
        self.set_y(38)
        
        self.set_font("Arial", "B", 10)
        self.set_fill_color(230, 230, 230)
        self.cell(15, 8, "Grupo", border=1, align="C", fill=True)
        self.cell(75, 8, "Rua / Destino", border=1, fill=True)
        self.cell(25, 8, "Valor", border=1, align="C", fill=True)
        self.cell(20, 8, "KM", border=1, align="C", fill=True)
        self.cell(30, 8, "Bairro", border=1, fill=True)
        self.cell(25, 8, "CEP", border=1, align="C", fill=True)
        self.ln()

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 9)
        self.set_text_color(100, 100, 100)
        texto_pagina = f"Página {self.page_no()} de {{nb}}"
        self.cell(0, 10, texto_pagina, align="C")

def gerar_pdf(dados_df):
    pdf = PDF_Relatorio(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages() 
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    pdf.set_font("Arial", "", 9)
    for _, row in dados_df.iterrows():
        valor_formatado = f"R$ {row['Valor_Num']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        pdf.cell(15, 7, str(int(row['Grupo'])), border=1, align="C")
        pdf.cell(75, 7, str(row['Rua'])[:38], border=1)
        pdf.cell(25, 7, valor_formatado, border=1, align="C")
        pdf.cell(20, 7, str(row['Km']), border=1, align="C")
        pdf.cell(30, 7, str(row['Bairro'])[:15], border=1)
        pdf.cell(25, 7, str(row['Cep']), border=1, align="C")
        pdf.ln()
        
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return io.BytesIO(pdf_output.encode('latin1'))
    return io.BytesIO(pdf_output)

# 4. Desenho da Interface Final
# Método infalível usando Base64 HTML para forçar a renderização do logo e quebrar o cache do site
if os.path.exists(NOME_LOGOTIPO):
    try:
        with open(NOME_LOGOTIPO, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f'<div class="logo-container"><img src="data:image/png;base64,{encoded_string}" width="50"></div>',
            unsafe_allow_html=True
        )
    except:
        pass

st.markdown('<div class="custom-title">Consulta de Corridas</div>', unsafe_allow_html=True)

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

st.markdown('<div class="custom-text">Digite qualquer parte da Rua, Bairro ou CEP.</div>', unsafe_allow_html=True)

busca = st.text_input("Digite sua busca aqui:", value="", placeholder="Ex: lig, realengo...")

if busca.strip() != "" and not df_base.empty:
    termo = busca.lower()
    resultado = df_base[
        df_base["Rua"].str.lower().str.contains(termo, na=False) |
        df_base["Bairro"].str.lower().str.contains(termo, na=False) |
        df_base["Cep"].str.lower().str.contains(termo, na=False)
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
                        <p style="margin: 5px 0 0 0; font-size: 15px; color: #555;"><b>Bairro:</b> {row['Bairro']} | <b>CEP:</b> {row['Cep']}</p>
                        <hr style="margin: 8px 0; border: 0; border-top: 1px solid #ddd;">
                        <span style="font-size: 20px; font-weight: bold; color: #2e7d32; background-color: #e8f5e9; padding: 3px 8px; border-radius: 5px;">💰 {row['Valor_Tela']}</span>
                        <span style="font-size: 16px; font-weight: bold; color: #1565c0; background-color: #e3f2fd; padding: 3px 8px; border-radius: 5px; margin-left: 10px;">📏 {row['Km']} KM</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
elif df_base.empty:
    st.warning("⚠️ Insira a planilha Excel para ativar o sistema.")
else:
    st.info("💡 Aguardando digitação...")
