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
        if hasattr(response, 'data'):
            return pd.DataFrame(response.data)
        return pd.DataFrame(response)
    except:
        return pd.DataFrame()

def run_insert(table_name, data_dict):
    try:
        supabase.table(table_name).insert(data_dict).execute()
        return True
    except:
        return False

def run_update(table_name, match_col, match_val, update_dict):
    try:
        supabase.table(table_name).update(update_dict).eq(match_col, match_val).execute()
        return True
    except:
        return False

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
        botao_entrar = st.form_submit_button("Entrar no Sistema")
        if botao_entrar:
            if user == USUARIO_MASTER and criar_hash(password) == SENHA_HASH_MASTER:
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

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

if choice == "Cadastros Base":
    st.header("⚙️ Cadastros Estruturais e Plano de Contas")
    tab1, tab2, tab3, tab4 = st.tabs(["Clientes/Fornecedores", "Históricos Padrão", "Acumuladores", "Plano de Contas"])
    
    with tab1:
        st.subheader("Gerenciar Participantes")
        with st.form("form_participante"):
            nome = st.text_input("Razão Social / Nome")
            doc = st.text_input("CPF / CNPJ")
            tipo = st.selectbox("Tipo", ["Fornecedor", "Cliente"])
            lista_contas = ["Padrão do Acumulador"]
            if not contas_df.empty:
                lista_contas += [f"{row['codigo_reduzido']} - {row['nome']}" for _, row in contas_df.iterrows()]
            conta_part = st.selectbox("Conta Contábil Específica (Opcional)", lista_contas)
            if st.form_submit_button("Salvar Novo Participante"):
                c_reduzido = conta_part.split(" - ")[0] if conta_part != "Padrão do Acumulador" else None
                if run_insert("participantes", {"nome": nome, "documento": doc, "tipo": tipo, "conta_contabil": c_reduzido}):
                    st.success("Cadastrado com sucesso!")
                    st.rerun()
        st.write("---")
        part_df = run_query("participantes")
        if not part_df.empty: st.dataframe(part_df, use_container_width=True)
            
    with tab2:
        st.subheader("Gerenciar Históricos Padrão")
        with st.form("form_historico"):
            cod_h = st.text_input("Código Histórico")
            desc_h = st.text_input("Texto do Histórico (Ex: Vlr ref nf)")
            if st.form_submit_button("Salvar Novo Histórico"):
                if run_insert("historicos", {"codigo": cod_h, "descricao": desc_h}):
                    st.success("Histórico Salvo!")
                    st.rerun()
        st.write("---")
        hist_df = run_query("historicos")
        if not hist_df.empty: st.dataframe(hist_df, use_container_width=True)

    with tab3:
        st.subheader("Gerenciar Acumuladores")
        with st.form("form_acumulador"):
            cod_a = st.text_input("Código do Acumulador")
            desc_a = st.text_input("Descrição da Operação")
            op_a = st.selectbox("Tipo de Movimento", ["Entrada", "Saída", "Serviço Prestado"])
            contas_com_dinamico = ["FORNECEDOR", "CLIENTE"]
            if not contas_df.empty:
                contas_com_dinamico += [f"{row['codigo_reduzido']} - {row['nome']}" for _, row in contas_df.iterrows()]
            c_deb = st.selectbox("Conta Débito", contas_com_dinamico)
            c_cred = st.selectbox("Conta Crédito", contas_com_dinamico)
            hist_df = run_query("historicos")
            lista_hist = [f"{row['codigo']} - {row['descricao']}" for _, row in hist_df.iterrows()] if not hist_df.empty else []
            h_padrao = st.selectbox("Histórico Padrão Base", lista_hist) if lista_hist else st.text_input("Código do Histórico Manual (Ex: 100)")
            aliq = st.number_input("Alíquota de Imposto (%)", min_value=0.0, max_value=100.0, step=0.1)
            if st.form_submit_button("Salvar Novo Acumulador"):
                d_cod = c_deb.split(" - ")[0] if " - " in c_deb else c_deb
                c_cod = c_cred.split(" - ")[0] if " - " in c_cred else c_cred
                h_cod = h_padrao.split(" - ")[0] if " - " in h_padrao else h_padrao
                if run_insert("acumuladores", {"codigo": cod_a, "descricao": desc_a, "operacao": op_a, "conta_debito": d_cod, "conta_credito": c_cod, "historico_padrao": h_cod, "aliquota_imposto": aliq/100}):
                    st.success("Acumulador Cadastrado!")
                    st.rerun()
        st.write("---")
        acum_df = run_query("acumuladores")
        if not acum_df.empty: st.dataframe(acum_df, use_container_width=True)

    with tab4:
        st.subheader("Gestão do Plano de Contas")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**Adicionar Nova Conta**")
            with st.form("new_account_form"):
                n_red = st.text_input("Código Reduzido (Ex: 12)")
                n_est = st.text_input("Código Estruturado (Ex: 1.1.01.02.0005)")
                n_nome = st.text_input("Nome da Conta Contábil")
                n_grp = st.selectbox("Grupo Contábil", ["Ativo", "Passivo", "PL", "Receita", "Despesa"])
                if st.form_submit_button("Adicionar Conta"):
                    if run_insert("plano_contas", {"codigo_reduzido": n_red, "codigo_estruturado": n_est, "nome": n_nome, "grupo": n_grp}):
                        st.success("Conta adicionada!")
                        st.rerun()
        with col_c2:
            st.markdown("**Editar Conta Existente**")
            if not contas_df.empty:
                dict_edit_contas = {f"{row['codigo_reduzido']} - {row['nome']}": row for _, row in contas_df.iterrows()}
                conta_para_editar = st.selectbox("Selecione a Conta", list(dict_edit_contas.keys()))
                dados_originais = dict_edit_contas[conta_para_editar]
                with st.form("edit_account_form"):
                    ed_nome = st.text_input("Novo Nome", value=dados_originais['nome'])
                    ed_est = st.text_input("Novo Estruturado", value=dados_originais['codigo_estruturado'])
                    ed_grp = st.selectbox("Novo Grupo", ["Ativo", "Passivo", "PL", "Receita", "Despesa"], index=["Ativo", "Passivo", "PL", "Receita", "Despesa"].index(dados_originais['grupo']))
                    if st.form_submit_button("Salvar Alterações"):
                        if run_update("plano_contas", "codigo_reduzido", dados_originais['codigo_reduzido'], {"nome": ed_nome, "codigo_estruturado": ed_est, "grupo": ed_grp}):
                            st.success("Conta updated!")
                            st.rerun()
            else:
                st.info("Nenhuma conta para editar ainda.")
        st.write("---")
        if not contas_df.empty: st.dataframe(contas_df.sort_values(by="codigo_estruturado"), use_container_width=True)

