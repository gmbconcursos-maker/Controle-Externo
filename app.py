#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║      SISTEMA DE ESTUDOS — AUDITOR DE CONTROLE EXTERNO           ║
║         Streamlit Web App  •  PC + iPhone + Android             ║
║         Persistência: Supabase (nuvem) ou JSON (local)          ║
╚══════════════════════════════════════════════════════════════════╝

INSTALAÇÃO:
    pip install streamlit pandas supabase

RODAR LOCALMENTE (sem Supabase — usa JSON local):
    streamlit run app.py

RODAR COM SUPABASE (persistência real na nuvem):
    1. Crie projeto gratuito em supabase.com
    2. Rode o SQL de  supabase_schema.sql  no SQL Editor do Supabase
    3. Configure .streamlit/secrets.toml com SUPABASE_URL e SUPABASE_KEY
    4. streamlit run app.py

ACESSAR NO IPHONE (mesma rede Wi-Fi):
    http://<IP-do-seu-PC>:8501

PUBLICAR NA NUVEM (gratuito):
    1. Crie conta em share.streamlit.io
    2. Suba os arquivos para um repositório GitHub
    3. Configure os "Secrets" do app no painel do Streamlit Cloud
       com SUPABASE_URL e SUPABASE_KEY
    4. Importe o repositório no Streamlit Cloud
"""

import streamlit as st
import json, os, datetime, random, math, time
from pathlib import Path

# ── Supabase é OPCIONAL — se não configurado, cai para JSON local ──────────
try:
    from supabase import create_client
    _SUPABASE_LIB_OK = True
except ImportError:
    _SUPABASE_LIB_OK = False

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURAÇÃO DA PÁGINA
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Estudos — Controle Externo",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
#  CSS CUSTOMIZADO (responsivo — funciona no iPhone)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* Tema escuro customizado */
:root {
    --accent:   #e94560;
    --accent2:  #f5a623;
    --accent3:  #4ecdc4;
    --verde:    #2ecc71;
    --vermelho: #e74c3c;
    --card:     #0f3460;
    --panel:    #16213e;
}

/* Esconder menu padrão do Streamlit */
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #16213e !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 15px !important;
    padding: 6px 0 !important;
}

/* Botões principais */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}

/* Cards KPI */
.kpi-card {
    background: linear-gradient(135deg, #0f3460, #16213e);
    border: 1px solid #2d2d4e;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    margin: 4px 0;
}
.kpi-valor { font-size: 28px; font-weight: 700; margin: 0; }
.kpi-label { font-size: 12px; color: #9e9e9e; margin: 0; }

/* Barra de progresso customizada */
.barra-wrap {
    background: #2d2d4e;
    border-radius: 8px;
    height: 10px;
    width: 100%;
    overflow: hidden;
}
.barra-fill {
    height: 10px;
    border-radius: 8px;
    transition: width 0.4s ease;
}

/* Badge de status */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.badge-dominado   { background:#1a4731; color:#2ecc71; }
.badge-andamento  { background:#3d2b00; color:#f5a623; }
.badge-revisar    { background:#3d1a00; color:#e67e22; }
.badge-nao        { background:#2d2d2d; color:#9e9e9e; }

/* Flashcard */
.flashcard-frente {
    background: linear-gradient(135deg, #0f3460, #1a1a2e);
    border: 2px solid #f5a623;
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    font-size: 18px;
    font-weight: 600;
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.flashcard-verso {
    background: linear-gradient(135deg, #0a3d2b, #1a1a2e);
    border: 2px solid #2ecc71;
    border-radius: 16px;
    padding: 28px 24px;
    font-size: 15px;
    min-height: 120px;
}

/* Responsivo mobile */
@media (max-width: 768px) {
    .kpi-valor { font-size: 22px; }
    .flashcard-frente { font-size: 15px; padding: 20px 16px; }
}

/* Título da página */
.page-title {
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 4px;
}
.page-sub {
    color: #9e9e9e;
    font-size: 13px;
    margin-bottom: 20px;
}

/* Linha separadora */
hr { border-color: #2d2d4e !important; }

/* Métricas nativas do Streamlit */
[data-testid="stMetric"] {
    background: #0f3460;
    border-radius: 10px;
    padding: 12px 16px;
    border: 1px solid #2d2d4e;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  DADOS — PERSISTÊNCIA HÍBRIDA (Supabase ou JSON local)
# ═══════════════════════════════════════════════════════════════════════════

DATA_FILE     = "dados_estudos.json"
SM2_INTERVALS = [1, 3, 7, 15, 30, 60, 120]
STATUS_LISTA  = ["Não estudado", "Em andamento", "Revisar", "Dominado"]
STATUS_ICONE  = {"Não estudado":"○","Em andamento":"◑","Revisar":"◈","Dominado":"●"}

def _hoje() -> str:
    return datetime.date.today().isoformat()

def _dias_ate(data_str: str) -> int:
    if not data_str: return 999
    return (datetime.date.fromisoformat(data_str) - datetime.date.today()).days

def _add_dias(n: int) -> str:
    return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()

def _novo_id(pref: str, dic: dict) -> str:
    return f"{pref}{len(dic)+1:04d}"

def _dados_iniciais() -> dict:
    return {
        "materias": {}, "flashcards": {}, "sessoes": [],
        "questoes": {}, "feynman": {},
        "config": {
            "horas_por_dia": 4, "tecnica": "25/5",
            "meta_semanal_horas": 28, "usuario": "Candidato",
        },
        "streak": {"ultimo_dia": None, "consecutivos": 0, "total_dias": 0},
    }

# ── Detecção de configuração Supabase ───────────────────────────────────────
def _supabase_configurado() -> bool:
    """Verifica se há credenciais Supabase em st.secrets."""
    if not _SUPABASE_LIB_OK:
        return False
    try:
        return bool(st.secrets.get("SUPABASE_URL")) and bool(st.secrets.get("SUPABASE_KEY"))
    except Exception:
        return False

@st.cache_resource
def _get_supabase_client():
    """Cliente Supabase, criado uma única vez por processo."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def _usuario_atual() -> str:
    """
    Identificador único do usuário para separar dados na tabela Supabase.
    Por padrão usa um ID fixo simples (single-user). Se quiser multiusuário
    com senha, ative o login simples na barra lateral (ver _sidebar_login).
    """
    return st.session_state.get("user_id", "usuario_padrao")

# ── Camada de persistência: Supabase ────────────────────────────────────────
def _carregar_supabase() -> dict:
    sb  = _get_supabase_client()
    uid = _usuario_atual()
    try:
        resp = sb.table("estudos_dados").select("payload").eq("user_id", uid).execute()
        if resp.data:
            d = resp.data[0]["payload"]
            for k, v in _dados_iniciais().items():
                if k not in d:
                    d[k] = v
            return d
    except Exception as e:
        st.session_state["_supabase_erro"] = str(e)
    return _dados_iniciais()

def _salvar_supabase(d: dict):
    sb  = _get_supabase_client()
    uid = _usuario_atual()
    try:
        sb.table("estudos_dados").upsert({
            "user_id": uid,
            "payload": d,
            "atualizado_em": datetime.datetime.now().isoformat(),
        }).execute()
    except Exception as e:
        st.session_state["_supabase_erro"] = str(e)

# ── Camada de persistência: JSON local ──────────────────────────────────────
def _carregar_json() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        for k, v in _dados_iniciais().items():
            if k not in d: d[k] = v
        return d
    return _dados_iniciais()

