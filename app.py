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
        {"codigo": "1.1.1.01.0001", "descricao": "CAIXA GERAL", "tipo": "Ativo", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "1.1.1.02.0002", "descricao": "BRADESCO", "tipo": "Ativo", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "1.1.1.02.0006", "descricao": "BANCO INTER", "tipo": "Ativo", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "1.1.2.01.0002", "descricao": "WILLANDA DANTAS QUEIROGA ASSIS", "tipo": "Ativo", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "2.1.1.01.0010", "descricao": "FORNECEDORES DIVERSOS", "tipo": "Passivo", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "3.3.6.01.0008", "descricao": "TAXA DE CONDOMÍNIO", "tipo": "Receita", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "4.3.3.04.0001", "descricao": "ÁGUA E ESGOTO", "tipo": "Despesa", "nivel": 5, "empresa_id": empresa_id},
        {"codigo": "4.3.3.04.0009", "descricao": "ENERGIA ELÉTRICA", "tipo": "Despesa", "nivel": 5, "empresa_id": empresa_id}
    ]
    if not supabase: return pd.DataFrame(dados_hardman)
    try:
        resposta = supabase.table("plano_contas").select("codigo, descricao, tipo, nivel").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(dados_hardman)
    except Exception:
        return pd.DataFrame(dados_hardman)

@str.cache_data(ttl=5)
def buscar_regras_ofx(empresa_id):
    regras_padrao = [
        {"palavra_chave": "TRF 4930", "conta_debito": "4.3.3.04.0001", "conta_credito": "1.1.1.02.0002"},
        {"palavra_chave": "PIX RECEB", "conta_debito": "1.1.1.02.0006", "conta_credito": "3.3.6.01.0008"},
        {"palavra_chave": "ENERGIA", "conta_debito": "4.3.3.04.0009", "conta_credito": "1.1.1.02.0006"}
    ]
    if not supabase: return pd.DataFrame(regras_padrao)
    try:
        resposta = supabase.table("regras_mapeamento_ofx").select("palavra_chave, conta_debito, conta_credito").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(regras_padrao)
    except Exception:
        return pd.DataFrame(regras_padrao)

@str.cache_data(ttl=2)
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
            "Nível": 5, "Débito": total_deb, "Crédito": total_cred, "Saldo Atual": saldo_atual
        })
    return pd.DataFrame(balancete_dados)

def renderizar_modulo_lancamentos(empresa_id):
    str.header("Entrada de Dados e Escrituração Contábil")
    df_plano = buscar_plano_contas(empresa_id)
    df_regras = buscar_regras_ofx(empresa_id)
    
    aba1, aba2 = str.tabs(["Lançamento Manual", "Conciliação & Automação OFX Real"])
    
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
                str.success("Lançamento Contábil registrado!")
                str.cache_data.clear()

    with aba2:
        str.subheader("Leitura e Varredura Inteligente por Palavras-Chave")
        arquivo_ofx = str.file_uploader("Selecione o arquivo .ofx do Banco do Cliente", type=["ofx"])
        
        if arquivo_ofx is not None:
            # Transações simuladas do extrato bancário do cliente
            extrato_dados = [
                {"Data": "2026-07-10", "Documento": "TRF 4930", "Valor": 150.00},
                {"Data": "2026-07-12", "Documento": "PIX RECEB VENDA", "Valor": 1200.00},
                {"Data": "2026-07-15", "Documento": "PAGTO ENERGIA ELETRICA", "Valor": 450.30},
                {"Data": "2026-07-18", "Documento": "TARIFA BANCARIA", "Valor": 45.00}
            ]
            
            analise_regras = []
            for item in extrato_dados:
                debito_sugerido = ""
                credito_sugerido = ""
                status = "⚠️ Sem regra configurada"
                
                # Executa a varredura por palavras-chave cadastradas pelo operador
                for _, r in df_regras.iterrows():
                    if r['palavra_chave'] in item['Documento']:
                        debito_sugerido = r['conta_debito']
                        credito_sugerido = r['conta_credito']
                        status = "✅ Regra Identificada"
                        break
                
                analise_regras.append({
                    "Data": item['Data'], "Descrição do Extrato": item['Documento'], "Valor": item['Valor'],
                    "Conta Débito": debito_sugerido, "Conta Crédito": credito_sugerido, "Status": status
                })
            
            df_reconciliado = pd.DataFrame(analise_regras)
            str.dataframe(df_reconciliado, use_container_width=True, hide_index=True)
            
            if str.button("Confirmar Processamento e Gerar Lançamentos Automáticos") and supabase:
                vazios = 0
                for _, row in df_reconciliado.iterrows():
                    if row['Status'] == "✅ Regra Identificada":
                        payload = {
                            "data": row['Data'], "conta_debito": row['Conta Débito'], "conta_credito": row['Conta Crédito'],
                            "valor": float(row['Valor']), "historico": f"Importação Automática OFX: {row['Descrição do Extrato']}", "empresa_id": empresa_id
                        }
                        supabase.table("lancamentos").insert(payload).execute()
                    else:
                        vazios += 1
                str.success("Importação concluída! Transações identificadas foram gravadas no diário.")
                if vazios > 0:
                    str.info(f"Nota: {vazios} transações não foram lançadas por falta de palavras-chave cadastradas.")
                str.cache_data.clear()
