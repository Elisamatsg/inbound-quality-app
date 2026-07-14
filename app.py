import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
import time

# IMPORTA E ATIVA O .env
from dotenv import load_dotenv
load_dotenv()

# AGORA PEGA AS VARIÁVEIS
user_env = os.getenv("USER")
pass_env = os.getenv("PASSWORD")

#st.write(user_env) - > Para testar se está pegando a variável do .env


st.set_page_config(page_title="Inbound Quality", page_icon="🚚", layout="wide", initial_sidebar_state="expanded")

# BLOCO ABAIXO PARA ESCONDER OS BOTÕES DO GITHUB E MENU
st.markdown(
    """
    <style>
    /* Força o desaparecimento de qualquer botão ou menu no topo direito */
    .stAppDeployButton, 
    [data-testid="stAppToolbar"], 
    [data-testid="stActionButtonIcon"],
    option-menu-themes {
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        width: 0px !important;
        height: 0px !important;
    }
    
    /* Esconde a barra cinza de fundo do cabeçalho, mantendo apenas os botões funcionais */
    header {
        background: transparent !important;
    }
    
    /* Remove o rodapé padrão */
    footer {
        visibility: hidden !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>

/* Fundo do sidebar */
section[data-testid="stSidebar"] {
    background-color: #F7F9FC;
}

/* Container do menu */
.menu-container {
    margin-top: 10px;
}

/* Botões do menu */
.menu-btn button {
    width: 100%;
    text-align: left;
    padding: 12px 16px;
    margin-bottom: 8px;
    border-radius: 10px;
    border: 1px solid transparent;
    background-color: transparent;
    color: #e6e6e6;
    font-size: 15px;
    font-weight: 500;
    transition: all 0.2s ease-in-out;
}

/* Hover */
.menu-btn button:hover {
    background-color: #1c1f26;
    border: 1px solid #3248f3;
    color: white;
}

/* Botão ativo */
.menu-btn-active button {
    width: 100%;
    text-align: left;
    padding: 12px 16px;
    margin-bottom: 8px;
    border-radius: 10px;
    border: 1px solid #3248f3;
    background-color: #1c1f26;
    color: white;
    font-size: 15px;
    font-weight: 600;
}

/* Botão sair */
.logout-btn button {
    width: 100%;
    padding: 10px;
    border-radius: 8px;
    background-color: #262730;
    color: #ff4b4b;
    border: 1px solid #ff4b4b;
}

.logout-btn button:hover {
    background-color: #ff4b4b;
    color: white;
}

</style>
""", unsafe_allow_html=True)



# ==========================================
# 0. CONTROLE DE ACESSO (LOGIN)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Criamos três colunas: a do meio será a nossa área de login
    # O "1" nas pontas cria um espaçamento lateral, o "2" no meio é o conteúdo
    col_esq, col_centro, col_dir = st.columns([1, 2, 1])
    
    with col_centro:
        # Usamos um container com borda para criar o "quadrante"
        with st.container(border=True):
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            st.image("https://1000logos.net/wp-content/uploads/2024/04/Stellantis-Logo.png", width=180)
            st.title("Auditoria de Recebimento 🚚")
            st.caption("CDC - Inbound Quality")
            st.markdown("</div>", unsafe_allow_html=True)
            
            user = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            
            if st.button("Entrar", use_container_width=True):
                if user == user_env and password == pass_env:

                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")

    # Adicionamos um pouco de espaço no topo para não ficar colado
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.stop()

