import re
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

# ==============================================================================
# CREDENCIAIS — lidas de .streamlit/secrets.toml, NUNCA do código-fonte.
# ==============================================================================
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    USUARIO_CORRETO = st.secrets["auth"]["usuario"]
    SENHA_CORRETA = st.secrets["auth"]["senha"]
except Exception:
    st.error(
        "Configuração ausente. Crie o arquivo `.streamlit/secrets.toml` "
        "com as credenciais do Supabase e o login do sistema (veja o README.md)."
    )
    st.stop()


@st.cache_resource
def inicializar_supabase() -> Client:
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro de conexão com o Supabase: {e}")
        return None


supabase = inicializar_supabase()


def executar_insert(tabela: str, payload: dict, mensagem_sucesso: str) -> bool:
    """Grava um registro no Supabase e mostra um erro compreensível em vez de travar a tela."""
    if not supabase:
        st.error("Sem conexão com o banco de dados. Verifique as credenciais em secrets.toml.")
        return False
    try:
        supabase.table(tabela).insert(payload).execute()
        st.success(mensagem_sucesso)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Não foi possível salvar o registro: {e}")
        return False


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');
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
# CAMADA DE DADOS
# plano_contas, participantes, acumuladores, historicos e lancamentos são as
# tabelas REAIS já existentes no Supabase do Condomínio Hardman Praia Flat.
# empresas_clientes e regras_mapeamento_ofx são tabelas novas, criadas só para
# este app (veja setup_supabase.sql).
# ==============================================================================
@st.cache_data(ttl=5)
def buscar_empresas_contabilidade():
    empresas_padrao = [
        {"id": 1, "razao_social": "Condomínio Edifício Hardman Praia Flat", "cnpj": "02.960.693/0001-90"},
    ]
    if not supabase:
        return pd.DataFrame(empresas_padrao)
    try:
        resposta = supabase.table("empresas_clientes").select("id, razao_social, cnpj").execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(empresas_padrao)
    except Exception:
        return pd.DataFrame(empresas_padrao)


@st.cache_data(ttl=5)
def buscar_plano_contas():
    """codigo_reduzido é o número curto do dia a dia (ex: 10 = Caixa);
    codigo_estruturado é o código hierárquico completo (ex: 1.1.01.0001),
    que é o valor gravado em lancamentos.conta_debito/conta_credito."""
    dados_fallback = [
        {"codigo_reduzido": "1", "codigo": "1.1.01.0001", "descricao": "Caixa Geral", "tipo": "Ativo"},
        {"codigo_reduzido": "2", "codigo": "1.1.01.02.0001", "descricao": "Banco Conta Movimento", "tipo": "Ativo"},
        {"codigo_reduzido": "3", "codigo": "1.1.03.01.0001", "descricao": "Clientes Nacionais", "tipo": "Ativo"},
        {"codigo_reduzido": "4", "codigo": "2.1.02.01.0001", "descricao": "Fornecedores Nacionais", "tipo": "Passivo"},
        {"codigo_reduzido": "7", "codigo": "3.1.01.01.0001", "descricao": "Receita de Serviços", "tipo": "Receita"},
        {"codigo_reduzido": "9", "codigo": "4.1.02.01.0001", "descricao": "Despesa com Uso e Consumo", "tipo": "Despesa"},
    ]
    if not supabase:
        return pd.DataFrame(dados_fallback)
    try:
        resposta = supabase.table("plano_contas").select("codigo_reduzido, codigo_estruturado, nome, grupo").execute()
        if not resposta.data:
            return pd.DataFrame(dados_fallback)
        df = pd.DataFrame(resposta.data)
        return df.rename(columns={"codigo_estruturado": "codigo", "nome": "descricao", "grupo": "tipo"})
    except Exception:
        return pd.DataFrame(dados_fallback)


@st.cache_data(ttl=5)
def buscar_participantes():
    dados_part = [
        {"id": 1, "nome": "THALIA DOS SANTOS GUILHERME", "documento": "53.957.929", "tipo": "Fornecedor", "conta_contabil": ""},
    ]
    if not supabase:
        return pd.DataFrame(dados_part)
    try:
        resposta = supabase.table("participantes").select("id, nome, documento, tipo, conta_contabil").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_part)
    except Exception:
        return pd.DataFrame(dados_part)