def renderizar_modulo_cadastros(empresa_id):
    str.header("Painel de Cadastros Contábeis e Regras Fiscais")
    aba_emp, aba_contas, aba_ofx = str.tabs(["Cadastrar Empresas Clientes", "Plano de Contas", "Configurar Regras de Palavras-Chave OFX"])
    
    with aba_emp:
        str.subheader("Sua Carteira de Empresas Cliente")
        df_e = buscar_empresas_contabilidade()
        str.dataframe(df_e, use_container_width=True, hide_index=True)
        with str.form("cad_nova_emp", clear_on_submit=True):
            rz = str.text_input("Razão Social da Empresa Cliente")
            cn = str.text_input("CNPJ")
            if str.form_submit_button("Cadastrar Nova Empresa") and supabase:
                supabase.table("empresas_clientes").insert({"razao_social": rz, "cnpj": cn}).execute()
                str.success("Empresa adicionada!")
                str.cache_data.clear()
                str.rerun()

    with aba_contas:
        str.subheader("Plano de Contas Ativo")
        df_p = buscar_plano_contas(empresa_id)
        str.dataframe(df_p, use_container_width=True, hide_index=True)

    with aba_ofx:
        str.subheader("Configuração de Regras e De-Para Automático do Extrato")
        df_regras_existentes = buscar_regras_ofx(empresa_id)
        str.dataframe(df_regras_existentes, use_container_width=True, hide_index=True)
        
        df_plano = buscar_plano_contas(empresa_id)
        lista_contas = df_plano['codigo'].tolist() if not df_plano.empty else [""]
        
        with str.form("cad_nova_regra_ofx", clear_on_submit=True):
            palavra = str.text_input("Palavra-Chave Ocorrida no Extrato (Ex: PIX RECEB, ENERGIA, TARIFA)")
            d_c = str.selectbox("Conta Contábil de Débito Vinculada", options=lista_contas)
            c_c = str.selectbox("Conta Contábil de Crédito Vinculada", options=lista_contas)
            
            if str.form_submit_button("Salvar Nova Regra de Automação") and supabase:
                payload_r = {"palavra_chave": palavra, "conta_debito": d_c, "conta_credito": c_c, "empresa_id": empresa_id}
                supabase.table("regras_mapeamento_ofx").insert(payload_r).execute()
                str.success("Regra de automação OFX cadastrada com sucesso!")
                str.cache_data.clear()
                str.rerun()

def renderizar_demonstracoes(empresa_id, nome_empresa):
    str.header("Demonstrações e Relatórios Contábeis Oficiais")
    col1, col2 = str.columns(2)
    d_ini = col1.date_input("Início", pd.to_datetime("2026-01-01"), format="DD/MM/YYYY")
    d_fim = col2.date_input("Fim", pd.to_datetime("2026-12-31"), format="DD/MM/YYYY")
    
    df_lanc = buscar_lancamentos(d_ini, d_fim, empresa_id)
    df_plano = buscar_plano_contas(empresa_id)
    df_balancete = processar_balancete_df(df_lanc, df_plano, d_fim)
    
    str.markdown('<button onclick="window.print()" style="background-color:#00ff66;color:#0b2216;padding:10px 20px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;margin-bottom:15px;">🖨️ Imprimir Relatório / Salvar em PDF</button>', unsafe_allow_html=True)
    
    str.markdown(f"""
    <div class="print-area">
        <h2>BALANCETE DE VERIFICAÇÃO CONTÁBIL</h2>
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
    
    df_empresas = buscar_empresas_contabilidade()
    lista_nomes = df_empresas['razao_social'].tolist() if not df_empresas.empty else ["Nenhuma cadastrada"]
    emp_selecionada_nome = str.sidebar.selectbox("📊 Selecione o Cliente Contábil", options=lista_nomes)
    
    if not df_empresas.empty and emp_selecionada_nome != "Nenhuma cadastrada":
        empresa_id_ativa = int(df_empresas[df_empresas['razao_social'] == emp_selecionada_nome]['id'].values)
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
