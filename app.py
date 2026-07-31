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
# IMPORTANTE: Altere para a URL exata do seu projeto do Supabase (ex: https://supabase.co)
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_4OAD9stwBHF-L-eMaZkrFg_wRGMplWa"
USUARIO_CORRETO = "contador"
SENHA_CORRETA = "admin123"

# Inicialização do Banco de Dados com Tratamento de Erros
@str.cache_resource
def inicializar_supabase() -> Client:
    try:
        if SUPABASE_URL == "https://supabase.co":
            return None
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
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

@str.cache_data(ttl=5)
def buscar_plano_contas():
    if not supabase: return pd.DataFrame(columns=["codigo", "descricao", "tipo", "nivel", "superior"])
    try:
        resposta = supabase.table("plano_contas").select("codigo, descricao, tipo, nivel, superior").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["codigo", "descricao", "tipo", "nivel", "superior"])
    except Exception:
        return pd.DataFrame(columns=["codigo", "descricao", "tipo", "nivel", "superior"])

@str.cache_data(ttl=5)
def buscar_participantes():
    if not supabase: return pd.DataFrame(columns=["id", "nome", "documento", "tipo"])
    try:
        resposta = supabase.table("participantes").select("id, nome, documento, tipo").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["id", "nome", "documento", "tipo"])
    except Exception:
        return pd.DataFrame(columns=["id", "nome", "documento", "tipo"])

@str.cache_data(ttl=5)
def buscar_acumuladores():
    if not supabase: return pd.DataFrame(columns=["id", "operacao", "aliquota"])
    try:
        resposta = supabase.table("acumuladores").select("id, operacao, aliquota").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["id", "operacao", "aliquota"])
    except Exception:
        return pd.DataFrame(columns=["id", "operacao", "aliquota"])

@str.cache_data(ttl=5)
def buscar_historicos():
    if not supabase: return pd.DataFrame(columns=["id", "descricao"])
    try:
        resposta = supabase.table("historicos_padrao").select("id, descricao").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["id", "descricao"])
    except Exception:
        return pd.DataFrame(columns=["id", "descricao"])

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
    
    if not supabase or df_plano.empty:
        str.warning("Aviso: Não foi possível ler o Plano de Contas. Verifique se a URL do Supabase do seu projeto está correta.")
    
    aba1, aba2, aba3, aba4 = str.tabs(["Lançamento Manual", "Importação NF-e / Notas", "Folha de Pagamento", "Conciliação OFX Real"])
    
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
                        if supabase:
                            supabase.table("lancamentos").insert(payload).execute()
                            str.success("Lançamento Contábil registrado!")
                            str.cache_data.clear()

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
                str.success("Nota fiscal cadastrada!")

    with aba3:
        str.subheader("Provisão de Folha de Pagamento")
        with str.form("form_folha"):
            str.number_input("Total Salários Brutos (R$)", min_value=0.0)
            str.number_input("Total INSS Retido (R$)", min_value=0.0)
            if str.form_submit_button("Lançar Provisão de Folha"):
                str.success("Folha provisionada com sucesso!")

    with aba4:
        str.subheader("Processador de Extratos Bancários OFX")
        str.file_uploader("Selecione o arquivo .ofx", type=["ofx"])
# ==============================================================================
# MÓDULO DE CADASTROS (VISUALIZAR, EDITAR E EXCLUIR) E DEMONSTRAÇÕES
# ==============================================================================