@st.cache_data(ttl=5)
def buscar_acumuladores():
    dados_acum = [
        {"codigo": "1", "descricao": "Rateio de Condomínio Geral", "operacao": "Entrada", "conta_debito": "", "conta_credito": "", "historico_padrao": "", "aliquota_imposto": 0.0},
    ]
    if not supabase:
        return pd.DataFrame(dados_acum)
    try:
        resposta = supabase.table("acumuladores").select("codigo, descricao, operacao, conta_debito, conta_credito, historico_padrao, aliquota_imposto").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_acum)
    except Exception:
        return pd.DataFrame(dados_acum)


@st.cache_data(ttl=5)
def buscar_historicos():
    dados_hist = [{"codigo": "1", "descricao": "Arrecadação de cota condominial ordinária"}]
    if not supabase:
        return pd.DataFrame(dados_hist)
    try:
        resposta = supabase.table("historicos").select("codigo, descricao").execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(dados_hist)
    except Exception:
        return pd.DataFrame(dados_hist)


@st.cache_data(ttl=5)
def buscar_regras_ofx(empresa_id):
    regras_padrao = [
        {"palavra_chave": "TRF 4930", "conta_debito": "4.1.02.01.0001", "conta_credito": "1.1.01.02.0001"},
        {"palavra_chave": "PIX RECEB", "conta_debito": "1.1.01.02.0001", "conta_credito": "3.1.01.01.0001"}
    ]
    if not supabase:
        return pd.DataFrame(regras_padrao)
    try:
        resposta = supabase.table("regras_mapeamento_ofx").select("palavra_chave, conta_debito, conta_credito").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(regras_padrao)
    except Exception:
        return pd.DataFrame(regras_padrao)


@st.cache_data(ttl=2)
def buscar_lancamentos(data_inicio, data_fim, empresa_id):
    if not supabase:
        return pd.DataFrame(columns=["id", "data", "conta_debito", "conta_credito", "valor", "historico"])
    try:
        resposta = supabase.table("lancamentos").select("id, data, conta_debito, conta_credito, valor, historico")\
            .eq("empresa_id", empresa_id)\
            .gte("data", data_inicio.strftime('%Y-%m-%d'))\
            .lte("data", data_fim.strftime('%Y-%m-%d')).execute()
        return pd.DataFrame(resposta.data) if resposta.data else pd.DataFrame(columns=["id", "data", "conta_debito", "conta_credito", "valor", "historico"])
    except Exception:
        return pd.DataFrame(columns=["id", "data", "conta_debito", "conta_credito", "valor", "historico"])


def processar_balancete_df(df_lancamentos, df_plano, data_limite):
    """O plano de contas real só tem contas-folha (sem códigos-resumo pai), então o
    saldo de cada conta é só a soma direta dos lançamentos feitos exatamente nela."""
    if df_plano.empty:
        return pd.DataFrame(columns=["Código Reduzido", "Código Estruturado", "Descrição", "Tipo", "Débito", "Crédito", "Saldo Atual"])
    saldos = {row['codigo']: {'debito': 0.0, 'credito': 0.0} for _, row in df_plano.iterrows()}
    if not df_lancamentos.empty:
        df_filtrado = df_lancamentos[pd.to_datetime(df_lancamentos['data']) <= pd.to_datetime(data_limite)]
        for _, lanc in df_filtrado.iterrows():
            deb, cred, val = lanc['conta_debito'], lanc['conta_credito'], float(lanc['valor'])
            if deb in saldos:
                saldos[deb]['debito'] += val
            if cred in saldos:
                saldos[cred]['credito'] += val
    balancete_dados = []
    for _, conta in df_plano.iterrows():
        cod, tipo = conta['codigo'], conta['tipo']
        total_deb = saldos[cod]['debito']
        total_cred = saldos[cod]['credito']
        saldo_atual = (total_deb - total_cred) if tipo in ['Ativo', 'Despesa'] else (total_cred - total_deb)
        balancete_dados.append({
            "Código Reduzido": conta.get('codigo_reduzido', ''), "Código Estruturado": cod,
            "Descrição": conta['descricao'], "Tipo": tipo,
            "Débito": total_deb, "Crédito": total_cred, "Saldo Atual": saldo_atual
        })
    return pd.DataFrame(balancete_dados)


