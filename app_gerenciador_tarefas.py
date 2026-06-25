import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions

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
        supabase_key = secret_key
        headers = {
            "apikey": secret_key,
            "apiKey": secret_key,
            "Authorization": f"Bearer {secret_key}"
        }
    elif public_key:
        supabase_key = public_key
        headers = {
            "apikey": public_key,
            "apiKey": public_key
        }
    else:
        raise ValueError("Nenhuma chave Supabase foi configurada. Adicione public_key e/ou secret_key nos secrets.")

    return create_client(url, supabase_key, options=SyncClientOptions(headers=headers))

try:
    supabase = inicializar_supabase()
except Exception as e:
    st.error(f"Erro real: {e}")
    st.stop()

# --- CONFIGURAÇÕES DE ENUMERADORES ---
LISTA_ANOS = ["2025", "2026", "2027"]
LISTA_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
TIPOS_DOCS_FIXOS = ["Contrato Social / Alterações", "Cartão CNPJ", "Procuração Eletrônica", "Inscrição Estadual/Municipal", "Senha de Acessos / Códigos", "Outros Documentos Fixos"]

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
        st.rerun()
    else:
        res = supabase.table("usuarios_clientes").select("*").eq("email", usuario).eq("senha", senha).execute()
        if res.data:
            st.session_state.logado = True
            st.session_state.perfil = "cliente"
            st.session_state.cliente_id_logado = res.data[0]["cliente_id"]
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

if not st.session_state.logado:
    st.title("🔑 Acesso ao Sistema - Vieira Controller")
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("form_login"):
            user_input = st.text_input("Usuário ou E-mail")
            pass_input = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                realizar_login(user_input, pass_input)
