import os
import io
import pandas as pd
import streamlit as st
from fpdf import FPDF

# 1. Configurações Visuais Avançadas (Cores, Fontes e Margens Coladas)
st.set_page_config(page_title="Consulta de Dados", layout="centered")

st.markdown(
    """
    <style>
    /* Compacta o topo e as laterais para telas de celular */
    .block-container { padding-top: 0.2rem !important; padding-bottom: 0.5rem !important; padding-left: 1rem; padding-right: 1rem; }
    
    /* Título em Azul Escuro e tamanho menor */
    .custom-title { font-size: 26px !important; font-weight: bold !important; color: #0f4c81 !important; text-align: center !important; margin-top: 2px !important; margin-bottom: 2px !important; padding: 0px !important; }
    
    /* Configuração padrão para os textos explicativos */
    .custom-text { text-align: center !important; font-size: 14px !important; margin-top: 0px !important; margin-bottom: 6px !important; color: #444444 !important; }
    
    /* Ajuste da caixa de digitação */
    div[data-testid="stTextInput"] input { font-size: 18px !important; height: 45px !important; }
    
    /* Ajuste das margens do botão de download e imagens */
    div.stDownloadButton { margin-bottom: 4px !important; margin-top: 2px !important; }
    div[data-testid="stImage"] { display: flex; justify-content: center; margin-bottom: 2px !important; }
    hr { margin-top: 4px !important; margin-bottom: 8px !important; }
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
        
        # Remove linhas fantasmas do Excel onde a Rua está em branco
        df = df.dropna(subset=["Rua"])
        
        df["Rua"] = df["Rua"].astype(str).str.strip()
        df["Bairro"] = df["Bairro"].astype(str).str.strip()
        df["CEP"] = df["CEP"].astype(str).str.strip()
        df["KM"] = df["KM"].astype(str).str.replace('"', '', regex=False).str.replace('.', ',', regex=False)
        
        # Cria versão numérica estável para o PDF e formata o preço para exibição visual
        df["Valor_Num"] = pd.to_numeric(df["Valor"], errors='coerce').fillna(0.0)
        df["Valor_Tela"] = df["Valor_Num"].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        return df
    except:
        return pd.DataFrame()

df_base = carregar_dados_do_excel()

# 3. Função para Gerar o Relatório PDF
def gerar_pdf(dados_df):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Adiciona o Logotipo no Canto Esquerdo se o arquivo existir
    if os.path.exists(NOME_LOGOTIPO):
        pdf.image(NOME_LOGOTIPO, x=10, y=10, w=30)
        pdf.set_y(45)
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
        valor_formatado = f"R$ {row['Valor_Num']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        pdf.cell(15, 7, str(int(row['Grupo'])), border=1, align="C")
        pdf.cell(75, 7, str(row['Rua'])[:38], border=1)
        pdf.cell(25, 7, valor_formatado, border=1, align="C")
        pdf.cell(20, 7, str(row['KM']), border=1, align="C")
        pdf.cell(30, 7, str(row['Bairro'])[:15], border=1)
        pdf.cell(25, 7, str(row['CEP']), border=1, align="C")
        pdf.ln()
        
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return io.BytesIO(pdf_output.encode('latin1'))
    return io.BytesIO(pdf_output)

# 4. Desenho da Interface com a Ordem Nova Solicitada
# Logotipo muito pequeno centralizado no topo sem sobrepor nada
if os.path.exists(NOME_LOGOTIPO):
    st.image(NOME_LOGOTIPO, width=50)

# Título customizado em Azul Escuro menor
st.markdown('<div class="custom-title">Consulta de Corridas</div>', unsafe_allow_html=True)

# Botão de Download do PDF Dinâmico logo abaixo do título
if not df_base.empty:
    pdf_bytes = gerar_pdf(df_base)
    st.download_button(
        label="📥 Baixar Relatório Completo em PDF",
        data=pdf_bytes,
        file_name="relatorio_corridas_base.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# Texto explicativo reposicionado para DEPOIS do botão
st.markdown('<div class="custom-text">Digite qualquer parte da Rua, Bairro ou CEP.</div>', unsafe_allow_html=True)

st.write("---")

# Campo de busca interativo colado logo em seguida
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
