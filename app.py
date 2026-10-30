import re
import html as html_lib
from collections import defaultdict
from datetime import date, datetime

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

GRUPOS_CONTABEIS = ["Ativo", "Passivo", "Patrimônio Líquido", "Receita", "Despesa"]
NATUREZAS = ["Grupo", "Sintética", "Analítica"]


# ==============================================================================
# OPERAÇÕES DE ESCRITA (inserir / editar / excluir)
# ==============================================================================
def avisar(mensagem: str):
    """Guarda a mensagem para ser exibida após o st.rerun()."""
    st.session_state['_flash'] = mensagem


def executar_insert(tabela: str, payload: dict, mensagem_sucesso: str) -> bool:
    """Grava um registro no Supabase e mostra um erro compreensível em vez de travar a tela."""
    if not supabase:
        st.error("Sem conexão com o banco de dados. Verifique as credenciais em secrets.toml.")
        return False
    try:
        supabase.table(tabela).insert(payload).execute()
        avisar(mensagem_sucesso)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Não foi possível salvar o registro: {e}")
        return False


def executar_update(tabela: str, chave_col: str, chave_val, payload: dict, mensagem_sucesso: str) -> bool:
    if not supabase:
        st.error("Sem conexão com o banco de dados. Verifique as credenciais em secrets.toml.")
        return False
    try:
        supabase.table(tabela).update(payload).eq(chave_col, chave_val).execute()
        avisar(mensagem_sucesso)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Não foi possível atualizar o registro: {e}")
        return False


def executar_delete(tabela: str, chave_col: str, chave_val, mensagem_sucesso: str) -> bool:
    if not supabase:
        st.error("Sem conexão com o banco de dados. Verifique as credenciais em secrets.toml.")
        return False
    try:
        supabase.table(tabela).delete().eq(chave_col, chave_val).execute()
        avisar(mensagem_sucesso)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Não foi possível excluir o registro: {e}")
        return False


def contar_registros(tabela: str, filtro_or: str = None, **igual) -> int:
    """Conta registros (usado para impedir exclusões que deixariam lançamentos órfãos)."""
    if not supabase:
        return 0
    try:
        consulta = supabase.table(tabela).select("id", count="exact")
        for col, val in igual.items():
            consulta = consulta.eq(col, val)
        if filtro_or:
            consulta = consulta.or_(filtro_or)
        resposta = consulta.limit(1).execute()
        return int(resposta.count or 0)
    except Exception:
        return 0


# ==============================================================================
# ESTILO
# ==============================================================================
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
# FUNÇÕES DE APOIO — hierarquia do plano de contas
# ==============================================================================
def chave_ordenacao(codigo):
    """Ordenação natural: 1.1.1.01 vem antes de 1.1.1.10 e de 1.2."""
    return [(0, int(p), "") if p.isdigit() else (1, 0, p) for p in str(codigo).split(".")]


def nivel_da_conta(codigo) -> int:
    return str(codigo).count(".") + 1


def codigo_pai(codigo) -> str:
    partes = str(codigo).split(".")
    return ".".join(partes[:-1]) if len(partes) > 1 else ""


def ancestrais_e_propria(codigo):
    """Devolve a própria conta e todos os códigos acima dela (1.1.1.01.00001 -> 1.1.1.01, 1.1.1, 1.1, 1)."""
    partes = str(codigo).split(".")
    return [".".join(partes[:i]) for i in range(len(partes), 0, -1)]


def fmt_num(valor: float) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_saldo(valor: float) -> str:
    """Saldo no formato contábil: 94.429,52D / 1.200,00C."""
    valor = round(float(valor), 2)
    if valor == 0:
        return "0,00"
    return fmt_num(abs(valor)) + ("D" if valor > 0 else "C")


def derivar_natureza(df: pd.DataFrame) -> pd.Series:
    """Usa a coluna tipo_conta quando existir; senão deduz pela posição na hierarquia."""
    codigos = df['codigo'].astype(str).tolist()
    com_filhos = set()
    for c in codigos:
        partes = c.split(".")
        for i in range(1, len(partes)):
            com_filhos.add(".".join(partes[:i]))

    def definir(linha):
        valor = linha.get('natureza')
        if valor in NATUREZAS:
            return valor
        cod = str(linha['codigo'])
        if "." not in cod:
            return "Grupo"
        return "Sintética" if cod in com_filhos else "Analítica"

    return df.apply(definir, axis=1)


# ==============================================================================
# CAMADA DE DADOS
# ==============================================================================
@st.cache_data(ttl=5)
def buscar_empresas_contabilidade():
    empresas_padrao = [
        {"id": 1, "razao_social": "Condomínio Edifício Hardman Praia Flat", "cnpj": "02.960.693/0001-90"},
    ]
    if not supabase:
        return pd.DataFrame(empresas_padrao)
    try:
        resposta = supabase.table("empresas_clientes").select("id, razao_social, cnpj").order("razao_social").execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(empresas_padrao)
    except Exception:
        return pd.DataFrame(empresas_padrao)


