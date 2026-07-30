import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import hashlib

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
    except Exception as e:
        st.error(f"Erro ao ler a tabela {table_name}: {e}")
        return pd.DataFrame()

def run_insert(table_name, data_dict):
    try:
        supabase.table(table_name).insert(data_dict).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
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
    col_l, col_c, col_r = st.columns(3)
    with col_c:
        tela_login()
    st.stop()

# 3. INTERFACE E MENUS
st.set_page_config(page_title="Sistema Contábil Próprio", layout="wide")

if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state['autenticado'] = False
    st.rerun()

st.title("📊 Mini Domínio - Sistema Contábil Particular")

menu = ["Lançamento de Notas", "Folha de Pagamento", "Importação OFX (Banco)", "Demonstrações Contábeis", "Cadastros Base"]
choice = st.sidebar.selectbox("Navegação do Sistema", menu)

# MENU: CADASTROS BASE
if choice == "Cadastros Base":
    st.header("⚙️ Cadastros Estruturais")
    tab1, tab2, tab3 = st.tabs(["Clientes/Fornecedores", "Históricos Padrão", "Acumuladores"])
    
    with tab1:
        st.subheader("Novo Participante")
        nome = st.text_input("Razão Social / Nome")
        doc = st.text_input("CPF / CNPJ")
        tipo = st.selectbox("Tipo", ["Fornecedor", "Cliente"])
        
        contas_df = run_query("plano_contas")
        if not contas_df.empty:
            lista_contas = ["Padrão do Acumulador"] + [f"{row['codigo_reduzido']} - {row['nome']}" for _, row in contas_df.iterrows()]
        else:
            lista_contas = ["Padrão do Acumulador"]
        conta_part = st.selectbox("Conta Contábil Específica (Opcional)", lista_contas)
        
        if st.button("Salvar Participante"):
            c_reduzido = conta_part.split(" - ")[0] if conta_part != "Padrão do Acumulador" else None
            if run_insert("participantes", {"nome": nome, "documento": doc, "tipo": tipo, "conta_contabil": c_reduzido}):
                st.success("Participante cadastrado no banco em nuvem!")
            
    with tab2:
        st.subheader("Novo Histórico Padrão")
        cod_h = st.text_input("Código Histórico")
        desc_h = st.text_input("Texto do Histórico (Ex: Vlr ref nf)")
        if st.button("Salvar Histórico"):
            if run_insert("historicos", {"codigo": cod_h, "descricao": desc_h}):
                st.success("Histórico cadastrado no banco em nuvem!")

    with tab3:
        st.subheader("Configuração de Acumuladores")
        cod_a = st.text_input("Código do Acumulador")
        desc_a = st.text_input("Descrição da Operação")
        op_a = st.selectbox("Tipo de Movimento", ["Entrada", "Saída", "Serviço Prestado"])
        
        contas_df = run_query("plano_contas")
        if not contas_df.empty:
            contas_com_dinamico = ["FORNECEDOR", "CLIENTE"] + [f"{row['codigo_reduzido']} - {row['nome']}" for _, row in contas_df.iterrows()]
        else:
            contas_com_dinamico = ["FORNECEDOR", "CLIENTE"]
        
        c_deb = st.selectbox("Conta Débito", contas_com_dinamico)
        c_cred = st.selectbox("Conta Crédito", contas_com_dinamico)
        
        hist_df = run_query("historicos")
        if not hist_df.empty:
            lista_hist = [f"{row['codigo']} - {row['descricao']}" for _, row in hist_df.iterrows()]
        else:
            lista_hist = []
            
        h_padrao = st.selectbox("Histórico Padrão Base", lista_hist) if lista_hist else st.text_input("Código do Histórico Manual")
        aliq = st.number_input("Alíquota de Imposto para este Acumulador (%)", min_value=0.0, max_value=100.0, step=0.1)
        
        if st.button("Salvar Acumulador"):
            d_cod = c_deb.split(" - ")[0] if " - " in c_deb else c_deb
            c_cod = c_cred.split(" - ")[0] if " - " in c_cred else c_cred
            h_cod = h_padrao.split(" - ")[0] if " - " in h_padrao else h_padrao
            if run_insert("acumuladores", {
                "codigo": cod_a, "descricao": desc_a, "operacao": op_a, 
                "conta_debito": d_cod, "conta_credito": c_cod, 
                "historico_padrao": h_cod, "aliquota_imposto": aliq/100
            }):
                st.success("Acumulador configurado com sucesso!")