def processar_arquivo_ofx(conteudo: str):
    """Lê um arquivo OFX de verdade (os bancos usam SGML, não XML válido,
    por isso aqui a extração é feita por marcação de tag, não por parser de XML)."""
    transacoes = []
    blocos = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", conteudo, re.DOTALL | re.IGNORECASE)
    for bloco in blocos:
        data_m = re.search(r"<DTPOSTED>([^<\r\n]+)", bloco, re.IGNORECASE)
        valor_m = re.search(r"<TRNAMT>([^<\r\n]+)", bloco, re.IGNORECASE)
        texto_m = re.search(r"<MEMO>([^<\r\n]+)", bloco, re.IGNORECASE) or re.search(r"<NAME>([^<\r\n]+)", bloco, re.IGNORECASE)
        if not (data_m and valor_m):
            continue
        data_bruta = data_m.group(1).strip()[:8]
        if len(data_bruta) != 8 or not data_bruta.isdigit():
            continue
        data_formatada = f"{data_bruta[0:4]}-{data_bruta[4:6]}-{data_bruta[6:8]}"
        try:
            valor = float(valor_m.group(1).strip())
        except ValueError:
            continue
        documento = texto_m.group(1).strip() if texto_m else "Sem descrição"
        transacoes.append({"Data": data_formatada, "Documento": documento, "Valor": valor})
    return transacoes


def montar_mapa_contas(df_plano):
    """Monta {rótulo exibido: código_estruturado} para os seletores de conta."""
    mapa = {}
    for _, row in df_plano.iterrows():
        rotulo = f"{row.get('codigo_reduzido', '')} | {row['codigo']} - {row['descricao']}"
        mapa[rotulo] = row['codigo']
    return mapa


