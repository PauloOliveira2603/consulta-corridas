import os
import io
import pandas as pd
import streamlit as st
from fpdf import FPDF

# 1. Configurações Visuais para Celular
st.set_page_config(page_title="Consulta de Dados", layout="centered")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2.0rem !important; padding-bottom: 0.5rem !important; padding-left: 1rem; padding-right: 1rem; }
    .custom-title { font-size: 28px !important; font-weight: bold !important; color: #0f4c81 !important; text-align: center !important; margin-top: 0px !important; margin-bottom: 12px !important; padding: 0px !important; width: 100%; display: block; }
    div.stDownloadButton { display: flex; justify-content: center; margin-bottom: 4px !important; margin-top: 2px !important; width: 100%; }
    div.stDownloadButton button { margin: 0 auto !important; display: block !important; }
    .custom-text { text-align: left !important; font-size: 14px !important; margin-top: 0px !important; margin-bottom: 2px !important; color: #444444 !important; font-weight: 500; }
    div[data-testid="stTextInput"] input { font-size: 18px !important; height: 45px !important; }
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
        
        # Garante tratamento numérico estável para as validações
        df["Grupo_Num"] = pd.to_numeric(df["Grupo"], errors='coerce').fillna(0).astype(int)
        df["Valor_Num"] = pd.to_numeric(df["Valor"], errors='coerce').fillna(0.0)
        
        df["Rua"] = df["Rua"].astype(str).str.strip()
        df["Bairro"] = df["Bairro"].astype(str).str.strip()
        df["Cep"] = df["Cep"].astype(str).str.strip()
        df["Km"] = df["Km"].astype(str).str.replace('"', '', regex=False).str.replace('.', ',', regex=False)
        
        df["Valor_Tela"] = df["Valor_Num"].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Ordena a base por grupo para que a quebra visual no relatório funcione perfeitamente
        df = df.sort_values(by="Grupo_Num").reset_index(drop=True)
        return df
    except:
        return pd.DataFrame()

df_base = carregar_dados_do_excel()

# 3. Classe do PDF com Linha Divisória de Grupos e Destaque Vermelho para Aumentos
class PDF_Relatorio(FPDF):
    def header(self):
        if os.path.exists(NOME_LOGOTIPO):
            try:
                self.image(NOME_LOGOTIPO, x=10, y=10, w=30)
            except:
                pass
        
        self.set_xy(10, 16)
        self.set_font("Arial", "B", 15)
        self.cell(190, 8, "RELATÓRIO GERAL DE CORRIDAS", ln=True, align="C")
        
        self.set_x(10)
        self.set_font("Arial", "", 9)
        self.cell(190, 5, "Documento gerado automaticamente pelo aplicativo de busca.", ln=True, align="C")
        
        self.set_y(40)
        
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
    
    ultimo_grupo = None
    
    for _, row in dados_df.iterrows():
        # Regra 1: Se mudou o grupo em relação à linha anterior, desenha uma linha preta espessa de divisão
        if ultimo_grupo is not None and row['Grupo_Num'] != ultimo_grupo:
            pdf.set_line_width(0.8) # Engrossa a linha
            pdf.set_draw_color(0, 0, 0) # Cor preta
            pdf.cell(190, 1, "", border="T", ln=True) # Desenha a linha horizontal
            pdf.set_line_width(0.2) # Restaura a espessura padrão da linha
            pdf.set_draw_color(0, 0, 0)
            
        ultimo_grupo = row['Grupo_Num']
        
        # Regra 2: Se Grupo for diferente de Valor, pinta o texto de vermelho. Caso contrário, usa preto.
        if int(row['Grupo_Num']) != int(row['Valor_Num']):
            pdf.set_text_color(200, 0, 0) # Vermelho
            pdf.set_font("Arial", "B", 9)  # Negrito para dar mais atenção
        else:
            pdf.set_text_color(0, 0, 0) # Preto
            pdf.set_font("Arial", "", 9)
            
        valor_formatado = f"R$ {row['Valor_Num']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        pdf.cell(15, 7, str(row['Grupo_Num']), border=1, align="C")
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

# 4. Desenho da Interface
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
            
            # Validação na Tela: Altera as variáveis de estilo CSS caso haja aumento (Grupo != Valor)
            houve_aumento = int(row['Grupo_Num']) != int(row['Valor_Num'])
            cor_texto_principal = "#c80000" if houve_aumento else "#1a1a1a"
            peso_fonte = "bold" if houve_aumento else "normal"
            
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: #f1f3f6; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 6px solid #2e7d32;">
                        <h3 style="margin: 0; font-size: 18px; color: {cor_texto_principal}; font-weight: {peso_fonte};">🗺️ {row['Rua']}</h3>
                        <p style="margin: 5px 0 0 0; font-size: 15px; color: {cor_texto_principal};"><b>Bairro:</b> {row['Bairro']} | <b>CEP:</b> {row['Cep']}</p>
                        <hr style="margin: 8px 0; border: 0; border-top: 1px solid #ddd;">
                        <span style="font-size: 20px; font-weight: bold; color: #2e7d32; background-color: #e8f5e9; padding: 3px 8px; border-radius: 5px;">💰 {row['Valor_Tela']}</span>
                        <span style="font-size: 16px; font-weight: bold; color: #1565c0; background-color: #e3f2fd; padding: 3px 8px; border-radius: 5px; margin-left: 10px;">📏 {row['Km']} KM</span>
                        <span style="font-size: 16px; font-weight: bold; color: #37474f; background-color: #eceff1; padding: 3px 8px; border-radius: 5px; margin-left: 10px;">👥 GRUPO {row['Grupo_Num']}</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
elif df_base.empty:
    st.warning("⚠️ Insira a planilha Excel para ativar o sistema.")
else:
    st.info("💡 Aguardando digitação...")