def _salvar_json(d: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ── Interface pública usada pelo resto do app ───────────────────────────────
def carregar() -> dict:
    if _supabase_configurado():
        return _carregar_supabase()
    return _carregar_json()

def salvar(d: dict):
    if _supabase_configurado():
        _salvar_supabase(d)
    else:
        _salvar_json(d)
    if "d" in st.session_state:
        st.session_state["d"] = d

def get_d() -> dict:
    if "d" not in st.session_state:
        st.session_state["d"] = carregar()
    return st.session_state["d"]

def save_d():
    salvar(st.session_state["d"])

def _atualizar_streak():
    d   = get_d()
    s   = d["streak"]
    hj  = _hoje()
    ult = s.get("ultimo_dia")
    if ult == hj: return
    ontem = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    s["consecutivos"] = (s.get("consecutivos",0)+1) if ult == ontem else 1
    s["ultimo_dia"]   = hj
    s["total_dias"]   = s.get("total_dias",0) + 1
    save_d()

# ═══════════════════════════════════════════════════════════════════════════
#  DADOS DEMO — 15 MATÉRIAS TCU / TCEs
# ═══════════════════════════════════════════════════════════════════════════

_MATERIAS_DEMO = [
    ("Controle Externo e Auditoria Gov.", 5, [
        ("TCU: CF/88, Lei Orgânica e Regimento Interno", 4, 5),
        ("Controle da Administração (interno e externo)", 3, 5),
        ("Improbidade administrativa", 3, 5),
        ("Tipos de auditoria (operacional, conformidade, financeira)", 4, 4),
        ("Tomada de contas especial (TCE)", 4, 5),
        ("Fiscalização financeira — arts. 70–75 CF/88", 3, 5),
    ]),
    ("AFO — Adm. Financeira e Orçamentária", 5, [
        ("LRF — Planejamento e despesa de pessoal", 4, 5),
        ("Ciclo orçamentário", 3, 5),
        ("PPA, LDO e LOA", 3, 5),
        ("Execução orçamentária e financeira", 4, 5),
        ("Restos a pagar e DEA", 3, 4),
        ("Créditos adicionais", 3, 4),
        ("Dívida pública", 4, 3),
    ]),
    ("Contabilidade Pública", 5, [
        ("Demonstrações contábeis — MCASP/NBC TSP", 4, 5),
        ("Receita e despesa pública — Lei 4.320/64", 3, 5),
        ("SIAFI e sistemas de controle", 3, 4),
        ("Ativo/passivo financeiro e permanente", 3, 4),
        ("Depreciação e amortização no setor público", 4, 3),
    ]),
    ("Direito Administrativo", 5, [
        ("Licitações e contratos — Lei 14.133/2021", 4, 5),
        ("Atos administrativos", 3, 5),
        ("Responsabilidade civil do Estado", 3, 5),
        ("Serviços públicos", 3, 4),
        ("Agentes públicos — regimes e responsabilidades", 3, 5),
    ]),
    ("Direito Constitucional", 5, [
        ("Organização dos Poderes — arts. 44–135 CF/88", 3, 5),
        ("Organização do Estado — arts. 18–43 CF/88", 3, 5),
        ("Direitos e garantias fundamentais — art. 5º", 3, 5),
        ("Tributação e orçamento — arts. 145–169", 3, 5),
        ("Controle de constitucionalidade", 3, 4),
    ]),
    ("Estatística", 5, [
        ("Estatística descritiva — média, mediana, moda", 4, 5),
        ("Probabilidade e distribuições — normal, binomial", 4, 5),
        ("Inferência estatística e intervalos de confiança", 5, 5),
        ("Regressão e correlação", 5, 4),
        ("Amostragem", 4, 4),
    ]),
    ("Análise de Dados", 5, [
        ("Business intelligence e visualização de dados", 4, 5),
        ("SQL e bancos de dados relacionais", 4, 5),
        ("Machine learning e data mining — conceitos", 5, 4),
        ("Análise de dados aplicada à auditoria", 4, 5),
    ]),
    ("Língua Portuguesa", 4, [
        ("Interpretação de textos", 2, 5),
        ("Reescrita de frases e substituição", 2, 5),
        ("Coerência e coesão textual", 3, 4),
        ("Morfologia", 3, 3),
        ("Pontuação", 3, 3),
        ("Regência e concordância", 3, 3),
    ]),
    ("Administração Pública", 4, [
        ("Processo de planejamento estratégico", 3, 5),
        ("Reforma do Estado e evolução da APU no Brasil", 3, 5),
        ("PMBOK — Gestão de projetos", 4, 4),
        ("Gestão de pessoas no setor público", 3, 4),
        ("Gestão por processos — BPM CBOK, PDCA", 3, 4),
    ]),
    ("Matemática Financeira", 4, [
        ("Juros simples e compostos", 2, 5),
        ("Equivalência de taxas", 3, 4),
        ("Séries de pagamentos — anuidades", 3, 4),
        ("Amortização SAC e Price", 3, 4),
        ("VPL, TIR e análise de investimentos", 4, 3),
    ]),
    ("Sistema Normativo Anticorrupção", 4, [
        ("Lei Anticorrupção — 12.846/2013", 3, 5),
        ("Improbidade administrativa — Lei 14.230/2021", 3, 5),
        ("LGPD aplicada ao setor público", 3, 4),
        ("Acordos de leniência e compliance público", 4, 4),
    ]),
    ("Direito Civil", 3, [
        ("Teoria geral das obrigações", 3, 4),
        ("Contratos — formação, vícios, extinção", 3, 4),
        ("Responsabilidade civil", 3, 4),
        ("Bens públicos", 2, 4),
    ]),
    ("Economia do Setor Público", 3, [
        ("Falhas de mercado e bens públicos", 3, 4),
        ("Teoria da tributação e federalismo fiscal", 4, 3),
        ("Dívida pública e política fiscal", 4, 3),
    ]),
    ("Direito Processual Civil", 3, [
        ("Princípios processuais", 2, 3),
        ("Processo no TCU/TCEs", 3, 4),
        ("Tutela de urgência e mandado de segurança", 3, 3),
    ]),
    ("Língua Inglesa", 3, [
        ("Interpretação de textos técnicos", 2, 5),
        ("Vocabulário e sinônimos em contexto", 2, 4),
        ("Reescrita e substituição de palavras", 2, 3),
    ]),
]

_FC_DEMO = [
    ("M0001","O que são Restos a Pagar (RAP)?",
     "Despesas empenhadas mas não pagas até 31/12. Podem ser processados (liquidados) ou não-processados."),
    ("M0001","Qual o prazo para Tomada de Contas Especial?",
     "O TCU pode determinar instauração imediata. Se a unidade não agir, o TCU avoca o processo."),
    ("M0002","O que é a Lei de Responsabilidade Fiscal?",
     "LC 101/2000: normas de finanças públicas voltadas à responsabilidade na gestão fiscal."),
    ("M0002","Quais os instrumentos de planejamento da LRF?",
     "PPA (4 anos), LDO (anual — metas e prioridades) e LOA (anual — orçamento detalhado)."),
    ("M0004","Principal inovação da Lei 14.133/2021?",
     "Unificou normas de licitações, criou Diálogo Competitivo, extinguiu convite e tomada de preços."),
    ("M0005","O que dizem os arts. 70–75 da CF/88?",
     "Estabelecem a fiscalização contábil, financeira, orçamentária, operacional e patrimonial da União, com auxílio do TCU."),
    ("M0006","Diferença entre média, mediana e moda?",
     "Média: soma/n. Mediana: valor central após ordenação. Moda: valor mais frequente. Diferem em distribuições assimétricas."),
    ("M0011","O que é compliance público?",
     "Conjunto de práticas para garantir conformidade com leis e padrões éticos, prevenindo corrupção na gestão pública."),
]

def _carregar_demo():
    d = get_d()
    d["materias"].clear()
    d["flashcards"].clear()
    for nome, prio, tops in _MATERIAS_DEMO:
        mid = _novo_id("M", d["materias"])
        d["materias"][mid] = {
            "nome": nome, "prioridade": prio,
            "topicos": {}, "criado_em": _hoje(),
        }
        for nt, dif, pt in tops:
            tid = _novo_id("T", d["materias"][mid]["topicos"])
            d["materias"][mid]["topicos"][tid] = {
                "nome": nt, "dificuldade": dif, "prioridade": pt,
                "status": "Não estudado",
                "ultima_revisao": None, "proxima_revisao": None,
                "intervalo_idx": 0, "total_revisoes": 0,
                "aula_ref": "",
                "criado_em": _hoje(),
            }
    for mid_ref, frente, verso in _FC_DEMO:
        fid = _novo_id("FC", d["flashcards"])
        d["flashcards"][fid] = {
            "frente": frente, "verso": verso, "materia_id": mid_ref,
            "proxima_revisao": _hoje(), "intervalo_idx": 0,
            "total_revisoes": 0, "facilidade_media": 3.0,
            "criado_em": _hoje(),
        }
    save_d()
    st.success("✅ 15 matérias e 8 flashcards de exemplo carregados!")
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS VISUAIS
# ═══════════════════════════════════════════════════════════════════════════

def _prio_cor(p: int) -> str:
    return ["","#e74c3c","#e67e22","#f1c40f","#2ecc71","#27ae60"][p]

def _status_badge(s: str) -> str:
    cls = {"Dominado":"dominado","Em andamento":"andamento",
           "Revisar":"revisar","Não estudado":"nao"}.get(s,"nao")
    icn = STATUS_ICONE.get(s,"○")
    return f'<span class="badge badge-{cls}">{icn} {s}</span>'

def _barra_html(pct: float, cor: str = "#2ecc71", altura: int = 10) -> str:
    w = int(max(0, min(100, pct * 100)))
    return (f'<div class="barra-wrap">'
            f'<div class="barra-fill" style="width:{w}%;background:{cor};height:{altura}px;"></div>'
            f'</div>')

def _kpi(label: str, valor: str, cor: str = "#e94560") -> str:
    return (f'<div class="kpi-card">'
            f'<p class="kpi-valor" style="color:{cor}">{valor}</p>'
            f'<p class="kpi-label">{label}</p>'
            f'</div>')

# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR — NAVEGAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

def _tela_login() -> bool:
    """
    Tela de login simples (nome + PIN de 4 dígitos) usada apenas quando
    o Supabase está configurado, para isolar dados entre pessoas que
    acessem o mesmo link público. Retorna True se o login foi concluído.
    """
    if not _supabase_configurado():
        st.session_state["user_id"] = "usuario_local"
        return True

    if st.session_state.get("user_id"):
        return True

    st.markdown(
        '<p class="page-title">⚖️ Sistema de Estudos — Controle Externo</p>',
        unsafe_allow_html=True)
    st.markdown(
        '<p class="page-sub">Seus dados ficam salvos na nuvem e isolados '
        'por nome + PIN. Use sempre a mesma combinação para acessar '
        'os mesmos dados de qualquer dispositivo.</p>',
        unsafe_allow_html=True)

    with st.form("form_login"):
        col1, col2 = st.columns([2,1])
        with col1:
            nome = st.text_input("Seu nome ou apelido",
                                  placeholder="ex: joao_concurseiro")
        with col2:
            pin = st.text_input("PIN (4 dígitos)", placeholder="0000",
                                max_chars=4, type="password")
        entrar = st.form_submit_button("🔓 Entrar", type="primary",
                                        use_container_width=True)
        if entrar:
            nome_limpo = "".join(c for c in nome.lower().strip()
                                 if c.isalnum() or c == "_")
            if not nome_limpo or not pin or len(pin) != 4 or not pin.isdigit():
                st.error("Preencha um nome válido e um PIN de exatamente 4 dígitos.")
            else:
                st.session_state["user_id"] = f"{nome_limpo}_{pin}"
                st.rerun()

    st.caption(
        "💡 Dica: anote seu nome + PIN. É a única forma de recuperar "
        "seus dados depois. Não há recuperação de senha.")
    return False

def _sidebar():
    d = get_d()
    s = d["streak"]
    with st.sidebar:
        st.markdown("## ⚖️ Controle Externo")
        st.markdown(f"**{d['config'].get('usuario','Candidato')}**")
        st.markdown(
            f"🔥 **{s.get('consecutivos',0)}** dias seguidos  "
            f"| {s.get('total_dias',0)} total")
        st.divider()

        pagina = st.radio(
            "Navegar",
            ["🏠 Dashboard", "📚 Matérias e Tópicos",
             "🃏 Flashcards", "✅ Tarefas", "📈 Análise",
             "✍ Feynman", "💾 Exportar"],
            label_visibility="collapsed",
        )
        st.divider()

        fc_hj = sum(
            1 for fc in d["flashcards"].values()
            if (fc.get("proxima_revisao") or _hoje()) <= _hoje())
        if fc_hj:
            st.warning(f"🃏 {fc_hj} flashcard(s) para revisar hoje!")

        if st.button("🏫 Carregar TCU/TCEs", use_container_width=True,
                     type="secondary"):
            _carregar_demo()

        st.divider()
        if _supabase_configurado():
            uid = _usuario_atual()
            st.success(f"☁️ Nuvem ativa  •  {uid}")
            erro = st.session_state.get("_supabase_erro")
            if erro:
                st.error(f"⚠️ Erro Supabase: {erro[:80]}")
            if st.button("🔒 Sair (trocar usuário)", use_container_width=True):
                del st.session_state["user_id"]
                if "d" in st.session_state:
                    del st.session_state["d"]
                st.rerun()
        else:
            st.info("💾 Armazenamento local (JSON)")
            st.caption("Configure Supabase para persistência na nuvem "
                       "— veja LEIA_ME_STREAMLIT.txt")

    return pagina

# ═══════════════════════════════════════════════════════════════════════════
#  PÁGINA: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

def p_dashboard():
    d  = get_d()
    hj = datetime.date.today()

    st.markdown('<p class="page-title">🏠 Dashboard</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="page-sub">{hj.strftime("%A, %d de %B de %Y")}</p>',
        unsafe_allow_html=True)

    # KPIs
    total_min = sum(s["duracao_min"] for s in d["sessoes"])
    fc_hj     = sum(1 for fc in d["flashcards"].values()
                    if (fc.get("proxima_revisao") or _hoje()) <= _hoje())
    streak    = d["streak"].get("consecutivos", 0)
    n_tops    = sum(len(m.get("topicos",{})) for m in d["materias"].values())
    n_dom     = sum(sum(1 for tp in m.get("topicos",{}).values()
                        if tp.get("status")=="Dominado")
                    for m in d["materias"].values())

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.metric("🔥 Streak",    f"{streak} dias")
    with c2: st.metric("⏱ Total",     f"{total_min//60}h{total_min%60:02d}m")
    with c3: st.metric("🃏 Hoje",      f"{fc_hj} cards")
    with c4: st.metric("📚 Matérias",  str(len(d["materias"])))
    with c5: st.metric("✅ Dominados", f"{n_dom}/{n_tops}")

    # Botão revisão rápida
    st.divider()
    if st.button("⚡ Revisão Rápida — 10 minutos de Active Recall",
                 use_container_width=True, type="primary"):
        st.session_state["pagina_override"] = "🃏 Flashcards"
        st.session_state["revisao_rapida"]  = True
        st.rerun()

    # Meta semanal
    st.divider()
    ini_s  = hj - datetime.timedelta(days=hj.weekday())
    min_s  = sum(s["duracao_min"] for s in d["sessoes"]
                 if s["data"] >= ini_s.isoformat())
    meta_m = d["config"].get("meta_semanal_horas", 28) * 60
    pct_s  = min(1.0, min_s / meta_m) if meta_m else 0
    cor_m  = ("#2ecc71" if pct_s >= 0.8
               else "#f5a623" if pct_s >= 0.5 else "#e74c3c")

    st.subheader("📅 Meta Semanal")
    st.markdown(_barra_html(pct_s, cor_m, 14), unsafe_allow_html=True)
    st.caption(f"{min_s//60}h{min_s%60:02d}m  /  {meta_m//60}h   ({pct_s*100:.0f}%)")

    # Progresso por matéria
    if d["materias"]:
        st.divider()
        st.subheader("📊 Progresso por Matéria")
        for mid, m in d["materias"].items():
            tops  = m.get("topicos", {})
            total = len(tops)
            dom   = sum(1 for tp in tops.values()
                        if tp.get("status") == "Dominado")
            pct   = dom / total if total else 0
            p     = m.get("prioridade", 3)
            col_n, col_b, col_p = st.columns([3, 4, 1])
            with col_n:
                st.markdown(f"**{m['nome'][:35]}**")
            with col_b:
                cor_b = "#2ecc71" if pct >= 0.7 else "#f5a623" if pct >= 0.3 else "#e74c3c"
                st.markdown(_barra_html(pct, cor_b, 8), unsafe_allow_html=True)
                st.caption(f"{pct*100:.0f}%  ({dom}/{total})")
            with col_p:
                st.markdown(
                    f'<span style="color:{_prio_cor(p)};font-weight:600;">P{p}</span>',
                    unsafe_allow_html=True)

    # Gráfico de horas — 7 dias
    st.divider()
    st.subheader("📈 Horas de Estudo — Últimos 7 Dias")
    dias_labels, horas_vals = [], []
    for i in range(6, -1, -1):
        dia    = (hj - datetime.timedelta(days=i)).isoformat()
        m_dia  = sum(s["duracao_min"] for s in d["sessoes"] if s["data"] == dia)
        label  = "Hoje" if i == 0 else (hj-datetime.timedelta(days=i)).strftime("%a %d")
        dias_labels.append(label)
        horas_vals.append(round(m_dia / 60, 2))

    import streamlit as _st
    chart_data = {"Horas": horas_vals}
    try:
        import pandas as pd
        df = pd.DataFrame(chart_data, index=dias_labels)
        st.bar_chart(df, color="#e94560")
    except ImportError:
        for lbl, h in zip(dias_labels, horas_vals):
            bar = "█" * int(h * 4) + "░" * max(0, 16 - int(h * 4))
            st.text(f"{lbl:>8}  {bar}  {h:.1f}h")

# ═══════════════════════════════════════════════════════════════════════════
#  PÁGINA: MATÉRIAS E TÓPICOS
# ═══════════════════════════════════════════════════════════════════════════

def p_materias():
    d = get_d()
    st.markdown('<p class="page-title">📚 Matérias e Tópicos</p>', unsafe_allow_html=True)

    # ── Nova matéria ──────────────────────────────────────────────────────
    with st.expander("➕ Nova Matéria", expanded=False):
        with st.form("form_nova_mat", clear_on_submit=True):
            col1, col2 = st.columns([3,1])
            with col1: nome_m = st.text_input("Nome da matéria")
            with col2: prio_m = st.selectbox("Prioridade", [5,4,3,2,1],
                                              format_func=lambda x: f"{'★'*x} ({x})")
            if st.form_submit_button("Adicionar Matéria", type="primary"):
                if nome_m.strip():
                    mid = _novo_id("M", d["materias"])
                    d["materias"][mid] = {
                        "nome": nome_m.strip(), "prioridade": prio_m,
                        "topicos": {}, "criado_em": _hoje(),
                    }
                    save_d()
                    st.success(f"✅ '{nome_m}' adicionada!")
                    st.rerun()

    st.divider()

    if not d["materias"]:
        st.info("Nenhuma matéria cadastrada. Use 'Carregar TCU/TCEs' ou adicione uma acima.")
        return

    # ── Lista de matérias ─────────────────────────────────────────────────
    for mid, m in d["materias"].items():
        tops  = m.get("topicos", {})
        total = len(tops)
        dom   = sum(1 for tp in tops.values() if tp.get("status")=="Dominado")
        pct   = dom / total if total else 0
        p     = m.get("prioridade", 3)

        with st.expander(
            f"{'★'*p}  **{m['nome']}**  —  {dom}/{total} tópicos  ({pct*100:.0f}%)",
            expanded=False
        ):
            cor_b = "#2ecc71" if pct>=0.7 else "#f5a623" if pct>=0.3 else "#e74c3c"
            st.markdown(_barra_html(pct, cor_b, 8), unsafe_allow_html=True)
            st.caption(f"Prioridade: {p}/5  |  Criada em: {m.get('criado_em','—')}")

            # Ações da matéria
            ca, cb, cc = st.columns(3)
            with ca:
                if st.button("🗑 Remover matéria", key=f"rm_mat_{mid}"):
                    st.session_state[f"confirm_rm_{mid}"] = True
            if st.session_state.get(f"confirm_rm_{mid}"):
                st.warning(f"Remover '{m['nome']}' e todos os tópicos?")
                col_s, col_n = st.columns(2)
                with col_s:
                    if st.button("✅ Sim, remover", key=f"sim_rm_{mid}"):
                        del d["materias"][mid]
                        save_d()
                        st.rerun()
                with col_n:
                    if st.button("❌ Cancelar", key=f"nao_rm_{mid}"):
                        st.session_state[f"confirm_rm_{mid}"] = False
                        st.rerun()

            st.divider()

            # ── Tópicos ───────────────────────────────────────────────────
            st.markdown("**Tópicos:**")
            if not tops:
                st.caption("Nenhum tópico ainda.")
            else:
                for tid, tp in tops.items():
                    t_col1, t_col2, t_col3, t_col4 = st.columns([3, 2, 2, 2])
                    with t_col1:
                        st.markdown(f"**{tp['nome']}**")
                        aula_atual = tp.get("aula_ref", "")
                        if aula_atual:
                            st.caption(f"🎓 {aula_atual}")
                    with t_col2:
                        st.markdown(_status_badge(tp.get("status","Não estudado")),
                                    unsafe_allow_html=True)
                    with t_col3:
                        novo_status = st.selectbox(
                            "Status", STATUS_LISTA,
                            index=STATUS_LISTA.index(tp.get("status","Não estudado")),
                            key=f"st_{mid}_{tid}",
                            label_visibility="collapsed")
                        if novo_status != tp.get("status"):
                            tp["status"]         = novo_status
                            tp["ultima_revisao"] = _hoje()
                            if novo_status == "Dominado":
                                tp["proxima_revisao"] = _add_dias(30)
                            save_d()
                            st.rerun()
                    with t_col4:
                        dif = tp.get("dificuldade",3)
                        st.caption(f"Dif: {'★'*dif}  Prio: {tp.get('prioridade',3)}")

                    # Campo editável de referência de aula/material
                    with st.form(f"form_aula_{mid}_{tid}", clear_on_submit=False):
                        ca1, ca2 = st.columns([5,1])
                        with ca1:
                            nova_aula = st.text_input(
                                "Aula/material de referência (ex: Aula 09 — Pontuação)",
                                value=tp.get("aula_ref",""),
                                key=f"in_aula_{mid}_{tid}",
                                placeholder="ex: Aula 12 — Estratégia Concursos")
                        with ca2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.form_submit_button("💾"):
                                tp["aula_ref"] = nova_aula.strip()
                                save_d()
                                st.rerun()
                    st.markdown(
                        '<hr style="margin:4px 0;border-color:#2d2d4e;">',
                        unsafe_allow_html=True)

            # ── Novo tópico ───────────────────────────────────────────────
            st.divider()
            with st.form(f"form_top_{mid}", clear_on_submit=True):
                st.markdown("**➕ Novo Tópico**")
                nt_col1, nt_col2, nt_col3 = st.columns([4,1,1])
                with nt_col1: nome_t = st.text_input("Nome", key=f"nt_nome_{mid}")
                with nt_col2: dif_t  = st.selectbox("Dific.", [1,2,3,4,5], index=2,
                                                      key=f"nt_dif_{mid}")
                with nt_col3: prio_t = st.selectbox("Prio.", [5,4,3,2,1], index=2,
                                                      key=f"nt_prio_{mid}")
                aula_t = st.text_input(
                    "Aula/material de referência (opcional)",
                    key=f"nt_aula_{mid}",
                    placeholder="ex: Aula 09 — Pontuação (Estratégia Concursos)")
                if st.form_submit_button("Adicionar Tópico"):
                    if nome_t.strip():
                        tid = _novo_id("T", tops)
                        tops[tid] = {
                            "nome": nome_t.strip(), "dificuldade": dif_t,
                            "prioridade": prio_t, "status": "Não estudado",
                            "ultima_revisao": None, "proxima_revisao": None,
                            "intervalo_idx": 0, "total_revisoes": 0,
                            "aula_ref": aula_t.strip(),
                            "criado_em": _hoje(),
                        }
                        save_d()
                        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  PÁGINA: FLASHCARDS + REVISÃO ESPAÇADA (SM-2)
# ═══════════════════════════════════════════════════════════════════════════

def p_flashcards():
    d     = get_d()
    fcs   = d["flashcards"]
    mats  = d["materias"]

    st.markdown('<p class="page-title">🃏 Flashcards + Revisão Espaçada</p>',
                unsafe_allow_html=True)

    pendentes = [(fid, fc) for fid, fc in fcs.items()
                 if (fc.get("proxima_revisao") or _hoje()) <= _hoje()]

    # Revisão rápida via dashboard
    if st.session_state.get("revisao_rapida"):
        st.session_state["revisao_rapida"] = False
        if fcs:
            todos = list(fcs.items())
            random.shuffle(todos)
            st.session_state["fila_revisao"] = todos[:8]
            st.session_state["idx_revisao"]  = 0
            st.session_state["modo_revisao"] = "rapida"

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("▶ Revisar Todos os Pendentes",
                     use_container_width=True, type="primary",
                     disabled=len(pendentes)==0):
            random.shuffle(pendentes)
            st.session_state["fila_revisao"] = pendentes
            st.session_state["idx_revisao"]  = 0
            st.session_state["modo_revisao"] = "completa"
            st.session_state["corretos_rev"] = 0
            st.rerun()
    with col_b:
        if st.button("⚡ Revisão Rápida (8 cards aleatórios)",
                     use_container_width=True,
                     disabled=len(fcs)<3):
            todos = list(fcs.items())
            random.shuffle(todos)
            st.session_state["fila_revisao"] = todos[:8]
            st.session_state["idx_revisao"]  = 0
            st.session_state["modo_revisao"] = "rapida"
            st.session_state["corretos_rev"] = 0
            st.rerun()

    if len(pendentes):
        st.info(f"🃏 **{len(pendentes)}** cartão(ões) para revisar hoje.")
    else:
        st.success("✅ Nenhum flashcard pendente para hoje!")

    # ── Sessão de revisão ─────────────────────────────────────────────────
    fila = st.session_state.get("fila_revisao", [])
    idx  = st.session_state.get("idx_revisao", 0)

    if fila and idx < len(fila):
        st.divider()
        fid, fc = fila[idx]
        mat_nome = mats.get(fc.get("materia_id",""),{}).get("nome","?")
        total_fila = len(fila)

        st.markdown(f"**Cartão {idx+1} de {total_fila}** — {mat_nome}")
        prog = idx / total_fila
        st.progress(prog)

        # Frente
        st.markdown(
            f'<div class="flashcard-frente">❓ {fc["frente"]}</div>',
            unsafe_allow_html=True)
        st.markdown("")

        # Ver verso
        chave_verso = f"verso_visivel_{fid}_{idx}"
        if not st.session_state.get(chave_verso):
            if st.button("👁 Ver Resposta", use_container_width=True):
                st.session_state[chave_verso] = True
                st.rerun()
        else:
            st.markdown(
                f'<div class="flashcard-verso">'
                f'<strong style="color:#2ecc71;">✅ Resposta:</strong><br><br>'
                f'{fc["verso"]}</div>',
                unsafe_allow_html=True)
            st.markdown("")
            st.markdown("**Como foi? Avalie sua facilidade:**")
            c1,c2,c3,c4,c5 = st.columns(5)
            notas = [
                (c1, 1, "1\n😰\nMuito\nDifícil", "#c0392b"),
                (c2, 2, "2\n😟\nDifícil",         "#e67e22"),
                (c3, 3, "3\n😐\nRegular",          "#f1c40f"),
                (c4, 4, "4\n😊\nFácil",            "#27ae60"),
                (c5, 5, "5\n🚀\nMuito\nFácil",     "#1abc9c"),
            ]
            for col, nota, txt, cor in notas:
                with col:
                    if st.button(txt, key=f"nota_{fid}_{idx}_{nota}",
                                 use_container_width=True):
                        # SM-2
                        i_at = fc.get("intervalo_idx", 0)
                        if nota >= 4:
                            i_novo = min(i_at+1, len(SM2_INTERVALS)-1)
                            st.session_state["corretos_rev"] = \
                                st.session_state.get("corretos_rev",0) + 1
                        elif nota == 3:
                            i_novo = i_at
                        else:
                            i_novo = max(0, i_at-1)
                        fc["proxima_revisao"]  = _add_dias(SM2_INTERVALS[i_novo])
                        fc["intervalo_idx"]    = i_novo
                        fc["total_revisoes"]   = fc.get("total_revisoes",0) + 1
                        fc["facilidade_media"] = round(
                            fc.get("facilidade_media",3.0)*0.7 + nota*0.3, 2)
                        st.session_state[chave_verso]   = False
                        st.session_state["idx_revisao"] = idx + 1
                        save_d()
                        _atualizar_streak()
                        st.rerun()

    elif fila and idx >= len(fila):
        # Resultado final
        corr  = st.session_state.get("corretos_rev", 0)
        total = len(fila)
        pct   = corr / total * 100 if total else 0
        st.balloons()
        st.success(
            f"🎉 **Sessão concluída!**  "
            f"Acertos: {corr}/{total}  ({pct:.0f}%)")
        if st.button("Fechar resultado"):
            st.session_state["fila_revisao"] = []
            st.session_state["idx_revisao"]  = 0
            st.rerun()

    # ── Criar novo flashcard ──────────────────────────────────────────────
    st.divider()
    with st.expander("➕ Criar Novo Flashcard"):
        with st.form("form_fc", clear_on_submit=True):
            opts = {m["nome"]: mid for mid, m in mats.items()}
            mat_sel = st.selectbox("Matéria", list(opts.keys()) or ["—"])
            frente  = st.text_area("Frente (pergunta/conceito)", height=80)
            verso   = st.text_area("Verso (resposta/definição)", height=100)
            if st.form_submit_button("💾 Criar Flashcard", type="primary"):
                if frente.strip() and verso.strip():
                    fid = _novo_id("FC", fcs)
                    fcs[fid] = {
                        "frente": frente.strip(), "verso": verso.strip(),
                        "materia_id": opts.get(mat_sel,""),
                        "proxima_revisao": _hoje(), "intervalo_idx": 0,
                        "total_revisoes": 0, "facilidade_media": 3.0,
                        "criado_em": _hoje(),
                    }
                    save_d()
                    st.success("✅ Flashcard criado!")
                    st.rerun()

    # ── Lista de flashcards ───────────────────────────────────────────────
    st.divider()
    st.subheader(f"📋 Todos os Flashcards ({len(fcs)})")
    if fcs:
        for fid, fc in list(fcs.items()):
            mat = mats.get(fc.get("materia_id",""),{}).get("nome","?")
            prox = fc.get("proxima_revisao","—")
            dias = _dias_ate(prox) if prox != "—" else 999
            cor_p = "#e74c3c" if dias < 0 else "#f5a623" if dias == 0 else "#9e9e9e"
            with st.expander(f"**{fc['frente'][:60]}**  —  {mat}"):
                st.markdown(f"**Verso:** {fc['verso']}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Revisões", fc.get("total_revisoes",0))
                c2.metric("Facilidade", f"{fc.get('facilidade_media',3.0):.1f}/5")
                c3.markdown(
                    f'<span style="color:{cor_p}">Próxima: {prox}</span>',
                    unsafe_allow_html=True)
                with c4:
                    if st.button("🗑", key=f"del_fc_{fid}"):
                        del fcs[fid]
                        save_d()
                        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  PÁGINA: PLANEJAMENTO
# ═══════════════════════════════════════════════════════════════════════════

_DIAS_SEMANA = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira",
                "Sexta-feira","Sábado","Domingo"]

