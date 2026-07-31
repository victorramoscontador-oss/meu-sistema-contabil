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
# CAMADA DE DADOS E CARGA DE CONTAS BASEADA NO BALANCETE REAL DO HARDMAN FLAT
# ==============================================================================

@str.cache_data(ttl=5)
def buscar_empresas_contabilidade():
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
        {"codigo": "1", "descricao": "ATIVO", "tipo": "Ativo", "nivel": 1},
        {"codigo": "1.1", "descricao": "ATIVO CIRCULANTE", "tipo": "Ativo", "nivel": 2},
        {"codigo": "1.1.1", "descricao": "DISPONÍVEL", "tipo": "Ativo", "nivel": 3},
        {"codigo": "1.1.1.01.0001", "descricao": "CAIXA GERAL", "tipo": "Ativo", "nivel": 5},
        {"codigo": "1.1.1.02.0002", "descricao": "BRADESCO", "tipo": "Ativo", "nivel": 5},
        {"codigo": "1.1.1.02.0006", "descricao": "BANCO INTER", "tipo": "Ativo", "nivel": 5},
        {"codigo": "2", "descricao": "PASSIVO", "tipo": "Passivo", "nivel": 1},
        {"codigo": "2.1", "descricao": "PASSIVO CIRCULANTE", "tipo": "Passivo", "nivel": 2},
        {"codigo": "2.1.1.01.0010", "descricao": "FORNECEDORES DIVERSOS", "tipo": "Passivo", "nivel": 5},
        {"codigo": "3", "descricao": "RECEITAS OPERACIONAIS", "tipo": "Receita", "nivel": 1},
        {"codigo": "3.3.6.01.0008", "descricao": "TAXA DE CONDOMÍNIO", "tipo": "Receita", "nivel": 5},
        {"codigo": "4", "descricao": "DESPESAS OPERACIONAIS", "tipo": "Despesa", "nivel": 1},
        {"codigo": "4.3.3.04.0001", "descricao": "ÁGUA E ESGOTO", "tipo": "Despesa", "nivel": 5},
        {"codigo": "4.3.3.04.0009", "descricao": "ENERGIA ELÉTRICA", "tipo": "Despesa", "nivel": 5}
    ]
    if not supabase: return pd.DataFrame(dados_hardman)
    try:
        resposta = supabase.table("plano_contas").select("codigo, descricao, tipo, nivel").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(dados_hardman)
    except Exception:
        return pd.DataFrame(dados_hardman)
@str.cache_data(ttl=5)
def buscar_participantes(empresa_id):
    dados_part = [
        {"id": 1, "nome": "THALIA DOS SANTOS GUILHERME", "documento": "53.957.929", "tipo": "Fornecedor"},
        {"id": 2, "nome": "MANUELINA ALVES HARDMAN VIRGOLINO", "documento": "556.988.754-72", "tipo": "Cliente"}
    ]
    if not supabase: return pd.DataFrame(dados_part)
    try:
        resposta = supabase.table("participantes").select("id, nome, documento, tipo").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_part)
    except Exception:
        return pd.DataFrame(dados_part)

@str.cache_data(ttl=5)
def buscar_acumuladores(empresa_id):
    dados_acum = [{"id": 1, "operacao": "Rateio de Condomínio Geral", "aliquota": 0.0}]
    if not supabase: return pd.DataFrame(dados_acum)
    try:
        resposta = supabase.table("acumuladores").select("id, operacao, aliquota").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_acum)
    except Exception:
        return pd.DataFrame(dados_acum)

@str.cache_data(ttl=5)
def buscar_historicos(empresa_id):
    dados_hist = [{"id": 1, "descricao": "Arrecadação de cota condominial ordinária"}]
    if not supabase: return pd.DataFrame(dados_hist)
    try:
        resposta = supabase.table("historicos_padrao").select("id, descricao").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_hist)
    except Exception:
        return pd.DataFrame(dados_hist)