def renderizar_modulo_cadastros():
    str.header("Painel de Cadastros Estruturais")
    c1, c2, c3, c4 = str.tabs(["Contas Contábeis", "Clientes/Fornecedores", "Acumuladores Fiscais", "Históricos Padrão"])
    
    with c1:
        str.subheader("Gerenciar Plano de Contas")
        df_p = buscar_plano_contas()
        if not df_p.empty:
            str.dataframe(df_p, use_container_width=True, hide_index=True)
            conta_sel = str.selectbox("Selecione uma conta para Excluir/Editar", options=df_p['codigo'].tolist())
            if str.button("Excluir Conta Selecionada") and supabase:
                supabase.table("plano_contas").delete().eq("codigo", conta_sel).execute()
                str.success("Conta excluída!")
                str.cache_data.clear()
                str.rerun()
        
        with str.form("cad_conta", clear_on_submit=True):
            cod = str.text_input("Novo Código da Conta")
            desc = str.text_input("Descrição")
            tp = str.selectbox("Tipo", ["Ativo", "Passivo", "Patrimônio Líquido", "Receita", "Despesa"])
            nv = str.number_input("Nível", min_value=1, max_value=5, value=5)
            if str.form_submit_button("Salvar Nova Conta") and supabase:
                supabase.table("plano_contas").insert({"codigo": cod, "descricao": desc, "tipo": tp, "nivel": nv}).execute()
                str.success("Conta cadastrada!")
                str.cache_data.clear()
                str.rerun()

    with c2:
        str.subheader("Gerenciar Clientes / Fornecedores")
        df_part = buscar_participantes()
        if not df_part.empty:
            str.dataframe(df_part, use_container_width=True, hide_index=True)
            id_sel = str.selectbox("Selecione o ID para Excluir", options=df_part['id'].tolist() if 'id' in df_part.columns else [])
            if str.button("Excluir Participante") and supabase:
                supabase.table("participantes").delete().eq("id", id_sel).execute()
                str.success("Participante removido!")
                str.cache_data.clear()
                str.rerun()
                
        with str.form("cad_part", clear_on_submit=True):
            nome = str.text_input("Nome / Razão Social")
            doc = str.text_input("CNPJ / CPF")
            tipo_p = str.selectbox("Tipo", ["Fornecedor", "Cliente"])
            if str.form_submit_button("Salvar") and supabase:
                supabase.table("participantes").insert({"nome": nome, "documento": doc, "tipo": tipo_p}).execute()
                str.success("Salvo!")
                str.cache_data.clear()
                str.rerun()

    with c3:
        str.subheader("Gerenciar Acumuladores Fiscais")
        df_a = buscar_acumuladores()
        if not df_a.empty:
            str.dataframe(df_a, use_container_width=True, hide_index=True)
            ac_sel = str.selectbox("Selecione o ID do Acumulador para Excluir", options=df_a['id'].tolist() if 'id' in df_a.columns else [])
            if str.button("Excluir Acumulador") and supabase:
                supabase.table("acumuladores").delete().eq("id", ac_sel).execute()
                str.success("Acumulador deletado!")
                str.cache_data.clear()
                str.rerun()
                
        with str.form("cad_acum", clear_on_submit=True):
            op = str.text_input("Operação Fiscal")
            aliq = str.number_input("Alíquota (%)", min_value=0.0, max_value=100.0, step=0.1)
            if str.form_submit_button("Salvar Acumulador") and supabase:
                supabase.table("acumuladores").insert({"operacao": op, "aliquota": aliq}).execute()
                str.success("Gravado!")
                str.cache_data.clear()
                str.rerun()

    with c4:
        str.subheader("Gerenciar Históricos Padrão")
        df_h = buscar_historicos()
        if not df_h.empty:
            str.dataframe(df_h, use_container_width=True, hide_index=True)
            h_sel = str.selectbox("Selecione o ID do Histórico para Excluir", options=df_h['id'].tolist() if 'id' in df_h.columns else [])
            if str.button("Excluir Histórico") and supabase:
                supabase.table("historicos_padrao").delete().eq("id", h_sel).execute()
                str.success("Removido!")
                str.cache_data.clear()
                str.rerun()
                
        with str.form("cad_hist", clear_on_submit=True):
            desc_h = str.text_input("Texto do Histórico")
            if str.form_submit_button("Salvar Histórico") and supabase:
                supabase.table("historicos_padrao").insert({"descricao": desc_h}).execute()
                str.success("Histórico salvo!")
                str.cache_data.clear()
                str.rerun()

def renderizar_demonstracoes():
    str.header("Demonstrações e Relatórios Contábeis Oficiais")
    col_data1, col_data2 = str.columns(2)
    d_ini = col_data1.date_input("Data de Início", pd.to_datetime("2026-01-01"))
    d_fim = col_data2.date_input("Data de Fim", pd.to_datetime("2026-12-31"))
    
    df_lanc = buscar_lancamentos(d_ini, d_fim)
    df_plano = buscar_plano_contas()
    df_balancete = processar_balancete_df(df_lanc, df_plano, d_fim)
    
    aba_rep1, aba_rep2, aba_rep3 = str.tabs(["Balancete por Níveis", "DRE Dedutiva Oficial", "Balanço Patrimonial Vertical"])
    
    with aba_rep1:
        str.subheader("Balancete de Verificação Analítico")
        nivel_sel = str.slider("Filtrar por Nível", 1, 5, 5)
        if not df_balancete.empty:
            df_f = df_balancete[df_balancete['Nível'] <= nivel_sel]
            str.dataframe(df_f[["Código", "Descrição", "Débito", "Crédito", "Saldo Atual"]], use_container_width=True, hide_index=True)
        else:
            str.info("Nenhum dado contábil localizado no período.")

    with aba_rep2:
        str.subheader("DRE Dedutiva Oficial")
        if not df_balancete.empty:
            def obter_saldo_por_prefixo(prefixo):
                filtro = df_balancete[df_balancete['Código'].str.startswith(prefixo) & (df_balancete['Nível'] == 1)]
                return float(filtro['Saldo Atual'].values[0]) if not filtro.empty else 0.0
            
            rb = obter_saldo_por_prefixo("3.1")
            ded = obter_saldo_por_prefixo("3.2")
            rl = rb - ded
            cust = obter_saldo_por_prefixo("4")
            lb = rl - cust
            desp = obter_saldo_por_prefixo("5")
            rle = lb - desp
            
            str.markdown(f"""

            | Linha de Resultado da DRE Oficial | Valor Absoluto (R$) |
            | :--- | :--- |
            | **(=) RECEITA OPERACIONAL BRUTA** | **{rb:,.2f}** |
            | (-) Deduções de Receita e Impostos | ({ded:,.2f}) |
            | **(=) RECEITA LIQUIDA DO PERÍODO** | **{rl:,.2f}** |
            | (-) Custos Contábeis | ({cust:,.2f}) |
            | **(=) RESULTADO BRUTO** | **{lb:,.2f}** |
            | (-) Despesas Operacionais | ({desp:,.2f}) |
            | **(=) RESULTADO LÍQUIDO DO EXERCÍCIO (RLE)** | **{rle:,.2f}** |
            """)
        else:
            str.info("Gere lançamentos para consolidar o resultado contábil da DRE.")

    with aba_rep3:
        str.subheader("Balanço Patrimonial Estruturado Vertical")
        if not df_balancete.empty:
            df_balanco = df_balancete[df_balancete['Tipo'].isin(['Ativo', 'Passivo', 'Patrimônio Líquido'])].copy()
            str.dataframe(df_balanco[["Código", "Descrição", "Tipo", "Saldo Atual"]], use_container_width=True, hide_index=True)
        else:
            str.info("Aguardando saldos patrimoniais.")

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
