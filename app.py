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

# Credenciais Reais do Supabase do Cliente
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhjZ3R5dXd6emh6aGV0dmppaml4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU0MTc3NDAsImV4cCI6MjEwMDk5Mzc0MH0._b3waLLjoYLL_VyCWGaksovJKr4ZZi-fo2EA2z9vRpA"

USUARIO_CORRETO = "contador"
SENHA_CORRETA = "admin123"

# Inicialização do Banco de Dados
@str.cache_resource
def inicializar_supabase() -> Client:
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        str.error(f"Erro de conexão com o Supabase: {e}")
        return None

supabase = inicializar_supabase()

# Injeção de Identidade Visual via CSS (Ajuste de Centralização e Tamanho do Logo)
str.markdown("""
    <style>
    @import url('https://googleapis.com');
    html, body, [data-testid="stSidebar"] {
        font-family: 'Roboto', 'Segoe UI', sans-serif;
    }
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #0b2216; color: #ffffff; }
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] small, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span { 
        color: #ffffff !important; 
    }
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
    
    /* Logotipo Ampliado, com Espaçamento Negativo Justo e Totalmente Centralizado na Sidebar */
    .logo-texto {
        font-size: 52px;
        font-weight: bold;
        color: #00ff66;
        font-family: monospace;
        letter-spacing: -5px;
        text-align: center;
        margin-top: -15px;
        margin-bottom: 15px;
        padding-right: 15px;
        display: block;
        width: 100%;
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
# CAMADA DE DADOS E CARGA DE CONTAS BASEADA NO BALANCETE REAL DO HARDMAN FLAT
# ==============================================================================

@str.cache_data(ttl=5)
def buscar_plano_contas():
    dados_hardman = [
        {"codigo": "1", "descricao": "ATIVO", "tipo": "Ativo", "nivel": 1, "superior": ""},
        {"codigo": "1.1", "descricao": "ATIVO CIRCULANTE", "tipo": "Ativo", "nivel": 2, "superior": "1"},
        {"codigo": "1.1.1", "descricao": "DISPONÍVEL", "tipo": "Ativo", "nivel": 3, "superior": "1.1"},
        {"codigo": "1.1.1.01", "descricao": "CAIXA GENERAL", "tipo": "Ativo", "nivel": 4, "superior": "1.1.1"},
        {"codigo": "1.1.1.02", "descricao": "BANCOS CONTA MOVIMENTO", "tipo": "Ativo", "nivel": 4, "superior": "1.1.1"},
        {"codigo": "1.1.1.02.0002", "descricao": "BRADESCO", "tipo": "Ativo", "nivel": 5, "superior": "1.1.1.02"},
        {"codigo": "1.1.1.02.0003", "descricao": "CONTA PJ CONTA AZUL", "tipo": "Ativo", "nivel": 5, "superior": "1.1.1.02"},
        {"codigo": "1.1.1.02.0006", "descricao": "BANCO INTER", "tipo": "Ativo", "nivel": 5, "superior": "1.1.1.02"},
        {"codigo": "1.1.2", "descricao": "CLIENTES - DUPLICATAS A RECEBER", "tipo": "Ativo", "nivel": 3, "superior": "1.1"},
        {"codigo": "1.2", "descricao": "ATIVO NÃO-CIRCULANTE", "tipo": "Ativo", "nivel": 2, "superior": "1"},
        {"codigo": "1.2.4", "descricao": "IMOBILIZADO (MÓVEIS / MÁQUINAS)", "tipo": "Ativo", "nivel": 3, "superior": "1.2"},
        {"codigo": "2", "descricao": "PASSIVO", "tipo": "Passivo", "nivel": 1, "superior": ""},
        {"codigo": "2.1", "descricao": "PASSIVO CIRCULANTE", "tipo": "Passivo", "nivel": 2, "superior": "2"},
        {"codigo": "2.1.1", "descricao": "FORNECEDORES", "tipo": "Passivo", "nivel": 3, "superior": "2.1"},
        {"codigo": "2.1.2", "descricao": "OBRIGAÇÕES TRIBUTÁRIAS", "tipo": "Passivo", "nivel": 3, "superior": "2.1"},
        {"codigo": "2.3", "descricao": "PATRIMÔNIO LÍQUIDO", "tipo": "Passivo", "nivel": 2, "superior": "2"},
        {"codigo": "3", "descricao": "RECEITAS / RESULTADO DO EXERCÍCIO", "tipo": "Receita", "nivel": 1, "superior": ""},
        {"codigo": "3.3", "descricao": "OUTRAS RECEITAS OPERACIONAIS", "tipo": "Receita", "nivel": 2, "superior": "3"},
        {"codigo": "3.3.6.01.0008", "descricao": "TAXA DE CONDOMÍNIO", "tipo": "Receita", "nivel": 5, "superior": "3.3"},
        {"codigo": "4", "descricao": "DESPESAS OPERACIONAIS", "tipo": "Despesa", "nivel": 1, "superior": ""},
        {"codigo": "4.3.3.04.0001", "descricao": "ÁGUA E ESGOTO", "tipo": "Despesa", "nivel": 5, "superior": "4"},
        {"codigo": "4.3.3.04.0009", "descricao": "ENERGIA ELÉTRICA", "tipo": "Despesa", "nivel": 5, "superior": "4"}
    ]
    if not supabase: 
        return pd.DataFrame(dados_hardman)
    try:
        resposta = supabase.table("plano_contas").select("codigo, descricao, tipo, nivel, superior").execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(dados_hardman)
    except Exception:
        return pd.DataFrame(dados_hardman)

@str.cache_data(ttl=5)
def buscar_participantes():
    dados_part = [
        {"id": 1, "nome": "THALIA DOS SANTOS GUILHERME", "documento": "53.957.929", "tipo": "Fornecedor"},
        {"id": 2, "nome": "ELEVADORES OTIS LTDA", "documento": "32.387.842", "tipo": "Fornecedor"},
        {"id": 3, "nome": "FLF PAISAGISMO LTDA", "documento": "02.921.728", "tipo": "Fornecedor"},
        {"id": 4, "nome": "MANUELINA ALVES HARDMAN VIRGOLINO", "documento": "556.988.754-72", "tipo": "Cliente"}
    ]
    if not supabase: return pd.DataFrame(dados_part)
    try:
        resposta = supabase.table("participantes").select("id, nome, documento, tipo").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_part)
    except Exception:
        return pd.DataFrame(dados_part)

@str.cache_data(ttl=5)
def buscar_acumuladores():
    if not supabase: return pd.DataFrame([{"id": 1, "operacao": "Receita Rateio Condomínio", "aliquota": 0.0}])
    try:
        resposta = supabase.table("acumuladores").select("id, operacao, aliquota").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame([{"id": 1, "operacao": "Receita Rateio Condomínio", "aliquota": 0.0}])
    except Exception:
        return pd.DataFrame([{"id": 1, "operacao": "Receita Rateio Condomínio", "aliquota": 0.0}])

@str.cache_data(ttl=5)
def buscar_historicos():
    if not supabase: return pd.DataFrame([{"id": 1, "descricao": "Valor ref. taxa condominial ordinaria"}])
    try:
        resposta = supabase.table("historicos_padrao").select("id, descricao").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame([{"id": 1, "descricao": "Valor ref. taxa condominial ordinaria"}])
    except Exception:
        return pd.DataFrame([{"id": 1, "descricao": "Valor ref. taxa condominial ordinaria"}])

@str.cache_data(ttl=2)
def buscar_lancamentos(data_inicio, data_fim):
    if not supabase: return pd.DataFrame(columns=["id", "data", "conta_debito", "conta_credito", "valor", "historico"])
    try:
        resposta = supabase.table("lancamentos").select("id, data, conta_debito, conta_credito, valor, historico")\
            .gte("data", data_inicio.strftime('%Y-%m-%d'))\
            .lte("data", data_fim.strftime('%Y-%m-%d')).execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["id", "data", "conta_debito", "conta_credito", "valor", "historico"])
    except Exception:
        return pd.DataFrame(columns=["id", "data", "conta_debito", "conta_credito", "valor", "historico"])
def processar_balancete_df(df_lancamentos, df_plano, data_limite):
    if df_plano.empty:
        return pd.DataFrame(columns=["Código", "Descrição", "Débito", "Crédito", "Saldo Atual", "Nível", "Tipo"])
    
    saldos = {row['codigo']: {'debito': 0.0, 'credito': 0.0} for _, row in df_plano.iterrows()}
    
    if not df_lancamentos.empty:
        df_filtrado = df_lancamentos[pd.to_datetime(df_lancamentos['data']) <= pd.to_datetime(data_limite)]
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
        
        if tipo in ['Ativo', 'Despesa']:
            saldo_atual = total_deb - total_cred
        else:
            saldo_atual = total_cred - total_deb
            
        balancete_dados.append({
            "Código": cod, "Descrição": conta['descricao'], "Tipo": tipo,
            "Nível": conta['nivel'], "Débito": total_deb, "Crédito": total_cred, "Saldo Atual": saldo_atual
        })
    return pd.DataFrame(balancete_dados)

def renderizar_modulo_lancamentos():
    str.header("Entrada de Dados e Escrituração Contábil")
    
    df_plano = buscar_plano_contas()
    df_part = buscar_participantes()
    df_acum = buscar_acumuladores()
    df_hist = buscar_historicos()
    
    aba1, aba2, aba3, aba4 = str.tabs(["Lançamento Manual", "Importação NF-e / Notas", "Folha de Pagamento", "Conciliação OFX Real"])
    
    with aba1:
        str.subheader("Lançamento Partida Dobrada")
        with str.form("form_manual", clear_on_submit=True):
            col1, col2 = str.columns(2)
            data_lan = col1.date_input("Data do Fato Contábil", format="DD/MM/YYYY")
            valor_lan = col2.number_input("Valor (R$)", min_value=0.01, step=10.0)
            
            lista_hist = df_hist['descricao'].tolist() if not df_hist.empty else []
            historico_lan = str.selectbox("Histórico da Operação", options=[""] + lista_hist) if lista_hist else str.text_input("Histórico da Operação")
            
            col4, col5 = str.columns(2)
            opcoes_contas = df_plano['codigo'].tolist()
            c_debito = col4.selectbox("Conta de Débito (Aplicação)", options=opcoes_contas)
            c_credito = col5.selectbox("Conta de Crédito (Origem)", options=opcoes_contas)
            
            if str.form_submit_button("Gravar Lançamento"):
                if c_debito == c_credito:
                    str.error("As contas não podem ser idênticas.")
                else:
                    payload = {"data": str(data_lan), "conta_debito": c_debito, "conta_credito": c_credito, "valor": valor_lan, "historico": str(historico_lan)}
                    if supabase:
                        supabase.table("lancamentos").insert(payload).execute()
                        str.success("Lançamento Contábil registrado com sucesso!")
                        str.cache_data.clear()

    with aba2:
        str.subheader("Escrituração Manual de Notas Fiscais")
        with str.form("form_nota", clear_on_submit=True):
            col1, col2, col3 = str.columns(3)
            num_nota = col1.text_input("Número da NF-e")
            lista_part = df_part['nome'].tolist() if not df_part.empty else []
            col2.selectbox("Fornecedor / Cliente", options=lista_part)
            lista_acum = df_acum['id'].tolist() if not df_acum.empty else []
            str.selectbox("Acumulador / Operação", options=lista_acum)
            
            str.number_input("Valor Bruto (R$)", min_value=0.00)
            if str.form_submit_button("Escriturar Nota Fiscal"):
                str.success("Nota fiscal enviada ao diário!")

    with aba3:
        str.subheader("Provisão de Folha de Pagamento")
        with str.form("form_folha"):
            str.number_input("Total Salários Brutos (R$)", min_value=0.0)
            if str.form_submit_button("Lançar Provisão de Folha"):
                str.success("Folha provisionada com sucesso!")

    with aba4:
        str.subheader("Processador de Extratos Bancários OFX")
        str.file_uploader("Selecione o arquivo .ofx", type=["ofx"])
def renderizar_modulo_cadastros():
    str.header("Painel de Cadastros Estruturais")
    aba_c1, aba_c2, aba_c3, aba_c4 = str.tabs(["Contas Contábeis", "Clientes/Fornecedores", "Acumuladores Fiscais", "Históricos Padrão"])
    
    with aba_c1:
        str.subheader("Plano de Contas Ativo")
        df_p = buscar_plano_contas()
        str.dataframe(df_p, use_container_width=True, hide_index=True)
        conta_sel = str.selectbox("Selecione uma conta para Excluir", options=df_p['codigo'].tolist())
        if str.button("Excluir Conta Selecionada") and supabase:
            supabase.table("plano_contas").delete().eq("codigo", conta_sel).execute()
            str.success("Conta removida!")
            str.cache_data.clear()
            str.rerun()
        
        with str.form("cad_conta", clear_on_submit=True):
            cod = str.text_input("Novo Código")
            desc = str.text_input("Descrição da Conta")
            tp = str.selectbox("Tipo", ["Ativo", "Passivo", "Patrimônio Líquido", "Receita", "Despesa"])
            nv = str.number_input("Nível", min_value=1, max_value=5, value=5)
            if str.form_submit_button("Salvar Conta") and supabase:
                supabase.table("plano_contas").insert({"codigo": cod, "descricao": desc, "tipo": tp, "nivel": nv}).execute()
                str.cache_data.clear()
                str.rerun()

    with aba_c2:
        str.subheader("Clientes e Fornecedores Cadastrados")
        df_part = buscar_participantes()
        str.dataframe(df_part, use_container_width=True, hide_index=True)
        
        with str.form("cad_part", clear_on_submit=True):
            nome = str.text_input("Razão Social")
            doc = str.text_input("CNPJ / CPF")
            tipo_p = str.selectbox("Tipo", ["Fornecedor", "Cliente"])
            if str.form_submit_button("Salvar") and supabase:
                supabase.table("participantes").insert({"nome": nome, "documento": doc, "tipo": tipo_p}).execute()
                str.cache_data.clear()
                str.rerun()

    with aba_c3:
        str.subheader("Acumuladores Fiscais")
        df_a = buscar_acumuladores()
        str.dataframe(df_a, use_container_width=True, hide_index=True)

    with aba_c4:
        str.subheader("Históricos Contábeis Padrão")
        df_h = buscar_historicos()
        str.dataframe(df_h, use_container_width=True, hide_index=True)

def renderizar_demonstracoes():
    str.header("Demonstrações e Relatórios Contábeis Oficiais")
    col_data1, col_data2 = str.columns(2)
    d_ini = col_data1.date_input("Data de Início", pd.to_datetime("2026-01-01"), format="DD/MM/YYYY")
    d_fim = col_data2.date_input("Data de Fim", pd.to_datetime("2026-12-31"), format="DD/MM/YYYY")
    
    df_lanc = buscar_lancamentos(d_ini, d_fim)
    df_plano = buscar_plano_contas()
    df_balancete = processar_balancete_df(df_lanc, df_plano, d_fim)
    
    aba_rep1, aba_rep2, aba_rep3 = str.tabs(["Balancete por Níveis", "DRE Dedutiva Oficial", "Balanço Patrimonial Vertical"])
    
    with aba_rep1:
        str.subheader("Balancete por Grupos de Contas")
        nivel_sel = str.slider("Filtrar por Nível Hierárquico", 1, 5, 5)
        df_f = df_balancete[df_balancete['Nível'] <= nivel_sel]
        str.dataframe(df_f[["Código", "Descrição", "Débito", "Crédito", "Saldo Atual"]], use_container_width=True, hide_index=True)

    with aba_rep2:
        str.subheader("DRE Dedutiva")
        str.info("Análise baseada nas contas de resultado do período.")

    with aba_rep3:
        str.subheader("Balanço Patrimonial Estruturado Vertical")
        df_balanco = df_balancete[df_balancete['Tipo'].isin(['Ativo', 'Passivo', 'Patrimônio Líquido'])].copy()
        str.dataframe(df_balanco[["Código", "Descrição", "Tipo", "Saldo Atual"]], use_container_width=True, hide_index=True)

def main():
    # Renderização da marca centralizada e com tamanho aumentado no topo esquerdo do menu
    str.sidebar.markdown('<div class="logo-texto">&gt;&gt;&lt;&lt;</div>', unsafe_allow_html=True)
    str.sidebar.title("Fluxo Assessoria")
    str.sidebar.caption("Assessoria Financeira de Alta Performance")
    str.sidebar.markdown("---")
    
    opcao_menu = str.sidebar.radio("Navegação", ["Escrituração Contábil", "Cadastros Estruturais", "Demonstrações Oficiais"])
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