@st.cache_data(ttl=5)
def buscar_plano_contas():
    """Colunas devolvidas:
    codigo_reduzido — número curto do dia a dia (ex: 10 = Caixa)
    codigo          — classificação estruturada (ex: 1.1.1.01.00001), valor gravado nos lançamentos
    descricao       — nome da conta
    tipo            — grupo contábil (Ativo, Passivo, Patrimônio Líquido, Receita, Despesa)
    natureza        — Grupo, Sintética ou Analítica (só contas Analíticas recebem lançamentos)
    """
    dados_fallback = [
        {"codigo_reduzido": "1", "codigo": "1", "descricao": "ATIVO", "tipo": "Ativo", "natureza": "Grupo"},
        {"codigo_reduzido": "2", "codigo": "1.1", "descricao": "ATIVO CIRCULANTE", "tipo": "Ativo", "natureza": "Sintética"},
        {"codigo_reduzido": "3", "codigo": "1.1.1", "descricao": "DISPONÍVEL", "tipo": "Ativo", "natureza": "Sintética"},
        {"codigo_reduzido": "5", "codigo": "1.1.1.01.00001", "descricao": "CAIXA GERAL", "tipo": "Ativo", "natureza": "Analítica"},
    ]
    colunas = ["codigo_reduzido", "codigo", "descricao", "tipo", "natureza", "tem_tipo_conta"]
    if not supabase:
        df = pd.DataFrame(dados_fallback)
        df["tem_tipo_conta"] = True
        return df
    try:
        resposta = supabase.table("plano_contas").select("*").execute()
        if not resposta.data:
            df = pd.DataFrame(dados_fallback)
            df["tem_tipo_conta"] = True
            return df
        bruto = pd.DataFrame(resposta.data)
        tem_tipo_conta = "tipo_conta" in bruto.columns
        df = bruto.rename(columns={"codigo_estruturado": "codigo", "nome": "descricao", "grupo": "tipo", "tipo_conta": "natureza"})
        if "natureza" not in df.columns:
            df["natureza"] = None
        if "codigo_reduzido" not in df.columns:
            df["codigo_reduzido"] = ""
        df["codigo"] = df["codigo"].astype(str)
        df["natureza"] = derivar_natureza(df)
        df["tem_tipo_conta"] = tem_tipo_conta
        df["_ord"] = df["codigo"].map(chave_ordenacao)
        df = df.sort_values("_ord").drop(columns="_ord").reset_index(drop=True)
        return df[colunas]
    except Exception:
        df = pd.DataFrame(dados_fallback)
        df["tem_tipo_conta"] = True
        return df


@st.cache_data(ttl=5)
def buscar_participantes():
    dados_part = [
        {"id": 1, "nome": "THALIA DOS SANTOS GUILHERME", "documento": "53.957.929", "tipo": "Fornecedor", "conta_contabil": ""},
    ]
    if not supabase:
        return pd.DataFrame(dados_part)
    try:
        resposta = supabase.table("participantes").select("id, nome, documento, tipo, conta_contabil").order("nome").execute()
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
        resposta = supabase.table("regras_mapeamento_ofx").select("id, palavra_chave, conta_debito, conta_credito").eq("empresa_id", empresa_id).execute()
        return pd.DataFrame(resposta.data) if (resposta.data and len(resposta.data) > 0) else pd.DataFrame(regras_padrao)
    except Exception:
        return pd.DataFrame(regras_padrao)


COLUNAS_LANCAMENTO = ["id", "data", "conta_debito", "conta_credito", "valor", "historico"]


@st.cache_data(ttl=2)
def buscar_lancamentos(data_inicio, data_fim, empresa_id):
    """Busca paginada: o Supabase devolve no máximo 1000 linhas por consulta."""
    if not supabase:
        return pd.DataFrame(columns=COLUNAS_LANCAMENTO)
    try:
        linhas, passo, inicio = [], 1000, 0
        while True:
            resposta = supabase.table("lancamentos").select("id, data, conta_debito, conta_credito, valor, historico")\
                .eq("empresa_id", empresa_id)\
                .gte("data", data_inicio.strftime('%Y-%m-%d'))\
                .lte("data", data_fim.strftime('%Y-%m-%d'))\
                .order("data").order("id")\
                .range(inicio, inicio + passo - 1).execute()
            lote = resposta.data or []
            linhas.extend(lote)
            if len(lote) < passo:
                break
            inicio += passo
        return pd.DataFrame(linhas) if linhas else pd.DataFrame(columns=COLUNAS_LANCAMENTO)
    except Exception:
        return pd.DataFrame(columns=COLUNAS_LANCAMENTO)


# ==============================================================================
# BALANCETE HIERÁRQUICO (Grupo > Sintética > Analítica)
# ==============================================================================
def processar_balancete_df(df_lancamentos, df_plano, data_ini, data_fim):
    """Os lançamentos só ocorrem em contas analíticas; os saldos de cada conta
    sintética e de cada grupo são a soma das contas que estão abaixo dela.
    Valores de saldo ficam em sinal contábil: positivo = Devedor, negativo = Credor."""
    colunas = ["Código Reduzido", "Classificação", "Descrição", "Tipo", "Natureza", "Nível",
               "Saldo Anterior", "Débito", "Crédito", "Saldo Atual"]
    if df_plano.empty:
        return pd.DataFrame(columns=colunas)

    codigos_validos = set(df_plano['codigo'])
    deb_ant, cred_ant = defaultdict(float), defaultdict(float)
    deb_per, cred_per = defaultdict(float), defaultdict(float)

    if not df_lancamentos.empty:
        ini, fim = pd.to_datetime(data_ini), pd.to_datetime(data_fim)
        datas = pd.to_datetime(df_lancamentos['data'])
        for dt, deb, cred, val in zip(datas, df_lancamentos['conta_debito'], df_lancamentos['conta_credito'], df_lancamentos['valor']):
            if dt > fim:
                continue
            anterior = dt < ini
            val = float(val)
            for conta, destino_ant, destino_per in ((str(deb), deb_ant, deb_per), (str(cred), cred_ant, cred_per)):
                if conta not in codigos_validos:
                    continue
                destino = destino_ant if anterior else destino_per
                for cod in ancestrais_e_propria(conta):
                    if cod in codigos_validos:
                        destino[cod] += val

    linhas = []
    for _, conta in df_plano.iterrows():
        cod = conta['codigo']
        saldo_ant = deb_ant[cod] - cred_ant[cod]
        deb, cred = deb_per[cod], cred_per[cod]
        linhas.append({
            "Código Reduzido": conta.get('codigo_reduzido', ''), "Classificação": cod,
            "Descrição": conta['descricao'], "Tipo": conta['tipo'], "Natureza": conta['natureza'],
            "Nível": nivel_da_conta(cod),
            "Saldo Anterior": saldo_ant, "Débito": deb, "Crédito": cred,
            "Saldo Atual": saldo_ant + deb - cred
        })
    return pd.DataFrame(linhas, columns=colunas)