@str.cache_data(ttl=5)
def buscar_regras_ofx(empresa_id):
    dados_ofx = [{"id": 1, "termo_chave": "COELBA", "conta_id": "4.3.3.04.0009"}]
    if not supabase: return pd.DataFrame(dados_ofx)
    try:
        resposta = supabase.table("regras_ofx").select("id, termo_chave, conta_id").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_ofx)
    except Exception:
        return pd.DataFrame(dados_ofx)
def renderizar_modulo_lancamentos(empresa_id):
    str.header("Escrituração Contábil Manual")
    
    df_contas = buscar_plano_contas(empresa_id)
    df_historicos = buscar_historicos(empresa_id)
    
    opcoes_contas = [f"{row['codigo']} - {row['descricao']}" for _, row in df_contas.iterrows()]
    opcoes_hist = [f"{row['id']} - {row['descricao']}" for _, row in df_historicos.iterrows()]
    
    data_lan = str.date_input("Data do Lançamento")
    c_debito = str.selectbox("Conta de Débito (Aplicação)", options=opcoes_contas)
    c_credito = str.selectbox("Conta de Crédito (Origem)", options=opcoes_contas)
    valor_lan = str.number_input("Valor do Lançamento", min_value=0.0)
    historic = str.selectbox("Histórico Padrão", options=opcoes_hist)
    
    if str.button("Gravar Lançamento"):
        # CORREÇÃO DO ERRO: Transforma o objeto de data em texto padrão (AAAA-MM-DD) esperado pelo banco
        payload = {
            "data": data_lan.strftime("%Y-%m-%d"), 
            "conta_debito": c_debito, 
            "conta_credito": c_credito, 
            "valor": valor_lan, 
            "historico": historic
        }
        try:
            supabase.table("lancamentos").insert(payload).execute()
            str.success("Lançamento gravado com sucesso!")
        except Exception as e:
            str.error(f"Erro ao gravar: {e}")
def renderizar_modulo_cadastros(empresa_id):
    str.header("Cadastros Estruturais")
    str.dataframe(buscar_plano_contas(empresa_id))

def renderizar_modulo_demonstracoes(empresa_id):
    str.header("Demonstrações Oficiais")
    
    # Aplica a div de impressão que você criou no CSS original
    str.markdown('<div class="print-area">', unsafe_allow_html=True)
    str.write("### Balancete de Verificação")
    str.dataframe(buscar_plano_contas(empresa_id))
    str.markdown('</div>', unsafe_allow_html=True)
    
    # CORREÇÃO DO PDF: Substituição do botão que não funcionava por execução JavaScript nativa do navegador
    botao_pdf = """
    <script>
    function dispararImpressao() {
        window.print();
    }
    </script>
    <button onclick="dispararImpressao()" style="
        background-color: #00ff66;
        color: #0b2216;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        padding: 10px 20px;
        cursor: pointer;
        font-size: 16px;
    ">🖨️ Gerar Relatório (Salvar em PDF)</button>
    """
    str.components.v1.html(botao_pdf, height=60)

def main():
    str.sidebar.markdown('<span class="logo-texto">>><<</span>', unsafe_allow_html=True)
    str.sidebar.title("Fluxo Assessoria")
    str.sidebar.caption("Assessoria Empresarial de Alta Performance")
    
    df_empresas = buscar_empresas_contabilidade()
    empresas = [row['razao_social'] for _, row in df_empresas.iterrows()]
    empresa_ativa = str.sidebar.selectbox("Selecione o Cliente Contábil", empresas)
    empresa_id = df_empresas[df_empresas['razao_social'] == empresa_ativa]['id'].values[0]
    
    str.sidebar.markdown("### Navegação")
    opcao = str.sidebar.radio("Ir para", ["Escrituração Contábil", "Cadastros Estruturais", "Demonstrações Oficiais"])
    
    if str.sidebar.button("Encerra Sessão / Logout"):
        str.session_state['autenticado'] = False
        str.rerun()
        
    if opcao == "Escrituração Contábil":
        renderizar_modulo_lancamentos(empresa_id)
    elif opcao == "Cadastros Estruturais":
        renderizar_modulo_cadastros(empresa_id)
    elif opcao == "Demonstrações Oficiais":
        renderizar_modulo_demonstracoes(empresa_id)

if __name__ == "__main__":
    main()
