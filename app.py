import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
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
    tela_login()
    st.stop()

# 3. INTERFACE E MENUS
st.set_page_config(page_title="Sistema Contábil Próprio", layout="wide")

if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state['autenticado'] = False
    st.rerun()

st.title("📊 Mini Domínio - Sistema Contábil Particular")
menu = ["Lançamento de Notas", "Lançamento Manual", "Folha de Pagamento", "Importação OFX (Banco)", "Demonstrações Contábeis", "Cadastros Base"]
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
                c_red = conta_p.split(" - ")[0] if conta_p != "Padrão do Acumulador" else None
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
            c_dinamico = ["FORNECEDOR", "CLIENTE"]
            if not contas_df.empty: c_dinamico += [f"{r['codigo_reduzido']} - {r['nome']}" for _, r in contas_df.iterrows()]
            c_deb = st.selectbox("Conta Débito", c_dinamico)
            c_cred = st.selectbox("Conta Crédito", c_dinamico)
            l_hist = [f"{r['codigo']} - {r['descricao']}" for _, r in hist_df.iterrows()] if not hist_df.empty else []
            h_pad = st.selectbox("Histórico Padrão Base", l_hist) if l_hist else st.text_input("Histórico Manual (Ex: 100)")
            aliq = st.number_input("Alíquota (%)", min_value=0.0, max_value=100.0, step=0.1)
            if st.form_submit_button("Salvar Novo Acumulador"):
                d_c = c_deb.split(" - ")[0]; c_c = c_cred.split(" - ")[0]; h_c = h_pad.split(" - ")[0]
                if run_insert("acumuladores", {"codigo": cod_a, "descricao": desc_a, "operacao": op_a, "conta_debito": d_c, "conta_credito": c_c, "historico_padrao": h_c, "aliquota_imposto": aliq/100}):
                    st.success("Acumulador Cadastrado!"); st.rerun()
        if not acum_df.empty: st.dataframe(acum_df, use_container_width=True)
    with tab4:
        st.subheader("Gestão do Plano de Contas")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**Adicionar Nova Conta**")
            with st.form("new_acc"):
                n_red = st.text_input("Código Reduzido")
                n_est = st.text_input("Código Estruturado")
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
                id_p = int(participante_sel.split(" - ")[0])
                nome_p, conta_especifica_p = dict_part[id_p]
                cod_ac = acum_sel.split(" - ")[0]
                config_ac = dict_acum[cod_ac]
                c_debito, c_credito = config_ac['conta_debito'], config_ac['conta_credito']
                if c_debito in ["FORNECEDOR", "CLIENTE"]:
                    c_debito = conta_especifica_p if conta_especifica_p else ('4' if c_debito == "FORNECEDOR" else '3')
                if c_credito in ["FORNECEDOR", "CLIENTE"]:
                    c_credito = conta_especifica_p if conta_especifica_p else ('4' if c_credito == "FORNECEDOR" else '3')
                historico_final = f"Aquisição ref NF {num_nf}, Part: {nome_p}"
                run_insert("diario", {"data": str(data_nf), "conta_debito": str(c_debito), "conta_credito": str(c_credito), "valor": valor_nf, "historico": historico_final, "origem": "Fiscal"})
                imposto_calculado = valor_nf * float(config_ac['aliquota_imposto'])
                if imposto_calculado > 0:
                    run_insert("diario", {"data": str(data_nf), "conta_debito": "11", "conta_credito": "6", "valor": imposto_calculado, "historico": f"Provisão Imposto ref NF {num_nf}", "origem": "Imposto Nota"})
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
            if contas_df.empty:
                st.error("Erro: Cadastre as contas contábeis na aba 'Plano de Contas' antes de lançar.")
            else:
                c_d_red = m_deb.split(" - ")[0]
                c_c_red = m_cred.split(" - ")[0]
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
    st.markdown("Regras de conciliação:")
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
                            sucessos += 1
                            break
                st.success(f"Conciliação concluída! {sucessos} lançamentos gerados.")

elif choice == "Demonstrações Contábeis":
    st.header("📋 Demonstrativos Oficiais (Tempo Real)")
    diario_completo = run_query("diario")
    if diario_completo.empty:
        st.warning("Nenhum lançamento contábil registrado no Livro Diário ainda.")
    else:
        saldos = {row['codigo_reduzido']: {'nome': row['nome'], 'grupo': row['grupo'], 'saldo': 0.0} for _, row in contas_df.iterrows()} if not contas_df.empty else {}
        for _, lanc in diario_completo.iterrows():
            d, c, v = str(lanc['conta_debito']), str(lanc['conta_credito']), float(lanc['valor'])
            if d in saldos: saldos[d]['saldo'] += v if saldos[d]['grupo'] in ['Ativo', 'Despesa'] else -v
            if c in saldos: saldos[c]['saldo'] += v if saldos[c]['grupo'] in ['Passivo', 'PL', 'Receita'] else -v
        df_saldos = pd.DataFrame.from_dict(saldos, orient='index').reset_index()
        tab_balancete, tab_dre, tab_balanco = st.tabs(["Balancete", "DRE", "Balanço Patrimonial"])
        with tab_balancete: st.dataframe(df_saldos, use_container_width=True)
        with tab_dre:
            rec = df_saldos[df_saldos['grupo'] == 'Receita']['saldo'].sum() if not df_saldos.empty else 0
            des = df_saldos[df_saldos['grupo'] == 'Despesa']['saldo'].sum() if not df_saldos.empty else 0
            st.metric("(+) Receitas", f"R$ {rec:.2f}"); st.metric("(-) Despesas", f"R$ {des:.2f}")
            st.subheader(f"Resultado Líquido: R$ {rec - des:.2f}")
        with tab_balanco:
            at = df_saldos[df_saldos['grupo'] == 'Ativo']['saldo'].sum() if not df_saldos.empty else 0
            pa = df_saldos[df_saldos['grupo'] == 'Passivo']['saldo'].sum() if not df_saldos.empty else 0
            pl = df_saldos[df_saldos['grupo'] == 'PL']['saldo'].sum() + (rec - des) if not df_saldos.empty else 0
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"ATIVO: R$ {at:.2f}")
                st.write(df_saldos[df_saldos['grupo'] == 'Ativo'] if not df_saldos.empty else "")
            with c2:
                st.info(f"PASSIVO + PL: R$ {pa + pl:.2f}")
                st.write(df_saldos[df_saldos['grupo'].isin(['Passivo', 'PL'])] if not df_saldos.empty else "")