# MENU: LANÇAMENTO DE NOTAS
elif choice == "Lançamento de Notas":
    st.header("🧾 Escrituração Fiscal Dinâmica")
    part_df = run_query("participantes")
    acum_df = run_query("acumuladores")
    
    if part_df.empty or acum_df.empty:
        st.warning("Vá ao menu 'Cadastros Base' do lado esquerdo e cadastre pelo menos um Participante (Cliente/Fornecedor) para liberar os lançamentos.")
    else:
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
            regime = st.selectbox("Simular Cálculo de Imposto sob Regime:", ["Simples Nacional", "Lucro Presumido"])

        if st.button("Processar e Gerar Lançamento Contábil"):
            id_p = int(participante_sel.split(" - ")[0])
            nome_p, conta_especifica_p = dict_part[id_p]
            cod_ac = acum_sel.split(" - ")[0]
            config_ac = dict_acum[cod_ac]
            c_debito = config_ac['conta_debito']
            c_credito = config_ac['conta_credito']
            
            if c_debito in ["FORNECEDOR", "CLIENTE"]:
                c_debito = conta_especifica_p if conta_especifica_p else ('4' if c_debito == "FORNECEDOR" else '3')
            if c_credito in ["FORNECEDOR", "CLIENTE"]:
                c_credito = conta_especifica_p if conta_especifica_p else ('4' if c_credito == "FORNECEDOR" else '3')
                
            try:
                hist_base = supabase.table("historicos").select("descricao").eq("codigo", config_ac['historico_padrao']).execute().data
                hist_txt = hist_base[0]['descricao'] if hist_base else ""
            except:
                hist_txt = ""
                
            historico_final = f"{hist_txt} NF {num_nf}, Part: {nome_p}"
            
            run_insert("diario", {"data": str(data_nf), "conta_debito": str(c_debito), "conta_credito": str(c_credito), "valor": valor_nf, "historico": historico_final, "origem": "Fiscal"})
            
            imposto_calculado = valor_nf * float(config_ac['aliquota_imposto'])
            if imposto_calculado > 0:
                run_insert("diario", {"data": str(data_nf), "conta_debito": "11", "conta_credito": "6", "valor": imposto_calculado, "historico": f"Provisao de Imposto ref. NF {num_nf}", "origem": "Imposto Nota"})
                st.info(f"Imposto provisionado: R$ {imposto_calculado:.2f} ({regime})")
            st.success("Lançamentos contábeis salvos permanentemente na nuvem!")

# MENU: FOLHA DE PAGAMENTO
elif choice == "Folha de Pagamento":
    st.header("👥 Módulo de Folha Simplificado")
    data_folha = st.date_input("Competência da Folha", datetime.now())
    salario_bruto = st.number_input("Valor Total dos Salários Brutos (R$)", min_value=0.0, step=100.0)
    inss_retido = st.number_input("Valor Total do INSS Retido (R$)", min_value=0.0, step=10.0)
    
    if st.button("Fechar Folha e Integrar"):
        data_str = str(data_folha)
        run_insert("diario", {"data": data_str, "conta_debito": "10", "conta_credito": "5", "valor": salario_bruto, "historico": f"Vr ref folha competencia {data_str[:7]}", "origem": "Folha"})
        if inss_retido > 0:
            run_insert("diario", {"data": data_str, "conta_debito": "5", "conta_credito": "6", "valor": inss_retido, "historico": f"Vr ref INSS descontado folha {data_str[:7]}", "origem": "Folha"})
        st.success("Folha integrada e gravada na nuvem!")

# MENU: IMPORTAÇÃO BANCO (OFX)
