import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import hashlib
import re

# =========================================================================
# CONFIGURAÇÃO E IDENTIDADE VISUAL - FLUXO ASSESSORIA FINANCEIRA
# =========================================================================
st.set_page_config(page_title="Fluxo Assessoria Financeira", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://googleapis.com');
        html, body, [data-testid="stAppViewContainer"], .stWidgetLabel, p, div {
            font-family: 'Roboto', -apple-system, "Segoe UI", sans-serif !important;
            background-color: #FAFAFA !important;
            color: #1E293B !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #031F11 !important;
            border-right: 1px solid #0C2E19 !important;
        }
        section[data-testid="stSidebar"] * {
            color: #F1F5F9 !important;
            font-family: 'Roboto', sans-serif !important;
        }
        h1, h2, h3, [data-testid="stHeader"] {
            font-family: 'Roboto', sans-serif !important;
            font-weight: 700 !important;
            color: #031F11 !important;
        }
        div.stButton > button {
            background: #031F11 !important;
            color: #FFFFFF !important;
            font-weight: 500 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            border-radius: 6px !important;
            border: 1px solid #031F11 !important;
            width: 100% !important;
        }
        div.stButton > button:hover {
            background: #10B981 !important;
            border-color: #10B981 !important;
        }
        div[data-testid="stDataFrame"] td {
            font-variant-numeric: tabular-nums !important;
        }
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_4OAD9stwBHF-L-eMaZkrFg_wRGMplWa"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

def run_query(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data) if hasattr(response, 'data') else pd.DataFrame(response)
    except: return pd.DataFrame()

def run_insert(table_name, data_dict):
    try: return bool(supabase.table(table_name).insert(data_dict).execute())
    except: return False

def run_update(table_name, match_col, match_val, update_dict):
    try: return bool(supabase.table(table_name).update(update_dict).eq(match_col, match_val).execute())
    except: return False

def criar_hash(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def formatar_data_br(data_str):
    try: return datetime.strptime(data_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except: return data_str

if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("""
        <div style='text-align: center; margin-bottom: 15px; margin-top: 40px;'>
            <div style='font-size: 42px; font-weight: 800; color: #031F11; letter-spacing: -2px; margin-bottom: 5px;'>&gt;&gt;&lt;</div>
            <h2 style='color: #031F11; margin: 0; font-size: 32px; font-weight:700; letter-spacing:-0.5px;'>FLUXO</h2>
            <p style='color: #10B981; font-size: 13px; text-transform: uppercase; letter-spacing: 2px; margin-top: 4px; font-weight: 700;'>Assessoria Financeira</p>
        </div>
    """, unsafe_allow_html=True)
    u = st.text_input("Usuário", placeholder="ID de acesso")
    p = st.text_input("Senha", type="password", placeholder="••••••••")
    if st.button("Autenticar no Sistema"):
        if u == "contador" and criar_hash(p) == criar_hash("admin123"):
            st.session_state['auth'] = True
            st.rerun()
        else: st.error("Credenciais inválidas.")
    st.stop()

st.sidebar.markdown("""
    <div style='text-align: center; padding: 20px 0; border-bottom: 1px solid #0C2E19; margin-bottom: 25px;'>
        <div style='font-size: 36px; font-weight: 800; color: #10B981; letter-spacing: -2px; line-height: 1; margin-bottom: 8px;'>&gt;&gt;&lt;</div>
        <h3 style='color: #FFFFFF; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;'>FLUXO</h3>
        <span style='color: #10B981; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px;'>Assessoria Financeira</span>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Encerrar Sessão Segura"):
    st.session_state['auth'] = False
    st.rerun()

menu = ["Lançamento de Notas", "Lançamento Manual", "Folha de Pagamento", "Importação OFX (Banco)", "Demonstrações Contábeis", "Central de Relatórios Fiscais/Gerenciais", "Cadastros Base"]
choice = st.sidebar.selectbox("Navegação do Sistema", menu)

contas_df = run_query("plano_contas")
part_df = run_query("participantes")
acum_df = run_query("acumuladores")
hist_df = run_query("historicos")

if choice == "Cadastros Base":
    st.header("⚙️ Central de Cadastros e Plano de Contas")
    tab1, tab2, tab3, tab4 = st.tabs(["Clientes/Fornecedores", "Históricos Padrão", "Acumuladores", "Plano de Contas"])
    with tab1:
        with st.form("f_p"):
            n = st.text_input("Razão Social / Nome")
            d = st.text_input("CNPJ / CPF")
            tipo = st.selectbox("Tipo de Cadastro", ["Fornecedor", "Cliente"])
            lista_c = ["Padrão do Acumulador"]
            if not contas_df.empty: lista_c += [f"{r['codigo_reduzido']} - {r['nome']}" for _, r in contas_df.iterrows()]
            conta_p = st.selectbox("Conta Contábil Específica (Opcional)", lista_c)
            if st.form_submit_button("Salvar Participante"):
                c_red = conta_p.split(" - ") if conta_p != "Padrão do Acumulador" else None
                run_insert("participantes", {"nome": n, "documento": d, "tipo": tipo, "conta_contabil": c_red})
                st.success("Participante salvo!"); st.rerun()
        if not part_df.empty: st.dataframe(part_df, use_container_width=True)
    with tab2:
        with st.form("f_h"):
            cod_h = st.text_input("Código Histórico")
            desc_h = st.text_input("Texto Descritivo")
            if st.form_submit_button("Salvar Histórico"):
                run_insert("historicos", {"codigo": cod_h, "descricao": desc_h})
                st.success("Histórico salvo!"); st.rerun()
        if not hist_df.empty: st.dataframe(hist_df, use_container_width=True)
    with tab3:
        with st.form("f_a"):
            cod_a = st.text_input("Código Acumulador")
            desc_a = st.text_input("Descrição do Acumulador")
            op_a = st.selectbox("Operação", ["Entrada", "Saída", "Serviço Prestado"])
            cfop_a = st.text_input("CFOP Associado")
            c_dinamico = ["FORNECEDOR", "CLIENTE"]
            if not contas_df.empty: c_dinamico += [f"{r['codigo_reduzido']} - {r['nome']}" for _, r in contas_df.iterrows()]
            c_deb = st.selectbox("Conta Débito Base", c_dinamico)
            c_cred = st.selectbox("Conta Crédito Base", c_dinamico)
            if st.form_submit_button("Salvar Acumulador"):
                d_cod = c_deb.split(" - "); c_cod = c_cred.split(" - ")
                run_insert("acumuladores", {"codigo": cod_a, "descricao": desc_a, "operacao": op_a, "conta_debito": d_cod, "conta_credito": c_cod, "aliquota_imposto": 0.0, "cfop": cfop_a})
                st.success("Acumulador salvo!"); st.rerun()
        if not acum_df.empty: st.dataframe(acum_df, use_container_width=True)
    with tab4:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**Adicionar Nova Conta**")
            with st.form("new_acc"):
                n_red = st.text_input("Reduzido")
                n_est = st.text_input("Máscara de Classificação (Ex: 1.1.1.01.0001)")
                n_nome = st.text_input("Nome da Conta")
                n_grp = st.selectbox("Grupo", ["Ativo", "Passivo", "PL", "Receita", "Despesa"])
                if st.form_submit_button("Gravar Conta"):
                    run_insert("plano_contas", {"codigo_reduzido": n_red, "codigo_estruturado": n_est, "nome": n_nome, "grupo": n_grp})
                    st.success("Conta criada!"); st.rerun()
        with col_c2:
            st.markdown("**Editar Conta Existente**")
            if not contas_df.empty:
                dict_edit = {f"{r['codigo_reduzido']} - {r['nome']}": r for _, r in contas_df.iterrows()}
                c_edit = st.selectbox("Selecione a Conta para Modificar", list(dict_edit.keys()))
                d_orig = dict_edit[c_edit]
                with st.form("edit_acc"):
                    e_nome = st.text_input("Novo Nome", value=d_orig['nome'])
                    e_est = st.text_input("Nova Máscara", value=d_orig['codigo_estruturado'])
                    e_grp = st.selectbox("Novo Grupo", ["Ativo", "Passivo", "PL", "Receita", "Despesa"], index=["Ativo", "Passivo", "PL", "Receita", "Despesa"].index(d_orig['grupo']))
                    if st.form_submit_button("Salvar Alterações"):
                        run_update("plano_contas", "codigo_reduzido", d_orig['codigo_reduzido'], {"nome": e_nome, "codigo_estruturado": e_est, "grupo": e_grp})
                        st.success("Conta atualizada!"); st.rerun()
        if not contas_df.empty: st.dataframe(contas_df.sort_values(by="codigo_estruturado"), use_container_width=True)
elif choice == "Lançamento de Notas":
    st.subheader("🧾 Escrituração Fiscal Dinâmica (Vendas / Entradas)")
    with st.form("form_nota"):
        col1, col2 = st.columns(2)
        with col1:
            data_nf = st.date_input("Data da Nota", datetime.now(), format="DD/MM/YYYY")
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
        if st.form_submit_button("Processar Lançamento Fiscal"):
            if part_df.empty or acum_df.empty: st.error("Cadastre participante e acumulador primeiro.")
            else:
                id_p = int(participante_sel.split(" - "))
                nome_p, conta_especifica_p = dict_part[id_p]
                cod_ac = acum_sel.split(" - ")
                config_ac = dict_acum[cod_ac]
                c_deb, c_cred = config_ac['conta_debito'], config_ac['conta_credito']
                cfop_associado = config_ac.get('cfop', '')
                if c_deb in ["FORNECEDOR", "CLIENTE"]: c_deb = conta_especifica_p if conta_especifica_p else ('4' if c_deb == "FORNECEDOR" else '3')
                if c_cred in ["FORNECEDOR", "CLIENTE"]: c_cred = conta_especifica_p if conta_especifica_p else ('4' if c_cred == "FORNECEDOR" else '3')
                run_insert("diario", {"data": str(data_nf), "conta_debito": str(c_deb), "conta_credito": str(c_cred), "valor": valor_nf, "historico": f"Aquisição ref NF {num_nf}, Part: {nome_p}", "origem": "Fiscal", "acumulador": str(cod_ac), "cfop": str(cfop_associado), "participante": str(nome_p)})
                st.success("Nota escriturada no Diário Central!"); st.rerun()

elif choice == "Lançamento Manual":
    st.subheader("✍️ Lançamento Contábil Manual (Partida Dobrada)")
    with st.form("manual_entry_form"):
        m_data = st.date_input("Data do Lançamento", datetime.now(), format="DD/MM/YYYY")
        lista_contas_m = ["Nenhuma conta cadastrada"]
        if not contas_df.empty: lista_contas_m = [f"{row['codigo_reduzido']} - {row['nome']}" for _, row in contas_df.iterrows()]
        m_deb = st.selectbox("Conta Débito (Reduzido)", lista_contas_m)
        m_cred = st.selectbox("Conta Crédito (Reduzido)", lista_contas_m)
        m_val = st.number_input("Valor (R$)", min_value=0.01, step=10.0)
        m_hist = st.text_input("Histórico Contábil")
        if st.form_submit_button("Gravar Lançamento Manual"):
            if contas_df.empty: st.error("Cadastre o plano de contas primeiro.")
            else:
                if run_insert("diario", {"data": str(m_data), "conta_debito": m_deb.split(" - "), "conta_credito": m_cred.split(" - "), "valor": m_val, "historico": m_hist, "origem": "Manual"}):
                    st.success("Lançamento Manual consolidado!"); st.rerun()

elif choice == "Folha de Pagamento":
    st.subheader("👥 Integração Automática de Folha de Pagamento")
    with st.form("form_folha"):
        data_folha = st.date_input("Competência / Mês da Folha", datetime.now(), format="DD/MM/YYYY")
        salario_bruto = st.number_input("Valor de Salários Brutos (R$)", min_value=0.0, step=100.0)
        inss_retido = st.number_input("Valor de INSS Retido (R$)", min_value=0.0, step=10.0)
        if st.form_submit_button("Fechar Emissão e Integrar"):
            data_str = str(data_folha)
            run_insert("diario", {"data": data_str, "conta_debito": "10", "conta_credito": "5", "valor": salario_bruto, "historico": f"Ref. Folha de Pagamento Competência {data_str[:7]}", "origem": "Folha"})
            if inss_retido > 0: run_insert("diario", {"data": data_str, "conta_debito": "5", "conta_credito": "6", "valor": inss_retido, "historico": f"Retenção INSS s/ Folha Competência {data_str[:7]}", "origem": "Folha"})
            st.success("Folha integrada ao Diário!"); st.rerun()
elif choice == "Importação OFX (Banco)":
    st.subheader("🏦 Importador Real de Extratos Bancários (.OFX)")
    regras = {"TARIFA": ("9", "2", "Despesa Bancaria"), "TELEFONICA": ("9", "2", "Despesa com Telefone"), "MATERIAIS": ("9", "2", "Uso e Consumo")}
    st.json(regras)
    uploaded_file = st.file_uploader("Selecione o arquivo .ofx do seu banco", type=["ofx"])
    if uploaded_file is not None:
        raw_ofx = uploaded_file.read().decode("utf-8", errors="ignore")
        transacoes = re.findall(r"<STMTTRN>([\s\S]*?)</STMTTRN>", raw_ofx)
        if not transacoes: st.error("Nenhuma transação contábil padrão localizada.")
        else:
            dados_ofx = []
            for tx in transacoes:
                valor = re.search(r"<TRNAMT>(.*?)\s", tx)
                memo = re.search(r"<MEMO>(.*?)\s", tx)
                val_num = float(valor.group(1)) if valor else 0.0
                dados_ofx.append({"Data": str(datetime.now().date()), "Histórico OFX": memo.group(1) if memo else "BANCO", "Valor": abs(val_num), "Tipo": "Crédito" if val_num > 0 else "Débito"})
            df_ofx = pd.DataFrame(dados_ofx)
            st.dataframe(df_ofx, use_container_width=True)
            if st.button("Processar Lançamentos via Regras De/Para"):
                sucessos = 0
                for _, linha in df_ofx.iterrows():
                    hist_banco = linha['Histórico OFX'].upper()
                    for termo, (c_deb, c_cred, nome_regra) in regras.items():
                        if termo in hist_banco:
                            deb_f = c_deb if linha['Tipo'] == "Débito" else "2"
                            cred_f = c_cred if linha['Tipo'] == "Débito" else c_deb
                            run_insert("diario", {"data": linha['Data'], "conta_debito": deb_f, "conta_credito": cred_f, "valor": linha['Valor'], "historico": f"OFX: {linha['Histórico OFX']}", "origem": "OFX"})
                            sucessos += 1; break
                st.success(f"Conciliação finalizada! {sucessos} linhas integradas."); st.rerun()
elif choice == "Demonstrações Contábeis":
    st.subheader("📋 Demonstrativos Oficiais (Padrão de Níveis com Saldo Anterior)")
    diario_completo = run_query("diario")
    col_dt1, col_dt2 = st.columns(2)
    with col_dt1: dt_inicio = st.date_input("Data de Início do Período", date(2025, 1, 1), format="DD/MM/YYYY")
    with col_dt2: dt_fim = st.date_input("Data de Fim do Período", date(2025, 12, 31), format="DD/MM/YYYY")
    if diario_completo.empty or contas_df.empty: st.warning("Efetue lançamentos e cadastre seu plano primeiro.")
    else:
        contas_sorted = contas_df.sort_values(by="codigo_estruturado").copy()
        diario_completo['data_dt'] = pd.to_datetime(diario_completo['data']).dt.date
        df_anterior = diario_completo[diario_completo['data_dt'] < dt_inicio]
        df_periodo = diario_completo[(diario_completo['data_dt'] >= dt_inicio) & (diario_completo['data_dt'] <= dt_fim)]
        ant_deb = {str(row['codigo_reduzido']): 0.0 for _, row in contas_sorted.iterrows()}
        ant_cred = {str(row['codigo_reduzido']): 0.0 for _, row in contas_sorted.iterrows()}
        for _, lanc in df_anterior.iterrows():
            d, c, v = str(lanc['conta_debito']), str(lanc['conta_credito']), float(lanc['valor'])
            if d in ant_deb: ant_deb[d] += v
            if c in ant_cred: ant_cred[c] += v
        per_deb = {str(row['codigo_reduzido']): 0.0 for _, row in contas_sorted.iterrows()}
        per_cred = {str(row['codigo_reduzido']): 0.0 for _, row in contas_sorted.iterrows()}
        for _, lanc in df_periodo.iterrows():
            d, c, v = str(lanc['conta_debito']), str(lanc['conta_credito']), float(lanc['valor'])
            if d in per_deb: per_deb[d] += v
            if c in per_cred: per_cred[c] += v
        linhas_balancete = []
        for _, row in contas_sorted.iterrows():
            mascara, nome, grupo_base = row['codigo_estruturado'], row['nome'], row['grupo']
            sa_deb = 0.0; sa_cred = 0.0; sp_deb = 0.0; sp_cred = 0.0
            for _, r_sub in contas_sorted.iterrows():
                if r_sub['codigo_estruturado'].startswith(mascara):
                    idx = str(r_sub['codigo_reduzido'])
                    sa_deb += ant_deb[idx]; sa_cred += ant_cred[idx]; sp_deb += per_deb[idx]; sp_cred += per_cred[idx]
            s_anterior = (sa_deb - sa_cred) if grupo_base in ['Ativo', 'Despesa'] else (sa_cred - sa_deb)
            s_atual = ((sa_deb + sp_deb) - (sa_cred + sp_cred)) if grupo_base in ['Ativo', 'Despesa'] else ((sa_cred + sp_cred) - (sa_deb + sp_deb))
            linhas_balancete.append({"Classificação": mascara, "Descrição": nome, "Saldo Anterior": f"R$ {s_anterior:,.2f}", "Débito": sp_deb, "Crédito": sp_cred, "Saldo Atual": f"R$ {s_atual:,.2f}", "_saldo_puro": s_atual, "_grupo": grupo_base})
        df_balancete_visual = pd.DataFrame(linhas_balancete)
        t_bal, t_dre, t_balanco = st.tabs(["Balancete por Níveis", "DRE Dedutiva Oficial", "Balanço Patrimonial Vertical"])
        with t_bal: st.dataframe(df_balancete_visual[["Classificação", "Descrição", "Saldo Anterior", "Débito", "Crédito", "Saldo Atual"]], use_container_width=True)
        with t_dre:
            rec_total = sum(l['_saldo_puro'] for l in linhas_balancete if l['_grupo'] == 'Receita' and '.' not in l['Classificação'])
            des_total = sum(l['_saldo_puro'] for l in linhas_balancete if l['_grupo'] == 'Despesa' and '.' not in l['Classificação'])
            st.markdown(f"**(+) RECEITA OPERACIONAL BRUTA:** R$ {max(0, rec_total):,.2f}")
            st.markdown(f"**(-) DEDUÇÕES E IMPOSTOS INCIDENTES:** R$ {abs(min(0, rec_total)):,.2f}")
            st.markdown(f"**(=) RECEITA LÍQUIDA DO PERÍODO:** R$ {rec_total:,.2f}")
            st.markdown(f"**(-) DESPESAS ADMINISTRATIVAS / OPERACIONAIS:** R$ {des_total:,.2f}")
            st.markdown("---")
            st.subheader(f"(=) RESULTADO LÍQUIDO DO EXERCÍCIO: R$ {rec_total - des_total:,.2f}")
        with t_balanco:
            c1, c2 = st.columns(2)
            with c1: st.info("**GRUPO 1 - ATIVO TOTAL**"); st.write(df_balancete_visual[df_balancete_visual['_grupo'] == 'Ativo'][["Classificação", "Descrição", "Saldo Atual"]])
            with c2: st.info("**GRUPO 2 - PASSIVO E PATRIMÔNIO LÍQUIDO**"); st.write(df_balancete_visual[df_balancete_visual['_grupo'].isin(['Passivo', 'PL'])][["Classificação", "Descrição", "Saldo Atual"]])

elif choice == "Central de Relatórios Fiscais/Gerenciais":
    st.header("🔍 Central Multicritério de Relatórios")
    diario_livro = run_query("diario")
    if diario_livro.empty: st.warning("Sem movimentações registradas.")
    else:
        diario_livro['data_dt'] = pd.to_datetime(diario_livro['data']).dt.date
        col_dt_i, col_dt_f = st.columns(2)
        with col_dt_i: r_inicio = st.date_input("Início do Filtro", date(2025, 1, 1), format="DD/MM/YYYY")
        with col_dt_f: r_fim = st.date_input("Fim do Filtro", date(2025, 12, 31), format="DD/MM/YYYY")
        df_filtrado = diario_livro[(diario_livro['data_dt'] >= r_inicio) & (diario_livro['data_dt'] <= r_fim)]
        col_f2, col_f3, col_f4 = st.columns(3)
        with col_f2: sel_acum = st.selectbox("Acumulador", ["Todos"] + (list(df_filtrado['acumulador'].dropna().unique()) if 'acumulador' in df_filtrado.columns else []))
        with col_f3: sel_cfop = st.selectbox("CFOP", ["Todos"] + (list(df_filtrado['cfop'].dropna().unique()) if 'cfop' in df_filtrado.columns else []))
        with col_f4: sel_part = st.selectbox("Cliente/Fornecedor", ["Todos"] + (list(df_filtrado['participante'].dropna().unique()) if 'participante' in df_filtrado.columns else []))
        if sel_acum != "Todos": df_filtrado = df_filtrado[df_filtrado['acumulador'] == sel_acum]
        if sel_cfop != "Todos": df_filtrado = df_filtrado[df_filtrado['cfop'] == sel_cfop]
        if sel_part != "Todos": df_filtrado = df_filtrado[df_filtrado['participante'] == sel_part]
        df_filtrado['data'] = df_filtrado['data'].apply(formatar_data_br)
        t1, t2, tab_f = st.tabs(["Lançamentos Contábeis do Diário", "Relatório de Livros Fiscais (Vendas e Entradas)", "Resumo da Folha por Mês"])
        with t1: st.dataframe(df_filtrado[["data", "conta_debito", "conta_credito", "valor", "historico", "origem"]], use_container_width=True)
        with t2: st.dataframe(df_filtrado[df_filtrado['origem'].isin(['Fiscal', 'OFX'])], use_container_width=True)
        with tab_f: st.dataframe(df_filtrado[df_filtrado['origem'] == 'Folha'], use_container_width=True)
