import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, date
import hashlib
import re

st.set_page_config(page_title="Fluxo Assessoria Financeira", layout="wide")

# Marca e Identidade Visual Otimizada (Verde e Branco)
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"], .stWidgetLabel, p, div {
            font-family: 'Segoe UI', sans-serif !important; background-color: #FAFAFA !important; color: #1E293B !important;
        }
        section[data-testid="stSidebar"] { background-color: #031F11 !important; border-right: 1px solid #0C2E19 !important; }
        section[data-testid="stSidebar"] * { color: #F1F5F9 !important; }
        h1, h2, h3 { font-weight: 700 !important; color: #031F11 !important; }
        div.stButton > button { background: #031F11 !important; color: white !important; width: 100% !important; }
        div.stButton > button:hover { background: #10B981 !important; }
    </style>
""", unsafe_allow_html=True)

# Coleta das chaves exatamente com o nome que está na sua caixa preta do Streamlit
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

def run_query(table_name):
    try:
        res = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(res.data) if hasattr(res, 'data') else pd.DataFrame(res)
    except: return pd.DataFrame()

def run_insert(table_name, data_dict):
    try: return bool(supabase.table(table_name).insert(data_dict).execute())
    except: return False

if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<div style='text-align:center;'><h2>&gt;&gt; &lt;&lt;</h2><h1>FLUXO</h1><p>Assessoria Financeira</p></div>", unsafe_allow_html=True)
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Acessar Painel"):
        if u == "contador" and hashlib.sha256(p.encode()).hexdigest() == hashlib.sha256("admin123".encode()).hexdigest():
            st.session_state['auth'] = True
            st.rerun()
        else: st.error("Incorreto.")
    st.stop()

st.sidebar.markdown("<div style='text-align:center;'><h1 style='color:#10B981;margin:0;'>&gt;&gt; &lt;&lt;</h1><h2 style='color:white;margin:0;'>FLUXO</h2><p style='color:#10B981;font-size:12px;margin:0;'>Assessoria Financeira</p></div><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Sair"):
    st.session_state['auth'] = False
    st.rerun()

choice = st.sidebar.selectbox("Menu", ["Lançamento de Notas", "Lançamento Manual", "Folha de Pagamento", "Importação OFX (Banco)", "Demonstrações Contábeis", "Central de Relatórios", "Cadastros Base"])

contas_df = run_query("plano_contas")
part_df = run_query("participantes")
acum_df = run_query("acumuladores")

if choice == "Cadastros Base":
    st.header("⚙️ Central de Cadastros")
    t1, t2, t3 = st.tabs(["Clientes/Fornecedores", "Acumuladores", "Plano de Contas"])
    with t1:
        with st.form("f_p"):
            n = st.text_input("Nome")
            d = st.text_input("CNPJ/CPF")
            t = st.selectbox("Tipo", ["Fornecedor", "Cliente"])
            if st.form_submit_button("Salvar"):
                run_insert("participantes", {"nome": n, "documento": d, "tipo": t})
                st.success("Salvo!"); st.rerun()
        st.dataframe(part_df, use_container_width=True)
    with t2:
        with st.form("f_a"):
            cod = st.text_input("Código")
            desc = st.text_input("Descrição")
            cfop = st.text_input("CFOP")
            deb = st.text_input("Débito (Reduzido)")
            cred = st.text_input("Crédito (Reduzido)")
            if st.form_submit_button("Salvar"):
                run_insert("acumuladores", {"codigo": cod, "descricao": desc, "cfop": cfop, "conta_debito": deb, "conta_credito": cred, "aliquota_imposto": 0.0})
                st.success("Salvo!"); st.rerun()
        st.dataframe(acum_df, use_container_width=True)
    with t3:
        with st.form("f_c"):
            r = st.text_input("Reduzido")
            e = st.text_input("Máscara (Ex: 1.1.1.01.0001)")
            nm = st.text_input("Nome")
            g = st.selectbox("Grupo", ["Ativo", "Passivo", "PL", "Receita", "Despesa"])
            if st.form_submit_button("Salvar"):
                run_insert("plano_contas", {"codigo_reduzido": r, "codigo_estruturado": e, "nome": nm, "grupo": g})
                st.success("Salvo!"); st.rerun()
        st.dataframe(contas_df, use_container_width=True)
elif choice == "Lançamento de Notas":
    st.subheader("🧾 Escrituração Fiscal")
    with st.form("f_n"):
        dt = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        num = st.text_input("Número NF")
        pt = st.selectbox("Participante", part_df['nome'].tolist() if not part_df.empty else ["Sem cadastros"])
        ac = st.selectbox("Acumulador", acum_df['codigo'].tolist() if not acum_df.empty else ["Sem cadastros"])
        v = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Processar Nota"):
            cfg = acum_df[acum_df['codigo'] == ac].iloc if not acum_df.empty else {}
            run_insert("diario", {"data": str(dt), "conta_debito": str(cfg.get('conta_debito','4')), "conta_credito": str(cfg.get('conta_credito','3')), "valor": v, "historico": f"Vr ref NF {num}, Part: {pt}", "origem": "Fiscal", "acumulador": str(ac), "cfop": str(cfg.get('cfop','')), "participante": str(pt)})
            st.success("Escriturado!"); st.rerun()

elif choice == "Lançamento Manual":
    st.subheader("✍️ Partida Dobrada")
    with st.form("f_m"):
        dt = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        d = st.text_input("Débito (Reduzido)")
        c = st.text_input("Crédito (Reduzido)")
        v = st.number_input("Valor", min_value=0.01)
        h = st.text_input("Histórico")
        if st.form_submit_button("Gravar"):
            run_insert("diario", {"data": str(dt), "conta_debito": d, "conta_credito": c, "valor": v, "historico": h, "origem": "Manual"})
            st.success("Gravado!"); st.rerun()

elif choice == "Folha de Pagamento":
    st.subheader("👥 Provisão de Folha")
    with st.form("f_f"):
        dt = st.date_input("Competência", datetime.now(), format="DD/MM/YYYY")
        sb = st.number_input("Valor Bruto", min_value=0.0)
        if st.form_submit_button("Integrar"):
            run_insert("diario", {"data": str(dt), "conta_debito": "10", "conta_credito": "5", "valor": sb, "historico": f"Folha {str(dt)[:7]}", "origem": "Folha"})
            st.success("Integrada!"); st.rerun()

elif choice == "Importação OFX (Banco)":
    st.subheader("🏦 Conciliação Bancária OFX")
    up = st.file_uploader("Arquivo .ofx", type=["ofx"])
    if up:
        txs = re.findall(r"<STMTTRN>([\s\S]*?)</STMTTRN>", up.read().decode("utf-8", errors="ignore"))
        dados = []
        for t in txs:
            v = re.search(r"<TRNAMT>(.*?)\s", t)
            m = re.search(r"<MEMO>(.*?)\s", t)
            dados.append({"Data": datetime.now().strftime("%d/%m/%Y"), "Histórico": m.group(1) if m else "BANCO", "Valor": abs(float(v.group(1))) if v else 0.0})
        st.dataframe(pd.DataFrame(dados), use_container_width=True)

elif choice == "Demonstrações Contábeis":
    st.subheader("📋 Demonstrativos Oficiais por Período")
    diario = run_query("diario")
    dt1 = st.date_input("Início", date(2025,1,1), format="DD/MM/YYYY")
    dt2 = st.date_input("Fim", date(2025,12,31), format="DD/MM/YYYY")
    if diario.empty or contas_df.empty: st.info("Sem lançamentos.")
    else:
        diario['dt'] = pd.to_datetime(diario['data']).dt.date
        df_ant = diario[diario['dt'] < dt1]
        df_per = diario[(diario['dt'] >= dt1) & (diario['dt'] <= dt2)]
        
        linhas = []
        for _, row in contas_df.sort_values(by="codigo_estruturado").iterrows():
            m, n, g, r_c = row['codigo_estruturado'], row['nome'], row['grupo'], str(row['codigo_reduzido'])
            ant_d = df_ant[df_ant['conta_debito'] == r_c]['valor'].sum()
            ant_c = df_ant[df_ant['conta_credito'] == r_c]['valor'].sum()
            per_d = df_per[df_per['conta_debito'] == r_c]['valor'].sum()
            per_c = df_per[df_per['conta_credito'] == r_c]['valor'].sum()
            s_ant = (ant_d - ant_c) if g in ['Ativo', 'Despesa'] else (ant_c - ant_d)
            s_at = ((ant_d + per_d) - (ant_c + per_c)) if g in ['Ativo', 'Despesa'] else ((ant_c + per_c) - (ant_d + per_d))
            linhas.append({"Classificação": m, "Descrição": n, "Saldo Anterior": f"R$ {s_ant:,.2f}", "Débito": per_d, "Crédito": per_c, "Saldo Atual": f"R$ {s_at:,.2f}", "_val": s_at, "_grp": g})
        
        df_v = pd.DataFrame(linhas)
        tb1, tb2, tb3 = st.tabs(["Balancete", "DRE", "Balanço"])
        with tb1: st.dataframe(df_v[["Classificação", "Descrição", "Saldo Anterior", "Débito", "Crédito", "Saldo Atual"]], use_container_width=True)
        with tb2:
            r = df_v[df_v['_grp'] == 'Receita']['_val'].sum()
            d = df_v[df_v['_grp'] == 'Despesa']['_val'].sum()
            st.markdown(f"**(+) RECEITA BRUTA:** R$ {r:,.2f}\n\n**(-) DESPESAS OPERACIONAIS:** R$ {d:,.2f}\n\n**(=) RESULTADO LÍQUIDO:** R$ {r-d:,.2f}")
        with tb3:
            c1, c2 = st.columns(2)
            c1.info("**ATIVO**"); c1.dataframe(df_v[df_v['_grp'] == 'Ativo'][["Classificação", "Descrição", "Saldo Atual"]], use_container_width=True)
            c2.info("**PASSIVO e PL**"); c2.dataframe(df_v[df_v['_grp'].isin(['Passivo', 'PL'])][["Classificação", "Descrição", "Saldo Atual"]], use_container_width=True)

elif choice == "Central de Relatórios":
    st.subheader("🔍 Filtros de Auditoria")
    diario = run_query("diario")
    if diario.empty: st.info("Vazio.")
    else:
        ac_f = st.text_input("Filtrar por Acumulador")
        if ac_f: diario = diario[diario['acumulador'] == ac_f]
        st.dataframe(diario[["data", "conta_debito", "conta_credito", "valor", "historico", "origem"]], use_container_width=True)
