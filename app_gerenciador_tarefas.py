import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# ============================================================================
# CONFIGURAÇÃO DE IDENTIDADE VISUAL - V-CONTROLL HUB
# ============================================================================

# Configuração da página com tema V-Controll
st.set_page_config(
    page_title="V-Controll Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema customizado com cores da logo V-Controll
CORES_VCONTROLL = {
    "azul_escuro": "#1C1A4A",      # Sidebar / Textos Principais
    "azul_claro": "#748DA6",       # Corpo Central / Elementos Secundários
    "branco": "#FFFFFF",
    "sucesso": "#10B981",
    "erro": "#EF4444",
    "aviso": "#F59E0B"
}

# CSS customizado para tema V-Controll
st.markdown(f"""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {CORES_VCONTROLL['azul_escuro']};
        color: {CORES_VCONTROLL['branco']};
    }}
    
    [data-testid="stSidebar"] * {{
        color: {CORES_VCONTROLL['branco']} !important;
    }}
    
    /* Corpo central */
    .main {{
        background-color: {CORES_VCONTROLL['azul_claro']}15;
    }}
    
    /* Headers */
    h1, h2 {{
        color: {CORES_VCONTROLL['azul_escuro']} !important;
    }}
    
    /* Botões */
    .stButton>button {{
        background-color: {CORES_VCONTROLL['azul_escuro']} !important;
        color: {CORES_VCONTROLL['branco']} !important;
    }}
    
    .stButton>button:hover {{
        background-color: {CORES_VCONTROLL['azul_claro']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONEXÃO SEGURA COM SUPABASE
# ============================================================================

def inicializar_supabase() -> Client:
    url = str(st.secrets["supabase"]["url"]).strip()
    public_key = str(st.secrets["supabase"].get("public_key", "")).strip().strip('"').strip("'")
    secret_key = str(st.secrets["supabase"].get("secret_key", "")).strip().strip('"').strip("'")

    if public_key and not public_key.startswith("sb_publicable_"):
        raise ValueError("public_key inválido: deve começar com sb_publicable_.")
    if secret_key and not secret_key.startswith("sb_secret_"):
        raise ValueError("secret_key inválido: deve começar com sb_secret_.")

    if secret_key:
        return create_client(url, secret_key)
    if public_key:
        return create_client(url, public_key)

    raise ValueError("Nenhuma chave Supabase foi configurada. Adicione public_key e/ou secret_key nos secrets.")

try:
    supabase = inicializar_supabase()
except Exception as e:
    st.error(f"Erro real: {e}")
    st.stop()

# ============================================================================
# CONFIGURAÇÕES DE ENUMERADORES
# ============================================================================

LISTA_ANOS = ["2025", "2026", "2027"]
LISTA_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

TIPOS_DOCS_FIXOS = [
    "Contrato Social / Alterações",
    "Cartão CNPJ",
    "Procuração Eletrônica",
    "Inscrição Estadual/Municipal",
    "Senha de Acessos / Códigos",
    "Outros Documentos Fixos"
]

PALETA_AZUL = {
    "primary": CORES_VCONTROLL["azul_escuro"],
    "secondary": CORES_VCONTROLL["azul_claro"],
    "muted": "#cfe3ff",
    "text": "#102a4b",
    "background": "#ffffff",
    "border": "#c8d9f0"
}

OBRIGACOES_BASE = {
    "Simples Nacional": [
        {"obrigacao": "DAS", "prazo": "Até o dia 20", "periodicidade": "Mensal"},
        {"obrigacao": "DEFIS", "prazo": "Até 31/03", "periodicidade": "Anual"},
        {"obrigacao": "Controle Faturamento", "prazo": "Mensal", "periodicidade": "Mensal"}
    ],
    "Lucro Presumido": [
        {"obrigacao": "PIS/COFINS", "prazo": "Até o dia 20", "periodicidade": "Mensal"},
        {"obrigacao": "IRPJ/CSLL", "prazo": "Até o último dia útil do mês subsequente", "periodicidade": "Trimestral"},
        {"obrigacao": "ECD", "prazo": "Até o último dia útil de Maio", "periodicidade": "Anual"},
        {"obrigacao": "ECF", "prazo": "Até o último dia útil de Julho", "periodicidade": "Anual"}
    ],
    "Lucro Real": [
        {"obrigacao": "PIS/COFINS", "prazo": "Até o dia 20", "periodicidade": "Mensal"},
        {"obrigacao": "IRPJ/CSLL", "prazo": "Mensal/Trimestral", "periodicidade": "Variável"},
        {"obrigacao": "ECD", "prazo": "Até o último dia útil de Maio", "periodicidade": "Anual"},
        {"obrigacao": "ECF", "prazo": "Até o último dia útil de Julho", "periodicidade": "Anual"}
    ]
}

OBRIGACOES_PADRAO = [
    {"obrigacao": "DAS - Simples Nacional", "prazo": "Até o dia 20", "periodicidade": "Mensal"},
    {"obrigacao": "DCTFWeb", "prazo": "Até o último dia útil do mês subsequente", "periodicidade": "Mensal"},
    {"obrigacao": "FGTS / SEFIP", "prazo": "Até o dia 7", "periodicidade": "Mensal"},
    {"obrigacao": "Folha de Pagamento", "prazo": "Até o último dia útil do mês subsequente", "periodicidade": "Mensal"}
]

# ============================================================================
# CONTROLE DE SESSÃO / LOGIN
# ============================================================================

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.perfil = None
    st.session_state.cliente_id_logado = None


def realizar_login(usuario, senha):
    if usuario == "vieiracontroller" and senha == "123456":
        st.session_state.logado = True
        st.session_state.perfil = "escritorio"
        st.session_state.cliente_id_logado = None
        st.rerun()

    res = supabase.table("usuarios_clientes").select("*").eq("email", usuario).eq("senha", senha).execute()
    if res.data:
        st.session_state.logado = True
        st.session_state.perfil = "cliente"
        st.session_state.cliente_id_logado = res.data[0]["cliente_id"]
        st.rerun()

    st.error("Usuário ou senha incorretos.")

# ============================================================================
# MÓDULO: FUNÇÕES DE CARREGAMENTO DE DADOS
# ============================================================================

def carregar_clientes():
    res = supabase.table("clientes").select("*").order("nome").execute()
    return res.data or []


def carregar_tarefas():
    res = supabase.table("tarefas").select("*").execute()
    return res.data or []


def carregar_documentos_fixos():
    res = supabase.table("documentos_fixos").select("*, clientes(nome)").execute()
    return res.data or []


def carregar_arquivos_escritorio():
    res = supabase.table("arquivos_escritorio").select("*").execute()
    return res.data or []


def carregar_acessos():
    res = supabase.table("usuarios_clientes").select("*, clientes(nome)").execute()
    return res.data or []


def carregar_config_obrigacoes():
    """Carrega configurações mestras de obrigações do catálogo"""
    try:
        res = supabase.table("config_obrigacoes").select("*").execute()
        return res.data or []
    except Exception:
        return []


def carregar_usuarios_escritorio():
    """Carrega usuários internos do escritório"""
    try:
        res = supabase.table("usuarios_escritorio").select("*").execute()
        return res.data or []
    except Exception:
        return []


def df_from_data(data):
    return pd.DataFrame(data) if data else pd.DataFrame()


def extrapolar_tarefas_por_mes(df_tarefas, mes, ano):
    if df_tarefas.empty:
        return df_tarefas
    return df_tarefas[(df_tarefas["mes"] == mes) & (df_tarefas["ano"] == ano)]

# ============================================================================
# MÓDULO: AUTOMAÇÃO DE OBRIGAÇÕES (NOVO CATÁLOGO MESTRE)
# ============================================================================

def gerar_obrigacoes_mes(mes: str, ano: str):
    """
    Função isolada para gerar automaticamente as obrigações do mês.
    Lê clientes ativos, cruza com as obrigações do regime em 'config_obrigacoes'
    e faz bulk insert na tabela 'tarefas'.
    """
    try:
        # Carregar clientes ativos
        clientes_ativos = supabase.table("clientes").select("*").eq("status_cadastro", "Ativo").execute().data or []
        
        if not clientes_ativos:
            return {"sucesso": False, "mensagem": "Nenhum cliente ativo encontrado.", "inseridas": 0}
        
        # Carregar config de obrigações
        config_obrigacoes = supabase.table("config_obrigacoes").select("*").execute().data or []
        
        if not config_obrigacoes:
            return {"sucesso": False, "mensagem": "Catálogo de obrigações não configurado.", "inseridas": 0}
        
        # Obrigações existentes para não duplicar
        tarefas_existentes = supabase.table("tarefas").select("cliente_id,obrigacao,mes,ano").execute().data or []
        existentes = {(t["cliente_id"], t["obrigacao"], t["mes"], t["ano"]) for t in tarefas_existentes}
        
        inseridas = 0
        novas_tarefas = []
        
        # Para cada cliente ativo
        for cliente in clientes_ativos:
            cliente_id = cliente.get("id")
            regime = cliente.get("regime", "Simples Nacional")
            
            if cliente_id is None:
                continue
            
            # Filtrar obrigações do regime do cliente
            obrigacoes_regime = [o for o in config_obrigacoes if o.get("regime") == regime]
            
            # Se não houver obrigações específicas do regime, usar obrigações padrão
            if not obrigacoes_regime:
                obrigacoes_regime = OBRIGACOES_PADRAO
            
            # Preparar tarefas para bulk insert
            for obr in obrigacoes_regime:
                key = (cliente_id, obr["obrigacao"], mes, ano)
                if key not in existentes:
                    novas_tarefas.append({
                        "cliente_id": cliente_id,
                        "obrigacao": obr["obrigacao"],
                        "vencimento": obr.get("prazo", ""),
                        "periodicidade": obr.get("periodicidade", "Mensal"),
                        "mes": mes,
                        "ano": ano,
                        "alerta": "✅ Normal",
                        "status": "Pendente"
                    })
                    inseridas += 1
        
        # Bulk insert
        if novas_tarefas:
            supabase.table("tarefas").insert(novas_tarefas).execute()
        
        return {"sucesso": True, "mensagem": f"{inseridas} obrigações geradas com sucesso.", "inseridas": inseridas}
    
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao gerar obrigações: {e}", "inseridas": 0}

# ============================================================================
# MÓDULO: VISUALIZAÇÕES - DASHBOARD
# ============================================================================

def render_dashboard():
    st.title("🐴 📊 V-Controll Hub - Painel de Controle")
    st.markdown("Bem-vindo(a) ao centro de monitoramento integrado da Vieira Controller. Acompanhe clientes, tarefas e documentos em tempo real.")

    hoje = datetime.now()
    mes_atual = LISTA_MESES[hoje.month - 1]
    ano_atual = str(hoje.year)

    if st.button("⚙️ Gerar Obrigações do Mês Atual", key="gerar_obrigacoes_dashboard"):
        resultado = gerar_obrigacoes_mes(mes_atual, ano_atual)
        if resultado["sucesso"]:
            st.success(resultado["mensagem"])
            st.rerun()
        else:
            st.warning(resultado["mensagem"])

    clientes = carregar_clientes()
    tarefas = carregar_tarefas()
    documentos_fixos = carregar_documentos_fixos()
    arquivos = carregar_arquivos_escritorio()

    df_clientes = df_from_data(clientes)
    df_tarefas = df_from_data(tarefas)
    df_documentos_fixos = df_from_data(documentos_fixos)
    df_arquivos = df_from_data(arquivos)

    # --- FILTROS DINÂMICOS ---
    f1, f2, f3, f4 = st.columns(4)

    cliente_options = ["Todos os Clientes"] + (df_clientes['nome'].tolist() if not df_clientes.empty else [])
    obrig_options = ["Todas as Obrigações"] + (sorted(df_tarefas['obrigacao'].dropna().unique().tolist()) if not df_tarefas.empty else [])

    cliente_sel = f1.selectbox("Filtrar por Cliente:", cliente_options)
    obrigacao_sel = f2.selectbox("Filtrar por Obrigação:", obrig_options)
    mes_sel = f3.selectbox("Filtrar por Mês:", LISTA_MESES, index=LISTA_MESES.index(mes_atual))
    ano_sel = f4.selectbox("Filtrar por Ano:", LISTA_ANOS, index=LISTA_ANOS.index(ano_atual) if ano_atual in LISTA_ANOS else 0)

    # Prepare fused dataframe
    if not df_tarefas.empty and not df_clientes.empty:
        df_fused = df_tarefas.merge(df_clientes[["id", "nome"]], left_on="cliente_id", right_on="id", how="left")
    else:
        df_fused = pd.DataFrame()

    # Apply filters
    if not df_fused.empty:
        df_filtered = df_fused[(df_fused['mes'] == mes_sel) & (df_fused['ano'] == ano_sel)].copy()
        if cliente_sel != "Todos os Clientes":
            df_filtered = df_filtered[df_filtered['nome'] == cliente_sel]
        if obrigacao_sel != "Todas as Obrigações":
            df_filtered = df_filtered[df_filtered['obrigacao'] == obrigacao_sel]
    else:
        df_filtered = pd.DataFrame()

    # Métricas
    total_clientes = int(df_filtered['cliente_id'].nunique()) if not df_filtered.empty else 0
    tarefas_pendentes = int(df_filtered[df_filtered['status'] == 'Pendente'].shape[0]) if not df_filtered.empty else 0
    tarefas_concluidas = int(df_filtered[df_filtered['status'] == 'Concluído'].shape[0]) if not df_filtered.empty else 0

    # Documentos processados
    if not df_arquivos.empty:
        df_arquivos_filtr = df_arquivos[(df_arquivos['mes'] == mes_sel) & (df_arquivos['ano'] == ano_sel)]
        if cliente_sel != "Todos os Clientes":
            cliente_id_sel = int(df_clientes[df_clientes['nome'] == cliente_sel]['id'].iloc[0]) if not df_clientes.empty else None
            if cliente_id_sel is not None:
                df_arquivos_filtr = df_arquivos_filtr[df_arquivos_filtr['cliente_id'] == cliente_id_sel]
        count_mensais = len(df_arquivos_filtr)
    else:
        count_mensais = 0

    if not df_documentos_fixos.empty:
        if cliente_sel != "Todos os Clientes":
            cliente_id_sel = int(df_clientes[df_clientes['nome'] == cliente_sel]['id'].iloc[0]) if not df_clientes.empty else None
            if cliente_id_sel is not None:
                count_fixos = len(df_documentos_fixos[df_documentos_fixos['cliente_id'] == cliente_id_sel])
            else:
                count_fixos = 0
        else:
            count_fixos = len(df_documentos_fixos)
    else:
        count_fixos = 0

    documentos_processados = count_mensais + count_fixos

    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes (filtrados)", total_clientes, delta=None)
    col2.metric("Tarefas pendentes", tarefas_pendentes, delta=None)
    col3.metric("Tarefas concluídas", tarefas_concluidas, delta=None)

    col4, col5, col6 = st.columns(3)
    col4.metric("Documentos processados", documentos_processados, delta=None)
    col5.metric("Mês", mes_sel, delta=None)
    col6.metric("Ano", ano_sel, delta=None)

    st.markdown("---")

    # --- GRÁFICOS (Plotly) ---
    if df_filtered.empty:
        st.info("Nenhuma obrigação encontrada para os filtros selecionados.")
    else:
        g1, g2 = st.columns(2)

        # Pie/Donut - status distribution
        with g1:
            status_counts = df_filtered['status'].fillna('Sem status').value_counts().reset_index()
            status_counts.columns = ['Status', 'Quantidade']
            color_map = {
                'Concluído': PALETA_AZUL['primary'],
                'Pendente': PALETA_AZUL['secondary'],
                'Atrasado': '#003a7a',
                'Sem status': PALETA_AZUL['muted']
            }
            fig_pie = px.pie(
                status_counts,
                names='Status',
                values='Quantidade',
                title='Status das Obrigações',
                hole=0.4,
                color_discrete_sequence=[color_map.get(s, PALETA_AZUL['muted']) for s in status_counts['Status']]
            )
            fig_pie.update_layout(
                plot_bgcolor=PALETA_AZUL['background'],
                paper_bgcolor=PALETA_AZUL['background'],
                font_color=PALETA_AZUL['text'],
                title_font_color=PALETA_AZUL['primary'],
                legend_title_font_color=PALETA_AZUL['primary']
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Bar chart
        with g2:
            if cliente_sel == "Todos os Clientes":
                df_group = df_filtered.groupby('nome').size().reset_index(name='Quantidade')
                fig_bar = px.bar(
                    df_group,
                    x='nome',
                    y='Quantidade',
                    title='Obrigações por Cliente',
                    text='Quantidade',
                    color_discrete_sequence=[PALETA_AZUL['primary'], PALETA_AZUL['secondary']]
                )
            else:
                df_group = df_filtered.groupby('obrigacao').size().reset_index(name='Quantidade')
                fig_bar = px.bar(
                    df_group,
                    x='obrigacao',
                    y='Quantidade',
                    title='Obrigações por Tipo',
                    text='Quantidade',
                    color_discrete_sequence=[PALETA_AZUL['primary'], PALETA_AZUL['secondary']]
                )
            fig_bar.update_layout(
                xaxis_tickangle=-45,
                height=360,
                plot_bgcolor=PALETA_AZUL['background'],
                paper_bgcolor=PALETA_AZUL['background'],
                font_color=PALETA_AZUL['text'],
                title_font_color=PALETA_AZUL['primary']
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown("### Últimas tarefas cadastradas")
    if not df_tarefas.empty and not df_clientes.empty:
        df_exibicao = df_tarefas.merge(df_clientes[["id", "nome"]], left_on="cliente_id", right_on="id", how="left")
        df_exibicao = df_exibicao[["nome", "obrigacao", "periodicidade", "mes", "ano", "vencimento", "status"]]
        df_exibicao.columns = ["Cliente", "Obrigação", "Periodicidade", "Mês", "Ano", "Prazo", "Status"]
        st.dataframe(df_exibicao.sort_values(by=["Ano", "Mês"], ascending=False).head(10), use_container_width=True)

        tarefas_pendentes = df_tarefas[df_tarefas["status"] == "Pendente"]
        if not tarefas_pendentes.empty:
            tarefas_pendentes = tarefas_pendentes.merge(
                df_clientes[["id", "nome"]],
                left_on="cliente_id",
                right_on="id",
                how="left",
                suffixes=("", "_cliente")
            )
            tarefa_options = {}
            if not tarefas_pendentes.empty:
                for _, row in tarefas_pendentes.iterrows():
                    cliente = row.get('Cliente', row.get('nome', ''))
                    obrigacao = row.get('Obrigação', row.get('obrigacao', ''))
                    mes = row.get('Mês', row.get('mes', ''))
                    t_id = row.get('id', row.get('ID', None))
                    if t_id is not None:
                        label = f"{cliente} - {obrigacao} ({mes})"
                        tarefa_options[label] = t_id

            st.subheader("⚙️ Gerenciar e Concluir Obrigações")
            if tarefa_options:
                selected_tarefa = st.selectbox("Selecione a obrigação pendente:", list(tarefa_options.keys()))
                if st.button("✅ Marcar como Concluída"):
                    tarefa_id = tarefa_options[selected_tarefa]
                    supabase.table("tarefas").update({"status": "Concluído"}).eq("id", int(tarefa_id)).execute()
                    st.success("Obrigação concluída com sucesso!")
                    st.rerun()
            else:
                st.info("Não há obrigações pendentes encontradas com dados de ID válidos.")
        else:
            st.info("Não há obrigações pendentes para concluir no momento.")
    else:
        st.info("Cadastre um cliente e suas obrigações para começar a preencher o painel.")

# ============================================================================
# MÓDULO: VISUALIZAÇÕES - DOCUMENTOS
# ============================================================================

def render_upload_documentos():
    st.subheader("📤 Enviar Documentos para Clientes")
    st.markdown("Use este formulário para enviar arquivos mensais e fixos diretamente para os clientes.")

    clientes = carregar_clientes()
    if not clientes:
        st.warning("Cadastre ao menos um cliente antes de enviar documentos.")
        return

    tipo_envio = st.selectbox("Que tipo de documento deseja enviar?", [
        "Documento Mensal (Guias, Impostos, Movimentos)",
        "Documento Fixo (Contrato Social, CNPJ, Inscrição Estadual)"
    ])

    cliente_selecionado = st.selectbox("Selecione o Cliente:", [c["nome"] for c in clientes])
    id_cliente = next(c["id"] for c in clientes if c["nome"] == cliente_selecionado)

    if tipo_envio == "Documento Mensal (Guias, Impostos, Movimentos)":
        mes_comp = st.selectbox("Mês:", LISTA_MESES, index=datetime.now().month - 1)
        ano_comp = st.selectbox("Ano:", LISTA_ANOS, index=1)
        arquivo_upload = st.file_uploader("Arquivo (PDF/XML/XLSX):", type=["pdf", "xml", "zip", "xlsx"])

        if st.button("Enviar Mensal"):
            if not arquivo_upload:
                st.error("Anexe um arquivo antes de enviar.")
            else:
                nome_limpo = f"{id_cliente}_{ano_comp}_{mes_comp}_{int(datetime.now().timestamp())}_{arquivo_upload.name}"
                caminho_storage = f"guias/{nome_limpo}"
                supabase.storage.from_("documentos-clientes").upload(
                    path=caminho_storage,
                    file=arquivo_upload.getvalue(),
                    file_options={"content-type": arquivo_upload.type}
                )
                supabase.table("arquivos_escritorio").insert({
                    "cliente_id": id_cliente,
                    "ano": ano_comp,
                    "mes": mes_comp,
                    "nome_arquivo": arquivo_upload.name,
                    "caminho_storage": caminho_storage,
                    "data_publicacao": datetime.now().strftime("%d/%m/%Y %H:%M")
                }).execute()
                st.success("Documento mensal enviado e salvo na tabela arquivos_escritorio.")

    else:
        descricao_doc = st.text_input("Nome/Descrição do documento", help="Ex: Contrato Social Consolidado")
        arquivo_upload = st.file_uploader("Arquivo (PDF/JPG/PNG):", type=["pdf", "jpg", "png"])

        if st.button("Enviar Fixo"):
            if not arquivo_upload:
                st.error("Anexe um arquivo antes de enviar.")
            elif not descricao_doc:
                st.error("Informe a descrição do documento fixo.")
            else:
                nome_limpo = f"{id_cliente}_{int(datetime.now().timestamp())}_{arquivo_upload.name}"
                caminho_storage = f"documentos/{nome_limpo}"
                supabase.storage.from_("documentos-fixos").upload(
                    path=caminho_storage,
                    file=arquivo_upload.getvalue(),
                    file_options={"content-type": arquivo_upload.type}
                )
                supabase.table("documentos_fixos").insert({
                    "cliente_id": id_cliente,
                    "tipo_documento": descricao_doc,
                    "nome_arquivo": arquivo_upload.name,
                    "caminho_storage": caminho_storage
                }).execute()
                st.success("Documento fixo enviado e salvo na tabela documentos_fixos.")

# ============================================================================
# MÓDULO: VISUALIZAÇÕES - CADASTRO
# ============================================================================

def render_cadastrar_cliente():
    st.title("➕ Cadastro de Cliente e Acesso")
    st.markdown("Registre o cliente e crie o usuário de acesso do cliente em um único fluxo.")

    if "empresa_nome" not in st.session_state:
        st.session_state["empresa_nome"] = ""
        st.session_state["empresa_cnpj"] = ""
        st.session_state["empresa_ie"] = ""
        st.session_state["empresa_email"] = ""
        st.session_state["empresa_telefone"] = ""
        st.session_state["empresa_regime"] = "Simples Nacional"
        st.session_state["empresa_socios"] = ""
        st.session_state["empresa_tem_folha"] = False
        st.session_state["usuario_nome"] = ""
        st.session_state["usuario_email"] = ""
        st.session_state["usuario_senha"] = ""

    with st.form("form_cadastro_cliente", clear_on_submit=True):
        st.subheader("Dados da Empresa")
        nome = st.text_input("Razão Social / Nome Fantasia", key="empresa_nome")
        email_empresa = st.text_input("E-mail institucional", key="empresa_email")
        telefone = st.text_input("Telefone", key="empresa_telefone")

        col1, col2 = st.columns(2)
        with col1:
            cnpj = st.text_input("CNPJ", key="empresa_cnpj")
        with col2:
            ie = st.text_input("Inscrição Estadual (IE)", key="empresa_ie")

        regime = st.selectbox("Regime Tributário", ["Simples Nacional", "Lucro Presumido", "Lucro Real"], key="empresa_regime")
        socios = st.text_area("Sócios", key="empresa_socios")
        tem_folha = st.checkbox("Possui folha de pagamento?", key="empresa_tem_folha")

        st.markdown("---")
        st.subheader("Dados de Acesso do Cliente")
        usuario_nome = st.text_input("Nome do usuário responsável", key="usuario_nome")
        usuario_email = st.text_input("E-mail de Login", key="usuario_email")
        usuario_senha = st.text_input("Senha de Acesso inicial", type="password", key="usuario_senha")

        if st.form_submit_button("Salvar Cadastro"):
            if not nome or not cnpj or not ie:
                st.error("Por favor, preencha Razão Social, CNPJ e Inscrição Estadual.")
            elif not usuario_nome or not usuario_email or not usuario_senha:
                st.error("Por favor, preencha os dados de acesso do cliente.")
            else:
                try:
                    ins_res = supabase.table("clientes").insert({
                        "nome": nome,
                        "cnpj": cnpj,
                        "inscricao_estadual": ie,
                        "regime": regime,
                        "email": email_empresa,
                        "telefone": telefone,
                        "socios": socios,
                        "tem_folha": tem_folha,
                        "status_cadastro": "Ativo"
                    }).execute()

                    if not ins_res.data or len(ins_res.data) == 0:
                        raise ValueError("Falha ao criar o cliente no Supabase.")

                    cliente_id = ins_res.data[0]["id"]
                    supabase.table("usuarios_clientes").insert({
                        "cliente_id": cliente_id,
                        "email": usuario_email,
                        "senha": usuario_senha,
                        "perfil": "cliente"
                    }).execute()

                    for ob in OBRIGACOES_BASE[regime]:
                        supabase.table("tarefas").insert({
                            "cliente_id": cliente_id,
                            "obrigacao": ob["obrigacao"],
                            "vencimento": ob["prazo"],
                            "periodicidade": ob["periodicidade"],
                            "mes": LISTA_MESES[datetime.now().month - 1],
                            "ano": str(datetime.now().year),
                            "alerta": "✅ Normal",
                            "status": "Pendente"
                        }).execute()

                    st.success("Cliente e Usuário de Acesso criados com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar cadastro: {e}")

# ============================================================================
# MÓDULO: VISUALIZAÇÕES - GERENCIAR OBRIGAÇÕES
# ============================================================================

def render_gerenciar_obrigacoes():
    st.title("🗂️ Gerenciar Obrigações (Contador)")
    st.markdown("Use este formulário para cadastrar as obrigações de cada cliente diretamente na tabela de tarefas.")

    clientes = carregar_clientes()
    if not clientes:
        st.warning("Cadastre ao menos um cliente antes de lançar obrigações.")
        return

    with st.form("form_gerenciar_obrigacoes"):
        cliente_selecionado = st.selectbox("Selecione o Cliente:", [c["nome"] for c in clientes])
        nome_ob = st.text_input("Nome da Obrigação (ex: DAS - Simples Nacional, DCTFWeb, FGTS / SEFIP, Folha de Pagamento)")
        col1, col2 = st.columns(2)
        with col1:
            mes_comp = st.selectbox("Mês de Competência:", LISTA_MESES, index=datetime.now().month - 1)
        with col2:
            ano_comp = st.selectbox("Ano de Competência:", LISTA_ANOS, index=1)
        vencimento = st.date_input("Data de Vencimento")
        periodicidade = st.selectbox("Periodicidade:", ["Mensal", "Trimestral", "Anual", "Eventual"], index=0)

        if st.form_submit_button("Cadastrar Obrigação"):
            if not nome_ob:
                st.error("Preencha o nome da obrigação.")
            else:
                cliente_id = next(c["id"] for c in clientes if c["nome"] == cliente_selecionado)
                supabase.table("tarefas").insert({
                    "cliente_id": cliente_id,
                    "obrigacao": nome_ob,
                    "vencimento": vencimento.strftime("%Y-%m-%d"),
                    "periodicidade": periodicidade,
                    "mes": mes_comp,
                    "ano": ano_comp,
                    "alerta": "✅ Normal",
                    "status": "Pendente"
                }).execute()
                st.success("Obrigação cadastrada com sucesso.")

# ============================================================================
# MÓDULO: VISUALIZAÇÕES - CONFIGURAR ACESSOS
# ============================================================================

def render_configurar_acessos():
    st.title("🔑 Gerenciamento de Acessos")
    st.markdown("Associe credenciais aos clientes e controle o perfil de acesso.")

    clientes = carregar_clientes()
    if not clientes:
        st.warning("Cadastre ao menos um cliente antes de liberar acessos.")
        return

    with st.form("form_acesso"):
        cliente_selecionado = st.selectbox("Cliente:", [c["nome"] for c in clientes])
        email = st.text_input("E-mail/Usuário de Login")
        senha = st.text_input("Senha Provisória", type="password")
        perfil = st.selectbox("Perfil de Acesso:", ["cliente", "administrador"])

        if st.form_submit_button("Gerar Usuário"):
            if not email or not senha:
                st.error("Preencha e-mail e senha para liberar o acesso.")
            else:
                cliente_id = next(c["id"] for c in clientes if c["nome"] == cliente_selecionado)
                supabase.table("usuarios_clientes").insert({
                    "cliente_id": cliente_id,
                    "email": email,
                    "senha": senha,
                    "perfil": perfil
                }).execute()
                st.success("Acesso criado com sucesso.")

    st.markdown("---")
    st.markdown("### Acessos já cadastrados")
    acessos = carregar_acessos()
    if acessos:
        for acesso in acessos:
            cliente_nome = acesso.get("clientes", {}).get("nome", "-") if acesso.get("clientes") else "-"
            st.write(f"Usuário: **{acesso['email']}** | Cliente: **{cliente_nome}** | Perfil: **{acesso.get('perfil', 'cliente')}**")
    else:
        st.info("Nenhum acesso registrado ainda.")

# ============================================================================
# MÓDULO: VISUALIZAÇÕES - BASE DE CLIENTES (COM CORREÇÃO DE APIError)
# ============================================================================

def render_base_clientes():
    st.title("👥 Base de Clientes")
    st.markdown("Visualize a base de clientes, regimes tributários e credenciais de acesso. Atualize senhas de clientes diretamente daqui.")

    try:
        res_usuarios = supabase.table("usuarios_clientes").select("*").execute()
        df_usuarios = pd.DataFrame(res_usuarios.data or [])

        res_clientes = supabase.table("clientes").select("*").execute()
        df_clientes = pd.DataFrame(res_clientes.data or [])

        if not df_usuarios.empty and not df_clientes.empty:
            col_ligacao = 'cliente_id' if 'cliente_id' in df_usuarios.columns else 'id_cliente' if 'id_cliente' in df_usuarios.columns else None

            if col_ligacao:
                df_final = pd.merge(df_usuarios, df_clientes, left_on=col_ligacao, right_on='id', suffixes=('_user', '_empresa'))
                if 'nome' in df_final.columns:
                    df_final['empresa'] = df_final['nome']
                elif 'nome_empresa' in df_final.columns:
                    df_final['empresa'] = df_final['nome_empresa']
                else:
                    df_final['empresa'] = '-'

                if 'regime' not in df_final.columns and 'regime_empresa' in df_final.columns:
                    df_final['regime'] = df_final['regime_empresa']

                if 'status_cadastro' not in df_final.columns and 'status_cadastro_empresa' in df_final.columns:
                    df_final['status_cadastro'] = df_final['status_cadastro_empresa']

                df_final['status_cadastro'] = df_final['status_cadastro'].fillna('Ativo') if 'status_cadastro' in df_final.columns else 'Ativo'

                df_ativos = df_final[df_final['status_cadastro'] == 'Ativo']
                df_inativos = df_final[df_final['status_cadastro'] == 'Inativo']

                display_cols = [c for c in ['id_empresa', 'nome', 'cnpj', 'regime', 'email_user', 'status_cadastro'] if c in df_final.columns]
                if 'nome' not in display_cols and 'nome_empresa' in df_final.columns:
                    display_cols.insert(1, 'nome_empresa')

                st.subheader('🟢 Clientes Ativos')
                st.dataframe(df_ativos[display_cols], use_container_width=True)

                st.subheader('🔴 Clientes Inativos')
                st.dataframe(df_inativos[display_cols], use_container_width=True)
            else:
                st.warning("Coluna de vínculo entre tabelas não encontrada automaticamente. Exibindo dados brutos:")
                st.dataframe(df_usuarios)
        else:
            st.info("Nenhum registro encontrado para realizar a listagem.")
    except Exception as e:
        st.error(f"Erro ao processar tabelas: {e}")

    st.markdown("---")
    st.subheader("Mudar Status do Cliente")

    if 'df_final' in locals() and not df_final.empty:
        lista_empresas = df_final['empresa'].astype(str).unique().tolist()
    else:
        clientes = carregar_clientes()
        lista_empresas = [c['nome'] for c in clientes]

    if not lista_empresas:
        st.warning("Cadastre ao menos um cliente antes de atualizar o status.")
        return

    with st.form('form_status_cliente'):
        empresa_selecionada = st.selectbox('Selecione o Cliente:', options=lista_empresas)
        novo_status = st.radio('Status de Cadastro:', ['Ativo', 'Inativo'], index=0)
        salvar_status = st.form_submit_button('Salvar Status')

        if 'df_final' in locals() and not df_final.empty:
            matching = df_final[df_final['empresa'] == empresa_selecionada]
            if matching.empty:
                st.error('Cliente selecionado não encontrado na base consolidada.')
                st.stop()
            
            # CORREÇÃO DO APIError: Usar .item() e int() para garantir tipo Python puro
            try:
                id_cliente_correto = df_final[df_final['empresa'] == empresa_selecionada]['id_empresa'].values[0].item()
                id_cliente_correto = int(id_cliente_correto)
            except Exception as e:
                st.error(f"Erro ao identificar o ID da empresa: {e}")
                id_cliente_correto = None
        else:
            try:
                id_cliente_correto = int(next(c['id'] for c in clientes if c['nome'] == empresa_selecionada))
            except Exception as e:
                st.error(f"Erro ao identificar o ID da empresa: {e}")
                id_cliente_correto = None

        if id_cliente_correto is not None and salvar_status:
            try:
                supabase.table('clientes').update({'status_cadastro': novo_status}).eq('id', id_cliente_correto).execute()
                if novo_status == 'Inativo':
                    supabase.table('tarefas').delete().eq('cliente_id', id_cliente_correto).eq('status', 'Pendente').execute()
                st.success('Status atualizado com sucesso!')
                st.rerun()
            except Exception as error:
                st.error(f'Erro técnico ao comunicar com o Supabase: {error}')

# ============================================================================
# MÓDULO: VISUALIZAÇÕES - OBRIGAÇÕES CUSTOMIZADAS
# ============================================================================

def render_obrigacoes_customizadas():
    st.title("⚙️ Obrigações Customizadas")
    st.markdown("Crie obrigações manuais específicas para clientes e mantenha o painel atualizado.")

    clientes = carregar_clientes()
    if not clientes:
        st.warning("Cadastre ao menos um cliente antes de lançar obrigações customizadas.")
        return

    with st.form("form_custom"):
        cliente_selecionado = st.selectbox("Selecione o Cliente:", [c["nome"] for c in clientes])
        nome_ob = st.text_input("Nome do Imposto/Obrigação")
        descricao_ob = st.text_area("Descrição da Obrigação")
        prazo_ob = st.text_input("Vencimento por extenso")
        periodicidade_ob = st.selectbox("Periodicidade:", ["Mensal", "Trimestral", "Anual", "Eventual"], index=3)
        mes_ob = st.selectbox("Mês:", LISTA_MESES, index=datetime.now().month - 1)
        ano_ob = st.selectbox("Ano:", LISTA_ANOS, index=1)
        alerta_ob = st.selectbox("Prioridade:", ["🚨 Urgente", "⚠️ Atenção", "✅ Normal"])

        if st.form_submit_button("Lançar no Painel"):
            if not nome_ob or not descricao_ob or not prazo_ob:
                st.error("Preencha nome, descrição e prazo da obrigação.")
            else:
                cliente_id = next(c["id"] for c in clientes if c["nome"] == cliente_selecionado)
                supabase.table("tarefas").insert({
                    "cliente_id": cliente_id,
                    "obrigacao": nome_ob,
                    "descricao": descricao_ob,
                    "vencimento": prazo_ob,
                    "periodicidade": periodicidade_ob,
                    "mes": mes_ob,
                    "ano": ano_ob,
                    "alerta": alerta_ob,
                    "status": "Pendente"
                }).execute()
                st.success("Obrigação customizada adicionada ao painel.")

# ============================================================================
# MÓDULO: VISUALIZAÇÕES - CONSULTA RÁPIDA DE LOGINS (NOVO)
# ============================================================================

def render_consulta_logins():
    """
    Seção nova para a Fernanda consultar rapidamente os e-mails de acesso
    criados para os clientes na tabela 'usuarios_clientes'.
    """
    st.title("🔐 Consulta Rápida de Acessos de Clientes")
    st.markdown("Ferramenta para consulta ágil de e-mails e credenciais de acesso dos clientes.")
    
    try:
        acessos = carregar_acessos()
        clientes = carregar_clientes()
        
        if not acessos:
            st.info("Nenhum acesso de cliente registrado ainda.")
            return
        
        # Criar dataframe com os acessos
        df_acessos = pd.DataFrame(acessos)
        
        # Consolidar com dados de clientes
        df_clientes = pd.DataFrame(clientes)
        if not df_clientes.empty:
            df_consolidado = df_acessos.merge(
                df_clientes[['id', 'nome', 'cnpj', 'regime']],
                left_on='cliente_id',
                right_on='id',
                how='left',
                suffixes=('_acesso', '_cliente')
            )
        else:
            df_consolidado = df_acessos.copy()
        
        # Opção de filtro
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            filtro_cliente = st.text_input("🔍 Filtrar por Nome do Cliente:", placeholder="Digite o nome do cliente...")
        
        with col_filtro2:
            filtro_email = st.text_input("✉️ Filtrar por E-mail:", placeholder="Digite o e-mail...")
        
        # Aplicar filtros
        df_exibicao = df_consolidado.copy()
        
        if filtro_cliente:
            df_exibicao = df_exibicao[df_exibicao['nome'].astype(str).str.contains(filtro_cliente, case=False, na=False)]
        
        if filtro_email:
            df_exibicao = df_exibicao[df_exibicao['email'].astype(str).str.contains(filtro_email, case=False, na=False)]
        
        # Selecionar colunas para exibição
        colunas_exibicao = []
        if 'nome' in df_exibicao.columns:
            colunas_exibicao.append('nome')
        if 'cnpj' in df_exibicao.columns:
            colunas_exibicao.append('cnpj')
        if 'regime' in df_exibicao.columns:
            colunas_exibicao.append('regime')
        if 'email' in df_exibicao.columns:
            colunas_exibicao.append('email')
        if 'perfil' in df_exibicao.columns:
            colunas_exibicao.append('perfil')
        
        # Renomear colunas para melhor legibilidade
        df_exibir = df_exibicao[colunas_exibicao].copy()
        df_exibir.columns = ['Cliente', 'CNPJ', 'Regime', 'E-mail de Acesso', 'Perfil']
        
        # Exibir com st.dataframe para melhor visualização
        st.markdown("### 📋 Lista de Acessos de Clientes")
        st.dataframe(df_exibir, use_container_width=True)
        
        # Estatísticas rápidas
        st.markdown("---")
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            total_acessos = len(df_exibicao)
            st.metric("Total de Acessos", total_acessos)
        
        with col_stats2:
            acessos_clientes = len(df_exibicao[df_exibicao['perfil'] == 'cliente']) if 'perfil' in df_exibicao.columns else 0
            st.metric("Acessos de Clientes", acessos_clientes)
        
        with col_stats3:
            clientes_unicos = df_exibicao['cliente_id'].nunique() if 'cliente_id' in df_exibicao.columns else 0
            st.metric("Clientes Únicos", clientes_unicos)
        
        # Exportação (opcional)
        st.markdown("---")
        if st.button("📥 Exportar para CSV"):
            csv = df_exibir.to_csv(index=False)
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name="acessos_clientes.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Erro ao carregar dados de acessos: {e}")

# ============================================================================
# MÓDULO: PORTAL CLIENTE
# ============================================================================

def render_portal_cliente():
    cli_res = supabase.table("clientes").select("*").eq("id", st.session_state.cliente_id_logado).execute()
    if not cli_res.data:
        st.error("Cliente não encontrado.")
        return

    cliente = cli_res.data[0]
    st.title(f"👤 Portal do Cliente - {cliente['nome']}")
    st.markdown("Acesse seus documentos fixos e guias mensais com filtros claros por competência.")

    tab_fixos, tab_mensais = st.tabs(["📁 Documentos Fixos", "📅 Guias e Impostos Mensais"])

    with tab_fixos:
        docs_fixos = supabase.table("documentos_fixos").select("*").eq("cliente_id", cliente["id"]).execute().data or []
        if docs_fixos:
            df_fixos = pd.DataFrame(docs_fixos)
            df_fixos_exib = df_fixos[["tipo_documento", "nome_arquivo"]].rename(columns={"tipo_documento": "Descrição", "nome_arquivo": "Arquivo"})
            st.dataframe(df_fixos_exib, use_container_width=True)
            st.markdown("---")
            for doc in docs_fixos:
                try:
                    assinatura = supabase.storage.from_("documentos-fixos").create_signed_url(doc["caminho_storage"], 60)
                    st.markdown(f"- **{doc['tipo_documento']}** — {doc['nome_arquivo']} — <a href=\"{assinatura['signedUrl']}\" target=\"_blank\">Abrir / Baixar</a>", unsafe_allow_html=True)
                except Exception:
                    st.markdown(f"- **{doc['tipo_documento']}** — {doc['nome_arquivo']} — Erro ao gerar link")
        else:
            st.info("Nenhum documento fixo encontrado.")

    with tab_mensais:
        col_a, col_b = st.columns(2)
        with col_a:
            mes_filtrado = st.selectbox("Mês:", ["Todos"] + LISTA_MESES, index=datetime.now().month)
        with col_b:
            ano_filtrado = st.selectbox("Ano:", ["Todos"] + LISTA_ANOS, index=1)

        query = supabase.table("arquivos_escritorio").select("*").eq("cliente_id", cliente["id"])
        if mes_filtrado != "Todos":
            query = query.eq("mes", mes_filtrado)
        if ano_filtrado != "Todos":
            query = query.eq("ano", ano_filtrado)

        arquivos = query.execute().data or []
        if arquivos:
            df_arquivos = pd.DataFrame(arquivos)
            df_arquivos_exib = df_arquivos[["ano", "mes", "nome_arquivo", "data_publicacao"]].rename(columns={"ano": "Ano", "mes": "Mês", "nome_arquivo": "Arquivo", "data_publicacao": "Data de Publicação"})
            st.dataframe(df_arquivos_exib, use_container_width=True)
            st.markdown("---")
            for arq in arquivos:
                try:
                    assinatura = supabase.storage.from_("documentos-clientes").create_signed_url(arq["caminho_storage"], 60)
                    st.markdown(f"- **{arq['nome_arquivo']}** ({arq['mes']}/{arq['ano']}) — <a href=\"{assinatura['signedUrl']}\" target=\"_blank\">Baixar</a>", unsafe_allow_html=True)
                except Exception:
                    st.markdown(f"- **{arq['nome_arquivo']}** ({arq['mes']}/{arq['ano']}) — Erro ao gerar link")
        else:
            st.warning("Nenhum guia ou imposto mensal disponível para a competência selecionada.")

    st.markdown("---")
    st.subheader("🔒 Segurança da Conta")
    with st.form("form_alterar_senha_cliente"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmação da Nova Senha", type="password")
        if st.form_submit_button("Alterar Senha"):
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.error("Preencha todos os campos de senha.")
            elif nova_senha != confirmar_senha:
                st.error("A confirmação da nova senha não confere.")
            else:
                acesso_res = supabase.table("usuarios_clientes").select("*").eq("cliente_id", cliente["id"]).eq("perfil", "cliente").execute()
                if not acesso_res.data:
                    st.error("Não foi possível encontrar seus dados de acesso.")
                elif acesso_res.data[0].get("senha") != senha_atual:
                    st.error("Senha atual incorreta.")
                else:
                    supabase.table("usuarios_clientes").update({"senha": nova_senha}).eq("id", acesso_res.data[0]["id"]).execute()
                    st.success("Senha alterada com sucesso!")
                    st.rerun()

# ============================================================================
# FLUXO PRINCIPAL - AUTENTICAÇÃO E NAVEGAÇÃO
# ============================================================================

if not st.session_state.logado:
    st.title("🔑 Acesso ao Sistema - 🐴 V-Controll Hub")
    st.markdown("Faça login para acessar o painel de gestão contábil e fiscal.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            usuario = st.text_input("Usuário ou E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                realizar_login(usuario, senha)
else:
    st.sidebar.header("🐴 V-CONTROLL HUB")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Sair / Logout"):
        st.session_state.logado = False
        st.session_state.perfil = None
        st.session_state.cliente_id_logado = None
        st.rerun()

    if st.session_state.perfil == "escritorio":
        opcao = st.sidebar.radio("📑 MENU:", [
            "🏠 Dashboard Geral",
            "📤 Documentos e Tarefas",
            "➕ Cadastrar Cliente",
            "🗂️ Gerenciar Obrigações",
            "⚙️ Obrigações Customizadas",
            "👥 Base de Clientes",
            "🔐 Consulta de Acessos"
        ])

        if opcao == "🏠 Dashboard Geral":
            render_dashboard()
        elif opcao == "📤 Documentos e Tarefas":
            render_upload_documentos()
        elif opcao == "➕ Cadastrar Cliente":
            render_cadastrar_cliente()
        elif opcao == "🗂️ Gerenciar Obrigações":
            render_gerenciar_obrigacoes()
        elif opcao == "⚙️ Obrigações Customizadas":
            render_obrigacoes_customizadas()
        elif opcao == "👥 Base de Clientes":
            render_base_clientes()
        elif opcao == "🔐 Consulta de Acessos":
            render_consulta_logins()
    else:
        st.sidebar.write(f"Conectado como: **CLIENTE**")
        st.sidebar.markdown("---")
        opcao_cliente = st.sidebar.radio("📑 MENU:", [
            "👤 Meu Portal",
            "🚪 Logout"
        ])
        
        if opcao_cliente == "👤 Meu Portal":
            render_portal_cliente()
        elif opcao_cliente == "🚪 Logout":
            st.session_state.logado = False
            st.session_state.perfil = None
            st.session_state.cliente_id_logado = None
            st.rerun()