def gerar_html_balancete(df, nome_empresa, cnpj, d_ini, d_fim):
    esc = html_lib.escape
    agora = datetime.now()
    linhas = []
    for _, r in df.iterrows():
        negrito = "font-weight:700;" if r['Natureza'] != "Analítica" else ""
        recuo = (int(r['Nível']) - 1) * 14
        topo = "border-top:1px solid #ccc;" if r['Natureza'] == "Grupo" else ""
        linhas.append(
            f"<tr style='{negrito}{topo}'>"
            f"<td class='c'>{esc(str(r['Código Reduzido']))}</td>"
            f"<td>{esc(str(r['Classificação']))}</td>"
            f"<td style='padding-left:{recuo + 4}px'>{esc(str(r['Descrição']))}</td>"
            f"<td class='n'>{fmt_saldo(r['Saldo Anterior'])}</td>"
            f"<td class='n'>{fmt_num(r['Débito'])}</td>"
            f"<td class='n'>{fmt_num(r['Crédito'])}</td>"
            f"<td class='n'>{fmt_saldo(r['Saldo Atual'])}</td></tr>"
        )
    return f"""
<html><head><meta charset="utf-8"><style>
body {{ font-family: Arial, sans-serif; font-size: 12px; color: #000; margin: 8px; }}
.cab {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
.cab td {{ padding: 1px 6px 1px 0; }}
h3 {{ text-align: center; margin: 14px 0 8px 0; }}
table.bal {{ width: 100%; border-collapse: collapse; }}
table.bal th {{ border-top: 2px solid #000; border-bottom: 2px solid #000; text-align: left; padding: 4px; }}
table.bal th.n, td.n {{ text-align: right; white-space: nowrap; }}
table.bal td {{ padding: 2px 4px; }}
td.c {{ text-align: right; padding-right: 10px; }}
button {{ background:#00ff66; color:#0b2216; padding:10px 20px; border:none; border-radius:5px; font-weight:bold; cursor:pointer; width:100%; margin-bottom:10px; }}
@media print {{ button {{ display: none; }} }}
</style></head><body>
<button onclick="window.print()">🖨️ Imprimir / Salvar em PDF</button>
<div class="cab">
  <table>
    <tr><td><b>Empresa:</b></td><td><b>{esc(nome_empresa)}</b></td></tr>
    <tr><td>C.N.P.J.:</td><td>{esc(str(cnpj or ''))}</td></tr>
    <tr><td>Período:</td><td>{d_ini.strftime('%d/%m/%Y')} - {d_fim.strftime('%d/%m/%Y')}</td></tr>
  </table>
  <table>
    <tr><td>Emissão:</td><td>{agora.strftime('%d/%m/%Y')}</td></tr>
    <tr><td>Hora:</td><td>{agora.strftime('%H:%M:%S')}</td></tr>
  </table>
</div>
<h3>BALANCETE</h3>
<table class="bal">
<thead><tr><th class="n">Código</th><th>Classificação</th><th>Descrição da conta</th>
<th class="n">Saldo Anterior</th><th class="n">Débito</th><th class="n">Crédito</th><th class="n">Saldo Atual</th></tr></thead>
<tbody>{''.join(linhas)}</tbody></table>
</body></html>"""


# ==============================================================================
# OFX
# ==============================================================================
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


def montar_mapa_contas(df_plano, somente_analiticas=True):
    """Monta {rótulo exibido: código_estruturado} para os seletores de conta.
    Por padrão só entram contas analíticas, que são as únicas que recebem lançamento."""
    base = df_plano[df_plano['natureza'] == "Analítica"] if somente_analiticas else df_plano
    mapa = {}
    for _, row in base.iterrows():
        rotulo = f"{row.get('codigo_reduzido', '')} | {row['codigo']} - {row['descricao']}"
        mapa[rotulo] = row['codigo']
    return mapa


# ==============================================================================
# PAINEL GENÉRICO DE EDIÇÃO / EXCLUSÃO
# ==============================================================================
def _py(valor):
    return valor.item() if hasattr(valor, "item") else valor


def _vazio(valor) -> bool:
    return valor is None or (isinstance(valor, float) and pd.isna(valor))


