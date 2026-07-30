import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import hashlib
import re

# 1. CONEXÃO COM O BANCO DE DADOS
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

def run_query(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        if hasattr(response, 'data'): return pd.DataFrame(response.data)
        return pd.DataFrame(response)
    except: return pd.DataFrame()

def run_insert(table_name, data_dict):
    try:
        supabase.table(table_name).insert(data_dict).execute()
        return True
    except: return False

def run_update(table_name, match_col, match_val, update_dict):
    try:
        supabase.table(table_name).update(update_dict).eq(match_col, match_val).execute()
        return True
    except: return False

def criar_hash(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

# 2. CONTROLE DE ACESSO (LOGIN)
USUARIO_MASTER = "contador"
SENHA_HASH_MASTER = criar_hash("admin123") 

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def tela_login():
    st.markdown("<h3 style='text-align: center;'>🔒 Acesso Restrito - Controle Contábil</h3>", unsafe_allow_html=True)
    with st.form("login_form"):
        user = st.text_input("Usuário", placeholder="Digite seu usuário")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        if st.form_submit_button("Entrar no Sistema"):
            if user == USUARIO_MASTER and criar_hash(password) == SENHA_HASH_MASTER:
                st.session_state['autenticado'] = True
                st.rerun()
            else: st.error("Usuário ou senha incorretos.")

if not st.session_state['autenticado']:
    tela_login(); st.stop()

# 3. INTERFACE E MENUS
st.set_page_config(page_title="Sistema Contábil Próprio", layout="wide")

if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state['autenticado'] = False
    st.rerun()

st.title("📊 Mini Domínio - Sistema Contábil Particular")
menu = ["Lançamento de Notas", "Lançamento Manual", "Folha de Pagamento", "Importação OFX (Banco)", "Demonstrações Contábeis", "Central de Relatórios Fiscais/Gerenciais", "Cadastros Base"]
choice = st.sidebar.selectbox("Navegação do Sistema", menu)

contas_df = run_query("plano_contas")
part_df = run_query("participantes")
acum_df = run_query("acumuladores")
hist_df = run_query("historicos")

if choice == "Cadastros Base":
    st.header("⚙️ Cadastros Estruturais e Plano de Contas")
    tab1, tab2, tab3, tab4 = st.tabs(["Clientes/Fornecedores", "Históricos Padrão", "Acumuladores", "Plano de Contas"])
    with tab1:
        st.subheader("Gerenciar Participantes")
        with st.form("form_p"):
            nome = st.text_input("Razão Social / Nome")
            doc = st.text_input("CPF / CNPJ")
            tipo = st.selectbox("Tipo", ["Fornecedor", "Cliente"])
            lista_c = ["Padrão do Acumulador"]
            if not contas_df.empty: lista_c += [f"{r['codigo_reduzido']} - {r['nome']}" for _, r in contas_df.iterrows()]
            conta_p = st.selectbox("Conta Contábil Específica", lista_c)
            if st.form_submit_button("Salvar Novo Participante"):
                c_red = conta_p.split(" - ") if conta_p != "Padrão do Acumulador" else None
                if run_insert("participantes", {"nome": nome, "documento": doc, "tipo": tipo, "conta_contabil": c_red}):
                    st.success("Cadastrado!"); st.rerun()
        if not part_df.empty: st.dataframe(part_df, use_container_width=True)
    with tab2:
        st.subheader("Gerenciar Históricos Padrão")
        with st.form("form_h"):
            cod_h = st.text_input("Código Histórico")
            desc_h = st.text_input("Texto do Histórico")
            if st.form_submit_button("Salvar Novo Histórico"):
                if run_insert("historicos", {"codigo": cod_h, "descricao": desc_h}):
                    st.success("Salvo!"); st.rerun()
        if not hist_df.empty: st.dataframe(hist_df, use_container_width=True)
    with tab3:
        st.subheader("Gerenciar Acumuladores")
        with st.form("form_a"):
            cod_a = st.text_input("Código do Acumulador")
            desc_a = st.text_input("Descrição da Operação")
            op_a = st.selectbox("Tipo de Movimento", ["Entrada", "Saída", "Serviço Prestado"])
            cfop_a = st.text_input("CFOP Associado (Ex: 5102, 1102)")
            c_dinamico = ["FORNECEDOR", "CLIENTE"]
            if not contas_df.empty: c_dinamico += [f"{r['codigo_reduzido']} - {r['nome']}" for _, r in contas_df.iterrows()]
            c_deb = st.selectbox("Conta Débito", c_dinamico)
            c_cred = st.selectbox("Conta Crédito", c_dinamico)
            l_hist = [f"{r['codigo']} - {r['descricao']}" for _, r in hist_df.iterrows()] if not hist_df.empty else []
            h_pad = st.selectbox("Histórico Padrão Base", l_hist) if l_hist else st.text_input("Histórico Manual")
            aliq = st.number_input("Alíquota (%)", min_value=0.0, max_value=100.0, step=0.1)
            if st.form_submit_button("Salvar Novo Acumulador"):
                d_c = c_deb.split(" - "); c_c = c_cred.split(" - "); h_c = h_pad.split(" - ")
                if run_insert("acumuladores", {"codigo": cod_a, "descricao": desc_a, "operacao": op_a, "conta_debito": d_c, "conta_credito": c_c, "historico_padrao": h_c, "aliquota_imposto": aliq/100, "cfop": cfop_a}):
                    st.success("Acumulador Cadastrado!"); st.rerun()
        if not acum_df.empty: st.dataframe(acum_df, use_container_width=True)
    with tab4:
        st.subheader("Gestão do Plano de Contas")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**Adicionar Nova Conta**")
            with st.form("new_acc"):
                n_red = st.text_input("Código Reduzido")
                n_est = st.text_input("Classificação / Máscara (Ex: 1.1.1.01.0001)")
                n_nome = st.text_input("Nome da Conta")
                n_grp = st.selectbox("Grupo Contábil", ["Ativo", "Passivo", "PL", "Receita", "Despesa"])
                if st.form_submit_button("Adicionar Conta"):
                    if run_insert("plano_contas", {"codigo_reduzido": n_red, "codigo_estruturado": n_est, "nome": n_nome, "grupo": n_grp}):
                        st.success("Conta adicionada!"); st.rerun()
        with col_c2:
            st.markdown("**Editar Conta Existente**")
            if not contas_df.empty:
                dict_edit = {f"{r['codigo_reduzido']} - {r['nome']}": r for _, r in contas_df.iterrows()}
                c_edit = st.selectbox("Selecione a Conta", list(dict_edit.keys()))
                d_orig = dict_edit[c_edit]
                with st.form("edit_acc"):
                    e_nome = st.text_input("Novo Nome", value=d_orig['nome'])
                    e_est = st.text_input("Novo Estruturado", value=d_orig['codigo_estruturado'])
                    e_grp = st.selectbox("Novo Grupo", ["Ativo", "Passivo", "PL", "Receita", "Despesa"], index=["Ativo", "Passivo", "PL", "Receita", "Despesa"].index(d_orig['grupo']))
                    if st.form_submit_button("Salvar Alterações"):
                        if run_update("plano_contas", "codigo_reduzido", d_orig['codigo_reduzido'], {"nome": e_nome, "codigo_estruturado": e_est, "grupo": e_grp}):
                            st.success("Conta atualizada!"); st.rerun()
        if not contas_df.empty: st.dataframe(contas_df.sort_values(by="codigo_estruturado"), use_container_width=True)
elif choice == "Lançamento de Notas":
    st.header("🧾 Escrituração Fiscal Dinâmica (Padrão Domínio)")
    with st.form("form_nota"):
        col1, col2 = st.columns(2)
        with col1:
            data_nf = st.date_input("Data da Nota", datetime.now())
            num_nf = st.text_input("Número do Documento / NF")
            lista_p = ["Padrão Sem Cadastro"]
            if not part_df.empty:
                dict_part = {row['id']: (row['nome'], row['conta_contabil']) for _, row in part_df.iterrows()}
                lista_p = [f"{i} - {n}" for i, n in dict_part.items()]
            participante_sel = st.selectbox("Cliente / Fornecedor", lista_p)
        with col2:
            lista_a = ["Padrão Sem Cadastro"]
            if not acum_df.empty:
                dict_acum = {row['codigo']: row for _, row in acum_df.iterrows()}
                lista_a = [f"{c} - {row['descricao']}" for c, row in dict_acum.items()]
            acum_sel = st.selectbox("Acumulador Contábil", lista_a)
            valor_nf = st.number_input("Valor Bruto da Nota (R$)", min_value=0.0, step=10.0)
            regime = st.selectbox("Regime Tributário:", ["Simples Nacional", "Lucro Presumido"])
        
        if st.form_submit_button("Processar e Gerar Lançamento Contábil"):
            if part_df.empty or acum_df.empty:
                st.error("Erro: Cadastre um Participante e um Acumulador no menu 'Cadastros Base' antes de processar notas.")
            else:
                id_p = int(participante_sel.split(" - "))
                nome_p, conta_especifica_p = dict_part[id_p]
                cod_ac = acum_sel.split(" - ")
                config_ac = dict_acum[cod_ac]
                c_debito, c_credito = config_ac['conta_debito'], config_ac['conta_credito']
                cfop_associado = config_ac.get('cfop', '')
                if c_debito in ["FORNECEDOR", "CLIENTE"]:
                    c_debito = conta_especifica_p if conta_especifica_p else ('4' if c_debito == "FORNECEDOR" else '3')
                if c_credito in ["FORNECEDOR", "CLIENTE"]:
                    c_credito = conta_especifica_p if conta_especifica_p else ('4' if c_credito == "FORNECEDOR" else '3')
                historico_final = f"Aquisição ref NF {num_nf}, Part: {nome_p}"
                run_insert("diario", {"data": str(data_nf), "conta_debito": str(c_debito), "conta_credito": str(c_credito), "valor": valor_nf, "historico": historico_final, "origem": "Fiscal", "acumulador": str(cod_ac), "cfop": str(cfop_associado), "participante": str(nome_p)})
                imposto_calculado = valor_nf * float(config_ac['aliquota_imposto'])
                if imposto_calculado > 0:
                    run_insert("diario", {"data": str(data_nf), "conta_debito": "11", "conta_credito": "6", "valor": imposto_calculado, "historico": f"Provisão Imposto ref NF {num_nf}", "origem": "Imposto Nota", "acumulador": str(cod_ac), "cfop": str(cfop_associado), "participante": str(nome_p)})
                st.success("Lançamento automático enviado ao diário!")

elif choice == "Lançamento Manual":
    st.header("✍️ Lançamento Contábil Manual (Partida Dobrada)")
    with st.form("manual_entry_form"):
        m_data = st.date_input("Data do Lançamento", datetime.now())
        lista_contas_m = ["Nenhuma conta cadastrada"]
        if not contas_df.empty:
            lista_contas_m = [f"{row['codigo_reduzido']} - {row['nome']}" for _, row in contas_df.iterrows()]
        m_deb = st.selectbox("Conta Débito", lista_contas_m)
        m_cred = st.selectbox("Conta Crédito", lista_contas_m)
        m_val = st.number_input("Valor (R$)", min_value=0.01, step=10.0)
        m_hist = st.text_input("Histórico Contábil")
        if st.form_submit_button("Gravar Lançamento Manual"):
            if contas_df.empty: st.error("Erro: Cadastre as contas contábeis primeiro.")
            else:
                c_d_red = m_deb.split(" - "); c_c_red = m_cred.split(" - ")
                if run_insert("diario", {"data": str(m_data), "conta_debito": c_d_red, "conta_credito": c_c_red, "valor": m_val, "historico": m_hist, "origem": "Manual"}):
                    st.success("Gravado com sucesso no Diário!")

elif choice == "Folha de Pagamento":
    st.header("👥 Módulo de Folha Simplificado")
    with st.form("form_folha"):
        data_folha = st.date_input("Competência da Folha", datetime.now())
        salario_bruto = st.number_input("Valor Total dos Salários Brutos (R$)", min_value=0.0, step=100.0)
        inss_retido = st.number_input("Valor Total do INSS Retido (R$)", min_value=0.0, step=10.0)
        if st.form_submit_button("Fechar Folha e Integrar"):
            data_str = str(data_folha)
            run_insert("diario", {"data": data_str, "conta_debito": "10", "conta_credito": "5", "valor": salario_bruto, "historico": f"Faturamento folha competência {data_str[:7]}", "origem": "Folha"})
            if inss_retido > 0:
                run_insert("diario", {"data": data_str, "conta_debito": "5", "conta_credito": "6", "valor": inss_retido, "historico": f"Retenção INSS competência {data_str[:7]}", "origem": "Folha"})
            st.success("Folha integrada com sucesso!")

elif choice == "Importação OFX (Banco)":
    st.header("🏦 Importador Real de Extratos Bancários (.OFX)")
    regras = {"TARIFA": ("9", "2", "Despesa Bancaria"), "TELEFONICA": ("9", "2", "Despesa com Telefone"), "MATERIAIS": ("9", "2", "Uso e Consumo")}
    st.markdown("**Regras de conciliação:**")
    st.json(regras)
    uploaded_file = st.file_uploader("Arraste e solte o seu arquivo .ofx aqui", type=["ofx"])
    if uploaded_file is not None:
        raw_ofx = uploaded_file.read().decode("utf-8", errors="ignore")
        transacoes = re.findall(r"<STMTTRN>([\s\S]*?)</STMTTRN>", raw_ofx)
        if not transacoes: st.error("Nenhuma transação localizada.")
        else:
            dados_ofx = []
            for tx in transacoes:
                valor = re.search(r"<TRNAMT>(.*?)\s", tx)
                memo = re.search(r"<MEMO>(.*?)\s", tx)
                val_num = float(valor.group(1)) if valor else 0.0
                memo_txt = memo.group(1) if memo else "BANCO"
                dados_ofx.append({"Data": str(datetime.now().date()), "Histórico OFX": memo_txt, "Valor": abs(val_num), "Tipo": "Crédito" if val_num > 0 else "Débito"})
            df_ofx = pd.DataFrame(dados_ofx)
            st.dataframe(df_ofx, use_container_width=True)
            if st.button("Processar Lançamentos do OFX"):
                sucessos = 0
                for _, linha in df_ofx.iterrows():
                    hist_banco = linha['Histórico OFX'].upper()
                    for termo, (c_deb, c_cred, nome_regra) in regras.items():
                        if termo in hist_banco:
                            deb_f = c_deb if linha['Tipo'] == "Débito" else "2"
                            cred_f = c_cred if linha['Tipo'] == "Débito" else c_deb
                            run_insert("diario", {"data": linha['Data'], "conta_debito": deb_f, "conta_credito": cred_f, "valor": linha['Valor'], "historico": f"OFX: {linha['Histórico OFX']}", "origem": "OFX"})
                            sucessos += 1; break
                st.success(f"Conciliação concluída! {sucessos} lançamentos gerados.")
elif choice == "Demonstrações Contábeis":
    st.header("📋 Demonstrativos Reais (Com Saldo Anterior e Filtro de Datas)")
    diario_completo = run_query("diario")
    
    col_dt1, col_dt2 = st.columns(2)
    with col_dt1: dt_inicio = st.date_input("Data de Início do Período", date(2025, 1, 1))
    with col_dt2: dt_fim = st.date_input("Data de Fim do Período", date(2025, 12, 31))
    
    if diario_completo.empty or contas_df.empty:
        st.warning("Cadastre as contas e faça lançamentos para visualizar os relatórios.")
    else:
        contas_df['codigo_estruturado'] = contas_df['codigo_estruturado'].str.strip()
        contas_sorted = contas_df.sort_values(by="codigo_estruturado").copy()
        
        # Filtros temporais baseados no Diário
        diario_completo['data_dt'] = pd.to_datetime(diario_completo['data']).dt.date
        df_anterior = diario_completo[diario_completo['data_dt'] < dt_inicio]
        df_periodo = diario_completo[(diario_completo['data_dt'] >= dt_inicio) & (diario_completo['data_dt'] <= dt_fim)]
        
        # 1. PROCESSAMENTO DE SALDO ANTERIOR DINÂMICO
        ant_deb = {str(row['codigo_reduzido']): 0.0 for _, row in contas_sorted.iterrows()}
        ant_cred = {str(row['codigo_reduzido']): 0.0 for _, row in contas_sorted.iterrows()}
        for _, lanc in df_anterior.iterrows():
            d, c, v = str(lanc['conta_debito']), str(lanc['conta_credito']), float(lanc['valor'])
            if d in ant_deb: ant_deb[d] += v
            if c in ant_cred: ant_cred[c] += v
            
        # 2. PROCESSAMENTO DO PERÍODO SELECIONADO
        per_deb = {str(row['codigo_reduzido']): 0.0 for _, row in contas_sorted.iterrows()}
        per_cred = {str(row['codigo_reduzido']): 0.0 for _, row in contas_sorted.iterrows()}
        for _, lanc in df_periodo.iterrows():
            d, c, v = str(lanc['conta_debito']), str(lanc['conta_credito']), float(lanc['valor'])
            if d in per_deb: per_deb[d] += v
            if c in per_cred: per_cred[c] += v

        linhas_balancete = []
        for _, row in contas_sorted.iterrows():
            mascara = row['codigo_estruturado']
            nome = row['nome']
            grupo_base = row['grupo']
            
            # Cálculo cascata de Níveis (Sintéticas acumulando as Analíticas)
            sa_deb = 0.0; sa_cred = 0.0; sp_deb = 0.0; sp_cred = 0.0
            for _, r_sub in contas_sorted.iterrows():
                if r_sub['codigo_estruturado'].startswith(mascara):
                    idx = str(r_sub['codigo_reduzido'])
                    sa_deb += ant_deb[idx]; sa_cred += ant_cred[idx]
                    sp_deb += per_deb[idx]; sp_cred += per_cred[idx]
            
            # Lógica Contábil de Natureza de Saldos (Igual ao modelo Hardman)
            if grupo_base in ['Ativo', 'Despesa']:
                s_anterior = sa_deb - sa_cred
                s_atual = (sa_deb + sp_deb) - (sa_cred + sp_cred)
                nat_ant = "D" if s_anterior >= 0 else "C"
                nat_at = "D" if s_atual >= 0 else "C"
            else:
                s_anterior = sa_cred - sa_deb
                s_atual = (sa_cred + sp_cred) - (sa_deb + sp_deb)
                nat_ant = "C" if s_anterior >= 0 else "D"
                nat_at = "C" if s_atual >= 0 else "D"
                
            linhas_balancete.append({
                "Classificação / Máscara": mascara, "Descrição da Conta": nome,
                "Saldo Anterior": f"R$ {abs(s_anterior):,.2f} {nat_ant}",
                "Débito": sp_deb, "Crédito": sp_cred,
                "Saldo Atual": f"R$ {abs(s_atual):,.2f} {nat_at}",
                "_saldo_puro": s_atual, "_grupo": grupo_base
            })
            
        df_balancete_visual = pd.DataFrame(linhas_balancete)
        tab_balancete, tab_dre, tab_balanco = st.tabs(["Balancete por Níveis", "DRE Oficial", "Balanço Patrimonial"])
        
        with tab_balancete:
            st.dataframe(df_balancete_visual[["Classificação / Máscara", "Descrição da Conta", "Saldo Anterior", "Débito", "Crédito", "Saldo Atual"]], use_container_width=True)
        with tab_dre:
            rec_total = sum(l['_saldo_puro'] for l in linhas_balancete if l['_grupo'] == 'Receita' and '.' not in l['Classificação / Máscara'])
            des_total = sum(l['_saldo_puro'] for l in linhas_balancete if l['_grupo'] == 'Despesa' and '.' not in l['Classificação / Máscara'])
            lucro_liquido = rec_total - des_total
            st.markdown(f"**(+) RECEITA OPERACIONAL BRUTA:** R$ {max(0, rec_total):,.2f}")
            st.markdown(f"**(-) DEDUÇÕES E IMPOSTOS INCIDENTES:** R$ {abs(min(0, rec_total)):,.2f}")
            st.markdown(f"**(=) RECEITA LÍQUIDA DO PERÍODO:** R$ {rec_total:,.2f}")
            st.markdown(f"**(-) DESPESAS ADMINISTRATIVAS / OPERACIONAIS:** R$ {des_total:,.2f}")
            st.markdown("---")
            st.subheader(f"(=) RESULTADO LÍQUIDO NO PERÍODO: R$ {lucro_liquido:,.2f}")
        with tab_balanco:
            df_at = df_balancete_visual[df_balancete_visual['_grupo'] == 'Ativo'][["Classificação / Máscara", "Descrição da Conta", "Saldo Atual"]]
            df_pa_pl = df_balancete_visual[df_balancete_visual['_grupo'].isin(['Passivo', 'PL'])][["Classificação / Máscara", "Descrição da Conta", "Saldo Atual"]]
            c1, c2 = st.columns(2)
            with c1: st.info("**GRUPO 1 - ATIVO**"); st.write(df_at)
            with c2: st.info("**GRUPO 2 - PASSIVO E PL**"); st.write(df_pa_pl); st.markdown(f"*(+) Lucro Líquido Incorporado: R$ {lucro_liquido:,.2f}*")

elif choice == "Central de Relatórios Fiscais/Gerenciais":
    st.header("🔍 Central Multicritério de Relatórios")
    diario_livro = run_query("diario")
    
    if diario_livro.empty: st.warning("Sem movimentações registradas.")
    else:
        diario_livro['data_dt'] = pd.to_datetime(diario_livro['data']).dt.date
        col_f1, col_dt_i, col_dt_f = st.columns(3)
        with col_dt_i: r_inicio = st.date_input("Início do Filtro", date(2025, 1, 1))
        with col_dt_f: r_fim = st.date_input("Fim do Filtro", date(2025, 12, 31))
        
        df_filtrado = diario_livro[(diario_livro['data_dt'] >= r_inicio) & (diario_livro['data_dt'] <= r_fim)]
        
        col_f2, col_f3, col_f4 = st.columns(3)
        with col_f2:
            lista_ac_f = ["Todos"] + (list(df_filtrado['acumulador'].dropna().unique()) if 'acumulador' in df_filtrado.columns else [])
            sel_acum = st.selectbox("Filtrar por Acumulador", lista_ac_f)
        with col_f3:
            lista_cf_f = ["Todos"] + (list(df_filtrado['cfop'].dropna().unique()) if 'cfop' in df_filtrado.columns else [])
            sel_cfop = st.selectbox("Filtrar por CFOP", lista_cf_f)
        with col_f4:
            lista_part_f = ["Todos"] + (list(df_filtrado['participante'].dropna().unique()) if 'participante' in df_filtrado.columns else [])
            sel_part = st.selectbox("Filtrar por Cliente / Fornecedor", lista_part_f)
            
        if sel_acum != "Todos": df_filtrado = df_filtrado[df_filtrado['acumulador'] == sel_acum]
        if sel_cfop != "Todos": df_filtrado = df_filtrado[df_filtrado['cfop'] == sel_cfop]
        if sel_part != "Todos": df_filtrado = df_filtrado[df_filtrado['participante'] == sel_part]
        
        t1, t2, tab_f = st.tabs(["Livro Diário / Lançamentos do Período", "Relatório de Livros Fiscais", "Resumo da Folha por Competência"])
        with t1:
            st.subheader("Lançamentos Contábeis Detalhados")
            st.dataframe(df_filtrado[["data", "conta_debito", "conta_credito", "valor", "historico", "origem"]], use_container_width=True)
        with t2:
            st.subheader("Relatório Unificado de Entradas, Vendas e Serviços")
            st.dataframe(df_filtrado[df_filtrado['origem'].isin(['Fiscal', 'Imposto Nota'])], use_container_width=True)
        with tab_f:
            st.subheader("Histórico de Custos com Departamento Pessoal")
            st.dataframe(df_filtrado[df_filtrado['origem'] == 'Folha'], use_container_width=True)