# ==========================================
# 1. BANCO DE DADOS E CONFIGURAÇÕES
# ==========================================
def iniciar_banco():
    conn = sqlite3.connect('inspecoes_v4.db') 
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspecoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            data_hora TEXT, 
            n_viagem TEXT,
            fornecedor TEXT, 
            transportadora TEXT,
            total_embalagens INTEGER,
            embalagens_ko INTEGER,
            embalagens_ok INTEGER,
            base_embalagem TEXT, 
            stretch TEXT, 
            caixas TEXT,
            observacoes TEXT, 
            caminho_foto TEXT
        )
    ''')
    conn.commit()
    conn.close()

iniciar_banco()

def salvar_foto(foto_carregada):
    if foto_carregada is not None:
        if not os.path.exists('evidencias'):
            os.makedirs('evidencias')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        caminho = f"evidencias/{timestamp}_avaria.jpg"
        with open(caminho, "wb") as f:
            f.write(foto_carregada.getbuffer())
        return caminho
    return ""

# INICIALIZA A CHAVE DINÂMICA (Para limpar o formulário sem dar erro)
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0


# ==========================================
# 2. MENU LATERAL E SUPORTE
# ==========================================

# Define valor inicial ANTES de usar
if "menu_selecionado" not in st.session_state:
    st.session_state.menu_selecionado = "📱 Monitor inspeção"

with st.sidebar:
    st.image("https://1000logos.net/wp-content/uploads/2024/04/Stellantis-Logo.png", width=160)
    st.title("Inbound Quality")
    st.caption("Sistema de Auditoria de Doca")

    st.divider()

    if "menu_selecionado" not in st.session_state:
        st.session_state.menu_selecionado = "📱 Monitor inspeção"

    st.markdown('<div class="menu-container">', unsafe_allow_html=True)

    # BOTÃO 1
    classe = "menu-btn-active" if st.session_state.menu_selecionado == "📱 Monitor inspeção" else "menu-btn"
    st.markdown(f'<div class="{classe}">', unsafe_allow_html=True)
    if st.button("📱 Monitor inspeção", use_container_width=True):
        st.session_state.menu_selecionado = "📱 Monitor inspeção"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # BOTÃO 2
    classe = "menu-btn-active" if st.session_state.menu_selecionado == "📊 Painel visual" else "menu-btn"
    st.markdown(f'<div class="{classe}">', unsafe_allow_html=True)
    if st.button("📊 Painel visual", use_container_width=True):
        st.session_state.menu_selecionado = "📊 Painel visual"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # SUPORTE
    st.markdown("### Suporte")
    with st.expander("Precisa de ajuda?"):
        st.info("elisama gomes")
        st.write("✉️ elisama@stellantis")
        st.write("📱 (81) 99999-9999")

    st.divider()

    # LOGOUT ESTILIZADO
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("↪️ Sair", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 3. MONITOR INSPEÇÃO (DOCA)
# ==========================================
if st.session_state.menu_selecionado == "📱 Monitor inspeção":

    st.header("INSPEÇÃO DE RECEBIMENTO")
    
    with st.container(border=True):
        st.markdown("#### 📄 1. Dados da Carga")
        col1, col2, col3 = st.columns(3)
        with col1:
            n_viagem = st.text_input("N° da viagem", key=f"n_viagem_{st.session_state.form_key}")
        with col2:
            fornecedor = st.text_input("Fornecedor", key=f"fornecedor_{st.session_state.form_key}").strip().upper()
        with col3:
            transportadora = st.text_input("Transportadora", key=f"transp_{st.session_state.form_key}").strip().upper()
            
    with st.container(border=True):
        st.markdown("#### 📦 2. Volumetria da Carga")
        col_t, col_ko = st.columns(2)
        with col_t:
            total_embalagens = st.number_input("Total de Embalagens na Carreta", min_value=1, step=1, value=30, key=f"total_emb_{st.session_state.form_key}")
        with col_ko:
            embalagens_ko = st.number_input("Embalagens com Avaria (KOs)", min_value=0, max_value=total_embalagens, step=1, value=0, key=f"ko_emb_{st.session_state.form_key}")
        
        embalagens_ok = total_embalagens - embalagens_ko
        
        if embalagens_ko == 0:
            st.success(f"✅ Carga 100% Íntegra: {embalagens_ok} embalagens OK. Pronta para registrar!")
        else:
            st.warning(f"⚠️ Atenção: {embalagens_ko} KOs e {embalagens_ok} OKs. Detalhe as avarias abaixo.")

    # Valores padrão caso não haja avaria
    base_embalagem, stretch, caixas, observacoes, foto = "🟢 Aprovado", "🟢 Aprovado", "🟢 Aprovadas", "", None
    
    if embalagens_ko > 0:
        with st.container(border=True):
            st.markdown(f"#### 🔍 3. Detalhamento das {embalagens_ko} embalagens avariadas")
            
            base_embalagem = st.radio("Condição da Base da Embalagem", ["🟡 Atenção (Madeira trincada)", "🔴 Crítico (Quebrado/Risco de Queda)"], horizontal=True, key=f"base_{st.session_state.form_key}")
            stretch = st.radio("Filme Stretch / Amarração", ["🟡 Atenção (Frouxo/Solto)", "🔴 Crítico (Rasgado/Ausente)"], horizontal=True, key=f"stretch_{st.session_state.form_key}")
            caixas = st.radio("Integridade das Caixas", ["🟡 Avariadas (Amassadas)", "🔴 Violadas (Rasgadas/Vazando)"], horizontal=True, key=f"caixas_{st.session_state.form_key}")
            
            foto = st.camera_input("Capturar imagem representativa das avarias", key=f"foto_{st.session_state.form_key}")
            observacoes = st.text_area("Observações (Opcional)", placeholder="Ex: A carga tombou no baú...", key=f"obs_{st.session_state.form_key}")

    st.write("") 
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 Gravar Inspeção", use_container_width=True, type="primary"):
            if not n_viagem or not fornecedor or not transportadora:
                st.error("⚠️ N° da viagem, Fornecedor e Transportadora são obrigatórios!")
            else:
                data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                caminho_foto = salvar_foto(foto)
                
                # Salvar no banco
                conn = sqlite3.connect('inspecoes_v4.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO inspecoes (data_hora, n_viagem, fornecedor, transportadora, total_embalagens, embalagens_ko, embalagens_ok, base_embalagem, stretch, caixas, observacoes, caminho_foto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (data_hora, n_viagem, fornecedor, transportadora, total_embalagens, embalagens_ko, embalagens_ok, base_embalagem, stretch, caixas, observacoes, caminho_foto))
                conn.commit()
                conn.close()
                
                st.toast(f"✅ Viagem {n_viagem} registrada com sucesso!", icon="✅")
                time.sleep(1) # Aguarda para o usuário ver o aviso
                
                # Incrementa o form_key: isso recria todos os inputs vazios no rerun
                st.session_state.form_key += 1
                st.rerun()


# ==========================================
# 4. PAINEL VISUAL (MÉTRICAS + FORNECEDOR/TRANSP)
# ==========================================
elif st.session_state.menu_selecionado == "📊 Painel visual":

    st.header("📈 Dashboard de Inbound Quality")
    
    # 1. Carrega os dados do banco
    conn = sqlite3.connect('inspecoes_v4.db')
    df = pd.read_sql_query("SELECT * FROM inspecoes", conn)
    conn.close()

    if df.empty:
        st.warning("Aguardando os primeiros dados da doca...")
    else:
        # Converter a coluna de data (que vem como texto do banco) para formato de data real
        df['data_hora'] = pd.to_datetime(df['data_hora'])
        
        # 2. CRIANDO O FILTRO DE DATAS
        st.markdown("### 📅 Período")
        
        # Pega a menor e a maior data que existem no seu banco para definir o calendário
        data_minima = df['data_hora'].min().date()
        data_maxima = df['data_hora'].max().date()
        
        col_filtro, _ = st.columns([1, 2]) # Deixa o filtro menorzinho no canto
        with col_filtro:
            datas_selecionadas = st.date_input(
                "Selecione o intervalo:",
                value=(data_minima, data_maxima),
                min_value=data_minima,
                max_value=data_maxima,
                format="DD/MM/YYYY"
            )

        # 3. APLICANDO O FILTRO AOS DADOS
        if len(datas_selecionadas) == 2:
            data_inicio, data_fim = datas_selecionadas
            # Adiciona 1 dia na data final para garantir que as viagens até 23:59 entrem
            data_fim_inclusiva = pd.to_datetime(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            # Corta a base de dados
            mask = (df['data_hora'] >= pd.to_datetime(data_inicio)) & (df['data_hora'] <= data_fim_inclusiva)
            df_filtrado = df.loc[mask].copy()
        else:
            # Se o usuário ainda não clicou na segunda data, mostra tudo
            df_filtrado = df.copy() 

        # 4. RENDERIZAR OS GRÁFICOS (Usando a base filtrada)
        if df_filtrado.empty:
            st.info("Nenhuma inspeção encontrada neste período selecionado.")
        else:
            df_filtrado['viagem_com_avaria'] = df_filtrado['embalagens_ko'] > 0

            total_volume = int(df_filtrado['total_embalagens'].sum())
            total_ko = int(df_filtrado['embalagens_ko'].sum())
            viagens_com_problema = df_filtrado['viagem_com_avaria'].sum()
            taxa_saude_volume = ((total_volume - total_ko) / total_volume * 100) if total_volume > 0 else 100

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🚚 Viagens Recebidas", len(df_filtrado))
                col2.metric("📦 Volume Total (Embalagens)", total_volume)
                col3.metric("⚠️ Volume Avariado (KOs)", total_ko)
                col4.metric("🏆 Health Score", f"{taxa_saude_volume:.1f}%")

            st.info(f"💡 Em {len(df_filtrado)} viagens recebidas neste período, **{viagens_com_problema}** apresentaram avarias.")

            aba1, aba2, aba3 = st.tabs(["🏭 Análise de Fornecedores", "🚛 Análise de Transportadoras", "📋 Histórico Base de Dados"])

            # ABA 1: FORNECEDORES
            with aba1:
                col_graf, col_tab = st.columns([2, 1])
                df_forn = df_filtrado.groupby('fornecedor').agg(
                    Volume_Total=('total_embalagens', 'sum'),
                    Volume_KO=('embalagens_ko', 'sum'),
                    Viagens_com_Avaria=('viagem_com_avaria', 'sum')
                ).reset_index()
                
                df_forn_ko = df_forn[df_forn['Volume_KO'] > 0]
                
                with col_graf:
                    if not df_forn_ko.empty:
                        st.markdown("**Volume Perdido (KOs) por Fornecedor**")
                        st.bar_chart(df_forn_ko.set_index('fornecedor')['Volume_KO'], color="#3248f3")
                    else:
                        st.success("Nenhum fornecedor com avarias no período!")
                
                with col_tab:
                    if not df_forn_ko.empty:
                        st.markdown("**Frequência**")
                        st.dataframe(df_forn_ko[['fornecedor', 'Viagens_com_Avaria']].sort_values('Viagens_com_Avaria', ascending=False), hide_index=True)

            # ABA 2: TRANSPORTADORAS
            with aba2:
                col_graf2, col_tab2 = st.columns([2, 1])
                df_transp = df_filtrado.groupby('transportadora').agg(
                    Volume_Total=('total_embalagens', 'sum'),
                    Volume_KO=('embalagens_ko', 'sum'),
                    Viagens_com_Avaria=('viagem_com_avaria', 'sum')
                ).reset_index()
                
                df_transp_ko = df_transp[df_transp['Volume_KO'] > 0]
                
                with col_graf2:
                    if not df_transp_ko.empty:
                        st.markdown("**Volume Perdido (KOs) por Transportadora**")
                        st.bar_chart(df_transp_ko.set_index('transportadora')['Volume_KO'], color="#18b1c6")
                    else:
                        st.success("Nenhuma transportadora com avarias no período!")
                
                with col_tab2:
                    if not df_transp_ko.empty:
                        st.markdown("**Frequência**")
                        st.dataframe(df_transp_ko[['transportadora', 'Viagens_com_Avaria']].sort_values('Viagens_com_Avaria', ascending=False), hide_index=True)

            # ABA 3: DADOS BRUTOS
            with aba3:
                df_bruto = df_filtrado.drop(columns=['id', 'viagem_com_avaria'])
                df_bruto.columns = [col.replace('_', ' ').capitalize() for col in df_bruto.columns]
                
                # Ajusta a formatação da data para ficar mais limpa na tabela
                df_bruto['Data hora'] = df_bruto['Data hora'].dt.strftime('%d/%m/%Y %H:%M:%S')
                
                st.dataframe(df_bruto, use_container_width=True)