def painel_editar_excluir(tabela, df, chave_col, rotulo_fn, campos, key,
                          obrigatorios=(), bloquear_exclusao=None):
    """Seleciona um registro existente, permite editar os campos e excluir.

    campos: lista de dicts {col, label, tipo: text|number|date|select, opcoes, formato, disabled, min}
    bloquear_exclusao: função(row) -> mensagem de impedimento ou None
    """
    st.markdown("##### ✏️ Editar ou excluir um cadastro existente")
    if df.empty or chave_col not in df.columns:
        st.caption("Nenhum cadastro disponível para edição.")
        return

    registros = {rotulo_fn(r): r for _, r in df.iterrows()}
    escolha = st.selectbox("Selecione o cadastro", options=[""] + list(registros.keys()), key=f"{key}_sel")
    if not escolha:
        return

    row = registros[escolha]
    chave_val = _py(row[chave_col])

    with st.form(f"{key}_form_{chave_val}"):
        novos = {}
        for c in campos:
            col, rotulo = c['col'], c['label']
            atual = row.get(col)
            k = f"{key}_{col}_{chave_val}"
            tipo = c.get('tipo', 'text')
            if c.get('disabled'):
                st.text_input(rotulo, value="" if _vazio(atual) else str(atual), disabled=True, key=k)
            elif tipo == 'text':
                novos[col] = st.text_input(rotulo, value="" if _vazio(atual) else str(atual), key=k)
            elif tipo == 'number':
                novos[col] = st.number_input(rotulo, value=0.0 if _vazio(atual) else float(atual),
                                             min_value=c.get('min', 0.0), step=0.01, key=k)
            elif tipo == 'date':
                novos[col] = st.date_input(rotulo, value=pd.to_datetime(atual).date(), format="DD/MM/YYYY", key=k)
            elif tipo == 'select':
                opcoes = list(c['opcoes'])
                atual_txt = "" if _vazio(atual) else atual
                if atual_txt not in opcoes:
                    opcoes.append(atual_txt)
                novos[col] = st.selectbox(rotulo, options=opcoes, index=opcoes.index(atual_txt),
                                          format_func=c.get('formato', str), key=k)
        salvar = st.form_submit_button("💾 Salvar alterações")

    if salvar:
        faltando = [c['label'] for c in campos if c['col'] in obrigatorios and not str(novos.get(c['col'], "")).strip()]
        if faltando:
            st.error("Preencha: " + ", ".join(faltando))
        else:
            payload = {}
            for col, val in novos.items():
                if isinstance(val, (date, datetime)):
                    val = val.strftime('%Y-%m-%d')
                payload[col] = val.strip() if isinstance(val, str) else val
            if executar_update(tabela, chave_col, chave_val, payload, "Cadastro atualizado com sucesso!"):
                st.rerun()

    st.markdown("**Excluir este cadastro**")
    impedimento = bloquear_exclusao(row) if bloquear_exclusao else None
    if impedimento:
        st.warning(impedimento)
    else:
        confirmar = st.checkbox("Confirmo que desejo excluir este cadastro (não pode ser desfeito)", key=f"{key}_conf_{chave_val}")
        if st.button("🗑️ Excluir", key=f"{key}_del_{chave_val}", disabled=not confirmar):
            if executar_delete(tabela, chave_col, chave_val, "Cadastro excluído com sucesso!"):
                st.rerun()


# ==============================================================================
# MÓDULO: ESCRITURAÇÃO
# ==============================================================================
def renderizar_modulo_lancamentos(empresa_id):
    st.header("Entrada de Dados e Escrituração Contábil")
    df_plano = buscar_plano_contas()
    df_part = buscar_participantes()
    df_acum = buscar_acumuladores()
    df_hist = buscar_historicos()
    df_regras = buscar_regras_ofx(empresa_id)

    aba1, aba2, aba3, aba4 = st.tabs([
        "Lançamento Manual", "Importação de Notas Fiscais", "Conciliação OFX Real", "Editar / Excluir Lançamentos"
    ])

    mapa_contas = montar_mapa_contas(df_plano)
    opcoes_contas = list(mapa_contas.keys())

    with aba1:
        st.subheader("Lançamento Partida Dobrada (Diário)")
        st.caption("Somente contas analíticas aparecem na lista — contas sintéticas e grupos apenas totalizam.")
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
                    if executar_insert("lancamentos", payload, "Lançamento gravado com sucesso!"):
                        st.rerun()

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
                    if executar_insert("lancamentos", payload_nota, f"Nota Fiscal {num_nota} integrada ao diário contábil!"):
                        st.rerun()

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
                                "valor": abs(float(row['Valor'])),
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

    with aba4:
        st.subheader("Editar ou Excluir Lançamentos já feitos")
        c1, c2 = st.columns(2)
        e_ini = c1.date_input("De", date(date.today().year, 1, 1), format="DD/MM/YYYY", key="edit_lanc_ini")
        e_fim = c2.date_input("Até", date.today(), format="DD/MM/YYYY", key="edit_lanc_fim")
        df_l = buscar_lancamentos(e_ini, e_fim, empresa_id)
        if df_l.empty:
            st.info("Nenhum lançamento no período selecionado.")
        else:
            st.dataframe(df_l, use_container_width=True, hide_index=True)
            mapa_inverso = {v: k for k, v in montar_mapa_contas(df_plano, somente_analiticas=False).items()}
            todas_contas = list(mapa_inverso.keys())
            painel_editar_excluir(
                "lancamentos", df_l, "id",
                lambda r: f"#{r['id']} | {pd.to_datetime(r['data']).strftime('%d/%m/%Y')} | R$ {fmt_num(float(r['valor']))} | {str(r['historico'])[:50]}",
                [
                    {"col": "data", "label": "Data", "tipo": "date"},
                    {"col": "valor", "label": "Valor (R$)", "tipo": "number", "min": 0.01},
                    {"col": "conta_debito", "label": "Conta de Débito", "tipo": "select", "opcoes": todas_contas,
                     "formato": lambda v: mapa_inverso.get(v, v)},
                    {"col": "conta_credito", "label": "Conta de Crédito", "tipo": "select", "opcoes": todas_contas,
                     "formato": lambda v: mapa_inverso.get(v, v)},
                    {"col": "historico", "label": "Histórico", "tipo": "text"},
                ],
                key="ed_lanc", obrigatorios=("historico",)
            )


