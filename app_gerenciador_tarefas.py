import streamlit as st
import pandas as pd
import plotly.express as px
import os
from PIL import Image
from datetime import datetime
from calendar import monthrange
from supabase import create_client, Client
from streamlit_option_menu import option_menu

ADMIN_MASTER_EMAIL = str(st.secrets.get("admin_master_email", "vieiracontroller@gmail.com")).strip().lower()

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

# Oculta globalmente menu nativo do Streamlit em qualquer estado da aplicacao.
st.markdown(
    """
    <style>
    /* Esconde o menu de opções (ícone de 3 pontinhos) e o botão Share */
    [data-testid="stToolbar"] {visibility: hidden !important;}

    /* Esconde o menu principal de edição do Streamlit */
    #MainMenu {visibility: hidden !important;}

    /* Esconde o botão de Deploy / Gerir app (seletores de Cloud e app) */
    .stAppDeployButton,
    [data-testid="stAppDeployButton"],
    [data-testid="stStatusWidget"],
    [data-testid="manage-app-button"] {
        display: none !important;
    }

    /* Mantém sidebar visível sem quebrar navegação */
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
    }

    /* Garante que os controles de sidebar apareçam */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    button[aria-label="Toggle navigation"],
    button[aria-label="Close sidebar"] {
        display: block !important;
        visibility: visible !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
    st.session_state.usuario = None
    st.session_state.usuario_logado_email = None
    st.session_state.escritorio_id = None
    st.session_state.is_admin_master = False

if 'usuario_logado_email' not in st.session_state:
    st.session_state.usuario_logado_email = None
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'escritorio_id' not in st.session_state:
    st.session_state.escritorio_id = None
if 'is_admin_master' not in st.session_state:
    st.session_state.is_admin_master = False


def obter_nome_usuario_ativo() -> str:
    nome_sessao = str(st.session_state.get("usuario") or "").strip()
    if nome_sessao:
        return nome_sessao

    usuario_logado = st.session_state.get("usuario_logado")
    if isinstance(usuario_logado, dict):
        nome_dict = str(usuario_logado.get("nome") or usuario_logado.get("usuario") or "").strip()
        if nome_dict:
            return nome_dict

    return "Conectado"


def escritorio_id_logado():
    return st.session_state.get("escritorio_id")


def garantir_escritorio_id():
    escritorio_id = escritorio_id_logado()
    if escritorio_id is None:
        st.error("Sessao invalida: escritorio_id nao encontrado. Faça login novamente.")
        st.stop()
    return escritorio_id


def obter_escritorio_vieira_id():
    try:
        res = supabase.table("escritorios").select("id,nome,email").execute()
        escritorios = res.data or []
        for escritorio in escritorios:
            nome = str(escritorio.get("nome", "")).strip().lower()
            email = str(escritorio.get("email", "")).strip().lower()
            if "vieira controller" in nome or "vieiracontroller" in nome or "vieiracontroller" in email:
                return escritorio.get("id")
    except Exception:
        return None
    return None


def garantir_usuario_master_vieira():
    """Seed de segurança para garantir o usuário master da Vieira Controller."""
    try:
        escritorio_id = obter_escritorio_vieira_id()
        if escritorio_id is None:
            return

        login_master = "vieiracontroller@gmail.com"
        senha_master = "123456"
        payload_master = {
            "escritorio_id": escritorio_id,
            "usuario": "vieiracontroller",
            "email": login_master,
            "senha": senha_master,
            "perfil": "Master"
        }

        usuario_existente = None
        for campo_busca in ("email", "usuario"):
            try:
                res_usuario = (
                    supabase.table("usuarios_escritorio")
                    .select("id")
                    .eq(campo_busca, login_master if campo_busca == "email" else "vieiracontroller")
                    .eq("escritorio_id", escritorio_id)
                    .limit(1)
                    .execute()
                )
                if res_usuario.data:
                    usuario_existente = res_usuario.data[0]
                    break
            except Exception:
                continue

        if usuario_existente:
            usuario_id = usuario_existente.get("id")
            if usuario_id is not None:
                supabase.table("usuarios_escritorio").update(payload_master).eq("id", int(usuario_id)).execute()
        else:
            supabase.table("usuarios_escritorio").insert(payload_master).execute()
    except Exception:
        return


def realizar_login(usuario, senha):
    garantir_usuario_master_vieira()

    usuario_dados = None
    for campo_busca in ("email", "usuario"):
        try:
            res = (
                supabase.table("usuarios_escritorio")
                .select("*")
                .eq(campo_busca, usuario)
                .eq("senha", senha)
                .limit(1)
                .execute()
            )
            if res.data:
                usuario_dados = res.data[0]
                break
        except Exception:
            continue

    if not usuario_dados and str(usuario).strip().lower() == "vieiracontroller@gmail.com":
        try:
            res = (
                supabase.table("usuarios_escritorio")
                .select("*")
                .eq("senha", senha)
                .limit(1)
                .execute()
            )
            if res.data:
                usuario_dados = res.data[0]
        except Exception:
            usuario_dados = None

    if usuario_dados:
        perfil_banco = str(usuario_dados.get('perfil') or '').strip().lower()
        eh_admin = perfil_banco in {"admin", "master"} or str(usuario_dados.get('email') or '').strip().lower() == ADMIN_MASTER_EMAIL
        st.session_state['usuario_logado'] = usuario_dados
        st.session_state['usuario'] = str(usuario_dados.get('nome') or usuario_dados.get('usuario') or usuario).strip()
        st.session_state['usuario_logado_email'] = str(usuario_dados.get('email') or usuario_dados.get('usuario') or usuario).strip()
        st.session_state['escritorio_id'] = usuario_dados.get('escritorio_id') or usuario_dados.get('id_escritorio') or 1
        st.session_state.logado = True
        st.session_state.perfil = "admin" if eh_admin else "escritorio"
        st.session_state.cliente_id_logado = None
        st.session_state.is_admin_master = eh_admin
        st.success("Login realizado com sucesso!")
        st.rerun()
    else:
        st.error("Usuário ou senha incorretos.")

# ============================================================================
# MÓDULO: FUNÇÕES DE CARREGAMENTO DE DADOS
# ============================================================================

def _avisar_falha_carregamento(chave: str, entidade: str, erro: Exception):
    """Mostra um aviso amigavel apenas uma vez por sessao para evitar ruido na tela."""
    aviso_key = f"_warning_carregamento_{chave}"
    if not st.session_state.get(aviso_key):
        st.session_state[aviso_key] = True
        st.warning(
            f"Nao foi possivel carregar {entidade} no momento. O painel vai seguir funcionando com dados vazios. "
            f"Detalhe tecnico: {erro}"
        )

def carregar_clientes():
    import streamlit as st
    escritorio_id = st.session_state.get('escritorio_id', 1)
    try:
        res = (
            supabase.table("clientes")
            .select("*")
            .eq("escritorio_id", escritorio_id)
            .order("nome")
            .execute()
        )
        return res.data or []
    except Exception as e:
        _avisar_falha_carregamento("clientes", "os clientes", e)
        try:
            res = supabase.table("clientes").select("*").order("nome").execute()
            return res.data or []
        except Exception as fallback_error:
            _avisar_falha_carregamento("clientes_fallback", "os clientes", fallback_error)
            return []


def carregar_tarefas():
    escritorio_id = garantir_escritorio_id()
    try:
        res = supabase.table("tarefas").select("*").eq("escritorio_id", escritorio_id).execute()
        return res.data or []
    except Exception as e:
        _avisar_falha_carregamento("tarefas", "as tarefas", e)
        return []


def carregar_documentos_fixos():
    escritorio_id = garantir_escritorio_id()
    try:
        res = supabase.table("documentos_fixos").select("*, clientes(nome)").eq("escritorio_id", escritorio_id).execute()
        return res.data or []
    except Exception as e:
        _avisar_falha_carregamento("documentos_fixos", "os documentos fixos", e)
        return []


def carregar_arquivos_escritorio():
    escritorio_id = garantir_escritorio_id()
    try:
        res = supabase.table("arquivos_escritorio").select("*").eq("escritorio_id", escritorio_id).execute()
        return res.data or []
    except Exception as e:
        _avisar_falha_carregamento("arquivos_escritorio", "os arquivos do escritorio", e)
        return []


def carregar_acessos():
    try:
        escritorio_id = garantir_escritorio_id()
        res = supabase.table("usuarios_clientes").select("*, clientes(nome)").eq("escritorio_id", escritorio_id).execute()
        return res.data or []
    except Exception as e:
        _avisar_falha_carregamento("acessos", "os acessos dos clientes", e)
        try:
            res = supabase.table("usuarios_clientes").select("*, clientes(nome)").execute()
            return res.data or []
        except Exception as fallback_error:
            _avisar_falha_carregamento("acessos_fallback", "os acessos dos clientes", fallback_error)
            return []


def carregar_config_obrigacoes():
    """Carrega configurações mestras de obrigações do catálogo"""
    try:
        escritorio_id = garantir_escritorio_id()
        res = supabase.table("config_obrigacoes").select("*").eq("escritorio_id", escritorio_id).execute()
        return res.data or []
    except Exception as e:
        _avisar_falha_carregamento("config_obrigacoes", "as configuracoes de obrigacoes", e)
        return []


def carregar_usuarios_escritorio():
    """Carrega usuários internos do escritório"""
    try:
        escritorio_id = garantir_escritorio_id()
        res = supabase.table("usuarios_escritorio").select("*").eq("escritorio_id", escritorio_id).execute()
        return res.data or []
    except Exception as e:
        _avisar_falha_carregamento("usuarios_escritorio", "os usuarios do escritorio", e)
        return []


def df_from_data(data):
    return pd.DataFrame(data) if data else pd.DataFrame()


def to_python_scalar(value):
    return value.item() if hasattr(value, "item") else value


def extrapolar_tarefas_por_mes(df_tarefas, mes, ano):
    if df_tarefas.empty:
        return df_tarefas
    return df_tarefas[(df_tarefas["mes"] == mes) & (df_tarefas["ano"] == ano)]


def carregar_financeiro():
    """Carrega dados financeiros da tabela 'financeiro_mensal'"""
    try:
        escritorio_id = garantir_escritorio_id()
        res = supabase.table("financeiro_mensal").select("*").eq("escritorio_id", escritorio_id).execute()
        return res.data or []
    except Exception as e:
        _avisar_falha_carregamento("financeiro", "os dados financeiros", e)
        return []


def carregar_permissoes_usuario():
    """Carrega permissões de usuários (tabela 'permissoes_usuarios')"""
    try:
        escritorio_id = garantir_escritorio_id()
        res = supabase.table("permissoes_usuarios").select("*").eq("escritorio_id", escritorio_id).execute()
        return res.data or []
    except Exception as e:
        _avisar_falha_carregamento("permissoes_usuario", "as permissoes dos usuarios", e)
        return []


def obter_perfil_usuario(usuario_email):
    """Obtém o perfil (Gestão/Funcionário) de um usuário"""
    try:
        escritorio_id = garantir_escritorio_id()
        res = supabase.table("usuarios_clientes").select("*").eq("email", usuario_email).eq("escritorio_id", escritorio_id).execute()
        if res.data:
            return res.data[0].get("grupo_acesso", "Cliente")
        return "Cliente"
    except Exception:
        return "Cliente"


def render_branding_sidebar():
    try:
        if os.path.exists("logo.png"):
            img_sidebar = Image.open("logo.png")
            st.sidebar.image(img_sidebar, use_container_width=True)
        else:
            st.sidebar.subheader("V-CONTROLL Hub")
    except Exception:
        st.sidebar.subheader("V-CONTROLL Hub")
    st.sidebar.markdown(f"👤 **Usuário:** {obter_nome_usuario_ativo()}")
    st.sidebar.markdown(" ")
    st.sidebar.markdown("---")


def gerar_data_vencimento(ano: str, mes: str, dia: int):
    """Gera data YYYY-MM-DD com ajuste de dia para o limite do mês."""
    try:
        ano_int = int(ano)
        mes_int = LISTA_MESES.index(mes) + 1
        dia_int = int(dia)
        ultimo_dia_mes = monthrange(ano_int, mes_int)[1]
        dia_ajustado = max(1, min(dia_int, ultimo_dia_mes))
        return datetime(ano_int, mes_int, dia_ajustado).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")

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
        escritorio_id = garantir_escritorio_id()
        # Carregar clientes ativos
        clientes_ativos = supabase.table("clientes").select("*").eq("escritorio_id", escritorio_id).eq("status_cadastro", "Ativo").execute().data or []
        
        if not clientes_ativos:
            return {"sucesso": False, "mensagem": "Nenhum cliente ativo encontrado.", "inseridas": 0}
        
        # Carregar config de obrigações
        config_obrigacoes = supabase.table("config_obrigacoes").select("*").eq("escritorio_id", escritorio_id).execute().data or []
        
        if not config_obrigacoes:
            return {"sucesso": False, "mensagem": "Catálogo de obrigações não configurado.", "inseridas": 0}
        
        # Obrigações existentes para não duplicar
        tarefas_existentes = supabase.table("tarefas").select("cliente_id,obrigacao,mes,ano").eq("escritorio_id", escritorio_id).execute().data or []
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
                        "escritorio_id": escritorio_id,
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
    escritorio_id = garantir_escritorio_id()
    st.title("📊 Painel de Controle")

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

    # FILTRO: Apenas clientes ativos
    clientes_ativos = [c for c in clientes if c.get("status_cadastro") == "Ativo"]
    
    df_clientes = df_from_data(clientes_ativos)
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
                    supabase.table("tarefas").update({"status": "Concluído"}).eq("id", int(tarefa_id)).eq("escritorio_id", escritorio_id).execute()
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
    escritorio_id = garantir_escritorio_id()
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
                    "escritorio_id": escritorio_id,
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
                    "escritorio_id": escritorio_id,
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
    escritorio_id = garantir_escritorio_id()
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
        st.session_state["empresa_valor_honorario"] = 0.0
        st.session_state["empresa_dia_vencimento"] = 20
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
        st.subheader("💰 Dados Financeiros")
        
        col_hon1, col_hon2 = st.columns(2)
        with col_hon1:
            valor_honorario = st.number_input("Valor dos Honorários Mensais (R$):", min_value=0.0, step=100.0, format="%.2f", key="empresa_valor_honorario")
        with col_hon2:
            dia_vencimento = st.number_input("Dia de Vencimento (1-31):", min_value=1, max_value=31, value=20, key="empresa_dia_vencimento")

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
                        "escritorio_id": escritorio_id,
                        "nome": nome,
                        "cnpj": cnpj,
                        "inscricao_estadual": ie,
                        "regime": regime,
                        "email": email_empresa,
                        "telefone": telefone,
                        "socios": socios,
                        "tem_folha": tem_folha,
                        "valor_honorario": float(valor_honorario),
                        "dia_vencimento": int(dia_vencimento),
                        "status_cadastro": "Ativo"
                    }).execute()

                    if not ins_res.data or len(ins_res.data) == 0:
                        raise ValueError("Falha ao criar o cliente no Supabase.")

                    cliente_id = ins_res.data[0]["id"]
                    supabase.table("usuarios_clientes").insert({
                        "escritorio_id": escritorio_id,
                        "cliente_id": cliente_id,
                        "email": usuario_email,
                        "senha": usuario_senha,
                        "perfil": "cliente",
                        "grupo_acesso": "Cliente"
                    }).execute()

                    supabase.table("usuarios_clientes").insert({
                        "escritorio_id": escritorio_id,
                        "cliente_id": cliente_id,
                        "nome": usuario_nome,
                        "email": usuario_email,
                        "senha": usuario_senha,
                        "perfil": "cliente"
                    }).execute()

                    for ob in OBRIGACOES_BASE[regime]:
                        supabase.table("tarefas").insert({
                            "escritorio_id": escritorio_id,
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
# MÓDULO: VISUALIZAÇÕES - CENTRAL DE OBRIGAÇÕES (UNIFICADA)
# ============================================================================

def render_central_obrigacoes():
    """
    Tela unificada para gerenciar obrigações automáticas e customizadas.
    Combina: geração automática por mês + criação manual de obrigações avulsas.
    """
    st.title("🗂️ Central de Obrigações")
    escritorio_id = garantir_escritorio_id()
    st.markdown("Gerencie as obrigações do mês e crie obrigações customizadas conforme necessário.")

    clientes = carregar_clientes()
    if not clientes:
        st.warning("Cadastre ao menos um cliente antes de lançar obrigações.")
        return

    hoje = datetime.now()
    mes_atual = LISTA_MESES[hoje.month - 1]
    ano_atual = str(hoje.year)

    # --- SEÇÃO 1: GERAÇÃO AUTOMÁTICA ---
    st.subheader("📋 Geração Automática de Obrigações do Mês")
    st.markdown("Clique para gerar automaticamente as obrigações padrão para todos os clientes ativos neste mês.")
    
    col_gerador1, col_gerador2, col_gerador3 = st.columns([2, 2, 1])
    
    with col_gerador1:
        mes_gerador = st.selectbox("Mês para geração:", LISTA_MESES, index=LISTA_MESES.index(mes_atual), key="mes_gerador")
    
    with col_gerador2:
        ano_gerador = st.selectbox("Ano para geração:", LISTA_ANOS, index=LISTA_ANOS.index(ano_atual) if ano_atual in LISTA_ANOS else 0, key="ano_gerador")
    
    with col_gerador3:
        st.write("")
        if st.button("⚙️ Gerar", key="btn_gerar_obrigacoes"):
            resultado = gerar_obrigacoes_mes(mes_gerador, ano_gerador)
            if resultado["sucesso"]:
                st.success(resultado["mensagem"])
                st.rerun()
            else:
                st.warning(resultado["mensagem"])

    st.markdown("---")

    # --- SEÇÃO 2: OBRIGAÇÃO CUSTOMIZADA/AVULSA ---
    with st.expander("➕ Criar Obrigação Customizada / Avulsa", expanded=False):
        st.markdown("Insira uma obrigação específica ou avulsa para um cliente.")
        
        with st.form("form_obrigacao_customizada"):
            cliente_selecionado = st.selectbox("Selecione o Cliente:", [c["nome"] for c in clientes], key="sel_cliente_custom")
            nome_ob = st.text_input("Nome do Imposto/Obrigação")
            descricao_ob = st.text_area("Descrição da Obrigação (opcional)")
            prazo_ob = st.text_input("Vencimento por extenso (ex: Até o dia 20)")
            
            col1, col2 = st.columns(2)
            with col1:
                periodicidade_ob = st.selectbox("Periodicidade:", ["Mensal", "Trimestral", "Anual", "Eventual"], index=0, key="sel_period_custom")
            with col2:
                alerta_ob = st.selectbox("Prioridade:", ["✅ Normal", "⚠️ Atenção", "🚨 Urgente"], index=0, key="sel_alerta_custom")
            
            col3, col4 = st.columns(2)
            with col3:
                mes_ob = st.selectbox("Mês de Competência:", LISTA_MESES, index=LISTA_MESES.index(mes_atual), key="mes_ob_custom")
            with col4:
                ano_ob = st.selectbox("Ano de Competência:", LISTA_ANOS, index=LISTA_ANOS.index(ano_atual) if ano_atual in LISTA_ANOS else 0, key="ano_ob_custom")

            if st.form_submit_button("Lançar Obrigação Customizada"):
                if not nome_ob or not prazo_ob:
                    st.error("Preencha no mínimo: Nome da Obrigação e Vencimento.")
                else:
                    cliente_id = next(c["id"] for c in clientes if c["nome"] == cliente_selecionado)
                    supabase.table("tarefas").insert({
                        "escritorio_id": escritorio_id,
                        "cliente_id": cliente_id,
                        "obrigacao": nome_ob,
                        "descricao": descricao_ob if descricao_ob else None,
                        "vencimento": prazo_ob,
                        "periodicidade": periodicidade_ob,
                        "mes": mes_ob,
                        "ano": ano_ob,
                        "alerta": alerta_ob,
                        "status": "Pendente"
                    }).execute()
                    st.success("Obrigação customizada adicionada com sucesso!")
                    st.rerun()

# ============================================================================
# MÓDULO: VISUALIZAÇÕES - BASE DE CLIENTES (COM CORREÇÃO DE APIError)
# ============================================================================

def render_base_clientes():
    escritorio_id = garantir_escritorio_id()
    st.title("👥 Base de Clientes")
    st.markdown("Visualize a base de clientes, regimes tributários e credenciais de acesso. Atualize senhas de clientes diretamente daqui.")

    try:
        try:
            res_usuarios = supabase.table("usuarios_clientes").select("*").eq("escritorio_id", escritorio_id).execute()
            df_usuarios = pd.DataFrame(res_usuarios.data or [])
        except Exception:
            res_usuarios = supabase.table("usuarios_clientes").select("*").execute()
            df_usuarios = pd.DataFrame(res_usuarios.data or [])

        try:
            res_clientes = supabase.table("clientes").select("*").eq("escritorio_id", escritorio_id).execute()
            df_clientes = pd.DataFrame(res_clientes.data or [])
        except Exception:
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
    except Exception:
        st.info("Não foi possível carregar a base consolidada no momento.")

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
                supabase.table('clientes').update({'status_cadastro': novo_status}).eq('id', id_cliente_correto).eq('escritorio_id', escritorio_id).execute()
                if novo_status == 'Inativo':
                    supabase.table('tarefas').delete().eq('cliente_id', id_cliente_correto).eq('status', 'Pendente').eq('escritorio_id', escritorio_id).execute()
                st.success('Status atualizado com sucesso!')
                st.rerun()
            except Exception as error:
                st.error(f'Erro técnico ao comunicar com o Supabase: {error}')

    st.markdown("---")
    st.subheader("🔐 Consultar e Gerenciar Logins de Acesso")
    
    with st.expander("🔐 Consultar Logins de Acesso e Permissões", expanded=False):
        st.markdown("Gerencie e-mails, senhas de suporte, grupos de acesso e permissões dos usuários.")
        
        try:
            acessos = carregar_acessos()
            clientes_todos = carregar_clientes()
            
            if not acessos:
                st.info("Nenhum acesso de cliente registrado ainda.")
            else:
                # Criar dataframe com os acessos
                df_acessos = pd.DataFrame(acessos)
                
                # Consolidar com dados de clientes
                df_clientes_login = pd.DataFrame(clientes_todos)
                if not df_clientes_login.empty:
                    df_consolidado_login = df_acessos.merge(
                        df_clientes_login[['id', 'nome', 'cnpj', 'regime']],
                        left_on='cliente_id',
                        right_on='id',
                        how='left',
                        suffixes=('_acesso', '_cliente')
                    )
                else:
                    df_consolidado_login = df_acessos.copy()
                
                # Opção de filtro
                col_filtro1, col_filtro2 = st.columns(2)
                
                with col_filtro1:
                    filtro_cliente_login = st.text_input("🔍 Filtrar por Nome:", placeholder="Digite o nome do cliente...", key="filtro_cliente_login")
                
                with col_filtro2:
                    filtro_email_login = st.text_input("✉️ Filtrar por E-mail:", placeholder="Digite o e-mail...", key="filtro_email_login")
                
                # Aplicar filtros
                df_exibicao_login = df_consolidado_login.copy()
                
                if filtro_cliente_login:
                    df_exibicao_login = df_exibicao_login[df_exibicao_login['nome'].astype(str).str.contains(filtro_cliente_login, case=False, na=False)]
                
                if filtro_email_login:
                    df_exibicao_login = df_exibicao_login[df_exibicao_login['email'].astype(str).str.contains(filtro_email_login, case=False, na=False)]
                
                # Selecionar colunas para exibição
                colunas_exibicao_login = []
                if 'nome' in df_exibicao_login.columns:
                    colunas_exibicao_login.append('nome')
                if 'cnpj' in df_exibicao_login.columns:
                    colunas_exibicao_login.append('cnpj')
                if 'regime' in df_exibicao_login.columns:
                    colunas_exibicao_login.append('regime')
                if 'email' in df_exibicao_login.columns:
                    colunas_exibicao_login.append('email')
                if 'perfil' in df_exibicao_login.columns:
                    colunas_exibicao_login.append('perfil')
                if 'senha' in df_exibicao_login.columns:
                    colunas_exibicao_login.append('senha')
                
                # Renomear colunas
                df_exibir_login = df_exibicao_login[colunas_exibicao_login].copy()
                df_exibir_login.columns = ['Cliente', 'CNPJ', 'Regime', 'E-mail de Acesso', 'Perfil', 'Senha']
                
                # Exibir tabela
                st.dataframe(df_exibir_login, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### Gerenciar Grupo de Acesso e Permissões")
                
                # Seleção de usuário para gerenciar permissões
                usuario_selecionado = st.selectbox("Selecione usuário para gerenciar:", df_exibicao_login['email'].unique(), key="sel_usuario_perm")
                
                if usuario_selecionado:
                    usuario_data = df_exibicao_login[df_exibicao_login['email'] == usuario_selecionado].iloc[0]
                    user_id = usuario_data['id'] if 'id' in usuario_data else None
                    
                    # Controle de grupo de acesso
                    grupo_atual = usuario_data.get('grupo_acesso', 'Funcionário')
                    novo_grupo = st.radio("Grupo de Acesso:", ["Funcionário", "Gestão"], key=f"grupo_{user_id}")
                    
                    # Se Gestão, permite marcar permissões específicas
                    if novo_grupo == "Funcionário":
                        st.info("👤 Funcionário - Acesso restrito às funcionalidades básicas.")
                        permissoes_marcadas = []
                    else:
                        st.success("👨‍💼 Gestão - Acesso completo às funcionalidades e relatórios financeiros.")
                        st.markdown("**Permissões de Gestão:**")
                        col_perm1, col_perm2, col_perm3 = st.columns(3)
                        with col_perm1:
                            perm_financeiro = st.checkbox("📊 Visualizar Financeiro", value=True, key=f"perm_fin_{user_id}")
                        with col_perm2:
                            perm_relatorios = st.checkbox("📈 Gerar Relatórios", value=True, key=f"perm_rel_{user_id}")
                        with col_perm3:
                            perm_usuarios = st.checkbox("👥 Gerenciar Usuários", value=False, key=f"perm_usu_{user_id}")
                        
                        permissoes_marcadas = []
                        if perm_financeiro:
                            permissoes_marcadas.append("financeiro")
                        if perm_relatorios:
                            permissoes_marcadas.append("relatorios")
                        if perm_usuarios:
                            permissoes_marcadas.append("usuarios")
                    
                    if st.button(f"Salvar Acesso para {usuario_selecionado}", key=f"btn_salvar_acesso_{user_id}"):
                        try:
                            if user_id:
                                supabase.table('usuarios_clientes').update({
                                    'grupo_acesso': novo_grupo
                                }).eq('id', int(user_id)).eq('escritorio_id', escritorio_id).execute()
                                st.success(f"Grupo de acesso atualizado para {novo_grupo}!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar grupo: {e}")
                
                # Estatísticas
                st.markdown("---")
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                
                with col_stats1:
                    total_acessos_login = len(df_exibicao_login)
                    st.metric("Total de Acessos", total_acessos_login)
                
                with col_stats2:
                    acessos_clientes_login = len(df_exibicao_login[df_exibicao_login['perfil'] == 'cliente']) if 'perfil' in df_exibicao_login.columns else 0
                    st.metric("Acessos de Clientes", acessos_clientes_login)
                
                with col_stats3:
                    clientes_unicos_login = df_exibicao_login['cliente_id'].nunique() if 'cliente_id' in df_exibicao_login.columns else 0
                    st.metric("Clientes Únicos", clientes_unicos_login)
                
                # Exportação
                if st.button("📥 Exportar Acessos para CSV"):
                    csv_login = df_exibir_login.to_csv(index=False)
                    st.download_button(
                        label="Baixar CSV",
                        data=csv_login,
                        file_name="acessos_clientes.csv",
                        mime="text/csv"
                    )
        
        except Exception as e:
            st.error(f"Erro ao carregar dados de acessos: {e}")


def render_financeiro():
    escritorio_id = garantir_escritorio_id()
    st.title("📊 Financeiro")
    st.markdown("Central financeira do escritório com contas a receber, contas a pagar e honorários dos clientes.")

    try:
        st.subheader("💰 Controle de Honorários e Financeiro")

        try:
            clientes_base = carregar_clientes()
        except Exception:
            clientes_base = []

        if clientes_base:
            clientes_list = [c.get('nome', '-') for c in clientes_base]
        else:
            clientes_list = []

        with st.expander("💰 Gerenciar Honorários e Dados Financeiros", expanded=False):
            st.markdown("Configure os honorários e dados financeiros dos clientes.")

            if not clientes_list:
                st.info("Nenhum cliente disponível para configurar honorários.")
            else:
                with st.form("form_financeiro_cliente"):
                    cliente_fin = st.selectbox("Selecione o Cliente:", options=clientes_list, key="sel_cliente_fin")

                    col_hon1, col_hon2 = st.columns(2)
                    with col_hon1:
                        valor_honorario = st.number_input("Valor dos Honorários (R$):", min_value=0.0, step=100.0, format="%.2f", key="valor_hon")
                    with col_hon2:
                        dia_vencimento = st.number_input("Dia de Vencimento (1-31):", min_value=1, max_value=31, value=20, key="dia_venc")

                    if st.form_submit_button("Salvar Dados Financeiros"):
                        try:
                            cliente_id_fin = next((c.get('id') for c in clientes_base if c.get('nome') == cliente_fin), None)
                            if cliente_id_fin is None:
                                st.error('Cliente não encontrado.')
                            else:
                                supabase.table('clientes').update({
                                    'valor_honorario': float(valor_honorario),
                                    'dia_vencimento': int(dia_vencimento)
                                }).eq('id', int(to_python_scalar(cliente_id_fin))).eq('escritorio_id', escritorio_id).execute()
                                st.success("Dados financeiros salvos com sucesso!")
                                st.rerun()
                        except Exception:
                            st.info("Não foi possível salvar os dados financeiros no momento.")

        st.markdown("---")
        st.subheader("📊 Gestão Financeira")

        with st.expander("📊 Gestão Financeira (Relatórios e Faturamento)", expanded=False):
            try:
                perfil_usuario = obter_perfil_usuario(st.session_state.get("usuario_logado_email", ""))
                perfil_sessao = str(st.session_state.get("perfil", "")).strip().lower()

                if perfil_sessao not in {"admin", "escritorio"} and perfil_usuario != "Gestão":
                    st.error("❌ Erro: Acesso restrito aos perfis autorizados.")
                    return

                st.markdown("Módulo unificado com contas a receber e contas a pagar para o mês atual.")

                hoje = datetime.now()
                mes_ref = LISTA_MESES[hoje.month - 1]
                ano_ref = str(hoje.year)
                clientes_ativos = [c for c in carregar_clientes() if c.get("status_cadastro") == "Ativo"]

                try:
                    recebimentos = supabase.table("financeiro_mensal").select("*").eq("escritorio_id", escritorio_id).eq("mes", mes_ref).eq("ano", ano_ref).execute().data or []
                except Exception:
                    recebimentos = []

                # Integra honorarios recorrentes dos clientes ativos no mes atual.
                try:
                    clientes_mensalidade_ja_lancada = set()
                    for rec in recebimentos:
                        tipo_rec = str(rec.get("tipo") or "").strip().lower()
                        cliente_ref = rec.get("cliente_id")
                        if "mensalidade" in tipo_rec and cliente_ref is not None:
                            clientes_mensalidade_ja_lancada.add(int(to_python_scalar(cliente_ref)))

                    for cliente in clientes_ativos:
                        cliente_id_ref = cliente.get("id")
                        if cliente_id_ref is None:
                            continue

                        cliente_id_int = int(to_python_scalar(cliente_id_ref))
                        if cliente_id_int in clientes_mensalidade_ja_lancada:
                            continue

                        valor_hon = float(to_python_scalar(cliente.get("valor_honorario", 0) or 0))
                        if valor_hon <= 0:
                            continue

                        dia_venc_hon = int(float(to_python_scalar(cliente.get("dia_vencimento", 10) or 10)))
                        recebimentos.append({
                            "id": None,
                            "cliente_id": cliente_id_int,
                            "tipo": "Mensalidade",
                            "descricao": f"Honorarios - {str(cliente.get('nome', '-')).strip() or '-'}",
                            "valor": valor_hon,
                            "data_vencimento": gerar_data_vencimento(ano_ref, mes_ref, dia_venc_hon),
                            "status": "Pendente",
                            "data_pagamento": None,
                            "mes": mes_ref,
                            "ano": ano_ref
                        })
                except Exception:
                    pass

                try:
                    despesas = supabase.table("contas_a_pagar").select("*").eq("escritorio_id", escritorio_id).eq("mes", mes_ref).eq("ano", ano_ref).execute().data or []
                except Exception:
                    despesas = []

                df_receber = pd.DataFrame(recebimentos)
                if not df_receber.empty:
                    if "status" not in df_receber.columns:
                        df_receber["status"] = "Pendente"
                    if "valor" not in df_receber.columns:
                        df_receber["valor"] = 0
                    df_receber["status"] = df_receber["status"].fillna("Pendente").astype(str)
                    df_receber["valor"] = pd.to_numeric(df_receber["valor"], errors="coerce").fillna(0)

                df_pagar = pd.DataFrame(despesas)
                if not df_pagar.empty:
                    if "status" not in df_pagar.columns:
                        df_pagar["status"] = "Pendente"
                    if "valor" not in df_pagar.columns:
                        df_pagar["valor"] = 0
                    df_pagar["status"] = df_pagar["status"].fillna("Pendente").astype(str)
                    df_pagar["valor"] = pd.to_numeric(df_pagar["valor"], errors="coerce").fillna(0)

                total_previsto_receber = float(df_receber["valor"].sum()) if not df_receber.empty else 0.0
                total_recebido = float(df_receber[df_receber["status"] == "Pago"]["valor"].sum()) if not df_receber.empty else 0.0
                total_pendente_receber = float(df_receber[df_receber["status"] == "Pendente"]["valor"].sum()) if not df_receber.empty else 0.0

                total_previsto_pagar = float(df_pagar["valor"].sum()) if not df_pagar.empty else 0.0
                total_pago_pagar = float(df_pagar[df_pagar["status"] == "Pago"]["valor"].sum()) if not df_pagar.empty else 0.0
                total_pendente_pagar = float(df_pagar[df_pagar["status"] == "Pendente"]["valor"].sum()) if not df_pagar.empty else 0.0

                tab_receber, tab_pagar = st.tabs(["💰 Contas a Receber", "💸 Contas a Pagar"])

                with tab_receber:
                    st.markdown(f"### 💰 Contas a Receber - {mes_ref}/{ano_ref}")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Total Previsto", f"R$ {total_previsto_receber:,.2f}")
                    with c2:
                        st.metric("Total Recebido", f"R$ {total_recebido:,.2f}")
                    with c3:
                        st.metric("Total Pendente", f"R$ {total_pendente_receber:,.2f}")

                    if not df_receber.empty:
                        cols_receber = [col for col in ["id", "cliente_id", "tipo", "descricao", "valor", "data_vencimento", "status", "data_pagamento"] if col in df_receber.columns]
                        st.dataframe(df_receber[cols_receber], use_container_width=True)

                        st.markdown("### ✅ Baixar Recebimento")
                        pendentes_receber = df_receber[df_receber["status"] == "Pendente"].copy()
                        if pendentes_receber.empty:
                            st.success("Nenhum recebimento pendente para baixa.")
                        else:
                            for idx, row in pendentes_receber.iterrows():
                                row_id = int(float(to_python_scalar(row.get("id")))) if pd.notna(row.get("id")) else None
                                if row_id is None:
                                    continue
                                col_info, col_btn = st.columns([5, 1])
                                with col_info:
                                    st.write(
                                        f"{str(row.get('descricao', '-'))} | R$ {float(to_python_scalar(row.get('valor', 0) or 0)):,.2f} | Venc: {str(row.get('data_vencimento', '-'))}"
                                    )
                                with col_btn:
                                    if st.button("Marcar como Pago", key=f"btn_receber_pago_{row_id}_{idx}"):
                                        try:
                                            data_atual = datetime.now().isoformat()
                                            supabase.table("financeiro_mensal").update({
                                                "status": "Pago",
                                                "data_pagamento": data_atual
                                            }).eq("id", int(row_id)).eq("escritorio_id", escritorio_id).execute()
                                            st.success("Recebimento atualizado como pago.")
                                            st.rerun()
                                        except Exception:
                                            st.info("Não foi possível baixar o recebimento neste momento.")
                    else:
                        st.info("Nenhum lançamento encontrado em contas a receber para o mês atual.")

                    st.markdown("---")
                    st.markdown("### 📝 Lançar Serviço Extra")
                    with st.expander("➕ Criar Serviço Extra / Cobrança Avulsa", expanded=False):
                        with st.form("form_servico_extra"):
                            if not clientes_ativos:
                                st.warning("Não há clientes ativos para lançamento de serviço extra.")
                                st.form_submit_button("Lançar Serviço Extra", disabled=True)
                            else:
                                cliente_extra = st.selectbox("Cliente:", [c["nome"] for c in clientes_ativos], key="sel_cliente_extra")
                                nome_servico = st.text_input("Nome do Serviço (ex: Abertura, Alteração, DECORE)", key="nome_serv_extra")
                                valor_servico = st.number_input("Valor (R$):", min_value=0.0, step=50.0, format="%.2f", key="valor_serv_extra")
                                data_venc_extra = st.date_input("Data de Vencimento", value=datetime.now(), key="data_venc_extra")

                                if st.form_submit_button("Lançar Serviço Extra"):
                                    if not nome_servico or float(to_python_scalar(valor_servico)) <= 0:
                                        st.error("Preencha descrição e valor da cobrança.")
                                    else:
                                        cliente_id_extra = next((c["id"] for c in clientes_ativos if c["nome"] == cliente_extra), None)
                                        if cliente_id_extra is not None:
                                            try:
                                                supabase.table("financeiro_mensal").insert({
                                                    "escritorio_id": escritorio_id,
                                                    "cliente_id": int(to_python_scalar(cliente_id_extra)),
                                                    "tipo": "Serviço Extra",
                                                    "descricao": nome_servico,
                                                    "valor": float(to_python_scalar(valor_servico)),
                                                    "mes": mes_ref,
                                                    "ano": ano_ref,
                                                    "data_vencimento": data_venc_extra.strftime("%Y-%m-%d"),
                                                    "status": "Pendente",
                                                    "data_lancamento": datetime.now().strftime("%Y-%m-%d")
                                                }).execute()
                                                st.success("Serviço extra lançado com sucesso!")
                                                st.rerun()
                                            except Exception:
                                                st.info("Não foi possível lançar o serviço extra neste momento.")

                with tab_pagar:
                    st.markdown(f"### 💸 Contas a Pagar - {mes_ref}/{ano_ref}")
                    p1, p2, p3 = st.columns(3)
                    with p1:
                        st.metric("Total a Pagar", f"R$ {total_previsto_pagar:,.2f}")
                    with p2:
                        st.metric("Total Pago", f"R$ {total_pago_pagar:,.2f}")
                    with p3:
                        st.metric("Total Pendente", f"R$ {total_pendente_pagar:,.2f}")

                    with st.expander("➕ Lançar Nova Despesa", expanded=False):
                        with st.form("form_nova_despesa"):
                            desp_descricao = st.text_input("Descrição")
                            desp_fornecedor = st.text_input("Fornecedor")
                            desp_categoria = st.selectbox(
                                "Categoria",
                                ["TI/Softwares", "Infraestrutura/Aluguel", "Pessoal/Pró-labore", "Impostos", "Marketing", "Outros"]
                            )
                            desp_valor = st.number_input("Valor (R$)", min_value=0.0, step=50.0, format="%.2f")
                            desp_venc = st.date_input("Data de Vencimento", value=datetime.now(), key="data_venc_despesa")

                            if st.form_submit_button("Salvar Despesa"):
                                if not desp_descricao or not desp_fornecedor or float(to_python_scalar(desp_valor)) <= 0:
                                    st.error("Preencha descrição, fornecedor e valor da despesa.")
                                else:
                                    try:
                                        escritorio_id_despesa = int(to_python_scalar(st.session_state.get("escritorio_id") or escritorio_id or 0))
                                        supabase.table("contas_a_pagar").insert({
                                            "escritorio_id": escritorio_id_despesa,
                                            "descricao": desp_descricao,
                                            "fornecedor": desp_fornecedor,
                                            "categoria": desp_categoria,
                                            "valor": float(to_python_scalar(desp_valor)),
                                            "data_vencimento": desp_venc.strftime("%Y-%m-%d"),
                                            "status": "Pendente",
                                            "mes": mes_ref,
                                            "ano": ano_ref,
                                            "data_lancamento": datetime.now().strftime("%Y-%m-%d")
                                        }).execute()
                                        st.success("Despesa lançada com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro detalhado: {e}")

                    if not df_pagar.empty:
                        cols_pagar = [col for col in ["id", "descricao", "fornecedor", "categoria", "valor", "data_vencimento", "status", "data_pagamento"] if col in df_pagar.columns]
                        st.dataframe(df_pagar[cols_pagar], use_container_width=True)

                        st.markdown("### ✅ Baixa de Despesas")
                        pendentes_pagar = df_pagar[df_pagar["status"] == "Pendente"].copy()
                        if pendentes_pagar.empty:
                            st.success("Nenhuma despesa pendente para baixar.")
                        else:
                            for idx, row in pendentes_pagar.iterrows():
                                desp_id = int(float(to_python_scalar(row.get("id")))) if pd.notna(row.get("id")) else None
                                if desp_id is None:
                                    continue
                                col_info, col_btn = st.columns([5, 1])
                                with col_info:
                                    st.write(
                                        f"{str(row.get('descricao', '-'))} | {str(row.get('fornecedor', '-'))} | R$ {float(to_python_scalar(row.get('valor', 0) or 0)):,.2f}"
                                    )
                                with col_btn:
                                    if st.button("Baixar Despesa", key=f"btn_baixar_desp_{desp_id}_{idx}"):
                                        try:
                                            data_atual = datetime.now().isoformat()
                                            supabase.table("contas_a_pagar").update({
                                                "status": "Pago",
                                                "data_pagamento": data_atual
                                            }).eq("id", int(desp_id)).eq("escritorio_id", escritorio_id).execute()
                                            st.success("Despesa baixada com sucesso.")
                                            st.rerun()
                                        except Exception:
                                            st.info("Não foi possível baixar a despesa neste momento.")
                    else:
                        st.info("Nenhuma despesa registrada em contas a pagar para o mês atual.")

                st.markdown("---")
                st.markdown("### 📌 Resumo Consolidado")
                receita_saas_pago = obter_total_receita_saas_paga() if int(to_python_scalar(escritorio_id) or 0) == 1 else 0.0
                total_receitas_consolidadas = total_previsto_receber + receita_saas_pago
                fluxo_caixa_estimado = total_receitas_consolidadas - total_previsto_pagar
                c_res_1, c_res_2 = st.columns(2)
                with c_res_1:
                    st.metric("Total de Receitas", f"R$ {total_receitas_consolidadas:,.2f}")
                with c_res_2:
                    st.metric("Fluxo de Caixa Estimado do Mês", f"R$ {fluxo_caixa_estimado:,.2f}")

                linhas_fluxo = [
                    {"Categoria": "Receitas Operacionais", "Valor": total_previsto_receber},
                ]
                if receita_saas_pago > 0:
                    linhas_fluxo.append({"Categoria": "Receita SaaS (Pago)", "Valor": receita_saas_pago})
                linhas_fluxo.extend([
                    {"Categoria": "Despesas", "Valor": total_previsto_pagar},
                    {"Categoria": "Saldo", "Valor": fluxo_caixa_estimado},
                ])

                df_fluxo = pd.DataFrame(linhas_fluxo)
                fig_fluxo = px.bar(df_fluxo, x="Categoria", y="Valor", color="Categoria", title="Fluxo de Caixa Consolidado")
                st.plotly_chart(fig_fluxo, use_container_width=True)

            except Exception:
                st.info("A área financeira não pôde ser carregada no momento.")
    except Exception:
        st.info("Não foi possível abrir a área financeira neste momento.")


def obter_total_receita_saas_paga() -> float:
    def _valor_assinatura_por_plano(plano_nome: str) -> float:
        plano = str(plano_nome or "").strip().lower()
        if "enterprise" in plano:
            return 799.0
        if "pro" in plano:
            return 399.0
        if "starter" in plano:
            return 0.0
        return 0.0

    try:
        try:
            escritorios_pago = (
                supabase.table("escritorios")
                .select("id,nome,plano,status_pagamento,valor_assinatura")
                .eq("status_pagamento", "Pago")
                .execute()
                .data
                or []
            )
        except Exception:
            escritorios_pago = (
                supabase.table("escritorios")
                .select("id,nome,plano,status_pagamento")
                .eq("status_pagamento", "Pago")
                .execute()
                .data
                or []
            )

        total = 0.0
        for esc in escritorios_pago:
            valor = esc.get("valor_assinatura")
            if valor is None:
                valor = _valor_assinatura_por_plano(esc.get("plano", ""))
            total += float(to_python_scalar(valor) or 0)
        return total
    except Exception:
        return 0.0


def render_financeiro_saas():
    if str(st.session_state.get("perfil", "")).strip().lower() != "admin":
        st.error("Acesso restrito ao administrador master.")
        return

    st.title("💳 Financeiro SaaS")
    st.markdown("Controle de faturamento das mensalidades dos escritórios parceiros.")

    def valor_plano_assinatura(plano_nome: str) -> float:
        plano = str(plano_nome or "").strip().lower()
        if "enterprise" in plano:
            return 799.0
        if "pro" in plano:
            return 399.0
        if "starter" in plano:
            return 0.0
        return 0.0

    def proximo_vencimento_padrao() -> str:
        hoje = datetime.now()
        mes = hoje.month + 1
        ano = hoje.year
        if mes > 12:
            mes = 1
            ano += 1
        return datetime(ano, mes, 10).strftime("%Y-%m-%d")

    try:
        try:
            res_escritorios = (
                supabase.table("escritorios")
                .select("id,nome,plano,status,valor_assinatura,proximo_vencimento,status_pagamento")
                .order("nome")
                .execute()
            )
            escritorios = res_escritorios.data or []
            colunas_financeiras_disponiveis = True
        except Exception as e_colunas:
            st.warning("Algumas colunas financeiras ainda nao existem na tabela escritorios. Mostrando visao com campos padrao.")
            st.info(f"Detalhe tecnico: {e_colunas}")
            res_escritorios = (
                supabase.table("escritorios")
                .select("id,nome,plano,status")
                .order("nome")
                .execute()
            )
            escritorios = res_escritorios.data or []
            colunas_financeiras_disponiveis = False

        if not escritorios:
            st.info("Nenhum escritório parceiro encontrado para controle de assinaturas.")
            return

        linhas_tabela = []
        total_ativos = 0
        faturamento_estimado = 0.0

        for esc in escritorios:
            status_escritorio = str(esc.get("status", "")).strip() or "-"
            plano_escritorio = str(esc.get("plano", "-")).strip() or "-"
            valor_assinatura = esc.get("valor_assinatura")
            if valor_assinatura is None:
                valor_assinatura = valor_plano_assinatura(plano_escritorio)
            valor_assinatura = float(to_python_scalar(valor_assinatura) or 0)

            prox_venc = esc.get("proximo_vencimento")
            if prox_venc is None or str(prox_venc).strip() == "":
                prox_venc = proximo_vencimento_padrao()

            status_pag = str(esc.get("status_pagamento") or "Em Aberto").strip() or "Em Aberto"

            if status_escritorio.lower() == "ativo":
                total_ativos += 1
                faturamento_estimado += valor_assinatura

            linhas_tabela.append({
                "id": to_python_scalar(esc.get("id")),
                "Código": to_python_scalar(esc.get("id")),
                "Nome do Escritório": str(esc.get("nome", "-")).strip() or "-",
                "Plano Contratado": plano_escritorio,
                "Valor da Assinatura": valor_assinatura,
                "Próximo Vencimento": str(prox_venc),
                "Status do Pagamento": status_pag
            })

        m1, m2 = st.columns(2)
        with m1:
            st.metric("Faturamento Mensal Estimado (R$)", f"R$ {faturamento_estimado:,.2f}")
        with m2:
            st.metric("Total de Escritórios Ativos", total_ativos)

        st.markdown("---")
        st.subheader("💳 Controle de Mensalidades dos Parceiros")

        df_saas = pd.DataFrame(linhas_tabela)
        df_editado = st.data_editor(
            df_saas,
            hide_index=True,
            use_container_width=True,
            disabled=["id", "Código", "Nome do Escritório", "Plano Contratado", "Valor da Assinatura", "Próximo Vencimento"],
            column_config={
                "Valor da Assinatura": st.column_config.NumberColumn(format="R$ %.2f"),
                "Status do Pagamento": st.column_config.SelectboxColumn(
                    "Status do Pagamento",
                    options=["Pago", "Em Aberto", "Atrasado"]
                )
            },
            key="editor_mensalidades_saas"
        )

        if st.button("💾 Salvar Status de Pagamento", key="salvar_status_pagamentos_saas"):
            alteracoes = 0
            try:
                for _, linha in df_editado.iterrows():
                    codigo = to_python_scalar(linha.get("id"))
                    status_novo = str(linha.get("Status do Pagamento", "")).strip() or "Em Aberto"

                    status_antigo_series = df_saas.loc[df_saas["id"] == codigo, "Status do Pagamento"]
                    status_antigo = str(status_antigo_series.iloc[0]).strip() if not status_antigo_series.empty else ""
                    if status_novo == status_antigo:
                        continue

                    supabase.table("escritorios").update({
                        "status_pagamento": status_novo
                    }).eq("id", int(codigo)).execute()
                    alteracoes += 1

                if alteracoes:
                    st.success(f"{alteracoes} status de pagamento atualizados com sucesso.")
                    st.rerun()
                else:
                    st.info("Nenhuma alteracao de status para salvar.")
            except Exception as e_update:
                st.error(f"Erro ao salvar status de pagamento: {e_update}")
                st.warning("Se a coluna status_pagamento ainda nao existir em escritorios, crie-a no Supabase e recarregue o schema.")

        if not colunas_financeiras_disponiveis:
            st.caption("Sugestao de colunas financeiras para evolucao da tabela escritorios: valor_assinatura (numeric), proximo_vencimento (date), status_pagamento (text).")

    except Exception as e:
        st.error(f"Nao foi possivel carregar o painel financeiro SaaS: {e}")
        st.warning("Verifique se as colunas financeiras existem na tabela escritorios e se o schema do PostgREST esta atualizado.")

# ============================================================================
# MÓDULO: PORTAL CLIENTE
# ============================================================================

def render_portal_cliente():
    escritorio_id = garantir_escritorio_id()
    cli_res = supabase.table("clientes").select("*").eq("id", st.session_state.cliente_id_logado).eq("escritorio_id", escritorio_id).execute()
    if not cli_res.data:
        st.error("Cliente não encontrado.")
        return

    cliente = cli_res.data[0]
    st.title(f"👤 Portal do Cliente - {cliente['nome']}")
    st.markdown("Acesse seus documentos, mensalidades e informações de acesso.")

    # ABAS DO PORTAL DO CLIENTE
    tab_usuario, tab_documentos, tab_mensalidades = st.tabs(["👤 Meu Usuário", "📁 Documentos e Guias", "💳 Minhas Mensalidades"])

    # ========== ABA: MEU USUÁRIO ==========
    with tab_usuario:
        st.subheader("👤 Meu Usuário")
        
        # Obter dados do usuário logado
        try:
            usuario_logado_res = supabase.table("usuarios_clientes").select("*").eq("cliente_id", cliente['id']).eq("escritorio_id", escritorio_id).execute()
            if usuario_logado_res.data:
                usuario_logado = usuario_logado_res.data[0]
            else:
                usuario_logado = None
        except Exception:
            try:
                usuario_logado_res = supabase.table("usuarios_clientes").select("*").eq("cliente_id", cliente['id']).execute()
                usuario_logado = usuario_logado_res.data[0] if usuario_logado_res.data else None
            except Exception:
                usuario_logado = None

        if usuario_logado:
            
            # Exibir informações básicas
            st.markdown("### Informações do Usuário")
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.write(f"**E-mail:** {usuario_logado.get('email', '-')}")
            with col_info2:
                st.write(f"**Perfil:** {usuario_logado.get('perfil', '-')}")
            
            st.write(f"**Cliente:** {cliente['nome']}")
            
            st.markdown("---")
            st.markdown("### 🔒 Alterar Senha")
            
            with st.form("form_alterar_senha_usuario"):
                senha_atual = st.text_input("Senha Atual", type="password", key="senha_atual_usuario")
                nova_senha = st.text_input("Nova Senha", type="password", key="nova_senha_usuario")
                confirmar_senha = st.text_input("Confirmar Nova Senha", type="password", key="conf_senha_usuario")
                
                if st.form_submit_button("Alterar Senha"):
                    if not senha_atual or not nova_senha or not confirmar_senha:
                        st.error("Preencha todos os campos.")
                    elif nova_senha != confirmar_senha:
                        st.error("As novas senhas não conferem.")
                    elif usuario_logado.get("senha") != senha_atual:
                        st.error("Senha atual incorreta.")
                    else:
                        try:
                            supabase.table("usuarios_clientes").update({
                                "senha": nova_senha
                            }).eq("id", int(usuario_logado['id'])).eq("escritorio_id", escritorio_id).execute()
                            supabase.table("usuarios_clientes").update({
                                "senha": nova_senha
                            }).eq("email", usuario_logado.get("email", "")).eq("escritorio_id", escritorio_id).execute()
                            st.success("Senha alterada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.info("Não foi possível alterar a senha neste momento.")
        else:
            st.warning("Dados de usuário não encontrados.")

    # ========== ABA: DOCUMENTOS E GUIAS ==========
    with tab_documentos:
        st.subheader("📁 Documentos Fixos e Guias Mensais")
        
        tab_fixos_sub, tab_mensais_sub = st.tabs(["📄 Documentos Fixos", "📅 Guias Mensais"])
        
        with tab_fixos_sub:
            docs_fixos = supabase.table("documentos_fixos").select("*").eq("cliente_id", cliente["id"]).eq("escritorio_id", escritorio_id).execute().data or []
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
        
        with tab_mensais_sub:
            col_a, col_b = st.columns(2)
            with col_a:
                mes_filtrado = st.selectbox("Mês:", ["Todos"] + LISTA_MESES, index=datetime.now().month)
            with col_b:
                ano_filtrado = st.selectbox("Ano:", ["Todos"] + LISTA_ANOS, index=1)

            query = supabase.table("arquivos_escritorio").select("*").eq("cliente_id", cliente["id"]).eq("escritorio_id", escritorio_id)
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

    # ========== ABA: MINHAS MENSALIDADES ==========
    with tab_mensalidades:
        st.subheader("💳 Minhas Mensalidades")
        st.markdown("Visualize o mês atual, itens pendentes e o histórico de pagamentos já baixados.")

        hoje = datetime.now()
        mes_atual = LISTA_MESES[hoje.month - 1]
        ano_atual = str(hoje.year)
        st.markdown(f"### 📅 Mês Atual: {mes_atual}/{ano_atual}")

        valor_honorario = float(to_python_scalar(cliente.get("valor_honorario", 0) or 0))
        dia_vencimento = int(float(to_python_scalar(cliente.get("dia_vencimento", 20) or 20)))
        data_venc_mensalidade = gerar_data_vencimento(ano_atual, mes_atual, dia_vencimento)

        try:
            financeiro_cliente = supabase.table("financeiro_mensal").select("*").eq("cliente_id", int(to_python_scalar(cliente["id"]))).eq("escritorio_id", escritorio_id).execute().data or []
            df_financeiro = pd.DataFrame(financeiro_cliente)

            mensalidade_atual = None
            if not df_financeiro.empty:
                filtro_mensalidade = df_financeiro[
                    (df_financeiro["tipo"].astype(str) == "Mensalidade") &
                    (df_financeiro["mes"].astype(str) == mes_atual) &
                    (df_financeiro["ano"].astype(str) == ano_atual)
                ]
                if not filtro_mensalidade.empty:
                    mensalidade_atual = filtro_mensalidade.iloc[0]

            lancamentos_mes_atual = []
            if valor_honorario > 0:
                lancamentos_mes_atual.append({
                    "Descrição": f"Mensalidade {mes_atual}/{ano_atual}",
                    "Valor": valor_honorario,
                    "Data de Vencimento": str(mensalidade_atual.get("data_vencimento")) if mensalidade_atual is not None and mensalidade_atual.get("data_vencimento") else data_venc_mensalidade,
                    "Status": str(mensalidade_atual.get("status", "Pendente")) if mensalidade_atual is not None else "Pendente",
                    "Data de Pagamento": str(mensalidade_atual.get("data_pagamento", "")) if mensalidade_atual is not None else ""
                })

            if not df_financeiro.empty:
                filtro_extras_mes = df_financeiro[
                    (df_financeiro["tipo"].astype(str) == "Serviço Extra") &
                    (df_financeiro["mes"].astype(str) == mes_atual) &
                    (df_financeiro["ano"].astype(str) == ano_atual)
                ]
                for _, extra in filtro_extras_mes.iterrows():
                    lancamentos_mes_atual.append({
                        "Descrição": str(extra.get("descricao", "Serviço Extra")),
                        "Valor": float(to_python_scalar(extra.get("valor", 0) or 0)),
                        "Data de Vencimento": str(extra.get("data_vencimento", "")),
                        "Status": str(extra.get("status", "Pendente")),
                        "Data de Pagamento": str(extra.get("data_pagamento", ""))
                    })

            df_mes_atual = pd.DataFrame(lancamentos_mes_atual)

            st.markdown("### 💳 Mensalidades e Serviços Pendentes")
            if not df_mes_atual.empty:
                df_pendentes = df_mes_atual[df_mes_atual["Status"].astype(str) == "Pendente"].copy()
                if not df_pendentes.empty:
                    st.dataframe(df_pendentes[["Descrição", "Valor", "Data de Vencimento"]], use_container_width=True)
                else:
                    st.success("Você não possui pendências no mês atual.")
            else:
                st.info("Não há lançamentos para o mês atual.")

            st.markdown("---")
            st.markdown("### ✅ Histórico de Pagamentos (Pagas)")
            if not df_financeiro.empty:
                df_pagas = df_financeiro[df_financeiro["status"].astype(str) == "Pago"].copy()
                if not df_pagas.empty:
                    df_pagas_exib = pd.DataFrame({
                        "Descrição": df_pagas.get("descricao", "-").fillna("-") if "descricao" in df_pagas.columns else "-",
                        "Valor": pd.to_numeric(df_pagas.get("valor", 0), errors="coerce").fillna(0),
                        "Data de Vencimento": df_pagas.get("data_vencimento", "-").fillna("-") if "data_vencimento" in df_pagas.columns else "-",
                        "Data de Pagamento": df_pagas.get("data_pagamento", "-").fillna("-") if "data_pagamento" in df_pagas.columns else "-"
                    })
                    st.dataframe(df_pagas_exib, use_container_width=True)
                else:
                    st.info("Nenhum pagamento já baixado até o momento.")
            else:
                st.info("Nenhum histórico financeiro disponível.")
        except Exception as e:
            st.warning(f"Não foi possível carregar os dados de mensalidades: {e}")
        
        st.markdown("---")
        st.markdown("### 📎 Documentos Fiscais (NF / Recibos)")
        st.info("📎 Consulte com o escritório para obter cópias de notas fiscais, recibos e faturas emitidas.")


def render_gestao_saas():
    st.title("⚙️ Gestão SaaS")
    st.markdown("Área master para onboarding de escritórios parceiros e seus administradores.")

    if not st.session_state.get("is_admin_master", False):
        st.error("Acesso restrito ao admin master.")
        return

    def carregar_planos_saas():
        try:
            res = supabase.table("planos_saas").select("*").order("nome").execute()
            return res.data or []
        except Exception:
            return []

    def carregar_escritorios_parceiros():
        try:
            res = (
                supabase.table("escritorios")
                .select("id,nome,email,telefone,plano,status")
                .order("nome")
                .execute()
            )
            return res.data or []
        except Exception as e:
            st.warning(f"Nao foi possivel carregar a lista de escritorios: {e}")
            return []

    def carregar_admins_escritorios():
        try:
            usuarios_res = (
                supabase.table("usuarios_escritorio")
                .select("id,nome,email,perfil,escritorio_id,senha")
                .order("nome")
                .execute()
            )
            usuarios = usuarios_res.data or []

            escritorios_res = supabase.table("escritorios").select("id,nome").execute()
            escritorios = escritorios_res.data or []
            mapa_escritorios = {
                to_python_scalar(item.get("id")): str(item.get("nome", "-")).strip() or "-"
                for item in escritorios
            }

            for usuario in usuarios:
                escritorio_ref = to_python_scalar(usuario.get("escritorio_id"))
                senha_bruta = str(usuario.get("senha") or "").strip()
                usuario["escritorio_nome"] = mapa_escritorios.get(escritorio_ref, "-")
                usuario["credencial"] = "Definida" if senha_bruta else "Nao definida"

            return usuarios
        except Exception as e:
            st.error(f"Erro ao carregar administradores: {e}")
            return []

    st.subheader("📦 Gerenciar Planos e Permissões")
    with st.expander("📦 Cadastrar Novo Plano", expanded=True):
        with st.form("form_novo_plano"):
            nome_plano = st.text_input("Nome do Plano")
            limite_clientes = st.number_input("Limite de Clientes", min_value=1, value=15, step=1)
            valor_cliente_extra = st.number_input("Valor do Cliente Extra", min_value=0.0, value=2.50, step=0.50, format="%.2f")
            valor_mensal = st.number_input("Valor Mensal", min_value=0.0, step=50.0, format="%.2f")
            modulos_liberados = st.multiselect(
                "Permissões / Módulos Liberados",
                ["Dashboard Geral", "Documentos e Tarefas", "Cadastrar Cliente", "Central de Obrigações", "Base de Clientes", "Financeiro", "Gestão SaaS"]
            )

            if st.form_submit_button("Salvar Plano"):
                if not nome_plano:
                    st.error("Informe o nome do plano.")
                else:
                    try:
                        permissoes_selecionadas = list(modulos_liberados)
                        dados_plano = {
                            "nome": nome_plano,
                            "valor": float(valor_mensal),
                            "limite_clientes": int(limite_clientes),
                            "valor_cliente_extra": float(valor_cliente_extra),
                            "modulos_liberados": permissoes_selecionadas
                        }
                        supabase.table("planos_saas").insert(dados_plano).execute()
                        st.success("Plano cadastrado com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar o plano: {str(e)}")

    st.markdown("---")
    st.subheader("📋 Planos Atuais e Edição")
    try:
        planos_cadastrados = carregar_planos_saas()
    except Exception:
        planos_cadastrados = []

    if planos_cadastrados:
        df_planos = pd.DataFrame(planos_cadastrados)
        if not df_planos.empty:
            if "valor" not in df_planos.columns and "valor_mensal" in df_planos.columns:
                df_planos["valor"] = df_planos["valor_mensal"]
            if "limite_clientes" not in df_planos.columns:
                df_planos["limite_clientes"] = "-"
            if "valor_cliente_extra" not in df_planos.columns:
                df_planos["valor_cliente_extra"] = "-"
            if "modulos_liberados" in df_planos.columns:
                df_planos["modulos_liberados"] = df_planos["modulos_liberados"].apply(
                    lambda itens: ", ".join(itens) if isinstance(itens, list) else str(itens or "-")
                )

            colunas_exibicao_planos = [col for col in ["id", "nome", "valor", "limite_clientes", "valor_cliente_extra", "modulos_liberados"] if col in df_planos.columns]
            st.dataframe(df_planos[colunas_exibicao_planos], use_container_width=True)

        mapa_planos_edicao = {}
        opcoes_planos_edicao = []
        for plano in planos_cadastrados:
            nome_plano_db = str(plano.get("nome", "Plano")).strip()
            valor_plano_db = float(to_python_scalar(plano.get("valor", plano.get("valor_mensal", 0)) or 0))
            label_plano = f"{nome_plano_db} - R$ {valor_plano_db:,.2f}"
            opcoes_planos_edicao.append(label_plano)
            mapa_planos_edicao[label_plano] = plano

        plano_selecionado_label = st.selectbox("Selecione o plano para editar", opcoes_planos_edicao, key="sel_plano_edicao")
        plano_selecionado = mapa_planos_edicao.get(plano_selecionado_label, {})

        if plano_selecionado:
            with st.form("form_editar_plano"):
                nome_plano_edit = st.text_input("Nome do Plano", value=str(plano_selecionado.get("nome", "")))
                limite_clientes_edit = st.number_input(
                    "Limite de Clientes",
                    min_value=1,
                    value=int(to_python_scalar(plano_selecionado.get("limite_clientes", 15)) or 15),
                    step=1,
                    key=f"limite_clientes_edit_{plano_selecionado.get('id')}"
                )
                valor_cliente_extra_edit = st.number_input(
                    "Valor do Cliente Extra",
                    min_value=0.0,
                    value=float(to_python_scalar(plano_selecionado.get("valor_cliente_extra", 2.50)) or 2.50),
                    step=0.50,
                    format="%.2f",
                    key=f"valor_cliente_extra_edit_{plano_selecionado.get('id')}"
                )
                valor_plano_edit = st.number_input(
                    "Valor Mensal",
                    min_value=0.0,
                    step=50.0,
                    format="%.2f",
                    value=float(to_python_scalar(plano_selecionado.get("valor", plano_selecionado.get("valor_mensal", 0)) or 0))
                )
                modulos_atuais = plano_selecionado.get("modulos_liberados", [])
                if not isinstance(modulos_atuais, list):
                    modulos_atuais = []
                modulos_edit = st.multiselect(
                    "Permissões / Módulos Liberados",
                    ["Dashboard Geral", "Documentos e Tarefas", "Cadastrar Cliente", "Central de Obrigações", "Base de Clientes", "Financeiro", "Gestão SaaS"],
                    default=modulos_atuais,
                    key="mods_edicao_plano"
                )

                if st.form_submit_button("Atualizar Plano"):
                    try:
                        supabase.table("planos_saas").update({
                            "nome": nome_plano_edit,
                            "valor": float(valor_plano_edit),
                            "limite_clientes": int(limite_clientes_edit),
                            "valor_cliente_extra": float(valor_cliente_extra_edit),
                            "modulos_liberados": list(modulos_edit)
                        }).eq("id", int(to_python_scalar(plano_selecionado.get("id")))).execute()
                        st.success("Plano atualizado com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar o plano: {str(e)}")

            st.markdown("---")
            st.caption("Exclusão segura: planos vinculados a escritórios não podem ser removidos.")
            if st.button("🗑️ Excluir Plano", key=f"btn_excluir_plano_{plano_selecionado.get('id')}"):
                try:
                    nome_plano_base = str(plano_selecionado.get("nome", "")).strip()
                    vinculados = supabase.table("escritorios").select("id").eq("plano", nome_plano_base).execute().data or []
                    if vinculados:
                        st.warning("Este plano está em uso por um ou mais escritórios e não pode ser excluído.")
                    else:
                        supabase.table("planos_saas").delete().eq("id", int(to_python_scalar(plano_selecionado.get("id")))).execute()
                        st.success("Plano excluído com sucesso.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir o plano: {str(e)}")
    else:
        st.info("Nenhum plano cadastrado ainda.")

    with st.expander("🏢 Cadastrar Novo Escritório", expanded=True):
        try:
            planos_cadastrados = carregar_planos_saas()
        except Exception:
            planos_cadastrados = []

        if planos_cadastrados:
            opcoes_planos = []
            mapa_planos = {}
            for plano in planos_cadastrados:
                nome_plano_db = str(plano.get("nome", "Plano")).strip()
                valor_plano_db = float(to_python_scalar(plano.get("valor_mensal", plano.get("valor", 0)) or 0))
                label_plano = f"{nome_plano_db} - R$ {valor_plano_db:,.2f}"
                opcoes_planos.append(label_plano)
                mapa_planos[label_plano] = plano
        else:
            opcoes_planos = ["Starter - R$ 0,00", "Pro - R$ 0,00", "Enterprise - R$ 0,00"]
            mapa_planos = {
                "Starter - R$ 0,00": {"nome": "Starter", "valor_mensal": 0},
                "Pro - R$ 0,00": {"nome": "Pro", "valor_mensal": 0},
                "Enterprise - R$ 0,00": {"nome": "Enterprise", "valor_mensal": 0},
            }

        with st.form("form_novo_escritorio"):
            nome_escritorio = st.text_input("Nome do Escritório")
            email_escritorio = st.text_input("E-mail de Contato")
            telefone_escritorio = st.text_input("Telefone")
            plano_escritorio_label = st.selectbox("Plano", opcoes_planos, index=0)

            if st.form_submit_button("Cadastrar Escritório"):
                if not nome_escritorio or not email_escritorio:
                    st.error("Informe ao menos nome e e-mail do escritório.")
                else:
                    try:
                        plano_escolhido = mapa_planos.get(plano_escritorio_label, {})
                        insert_escritorio = supabase.table("escritorios").insert({
                            "nome": nome_escritorio,
                            "email": email_escritorio,
                            "telefone": telefone_escritorio,
                            "plano": plano_escolhido.get("nome", plano_escritorio_label.split(" - ")[0]),
                            "status": "Ativo"
                        }).execute()

                        if not insert_escritorio.data:
                            raise ValueError("Falha ao cadastrar escritório.")

                        st.session_state["novo_escritorio_id"] = insert_escritorio.data[0].get("id")
                        st.success("Escritório cadastrado com sucesso.")
                    except Exception as e:
                        st.error(f"Erro detalhado: {str(e)}")

    st.subheader("🏢 Escritórios Parceiros Cadastrados")
    col_atualizar, _ = st.columns([1, 5])
    with col_atualizar:
        if st.button("🔄 Atualizar Lista", key="atualizar_lista_escritorios"):
            st.rerun()

    escritorios_parceiros = carregar_escritorios_parceiros()
    if escritorios_parceiros:
        df_escritorios = pd.DataFrame(escritorios_parceiros)
        colunas_escritorios = ["id", "nome", "email", "telefone", "plano", "status"]
        for coluna in colunas_escritorios:
            if coluna not in df_escritorios.columns:
                df_escritorios[coluna] = "-"
        st.dataframe(df_escritorios[colunas_escritorios], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum escritório cadastrado até o momento.")

    with st.expander("👤 Cadastrar Primeiro Usuário Administrador", expanded=True):
        try:
            escritorios = supabase.table("escritorios").select("id,nome,status").order("nome").execute().data or []
        except Exception:
            escritorios = []

        if not escritorios:
            st.info("Cadastre um escritório antes de criar o usuário administrador.")
            return

        mapa_escritorios = {f"{e.get('nome', '-') } (ID {e.get('id')})": e.get("id") for e in escritorios}
        default_escritorio_id = st.session_state.get("novo_escritorio_id")
        default_index = 0
        if default_escritorio_id is not None:
            for i, (_, eid) in enumerate(mapa_escritorios.items()):
                if eid == default_escritorio_id:
                    default_index = i
                    break

        with st.form("form_primeiro_admin_escritorio"):
            escritorio_label = st.selectbox("Escritório", list(mapa_escritorios.keys()), index=default_index)
            nome_admin = st.text_input("Nome do Administrador")
            email_admin = st.text_input("E-mail de Login")
            senha_admin = st.text_input("Senha Inicial", type="password")

            if st.form_submit_button("Cadastrar Administrador"):
                if not nome_admin or not email_admin or not senha_admin:
                    st.error("Preencha nome, e-mail e senha do administrador.")
                else:
                    try:
                        escritorio_id = mapa_escritorios[escritorio_label]
                        payload_admin = {
                            "nome": nome_admin,
                            "email": email_admin,
                            "grupo_acesso": "Gestão",
                            "escritorio_id": escritorio_id,
                            "senha": senha_admin,
                            "perfil": "escritorio"
                        }
                        supabase.table("usuarios_escritorio").insert(payload_admin).execute()
                        st.success("Administrador do escritório cadastrado com sucesso.")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    st.subheader("🔑 Administradores de Escritórios")
    col_admin_refresh, _ = st.columns([1, 5])
    with col_admin_refresh:
        if st.button("🔄 Atualizar Administradores", key="atualizar_lista_admins"):
            st.rerun()

    admins_escritorios = carregar_admins_escritorios()
    if admins_escritorios:
        df_admins = pd.DataFrame(admins_escritorios)
        colunas_admins = ["id", "nome", "email", "perfil", "escritorio_id", "escritorio_nome", "credencial", "senha"]
        for coluna in colunas_admins:
            if coluna not in df_admins.columns:
                df_admins[coluna] = "-"
        st.dataframe(df_admins[colunas_admins], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum administrador de escritório cadastrado.")


def render_meu_acesso():
    st.title("👤 Meu Acesso")

    usuario_logado = st.session_state.get("usuario_logado")
    if not isinstance(usuario_logado, dict):
        usuario_logado = {}

    if not usuario_logado.get("id"):
        try:
            email_logado = str(st.session_state.get("usuario_logado_email") or "").strip()
            escritorio_id = st.session_state.get("escritorio_id")
            if email_logado:
                query = supabase.table("usuarios_escritorio").select("*").eq("email", email_logado)
                if escritorio_id is not None:
                    query = query.eq("escritorio_id", escritorio_id)
                res_usuario = query.limit(1).execute()
                if res_usuario.data:
                    usuario_logado = res_usuario.data[0]
                    st.session_state["usuario_logado"] = usuario_logado
        except Exception:
            usuario_logado = usuario_logado or {}

    nome_usuario = str(usuario_logado.get("nome") or usuario_logado.get("usuario") or "-")
    email_usuario = str(usuario_logado.get("email") or st.session_state.get("usuario_logado_email") or "-")

    col_info_nome, col_info_email = st.columns(2)
    with col_info_nome:
        st.write(f"**Nome:** {nome_usuario}")
    with col_info_email:
        st.write(f"**E-mail:** {email_usuario}")

    st.markdown("---")
    st.subheader("🔒 Alterar Senha")

    with st.form("form_alterar_senha_meu_acesso"):
        nova_senha = st.text_input("Nova Senha", type="password", key="nova_senha_meu_acesso")
        confirmar_senha = st.text_input("Confirme a Nova Senha", type="password", key="confirmar_nova_senha_meu_acesso")

        if st.form_submit_button("Atualizar Senha"):
            if not nova_senha or not confirmar_senha:
                st.error("Preencha os dois campos de senha.")
            elif nova_senha != confirmar_senha:
                st.error("As senhas informadas nao coincidem.")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                try:
                    usuario_id = to_python_scalar(usuario_logado.get("id"))
                    if usuario_id is None:
                        raise ValueError("ID do usuario logado nao encontrado na sessao.")

                    escritorio_id = st.session_state.get("escritorio_id")
                    query_update = supabase.table("usuarios_escritorio").update({"senha": nova_senha}).eq("id", int(usuario_id))
                    if escritorio_id is not None:
                        query_update = query_update.eq("escritorio_id", escritorio_id)
                    query_update.execute()

                    if isinstance(st.session_state.get("usuario_logado"), dict):
                        st.session_state["usuario_logado"]["senha"] = nova_senha
                    st.success("Senha atualizada com sucesso.")
                except Exception as e:
                    st.error(f"Erro ao atualizar senha: {e}")

# ============================================================================
# FLUXO PRINCIPAL - AUTENTICAÇÃO E NAVEGAÇÃO
# ============================================================================

if not st.session_state.logado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            if os.path.exists("logo.png"):
                img = Image.open("logo.png")
                st.image(img, width=280)
            else:
                st.subheader("V-CONTROLL Hub")
        except Exception:
            st.subheader("V-CONTROLL Hub")
        with st.form("form_login"):
            usuario = st.text_input("Usuário ou E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                realizar_login(usuario, senha)
else:
    if st.session_state.perfil in {"escritorio", "admin"}:
        render_branding_sidebar()
        with st.sidebar:
            opcoes_menu = ["Dashboard Geral", "Documentos e Tarefas", "Cadastrar Cliente", "Central de Obrigações", "Base de Clientes", "Financeiro", "👤 Meu Acesso"]
            icones_menu = ["house", "file-earmark-check", "plus-circle", "calendar-check", "people", "currency-dollar", "person-circle"]
            if st.session_state.get("is_admin_master", False):
                opcoes_menu.append("💳 Financeiro SaaS")
                icones_menu.append("credit-card")
                opcoes_menu.append("Gestão SaaS")
                icones_menu.append("gear-wide-connected")

            escolha = option_menu(
                menu_title=None,
                options=opcoes_menu,
                icons=icones_menu,
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "5px!important", "background-color": "#111827"},
                    "icon": {"color": "#fbbf24", "font-size": "16px"},
                    "nav-link": {"font-size": "14px", "text-align": "left", "margin": "4px 0px", "color": "#9ca3af", "--hover-color": "#1f2937"},
                    "nav-link-selected": {"background-color": "#4f46e5", "color": "#ffffff", "font-weight": "600"},
                }
            )

            if st.button("🚪 Sair / Logout", use_container_width=True):
                st.session_state.logado = False
                st.session_state.perfil = None
                st.session_state.cliente_id_logado = None
                st.session_state.usuario = None
                st.session_state.usuario_logado_email = None
                st.session_state.escritorio_id = None
                st.session_state.is_admin_master = False
                st.rerun()

        if escolha == "Dashboard Geral":
            render_dashboard()
        elif escolha == "Documentos e Tarefas":
            render_upload_documentos()
        elif escolha == "Cadastrar Cliente":
            render_cadastrar_cliente()
        elif escolha == "Central de Obrigações":
            render_central_obrigacoes()
        elif escolha == "Base de Clientes":
            render_base_clientes()
        elif escolha == "Financeiro":
            render_financeiro()
        elif escolha == "👤 Meu Acesso":
            render_meu_acesso()
        elif escolha == "💳 Financeiro SaaS":
            render_financeiro_saas()
        elif escolha == "Gestão SaaS":
            render_gestao_saas()
    else:
        render_branding_sidebar()
        with st.sidebar:
            st.write("Conectado como: **CLIENTE**")

            opcao_cliente = option_menu(
                menu_title=None,
                options=["Meu Portal", "👤 Meu Acesso", "Logout"],
                icons=["person-circle", "person-gear", "box-arrow-right"],
                default_index=0,
                styles={
                    "container": {"padding": "5px!important", "background-color": "#111827"},
                    "icon": {"color": "#fbbf24", "font-size": "16px"},
                    "nav-link": {"font-size": "14px", "text-align": "left", "margin": "4px 0px", "color": "#9ca3af", "--hover-color": "#1f2937"},
                    "nav-link-selected": {"background-color": "#4f46e5", "color": "#ffffff", "font-weight": "600"},
                }
            )

        if opcao_cliente == "Meu Portal":
            render_portal_cliente()
        elif opcao_cliente == "👤 Meu Acesso":
            render_meu_acesso()
        elif opcao_cliente == "Logout":
            st.session_state.logado = False
            st.session_state.perfil = None
            st.session_state.cliente_id_logado = None
            st.session_state.usuario = None
            st.session_state.usuario_logado_email = None
            st.session_state.escritorio_id = None
            st.session_state.is_admin_master = False
            st.rerun()
