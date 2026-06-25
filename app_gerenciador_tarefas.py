import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# Configuração da página
st.set_page_config(page_title="Gestão Vieira Controller", layout="wide")

# --- CONEXÃO SEGURA COM SUPABASE ---
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

# --- CONFIGURAÇÕES DE ENUMERADORES ---
LISTA_ANOS = ["2025", "2026", "2027"]
LISTA_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
TIPOS_DOCS_FIXOS = [
    "Contrato Social / Alterações",
    "Cartão CNPJ",
    "Procuração Eletrônica",
    "Inscrição Estadual/Municipal",
    "Senha de Acessos / Códigos",
    "Outros Documentos Fixos"
]
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

# --- CONTROLE DE SESSÃO / LOGIN ---
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


# --- FUNÇÕES DE DADOS ---
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


def df_from_data(data):
    return pd.DataFrame(data) if data else pd.DataFrame()


def extrapolar_tarefas_por_mes(df_tarefas, mes, ano):
    if df_tarefas.empty:
        return df_tarefas
    return df_tarefas[(df_tarefas["mes"] == mes) & (df_tarefas["ano"] == ano)]


# --- MÓDULOS VISUAIS ---
def render_dashboard():
    st.title("📊 Painel de Controle Vieira Controller")
    st.markdown("Bem-vindo(a) ao centro de monitoramento da contabilidade. Acompanhe clientes, tarefas e documentos em tempo real.")

    clientes = carregar_clientes()
    tarefas = carregar_tarefas()
    documentos_fixos = carregar_documentos_fixos()
    arquivos = carregar_arquivos_escritorio()

    df_clientes = df_from_data(clientes)
    df_tarefas = df_from_data(tarefas)
    df_documentos_fixos = df_from_data(documentos_fixos)
    df_arquivos = df_from_data(arquivos)

    hoje = datetime.now()
    mes_atual = LISTA_MESES[hoje.month - 1]
    ano_atual = str(hoje.year)
    df_tarefas_mes = extrapolar_tarefas_por_mes(df_tarefas, mes_atual, ano_atual)

    total_clientes = len(df_clientes)
    tarefas_pendentes = int(df_tarefas_mes[df_tarefas_mes["status"] == "Pendente"].shape[0]) if not df_tarefas_mes.empty else 0
    tarefas_concluidas = int(df_tarefas_mes[df_tarefas_mes["status"] == "Concluído"].shape[0]) if not df_tarefas_mes.empty else 0
    documentos_processados = len(df_documentos_fixos) + len(df_arquivos)

    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes ativos", total_clientes, delta=None)
    col2.metric("Tarefas pendentes neste mês", tarefas_pendentes, delta=None)
    col3.metric("Tarefas concluídas neste mês", tarefas_concluidas, delta=None)

    col4, col5, col6 = st.columns(3)
    col4.metric("Documentos processados", documentos_processados, delta=None)
    col5.metric("Mês atual", mes_atual, delta=None)
    col6.metric("Ano", ano_atual, delta=None)

    st.markdown("---")

    if not df_tarefas_mes.empty:
        df_status = (
            df_tarefas_mes["status"].fillna("Sem status")
            .value_counts()
            .reset_index()
            .rename(columns={"index": "Status", "status": "Quantidade"})
        )
        fig_status = px.bar(df_status, x="Status", y="Quantidade", color="Status", title="Status das obrigações do mês", text="Quantidade")
        fig_status.update_layout(showlegend=False, height=320)
        st.plotly_chart(fig_status, use_container_width=True)

        if not df_clientes.empty:
            df_pendentes = df_tarefas_mes[df_tarefas_mes["status"] == "Pendente"].merge(df_clientes[["id", "nome"]], left_on="cliente_id", right_on="id", how="left")
            if not df_pendentes.empty:
                df_pendentes_por_cliente = (
                    df_pendentes["nome"].value_counts().reset_index().rename(columns={"index": "Cliente", "nome": "Pendentes"})
                )
                fig_pendentes = px.bar(df_pendentes_por_cliente, x="Cliente", y="Pendentes", title="Tarefas pendentes por cliente", text="Pendentes")
                fig_pendentes.update_layout(xaxis_tickangle=-45, height=320)
                st.plotly_chart(fig_pendentes, use_container_width=True)
    else:
        st.info("Ainda não há tarefas registradas para o mês atual.")

    st.markdown("---")
    st.markdown("### Últimas tarefas cadastradas")
    if not df_tarefas.empty and not df_clientes.empty:
        df_exibicao = df_tarefas.merge(df_clientes[["id", "nome"]], left_on="cliente_id", right_on="id", how="left")
        df_exibicao = df_exibicao[["nome", "obrigacao", "periodicidade", "mes", "ano", "vencimento", "status"]]
        df_exibicao.columns = ["Cliente", "Obrigação", "Periodicidade", "Mês", "Ano", "Prazo", "Status"]
        st.dataframe(df_exibicao.sort_values(by=["Ano", "Mês"], ascending=False).head(10), use_container_width=True)
    else:
        st.info("Cadastre um cliente e suas obrigações para começar a preencher o painel.")