# ==============================================================================
# MÓDULO: DEMONSTRAÇÕES
# ==============================================================================
def renderizar_demonstracoes(empresa_id, nome_empresa, cnpj):
    st.header("Demonstrações e Relatórios Contábeis Oficiais")
    col1, col2 = st.columns(2)
    d_ini = col1.date_input("Início", pd.to_datetime("2026-01-01"), format="DD/MM/YYYY")
    d_fim = col2.date_input("Fim", pd.to_datetime("2026-12-31"), format="DD/MM/YYYY")

    # O saldo anterior precisa de todos os lançamentos desde o início da escrituração.
    df_lanc = buscar_lancamentos(date(2000, 1, 1), d_fim, empresa_id)
    df_plano = buscar_plano_contas()
    df_balancete = processar_balancete_df(df_lanc, df_plano, d_ini, d_fim)

    aba_rep1, aba_rep2, aba_rep3 = st.tabs(["Balancete", "DRE", "Balanço Patrimonial Vertical"])

    with aba_rep1:
        if df_balancete.empty:
            st.info("Sem contas cadastradas no plano de contas.")
        else:
            f1, f2, f3 = st.columns([2, 2, 2])
            tipos_disponiveis = sorted(df_balancete['Tipo'].dropna().unique().tolist())
            tipos_sel = f1.multiselect("Filtrar por Grupo", options=tipos_disponiveis, default=tipos_disponiveis)
            naturezas_sel = f2.multiselect("Mostrar contas", options=NATUREZAS, default=NATUREZAS)
            ocultar_zeradas = f3.checkbox("Ocultar contas sem saldo e sem movimento", value=True)

            df_f = df_balancete[df_balancete['Tipo'].isin(tipos_sel) & df_balancete['Natureza'].isin(naturezas_sel)]
            if ocultar_zeradas:
                sem_valor = (df_f[["Saldo Anterior", "Débito", "Crédito", "Saldo Atual"]].abs().sum(axis=1) == 0)
                df_f = df_f[~sem_valor]
            components.html(gerar_html_balancete(df_f, nome_empresa, cnpj, d_ini, d_fim), height=750, scrolling=True)

    with aba_rep2:
        st.subheader("Demonstração do Resultado do Exercício")
        resultado_df = df_balancete[df_balancete['Tipo'].isin(['Receita', 'Despesa'])].copy() if not df_balancete.empty else pd.DataFrame()
        if resultado_df.empty:
            st.info("Sem contas de resultado cadastradas.")
        else:
            # Receita tem natureza credora; despesa, devedora. Usa apenas o movimento do período.
            resultado_df["Valor do Período"] = resultado_df.apply(
                lambda r: (r['Crédito'] - r['Débito']) if r['Tipo'] == "Receita" else (r['Débito'] - r['Crédito']), axis=1)
            analiticas = resultado_df[resultado_df['Natureza'] == "Analítica"]
            rec_total = float(analiticas[analiticas['Tipo'] == "Receita"]['Valor do Período'].sum())
            desp_total = float(analiticas[analiticas['Tipo'] == "Despesa"]['Valor do Período'].sum())
            resultado = rec_total - desp_total

            st.markdown(f"""
| Linha | Valor no Período (R$) |
| :--- | :--- |
| **(=) RECEITA TOTAL** | **{fmt_num(rec_total)}** |
| (-) DESPESAS TOTAIS | ({fmt_num(desp_total)}) |
| **(=) RESULTADO LÍQUIDO DO PERÍODO** | **{fmt_num(resultado)}** |
""")
            detalhe = resultado_df[resultado_df['Valor do Período'] != 0].copy()
            if not detalhe.empty:
                detalhe["Descrição"] = detalhe.apply(lambda r: "   " * (int(r['Nível']) - 1) + r['Descrição'], axis=1)
                detalhe["Valor do Período"] = detalhe["Valor do Período"].map(fmt_num)
                st.dataframe(detalhe[["Classificação", "Descrição", "Tipo", "Valor do Período"]], use_container_width=True, hide_index=True)

    with aba_rep3:
        st.subheader("Balanço Patrimonial")
        if df_balancete.empty:
            st.info("Aguardando consolidação de lançamentos patrimoniais.")
        else:
            df_pat = df_balancete[df_balancete['Tipo'].isin(['Ativo', 'Passivo', 'Patrimônio Líquido'])].copy()
            df_pat = df_pat[df_pat['Saldo Atual'].abs() > 0]
            if df_pat.empty:
                st.info("Sem saldos patrimoniais no período.")
            else:
                analiticas = df_pat[df_pat['Natureza'] == "Analítica"]
                total_ativo = float(analiticas[analiticas['Tipo'] == "Ativo"]['Saldo Atual'].sum())
                total_passivo_pl = -float(analiticas[analiticas['Tipo'] != "Ativo"]['Saldo Atual'].sum())
                m1, m2 = st.columns(2)
                m1.metric("Total do Ativo", f"R$ {fmt_num(total_ativo)}")
                m2.metric("Total do Passivo + PL", f"R$ {fmt_num(total_passivo_pl)}")
                df_pat["Descrição"] = df_pat.apply(lambda r: "   " * (int(r['Nível']) - 1) + r['Descrição'], axis=1)
                df_pat["Saldo Atual"] = df_pat["Saldo Atual"].map(fmt_saldo)
                st.dataframe(df_pat[["Código Reduzido", "Classificação", "Descrição", "Tipo", "Saldo Atual"]], use_container_width=True, hide_index=True)