def renderizar_modulo_lancamentos(empresa_id):
    st.header("Entrada de Dados e Escrituração Contábil")
    df_plano = buscar_plano_contas()
    df_part = buscar_participantes()
    df_acum = buscar_acumuladores()
    df_hist = buscar_historicos()
    df_regras = buscar_regras_ofx(empresa_id)

    aba1, aba2, aba3 = st.tabs(["Lançamento Manual", "Importação de Notas Fiscais", "Conciliação OFX Real"])

    mapa_contas = montar_mapa_contas(df_plano)
    opcoes_contas = list(mapa_contas.keys())

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

            c_debito_sel = st.selectbox("Conta de Débito (Aplicação)", options=opcoes_contas if opcoes_contas else [""])
            c_credito_sel = st.selectbox("Conta de Crédito (Origem)", options=opcoes_contas if opcoes_contas else [""])

            if st.form_submit_button("Gravar Lançamento"):
                conta_debito_puro = mapa_contas.get(c_debito_sel, "")
                conta_credito_puro = mapa_contas.get(c_credito_sel, "")

                if not conta_debito_puro or not conta_credito_puro:
                    st.error("Selecione a conta de débito e a conta de crédito antes de gravar.")
                elif not historico_lan:
                    st.error("Informe um histórico para o lançamento.")
                else:
                    payload = {
                        "data": data_lan.strftime('%Y-%m-%d'),
                        "conta_debito": conta_debito_puro,
                        "conta_credito": conta_credito_puro,
                        "valor": valor_lan,
                        "historico": str(historico_lan),
                        "empresa_id": empresa_id
                    }
                    executar_insert("lancamentos", payload, "Lançamento gravado com sucesso!")

    with aba2:
        st.subheader("Escrituração Real de Notas Fiscais")
        with st.form("form_nota_fiscal", clear_on_submit=True):
            col_n1, col_n2 = st.columns(2)
            num_nota = col_n1.text_input("Número da NF-e / NFS-e")
            data_nota = col_n2.date_input("Data da Nota", format="DD/MM/YYYY")
            partic = st.selectbox("Participante Vinculado", options=df_part['nome'].tolist() if not df_part.empty else [""])
            lista_acum = [f"{row['codigo']} - {row['descricao']} ({row['operacao']})" for _, row in df_acum.iterrows()] if not df_acum.empty else [""]
            acum = st.selectbox("Operação / Acumulador", options=lista_acum)
            v_bruto = st.number_input("Valor Bruto da Nota (R$)", min_value=0.01)
            c_despesa_sel = st.selectbox("Conta de Contrapartida (Despesa/Estoque)", options=opcoes_contas if opcoes_contas else [""])
            c_origem_sel = st.selectbox("Conta Financiadora (Fornecedores/Caixa)", options=opcoes_contas if opcoes_contas else [""])

            if st.form_submit_button("Processar e Escriturar Nota"):
                c_desp_puro = mapa_contas.get(c_despesa_sel, "")
                c_orig_puro = mapa_contas.get(c_origem_sel, "")
                if not c_desp_puro or not c_orig_puro:
                    st.error("Selecione as duas contas contábeis da nota antes de processar.")
                else:
                    payload_nota = {
                        "data": data_nota.strftime('%Y-%m-%d'),
                        "conta_debito": c_desp_puro,
                        "conta_credito": c_orig_puro,
                        "valor": v_bruto,
                        "historico": f"Ref. NF-e Num {num_nota} - Part: {partic} - Op: {acum}",
                        "empresa_id": empresa_id
                    }
                    executar_insert("lancamentos", payload_nota, f"Nota Fiscal {num_nota} integrada ao diário contábil!")

    with aba3:
        st.subheader("Processador de Extratos Bancários OFX")
        arquivo_ofx = st.file_uploader("Selecione o arquivo .ofx", type=["ofx"])
        if arquivo_ofx is not None:
            conteudo_bytes = arquivo_ofx.read()
            try:
                conteudo = conteudo_bytes.decode("utf-8")
            except UnicodeDecodeError:
                conteudo = conteudo_bytes.decode("latin-1", errors="ignore")

            extrato_dados = processar_arquivo_ofx(conteudo)

            if not extrato_dados:
                st.warning("Não foi possível identificar transações neste arquivo. Confira se é um OFX válido exportado pelo banco.")
            else:
                analise_regras = []
                for item in extrato_dados:
                    deb, cred, status = "", "", "Sem Regra"
                    for _, r in df_regras.iterrows():
                        if r['palavra_chave'] in item['Documento']:
                            deb, cred, status = r['conta_debito'], r['conta_credito'], "Identificada"
                            break
                    analise_regras.append({"Data": item['Data'], "Documento": item['Documento'], "Valor": item['Valor'], "Débito": deb, "Crédito": cred, "Status": status})

                df_reconciliado = pd.DataFrame(analise_regras)
                st.dataframe(df_reconciliado, use_container_width=True, hide_index=True)
                if st.button("Confirmar Importação OFX no Diário"):
                    erros = 0
                    gravados = 0
                    for _, row in df_reconciliado.iterrows():
                        if "Identificada" in row['Status']:
                            payload_ofx = {
                                "data": row['Data'],
                                "conta_debito": str(row['Débito']).strip(),
                                "conta_credito": str(row['Crédito']).strip(),
                                "valor": float(row['Valor']),
                                "historico": f"OFX Auto: {row['Documento']}",
                                "empresa_id": empresa_id
                            }
                            if supabase:
                                try:
                                    supabase.table("lancamentos").insert(payload_ofx).execute()
                                    gravados += 1
                                except Exception as e:
                                    erros += 1
                                    st.error(f"Falha ao gravar '{row['Documento']}': {e}")
                    st.cache_data.clear()
                    if gravados:
                        st.success(f"{gravados} transação(ões) gravada(s) no diário.")
                    if erros == 0 and gravados == 0:
                        st.info("Nenhuma transação com regra identificada para importar.")