def _candidatos_pendentes(d: dict) -> list:
    """
    Lista de tópicos não dominados, ordenada por peso (prioridade × dificuldade)
    do maior para o menor — é a aplicação prática do Pareto: tópicos mais
    importantes e mais difíceis sobem para o topo da fila.

    Cada item: (peso, nome_materia, nome_topico, topico_id, aula_ref)
    """
    candidatos = []
    for mid, m in d["materias"].items():
        for tid, tp in m.get("topicos", {}).items():
            if tp.get("status") != "Dominado":
                peso = tp.get("prioridade", 3) * tp.get("dificuldade", 3)
                candidatos.append((peso, m["nome"], tp["nome"], tid,
                                   tp.get("aula_ref", "")))
    candidatos.sort(reverse=True)
    return candidatos

def _distribuir_pela_semana(candidatos: list, dia_atual_idx: int,
                             modo: str) -> dict:
    """
    Distribui os tópicos pendentes pelos dias da semana.

    modo "restante": só preenche de hoje até domingo (dias passados ficam
        vazios/cinza) — útil para quem abre o app no meio da semana e quer
        saber "o que ainda falta esta semana", sem reabrir o que já passou.

    modo "completa": preenche todos os 7 dias, como antes (útil para
        visualizar/planejar a semana inteira de uma vez, ex.: domingo
        à noite planejando a semana toda).

    IMPORTANTE: cada tópico (tid) aparece em NO MÁXIMO um dia da semana.
    Quando há poucos tópicos pendentes, alguns dias ficam "livres" em vez
    de repetir um tópico já mostrado em outro dia — repetir geraria chaves
    de widget duplicadas no Streamlit (mesmo tid renderizado duas vezes na
    mesma tela) e quebraria a página com StreamlitDuplicateElementKey.
    """
    plano = {i: [] for i in range(7)}
    if not candidatos:
        return plano

    if modo == "restante":
        dias_uteis = list(range(dia_atual_idx, 7))
    else:
        dias_uteis = list(range(7))

    n_dias = len(dias_uteis) or 1
    por_d  = max(1, len(candidatos) // n_dias)

    for i, dia_idx in enumerate(dias_uteis):
        sl = candidatos[i*por_d:(i+1)*por_d]
        # Não reaproveitar candidatos[:1] aqui — isso duplicaria um tópico
        # que já apareceu em outro dia. Se não houver candidatos suficientes
        # para preencher este dia, ele simplesmente fica vazio (correto).
        plano[dia_idx] = sl

    return plano

def p_tarefas():
    """
    Página unificada de Planejamento + Sessões + Questões.

    Cada tópico pendente do plano semanal se torna uma "tarefa" clicável.
    Ao expandir, o usuário tem acesso a: status, timer Pomodoro vinculado
    ao tópico, registro de desempenho em questões (acertos/total), criação
    rápida de flashcard e referência de aula — tudo em um único lugar, sem
    precisar trocar de aba no meio do estudo.
    """
    d   = get_d()
    cfg = d["config"]

    # Se o usuário clicou em "Abrir →" em algum card, exibe a janela modal
    # (pop-up) com os detalhes daquela tarefa. Precisa ser chamado logo no
    # início da página para o decorador @st.dialog funcionar corretamente.
    if st.session_state.get("_dialog_tarefa_aberta"):
        _dialog_tarefa(d)

    # Blindagem contra duplicação de widgets: rastreia quais tópicos já
    # foram renderizados nesta execução da página. Se por qualquer motivo
    # (bug futuro, dado inconsistente) o mesmo tid aparecer duas vezes na
    # mesma seção, a segunda ocorrência é ignorada silenciosamente em vez
    # de quebrar a página com StreamlitDuplicateElementKey.
    st.session_state["_tids_renderizados_tarefas"] = set()

    st.markdown('<p class="page-title">✅ Tarefas</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-sub">Planejamento, tempo de estudo e desempenho em '
        'questões — tudo em um único lugar, por tópico.</p>',
        unsafe_allow_html=True)

    # ── Configurações ────────────────────────────────────────────────────
    with st.expander("⚙ Configurações"):
        with st.form("form_cfg"):
            c1,c2,c3,c4 = st.columns(4)
            with c1: hpd  = st.number_input("Horas/dia", 1, 12,
                                              cfg.get("horas_por_dia",4))
            with c2: meta = st.number_input("Meta semanal (h)", 5, 84,
                                             cfg.get("meta_semanal_horas",28))
            with c3: tec  = st.selectbox("Técnica Pomodoro",
                                          ["25/5","50/10"],
                                          index=0 if "25" in cfg.get("tecnica","25/5") else 1)
            with c4: nome = st.text_input("Seu nome",
                                           cfg.get("usuario","Candidato"))
            if st.form_submit_button("💾 Salvar"):
                cfg["horas_por_dia"]      = hpd
                cfg["meta_semanal_horas"] = meta
                cfg["tecnica"]            = tec
                cfg["usuario"]            = nome or "Candidato"
                save_d()
                st.success("✅ Configurações salvas!")
                st.rerun()

    # ── Quadro explicativo do critério de geração ───────────────────────────
    with st.expander("❓ Como esse plano é gerado? (clique para entender o critério)"):
        st.markdown(
            "O plano não é aleatório — ele segue uma lógica de "
            "**priorização objetiva**, recalculada toda vez que você abre "
            "esta página. Veja as 3 etapas:")
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            st.markdown("""
**① Filtragem**

Tópicos marcados como **"Dominado"** são excluídos do plano.

Só entram na fila os tópicos com status:
- Não estudado
- Em andamento
- Revisar
""")
        with ec2:
            st.markdown("""
**② Cálculo do peso**

Para cada tópico restante:

`peso = prioridade × dificuldade`

Exemplo: prioridade 5 e dificuldade 4
→ peso 20 (mais urgente)

Exemplo: prioridade 3 e dificuldade 2
→ peso 6 (menos urgente)
""")
        with ec3:
            st.markdown("""
**③ Ordenação e distribuição**

A fila é ordenada do **maior peso para o menor**
(lógica de Pareto: o que é mais importante e
mais difícil aparece primeiro).

Depois é dividida nos dias da semana — ou só nos
dias restantes, se o modo "Só o que resta" estiver
selecionado.
""")
        st.caption(
            "🔄 **Atualização:** o plano é recalculado a cada vez que você "
            "visita esta página — não é fixo por semana. Se você marcar um "
            "tópico como 'Dominado' ou mudar sua prioridade/dificuldade, a "
            "posição dele na fila muda imediatamente, sem esperar a virada "
            "da semana.")
        st.caption(
            "🎓 **Referência de aula/material:** em 'Matérias e Tópicos', cada "
            "tópico tem um campo onde você anota a aula do seu curso (ex: "
            "'Aula 09 — Pontuação'). Uma vez preenchido, essa referência "
            "aparece nos cards de tarefa abaixo.")
        st.caption(
            "✅ **Clique em qualquer tarefa abaixo** para expandir e acessar "
            "timer Pomodoro, registro de questões e criação de flashcard — "
            "tudo vinculado àquele tópico específico.")

    st.divider()

    # ── Parâmetros de exibição do plano ─────────────────────────────────────
    ms, mp = (25, 5) if "25" in cfg.get("tecnica","25/5") else (50, 10)
    hpd    = cfg.get("horas_por_dia", 4)
    ciclos = max(1, int(hpd * 60 / (ms + mp)))

    hj            = datetime.date.today()
    dia_atual_idx = hj.weekday()  # 0 = Segunda ... 6 = Domingo

    candidatos = _candidatos_pendentes(d)

    col_tit, col_modo = st.columns([3,2])
    with col_tit:
        st.subheader("📅 Tarefas da Semana")
        st.caption(f"Hoje é **{_DIAS_SEMANA[dia_atual_idx]}**  •  "
                   f"Baseado em Pareto (prioridade × dificuldade)  •  "
                   f"{ciclos} ciclos Pomodoro ({ms}'+{mp}') por dia")
    with col_modo:
        modo_label = st.radio(
            "Modo de visualização",
            ["Só o que resta esta semana", "Semana completa (Seg–Dom)"],
            index=0,
            label_visibility="collapsed",
        )
        modo = "restante" if "resta" in modo_label else "completa"

    if not candidatos:
        st.info("Nenhum tópico pendente! Você dominou tudo ou não cadastrou tópicos ainda.")
    else:
        plano = _distribuir_pela_semana(candidatos, dia_atual_idx, modo)

        # ── Renderização dos 7 dias, cada tópico é um expander clicável ─────
        cols_dias = st.columns(7)
        for i, (dia, col) in enumerate(zip(_DIAS_SEMANA, cols_dias)):
            with col:
                eh_hoje    = (i == dia_atual_idx)
                eh_passado = (modo == "restante") and (i < dia_atual_idx)

                if eh_hoje:
                    st.markdown(
                        '<div style="background:#e94560;border-radius:6px;'
                        'padding:4px 6px;text-align:center;font-size:11px;'
                        'font-weight:700;color:white;margin-bottom:4px;">'
                        '🔥 HOJE</div>', unsafe_allow_html=True)
                st.markdown(f"**{dia[:3]}**")

                if eh_passado:
                    st.markdown(
                        '<div style="color:#5a5a6e;font-size:11px;'
                        'padding:8px 0;">— dia já passou —</div>',
                        unsafe_allow_html=True)
                    continue

                sl = plano.get(i, [])
                if not sl:
                    st.caption("Livre / revisão")
                    continue

                for _, mat, top, tid, aula_ref in sl:
                    _render_tarefa_card(d, tid, mat, top, aula_ref, eh_hoje,
                                        key_suffix=f"d{i}")
                st.caption(f"⏱ {ciclos}x{ms}'")

        st.divider()
        if modo == "restante":
            st.caption(
                "💡 Modo 'restante': os tópicos já se redistribuem "
                "automaticamente entre hoje e domingo. Dias passados não "
                "são reabertos — o que não foi estudado neles entra na "
                "redistribuição dos dias seguintes na próxima vez que você "
                "abrir esta página.")
        else:
            st.caption(
                "💡 Modo 'completa': mostra a semana inteira de Segunda a "
                "Domingo, útil para planejar com antecedência.")

    # ── Revisões pendentes hoje (spaced repetition de tópico) ──────────────
    st.divider()
    st.subheader("🔁 Revisões Pendentes Hoje")
    pendentes = []
    for mid, m in d["materias"].items():
        for tid, tp in m.get("topicos",{}).items():
            prox = tp.get("proxima_revisao")
            if prox and _dias_ate(prox) <= 0:
                pendentes.append((m["nome"], tp["nome"], tid, tp.get("aula_ref","")))
    if pendentes:
        for mat, top, tid, aula_ref in pendentes:
            _render_tarefa_card(d, tid, mat, top, aula_ref, eh_hoje=False,
                                key_suffix="revisao")
    else:
        st.success("✅ Nenhuma revisão de tópico pendente para hoje!")

    # ── Métricas gerais de tempo estudado ────────────────────────────────────
    st.divider()
    st.subheader("📊 Resumo de Tempo Estudado")
    sess      = d["sessoes"]
    total_min = sum(s["duracao_min"] for s in sess)
    ini_s     = hj - datetime.timedelta(days=hj.weekday())
    min_s     = sum(s["duracao_min"] for s in sess if s["data"] >= ini_s.isoformat())
    min_hj    = sum(s["duracao_min"] for s in sess if s["data"] == _hoje())

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total geral",    f"{total_min//60}h{total_min%60:02d}m")
    c2.metric("Esta semana",    f"{min_s//60}h{min_s%60:02d}m")
    c3.metric("Hoje",           f"{min_hj//60}h{min_hj%60:02d}m")
    c4.metric("Sessões registradas", str(len(sess)))

    with st.expander("➕ Registrar tempo manualmente (sem vincular a um tópico)"):
        with st.form("form_sessao_manual", clear_on_submit=True):
            mats = d["materias"]
            opts = {m["nome"]: mid for mid, m in mats.items()}
            cc1,cc2,cc3 = st.columns([3,1,3])
            with cc1: mat_sel = st.selectbox("Matéria", ["Geral"]+list(opts.keys()))
            with cc2: dur     = st.number_input("Minutos", 5, 300, ms)
            with cc3: nota_s  = st.text_input("Notas (opcional)")
            if st.form_submit_button("✅ Registrar"):
                sess.append({
                    "data": _hoje(), "duracao_min": int(dur),
                    "materia_id": opts.get(mat_sel, ""), "topico_id": "",
                    "notas": nota_s,
                })
                save_d()
                _atualizar_streak()
                st.success(f"✅ {dur} min registrados!")
                st.rerun()


def _render_tarefa_card(d: dict, tid: str, mat_nome: str, top_nome: str,
                         aula_ref: str, eh_hoje: bool, key_suffix: str):
    """
    Renderiza um card-resumo de tarefa com um botão "Abrir". Ao clicar,
    abre uma janela modal (pop-up) via @st.dialog com status, timer
    Pomodoro vinculado ao tópico, registro de questões, criação rápida de
    flashcard e a referência de aula — tudo sobreposto à página, sem
    empurrar o restante do layout para baixo (diferente de um expander).
    """
    # Blindagem: a combinação (tid, key_suffix) deve ser única na execução
    # atual da página. Isso normalmente já é garantido por quem chama esta
    # função (plano semanal nunca repete tid; revisões usa suffix fixo
    # "revisao", que não colide com "d0".."d6") — mas a checagem aqui evita
    # qualquer StreamlitDuplicateElementKey mesmo se um cenário futuro não
    # previsto reintroduzir uma repetição.
    chave_unica = f"{tid}_{key_suffix}"
    vistos = st.session_state.setdefault("_tids_renderizados_tarefas", set())
    if chave_unica in vistos:
        return
    vistos.add(chave_unica)

    mid_alvo, tp_alvo = None, None
    for mid, m in d["materias"].items():
        if tid in m.get("topicos", {}):
            mid_alvo = mid
            tp_alvo  = m["topicos"][tid]
            break
    if tp_alvo is None:
        st.caption(f"⚠ Tópico '{top_nome}' não encontrado (pode ter sido removido).")
        return

    status_atual = tp_alvo.get("status", "Não estudado")
    icone        = STATUS_ICONE.get(status_atual, "○")
    reg          = tp_alvo.setdefault("questoes_registro", [])
    ac_tot       = sum(r.get("acertos",0) for r in reg)
    qt_tot       = sum(r.get("total",0)   for r in reg)
    pct_q        = (ac_tot/qt_tot*100) if qt_tot else None

    aula_txt = f"🎓 {aula_ref}" if aula_ref else ""
    pct_txt  = f"{pct_q:.0f}% ({ac_tot}/{qt_tot})" if pct_q is not None else ""
    key_base = f"{tid}_{key_suffix}"

    # ── Card-resumo clicável (substitui o antigo st.expander) ────────────
    borda = "2px solid #f5a623" if eh_hoje else "1px solid #2d2d4e"
    st.markdown(
        f'<div style="background:#0f3460;border:{borda};border-radius:8px;'
        f'padding:8px 10px;margin:4px 0 2px;font-size:12px;">'
        f'<strong>{icone} {top_nome}</strong><br>'
        f'<span style="color:#9e9e9e;font-size:10px;">{mat_nome}</span>'
        + (f'<br><span style="color:#9e9e9e;font-size:10px;">{aula_txt}</span>' if aula_txt else '')
        + (f'<br><span style="color:#f5a623;font-size:10px;">{pct_txt}</span>' if pct_txt else '')
        + '</div>', unsafe_allow_html=True)

    if st.button("Abrir →", key=f"abrir_{key_base}", use_container_width=True):
        st.session_state["_dialog_tarefa_aberta"] = {
            "tid": tid, "mid": mid_alvo, "mat_nome": mat_nome,
            "top_nome": top_nome, "aula_ref": aula_ref,
            "key_base": key_base,
        }
        st.rerun()


@st.dialog("Detalhes da Tarefa", width="large")
def _dialog_tarefa(d: dict):
    """
    Janela modal (pop-up) com o conteúdo completo de uma tarefa: status,
    timer Pomodoro, registro de questões e criação rápida de flashcard.
    Substitui o antigo conteúdo do st.expander — agora abre sobreposto à
    página em vez de empurrar o layout para baixo.
    """
    ctx = st.session_state.get("_dialog_tarefa_aberta")
    if not ctx:
        st.error("Tarefa não encontrada.")
        return

    tid       = ctx["tid"]
    mid_alvo  = ctx["mid"]
    mat_nome  = ctx["mat_nome"]
    top_nome  = ctx["top_nome"]
    aula_ref  = ctx["aula_ref"]
    key_base  = ctx["key_base"]

    if mid_alvo not in d["materias"] or tid not in d["materias"][mid_alvo].get("topicos", {}):
        st.error("Este tópico não existe mais (pode ter sido removido).")
        return
    tp_alvo = d["materias"][mid_alvo]["topicos"][tid]

    status_atual = tp_alvo.get("status", "Não estudado")
    reg          = tp_alvo.setdefault("questoes_registro", [])
    ac_tot       = sum(r.get("acertos",0) for r in reg)
    qt_tot       = sum(r.get("total",0)   for r in reg)
    pct_q        = (ac_tot/qt_tot*100) if qt_tot else None

    st.markdown(f"### {top_nome}")
    st.caption(f"📚 {mat_nome}" + (f"  •  🎓 {aula_ref}" if aula_ref else ""))
    if pct_q is not None:
        st.caption(f"📝 Aproveitamento acumulado: {pct_q:.0f}% ({ac_tot}/{qt_tot})")

    st.markdown("---")

    # ── Status ────────────────────────────────────────────────────────
    novo_status = st.selectbox(
        "Status", STATUS_LISTA,
        index=STATUS_LISTA.index(status_atual) if status_atual in STATUS_LISTA else 0,
        key=f"status_{key_base}")
    if novo_status != status_atual:
        tp_alvo["status"]         = novo_status
        tp_alvo["ultima_revisao"] = _hoje()
        if novo_status == "Dominado":
            tp_alvo["proxima_revisao"] = _add_dias(30)
        save_d()
        st.rerun()

    st.markdown("---")

    # ── Timer Pomodoro vinculado ao tópico ───────────────────────────
    st.markdown("**⏱ Timer Pomodoro**")
    cfg    = d["config"]
    tec    = cfg.get("tecnica", "25/5")
    ms, mp = (25, 5) if "25" in tec else (50, 10)

    timer_key  = f"timer_ativo_{key_base}"
    inicio_key = f"timer_inicio_{key_base}"

    if timer_key not in st.session_state:
        st.session_state[timer_key] = False

    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        if not st.session_state[timer_key]:
            if st.button("▶ Iniciar", key=f"btn_ini_{key_base}", use_container_width=True):
                st.session_state[timer_key]  = True
                st.session_state[inicio_key] = time.time()
                st.rerun()
        else:
            if st.button("⏹ Parar e Salvar", key=f"btn_parar_{key_base}",
                         use_container_width=True, type="primary"):
                decorrido = int(time.time() - st.session_state.get(inicio_key, time.time()))
                minutos = max(1, decorrido // 60)
                d["sessoes"].append({
                    "data": _hoje(), "duracao_min": minutos,
                    "materia_id": mid_alvo, "topico_id": tid,
                    "notas": f"Tarefa: {top_nome}",
                })
                save_d()
                _atualizar_streak()
                st.session_state[timer_key] = False
                st.success(f"✅ {minutos} min registrados em '{top_nome}'!")
                st.rerun()
    with tc2:
        if st.session_state[timer_key]:
            decorrido = int(time.time() - st.session_state.get(inicio_key, time.time()))
            st.metric("Tempo decorrido", f"{decorrido//60:02d}:{decorrido%60:02d}")
        else:
            st.caption(f"Ciclo sugerido: {ms} min")
    with tc3:
        if st.session_state[timer_key]:
            if st.button("🔄 Atualizar", key=f"btn_refresh_{key_base}",
                         use_container_width=True):
                st.rerun()

    if st.session_state[timer_key]:
        st.caption("⏳ Timer rodando — clique em 'Atualizar' para ver o "
                  "tempo avançar, ou 'Parar e Salvar' quando terminar.")

    st.markdown("---")

    # ── Registro de desempenho em questões ───────────────────────────
    st.markdown("**📝 Registro de Questões**")
    with st.form(f"form_questoes_{key_base}", clear_on_submit=True):
        qc1, qc2 = st.columns(2)
        with qc1: novos_acertos = st.number_input("Acertos", 0, 999, 0,
                                                   key=f"ac_{key_base}")
        with qc2: novo_total    = st.number_input("Total de questões", 0, 999, 0,
                                                   key=f"tt_{key_base}")
        if st.form_submit_button("💾 Registrar Desempenho"):
            if novo_total > 0 and novos_acertos <= novo_total:
                reg.append({
                    "data": _hoje(), "acertos": int(novos_acertos),
                    "total": int(novo_total),
                })
                save_d()
                st.success(f"✅ {novos_acertos}/{novo_total} registrado!")
                st.rerun()
            elif novo_total == 0:
                st.warning("Informe o total de questões resolvidas.")
            else:
                st.warning("Acertos não pode ser maior que o total.")

    if reg:
        resumo = (f"Histórico: {len(reg)} registro(s)  •  "
                 f"Acumulado: {ac_tot}/{qt_tot} ({pct_q:.0f}%)"
                 if qt_tot else f"Histórico: {len(reg)} registro(s)")
        st.caption(resumo)
        for r in reversed(reg[-5:]):
            st.caption(f"  {r['data']} — {r['acertos']}/{r['total']}")

    st.markdown("---")

    # ── Criar flashcard rápido a partir do tópico ────────────────────
    st.markdown("**🃏 Criar Flashcard a partir deste tópico**")
    with st.form(f"form_fc_rapido_{key_base}", clear_on_submit=True):
        fc_frente = st.text_input("Frente (pergunta)",
                                   placeholder=f"ex: O que é {top_nome}?",
                                   key=f"fcf_{key_base}")
        fc_verso  = st.text_area("Verso (resposta)", height=80,
                                  key=f"fcv_{key_base}")
        if st.form_submit_button("🃏 Criar Flashcard"):
            if fc_frente.strip() and fc_verso.strip():
                fid = _novo_id("FC", d["flashcards"])
                d["flashcards"][fid] = {
                    "frente": fc_frente.strip(), "verso": fc_verso.strip(),
                    "materia_id": mid_alvo,
                    "proxima_revisao": _hoje(), "intervalo_idx": 0,
                    "total_revisoes": 0, "facilidade_media": 3.0,
                    "criado_em": _hoje(),
                }
                save_d()
                st.success("✅ Flashcard criado! Veja em 'Flashcards'.")
                st.rerun()
            else:
                st.warning("Preencha frente e verso para criar o flashcard.")

    st.markdown("---")
    if st.button("✖ Fechar", use_container_width=True):
        st.session_state["_dialog_tarefa_aberta"] = None
        st.rerun()



# ═══════════════════════════════════════════════════════════════════════════
#  PÁGINA: ANÁLISE / ESTATÍSTICA SEMANAL
# ═══════════════════════════════════════════════════════════════════════════

def _coletar_registros_questoes(d: dict) -> list:
    """
    Percorre todas as matérias/tópicos e retorna uma lista plana de
    registros de desempenho, cada um já enriquecido com o contexto
    (matéria, tópico, dificuldade, prioridade, aula_ref). Isso evita
    repetir a navegação da estrutura aninhada em cada função de análise.

    Cada item: dict com chaves
        data, acertos, total, materia_id, materia_nome,
        topico_id, topico_nome, dificuldade, prioridade, aula_ref
    """
    registros = []
    for mid, m in d.get("materias", {}).items():
        for tid, tp in m.get("topicos", {}).items():
            for r in tp.get("questoes_registro", []):
                registros.append({
                    "data":        r.get("data", ""),
                    "acertos":     r.get("acertos", 0),
                    "total":       r.get("total", 0),
                    "materia_id":  mid,
                    "materia_nome":m.get("nome", "?"),
                    "topico_id":   tid,
                    "topico_nome": tp.get("nome", "?"),
                    "dificuldade": tp.get("dificuldade", 3),
                    "prioridade":  tp.get("prioridade", 3),
                    "aula_ref":    tp.get("aula_ref", ""),
                })
    return registros

def _filtrar_por_periodo(registros: list, inicio_iso: str, fim_iso: str) -> list:
    """Filtra registros cuja data está no intervalo [inicio, fim], inclusive."""
    return [r for r in registros if inicio_iso <= r["data"] <= fim_iso]

def _agregar_por_materia(registros: list) -> dict:
    """
    Agrega acertos/total por matéria.
    Retorna: {materia_nome: {"acertos": int, "total": int, "pct": float,
                              "n_registros": int}}
    """
    agg = {}
    for r in registros:
        nome = r["materia_nome"]
        a = agg.setdefault(nome, {"acertos": 0, "total": 0, "n_registros": 0})
        a["acertos"]     += r["acertos"]
        a["total"]       += r["total"]
        a["n_registros"] += 1
    for nome, a in agg.items():
        a["pct"] = (a["acertos"] / a["total"] * 100) if a["total"] else 0.0
    return agg

def _agregar_por_topico(registros: list) -> dict:
    """
    Agrega acertos/total por tópico (chave = topico_id), preservando
    contexto de matéria, dificuldade, prioridade e aula_ref para uso
    posterior na identificação de pontos fracos.
    """
    agg = {}
    for r in registros:
        tid = r["topico_id"]
        a = agg.setdefault(tid, {
            "topico_nome": r["topico_nome"], "materia_nome": r["materia_nome"],
            "dificuldade": r["dificuldade"], "prioridade": r["prioridade"],
            "aula_ref": r["aula_ref"], "acertos": 0, "total": 0, "n_registros": 0,
        })
        a["acertos"]     += r["acertos"]
        a["total"]       += r["total"]
        a["n_registros"] += 1
    for tid, a in agg.items():
        a["pct"] = (a["acertos"] / a["total"] * 100) if a["total"] else 0.0
    return agg

def _identificar_pontos_fracos(agg_topico: dict, min_questoes: int = 3,
                                limiar_pct: float = 70.0) -> list:
    """
    Identifica tópicos com desempenho abaixo do limiar, exigindo um
    número mínimo de questões respondidas para evitar julgar um tópico
    a partir de uma amostra pequena (ex: 1 questão errada = 0%, o que
    distorceria a análise).

    Retorna lista ordenada do PIOR para o melhor desempenho, cada item:
        (pct, topico_nome, materia_nome, acertos, total, dificuldade,
         prioridade, aula_ref)
    """
    fracos = []
    for tid, a in agg_topico.items():
        if a["total"] >= min_questoes and a["pct"] < limiar_pct:
            fracos.append((
                a["pct"], a["topico_nome"], a["materia_nome"],
                a["acertos"], a["total"], a["dificuldade"],
                a["prioridade"], a["aula_ref"],
            ))
    fracos.sort(key=lambda x: x[0])  # pior desempenho primeiro
    return fracos

def _classificar_prioridade_revisao(pct: float, prioridade: int,
                                     dificuldade: int) -> tuple:
    """
    Classifica a urgência de revisão de um ponto fraco combinando:
    - quão baixo é o desempenho (pct)
    - quão importante é o tópico no edital (prioridade)
    - quão difícil ele é (dificuldade)

    Retorna (label, cor) para exibição.
    """
    score = (100 - pct) * (prioridade / 5) * (dificuldade / 5)
    if score >= 35:
        return "🔴 Urgente", "#e74c3c"
    elif score >= 18:
        return "🟠 Alta", "#f5a623"
    else:
        return "🟡 Moderada", "#f1c40f"


def p_analise():
    d = get_d()

    st.markdown('<p class="page-title">📈 Análise e Estatística Semanal</p>',
                unsafe_allow_html=True)
    st.markdown(
        '<p class="page-sub">Desempenho em questões por matéria e tópico, '
        'com identificação automática dos pontos que mais precisam de '
        'revisão.</p>', unsafe_allow_html=True)

    registros_todos = _coletar_registros_questoes(d)

    if not registros_todos:
        st.info(
            "Nenhum registro de questões ainda. Resolva questões dentro de "
            "uma tarefa (aba '✅ Tarefas' → expandir um tópico → "
            "'Registro de Questões') para começar a gerar estatísticas aqui.")
        return

    # ── Seletor de período ───────────────────────────────────────────────
    hj       = datetime.date.today()
    ini_sem  = hj - datetime.timedelta(days=hj.weekday())
    fim_sem  = ini_sem + datetime.timedelta(days=6)

    col_per, col_info = st.columns([2,3])
    with col_per:
        periodo_label = st.radio(
            "Período de análise",
            ["Esta semana", "Últimos 7 dias", "Desde o início"],
            horizontal=True, label_visibility="collapsed")

    if periodo_label == "Esta semana":
        ini_iso, fim_iso = ini_sem.isoformat(), fim_sem.isoformat()
        desc_periodo = f"{ini_sem.strftime('%d/%m')} a {fim_sem.strftime('%d/%m')} (semana atual)"
    elif periodo_label == "Últimos 7 dias":
        ini_iso = (hj - datetime.timedelta(days=6)).isoformat()
        fim_iso = hj.isoformat()
        desc_periodo = "últimos 7 dias corridos"
    else:
        ini_iso, fim_iso = "0000-01-01", "9999-12-31"
        desc_periodo = "todo o histórico"

    with col_info:
        st.caption(f"📅 Mostrando: **{desc_periodo}**")

    registros = _filtrar_por_periodo(registros_todos, ini_iso, fim_iso)

    if not registros:
        st.warning(
            f"Nenhum registro de questões no período selecionado "
            f"({desc_periodo}). Tente 'Desde o início' para ver todo o "
            f"histórico.")
        return

    # ── KPIs gerais do período ───────────────────────────────────────────
    total_ac  = sum(r["acertos"] for r in registros)
    total_qt  = sum(r["total"]   for r in registros)
    pct_geral = (total_ac/total_qt*100) if total_qt else 0
    n_topicos_trabalhados = len({r["topico_id"] for r in registros})

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Questões resolvidas", f"{total_qt}")
    c2.metric("Acertos",             f"{total_ac}")
    c3.metric("Aproveitamento geral", f"{pct_geral:.0f}%")
    c4.metric("Tópicos trabalhados", f"{n_topicos_trabalhados}")

    cor_geral = "#2ecc71" if pct_geral>=70 else "#f5a623" if pct_geral>=50 else "#e74c3c"
    st.markdown(_barra_html(pct_geral/100, cor_geral, 14), unsafe_allow_html=True)

    st.divider()

    # ── Desempenho por matéria ───────────────────────────────────────────
    st.subheader("📊 Desempenho por Matéria")
    agg_mat = _agregar_por_materia(registros)
    agg_mat_ordenado = sorted(agg_mat.items(), key=lambda x: x[1]["pct"])

    try:
        import pandas as pd
        df_mat = pd.DataFrame([
            {"Matéria": nome, "Aproveitamento (%)": round(a["pct"],1)}
            for nome, a in sorted(agg_mat.items(), key=lambda x: -x[1]["pct"])
        ]).set_index("Matéria")
        st.bar_chart(df_mat, color="#4ecdc4")
    except ImportError:
        pass

    for nome, a in agg_mat_ordenado:
        cor = "#2ecc71" if a["pct"]>=70 else "#f5a623" if a["pct"]>=50 else "#e74c3c"
        col_n, col_b = st.columns([2,5])
        with col_n:
            st.markdown(f"**{nome}**")
            st.caption(f"{a['acertos']}/{a['total']} questões  •  {a['n_registros']} registro(s)")
        with col_b:
            st.markdown(_barra_html(a["pct"]/100, cor, 12), unsafe_allow_html=True)
            st.caption(f"{a['pct']:.0f}%")

    st.divider()

    # ── Pontos fracos identificados ──────────────────────────────────────
    st.subheader("🎯 Pontos Fracos Identificados")
    st.caption(
        "Tópicos com pelo menos 3 questões respondidas e aproveitamento "
        "abaixo de 70% — esses são os candidatos prioritários para revisão.")

    agg_top = _agregar_por_topico(registros)
    fracos  = _identificar_pontos_fracos(agg_top, min_questoes=3, limiar_pct=70.0)

    if not fracos:
        st.success(
            "✅ Nenhum ponto fraco identificado com os critérios atuais "
            "(mínimo de 3 questões e abaixo de 70%). Ou seu desempenho está "
            "consistente, ou ainda faltam registros suficientes por tópico "
            "para uma análise confiável.")
    else:
        for pct, top_nome, mat_nome, ac, tot, dif, prio, aula_ref in fracos:
            label_urg, cor_urg = _classificar_prioridade_revisao(pct, prio, dif)
            aula_txt = f"  🎓 {aula_ref}" if aula_ref else ""
            st.markdown(
                f'<div style="background:#0f3460;border-left:4px solid {cor_urg};'
                f'border-radius:8px;padding:12px 16px;margin:6px 0;">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;">'
                f'<strong style="font-size:14px;">{top_nome}</strong>'
                f'<span style="color:{cor_urg};font-weight:700;font-size:12px;">'
                f'{label_urg}</span>'
                f'</div>'
                f'<div style="color:#9e9e9e;font-size:12px;margin-top:4px;">'
                f'{mat_nome}{aula_txt}'
                f'</div>'
                f'<div style="color:#e74c3c;font-weight:600;font-size:13px;'
                f'margin-top:6px;">{pct:.0f}% de aproveitamento  '
                f'({ac}/{tot} questões)</div>'
                f'</div>', unsafe_allow_html=True)

        st.caption(
            "💡 **Como a urgência é calculada:** combina o quão baixo é seu "
            "aproveitamento com a prioridade e dificuldade do tópico no "
            "edital. Um tópico de prioridade 5 com 40% de acerto é mais "
            "urgente que um de prioridade 2 com o mesmo percentual.")

    st.divider()

    # ── Recomendação de conteúdos a revisar/estudar mais ─────────────────
    st.subheader("📚 Recomendação de Revisão")
    if fracos:
        top5 = fracos[:5]
        st.markdown(
            "Com base nos pontos fracos acima, priorize revisar, **nesta ordem**:")
        for i, (pct, top_nome, mat_nome, ac, tot, dif, prio, aula_ref) in enumerate(top5, 1):
            aula_txt = f" (consulte: {aula_ref})" if aula_ref else ""
            st.markdown(
                f"{i}. **{top_nome}** — _{mat_nome}_ — "
                f"{pct:.0f}% de acerto{aula_txt}")

        st.markdown("")
        if st.button("➕ Adicionar estes tópicos como prioridade máxima",
                     help="Define prioridade 5 e status 'Revisar' para os "
                          "tópicos listados acima, fazendo-os aparecer no "
                          "topo do plano semanal."):
            ajustados = 0
            nomes_top5 = {top_nome for _, top_nome, *_ in top5}
            for mid, m in d["materias"].items():
                for tid, tp in m.get("topicos", {}).items():
                    if tp["nome"] in nomes_top5:
                        tp["prioridade"] = 5
                        if tp.get("status") != "Dominado":
                            tp["status"] = "Revisar"
                        ajustados += 1
            save_d()
            st.success(f"✅ {ajustados} tópico(s) marcados como prioridade "
                      f"máxima! Veja o plano atualizado em 'Tarefas'.")
            st.rerun()
    else:
        st.info(
            "Continue registrando seu desempenho em questões dentro das "
            "tarefas para receber recomendações personalizadas de revisão "
            "aqui.")

# ═══════════════════════════════════════════════════════════════════════════
#  PÁGINA: FEYNMAN
# ═══════════════════════════════════════════════════════════════════════════

def p_feynman():
    d    = get_d()
    mats = d["materias"]

    st.markdown('<p class="page-title">✍ Técnica de Feynman</p>',
                unsafe_allow_html=True)
    st.info(
        "**Como usar:** escolha um tópico, explique-o com suas próprias palavras "
        "como se ensinasse a alguém que nunca ouviu falar. "
        "Onde você travar, há uma lacuna no seu entendimento — volte ao material.")

    if not mats:
        st.warning("Cadastre matérias e tópicos primeiro.")
        return

    col1, col2 = st.columns(2)
    with col1:
        mat_sel = st.selectbox("Matéria", list(m["nome"] for m in mats.values()))
    mid_sel = next((mid for mid, m in mats.items() if m["nome"] == mat_sel), None)

    tops_dict = {}
    if mid_sel:
        tops_dict = {tp["nome"]: tid
                     for tid, tp in mats[mid_sel].get("topicos",{}).items()}
    with col2:
        top_sel = st.selectbox("Tópico", list(tops_dict.keys()) or ["—"])

    tid_sel = tops_dict.get(top_sel)

    # Ver explicação salva
    feynman_salvo = d["feynman"].get(tid_sel)
    if feynman_salvo:
        with st.expander(
            f"📖 Explicação anterior — {feynman_salvo.get('data','?')}"):
            st.markdown(feynman_salvo["texto"])

    st.markdown("**Escreva sua explicação agora:**")
    texto = st.text_area(
        f"Explique '{top_sel}' com suas próprias palavras:",
        height=250,
        placeholder="Use linguagem simples. Evite termos técnicos que você não consegue definir...",
        label_visibility="collapsed")

    if st.button("💾 Salvar Explicação", type="primary"):
        if texto.strip() and tid_sel:
            d["feynman"][tid_sel] = {
                "texto": texto.strip(), "data": _hoje(),
                "topico": top_sel, "materia": mat_sel,
            }
            save_d()
            st.success("✅ Explicação salva! Revise onde travou e volte ao material.")
        else:
            st.warning("Escreva a explicação antes de salvar.")

    # Histórico de explicações
    if d["feynman"]:
        st.divider()
        st.subheader("📚 Explicações Salvas")
        for tid, f in d["feynman"].items():
            with st.expander(f"**{f.get('topico','?')}** — {f.get('materia','?')} — {f.get('data','?')}"):
                st.markdown(f["texto"])

# ═══════════════════════════════════════════════════════════════════════════
#  PÁGINA: EXPORTAR / IMPORTAR
# ═══════════════════════════════════════════════════════════════════════════

def p_exportar():
    d = get_d()
    st.markdown('<p class="page-title">💾 Exportar / Importar</p>',
                unsafe_allow_html=True)

    tab_exp, tab_imp = st.tabs(["📤 Exportar", "📥 Importar"])

    with tab_exp:
        st.subheader("Exportar JSON — backup completo")
        json_str = json.dumps(d, ensure_ascii=False, indent=2)
        st.download_button(
            label="⬇️ Baixar dados_estudos.json",
            data=json_str.encode("utf-8"),
            file_name=f"backup_estudos_{_hoje()}.json",
            mime="application/json",
            use_container_width=True,
        )

        st.divider()
        st.subheader("Exportar Flashcards — CSV (abre no Excel)")
        linhas = ["ID,Matéria,Frente,Verso,Revisões,Facilidade,Próxima Revisão"]
        for fid, fc in d["flashcards"].items():
            mat = d["materias"].get(fc.get("materia_id",""),{}).get("nome","?")
            linhas.append(
                f'{fid},"{mat}","{fc["frente"]}","{fc["verso"]}",'
                f'{fc.get("total_revisoes",0)},'
                f'{fc.get("facilidade_media",3.0):.1f},'
                f'{fc.get("proxima_revisao","")}')
        csv_str = "\n".join(linhas)
        st.download_button(
            label="⬇️ Baixar flashcards.csv",
            data=csv_str.encode("utf-8-sig"),
            file_name=f"flashcards_{_hoje()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with tab_imp:
        st.subheader("Importar Backup JSON")
        st.warning("⚠️ A importação substituirá todos os dados atuais.")
        arq = st.file_uploader("Selecione o arquivo JSON", type=["json"])
        if arq:
            try:
                imp = json.load(arq)
                st.session_state["d"] = imp
                save_d()
                st.success("✅ Dados importados com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao importar: {e}")

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — ROTEADOR
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if not _tela_login():
        return  # Aguardando login

    pagina = _sidebar()

    # Override de navegação (ex: botão revisão rápida no dashboard)
    if "pagina_override" in st.session_state:
        pagina = st.session_state.pop("pagina_override")

    rotas = {
        "🏠 Dashboard":          p_dashboard,
        "📚 Matérias e Tópicos": p_materias,
        "🃏 Flashcards":         p_flashcards,
        "✅ Tarefas":            p_tarefas,
        "📈 Análise":            p_analise,
        "✍ Feynman":            p_feynman,
        "💾 Exportar":           p_exportar,
    }
    rotas.get(pagina, p_dashboard)()

if __name__ == "__main__":
    main()