# ==============================================================================
# MÓDULO: CADASTROS
# ==============================================================================
def proximo_codigo_filho(df_plano, pai, natureza):
    """Sugere o próximo código livre dentro de um pai (ex.: pai 1.1.1 com filho 1.1.1.01 -> 1.1.1.02)."""
    prefixo = f"{pai}." if pai else ""
    irmaos = [str(c)[len(prefixo):] for c in df_plano['codigo']
              if str(c).startswith(prefixo) and "." not in str(c)[len(prefixo):]]
    numeros = [int(s) for s in irmaos if s.isdigit()]
    proximo = (max(numeros) + 1) if numeros else 1
    if irmaos:
        largura = max(len(s) for s in irmaos)
    else:
        profundidade = (pai.count(".") + 2) if pai else 1
        largura = 5 if natureza == "Analítica" else (2 if profundidade == 4 else 1)
    return f"{prefixo}{str(proximo).zfill(largura)}"


def proximo_reduzido(df_plano):
    numeros = [int(x) for x in df_plano['codigo_reduzido'].astype(str) if x.strip().isdigit()]
    return str(max(numeros) + 1) if numeros else "1"


def renderizar_contas_contabeis():
    st.subheader("Plano de Contas — Grupos, Sintéticas e Analíticas")
    df_p = buscar_plano_contas()

    if not df_p.empty and not bool(df_p['tem_tipo_conta'].iloc[0]):
        st.warning(
            "A tabela `plano_contas` ainda não tem a coluna `tipo_conta`. Execute o script "
            "`migracao_plano_contas.sql` no SQL Editor do Supabase antes de cadastrar novas contas."
        )

    exibir = df_p.copy()
    exibir["descricao"] = exibir.apply(lambda r: "   " * (nivel_da_conta(r['codigo']) - 1) + str(r['descricao']), axis=1)
    st.dataframe(
        exibir[["codigo_reduzido", "codigo", "descricao", "natureza", "tipo"]].rename(columns={
            "codigo_reduzido": "Código", "codigo": "Classificação", "descricao": "Descrição da conta",
            "natureza": "Natureza", "tipo": "Grupo contábil"}),
        use_container_width=True, hide_index=True
    )

    sub_nova, sub_edit = st.tabs(["➕ Nova conta", "✏️ Editar / Excluir conta"])

    with sub_nova:
        seq = st.session_state.get('nc_seq', 0)
        nivel = st.radio("O que você vai cadastrar?", NATUREZAS, horizontal=True, key=f"nc_nivel_{seq}",
                         help="Grupo = nível 1 (ex.: 1 ATIVO). Sintética = totalizadora (ex.: 1.1.1 DISPONÍVEL). "
                              "Analítica = recebe lançamentos (ex.: 1.1.1.01.00001 CAIXA GERAL).")

        pai_codigo, grupo_contabil = "", None
        if nivel == "Grupo":
            grupo_contabil = st.selectbox("Grupo contábil", GRUPOS_CONTABEIS, key=f"nc_grupo_{seq}")
        else:
            pais = df_p[df_p['natureza'].isin(["Grupo", "Sintética"])]
            mapa_pais = {f"{r['codigo']} - {r['descricao']}": r['codigo'] for _, r in pais.iterrows()}
            if not mapa_pais:
                st.info("Cadastre primeiro um Grupo (ex.: 1 - ATIVO) para poder criar contas dentro dele.")
            pai_sel = st.selectbox("Dentro de qual grupo / conta sintética a nova conta será criada?",
                                   options=list(mapa_pais.keys()), key=f"nc_pai_{seq}") if mapa_pais else None
            if pai_sel:
                pai_codigo = mapa_pais[pai_sel]
                grupo_contabil = df_p[df_p['codigo'] == pai_codigo]['tipo'].iloc[0]
                st.caption(f"Grupo contábil herdado: **{grupo_contabil}**")

        pode_cadastrar = nivel == "Grupo" or bool(pai_codigo)
        if pode_cadastrar:
            sugestao = proximo_codigo_filho(df_p, pai_codigo, nivel)
            chave = f"{seq}_{nivel}_{pai_codigo}"
            n_cod = st.text_input("Classificação (código estruturado)", value=sugestao, key=f"nc_cod_{chave}")
            n_red = st.text_input("Código reduzido", value=proximo_reduzido(df_p), key=f"nc_red_{chave}")
            n_nome = st.text_input("Nome da conta", key=f"nc_nome_{chave}")

            if st.button("Salvar Conta", key=f"nc_salvar_{chave}"):
                n_cod, n_red, n_nome = n_cod.strip(), n_red.strip(), n_nome.strip()
                codigos_existentes = set(df_p['codigo'].astype(str))
                reduzidos_existentes = set(df_p['codigo_reduzido'].astype(str))
                if not n_cod or not n_nome or not n_red:
                    st.error("Preencha classificação, código reduzido e nome.")
                elif not re.fullmatch(r"\d+(\.\d+)*", n_cod):
                    st.error("A classificação deve conter apenas números separados por ponto (ex.: 1.1.1.01).")
                elif n_cod in codigos_existentes:
                    st.error(f"Já existe uma conta com a classificação {n_cod}.")
                elif n_red in reduzidos_existentes:
                    st.error(f"Já existe uma conta com o código reduzido {n_red}.")
                elif nivel == "Grupo" and "." in n_cod:
                    st.error("Um Grupo é de nível 1 e não pode ter ponto na classificação (ex.: 1, 2, 3).")
                elif nivel != "Grupo" and codigo_pai(n_cod) != pai_codigo:
                    st.error(f"A classificação deve ficar imediatamente abaixo de {pai_codigo} (ex.: {sugestao}).")
                else:
                    payload = {"codigo_reduzido": n_red, "codigo_estruturado": n_cod, "nome": n_nome,
                               "grupo": grupo_contabil, "tipo_conta": nivel}
                    if executar_insert("plano_contas", payload, f"Conta {n_cod} - {n_nome} salva!"):
                        st.session_state['nc_seq'] = seq + 1
                        st.rerun()

    with sub_edit:
        df_edit = df_p.rename(columns={"codigo": "codigo_estruturado", "descricao": "nome", "tipo": "grupo", "natureza": "tipo_conta"})

        def impedir_exclusao(row):
            cod = str(row['codigo_estruturado'])
            if any(str(c).startswith(cod + ".") for c in df_p['codigo']):
                return "Esta conta possui contas abaixo dela. Exclua ou mova as contas filhas primeiro."
            usos = contar_registros("lancamentos", filtro_or=f"conta_debito.eq.{cod},conta_credito.eq.{cod}")
            if usos:
                return f"Esta conta possui {usos} lançamento(s). Edite ou exclua os lançamentos antes de excluir a conta."
            return None

        painel_editar_excluir(
            "plano_contas", df_edit, "codigo_estruturado",
            lambda r: f"{r['codigo_estruturado']} - {r['nome']} ({r['tipo_conta']})",
            [
                {"col": "codigo_estruturado", "label": "Classificação (não editável)", "disabled": True},
                {"col": "tipo_conta", "label": "Natureza (não editável)", "disabled": True},
                {"col": "codigo_reduzido", "label": "Código reduzido"},
                {"col": "nome", "label": "Nome da conta"},
                {"col": "grupo", "label": "Grupo contábil", "tipo": "select", "opcoes": GRUPOS_CONTABEIS},
            ],
            key="ed_conta", obrigatorios=("codigo_reduzido", "nome"), bloquear_exclusao=impedir_exclusao
        )
        st.caption("A classificação não pode ser alterada porque os lançamentos usam esse código. "
                   "Para mudar uma conta de lugar, crie uma nova no grupo correto e transfira os lançamentos.")


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
                if not rz.strip():
                    st.error("Informe a razão social.")
                elif executar_insert("empresas_clientes", {"razao_social": rz.strip(), "cnpj": cn.strip()}, "Empresa cadastrada!"):
                    st.rerun()
        painel_editar_excluir(
            "empresas_clientes", df_e, "id",
            lambda r: f"{r['razao_social']} ({r.get('cnpj', '')})",
            [{"col": "razao_social", "label": "Razão Social"}, {"col": "cnpj", "label": "CNPJ"}],
            key="ed_emp", obrigatorios=("razao_social",),
            bloquear_exclusao=lambda r: (
                "Esta empresa possui lançamentos. Exclua os lançamentos antes de excluir a empresa."
                if contar_registros("lancamentos", empresa_id=_py(r['id'])) else None)
        )

    with aba_contas:
        renderizar_contas_contabeis()

    with aba_part:
        st.subheader("Clientes e Fornecedores")
        df_pt = buscar_participantes()
        st.dataframe(df_pt, use_container_width=True, hide_index=True)
        df_plano_part = buscar_plano_contas()
        df_plano_part = df_plano_part[df_plano_part['natureza'] == "Analítica"]
        mapa_contas_part = {f"{row.get('codigo_reduzido', '')} - {row['descricao']}": row.get('codigo_reduzido', '') for _, row in df_plano_part.iterrows()}
        rotulo_conta = {v: k for k, v in mapa_contas_part.items()}
        rotulo_conta[""] = "(sem conta vinculada)"
        with st.form("form_part", clear_on_submit=True):
            p_nom = st.text_input("Nome")
            p_doc = st.text_input("CPF/CNPJ")
            p_tp = st.selectbox("Tipo", ["Fornecedor", "Cliente"])
            p_conta_sel = st.selectbox("Conta Contábil Vinculada", options=[""] + list(mapa_contas_part.keys()))
            if st.form_submit_button("Salvar Participante"):
                if not p_nom.strip():
                    st.error("Informe o nome.")
                else:
                    payload = {
                        "nome": p_nom.strip(), "documento": p_doc.strip(), "tipo": p_tp,
                        "conta_contabil": mapa_contas_part.get(p_conta_sel, "")
                    }
                    if executar_insert("participantes", payload, "Participante salvo!"):
                        st.rerun()
        painel_editar_excluir(
            "participantes", df_pt, "id",
            lambda r: f"{r['nome']} ({r.get('tipo', '')})",
            [
                {"col": "nome", "label": "Nome"},
                {"col": "documento", "label": "CPF/CNPJ"},
                {"col": "tipo", "label": "Tipo", "tipo": "select", "opcoes": ["Fornecedor", "Cliente"]},
                {"col": "conta_contabil", "label": "Conta Contábil Vinculada", "tipo": "select",
                 "opcoes": [""] + list(rotulo_conta.keys() - {""}), "formato": lambda v: rotulo_conta.get(v, v)},
            ],
            key="ed_part", obrigatorios=("nome",)
        )

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
                if not a_cod.strip() or not a_desc.strip():
                    st.error("Preencha código e descrição.")
                else:
                    payload = {
                        "codigo": a_cod.strip(), "descricao": a_desc.strip(), "operacao": a_oper,
                        "conta_debito": a_cdeb, "conta_credito": a_ccred,
                        "historico_padrao": a_hist, "aliquota_imposto": a_aliq
                    }
                    if executar_insert("acumuladores", payload, "Acumulador cadastrado!"):
                        st.rerun()
        painel_editar_excluir(
            "acumuladores", df_ac, "codigo",
            lambda r: f"{r['codigo']} - {r['descricao']}",
            [
                {"col": "codigo", "label": "Código (não editável)", "disabled": True},
                {"col": "descricao", "label": "Descrição"},
                {"col": "operacao", "label": "Operação", "tipo": "select", "opcoes": ["Entrada", "Saída"]},
                {"col": "conta_debito", "label": "Conta de Débito Padrão"},
                {"col": "conta_credito", "label": "Conta de Crédito Padrão"},
                {"col": "historico_padrao", "label": "Histórico Padrão"},
                {"col": "aliquota_imposto", "label": "Alíquota de Imposto (%)", "tipo": "number"},
            ],
            key="ed_acum", obrigatorios=("descricao",)
        )

    with aba_hist:
        st.subheader("Históricos Contábeis Padrão")
        df_hs = buscar_historicos()
        st.dataframe(df_hs, use_container_width=True, hide_index=True)
        with st.form("form_hist", clear_on_submit=True):
            h_cod = st.text_input("Código")
            h_ds = st.text_input("Texto do Histórico")
            if st.form_submit_button("Salvar Histórico"):
                if not h_cod.strip() or not h_ds.strip():
                    st.error("Preencha código e texto do histórico.")
                else:
                    payload = {"codigo": h_cod.strip(), "descricao": h_ds.strip()}
                    if executar_insert("historicos", payload, "Histórico salvo!"):
                        st.rerun()
        painel_editar_excluir(
            "historicos", df_hs, "codigo",
            lambda r: f"{r['codigo']} - {r['descricao'][:70]}",
            [
                {"col": "codigo", "label": "Código (não editável)", "disabled": True},
                {"col": "descricao", "label": "Texto do Histórico"},
            ],
            key="ed_hist", obrigatorios=("descricao",)
        )

    with aba_ofx_regra:
        st.subheader("Regras de Mapeamento Automatizado do OFX")
        df_regras_visualizar = buscar_regras_ofx(empresa_id)
        st.dataframe(df_regras_visualizar, use_container_width=True, hide_index=True)
        with st.form("form_ofx_regra", clear_on_submit=True):
            palavra_chave = st.text_input("Palavra-Chave do Extrato")
            c_deb = st.text_input("Conta de Débito Padrão (código estruturado)")
            c_cred = st.text_input("Conta de Crédito Padrão (código estruturado)")
            if st.form_submit_button("Salvar Nova Regra OFX"):
                if not palavra_chave.strip():
                    st.error("Informe a palavra-chave.")
                else:
                    payload = {"palavra_chave": palavra_chave.strip(), "conta_debito": c_deb.strip(), "conta_credito": c_cred.strip(), "empresa_id": empresa_id}
                    if executar_insert("regras_mapeamento_ofx", payload, "Regra de conciliação salva com sucesso!"):
                        st.rerun()
        painel_editar_excluir(
            "regras_mapeamento_ofx", df_regras_visualizar, "id",
            lambda r: f"{r['palavra_chave']}  →  D {r['conta_debito']} / C {r['conta_credito']}",
            [
                {"col": "palavra_chave", "label": "Palavra-Chave do Extrato"},
                {"col": "conta_debito", "label": "Conta de Débito Padrão"},
                {"col": "conta_credito", "label": "Conta de Crédito Padrão"},
            ],
            key="ed_regra", obrigatorios=("palavra_chave",)
        )


