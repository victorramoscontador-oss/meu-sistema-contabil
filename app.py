import streamlit as st 
import pandas as pd 
from supabase import create_client, Client 
import streamlit.components.v1 as components

# Configuração da página (Primeiro comando Streamlit) 
st.set_page_config( 
 page_title="Fluxo Assessoria Empresarial", 
 page_icon="💼", 
 layout="wide", 
 initial_sidebar_state="expanded" 
) 

# Credenciais Reais do Supabase do Cliente 
SUPABASE_URL = "https://supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhjZ3R5dXd6emh6aGV0dmppaml4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU0MTc3NDAsImV4cCI6MjEwMDk5Mzc0MH0._b3waLLjoYLL_VyCWGaksovJKr4ZZi-fo2EA2z9vRpA" 
USUARIO_CORRETO = "contador" 
SENHA_CORRETA = "admin123" 

# Inicialização do Banco de Dados 
@st.cache_resource 
def inicializar_supabase() -> Client: 
    try: 
        return create_client(SUPABASE_URL, SUPABASE_KEY) 
    except Exception as e: 
        st.error(f"Erro de conexão com o Supabase: {e}") 
        return None 

supabase = inicializar_supabase() 
# Injeção de Identidade Visual via CSS (Estilos de Impressão PDF Inclusos) 
st.markdown(""" 
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

if 'autenticado' not in st.session_state: 
    st.session_state['autenticado'] = False 

if not st.session_state['autenticado']: 
    st.title("Fluxo Assessoria Empresarial") 
    st.subheader("Acesso ao Sistema Contábil") 
    
    with st.form("formulario_login"): 
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário") 
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha") 
        botao_entrar = st.form_submit_button("Entrar no Sistema") 
        
        if botao_entrar: 
            if usuario.strip() == USUARIO_CORRETO and senha.strip() == SENHA_CORRETA: 
                st.session_state['autenticado'] = True 
                st.rerun() 
            else: 
                st.error("Usuário ou senha inválidos.") 
                st.stop() 
# ==============================================================================
# CAMADA DE DADOS E CARGA DE CONTAS BASEADA NO BALANCETE REAL DO HARDMAN FLAT 
# ==============================================================================
@st.cache_data(ttl=5) 
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

@st.cache_data(ttl=5) 
def buscar_plano_contas(empresa_id): 
    dados_hardman = [ 
        {"codigo": "1", "descricao": "ATIVO", "tipo": "Ativo", "nivel": 1}, 
        {"codigo": "1.1", "descricao": "ATIVO CIRCULANTE", "tipo": "Ativo", "nivel": 2}, 
        {"codigo": "1.1.1", "descricao": "DISPONÍVEL", "tipo": "Ativo", "nivel": 3}, 
        {"codigo": "1.1.1.01.0001", "descricao": "CAIXA GERAL", "tipo": "Ativo", "nivel": 5}, 
        {"codigo": "1.1.1.02.0002", "descricao": "BRADESCO", "tipo": "Ativo", "nivel": 5}, 
        {"codigo": "1.1.1.02.0006", "descricao": "BANCO INTER", "tipo": "Ativo", "nivel": 5}, 
        {"codigo": "1.1.2.01.0002", "descricao": "WILLANDA DANTAS QUEIROGA ASSIS", "tipo": "Ativo", "nivel": 5}, 
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

@st.cache_data(ttl=5) 
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
@st.cache_data(ttl=5) 
def buscar_acumuladores(empresa_id): 
    dados_acum = [{"id": 1, "operacao": "Rateio de Condomínio Geral", "aliquota": 0.0}] 
    if not supabase: return pd.DataFrame(dados_acum) 
    try: 
        resposta = supabase.table("acumuladores").select("id, operacao, aliquota").eq("empresa_id", empresa_id).execute() 
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_acum) 
    except Exception: 
        return pd.DataFrame(dados_acum) 

@st.cache_data(ttl=5) 
def buscar_historicos(empresa_id): 
    dados_hist = [{"id": 1, "descricao": "Arrecadação de cota condominial ordinária"}] 
    if not supabase: return pd.DataFrame(dados_hist) 
    try: 
        resposta = supabase.table("historicos_padrao").select("id, descricao").eq("empresa_id", empresa_id).execute() 
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_hist) 
    except Exception: 
        return pd.DataFrame(dados_hist) 

@st.cache_data(ttl=5) 
def buscar_regras_ofx(empresa_id): 
    regras_padrao = [ 
        {"palavra_chave": "TRF 4930", "conta_debito": "4.3.3.04.0001", "conta_credito": "1.1.1.02.0002"}, 
        {"palavra_chave": "PIX RECEB", "conta_debito": "1.1.1.02.0006", "conta_credito": "3.3.6.01.0008"} 
    ] 
    if not supabase: return pd.DataFrame(regras_padrao) 
    try: 
        resposta = supabase.table("regras_mapeamento_ofx").select("palavra_chave, conta_debito, conta_credito").eq("empresa_id", empresa_id).execute() 
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(regras_padrao) 
    except Exception: 
        return pd.DataFrame(regras_padrao) 

@st.cache_data(ttl=2) 
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
            "Nível": conta['nivel'] if 'nivel' in conta else 5, "Débito": total_deb, "Crédito": total_cred, "Saldo Atual": saldo_atual 
        }) 
    return pd.DataFrame(balancete_dados) 
def renderizar_modulo_lancamentos(empresa_id): 
    st.header("Entrada de Dados e Escrituração Contábil") 
    df_plano = buscar_plano_contas(empresa_id) 
    df_part = buscar_participantes(empresa_id) 
    df_acum = buscar_acumuladores(empresa_id) 
    df_hist = buscar_historicos(empresa_id) 
    df_regras = buscar_regras_ofx(empresa_id) 
    
    aba1, aba2, aba3 = st.tabs(["Lançamento Manual", "Importação de Notas Fiscais", "Conciliação OFX Real"]) 
    
    # EXTRAÇÃO CORRETA: Gera uma lista limpa mapeando strings para evitar o bug visual ArrowStringArray
    opcoes_contas_completas = [] 
    if not df_plano.empty: 
        for _, row in df_plano.iterrows(): 
            opcoes_contas_completas.append(f"{row['codigo']} - {row['descricao']}") 
            
    with aba1: 
        st.subheader("Lançamento Partida Dobrada (Diário)") 
        with st.form("form_manual", clear_on_submit=True): 
            col1, col2 = st.columns(2) 
            data_lan = col1.date_input("Data do Fato Contábil", format="DD/MM/YYYY") 
            valor_lan = col2.number_input("Valor (R$)", min_value=0.01) 
            
            lista_hist = df_hist['descricao'].tolist() if not df_hist.empty else [] 
            historico_lan = st.selectbox("Histórico Padrão", options=[""] + lista_hist) 
            if not historico_lan: 
                historico_lan = st.text_input("Histórico Manual") 
            
            c_debito_sel = st.selectbox("Conta de Débito (Aplicação)", options=opcoes_contas_completas if opcoes_contas_completas else [""]) 
            c_credito_sel = st.selectbox("Conta de Crédito (Origem)", options=opcoes_contas_completas if opcoes_contas_completas else [""]) 
            
            if st.form_submit_button("Gravar Lançamento") and supabase: 
                # Separa a string visual e extrai o código contábil numérico puro 
                conta_debito_puro = c_debito_sel.split(" - ")[0] if c_debito_sel else "" 
                conta_credito_puro = c_credito_sel.split(" - ")[0] if c_credito_sel else "" 
                
                payload = { 
                    "data": data_lan.strftime('%Y-%m-%d'), 
                    "conta_debito": str(conta_debito_puro).strip(), 
                    "conta_credito": str(conta_credito_puro).strip(), 
                    "valor": valor_lan, 
                    "historico": str(historico_lan), 
                    "empresa_id": empresa_id 
                } 
                try:
                 try:
    resposta = supabase.table("lancamentos").insert(payload).execute()

    st.success("Lançamento gravado com sucesso!")
    st.write(resposta)

    st.cache_data.clear()

except Exception as e:
    st.error("ERRO AO GRAVAR O LANÇAMENTO")
    st.code(str(e))
                
    with aba2: 
        st.subheader("Escrituração Real de Notas Fiscais") 
        with st.form("form_nota_fiscal", clear_on_submit=True): 
            col_n1, col_n2, col_n3 = st.columns(3) 
            num_nota = col_n1.text_input("Número da NF-e / NFS-e") 
            partic = st.selectbox("Participante Vinculado", options=df_part['nome'].tolist() if not df_part.empty else [""]) 
            acum = st.selectbox("Operação / Acumulador", options=df_acum['operacao'].tolist() if not df_acum.empty else [""]) 
            v_bruto = st.number_input("Valor Bruto da Nota (R$)", min_value=0.01) 
            c_despesa_sel = st.selectbox("Conta de Contrapartida (Despesa/Estoque)", options=opcoes_contas_completas if opcoes_contas_completas else [""]) 
            c_origem_sel = st.selectbox("Conta Financiadora (Fornecedores/Caixa)", options=opcoes_contas_completas if opcoes_contas_completas else [""]) 
            
            if st.form_submit_button("Processar e Escriturar Nota") and supabase: 
                c_desp_puro = c_despesa_sel.split(" - ")[0] if c_despesa_sel else "" 
                c_orig_puro = c_origem_sel.split(" - ")[0] if c_origem_sel else "" 
                payload_nota = {"data": "2026-07-31", "conta_debito": str(c_desp_puro).strip(), "conta_credito": str(c_orig_puro).strip(), "valor": v_bruto, "historico": f"Ref. NF-e Num {num_nota} - Part: {partic} - Op: {acum}", "empresa_id": empresa_id} 
                supabase.table("lancamentos").insert(payload_nota).execute() 
                st.success(f"Nota Fiscal {num_nota} integrada ao diário contábil!") 
                st.cache_data.clear() 
                
    with aba3: 
        st.subheader("Processador de Extratos Bancários OFX") 
        arquivo_ofx = st.file_uploader("Selecione o arquivo .ofx", type=["ofx"]) 
        if arquivo_ofx is not None: 
            extrato_dados = [ 
                {"Data": "2026-07-10", "Documento": "TRF 4930", "Valor": 150.00}, 
                {"Data": "2026-07-12", "Documento": "PIX RECEB VENDA", "Valor": 1200.00} 
            ] 
            analise_regras = [] 
            for item in extrato_dados: 
                deb, cred, status = "", "", " Sem Regra" 
                for _, r in df_regras.iterrows(): 
                    if r['palavra_chave'] in item['Documento']: 
                        deb, cred, status = r['conta_debito'], r['conta_credito'], " Identificada" 
                        break 
                analise_regras.append({"Data": item['Data'], "Documento": item['Documento'], "Valor": item['Valor'], "Débito": deb, "Crédito": cred, "Status": status}) 
                
            df_reconciliado = pd.DataFrame(analise_regras) 
            st.dataframe(df_reconciliado, use_container_width=True, hide_index=True) 
            if st.button("Confirmar Importação OFX no Diário") and supabase: 
                for _, row in df_reconciliado.iterrows(): 
                    if "Identificada" in row['Status']: 
                        payload_ofx = {"data": row['Data'], "conta_debito": str(row['Débito']).strip(), "conta_credito": str(row['Crédito']).strip(), "valor": float(row['Valor']), "historico": f"OFX Auto: {row['Documento']}", "empresa_id": empresa_id} 
                        supabase.table("lancamentos").insert(payload_ofx).execute() 
                st.success("Transações mapeadas gravadas!") 
                st.cache_data.clear() 
def renderizar_demonstracoes(empresa_id, nome_empresa): 
    st.header("Demonstrações e Relatórios Contábeis Oficiais") 
    col1, col2 = st.columns(2) 
    d_ini = col1.date_input("Início", pd.to_datetime("2026-01-01"), format="DD/MM/YYYY") 
    d_fim = col2.date_input("Fim", pd.to_datetime("2026-12-31"), format="DD/MM/YYYY") 
    
    df_lanc = buscar_lancamentos(d_ini, d_fim, empresa_id) 
    df_plano = buscar_plano_contas(empresa_id) 
    df_balancete = processar_balancete_df(df_lanc, df_plano, d_fim) 
    
    components.html(""" 
 <button onclick="window.print()" style="background-color:#00ff66; color:#0b2216; padding:10px 20px; border:none; border-radius:5px; font-weight:bold; cursor:pointer; font-family: sans-serif; width: 100%;"> 
 🖨️ Imprimir / Salvar em PDF 
 </button> 
 """, height=50) 
    
    aba_rep1, aba_rep2, aba_rep3 = st.tabs(["Balancete por Níveis", "DRE Oficial Dedutiva", "Balanço Patrimonial Vertical"]) 
    
    with aba_rep1: 
        st.markdown(f'<div class="print-area"><h2>BALANCETE DE VERIFICAÇÃO</h2><p><b>Empresa:</b> {nome_empresa}</p><p><b>Período:</b> {d_ini.strftime("%d/%m/%Y")} - {d_fim.strftime("%d/%m/%Y")}</p><hr/></div>', unsafe_allow_html=True) 
        nivel_sel = st.slider("Filtrar por Nível Hierárquico", 1, 5, 5) 
        if not df_balancete.empty: 
            df_f = df_balancete[df_balancete['Nível'] <= nivel_sel] 
            st.dataframe(df_f[["Código", "Descrição", "Débito", "Crédito", "Saldo Atual"]], use_container_width=True, hide_index=True) 
            
    with aba_rep2: 
        st.subheader("Demonstração do Resultado do Exercício Estruturada") 
        if not df_balancete.empty: 
            def obter_saldo(prefixo): 
                filtro = df_balancete[df_balancete['Código'].str.startswith(prefixo) & (df_balancete['Nível'] == 1)] 
                return float(filtro['Saldo Atual'].values[0]) if not filtro.empty else 0.0 
                
            rec_bruta = obter_saldo("3") 
            deducoes = obter_saldo("3.2") 
            rec_liquida = rec_bruta - deducoes 
            custos = obter_saldo("5") if "5" in df_balancete['Código'].values else 0.0 
            lucro_bruto = rec_liquida - custos 
            despesas = obter_saldo("4") 
            lucro_liquido = lucro_bruto - despesas 
            
            st.markdown(f""" 

 | Linhas de Resultado Estruturadas (Lei 6.404/76) | Valor Acumulado (R$) | 
 | :--- | :--- | 
 | **(=) RECEITA OPERACIONAL BRUTA (Faturamento)** | **{rec_bruta:,.2f}** | 
 | (-) Deduções de Receita, Glosas e Impostos Diretos | ({deducoes:,.2f}) | 
 | **(=) RECEITA OPERACIONAL LÍQUIDA** | **{rec_liquida:,.2f}** | 
 | (-) Custos dos Serviços e Produtos Comercializados | ({custos:,.2f}) | 
 | **(=) RESULTADO BRUTO DO PERÍODO** | **{lucro_bruto:,.2f}** | 
 | (-) Despesas Administrativas, Gerais e Operacionais | ({despesas:,.2f}) | 
 | **(=) RESULTADO LÍQUIDO DO EXERCÍCIO (RLE)** | **{lucro_liquido:,.2f}** | 
 """) 
        else: 
            st.info("Sem movimentações de contas de resultado registrada no diário.") 
            
    with aba_rep3: 
        st.subheader("Balanço Patrimonial") 
        if not df_balancete.empty: 
            df_patrimonio = df_balancete[df_balancete['Tipo'].isin(['Ativo', 'Passivo', 'Patrimônio Líquido'])].copy() 
            st.dataframe(df_patrimonio[["Código", "Descrição", "Tipo", "Saldo Atual"]], use_container_width=True, hide_index=True) 
        else: 
            st.info("Aguardando consolidação de lançamentos patrimoniais.") 

def renderizar_modulo_cadastros(empresa_id): 
    st.header("Painel de Cadastros Estruturais") 
    aba_emp, aba_contas, aba_part, aba_acum, aba_hist, aba_ofx_regra = st.tabs([
        "Empresas", "Contas Contábeis", "Clientes/Fornecedores", 
        "Acumuladores Fiscais", "Históricos Padrão", "Mapeamento de Regras OFX"
    ]) 
    
    with aba_emp: 
        st.subheader("Carteira de Empresas Cliente") 
        df_e = buscar_empresas_contabilidade() 
        st.dataframe(df_e, use_container_width=True, hide_index=True) 
        with st.form("form_emp", clear_on_submit=True): 
            rz = st.text_input("Razão Social") 
            cn = st.text_input("CNPJ") 
            if st.form_submit_button("Salvar Empresa") and supabase: 
                supabase.table("empresas_clientes").insert({"razao_social": rz, "cnpj": cn}).execute() 
                st.success("Empresa cadastrada!") 
                st.cache_data.clear() 
                st.rerun() 
                
    with aba_contas: 
        st.subheader("Plano de Contas Vinculado") 
        df_p = buscar_plano_contas(empresa_id) 
        st.dataframe(df_p, use_container_width=True, hide_index=True) 
        with st.form("form_conta", clear_on_submit=True): 
            c_cod = st.text_input("Código") 
            c_des = st.text_input("Descrição") 
            c_tp = st.selectbox("Tipo", ["Ativo", "Passivo", "Patrimônio Líquido", "Receita", "Despesa"]) 
            if st.form_submit_button("Salvar Conta") and supabase: 
                supabase.table("plano_contas").insert({"codigo": c_cod, "descricao": c_des, "tipo": c_tp, "nivel": 5, "empresa_id": empresa_id}).execute() 
                st.success("Conta salva!") 
                st.cache_data.clear() 
                st.rerun() 

    with aba_part: 
        st.subheader("Clientes e Fornecedores") 
        df_pt = buscar_participantes(empresa_id) 
        st.dataframe(df_pt, use_container_width=True, hide_index=True) 
        with st.form("form_part", clear_on_submit=True): 
            p_nom = st.text_input("Nome") 
            p_doc = st.text_input("CPF/CNPJ") 
            p_tp = st.selectbox("Tipo", ["Fornecedor", "Cliente"]) 
            if st.form_submit_button("Salvar Participante") and supabase: 
                supabase.table("participantes").insert({"nome": p_nom, "documento": p_doc, "tipo": p_tp, "empresa_id": empresa_id}).execute() 
                st.success("Participante salvo!") 
                st.cache_data.clear() 
                st.rerun() 

    with aba_acum: 
        st.subheader("Acumuladores / Operações Fiscais") 
        df_ac = buscar_acumuladores(empresa_id) 
        st.dataframe(df_ac, use_container_width=True, hide_index=True) 
        with st.form("form_acum", clear_on_submit=True): 
            a_op = st.text_input("Nome da Operação") 
            a_al = st.number_input("Alíquota (%)", min_value=0.0) 
            if st.form_submit_button("Salvar Acumulador") and supabase: 
                supabase.table("acumuladores").insert({"operacao": a_op, "aliquota": a_al, "empresa_id": empresa_id}).execute() 
                st.success("Acumulador cadastrado!") 
                st.cache_data.clear() 
                st.rerun() 

    with aba_hist: 
        st.subheader("Históricos Contábeis Padrão") 
        df_hs = buscar_historicos(empresa_id) 
        st.dataframe(df_hs, use_container_width=True, hide_index=True) 
        with st.form("form_hist", clear_on_submit=True): 
            h_ds = st.text_input("Texto do Histórico") 
            if st.form_submit_button("Salvar Histórico") and supabase: 
                supabase.table("historicos_padrao").insert({"descricao": h_ds, "empresa_id": empresa_id}).execute() 
                st.success("Histórico salvo!") 
                st.cache_data.clear() 
                st.rerun() 

    with aba_ofx_regra: 
        st.subheader("Regras de Mapeamento Automatizado do OFX") 
        df_regras_visualizar = buscar_regras_ofx(empresa_id) 
        st.dataframe(df_regras_visualizar, use_container_width=True, hide_index=True) 
        with st.form("form_ofx_regra", clear_on_submit=True): 
            palavra_chave = st.text_input("Palavra-Chave do Extrato") 
            c_deb = st.text_input("Conta de Débito Padrão") 
            c_cred = st.text_input("Conta de Crédito Padrão") 
            if st.form_submit_button("Salvar Nova Regra OFX") and supabase: 
                supabase.table("regras_mapeamento_ofx").insert({"palavra_chave": palavra_chave, "conta_debito": c_deb, "conta_credito": c_cred, "empresa_id": empresa_id}).execute() 
                st.success("Regra de conciliação salva com sucesso!") 
                st.cache_data.clear() 
                st.rerun() 

def main(): 
    st.sidebar.markdown('<div class="logo-texto">&gt;&gt;&lt;&lt;</div>', unsafe_allow_html=True) 
    st.sidebar.title("Fluxo Assessoria") 
    st.sidebar.caption("Assessoria Empresarial de Alta Performance") 
    st.sidebar.markdown("---") 
    
    df_empresas = buscar_empresas_contabilidade() 
    lista_nomes = df_empresas['razao_social'].tolist() if not df_empresas.empty else ["Nenhuma cadastrada"] 
    emp_selecionada_nome = st.sidebar.selectbox(" Selecione o Cliente Contábil", options=lista_nomes) 
    
    if not df_empresas.empty and emp_selecionada_nome != "Nenhuma cadastrada": 
        id_filtrado = df_empresas[df_empresas['razao_social'] == emp_selecionada_nome]['id'].values 
        empresa_id_ativa = int(id_filtrado[0]) if len(id_filtrado) > 0 else 1 
    else: 
        empresa_id_ativa = 1 
        
    st.sidebar.markdown("---") 
    opcao_menu = st.sidebar.radio("Navegação", ["Escrituração Contábil", "Cadastros Estruturais", "Demonstrações Oficiais"]) 
    
    if st.sidebar.button("Encerrar Sessão / Logout"): 
        st.session_state['autenticado'] = False 
        st.rerun() 
        
    if opcao_menu == "Escrituração Contábil": 
        renderizar_modulo_lancamentos(empresa_id_ativa) 
    elif opcao_menu == "Cadastros Estruturais": 
        renderizar_modulo_cadastros(empresa_id_ativa) 
    elif opcao_menu == "Demonstrações Oficiais": 
        renderizar_demonstracoes(empresa_id_ativa, emp_selecionada_nome) 

if __name__ == "__main__": 
    main()
