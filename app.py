import streamlit as str
import pandas as pd
from supabase import create_client, Client

# Configuração da página (Primeiro comando Streamlit)
str.set_page_config(
    page_title="Fluxo Assessoria Empresarial",
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

# Injeção de Identidade Visual via CSS (Estilos de Impressão PDF Inclusos)
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
    .logo-texto {
        font-size: 72px;
        font-weight: 900;
        color: #00ff66;
        font-family: 'Segoe UI', monospace;
        letter-spacing: -6px;
        text-align: center;
        margin-top: -25px;
        margin-bottom: 5px;
        padding: 0;
        display: block;
        width: 100%;
        line-height: 1;
    }
    
    /* REGRAS CSS EXCLUSIVAS PARA IMPRESSÃO DO PDF CONTÁBIL */
    @media print {
        body * { visibility: hidden; }
        .print-area, .print-area * { visibility: visible; }
        .print-area {
            position: absolute;
            left: 0; top: 0; width: 100%;
            color: #000000 !important;
            background: #ffffff !important;
            font-size: 12px;
        }
        [data-testid="stSidebar"] { display: none !important; }
        header { display: none !important; }
        
        /* Marca D'água Cabeçalho Superior Direito Exigido */
        .print-area::before {
            content: "FLUXO ASSESSORIA EMPRESARIAL";
            position: absolute;
            right: 0; top: -20px;
            font-size: 10px;
            font-weight: bold;
            color: #555555;
            font-family: sans-serif;
        }
    }
    </style>
""", unsafe_allow_html=True)

if 'autenticado' not in str.session_state:
    str.session_state['autenticado'] = False

if not str.session_state['autenticado']:
    str.title("Fluxo Assessoria Empresarial")
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
# CONTROLE DE NÚCLEO MULTIEMPRESAS (ISOLAMENTO DE DADOS)
# ==============================================================================

@str.cache_data(ttl=5)
def buscar_empresas_contabilidade():
    # Carga fixa inicial para garantir o funcionamento caso a tabela remota seja criada agora
    empresas_padrao = [
        {"id": 1, "razao_social": "Condomínio Edifício Hardman Praia Flat", "cnpj": "02.960.693/0001-90"},
        {"id": 2, "razao_social": "Fluxo Prime Holding Ltda", "cnpj": "44.123.456/0001-99"}
    ]
    if not supabase: return pd.DataFrame(empresas_padrao)
    try:
        resposta = supabase.table("empresas_clientes").select("id, razao_social, cnpj").execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(empresas_padrao)
    except Exception:
        return pd.DataFrame(empresas_padrao)

@str.cache_data(ttl=5)
def buscar_plano_contas(empresa_id):
    dados_hardman = [
        {"codigo": "1", "descricao": "ATIVO", "tipo": "Ativo", "nivel": 1, "empresa_id": empresa_id},
        {"codigo": "1.1", "descricao": "ATIVO CIRCULANTE", "tipo": "Ativo", "nivel": 2, "empresa_id": empresa_id},
        {"codigo": "1.1.1", "descricao": "DISPONÍVEL", "tipo": "Ativo", "nivel": 3, "empresa_id": empresa_id},
        {"codigo": "1.1.1.01", "descricao": "CAIXA GENERAL", "tipo": "Ativo", "nivel": 4, "empresa_id": empresa_id},
        {"codigo": "1.1.1.02", "descricao": "BANCOS CONTA MOVIMENTO", "tipo": "Ativo", "nivel": 4, "empresa_id": empresa_id},
        {"codigo": "1.1.1.02.0002", "descricao": "BRADESCO", "tipo": "Ativo", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "1.1.1.02.0006", "descricao": "BANCO INTER", "tipo": "Ativo", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "2", "descricao": "PASSIVO", "tipo": "Passivo", "nivel": 1, "empresa_id": empresa_id},
        {"codigo": "2.1", "descricao": "PASSIVO CIRCULANTE", "tipo": "Passivo", "nivel": 2, "empresa_id": empresa_id},
        {"codigo": "2.1.1", "descricao": "FORNECEDORES", "tipo": "Passivo", "nivel": 3, "empresa_id": empresa_id},
        {"codigo": "3", "descricao": "RECEITAS", "tipo": "Receita", "nivel": 1, "empresa_id": empresa_id},
        {"codigo": "3.3.6.01.0008", "descricao": "TAXA DE CONDOMÍNIO", "tipo": "Receita", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "4", "descricao": "DESPESAS OPERACIONAIS", "tipo": "Despesa", "nivel": 1, "empresa_id": empresa_id},
        {"codigo": "4.3.3.04.0009", "descricao": "ENERGIA ELÉTRICA", "tipo": "Despesa", "nivel": 5, "empresa_id": empresa_id}
    ]
    if not supabase: return pd.DataFrame(dados_hardman)
    try:
        # Filtro ativo na query do Supabase para buscar apenas registros da empresa selecionada
        resposta = supabase.table("plano_contas").select("codigo, descricao, tipo, nivel").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(dados_hardman)
    except Exception:
        return pd.DataFrame(dados_hardman)

@str.cache_data(ttl=5)
def buscar_participantes(empresa_id):
    dados_part = [
        {"id": 1, "nome": "THALIA DOS SANTOS GUILHERME", "documento": "53.957.929", "tipo": "Fornecedor", "empresa_id": empresa_id},
        {"id": 2, "nome": "MANUELINA ALVES HARDMAN VIRGOLINO", "documento": "556.988.754-72", "tipo": "Cliente", "empresa_id": empresa_id}
    ]
    if not supabase: return pd.DataFrame(dados_part)
    try:
        resposta = supabase.table("participantes").select("id, nome, documento, tipo").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_part)
    except Exception:
        return pd.DataFrame(dados_part)

@str.cache_data(ttl=5)
def buscar_lancamentos(data_inicio, data_fim, empresa_id):
    if not supabase: return pd.DataFrame(columns=["id", "data", "conta_debito", "conta_credito", "valor", "historico"])
    try:
        resposta = supabase.table("lancamentos").select("id, data, conta_debito, conta_credito, valor, historico")\
            .eq("empresa_id", empresa_id)\
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
            deb, cred, val = lanc['conta_debito'], lanc['conta_credito'], float(lanc['valor'])
            if deb in saldos: saldos[deb]['debito'] += val
            if cred in saldos: saldos[cred]['credito'] += val

    balancete_dados = []
    for _, conta in df_plano.iterrows():
        cod, tipo = conta['codigo'], conta['tipo']
        total_deb = sum(valores['debito'] for c_cod, valores in saldos.items() if c_cod.startswith(cod))
        total_cred = sum(valores['credito'] for c_cod, valores in saldos.items() if c_cod.startswith(cod))
        saldo_atual = (total_deb - total_cred) if tipo in ['Ativo', 'Despesa'] else (total_cred - total_deb)
        balancete_dados.append({
            "Código": cod, "Descrição": conta['descricao'], "Tipo": tipo,
            "Nível": conta['nivel'], "Débito": total_deb, "Crédito": total_cred, "Saldo Atual": saldo_atual
        })
    return pd.DataFrame(balancete_dados)

def renderizar_modulo_lancamentos(empresa_id):
    str.header("Entrada de Dados e Escrituração Contábil")
    df_plano = buscar_plano_contas(empresa_id)
    df_part = buscar_participantes(empresa_id)
    
    aba1, aba2, aba3 = str.tabs(["Lançamento Manual", "Importação NF-e", "Conciliação OFX Real"])
    
    with aba1:
        str.subheader("Lançamento Partida Dobrada (Diário Geral)")
        with str.form("form_manual", clear_on_submit=True):
            col1, col2 = str.columns(2)
            data_lan = col1.date_input("Data do Fato Contábil", format="DD/MM/YYYY")
            valor_lan = col2.number_input("Valor (R$)", min_value=0.01)
            historico_lan = str.text_input("Histórico")
            
            c_debito = str.selectbox("Conta de Débito", options=df_plano['codigo'].tolist() if not df_plano.empty else [""])
            c_credito = str.selectbox("Conta de Crédito", options=df_plano['codigo'].tolist() if not df_plano.empty else [""])
            
            if str.form_submit_button("Gravar Lançamento") and supabase:
                payload = {"data": str(data_lan), "conta_debito": c_debito, "conta_credito": c_credito, "valor": valor_lan, "historico": historico_lan, "empresa_id": empresa_id}
                supabase.table("lancamentos").insert(payload).execute()
                str.success("Lançamento Contábil registrado nesta empresa!")
                str.cache_data.clear()
def renderizar_modulo_cadastros(empresa_id):
    str.header("Painel de Cadastros Contábeis e Empresas Cliente")
    aba_emp, aba_contas, aba_part = str.tabs(["Cadastrar Empresas (Suas Clientes)", "Plano de Contas da Empresa", "Clientes/Fornecedores"])
    
    with aba_emp:
        str.subheader("Suas Empresas Clientes Ativas")
        df_e = buscar_empresas_contabilidade()
        str.dataframe(df_e, use_container_width=True, hide_index=True)
        with str.form("cad_nova_empresa", clear_on_submit=True):
            rz = str.text_input("Razão Social da Empresa Cliente")
            cn = str.text_input("CNPJ")
            if str.form_submit_button("Cadastrar Nova Empresa Cliente") and supabase:
                supabase.table("empresas_clientes").insert({"razao_social": rz, "cnpj": cn}).execute()
                str.success("Empresa adicionada à sua carteira contábil!")
                str.cache_data.clear()
                str.rerun()

    with aba_contas:
        str.subheader("Plano de Contas Vinculado")
        df_p = buscar_plano_contas(empresa_id)
        str.dataframe(df_p, use_container_width=True, hide_index=True)
        with str.form("cad_conta_p", clear_on_submit=True):
            c_cod = str.text_input("Código")
            c_des = str.text_input("Nome da Conta")
            c_tp = str.selectbox("Tipo", ["Ativo", "Passivo", "Patrimônio Líquido", "Receita", "Despesa"])
            c_nv = str.number_input("Nível", min_value=1, max_value=5, value=5)
            if str.form_submit_button("Salvar Conta") and supabase:
                supabase.table("plano_contas").insert({"codigo": c_cod, "descricao": c_des, "tipo": c_tp, "nivel": c_nv, "empresa_id": empresa_id}).execute()
                str.success("Conta salva nesta empresa!")
                str.cache_data.clear()
                str.rerun()

def renderizar_demonstracoes(empresa_id, nome_empresa):
    str.header("Demonstrações e Relatórios Contábeis")
    
    col1, col2 = str.columns(2)
    d_ini = col1.date_input("Início", pd.to_datetime("2026-01-01"), format="DD/MM/YYYY")
    d_fim = col2.date_input("Fim", pd.to_datetime("2026-12-31"), format="DD/MM/YYYY")
    
    df_lanc = buscar_lancamentos(d_ini, d_fim, empresa_id)
    df_plano = buscar_plano_contas(empresa_id)
    df_balancete = processar_balancete_df(df_lanc, df_plano, d_fim)
    
    # BOTÃO PARA ACIONAR IMPRESSÃO DO PDF
    str.markdown('<button onclick="window.print()" style="background-color:#00ff66;color:#0b2216;padding:10px 20px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;margin-bottom:15px;">🖨️ Imprimir Relatório / Salvar em PDF</button>', unsafe_allow_html=True)
    
    aba_rep1, aba_rep2 = str.tabs(["Balancete Oficial por Grupos", "Balanço Patrimonial Vertical"])
    
    with aba_rep1:
        # Bloco HTML com classe para isolamento na área de impressão do PDF
        str.markdown(f"""
        <div class="print-area">
            <h2>BALANCETE DE VERIFICAÇÃO</h2>
            <p><b>Empresa Cliente:</b> {nome_empresa}</p>
            <p><b>Período Contábil:</b> {d_ini.strftime('%d/%m/%Y')} até {d_fim.strftime('%d/%m/%Y')}</p>
            <hr/>
        </div>
        """, unsafe_allow_html=True)
        str.dataframe(df_balancete[["Código", "Descrição", "Débito", "Crédito", "Saldo Atual"]], use_container_width=True, hide_index=True)

def main():
    str.sidebar.markdown('<div class="logo-texto">&gt;&gt;&lt;&lt;</div>', unsafe_allow_html=True)
    str.sidebar.title("Fluxo Assessoria")
    str.sidebar.caption("Assessoria Empresarial de Alta Performance")
    str.sidebar.markdown("---")
    
    # SELETOR DO SEU CLIENTE CENTRAL (SISTEMA MULTIEMPRESA E SEGURO)
    df_empresas_disponiveis = buscar_empresas_contabilidade()
    lista_nomes = df_empresas_disponiveis['razao_social'].tolist() if not df_empresas_disponiveis.empty else ["Nenhuma cadastrada"]
    
    emp_selecionada_nome = str.sidebar.selectbox("📊 Selecione o Cliente Contábil", options=lista_nomes)
    
    # Captura com segurança o ID da empresa selecionada
    if not df_empresas_disponiveis.empty and emp_selecionada_nome != "Nenhuma cadastrada":
        empresa_id_ativa = int(df_empresas_disponiveis[df_empresas_disponiveis['razao_social'] == emp_selecionada_nome]['id'].values[0])
    else:
        empresa_id_ativa = 1
        
    str.sidebar.markdown("---")
    opcao_menu = str.sidebar.radio("Navegação", ["Escrituração Contábil", "Cadastros Estruturais", "Demonstrações Oficiais"])
    
    if str.sidebar.button("Encerrar Sessão / Logout"):
        str.session_state['autenticado'] = False
        str.rerun()

    if opcao_menu == "Escrituração Contábil":
        renderizar_modulo_lancamentos(empresa_id_ativa)
    elif opcao_menu == "Cadastros Estruturais":
        renderizar_modulo_cadastros(empresa_id_ativa)
    elif opcao_menu == "Demonstrações Oficiais":
        renderizar_demonstracoes(empresa_id_ativa, emp_selecionada_nome)

if __name__ == "__main__":
    main()
