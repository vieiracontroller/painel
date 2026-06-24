import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Gestão Vieira Controller", layout="wide")

# --- LISTA DOS PRINCIPAIS BANCOS NO BRASIL ---
LISTA_BANCOS = [
    "Banco do Brasil (001)", "Bradesco (237)", "Itaú Unibanco (341)", "Santander (033)", 
    "Caixa Econômica Federal (104)", "Sicoob (756)", "Sicredi (748)", "Banco Inter (077)", 
    "Nubank (260)", "C6 Bank (336)", "BTG Pactual (208)", "Safra (422)", "Banrisul (041)", 
    "Original (212)", "Neon (536)", "PagBank (290)", "Stone / Banco Segur_ (197)", "Outro Banco..."
]

LISTA_ANOS = ["2025", "2026", "2027"]
LISTA_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
CATEGORIAS_FIXAS = ["Cartão CNPJ", "Contrato Social", "Alvará de Funcionamento", "Inscrição Estadual / Municipal", "Regime Tributário (Opção)", "Outros Documentos Fixos"]

# --- 1. DEFINIÇÃO DAS OBRIGAÇÕES BASE ---
OBRIGACOES_BASE = {
    "Simples Nacional": [
        {"obrigacao": "DAS", "prazo": "Até o dia 15", "periodicidade": "Mensal"},
        {"obrigacao": "DEFIS", "prazo": "Até 31/03", "periodicidade": "Anual"},
        {"obrigacao": "Controle Faturamento", "prazo": "Mensal", "periodicidade": "Mensal"}
    ],
    "Lucro Presumido": [
        {"obrigacao": "PIS/COFINS", "prazo": "Até o dia 20", "periodicidade": "Mensal"},
        {"obrigacao": "IRPJ/CSLL", "prazo": "Até o dia 25", "periodicidade": "Trimestral"},
        {"obrigacao": "ECD", "prazo": "Até 31/05", "periodicidade": "Anual"},
        {"obrigacao": "ECF", "prazo": "Até 31/05", "periodicidade": "Anual"}
    ],
    "Lucro Real": [
        {"obrigacao": "PIS/COFINS", "prazo": "Até o dia 20", "periodicidade": "Mensal"},
        {"obrigacao": "IRPJ/CSLL", "prazo": "Até o dia 25", "periodicidade": "Trimestral"},
        {"obrigacao": "ECD", "prazo": "Até 31/05", "periodicidade": "Anual"},
        {"obrigacao": "ECF", "prazo": "Até 31/05", "periodicidade": "Anual"}
    ]
}

# --- 2. BANCO DE DADOS EM MEMÓRIA (SESSÃO) ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = [
        {
            "id": 1, "nome": "Empresa Alfa", "cnpj": "12.345.678/0001-00", "regime": "Simples Nacional", 
            "tem_ie": True, "ie_numero": "12345678-9", "endereco": "Av. JK, Centro, Palmas - TO",
            "telefone": "(63) 99999-1111", "email": "contato@alfa.com", "socios": "Fernanda Vieira (CPF: 000.000.000-00)",
            "tem_folha": True, "fechamento_real": "Não se aplica"
        },
        {
            "id": 2, "nome": "Beta Alimentos", "cnpj": "98.765.432/0001-99", "regime": "Lucro Presumido", 
            "tem_ie": False, "ie_numero": "", "endereco": "Palmas - TO",
            "telefone": "(63) 99999-2222", "email": "beta@alimentos.com", "socios": "Sócio Exemplo",
            "tem_folha": False, "fechamento_real": "Não se aplica"
        }
    ]

if 'usuarios_clientes' not in st.session_state:
    st.session_state.usuarios_clientes = {
        "contato@alfa.com": {"senha": "cliente123", "cliente_id": 1},
        "beta@alimentos.com": {"senha": "beta123", "cliente_id": 2}
    }

if 'tarefas' not in st.session_state:
    # Ajustado estrutura para conter Mês e Ano de competência da obrigação
    st.session_state.tarefas = [
        {"id": 1, "cliente_id": 1, "obrigacao": "DAS", "vencimento": "Até o dia 15", "periodicidade": "Mensal", "mes": "Junho", "ano": "2026", "alerta": "🚨 Urgente", "status": "Pendente"},
        {"id": 2, "cliente_id": 1, "obrigacao": "ICMS Complementar", "vencimento": "Até o dia 07", "periodicidade": "Mensal", "mes": "Junho", "ano": "2026", "alerta": "⚠️ Atenção", "status": "Pendente"},
        {"id": 3, "cliente_id": 1, "obrigacao": "Fechamento Folha de Pagamento", "vencimento": "Até o 5º dia útil", "periodicidade": "Mensal", "mes": "Junho", "ano": "2026", "alerta": "✅ Normal", "status": "Concluído"},
        {"id": 4, "cliente_id": 2, "obrigacao": "PIS/COFINS", "vencimento": "Até o dia 20", "periodicidade": "Mensal", "mes": "Junho", "ano": "2026", "alerta": "🚨 Urgente", "status": "Pendente"}
    ]