def renderizar_demonstracoes(empresa_id, nome_empresa):
    st.header("Demonstrações e Relatórios Contábeis Oficiais")
    col1, col2 = st.columns(2)
    d_ini = col1.date_input("Início", pd.to_datetime("2026-01-01"), format="DD/MM/YYYY")
    d_fim = col2.date_input("Fim", pd.to_datetime("2026-12-31"), format="DD/MM/YYYY")

    df_lanc = buscar_lancamentos(d_ini, d_fim, empresa_id)
    df_plano = buscar_plano_contas()
    df_balancete = processar_balancete_df(df_lanc, df_plano, d_fim)

    components.html("""
    <button onclick="window.print()" style="background-color:#00ff66; color:#0b2216; padding:10px 20px; border:none; border-radius:5px; font-weight:bold; cursor:pointer; font-family: sans-serif; width: 100%;">
    🖨️ Imprimir / Salvar em PDF
    </button>
    """, height=50)

    aba_rep1, aba_rep2, aba_rep3 = st.tabs(["Balancete", "DRE", "Balanço Patrimonial Vertical"])

    with aba_rep1:
        st.markdown(f'<div class="print-area"><h2>BALANCETE DE VERIFICAÇÃO</h2><p><b>Empresa:</b> {nome_empresa}</p><p><b>Período:</b> {d_ini.strftime("%d/%m/%Y")} - {d_fim.strftime("%d/%m/%Y")}</p><hr/></div>', unsafe_allow_html=True)
        if not df_balancete.empty:
            tipos_disponiveis = sorted(df_balancete['Tipo'].dropna().unique().tolist())
            tipos_sel = st.multiselect("Filtrar por Grupo", options=tipos_disponiveis, default=tipos_disponiveis)
            df_f = df_balancete[df_balancete['Tipo'].isin(tipos_sel)] if tipos_sel else df_balancete
            st.dataframe(df_f[["Código Reduzido", "Código Estruturado", "Descrição", "Tipo", "Débito", "Crédito", "Saldo Atual"]], use_container_width=True, hide_index=True)
        else:
            st.info("Sem contas cadastradas no plano de contas.")

    with aba_rep2:
        st.subheader("Demonstração do Resultado do Exercício")
        if not df_balancete.empty:
            def obter_total(tipo):
                return float(df_balancete[df_balancete['Tipo'] == tipo]['Saldo Atual'].sum())

            rec_total = obter_total("Receita")
            desp_total = obter_total("Despesa")
            resultado = rec_total - desp_total

            st.markdown(f"""
| Linha | Valor Acumulado (R$) |
| :--- | :--- |
| **(=) RECEITA TOTAL** | **{rec_total:,.2f}** |
| (-) DESPESAS TOTAIS | ({desp_total:,.2f}) |
| **(=) RESULTADO LÍQUIDO DO PERÍODO** | **{resultado:,.2f}** |
""")
            st.caption("DRE simplificada por grupo de conta. Linhas de deduções/custos podem ser adicionadas quando o plano de contas distinguir essas categorias.")
        else:
            st.info("Sem movimentações de contas de resultado registrada no diário.")

    with aba_rep3:
        st.subheader("Balanço Patrimonial")
        if not df_balancete.empty:
            df_patrimonio = df_balancete[df_balancete['Tipo'].isin(['Ativo', 'Passivo', 'Patrimônio Líquido'])].copy()
            st.dataframe(df_patrimonio[["Código Reduzido", "Código Estruturado", "Descrição", "Tipo", "Saldo Atual"]], use_container_width=True, hide_index=True)
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
            if st.form_submit_button("Salvar Empresa"):
                if executar_insert("empresas_clientes", {"razao_social": rz, "cnpj": cn}, "Empresa cadastrada!"):
                    st.rerun()

    with aba_contas:
        st.subheader("Plano de Contas (dados reais)")
        df_p = buscar_plano_contas()
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        with st.form("form_conta", clear_on_submit=True):
            c_red = st.text_input("Código Reduzido (ex: 10)")
            c_est = st.text_input("Código Estruturado (ex: 1.1.01.0005)")
            c_nome = st.text_input("Nome da Conta")
            c_grupo = st.selectbox("Grupo", ["Ativo", "Passivo", "Patrimônio Líquido", "Receita", "Despesa"])
            if st.form_submit_button("Salvar Conta"):
                if not c_red or not c_est or not c_nome:
                    st.error("Preencha código reduzido, código estruturado e nome.")
                else:
                    payload = {"codigo_reduzido": c_red, "codigo_estruturado": c_est, "nome": c_nome, "grupo": c_grupo}
                    if executar_insert("plano_contas", payload, "Conta salva!"):
                        st.rerun()

    with aba_part:
        st.subheader("Clientes e Fornecedores")
        df_pt = buscar_participantes()
        st.dataframe(df_pt, use_container_width=True, hide_index=True)
        df_plano_part = buscar_plano_contas()
        mapa_contas_part = {f"{row.get('codigo_reduzido', '')} - {row['descricao']}": row.get('codigo_reduzido', '') for _, row in df_plano_part.iterrows()}
        with st.form("form_part", clear_on_submit=True):
            p_nom = st.text_input("Nome")
            p_doc = st.text_input("CPF/CNPJ")
            p_tp = st.selectbox("Tipo", ["Fornecedor", "Cliente"])
            p_conta_sel = st.selectbox("Conta Contábil Vinculada", options=[""] + list(mapa_contas_part.keys()))
            if st.form_submit_button("Salvar Participante"):
                payload = {
                    "nome": p_nom, "documento": p_doc, "tipo": p_tp,
                    "conta_contabil": mapa_contas_part.get(p_conta_sel, "")
                }
                if executar_insert("participantes", payload, "Participante salvo!"):
                    st.rerun()

    with aba_acum:
        st.subheader("Acumuladores / Operações Fiscais")
        df_ac = buscar_acumuladores()
        st.dataframe(df_ac, use_container_width=True, hide_index=True)
        with st.form("form_acum", clear_on_submit=True):
            a_cod = st.text_input("Código")
            a_desc = st.text_input("Descrição")
            a_oper = st.selectbox("Operação", ["Entrada", "Saída"])
            a_cdeb = st.text_input("Conta de Débito Padrão (código estruturado ou referência)")
            a_ccred = st.text_input("Conta de Crédito Padrão (código estruturado ou referência)")
            a_hist = st.text_input("Histórico Padrão")
            a_aliq = st.number_input("Alíquota de Imposto (%)", min_value=0.0)
            if st.form_submit_button("Salvar Acumulador"):
                payload = {
                    "codigo": a_cod, "descricao": a_desc, "operacao": a_oper,
                    "conta_debito": a_cdeb, "conta_credito": a_ccred,
                    "historico_padrao": a_hist, "aliquota_imposto": a_aliq
                }
                if executar_insert("acumuladores", payload, "Acumulador cadastrado!"):
                    st.rerun()

    with aba_hist:
        st.subheader("Históricos Contábeis Padrão")
        df_hs = buscar_historicos()
        st.dataframe(df_hs, use_container_width=True, hide_index=True)
        with st.form("form_hist", clear_on_submit=True):
            h_cod = st.text_input("Código")
            h_ds = st.text_input("Texto do Histórico")
            if st.form_submit_button("Salvar Histórico"):
                if not h_cod or not h_ds:
                    st.error("Preencha código e texto do histórico.")
                else:
                    payload = {"codigo": h_cod, "descricao": h_ds}
                    if executar_insert("historicos", payload, "Histórico salvo!"):
                        st.rerun()

    with aba_ofx_regra:
        st.subheader("Regras de Mapeamento Automatizado do OFX")
        df_regras_visualizar = buscar_regras_ofx(empresa_id)
        st.dataframe(df_regras_visualizar, use_container_width=True, hide_index=True)
        with st.form("form_ofx_regra", clear_on_submit=True):
            palavra_chave = st.text_input("Palavra-Chave do Extrato")
            c_deb = st.text_input("Conta de Débito Padrão (código estruturado)")
            c_cred = st.text_input("Conta de Crédito Padrão (código estruturado)")
            if st.form_submit_button("Salvar Nova Regra OFX"):
                payload = {"palavra_chave": palavra_chave, "conta_debito": c_deb, "conta_credito": c_cred, "empresa_id": empresa_id}
                if executar_insert("regras_mapeamento_ofx", payload, "Regra de conciliação salva com sucesso!"):
                    st.rerun()


def main():
    st.sidebar.markdown('<div class="logo-texto">&gt;&gt;&lt;&lt;</div>', unsafe_allow_html=True)
    st.sidebar.title("Fluxo Assessoria")
    st.sidebar.caption("Assessoria Empresarial de Alta Performance")
    st.sidebar.markdown("---")

    df_empresas = buscar_empresas_contabilidade()
    lista_nomes = df_empresas['razao_social'].tolist() if not df_empresas.empty else ["Nenhuma cadastrada"]
    emp_selecionada_nome = st.sidebar.selectbox("Selecione o Cliente Contábil", options=lista_nomes)

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