else:
    st.sidebar.write(f"Conectado como: **{st.session_state.perfil.upper()}**")
    if st.sidebar.button("Sair / Logout"):
        st.session_state.logado = False
        st.session_state.perfil = None
        st.session_state.cliente_id_logado = None
        st.rerun()
    st.sidebar.markdown("---")

    # --- VISÃO 1: ESCRITÓRIO (CONTADOR) ---
    if st.session_state.perfil == "escritorio":
        menu = st.sidebar.radio("Navegação do Escritório:", [
            "Dashboard Geral", 
            "Upload de Documentos Fixos",
            "Cadastrar Cliente", 
            "Configurar Acessos", 
            "Gerenciar Obrigações Customizadas"
        ])
        
        try:
            clientes_res = supabase.table("clientes").select("*").order("nome").execute()
            lista_clientes_db = clientes_res.data if clientes_res.data else []
        except Exception as e:
            st.error(f"Erro de conexão Supabase: {e}")
            st.stop()

        if menu == "Dashboard Geral":
            st.title("📊 Painel de Controle de Obrigações Contábeis")
            
            st.markdown("### 🔍 Filtros de Visualização")
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filtro_cliente = st.selectbox("Filtrar por Cliente:", ["Todos os Clientes"] + [c["nome"] for c in lista_clientes_db])
            with col_f2:
                filtro_mes = st.selectbox("Filtrar por Mês Competência:", ["Todos os Meses"] + LISTA_MESES, index=datetime.now().month - 1)
            with col_f3:
                filtro_ano = st.selectbox("Filtrar por Ano Competência:", ["Todos os Anos"] + LISTA_ANOS, index=1)

            tarefas_res = supabase.table("tarefas").select("*").execute()
            df_tarefas = pd.DataFrame(tarefas_res.data) if tarefas_res.data else pd.DataFrame()
            df_clientes = pd.DataFrame(lista_clientes_db)

            if not df_tarefas.empty and not df_clientes.empty:
                df_fused = pd.merge(df_tarefas, df_clientes, left_on="cliente_id", right_on="id")
                
                if filtro_cliente != "Todos os Clientes":
                    df_fused = df_fused[df_fused["nome"] == filtro_cliente]
                if filtro_mes != "Todos os Meses":
                    df_fused = df_fused[df_fused["mes"] == filtro_mes]
                if filtro_ano != "Todos os Anos":
                    df_fused = df_fused[df_fused["ano"] == filtro_ano]

                st.markdown("#### 📈 Indicadores de Produtividade do Período")
                if not df_fused.empty:
                    contagem = df_fused["status"].value_counts().to_dict()
                    concluidas = contagem.get("Concluído", 0)
                    pendentes = contagem.get("Pendente", 0)
                    
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Obrigações Concluídas ✅", concluidas)
                    col_m2.metric("Obrigações Pendentes ⏳", pendentes)
                    col_m3.metric("Total Filtrado", len(df_fused))
                    
                    df_grafico = df_fused["status"].value_counts().reset_index()
                    df_grafico.columns = ["Status", "Quantidade"]
                    fig = px.bar(df_grafico, x="Status", y="Quantidade", color="Status", 
                                 color_discrete_map={"Concluído": "#2ecc71", "Pendente": "#e74c3c"}, text_auto=True, height=280)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("#### 📋 Listagem de Obrigações")
                    df_exibicao = df_fused[["alerta", "nome", "obrigacao", "periodicidade", "mes", "ano", "vencimento", "status"]]
                    df_exibicao.columns = ["Prioridade", "Cliente", "Obrigação", "Periodicidade", "Mês", "Ano", "Prazo", "Status"]
                    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

                    st.markdown("### ⚡ Enviar Documento Mensal e Concluir Tarefa")
                    opcoes_tarefas = {f"{row['nome']} - {row['obrigacao']} ({row['mes']}/{row['ano']})": row['id_x'] for idx, row in df_fused.iterrows() if row['status'] == 'Pendente'}
                    
                    if opcoes_tarefas:
                        with st.form("form_baixa_real"):
                            tarefa_selecionada = st.selectbox("Escolha a obrigação para dar baixa:", list(opcoes_tarefas.keys()))
                            arquivo_guia = st.file_uploader("Anexar Guia Fiscal (PDF/XML):", type=["pdf", "xml", "zip", "xlsx"])
                            
                            if st.form_submit_button("Enviar para o Cliente e Marcar como Concluído"):
                                id_tarefa = opcoes_tarefas[tarefa_selecionada]
                                tarefa_objeto = next(t for t in tarefas_res.data if t["id"] == id_tarefa)
                                
                                if arquivo_guia:
                                    nome_limpo = f"{id_tarefa}_{arquivo_guia.name}"
                                    caminho_storage = f"guias/{nome_limpo}"
                                    
                                    supabase.storage.from_("documentos-clientes").upload(
                                        path=caminho_storage, file=arquivo_guia.getvalue(),
                                        file_options={"content-type": arquivo_guia.type}
                                    )
                                    
                                    supabase.table("arquivos_escritorio").insert({
                                        "cliente_id": tarefa_objeto["cliente_id"], "ano": tarefa_objeto["ano"], "mes": tarefa_objeto["mes"],
                                        "nome_arquivo": arquivo_guia.name, "caminho_storage": caminho_storage,
                                        "data_publicacao": datetime.now().strftime("%d/%m/%Y %H:%M")
                                    }).execute()

                                supabase.table("tarefas").update({"status": "Concluído", "alerta": "✅ Normal"}).eq("id", id_tarefa).execute()
                                st.success("Guia enviada com sucesso!")
                                st.rerun()
                    else:
                        st.success("🎉 Todas as obrigações filtradas já estão resolvidas!")
                else:
                    st.info("Nenhuma obrigação encontrada para este filtro.")

        elif menu == "Upload de Documentos Fixos":
            st.title("📌 Upload de Documentos Fixos / Institucionais")
            st.caption("Arquivos permanentes (Contrato Social, CNPJ) salvos no balde seguro 'documentos-fixos'")
            
            if lista_clientes_db:
                with st.form("form_doc_fixo"):
                    c_nome = st.selectbox("Selecione o Cliente:", [c["nome"] for c in lista_clientes_db])
                    tipo_doc = st.selectbox("Tipo de Documento:", TIPOS_DOCS_FIXOS)
                    arquivo_upload = st.file_uploader("Selecione o Arquivo (PDF/Imagens):", type=["pdf", "jpg", "png"])
                    
                    if st.form_submit_button("Salvar Documento Fixo"):
                        if arquivo_upload:
                            id_c = next(c["id"] for c in lista_clientes_db if c["nome"] == c_nome)
                            nome_limpo = f"{id_c}_{int(datetime.now().timestamp())}_{arquivo_upload.name}"
                            caminho_storage = f"arquivos/{nome_limpo}"
                            
                            # Envia direcionado para o balde exclusivo 'documentos-fixos'
                            supabase.storage.from_("documentos-fixos").upload(
                                path=caminho_storage, file=arquivo_upload.getvalue(),
                                file_options={"content-type": arquivo_upload.type}
                            )
                            
                            # Registra na tabela de controle
                            supabase.table("documentos_fixos").insert({
                                "cliente_id": id_c, "tipo_documento": tipo_doc,
                                "nome_arquivo": arquivo_upload.name, "caminho_storage": caminho_storage
                            }).execute()
                            
                            st.success(f"O documento '{tipo_doc}' foi guardado com sucesso!")
                        else:
                            st.error("Por favor, anexe um arquivo antes de salvar.")

        elif menu == "Cadastrar Cliente":
            st.title("➕ Cadastrar Novo Cliente")
            with st.form("form_cliente"):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    nome = st.text_input("Razão Social")
                    cnpj = st.text_input("CNPJ")
                    regime = st.selectbox("Regime Tributário", ["Simples Nacional", "Lucro Presumido", "Lucro Real"])
                with col_c2:
                    email = st.text_input("E-mail Comercial")
                    telefone = st.text_input("Telefone")
                    socios = st.text_area("Sócios")
                
                tem_folha = st.checkbox("Possui folha de pagamento?")
                
                if st.form_submit_button("Salvar Cliente"):
                    if nome and cnpj:
                        ins_res = supabase.table("clientes").insert({
                            "nome": nome, "cnpj": cnpj, "regime": regime, "email": email, "telefone": telefone, "socios": socios, "tem_folha": tem_folha
                        }).execute()
                        
                        if ins_res.data:
                            novo_id = ins_res.data[0]["id"]
                            for ob in OBRIGACOES_BASE[regime]:
                                supabase.table("tarefas").insert({
                                    "cliente_id": novo_id, "obrigacao": ob["obrigacao"], "vencimento": ob["prazo"],
                                    "periodicidade": ob["periodicidade"], "mes": LISTA_MESES[datetime.now().month - 1], "ano": "2026"
                                }).execute()
                            st.success(f"Cliente {nome} salvo com sucesso!")

        elif menu == "Configurar Acessos":
            st.title("🔑 Credenciais de Acesso do Cliente")
            if lista_clientes_db:
                with st.form("form_acesso"):
                    c_nome = st.selectbox("Escolha o Cliente:", [c["nome"] for c in lista_clientes_db])
                    c_email = st.text_input("E-mail/Usuário de Login")
                    c_senha = st.text_input("Senha Provisória", type="password")
                    
                    if st.form_submit_button("Gerar Usuário"):
                        id_c = next(c["id"] for c in lista_clientes_db if c["nome"] == c_nome)
                        supabase.table("usuarios_clientes").insert({"cliente_id": id_c, "email": c_email, "senha": c_senha}).execute()
                        st.success("Acesso liberado!")

        elif menu == "Gerenciar Obrigações Customizadas":
            st.title("⚙️ Lançar Obrigação Manual/Avulsa")
            if lista_clientes_db:
                with st.form("form_custom"):
                    c_nome = st.selectbox("Selecione o Cliente:", [c["nome"] for c in lista_clientes_db])
                    nome_ob = st.text_input("Nome do Imposto/Obrigação")
                    prazo_ob = st.text_input("Vencimento por extenso")
                    m_ob = st.selectbox("Mês:", LISTA_MESES, index=datetime.now().month - 1)
                    a_ob = st.selectbox("Ano:", LISTA_ANOS, index=1)
                    alerta_ob = st.selectbox("Prioridade:", ["🚨 Urgente", "⚠️ Atenção", "✅ Normal"])
                    
                    if st.form_submit_button("Lançar no Painel"):
                        id_c = next(c["id"] for c in lista_clientes_db if c["nome"] == c_nome)
                        supabase.table("tarefas").insert({
                            "cliente_id": id_c, "obrigacao": nome_ob, "vencimento": prazo_ob,
                            "periodicidade": "Eventual", "mes": m_ob, "ano": a_ob, "alerta": alerta_ob
                        }).execute()
                        st.success("Obrigação adicionada!")

    # --- VISÃO 2: PORTAL DO CLIENTE (EMPRESA) ---
    elif st.session_state.perfil == "cliente":
        cli_res = supabase.table("clientes").select("*").eq("id", st.session_state.cliente_id_logado).execute()
        if cli_res.data:
            info_c = cli_res.data[0]
            st.title(f"👤 Central de Atendimento - {info_c['nome']}")
            
            # ----------------------------------------------------
            # DOCUMENTOS FIXOS EMPRESARIAIS (BALDE: documentos-fixos)
            # ----------------------------------------------------
            st.markdown("### 📌 Documentos da Empresa (Acesso Permanente)")
            docs_fixos_res = supabase.table("documentos_fixos").select("*").eq("cliente_id", info_c["id"]).execute()
            
            if docs_fixos_res.data:
                col_fixo_1, col_fixo_2 = st.columns(2)
                for index, doc in enumerate(docs_fixos_res.data):
                    col_alvo = col_fixo_1 if index % 2 == 0 else col_fixo_2
                    with col_alvo:
                        with st.container(border=True):
                            st.write(f"📂 **{doc['tipo_documento']}**")
                            st.caption(f"Arquivo: {doc['nome_arquivo']}")
                            try:
                                # Busca o link temporário apontando para o bucket correto
                                url_temp = supabase.storage.from_("documentos-fixos").create_signed_url(doc["caminho_storage"], 60)
                                st.markdown(f'<a href="{url_temp["signedUrl"]}" target="_blank"><button style="background-color:#3498db; color:white; border:none; padding:6px 12px; border-radius:4px; cursor:pointer; width:100%;">Visualizar / Baixar</button></a>', unsafe_allow_html=True)
                            except:
                                st.caption("⚠️ Erro ao gerar link seguro.")
            else:
                st.info("Nenhum documento institucional fixo anexado até o momento.")
                
            st.markdown("---")
            
            # SEÇÃO TRADICIONAL DAS GUIAS DO MÊS (BALDE: documentos-clientes)
            st.markdown("### 📥 Impostos e Guias Mensais Recentes")
            col_fc1, col_fc2 = st.columns(2)
            with col_fc1: filtro_ano_c = st.selectbox("Filtrar Ano:", LISTA_ANOS, index=1)
            with col_fc2: filtro_mes_c = st.selectbox("Filtrar Mês:", LISTA_MESES, index=datetime.now().month - 1)
            
            arquivos_res = supabase.table("arquivos_escritorio").select("*").eq("cliente_id", info_c["id"]).eq("ano", filtro_ano_c).eq("mes", filtro_mes_c).execute()
            
            if arquivos_res.data:
                for arq in arquivos_res.data:
                    col_arq, col_btn = st.columns([3, 1])
                    with col_arq:
                        st.markdown(f"📄 **{arq['nome_arquivo']}**")
                        st.caption(f"Disponibilizado em: {arq['data_publicacao']}")
                    with col_btn:
                        try:
                            url_temporaria = supabase.storage.from_("documentos-clientes").create_signed_url(arq["caminho_storage"], 60)
                            st.markdown(f'<a href="{url_temporaria["signedUrl"]}" target="_blank"><button style="background-color:#2ecc71; color:white; border:none; padding:6px 12px; border-radius:4px; cursor:pointer;">⬇️ Baixar</button></a>', unsafe_allow_html=True)
                        except:
                            st.error("Erro no link.")
            else:
                st.warning("Nenhuma guia lançada para o período selecionado.")