def render_upload_documentos():
    st.title("📌 Upload de Documentos e Conclusão de Atividades")
    st.markdown("Use este espaço para enviar documentos fixos e concluir tarefas diretamente no banco.")

    clientes = carregar_clientes()
    tarefas = carregar_tarefas()
    lista_clientes = clientes

    if not lista_clientes:
        st.warning("Cadastre ao menos um cliente antes de usar os uploads e tarefas.")
        return

    tab_docs, tab_tarefas = st.tabs(["Documentos", "Tarefas Pendentes"])

    with tab_docs:
        sub_tab_mensal, sub_tab_fixos = st.tabs(["Documentos Mensais", "Documentos Fixos"])

        with sub_tab_mensal:
            st.subheader("Upload de Documentos Mensais")
            with st.form("form_doc_mensal"):
                cliente_sel = st.selectbox("Selecione o Cliente:", [c["nome"] for c in lista_clientes])
                mes_comp = st.selectbox("Mês de Competência:", LISTA_MESES, index=datetime.now().month - 1)
                ano_comp = st.selectbox("Ano:", LISTA_ANOS, index=1)
                arquivo_mensal = st.file_uploader("Arquivo (PDF/XML/XLSX):", type=["pdf", "xml", "zip", "xlsx"])

                if st.form_submit_button("Salvar Documento Mensal"):
                    if not arquivo_mensal:
                        st.error("Anexe um arquivo antes de salvar.")
                    else:
                        id_cliente = next(c["id"] for c in lista_clientes if c["nome"] == cliente_sel)
                        nome_limpo = f"{id_cliente}_{ano_comp}_{mes_comp}_{int(datetime.now().timestamp())}_{arquivo_mensal.name}"
                        caminho_storage = f"guias/{nome_limpo}"
                        supabase.storage.from_("documentos-clientes").upload(
                            path=caminho_storage,
                            file=arquivo_mensal.getvalue(),
                            file_options={"content-type": arquivo_mensal.type}
                        )
                        supabase.table("arquivos_escritorio").insert({
                            "cliente_id": id_cliente,
                            "ano": ano_comp,
                            "mes": mes_comp,
                            "nome_arquivo": arquivo_mensal.name,
                            "caminho_storage": caminho_storage,
                            "data_publicacao": datetime.now().strftime("%d/%m/%Y %H:%M")
                        }).execute()
                        st.success("Documento mensal salvo com sucesso.")

        with sub_tab_fixos:
            st.subheader("Upload de Documentos Fixos / Institucionais")
            with st.form("form_doc_fixo"):
                cliente_selecionado = st.selectbox("Selecione o Cliente:", [c["nome"] for c in lista_clientes])
                tipo_doc = st.selectbox("Tipo de Documento:", TIPOS_DOCS_FIXOS)
                arquivo_upload = st.file_uploader("Selecione o arquivo (PDF/JPG/PNG):", type=["pdf", "jpg", "png"])

                if st.form_submit_button("Salvar Documento Institucional"):
                    if not arquivo_upload:
                        st.error("Anexe um arquivo antes de salvar.")
                    else:
                        id_cliente = next(c["id"] for c in lista_clientes if c["nome"] == cliente_selecionado)
                        nome_limpo = f"{id_cliente}_{int(datetime.now().timestamp())}_{arquivo_upload.name}"
                        caminho_storage = f"arquivos/{nome_limpo}"

                        supabase.storage.from_("documentos-fixos").upload(
                            path=caminho_storage,
                            file=arquivo_upload.getvalue(),
                            file_options={"content-type": arquivo_upload.type}
                        )
                        supabase.table("documentos_fixos").insert({
                            "cliente_id": id_cliente,
                            "tipo_documento": tipo_doc,
                            "nome_arquivo": arquivo_upload.name,
                            "caminho_storage": caminho_storage
                        }).execute()
                        st.success(f"Documento institucional '{tipo_doc}' enviado com sucesso.")

            st.markdown("---")
            st.markdown("### Documentos institucionais já cadastrados")
            documentos_fixos = carregar_documentos_fixos()
            if documentos_fixos:
                for doc in documentos_fixos:
                    cliente_nome = doc.get("clientes", {}).get("nome", "-") if doc.get("clientes") else "-"
                    st.write(f"**{doc['nome_arquivo']}** — Cliente: {cliente_nome} — Tipo: {doc['tipo_documento']}")
            else:
                st.info("Nenhum documento institucional cadastrado ainda.")

    with tab_tarefas:
        st.markdown("### Tarefas pendentes")
        df_tarefas = df_from_data(tarefas)
        df_clientes = df_from_data(clientes)

        if df_tarefas.empty:
            st.info("Não há tarefas cadastradas.")
            return

        tarefas_pendentes = df_tarefas[df_tarefas["status"] == "Pendente"]
        if tarefas_pendentes.empty:
            st.success("Todas as tarefas estão concluídas.")
            return

        tarefas_pendentes = tarefas_pendentes.merge(df_clientes[["id", "nome"]], left_on="cliente_id", right_on="id", how="left")
        tarefas_pendentes = tarefas_pendentes.sort_values(by=["ano", "mes"])

        for _, tarefa in tarefas_pendentes.iterrows():
            with st.expander(f"{tarefa['nome']} — {tarefa['obrigacao']} ({tarefa['mes']}/{tarefa['ano']})"):
                st.write(f"**Cliente:** {tarefa['nome']}")
                st.write(f"**Obrigação:** {tarefa['obrigacao']}")
                st.write(f"**Vencimento:** {tarefa['vencimento']}")
                st.write(f"**Periodicidade:** {tarefa['periodicidade']}")
                st.write(f"**Prioridade:** {tarefa.get('alerta', '✅ Normal')}")

                arquivo_guia = st.file_uploader(
                    "Anexar guia ou comprovante", type=["pdf", "xml", "zip", "xlsx"], key=f"file_tarefa_{tarefa['id']}"
                )
                if st.button("Concluir Atividade", key=f"btn_tarefa_{tarefa['id']}"):
                    update_data = {
                        "status": "Concluído",
                        "alerta": "✅ Normal",
                        "data_conclusao": datetime.now().strftime("%d/%m/%Y %H:%M")
                    }
                    if arquivo_guia:
                        nome_limpo = f"{tarefa['id']}_{arquivo_guia.name}"
                        caminho_storage = f"guias/{nome_limpo}"
                        supabase.storage.from_("documentos-clientes").upload(
                            path=caminho_storage,
                            file=arquivo_guia.getvalue(),
                            file_options={"content-type": arquivo_guia.type}
                        )
                        supabase.table("arquivos_escritorio").insert({
                            "cliente_id": int(tarefa["cliente_id"]),
                            "ano": tarefa["ano"],
                            "mes": tarefa["mes"],
                            "nome_arquivo": arquivo_guia.name,
                            "caminho_storage": caminho_storage,
                            "data_publicacao": datetime.now().strftime("%d/%m/%Y %H:%M")
                        }).execute()

                    supabase.table("tarefas").update(update_data).eq("id", int(tarefa["id"])).execute()
                    st.success("Tarefa marcada como concluída.")
                    st.experimental_rerun()


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

    with st.form("form_cliente_unificado"):
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
                        "tem_folha": tem_folha
                    }).execute()

                    if not ins_res.data or len(ins_res.data) == 0:
                        raise ValueError("Falha ao criar o cliente no Supabase.")

                    cliente_id = ins_res.data[0]["id"]
                    supabase.table("usuarios_clientes").insert({
                        "cliente_id": cliente_id,
                        "email": usuario_email,
                        "senha": usuario_senha,
                        "perfil": "cliente",
                        "nome": usuario_nome
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
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar cadastro: {e}")


def render_gerenciar_obrigacoes():
    st.title("🗂️ Gerenciar Obrigações (Contador)")
    st.markdown("Cadastre obrigações para clientes. Essas entradas serão gravadas na tabela `tarefas`.")

    clientes = carregar_clientes()
    if not clientes:
        st.warning("Cadastre ao menos um cliente antes de lançar obrigações.")
        return

    with st.form("form_gerenciar_obrigacoes"):
        cliente_selecionado = st.selectbox("Selecione o Cliente:", [c["nome"] for c in clientes])
        nome_ob = st.text_input("Nome da Obrigação (ex: DAS, GIA, Folha de Pagamento)")
        vencimento = st.text_input("Data de Vencimento (por extenso)")
        status_inicial = st.selectbox("Status Inicial:", ["Pendente", "Concluído"], index=0)
        periodicidade = st.selectbox("Periodicidade:", ["Mensal", "Trimestral", "Anual", "Eventual"], index=0)
        mes_padrao = st.selectbox("Mês (opcional)", [""] + LISTA_MESES, index=0)
        ano_padrao = st.selectbox("Ano (opcional)", [""] + LISTA_ANOS, index=0)

        if st.form_submit_button("Cadastrar Obrigação"):
            if not nome_ob or not vencimento:
                st.error("Preencha o nome da obrigação e a data de vencimento.")
            else:
                cliente_id = next(c["id"] for c in clientes if c["nome"] == cliente_selecionado)
                supabase.table("tarefas").insert({
                    "cliente_id": cliente_id,
                    "obrigacao": nome_ob,
                    "vencimento": vencimento,
                    "periodicidade": periodicidade,
                    "mes": mes_padrao if mes_padrao else None,
                    "ano": ano_padrao if ano_padrao else None,
                    "alerta": "✅ Normal",
                    "status": status_inicial
                }).execute()
                st.success("Obrigação cadastrada com sucesso.")

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


def render_portal_cliente():
    cli_res = supabase.table("clientes").select("*").eq("id", st.session_state.cliente_id_logado).execute()
    if not cli_res.data:
        st.error("Cliente não encontrado.")
        return

    cliente = cli_res.data[0]
    st.title(f"👤 Portal do Cliente - {cliente['nome']}")
    st.markdown("Acesse seus documentos institucionais e guias fiscais por competência.")

    tab_fixos, tab_mensais = st.tabs(["📁 Documentos Fixos da Empresa", "📅 Guias e Documentos Mensais"])

    with tab_fixos:
        docs_fixos = supabase.table("documentos_fixos").select("*").eq("cliente_id", cliente["id"]).execute().data or []
        if docs_fixos:
            df_fixos = pd.DataFrame(docs_fixos)
            # show simple table with download links
            for doc in docs_fixos:
                st.write(f"**{doc['tipo_documento']}** — {doc['nome_arquivo']}")
                try:
                    assinatura = supabase.storage.from_("documentos-fixos").create_signed_url(doc["caminho_storage"], 60)
                    st.markdown(f"<a href=\"{assinatura['signedUrl']}\" target=\"_blank\">Abrir / Baixar</a>", unsafe_allow_html=True)
                except Exception:
                    st.caption("Erro ao gerar link seguro.")
        else:
            st.info("Nenhum documento institucional anexado ainda.")

    with tab_mensais:
        col_a, col_b = st.columns([1, 1])
        with col_a:
            ano_filtrado = st.selectbox("Filtrar por ano:", ["Todos"] + LISTA_ANOS, index=1)
        with col_b:
            mes_filtrado = st.selectbox("Filtrar por mês:", ["Todos"] + LISTA_MESES, index=datetime.now().month)

        query = supabase.table("arquivos_escritorio").select("*").eq("cliente_id", cliente["id"])
        if ano_filtrado != "Todos":
            query = query.eq("ano", ano_filtrado)
        if mes_filtrado != "Todos":
            query = query.eq("mes", mes_filtrado)
        arquivos = query.execute().data or []

        if arquivos:
            for arq in arquivos:
                col_arq, col_btn = st.columns([3, 1])
                with col_arq:
                    st.markdown(f"📄 **{arq['nome_arquivo']}**")
                    st.caption(f"Disponibilizado em: {arq.get('data_publicacao', '-')}")
                with col_btn:
                    try:
                        assinatura = supabase.storage.from_("documentos-clientes").create_signed_url(arq["caminho_storage"], 60)
                        st.markdown(f"<a href=\"{assinatura['signedUrl']}\" target=\"_blank\">⬇️ Baixar</a>", unsafe_allow_html=True)
                    except Exception:
                        st.error("Erro ao gerar link de download.")
        else:
            st.warning("Nenhum documento mensal disponível para o período selecionado.")


# --- FLUXO PRINCIPAL ---
if not st.session_state.logado:
    st.title("🔑 Acesso ao Sistema - Vieira Controller")
    st.markdown("Faça login para acessar o painel de gestão contábil e fiscal.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            usuario = st.text_input("Usuário ou E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                realizar_login(usuario, senha)
else:
    st.sidebar.header("Navegação")
    if st.sidebar.button("Sair / Logout"):
        st.session_state.logado = False
        st.session_state.perfil = None
        st.session_state.cliente_id_logado = None
        st.experimental_rerun()

    if st.session_state.perfil == "escritorio":
        opcao = st.sidebar.radio("Menu:", [
            "Dashboard Geral",
            "Documentos e Tarefas",
            "Cadastrar Cliente",
            "Gerenciar Obrigações",
            "Obrigações Customizadas"
        ])

        if opcao == "Dashboard Geral":
            render_dashboard()
        elif opcao == "Documentos e Tarefas":
            render_upload_documentos()
        elif opcao == "Cadastrar Cliente":
            render_cadastrar_cliente()
        elif opcao == "Gerenciar Obrigações":
            render_gerenciar_obrigacoes()
        elif opcao == "Obrigações Customizadas":
            render_obrigacoes_customizadas()
    else:
        st.sidebar.write(f"Conectado como: **CLIENTE**")
        st.sidebar.markdown("---")
        render_portal_cliente()