elif choice == "Lançamento de Notas":
    st.header("🧾 Escrituração Fiscal Dinâmica (Padrão Domínio)")
    part_df = run_query("participantes")
    acum_df = run_query("acumuladores")
    if part_df.empty or acum_df.empty:
        st.warning("Acesse o menu 'Cadastros Base' (última opção da lista) e registre um Participante e um Acumulador para liberar esta tela.")
    else:
        with st.form("form_nota"):
            col1, col2 = st.columns(2)
            with col1:
                data_nf = st.date_input("Data da Nota", datetime.now())
                num_nf = st.text_input("Número do Documento / NF")
                dict_part = {row['id']: (row['nome'], row['conta_contabil']) for _, row in part_df.iterrows()}
                lista_p = [f"{i} - {n}" for i, n in dict_part.items()]
                participante_sel = st.selectbox("Cliente / Fornecedor", lista_p)
            with col2:
                dict_acum = {row['codigo']: row for _, row in acum_df.iterrows()}
                lista_a = [f"{c} - {row['descricao']}" for c, row in dict_acum.items()]
                acum_sel = st.selectbox("Acumulador Contábil", lista_a)
                valor_nf = st.number_input("Valor Bruto da Nota (R$)", min_value=0.0, step=10.0)
                regime = st.selectbox("Regime Tributário:", ["Simples Nacional", "Lucro Presumido"])