if 'arquivos_escritorio' not in st.session_state:
    st.session_state.arquivos_escritorio = []

if 'documentos_fixos' not in st.session_state:
    st.session_state.documentos_fixos = []

if 'envios_cliente_protocolo' not in st.session_state:
    st.session_state.envios_cliente_protocolo = []


# --- 3. CONTROLE DE ACESSO / LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.perfil = None  
    st.session_state.cliente_id_logado = None

def realizar_login(usuario, senha):
    if usuario == "vieiracontroller" and senha == "123456":
        st.session_state.logado = True
        st.session_state.perfil = "escritorio"
        st.success("Logado como Escritório Master!")
        st.rerun()
    elif usuario in st.session_state.usuarios_clientes:
        if st.session_state.usuarios_clientes[usuario]["senha"] == senha:
            st.session_state.logado = True
            st.session_state.perfil = "cliente"
            st.session_state.cliente_id_logado = st.session_state.usuarios_clientes[usuario]["cliente_id"]
            st.success("Logado com sucesso!")
            st.rerun()
        else:
            st.error("Senha incorreta.")
    else:
        st.error("Usuário não encontrado.")

def realizar_logout():
    st.session_state.logado = False
    st.session_state.perfil = None
    st.session_state.cliente_id_logado = None
    st.rerun()

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔑 Acesso ao Sistema - Vieira Controller")
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("form_login"):
            user_input = st.text_input("Usuário ou E-mail")
            pass_input = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                realizar_login(user_input, pass_input)

