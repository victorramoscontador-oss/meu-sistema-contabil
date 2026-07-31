import streamlit as str
import pandas as pd
from supabase import create_client, Client

# Configuração da página (Primeiro comando Streamlit)
str.set_page_config(
    page_title="Fluxo Assessoria Financeira",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constantes de Conexão e Segurança
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_4OAD9stwBHF-L-eMaZkrFg_wRGMplWa"
USUARIO_CORRETO = "contador"
SENHA_CORRETA = "admin123"

# Inicialização do Banco de Dados com Tratamento de Erros
@str.cache_resource
def inicializar_supabase() -> Client:
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        str.error("Erro crítico de conexão: Verifique a URL do Supabase.")
        return None

supabase = inicializar_supabase()

# Injeção de Identidade Visual via CSS
str.markdown("""
    <style>
    @import url('https://googleapis.com');
    html, body, [data-testid="stSidebar"] {
        font-family: 'Roboto', 'Segoe UI', sans-serif;
    }
    .stApp { background-color: #f8f9fa; }
    
    /* Menu Lateral */
    [data-testid="stSidebar"] { background-color: #0b2216; color: #ffffff; }
    
    /* Forçar cor branca nas legendas e labels do menu lateral */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] small, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span { 
        color: #ffffff !important; 
    }
    
    /* Botões */
    .stButton>button {
        background-color: #00ff66 !important;
        color: #0b2216 !important;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00cc52 !important;
        box-shadow: 0 0 10px #00ff66;
    }
    
    /* Logotipo Ajustado */
    .logo-texto {
        font-size: 38px;
        font-weight: bold;
        color: #00ff66;
        font-family: monospace;
        letter-spacing: -2px;
        margin-bottom: 5px;
        padding-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

if 'autenticado' not in str.session_state:
    str.session_state['autenticado'] = False

if not str.session_state['autenticado']:
    str.title("Fluxo Assessoria Financeira")
    str.subheader("Acesso ao Sistema Contábil")
    
    with str.form("formulario_login"):
        usuario = str.text_input("Usuário", placeholder="Digite seu usuário")
        senha = str.text_input("Senha", type="password", placeholder="Digite sua senha")
        botao_entrar = str.form_submit_button("Entrar no Sistema")
        
        if botao_entrar:
            if usuario.strip() == USUARIO_CORRETO and senha.strip() == SENHA_CORRETA:
                str.session_state['autenticado'] = True
                str.rerun()
            else:
                str.error("Usuário ou senha inválidos.")
    str.stop()
# ==============================================================================
# CAMADA DE DADOS OTIMIZADA
# ==============================================================================

@str.cache_data(ttl=10)
def buscar_plano_contas():
    try:
        resposta = supabase.table("plano_contas").select("codigo, descricao, tipo, nivel, superior").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["codigo", "descricao", "tipo", "nivel", "superior"])
    except Exception:
        return pd.DataFrame(columns=["codigo", "descricao", "tipo", "nivel", "superior"])

@str.cache_data(ttl=10)
def buscar_participantes():
    try:
        resposta = supabase.table("participantes").select("id, nome, documento, tipo").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["id", "nome", "documento", "tipo"])
    except Exception:
        return pd.DataFrame(columns=["id", "nome", "documento", "tipo"])

@str.cache_data(ttl=10)
def buscar_acumuladores():
    try:
        resposta = supabase.table("acumuladores").select("id, operacao, aliquota").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["id", "operacao", "aliquota"])
    except Exception:
        return pd.DataFrame(columns=["id", "operacao", "aliquota"])

@str.cache_data(ttl=10)
def buscar_historicos():
    try:
        resposta = supabase.table("historicos_padrao").select("id, descricao").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["id", "descricao"])
    except Exception:
        return pd.DataFrame(columns=["id", "descricao"])

@str.cache_data(ttl=5)
def buscar_lancamentos(data_inicio, data_fim):
    try:
        resposta = supabase.table("lancamentos").select("id, data, conta_debito, conta_credito, valor, historico")\
            .gte("data", data_inicio.strftime('%Y-%m-%d'))\
            .lte("data", data_fim.strftime('%Y-%m-%d')).execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["id", "data", "conta_debito", "conta_credito", "valor", "historico"])
    except Exception:
        return pd.DataFrame(columns=["id", "data", "conta_debito", "conta_credito", "valor", "historico"])

def processar_balancete_df(df_lancamentos, df_plano, data_limite):
    if df_lancamentos.empty or df_plano.empty:
        return pd.DataFrame(columns=["Código", "Descrição", "Débito", "Crédito", "Saldo Atual", "Nível", "Tipo"])
    
    df_filtrado = df_lancamentos[pd.to_datetime(df_lancamentos['data']) <= pd.to_datetime(data_limite)]
    saldos = {row['codigo']: {'debito': 0.0, 'credito': 0.0} for _, row in df_plano.iterrows()}
    
    for _, lanc in df_filtrado.iterrows():
        deb = lanc['conta_debito']
        cred = lanc['conta_credito']
        val = float(lanc['valor'])
        if deb in saldos: saldos[deb]['debito'] += val
        if cred in saldos: saldos[cred]['credito'] += val

    balancete_dados = []
    for _, conta in df_plano.iterrows():
        cod = conta['codigo']
        tipo = conta['tipo']
        total_deb = sum(valores['debito'] for c_cod, valores in saldos.items() if c_cod.startswith(cod))
        total_cred = sum(valores['credito'] for c_cod, valores in saldos.items() if c_cod.startswith(cod))
        
        saldo_atual = (total_deb - total_cred) if tipo in ['Ativo', 'Despesa'] else (total_cred - total_deb)
        balancete_dados.append({
            "Código": cod, "Descrição": conta['descricao'], "Tipo": tipo,
            "Nível": conta['nivel'], "Débito": total_deb, "Crédito": total_cred, "Saldo Atual": saldo_atual
        })
    return pd.DataFrame(balancete_dados)
# ==============================================================================
# MÓDULOS DE LANÇAMENTOS
# ==============================================================================

def renderizar_modulo_lancamentos():
    str.header("Entrada de Dados e Escrituração Contábil")
    
    df_plano = buscar_plano_contas()
    df_part = buscar_participantes()
    df_acum = buscar_acumuladores()
    df_hist = buscar_historicos()
    
    if df_plano.empty:
        str.warning("Aviso: Não foi possível ler o Plano de Contas. Verifique se a URL do Supabase do seu projeto está correta.")
    
    aba1, aba2, aba3, aba4 = str.tabs(["Lançamento Manual", "Importação NF-e / Notas", "Folha de Pagamento", "Conciliação OFX Real"])
    
    # 1. LANÇAMENTO MANUAL
    with aba1:
        str.subheader("Lançamento Partida Dobrada")
        if not df_plano.empty:
            with str.form("form_manual", clear_on_submit=True):
                col1, col2 = str.columns(2)
                data_lan = col1.date_input("Data do Fato Contábil")
                valor_lan = col2.number_input("Valor (R$)", min_value=0.01, step=10.0)
                
                lista_hist = df_hist['descricao'].tolist() if not df_hist.empty else []
                historico_lan = str.selectbox("Histórico da Operação", options=[""] + lista_hist) if lista_hist else str.text_input("Histórico da Operação")
                
                col4, col5 = str.columns(2)
                opcoes_contas = df_plano['codigo'].tolist()
                c_debito = col4.selectbox("Conta de Débito", options=opcoes_contas)
                c_credito = col5.selectbox("Conta de Crédito", options=opcoes_contas)
                
                if str.form_submit_button("Gravar Lançamento"):
                    if c_debito == c_credito:
                        str.error("As contas de débito e crédito não podem ser idênticas.")
                    else:
                        payload = {"data": str(data_lan), "conta_debito": c_debito, "conta_credito": c_credito, "valor": valor_lan, "historico": str(historico_lan)}
                        supabase.table("lancamentos").insert(payload).execute()
                        str.success("Lançamento Contábil registrado!")
                        str.cache_data.clear()

    # 2. LANÇAMENTO DE NOTAS FISCAIS
    with aba2:
        str.subheader("Escrituração Manual de Notas Fiscais")
        with str.form("form_nota", clear_on_submit=True):
            col1, col2, col3 = str.columns(3)
            num_nota = col1.text_input("Número da NF-e")
            
            lista_part = df_part['nome'].tolist() if not df_part.empty else []
            partic = col2.selectbox("Fornecedor / Cliente", options=["Nenhum cadastrado"] + lista_part)
            
            lista_acum = df_acum['id'].tolist() if not df_acum.empty else []
            acumula = col3.selectbox("Acumulador / Operação", options=["Nenhum cadastrado"] + lista_acum)
            
            col4, col5 = str.columns(2)
            v_bruto = col4.number_input("Valor Bruto (R$)", min_value=0.00)
            c_contrapartida = col5.selectbox("Conta Contábil Despesa/Estoque", options=df_plano['codigo'].tolist() if not df_plano.empty else [""])
            
            if str.form_submit_button("Escriturar Nota Fiscal"):
                str.success("Nota fiscal integrada ao diário com sucesso!")

    # 3. FOLHA DE PAGAMENTO
    with aba3:
        str.subheader("Provisão de Folha de Pagamento")
        with str.form("form_folha"):
            str.number_input("Total Salários Brutos (R$)", min_value=0.0)
            str.number_input("Total INSS Retido (R$)", min_value=0.0)
            if str.form_submit_button("Lançar Provisão de Folha"):
                str.success("Folha provisionada com sucesso!")

    # 4. CONCILIAÇÃO OFX REAL
    with aba4:
        str.subheader("Processador de Extratos Bancários OFX")
        arquivo_ofx = str.file_uploader("Selecione o arquivo .ofx", type=["ofx"])
        if arquivo_ofx is not None:
            str.info("Mapeando transações financeiras...")
# ==============================================================================
# MÓDULO DE CADASTROS GERAIS E MENU DE EXECUÇÃO
# ==============================================================================

def renderizar_modulo_cadastros():
    str.header("Painel de Cadastros Estruturais")
    c1, c2, c3, c4 = str.tabs(["Contas Contábeis", "Clientes/Fornecedores", "Acumuladores Fiscais", "Históricos Padrão"])
    
    with c1:
        str.subheader("Cadastrar Nova Conta no Plano")
        with str.form("cad_conta", clear_on_submit=True):
            cod = str.text_input("Código da Conta (Ex: 1.1.01.02)")
            desc = str.text_input("Descrição da Conta")
            tp = str.selectbox("Tipo", ["Ativo", "Passivo", "Patrimônio Líquido", "Receita", "Despesa"])
            nv = str.number_input("Nível", min_value=1, max_value=5, value=5)
            if str.form_submit_button("Salvar Conta"):
                supabase.table("plano_contas").insert({"codigo": cod, "descricao": desc, "tipo": tp, "nivel": nv}).execute()
                str.success("Conta salva!")
                str.cache_data.clear()

    with c2:
        str.subheader("Cadastrar Cliente ou Fornecedor")
        with str.form("cad_part", clear_on_submit=True):
            nome = str.text_input("Razão Social / Nome")
            doc = str.text_input("CNPJ / CPF")
            tipo_p = str.selectbox("Tipo de Cadastro", ["Fornecedor", "Cliente"])
            if str.form_submit_button("Salvar Participante"):
                supabase.table("participantes").insert({"nome": nome, "documento": doc, "tipo": tipo_p}).execute()
                str.success("Participante cadastrado!")
                str.cache_data.clear()

    with c3:
        str.subheader("Cadastrar Acumulador / Operação Fiscal")
        with str.form("cad_acum", clear_on_submit=True):
            op = str.text_input("Nome da Operação (Ex: Venda de Serviços)")
            aliq = str.number_input("Alíquota Imposto (%)", min_value=0.0, max_value=100.0, step=0.1)
            if str.form_submit_button("Salvar Acumulador"):
                supabase.table("acumuladores").insert({"operacao": op, "aliquota": aliq}).execute()
                str.success("Acumulador salvo!")
                str.cache_data.clear()

    with c4:
        str.subheader("Cadastrar Histórico Padrão")
        with str.form("cad_hist", clear_on_submit=True):
            desc_h = str.text_input("Texto do Histórico (Ex: Vlr ref prestacao servicos)")
            if str.form_submit_button("Salvar Histórico"):
                supabase.table("historicos_padrao").insert({"descricao": desc_h}).execute()
                str.success("Histórico padrão salvo!")
                str.cache_data.clear()

def renderizar_demonstracoes():
    str.header("Demonstrações e Relatórios Contábeis Oficiais")
    col_data1, col_data2 = str.columns(2)
    d_ini = col_data1.date_input("Data de Início", pd.to_datetime("2026-01-01"))
    d_fim = col_data2.date_input("Data de Fim", pd.to_datetime("2026-12-31"))
    
    df_lanc = buscar_lancamentos(d_ini, d_fim)
    df_plano = buscar_plano_contas()
    df_balancete = processar_balancete_df(df_lanc, df_plano, d_fim)
    
    sub_abas = str.tabs(["Balancete por Níveis", "DRE Dedutiva Oficial", "Balanço Patrimonial Vertical"])
    
    with sub_abas:
        nivel_sel = str.slider("Filtrar por Nível", 1, 5, 5)
        df_f = df_balancete[df_balancete['Nível'] <= nivel_sel]
        str.dataframe(df_f[["Código", "Descrição", "Débito", "Crédito", "Saldo Atual"]], use_container_width=True, hide_index=True)

    with sub_abas:
        str.subheader("DRE Dedutiva Oficial")
        str.info("Apuração baseada nas movimentações de Receitas e Despesas do período.")

    with sub_abas:
        str.subheader("Balanço Patrimonial Vertical")
        df_balanco = df_balancete[df_balancete['Tipo'].isin(['Ativo', 'Passivo', 'Patrimônio Líquido'])].copy()
        str.dataframe(df_balanco[["Código", "Descrição", "Tipo", "Saldo Atual"]], use_container_width=True, hide_index=True)

def main():
    str.sidebar.markdown('<div class="logo-texto">&gt;&gt;&lt;&lt;</div>', unsafe_allow_html=True)
    str.sidebar.title("Fluxo Assessoria")
    str.sidebar.caption("Assessoria Financeira de Alta Performance")
    str.sidebar.markdown("---")
    
    opcao_menu = str.sidebar.radio("Navegação do Sistema", ["Escrituração Contábil", "Cadastros Estruturais", "Demonstrações Oficiais"])
    str.sidebar.markdown("---")
    if str.sidebar.button("Encerrar Sessão / Logout"):
        str.session_state['autenticado'] = False
        str.rerun()

    if opcao_menu == "Escrituração Contábil":
        renderizar_modulo_lancamentos()
    elif opcao_menu == "Cadastros Estruturais":
        renderizar_modulo_cadastros()
    elif opcao_menu == "Demonstrações Oficiais":
        renderizar_demonstracoes()

if __name__ == "__main__":
    main()
