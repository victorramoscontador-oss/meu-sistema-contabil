import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import hashlib
import re

# Configuração Base Ultra Leve (Sem CSS pesado para não estourar a nuvem)
st.set_page_config(page_title="Fluxo Assessoria Financeira", layout="wide")

SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_4OAD9stwBHF-L-eMaZkrFg_wRGMplWa"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

def run_query(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data) if hasattr(response, 'data') else pd.DataFrame(response)
    except: return pd.DataFrame()

def run_insert(table_name, data_dict):
    try: return bool(supabase.table(table_name).insert(data_dict).execute())
    except: return False

def criar_hash(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("### 📈 FLUXO ASSESSORIA FINANCEIRA\n**Acesso Restrito Contábil**")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar no Sistema"):
        if u == "contador" and criar_hash(p) == criar_hash("admin123"):
            st.session_state['auth'] = True
            st.rerun()
        else: st.error("Incorreto.")
    st.stop()

st.title("📈 Fluxo Assessoria Financeira - Sistema Particular")
menu = ["Lançamento de Notas", "Lançamento Manual", "Folha de Pagamento", "Importação OFX (Banco)", "Demonstrações Contábeis", "Cadastros Base"]
choice = st.sidebar.selectbox("Navegação", menu)

contas_df = run_query("plano_contas")
part_df = run_query("participantes")
acum_df = run_query("acumuladores")
if choice == "Cadastros Base":
    st.header("⚙️ Cadastros Estruturais")
    t1, t2, t3 = st.tabs(["Participantes", "Acumuladores", "Plano de Contas"])
    with t1:
        with st.form("f_p"):
            n = st.text_input("Razão Social")
            d = st.text_input("CNPJ/CPF")
            tipo = st.selectbox("Tipo", ["Fornecedor", "Cliente"])
            if st.form_submit_button("Salvar Participante"):
                run_insert("participantes", {"nome": n, "documento": d, "tipo": tipo})
                st.success("Salvo!"); st.rerun()
        st.dataframe(part_df, use_container_width=True)
    with t2:
        with st.form("f_a"):
            cod = st.text_input("Código Acumulador")
            desc = st.text_input("Descrição")
            cfop = st.text_input("CFOP")
            c_d = st.text_input("Conta Débito (Reduzido)")
            c_c = st.text_input("Conta Crédito (Reduzido)")
            if st.form_submit_button("Salvar Acumulador"):
                run_insert("acumuladores", {"codigo": cod, "descricao": desc, "cfop": cfop, "conta_debito": c_d, "conta_credito": c_c, "aliquota_imposto": 0.0})
                st.success("Salvo!"); st.rerun()
        st.dataframe(acum_df, use_container_width=True)
    with t3:
        with st.form("f_c"):
            red = st.text_input("Reduzido")
            est = st.text_input("Máscara (Ex: 1.1.1.01.0001)")
            nome_c = st.text_input("Nome da Conta")
            grp = st.selectbox("Grupo", ["Ativo", "Passivo", "PL", "Receita", "Despesa"])
            if st.form_submit_button("Adicionar Conta"):
                run_insert("plano_contas", {"codigo_reduzido": red, "codigo_estruturado": est, "nome": nome_c, "grupo": grp})
                st.success("Salvo!"); st.rerun()
        st.dataframe(contas_df, use_container_width=True)

elif choice == "Lançamento de Notas":
    st.subheader("🧾 Escrituração Fiscal")
    with st.form("f_nota"):
        dt = st.date_input("Data Nota", datetime.now(), format="DD/MM/YYYY")
        num = st.text_input("Número NF")
        part_sel = st.selectbox("Participante", part_df['nome'].tolist() if not part_df.empty else ["Sem cadastros"])
        acum_sel = st.selectbox("Acumulador", acum_df['codigo'].tolist() if not acum_df.empty else ["Sem cadastros"])
        vlr = st.number_input("Valor Bruto", min_value=0.0)
        if st.form_submit_button("Gravar Nota"):
            cfg = acum_df[acum_df['codigo'] == acum_sel].iloc[0] if not acum_df.empty else {}
            run_insert("diario", {"data": str(dt), "conta_debito": str(cfg.get('conta_debito','4')), "conta_credito": str(cfg.get('conta_credito','3')), "valor": vlr, "historico": f"Vr ref NF {num}", "origem": "Fiscal", "acumulador": str(acum_sel), "participante": str(part_sel)})
            st.success("Lançamento Contábil integrado!"); st.rerun()

elif choice == "Lançamento Manual":
    st.subheader("✍️ Partida Dobrada Manual")
    with st.form("f_man"):
        dt = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        d = st.text_input("Conta Débito (Reduzido)")
        c = st.text_input("Conta Crédito (Reduzido)")
        v = st.number_input("Valor", min_value=0.01)
        h = st.text_input("Histórico")
        if st.form_submit_button("Gravar Lançamento"):
            run_insert("diario", {"data": str(dt), "conta_debito": d, "conta_credito": c, "valor": v, "historico": h, "origem": "Manual"})
            st.success("Gravado!"); st.rerun()

elif choice == "Folha de Pagamento":
    st.subheader("👥 Provisão de Folha")
    with st.form("f_folha"):
        dt = st.date_input("Competência", datetime.now(), format="DD/MM/YYYY")
        sb = st.number_input("Salários Brutos", min_value=0.0)
        if st.form_submit_button("Integrar Folha"):
            run_insert("diario", {"data": str(dt), "conta_debito": "10", "conta_credito": "5", "valor": sb, "historico": f"Ref. Folha {str(dt)[:7]}", "origem": "Folha"})
            st.success("Folha integrada!"); st.rerun()

elif choice == "Importação OFX (Banco)":
    st.subheader("🏦 Conciliação Extrato Bancário")
    up = st.file_uploader("Arquivo .ofx", type=["ofx"])
    if up:
        txs = re.findall(r"<STMTTRN>([\s\S]*?)</STMTTRN>", up.read().decode("utf-8", errors="ignore"))
        dados = []
        for t in txs:
            v = re.search(r"<TRNAMT>(.*?)\s", t)
            m = re.search(r"<MEMO>(.*?)\s", t)
            v_num = float(v.group(1)) if v else 0.0
            dados.append({"Data": str(datetime.now().date()), "Histórico": m.group(1) if m else "BANCO", "Valor": abs(v_num)})
        st.dataframe(pd.DataFrame(dados), use_container_width=True)

elif choice == "Demonstrações Contábeis":
    st.subheader("📋 Relatórios Fiscais por Níveis de Máscara")
    diario = run_query("diario")
    dt1 = st.date_input("Início", date(2025,1,1), format="DD/MM/YYYY")
    dt2 = st.date_input("Fim", date(2025,12,31), format="DD/MM/YYYY")
    
    if diario.empty or contas_df.empty: st.info("Sem dados.")
    else:
        diario['dt'] = pd.to_datetime(diario['data']).dt.date
        df_p = diario[(diario['dt'] >= dt1) & (diario['dt'] <= dt2)]
        
        linhas = []
        for _, row in contas_df.sort_values(by="codigo_estruturado").iterrows():
            m, n, g = row['codigo_estruturado'], row['nome'], row['grupo']
            v_deb = df_p[df_p['conta_debito'] == str(row['codigo_reduzido'])]['valor'].sum()
            v_cred = df_p[df_p['conta_credito'] == str(row['codigo_reduzido'])]['valor'].sum()
            saldo = (v_deb - v_cred) if g in ['Ativo', 'Despesa'] else (v_cred - v_deb)
            linhas.append({"Classificação": m, "Descrição": n, "Saldo Atual": f"R$ {saldo:,.2f}"})
        st.dataframe(pd.DataFrame(linhas), use_container_width=True)