# --- SISTEMA PÓS LOGIN ---
else:
    st.sidebar.write(f"Conectado como: **{st.session_state.perfil.upper()}**")
    if st.sidebar.button("Sair / Logout"):
        realizar_logout()
    st.sidebar.markdown("---")

    # --- MENUS DO ESCRITÓRIO ---
    if st.session_state.perfil == "escritorio":
        menu = st.sidebar.radio("Navegação do Escritório:", ["Dashboard Geral", "Cadastrar Cliente", "Configurar Acessos", "Gerenciar Obrigações Customizadas", "Enviar Arquivos avulsos"])
        
        if menu == "Dashboard Geral":
            st.title("📊 Painel de Controle de Obrigações Contábeis")
            
            # FILTROS GRÁFICOS E DE TABELA (MÊS E ANO)
            st.markdown("### 🔍 Filtros de Visualização")
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filtro_cliente = st.selectbox("Filtrar por Cliente:", ["Todos os Clientes"] + [c["nome"] for c in st.session_state.clientes])
            with col_f2:
                filtro_mes = st.selectbox("Filtrar por Mês Competência:", ["Todos os Meses"] + LISTA_MESES, index=6) # Padrão Junho
            with col_f3:
                filtro_ano = st.selectbox("Filtrar por Ano Competência:", ["Todos os Anos"] + LISTA_ANOS, index=2) # Padrão 2026

            # PROCESSAMENTO DOS DADOS FILTRADOS
            df_tarefas = pd.DataFrame(st.session_state.tarefas)
            df_clientes = pd.DataFrame(st.session_state.clientes)
            
            if not df_tarefas.empty and not df_clientes.empty:
                df_fused = pd.merge(df_tarefas, df_clientes, left_on="cliente_id", right_on="id")
                
                # Aplicando os filtros selecionados pelo usuário
                if filtro_cliente != "Todos os Clientes":
                    df_fused = df_fused[df_fused["nome"] == filtro_cliente]
                if filtro_mes != "Todos os Meses":
                    df_fused = df_fused[df_fused["mes"] == filtro_mes]
                if filtro_ano != "Todos os Anos":
                    df_fused = df_fused[df_fused["ano"] == filtro_ano]

                # --- SEÇÃO DE GRÁFICOS ---
                st.markdown("#### 📈 Indicadores de Produtividade do Período")
                if not df_fused.empty:
                    contagem_status = df_fused["status"].value_counts().to_dict()
                    concluidas = contagem_status.get("Concluido", 0)
                    pendentes = contagem_status.get("Pendente", 0)
                    
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Obrigações Concluidas ✅", concluidas)
                    col_m2.metric("Obrigações Pendentes ⏳", pendentes)
                    col_m3.metric("Total no Filtro", len(df_fused))
                    
                    # Gráfico Plotly Express
                    df_grafico = df_fused["status"].value_counts().reset_index()
                    df_grafico.columns = ["Status", "Quantidade"]
                    fig = px.bar(df_grafico, x="Status", y="Quantidade", color="Status", 
                                 color_discrete_map={"Concluído": "#2ecc71", "Pendente": "#e74c3c"},
                                 text_auto=True, height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhum dado encontrado para gerar gráficos com os filtros selecionados.")
                
                st.markdown("---")
                st.markdown("#### 📋 Listagem de Obrigações Encontradas")
                
                # Exibição estruturada da tabela similar à image_d035e0.png
                if not df_fused.empty:
                    df_exibicao = df_fused[["id_x", "alerta", "nome", "obrigacao", "periodicidade", "mes", "ano", "vencimento", "status"]]
                    df_exibicao.columns = ["ID", "Prioridade/Prazo", "Cliente", "Obrigação", "Periodicidade", "Mês", "Ano", "Prazo de Vencimento", "Status"]
                    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
                    
                    # --- OPERAÇÃO DIRETA NA LINHA (MARCAR CONCLUÍDO / ANEXAR GUIA) ---
                    st.markdown("### ⚡ Ações Rápidas na Obrigação")
                    st.write("Selecione uma obrigação na lista abaixo para dar baixa ou anexar o imposto gerado:")
                    
                    # Apenas obrigações que estão listadas no filtro atual
                    opcoes_tarefas = {f"ID {row['ID']} - {row['Cliente']} - {row['Obrigação']} ({row['Mês']}/{row['Ano']})": row['ID'] for index, row in df_exibicao.iterrows() if row['Status'] == 'Pendente'}
                    
                    if opcoes_tarefas:
                        with st.form("form_baixa_rapida"):
                            tarefa_selecionada = st.selectbox("Escolha qual obrigação deseja concluir/anexar:", list(opcoes_tarefas.keys()))
                            opcao_acao = st.radio("Ação desejada:", ["Apenas marcar como Concluído", "Anexar documento da guia e mudar para Concluído"])
                            
                            arquivo_guia = None
                            if opcao_acao == "Anexar documento da guia e mudar para Concluído":
                                arquivo_guia = st.file_uploader("Anexar arquivo da Guia/Imposto (PDF, XML, ZIP):", type=["pdf", "xml", "xlsx", "zip", "txt"])
                                
                            if st.form_submit_button("Salvar Alteração e Notificar Cliente"):
                                id_tarefa_alvo = opcoes_tarefas[tarefa_selecionada]
                                
                                # Localiza a tarefa na lista original do session_state
                                for idx, t in enumerate(st.session_state.tarefas):
                                    if t["id"] == id_tarefa_alvo:
                                        st.session_state.tarefas[idx]["status"] = "Concluído"
                                        st.session_state.tarefas[idx]["alerta"] = "✅ Normal"
                                        
                                        # Se anexou arquivo, salva ele na central do cliente automaticamente
                                        if opcao_acao == "Anexar documento da guia e mudar para Concluído" and arquivo_guia is not None:
                                            agora_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                            st.session_state.arquivos_escritorio.append({
                                                "cliente_id": t["cliente_id"],
                                                "ano": t["ano"],
                                                "mes": t["mes"],
                                                "nome_arquivo": arquivo_guia.name,
                                                "conteudo": arquivo_guia.read(),
                                                "data_publicacao": agora_str
                                            })
                                            st.success(f"Documento '{arquivo_guia.name}' foi publicado e anexado com sucesso!")
                                        
                                        st.success("Atividade atualizada com sucesso! Painel atualizado.")
                                        st.rerun()
                    else:
                        st.success("🎉 Todas as obrigações listadas neste filtro já estão concluídas!")
                else:
                    st.info("Nenhuma obrigação correspondente aos filtros.")
            else:
                st.info("Nenhuma obrigação cadastrada no sistema.")
                
            st.markdown("---")
            st.markdown("### 🕒 Protocolos Recentes Recebidos dos Clientes")
            if st.session_state.envios_cliente_protocolo:
                df_envios = pd.DataFrame(st.session_state.envios_cliente_protocolo)
                df_envios_fused = pd.merge(df_envios, df_clientes, left_on="cliente_id", right_on="id")
                st.dataframe(df_envios_fused[["data_hora", "nome", "tipo_documento", "competencia", "nome_arquivo"]], use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhum arquivo enviado por clientes nas últimas horas.")

        elif menu == "Cadastrar Cliente":
            st.title("➕ Cadastrar Novo Cliente")
            with st.form("form_cliente"):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    nome = st.text_input("Razão Social / Nome Fantasia")
                    cnpj = st.text_input("CNPJ")
                    regime = st.selectbox("Regime Tributário", ["Simples Nacional", "Lucro Presumido", "Lucro Real"])
                    endereco = st.text_input("Endereço Completo")
                with col_c2:
                    telefone = st.text_input("Telefone de Contato (Com DDD)")
                    email = st.text_input("E-mail de Contato")
                    socios = st.text_area("Sócios e CPFs")

                st.markdown("### Configurações Específicas")
                tem_ie = st.checkbox("Cliente possui Inscrição Estadual (IE)?")
                ie_numero = st.text_input("Número da Inscrição Estadual (IE)") if tem_ie else ""
                tem_folha = st.checkbox("Cliente possui Folha de Pagamento?")
                fechamento_real = st.selectbox("Tipo de Fechamento de Balanço e DRE", ["Mensal", "Trimestral", "Anual"]) if regime == "Lucro Real" else "Não se aplica"
                    
                if st.form_submit_button("Salvar Cliente e Gerar Obrigações"):
                    if nome and cnpj:
                        novo_id = len(st.session_state.clientes) + 1
                        st.session_state.clientes.append({
                            "id": novo_id, "nome": nome, "cnpj": cnpj, "regime": regime, "tem_ie": tem_ie, "ie_numero": ie_numero, 
                            "endereco": endereco, "telefone": telefone, "email": email, "socios": socios, "tem_folha": tem_folha, "fechamento_real": fechamento_real
                        })
                        # Geração base para o mês vigente padrão
                        for ob in OBRIGACOES_BASE[regime]:
                            st.session_state.tarefas.append({"id": len(st.session_state.tarefas) + 1, "cliente_id": novo_id, "obrigacao": ob["obrigacao"], "vencimento": ob["prazo"], "periodicidade": ob["periodicidade"], "mes": "Junho", "ano": "2026", "alerta": "✅ Normal", "status": "Pendente"})
                        st.success(f"Cliente '{nome}' cadastrado com obrigações geradas para Junho/2026!")

        elif menu == "Configurar Acessos":
            st.title("🔑 Configurar Acessos e Logins dos Clientes")
            df_clientes = pd.DataFrame(st.session_state.clientes)
            if not df_clientes.empty:
                with st.form("form_criar_acesso"):
                    cliente_selecionado = st.selectbox("Selecione o Cliente:", df_clientes["nome"].tolist())
                    novo_usuario = st.text_input("Definir Usuário/E-mail de Login")
                    nova_senha = st.text_input("Definir Senha de Acesso", type="password")
                    if st.form_submit_button("Gerar Credencial"):
                        if novo_usuario and nova_senha:
                            id_c = df_clientes[df_clientes["nome"] == cliente_selecionado]["id"].values[0]
                            st.session_state.usuarios_clientes[novo_usuario] = {"senha": nova_senha, "cliente_id": int(id_c)}
                            st.success("Acesso configurado!")

        elif menu == "Gerenciar Obrigações Customizadas":
            st.title("⚙️ Lançar e Personalizar Obrigações Avulsas")
            df_clientes = pd.DataFrame(st.session_state.clientes)
            if not df_clientes.empty:
                with st.form("form_nova_obrigacao_custom"):
                    c_alvo = st.selectbox("Vincular ao Cliente:", df_clientes["nome"].tolist())
                    nome_obrigacao = st.text_input("Nome da Obrigação Extra")
                    prazo_venc = st.text_input("Prazo / Data de Vencimento por Extenso")
                    periodicidade_sel = st.selectbox("Periodicidade da Obrigação:", ["Mensal", "Trimestral", "Semestral", "Anual", "Eventual / Única"])
                    comp_m = st.selectbox("Mês Mapeado:", LISTA_MESES, index=5)
                    comp_a = st.selectbox("Ano Mapeado:", LISTA_ANOS, index=1)
                    nivel_alerta = st.selectbox("Definir Alerta Visual de Prazo:", ["🚨 Urgente", "⚠️ Atenção", "✅ Normal"])
                    status_inicial = st.selectbox("Status Inicial:", ["Pendente", "Concluído"])
                    
                    if st.form_submit_button("Lançar Obrigação no Painel"):
                        if nome_obrigacao and prazo_venc:
                            id_alvo = df_clientes[df_clientes["nome"] == c_alvo]["id"].values[0]
                            st.session_state.tarefas.append({
                                "id": len(st.session_state.tarefas) + 1, "cliente_id": int(id_alvo), "obrigacao": nome_obrigacao,
                                "vencimento": prazo_venc, "periodicidade": periodicidade_sel, "mes": comp_m, "ano": comp_a,
                                "alerta": nivel_alerta, "status": status_inicial
                            })
                            st.success(f"Obrigação '{nome_obrigacao}' lançada com sucesso!")

        elif menu == "Enviar Arquivos avulsos":
            st.title("📤 Upload Manual de Arquivos Extras")
            with st.form("form_upload_manual"):
                c_destino = st.selectbox("Cliente Destinatário:", [c["nome"] for c in st.session_state.clientes])
                ano_doc = st.selectbox("Ano Competência:", LISTA_ANOS, index=2)
                mes_doc = st.selectbox("Mês Competência:", LISTA_MESES, index=5)
                arquivo_carregado = st.file_uploader("Documento", type=["pdf", "xml", "xlsx", "zip"])
                if st.form_submit_button("Enviar Documento Solto"):
                    if arquivo_carregado:
                        id_dest = next(c["id"] for c in st.session_state.clientes if c["nome"] == c_destino)
                        agora_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        st.session_state.arquivos_escritorio.append({
                            "cliente_id": id_dest, "ano": ano_doc, "mes": mes_doc,
                            "nome_arquivo": arquivo_carregado.name, "conteudo": arquivo_carregado.read(),
                            "data_publicacao": agora_str
                        })
                        st.success("Publicado!")

    # --- MENUS DO CLIENTE ---
    elif st.session_state.perfil == "cliente":
        info_c = next(c for c in st.session_state.clientes if c["id"] == st.session_state.cliente_id_logado)
        st.title(f"👤 Portal do Cliente - {info_c['nome']}")
        
        menu_cliente = st.sidebar.radio("Seções Disponíveis:", ["📂 Documentos Permanentes", "📥 Guias e Impostos Mensais", "📤 Enviar Arquivos Mensais"])
        
        if menu_cliente == "📥 Guias e Impostos Mensais":
            st.subheader("📁 Central de Documentos e Guias Mensais Liberadas")
            col_f1, col_f2 = st.columns(2)
            with col_f1: filtro_ano_c = st.selectbox("Ano:", LISTA_ANOS, index=2)
            with col_f2: filtro_mes_c = st.selectbox("Mês:", LISTA_MESES, index=5)
            
            arquivos_filtrados = [arq for arq in st.session_state.arquivos_escritorio if arq["cliente_id"] == info_c["id"] and arq["ano"] == filtro_ano_c and arq["mes"] == filtro_mes_c]
            if arquivos_filtrados:
                for arq in arquivos_filtrados:
                    col_arq, col_btn = st.columns([3, 1])
                    with col_arq: 
                        st.markdown(f"📄 **{arq['nome_arquivo']}**")
                        st.caption(f"Disponibilizado em: {arq['data_publicacao']}")
                    with col_btn: 
                        st.download_button(label="⬇️ Baixar Guia", data=arq["conteudo"], file_name=arq["nome_arquivo"], key=f"dl_{arq['nome_arquivo']}")
            else:
                st.warning("Nenhum documento ou imposto disponível para o período filtrado.")
                
        elif menu_cliente == "📂 Documentos Permanentes":
            st.info("Documentos fixos da empresa estão disponíveis nesta área.")
            
        elif menu_cliente == "📤 Enviar Arquivos Mensais":
            st.subheader("Fazer entrega de arquivos para a contabilidade")
            with st.form("form_cliente_envio"):
                tipo_doc = st.selectbox("Tipo:", ["Extrato Bancário", "XML Notas", "Outros"])
                arquivo_cliente = st.file_uploader("Arquivo")
                if st.form_submit_button("Protocolar"):
                    if arquivo_cliente:
                        st.session_state.envios_cliente_protocolo.append({
                            "cliente_id": info_c["id"], "tipo_documento": tipo_doc, "competencia": "Mês Corrente", "nome_arquivo": arquivo_cliente.name, "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        })
                        st.success("Protocolado com sucesso!")