def main():
    st.sidebar.markdown('<div class="logo-texto">&gt;&gt;&lt;&lt;</div>', unsafe_allow_html=True)
    st.sidebar.title("Fluxo Assessoria")
    st.sidebar.caption("Assessoria Empresarial de Alta Performance")
    st.sidebar.markdown("---")

    mensagem = st.session_state.pop('_flash', None)
    if mensagem:
        st.success(mensagem)

    df_empresas = buscar_empresas_contabilidade()
    lista_nomes = df_empresas['razao_social'].tolist() if not df_empresas.empty else ["Nenhuma cadastrada"]
    emp_selecionada_nome = st.sidebar.selectbox("Selecione o Cliente Contábil", options=lista_nomes)

    cnpj_ativo = ""
    if not df_empresas.empty and emp_selecionada_nome != "Nenhuma cadastrada":
        filtrado = df_empresas[df_empresas['razao_social'] == emp_selecionada_nome]
        empresa_id_ativa = int(filtrado['id'].values[0]) if len(filtrado) > 0 else 1
        cnpj_ativo = filtrado['cnpj'].values[0] if len(filtrado) > 0 else ""
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
        renderizar_demonstracoes(empresa_id_ativa, emp_selecionada_nome, cnpj_ativo)


if __name__ == "__main__":
    main()
