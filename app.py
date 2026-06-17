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
import json, os, datetime, random, math
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
             "🃏 Flashcards", "📅 Planejamento",
             "⏱ Sessões", "📝 Questões",
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
                    t_col1, t_col2, t_col3, t_col4 = st.columns([4, 2, 2, 2])
                    with t_col1:
                        st.markdown(tp["nome"])
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
                if st.form_submit_button("Adicionar Tópico"):
                    if nome_t.strip():
                        tid = _novo_id("T", tops)
                        tops[tid] = {
                            "nome": nome_t.strip(), "dificuldade": dif_t,
                            "prioridade": prio_t, "status": "Não estudado",
                            "ultima_revisao": None, "proxima_revisao": None,
                            "intervalo_idx": 0, "total_revisoes": 0,
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

def p_planejamento():
    d   = get_d()
    cfg = d["config"]

    st.markdown('<p class="page-title">📅 Planejamento de Estudos</p>',
                unsafe_allow_html=True)

    # Configurações
    with st.expander("⚙ Configurações", expanded=True):
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

    st.divider()

    # Plano semanal
    ms, mp = (25, 5) if "25" in cfg.get("tecnica","25/5") else (50, 10)
    hpd    = cfg.get("horas_por_dia", 4)
    ciclos = max(1, int(hpd * 60 / (ms + mp)))

    candidatos = []
    for mid, m in d["materias"].items():
        for tid, tp in m.get("topicos",{}).items():
            if tp.get("status") != "Dominado":
                peso = tp.get("prioridade",3) * tp.get("dificuldade",3)
                candidatos.append((peso, m["nome"], tp["nome"]))
    candidatos.sort(reverse=True)

    dias  = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira",
              "Sexta-feira","Sábado","Domingo"]
    por_d = max(1, len(candidatos)//7) if candidatos else 1

    st.subheader("📅 Plano da Semana — gerado automaticamente")
    st.caption(f"Baseado em Pareto: tópicos ordenados por prioridade × dificuldade  |  "
               f"{ciclos} ciclos Pomodoro ({ms}'+{mp}') por dia  =  {ciclos*ms} min de estudo")

    if not candidatos:
        st.info("Nenhum tópico pendente! Você dominou tudo ou não cadastrou tópicos ainda.")
        return

    cols_dias = st.columns(7)
    for i, (dia, col) in enumerate(zip(dias, cols_dias)):
        sl = candidatos[i*por_d:(i+1)*por_d]
        if not sl: sl = candidatos[:1]
        with col:
            st.markdown(f"**{dia[:3]}**")
            for _, mat, top in sl:
                st.markdown(
                    f'<div style="background:#0f3460;border-radius:8px;'
                    f'padding:8px;margin:4px 0;font-size:12px;">'
                    f'<strong>{top[:30]}</strong><br>'
                    f'<span style="color:#9e9e9e;font-size:10px;">{mat[:20]}</span>'
                    f'</div>',
                    unsafe_allow_html=True)
            st.caption(f"⏱ {ciclos}x{ms}'")

    # Revisões pendentes hoje
    st.divider()
    st.subheader("🔁 Revisões Pendentes Hoje")
    pendentes = []
    for mid, m in d["materias"].items():
        for tid, tp in m.get("topicos",{}).items():
            prox = tp.get("proxima_revisao")
            if prox and _dias_ate(prox) <= 0:
                pendentes.append((m["nome"], tp["nome"]))
    if pendentes:
        for mat, top in pendentes:
            st.markdown(f"- **{top}** — _{mat}_")
    else:
        st.success("✅ Nenhuma revisão de tópico pendente para hoje!")

# ═══════════════════════════════════════════════════════════════════════════
#  PÁGINA: SESSÕES
# ═══════════════════════════════════════════════════════════════════════════

def p_sessoes():
    d    = get_d()
    sess = d["sessoes"]
    mats = d["materias"]
    cfg  = d["config"]

    st.markdown('<p class="page-title">⏱ Sessões de Estudo</p>',
                unsafe_allow_html=True)

    # Timer Pomodoro simples (contagem regressiva via JS)
    tec    = cfg.get("tecnica","25/5")
    ms, mp = (25,5) if "25" in tec else (50,10)

    st.subheader("⏱ Timer Pomodoro")
    st.markdown(
        f"""
        <div style="background:#0f3460;border-radius:12px;padding:20px;text-align:center;">
            <div id="timer" style="font-size:64px;font-weight:700;
                color:#f5a623;font-family:monospace;">{ms:02d}:00</div>
            <div style="color:#9e9e9e;margin:8px 0;">
                Estudo: {ms} min  |  Pausa: {mp} min
            </div>
            <button onclick="iniciar()" id="btn_ini"
                style="background:#2ecc71;color:white;border:none;
                       border-radius:8px;padding:10px 24px;
                       font-size:16px;font-weight:600;
                       margin:6px;cursor:pointer;">▶ Iniciar</button>
            <button onclick="pausar()"
                style="background:#f5a623;color:white;border:none;
                       border-radius:8px;padding:10px 24px;
                       font-size:16px;font-weight:600;
                       margin:6px;cursor:pointer;">⏸ Pausar</button>
            <button onclick="parar()"
                style="background:#e74c3c;color:white;border:none;
                       border-radius:8px;padding:10px 24px;
                       font-size:16px;font-weight:600;
                       margin:6px;cursor:pointer;">⏹ Parar</button>
        </div>
        <script>
        var _total = {ms}*60;
        var _rest  = _total;
        var _ativo = false;
        var _pausa = false;
        var _timer = null;

        function fmt(s){{
            var m=Math.floor(s/60), sec=s%60;
            return (m<10?'0':'')+m+':'+(sec<10?'0':'')+sec;
        }}

        function iniciar(){{
            if(_ativo) return;
            _ativo=true; _pausa=false;
            _timer=setInterval(function(){{
                if(!_pausa){{
                    _rest--;
                    document.getElementById('timer').innerText=fmt(_rest);
                    if(_rest<=0){{
                        clearInterval(_timer);
                        _ativo=false;
                        document.getElementById('timer').innerText='00:00';
                        document.getElementById('timer').style.color='#2ecc71';
                        alert('✅ Sessão de {ms} min concluída! Registre sua sessão abaixo.');
                    }}
                }}
            }},1000);
        }}

        function pausar(){{
            _pausa=!_pausa;
        }}

        function parar(){{
            clearInterval(_timer);
            _ativo=false; _pausa=false;
            _rest={ms}*60;
            document.getElementById('timer').innerText='{ms:02d}:00';
            document.getElementById('timer').style.color='#f5a623';
        }}
        </script>
        """,
        unsafe_allow_html=True,
    )

    # Registrar sessão manual
    st.divider()
    st.subheader("📝 Registrar Sessão")
    with st.form("form_sessao", clear_on_submit=True):
        opts = {m["nome"]: mid for mid, m in mats.items()}
        c1,c2,c3 = st.columns([3,1,3])
        with c1: mat_sel = st.selectbox("Matéria", ["Geral"]+list(opts.keys()))
        with c2: dur     = st.number_input("Minutos", 5, 300, ms)
        with c3: nota_s  = st.text_input("Notas (opcional)")
        if st.form_submit_button("✅ Registrar", type="primary"):
            mid = opts.get(mat_sel, "")
            sess.append({
                "data": _hoje(), "duracao_min": int(dur),
                "materia_id": mid, "notas": nota_s,
            })
            save_d()
            _atualizar_streak()
            st.success(f"✅ Sessão de {dur} min registrada!")
            st.rerun()

    # KPIs
    st.divider()
    total_min = sum(s["duracao_min"] for s in sess)
    hj        = datetime.date.today()
    ini_s     = hj - datetime.timedelta(days=hj.weekday())
    min_s     = sum(s["duracao_min"] for s in sess
                    if s["data"] >= ini_s.isoformat())
    min_hj    = sum(s["duracao_min"] for s in sess if s["data"] == _hoje())

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total geral",     f"{total_min//60}h{total_min%60:02d}m")
    c2.metric("Esta semana",     f"{min_s//60}h{min_s%60:02d}m")
    c3.metric("Hoje",            f"{min_hj//60}h{min_hj%60:02d}m")
    c4.metric("Sessões totais",  str(len(sess)))

    # Histórico
    st.divider()
    st.subheader("📋 Últimas 20 Sessões")
    for s in sorted(sess, key=lambda x: x["data"], reverse=True)[:20]:
        mat = mats.get(s.get("materia_id",""),{}).get("nome","Geral")
        st.markdown(
            f'<div style="background:#0f3460;border-radius:8px;'
            f'padding:10px 14px;margin:4px 0;font-size:13px;">'
            f'<strong>{s["data"]}</strong>  ·  {mat}  ·  '
            f'<span style="color:#f5a623;">{s["duracao_min"]} min</span>'
            f'{("  ·  " + s["notas"][:50]) if s.get("notas") else ""}'
            f'</div>',
            unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  PÁGINA: BANCO DE QUESTÕES
# ═══════════════════════════════════════════════════════════════════════════

def p_questoes():
    d    = get_d()
    qs   = d["questoes"]
    mats = d["materias"]

    st.markdown('<p class="page-title">📝 Banco de Questões</p>',
                unsafe_allow_html=True)

    tab_sim, tab_add, tab_lista = st.tabs(
        ["▶ Simulado", "➕ Adicionar Questão", "📋 Listar Questões"])

    # ── Simulado ──────────────────────────────────────────────────────────
    with tab_sim:
        if not qs:
            st.info("Adicione questões primeiro.")
        else:
            qtd = st.slider("Quantidade de questões", 1,
                             min(20, len(qs)), min(5, len(qs)))
            if st.button("▶ Iniciar Simulado", type="primary"):
                sel = random.sample(list(qs.items()), qtd)
                st.session_state["simulado_fila"]  = sel
                st.session_state["simulado_idx"]   = 0
                st.session_state["simulado_acert"] = 0
                st.rerun()

            fila  = st.session_state.get("simulado_fila", [])
            s_idx = st.session_state.get("simulado_idx", 0)

            if fila and s_idx < len(fila):
                qid, q = fila[s_idx]
                mat = mats.get(q.get("materia_id",""),{}).get("nome","?")
                total_q = len(fila)
                st.progress(s_idx / total_q)
                st.markdown(f"**Questão {s_idx+1}/{total_q}** — {mat} | {q.get('banca','')}")
                st.markdown(
                    f'<div style="background:#0f3460;border-radius:10px;'
                    f'padding:16px;margin:8px 0;">{q["enunciado"]}</div>',
                    unsafe_allow_html=True)
                resp = st.radio(
                    "Escolha a alternativa:",
                    [f"({l}) {t}" for l, t in q["alternativas"].items()],
                    key=f"sim_resp_{qid}_{s_idx}",
                    index=None)
                if resp and st.button("Confirmar Resposta",
                                       key=f"sim_conf_{s_idx}"):
                    letra = resp[1]
                    q["tentativas"] = q.get("tentativas",0) + 1
                    if letra == q["gabarito"]:
                        q["acertos"] = q.get("acertos",0) + 1
                        st.session_state["simulado_acert"] += 1
                        st.success("✅ Correto!")
                    else:
                        st.error(f"❌ Errado. Gabarito: **{q['gabarito']}**")
                    save_d()
                    import time; time.sleep(1.2)
                    st.session_state["simulado_idx"] = s_idx + 1
                    st.rerun()

            elif fila and s_idx >= len(fila):
                acert = st.session_state.get("simulado_acert",0)
                total = len(fila)
                pct   = acert/total*100
                st.balloons()
                st.success(
                    f"🎉 Simulado concluído!  "
                    f"**{acert}/{total}  ({pct:.0f}%)**")
                if pct >= 70:
                    st.info("Excelente! Continue assim.")
                else:
                    st.warning("Revise os tópicos errados antes da próxima tentativa.")
                if st.button("Novo Simulado"):
                    st.session_state["simulado_fila"] = []
                    st.session_state["simulado_idx"]  = 0
                    st.rerun()

    # ── Adicionar questão ─────────────────────────────────────────────────
    with tab_add:
        with st.form("form_q", clear_on_submit=True):
            opts = {m["nome"]: mid for mid, m in mats.items()}
            enunciado = st.text_area("Enunciado", height=100)
            st.markdown("**Alternativas:**")
            ca,cb = st.columns(2)
            with ca:
                alt_a = st.text_input("(A)")
                alt_c = st.text_input("(C)")
                alt_e = st.text_input("(E) — opcional")
            with cb:
                alt_b = st.text_input("(B)")
                alt_d = st.text_input("(D)")
            c1,c2,c3 = st.columns(3)
            with c1: gab    = st.selectbox("Gabarito", ["A","B","C","D","E"])
            with c2: banca  = st.text_input("Banca")
            with c3: mat_q  = st.selectbox("Matéria", list(opts.keys()) or ["—"])
            if st.form_submit_button("💾 Adicionar Questão", type="primary"):
                alts = {l:t for l,t in zip("ABCDE",[alt_a,alt_b,alt_c,alt_d,alt_e]) if t}
                if enunciado.strip() and alts:
                    qid = _novo_id("Q", qs)
                    qs[qid] = {
                        "enunciado": enunciado.strip(), "alternativas": alts,
                        "gabarito": gab, "materia_id": opts.get(mat_q,""),
                        "banca": banca, "acertos": 0, "tentativas": 0,
                        "criado_em": _hoje(),
                    }
                    save_d()
                    st.success("✅ Questão adicionada!")
                    st.rerun()

    # ── Lista ─────────────────────────────────────────────────────────────
    with tab_lista:
        if not qs:
            st.info("Nenhuma questão ainda.")
        else:
            for qid, q in qs.items():
                mat  = mats.get(q.get("materia_id",""),{}).get("nome","?")
                tent = q.get("tentativas",0)
                ac   = q.get("acertos",0)
                with st.expander(
                    f"{q['enunciado'][:60]}… — {mat} | "
                    f"Acertos: {ac}/{tent if tent else '—'}"):
                    st.markdown(q["enunciado"])
                    for l,t in q["alternativas"].items():
                        cor = "#2ecc71" if l==q["gabarito"] else "#e0e0e0"
                        st.markdown(
                            f'<span style="color:{cor}">({l}) {t}</span>',
                            unsafe_allow_html=True)
                    st.caption(f"Gabarito: {q['gabarito']}  |  Banca: {q.get('banca','—')}")
                    if st.button("🗑 Remover", key=f"del_q_{qid}"):
                        del qs[qid]; save_d(); st.rerun()

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
        "📅 Planejamento":       p_planejamento,
        "⏱ Sessões":            p_sessoes,
        "📝 Questões":           p_questoes,
        "✍ Feynman":            p_feynman,
        "💾 Exportar":           p_exportar,
    }
    rotas.get(pagina, p_dashboard)()

if __name__ == "__main__":
    main()
