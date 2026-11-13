from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import logging
import os
import math
import pandas as pd
import requests
import streamlit as st
from supabase import create_client
try:
  from streamlit_geolocation import streamlit_geolocation
except ImportError:
  streamlit_geolocation = None

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="LRVIX - CONTROLE DE PONTO",
    page_icon=str(__import__("pathlib").Path(__file__).resolve().parent / "LRVIX_PONTO.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- IDENTIDADE VISUAL LRVIX GESTÃO | PALETA EXTRAÍDA DO APP DE GESTÃO TÉCNICA ---
st.markdown("""
<style>
:root{color-scheme:dark;--lrvix-bg:#081629;--lrvix-side:#0D2340;--lrvix-panel:#102A49;--lrvix-field:#122C4B;--lrvix-line:#315477;--lrvix-text:#F7FAFF;--lrvix-muted:#B9CDE4;--lrvix-accent:#69B5F4;}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:#081629!important;color:#F7FAFF!important;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;}
[data-testid="stHeader"]{background:#081629!important;}
.block-container{max-width:1200px!important;padding-top:2rem!important;padding-bottom:2rem!important;}
h1,h2,h3,h4,h5,h6,[data-testid="stMarkdownContainer"] strong{color:#F7FAFF!important;}
p,label,[data-testid="stMarkdownContainer"]{color:#F7FAFF;}
[data-testid="stCaptionContainer"],.stCaption,[data-testid="stCaptionContainer"] p{color:#B9CDE4!important;}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div{background:#0D2340!important;color:#F7FAFF!important;}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label{color:#F7FAFF!important;}
[data-testid="stSidebar"] div.stButton>button{background:#102B4B!important;border-color:#315D8D!important;text-align:left!important;}
[data-testid="stSidebar"] div.stButton>button:hover{background:#1A4777!important;}
div.stButton>button,div.stDownloadButton>button,[data-testid="stFormSubmitButton"] button{background:#12345A!important;color:#F7FAFF!important;border:1px solid #315D8D!important;border-radius:9px!important;font-weight:600!important;min-height:42px;transition:background .15s ease,border-color .15s ease;}
div.stButton>button:hover,div.stDownloadButton>button:hover,[data-testid="stFormSubmitButton"] button:hover{background:#1D568B!important;border-color:#69B5F4!important;}
button[kind="primary"],button[data-testid="stBaseButton-primary"]{background:#20558B!important;border-color:#69B5F4!important;color:white!important;}
[data-testid="stForm"],[data-testid="stExpander"]{background:#0E2543!important;border:1px solid #315477!important;border-radius:10px!important;}
[data-testid="stForm"]{padding:1.25rem!important;}

/* Login Android: campos escuros permanentes e sem dica de envio com Enter. */
[data-testid="stForm"] [data-testid="stTextInput"] div[data-baseweb="input"],
[data-testid="stForm"] [data-testid="stTextInput"] div[data-baseweb="input"] > div,
[data-testid="stForm"] [data-testid="stTextInput"] input,
[data-testid="stForm"] [data-testid="stTextInput"] input:focus,
[data-testid="stForm"] [data-testid="stTextInput"] input:active,
[data-testid="stForm"] [data-testid="stTextInput"] input:-webkit-autofill,
[data-testid="stForm"] [data-testid="stTextInput"] input:-webkit-autofill:focus {
  background-color:#292929!important;
  color:#F7FAFF!important;
  -webkit-text-fill-color:#F7FAFF!important;
  caret-color:#F7FAFF!important;
  -webkit-box-shadow:0 0 0 1000px #292929 inset!important;
  box-shadow:0 0 0 1000px #292929 inset!important;
}
[data-testid="InputInstructions"],
[data-testid="stInputInstructions"],
[data-testid="stForm"] [data-baseweb="input"] [data-testid="InputInstructions"] {
  display:none!important;
}

div[data-baseweb="input"]>div,div[data-baseweb="select"]>div,div[data-baseweb="textarea"]>div,[data-testid="stDateInput"] div[data-baseweb="input"]>div{background:#122C4B!important;color:#F7FAFF!important;border-color:#41678E!important;border-radius:8px!important;}
input,textarea,[data-baseweb="select"] input,[data-baseweb="select"] span{color:#F7FAFF!important;-webkit-text-fill-color:#F7FAFF!important;}
input::placeholder,textarea::placeholder{color:#AFC5DD!important;}
[data-baseweb="popover"] [role="listbox"],[data-baseweb="popover"] ul,[data-baseweb="menu"]{background:#132F51!important;color:#F7FAFF!important;}
[data-baseweb="popover"] li{color:#F7FAFF!important;}
[data-baseweb="popover"] li:hover{background:#23517E!important;}
[data-testid="stMetric"]{background:#102A49!important;border:1px solid #315477!important;border-radius:12px!important;padding:14px 18px!important;box-shadow:0 4px 14px rgba(0,0,0,.14);}
[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] p{color:#B9DEFF!important;}
[data-testid="stMetricValue"],[data-testid="stMetricValue"] div{color:#E9F5FF!important;}
[data-testid="stDataFrame"],[data-testid="stDataEditor"],[data-testid="stTable"]{border:1px solid #315477!important;border-radius:10px!important;overflow:hidden;}
.stTabs [data-baseweb="tab-list"]{border-bottom:1px solid #315477;gap:8px;}
.stTabs [data-baseweb="tab"]{color:#C4DDF5!important;font-weight:600;}
.stTabs [aria-selected="true"]{color:white!important;border-bottom:3px solid #69B5F4!important;}
[data-testid="stAlert"]{border-radius:10px!important;}
hr{border-color:#315477!important;}
[data-testid="collapsedControl"]{background:#102B4B!important;border:1px solid #315D8D!important;border-radius:8px!important;}
/* Componentes idênticos à identidade do dashboard financeiro LRVIX Gestão */
.fin-hero,.lrvix-hero{background:linear-gradient(115deg,#102C50,#20558B)!important;border:1px solid #4979AC!important;color:white!important;padding:24px 28px;border-radius:16px;margin:10px 0 20px;}
.fin-hero h2,.lrvix-hero h2{color:#FFFFFF!important;margin:0;font-size:28px;}
.fin-hero p,.lrvix-hero p{color:#C5DDF5!important;margin:6px 0 0;}
.fin-card{background:linear-gradient(140deg,#102A49,#183D66)!important;border:1px solid #416B96!important;border-radius:13px;padding:16px 18px;min-height:112px;margin-bottom:12px;}
.fin-label{font-size:13px;color:#C2DBF5!important;font-weight:650;}
.fin-value{font-size:25px;font-weight:800;color:#FFFFFF!important;margin-top:10px;}
.fin-note{font-size:12px;color:#AFC9E5!important;margin-top:5px;}
.fin-section{background:linear-gradient(90deg,#173E6A,#102A49)!important;color:#F7FAFF!important;border-left:5px solid #69B5F4!important;border-radius:8px;padding:12px 16px;font-size:19px;font-weight:750;margin:22px 0 15px;}
.lrvix-brand{display:flex;align-items:center;gap:13px;margin-bottom:1.2rem;}
.lrvix-brand-mark{background:linear-gradient(115deg,#102C50,#20558B);border:1px solid #4979AC;color:white;padding:12px 14px;border-radius:12px;font-weight:850;}
.lrvix-brand-name{font-size:1.2rem;font-weight:800;color:#F7FAFF;}
.lrvix-brand-sub{color:#B9CDE4;font-size:.79rem;}
.lrvix-eyebrow{font-size:.75rem;font-weight:800;letter-spacing:.12em;color:#B9DEFF;margin-bottom:.5rem;}
.lrvix-login-head{text-align:center;padding:2rem 0 1.1rem;}.lrvix-login-head .lrvix-brand-mark{display:inline-block;margin-bottom:15px;font-size:1.45rem;}
.lrvix-login-head h1{color:#F7FAFF!important;}.lrvix-login-head p{color:#B9CDE4!important;}
.lrvix-step{background:#0E2543;border:1px solid #315477;border-radius:10px;padding:16px 18px;margin:12px 0;color:#C2DBF5;}.lrvix-step strong{color:white;}
@media(max-width:700px){.block-container{padding:1rem .8rem 2rem!important;}.fin-hero,.lrvix-hero{padding:20px 18px;}.fin-hero h2,.lrvix-hero h2{font-size:22px!important;}}

/* LRVIX PONTO | PADRONIZACAO VISUAL PREMIUM — APENAS APRESENTACAO */
/* Nao altera os valores enviados aos formularios, Supabase ou Telegram. */
[data-testid="stSidebar"] div.stButton > button,
[data-testid="stSidebar"] div.stButton > button p,
div.stButton > button, div.stButton > button p,
div.stDownloadButton > button, div.stDownloadButton > button p,
[data-testid="stFormSubmitButton"] button,
[data-testid="stFormSubmitButton"] button p {
  text-transform:uppercase!important;
  text-align:center!important;
  justify-content:center!important;
  align-items:center!important;
  letter-spacing:.045em!important;
  font-weight:700!important;
}
[data-testid="stSidebar"] div.stButton > button {min-height:44px!important;width:100%!important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  text-transform:uppercase!important;text-align:center!important;
}
/* Titulos, rotulos, metricas e paineis */
h1,h2,h3,h4,h5,h6,
[data-testid="stHeadingWithActionElements"],
[data-testid="stWidgetLabel"] p,
[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div,
.fin-label,.fin-value,.fin-note,.fin-section,
.lrvix-eyebrow,.lrvix-brand-name,.lrvix-brand-sub,
.lrvix-hero h2,.lrvix-hero p,.fin-hero h2,.fin-hero p,
.lrvix-login-head h1,.lrvix-login-head p {
  text-transform:uppercase!important;text-align:center!important;
}
[data-testid="stMetric"] {text-align:center!important;}
[data-testid="stMetric"] > div,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {justify-content:center!important;align-items:center!important;}
[data-testid="stWidgetLabel"] {justify-content:center!important;text-align:center!important;}
/* Campos: centraliza exibicao, mas nao altera o dado digitado (senha, CPF, datas). */
[data-testid="stTextInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input,
[data-baseweb="select"] [role="combobox"],
[data-baseweb="select"] [role="combobox"] span {
  text-align:center!important;
}
/* O texto exibido nos seletores fica em caixa alta, sem alterar o valor real. */
[data-baseweb="select"] [role="combobox"],
[data-baseweb="select"] [role="combobox"] span,
[data-baseweb="tab"],
[data-testid="stAlert"] p,
[data-testid="stCaptionContainer"] p,
.lrvix-install-link {text-transform:uppercase!important;}
.lrvix-install-link {letter-spacing:.045em!important;}
.fin-card,.fin-section,.lrvix-step,.lrvix-brand {text-align:center!important;}
.lrvix-brand {justify-content:center!important;}
/* Cabecalhos de tabelas Streamlit (quando renderizados em DOM). */
[data-testid="stTable"] th {text-align:center!important;text-transform:uppercase!important;}
@media(max-width:700px){
 [data-testid="stSidebar"] div.stButton > button {font-size:12px!important;}
 h1{font-size:1.7rem!important;}
}
</style>
""",unsafe_allow_html=True)

pwa_code = """
<link rel="manifest" href="https://raw.githubusercontent.com/mmagre-droid/lrvix-ponto/main/manifest.json">
<link rel="icon" href="https://raw.githubusercontent.com/mmagre-droid/lrvix-ponto/main/icone.png">
<link rel="apple-touch-icon" href="https://raw.githubusercontent.com/mmagre-droid/lrvix-ponto/main/icone.png">
"""
st.markdown(pwa_code, unsafe_allow_html=True)


# --- CERCA GEOGRÁFICA: CONFIGURAR NO STREAMLIT SECRETS OU AMBIENTE ---
def configuracao_geofence():
  def valor(chave):
    ambiente = os.environ.get(chave)
    if ambiente is not None:
      return ambiente
    try:
      return st.secrets.get(chave)
    except (FileNotFoundError, KeyError):
      return None

  try:
    lat = float(valor("PONTO_LATITUDE"))
    lon = float(valor("PONTO_LONGITUDE"))
    raio = float(valor("PONTO_RAIO_METROS"))
    precisao = float(valor("PONTO_PRECISAO_MAX_METROS") or 100)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180 and 0 < raio <= 100000 and 0 < precisao <= 10000):
      raise ValueError("Coordenadas, raio ou precisão inválidos")
    return lat, lon, raio, precisao
  except (TypeError, ValueError):
    return None


def distancia_metros(lat1, lon1, lat2, lon2):
  r = 6371000.0
  a1, a2 = math.radians(lat1), math.radians(lat2)
  da = math.radians(lat2 - lat1)
  dl = math.radians(lon2 - lon1)
  h = math.sin(da / 2) ** 2 + math.cos(a1) * math.cos(a2) * math.sin(dl / 2) ** 2
  return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def validar_geolocalizacao(posicao, configuracao):
  if not configuracao:
    return False, "ZONA DE PONTO NÃO CONFIGURADA. CONTATE O ADMINISTRADOR."
  if not isinstance(posicao, dict):
    return False, "AUTORIZE A LOCALIZAÇÃO NO NAVEGADOR PARA REGISTRAR O PONTO."
  try:
    lat, lon = float(posicao.get("latitude")), float(posicao.get("longitude"))
    precisao = float(posicao.get("accuracy"))
    if not all(map(math.isfinite, (lat, lon, precisao))):
      raise ValueError("Coordenadas inválidas")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180) or precisao < 0:
      raise ValueError("Coordenadas inválidas")
  except (ValueError, TypeError):
    return False, "LOCALIZAÇÃO INDISPONÍVEL. ATIVE O GPS E TENTE NOVAMENTE."
  centro_lat, centro_lon, raio, precisao_max = configuracao
  if precisao > precisao_max:
    return False, f"PRECISÃO INSUFICIENTE (±{precisao:.0f} M). AGUARDE O GPS MELHORAR."
  distancia = distancia_metros(lat, lon, centro_lat, centro_lon)
  # Margem conservadora: a área de incerteza deve estar dentro da zona.
  if distancia + precisao > raio:
    return False, f"FORA DA ZONA AUTORIZADA OU PRÓXIMO AO LIMITE (DISTÂNCIA: {distancia:.0f} M; RAIO: {raio:.0f} M)."
  return True, f"LOCALIZAÇÃO VALIDADA · {distancia:.0f} M DO CENTRO · RAIO {raio:.0f} M"


# --- MODELO MISTO: REGRAS PERSISTIDAS NO SUPABASE ---
def cliente_geo():
  """Cliente exclusivamente servidor; a chave de serviço nunca vai ao navegador."""
  try:
    chave = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
  except (FileNotFoundError, KeyError):
    return None
  if not chave or not url:
    return None
  return create_client(str(url), str(chave))


def geo_dados():
  db = cliente_geo()
  if db is None:
    raise RuntimeError("CONFIGURE SUPABASE_URL E SUPABASE_SERVICE_ROLE_KEY NOS SECRETS.")
  locais = db.table("PONTO_LOCAIS").select("*").order("nome").execute().data or []
  permissoes = db.table("PONTO_PERMISSOES").select("*").execute().data or []
  return db, locais, permissoes


def autorizacao_mista(cpf, posicao, locais, permissoes):
  """Bloqueio individual prevalece; liberação temporária exige local ativo."""
  if not isinstance(posicao, dict):
    return False, "AUTORIZE O GPS PARA REGISTRAR O PONTO."
  try:
    lat = float(posicao["latitude"])
    lon = float(posicao["longitude"])
    accuracy = float(posicao["accuracy"])
    if not all(map(math.isfinite, [lat, lon, accuracy])) or not (-90 <= lat <= 90 and -180 <= lon <= 180) or accuracy < 0:
      raise ValueError()
  except (ValueError, TypeError, KeyError):
    return False, "GPS INVÁLIDO OU INDISPONÍVEL."
  cpf = str(cpf).zfill(11)
  agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
  regras = [r for r in permissoes if str(r.get("cpf", "")).zfill(11) == cpf]
  if any(r.get("tipo") == "BLOQUEIO" and r.get("ativo") for r in regras):
    return False, "TÉCNICO BLOQUEADO PELO GESTOR."
  for local in locais:
    if not local.get("ativo"):
      continue
    id_local = local["id"]
    permitido = bool(local.get("liberado_geral"))
    for r in regras:
      if not r.get("ativo") or r.get("local_id") != id_local:
        continue
      if r.get("tipo") == "LOCAL":
        permitido = True
      if r.get("tipo") == "TEMPORARIA" and r.get("expira_em"):
        try:
          expira = datetime.fromisoformat(str(r["expira_em"]).replace("Z", "+00:00"))
          if expira.tzinfo is not None and agora <= expira:
            permitido = True
        except ValueError:
          pass
    if not permitido:
      continue
    raio = float(local["raio_metros"])
    precisao_max = float(local["precisao_max_metros"])
    if accuracy > precisao_max:
      continue
    distancia = distancia_metros(lat, lon, float(local["latitude"]), float(local["longitude"]))
    if distancia + accuracy <= raio:
      return True, f"LOCAL AUTORIZADO: {local['nome']} · DISTÂNCIA {distancia:.0f} M"
  return False, "FORA DAS ZONAS PERMITIDAS OU SEM AUTORIZAÇÃO PARA ESTE LOCAL."


def painel_localizacoes():
  st.markdown('<div class="lrvix-hero"><h2>📍 GESTÃO DE LOCALIZAÇÕES</h2><p>CONTROLE MISTO DE ZONAS E PERMISSÕES</p></div>', unsafe_allow_html=True)
  try:
    db, locais, permissoes = geo_dados()
    tecnicos = db.table("TECNICOS").select("cpf,nome").order("nome").execute().data or []
  except Exception as exc:
    st.error(f"NÃO FOI POSSÍVEL CARREGAR A GESTÃO DE LOCALIZAÇÕES: {exc}")
    return
  c1,c2,c3 = st.columns(3)
  c1.metric("LOCAIS CADASTRADOS", len(locais))
  c2.metric("LOCAIS ATIVOS", sum(bool(x.get("ativo")) for x in locais))
  c3.metric("REGRAS INDIVIDUAIS", len(permissoes))
  st.markdown('<div class="fin-section">CADASTRAR LOCAL AUTORIZADO</div>', unsafe_allow_html=True)
  with st.form("geo_novo_local", clear_on_submit=True):
    nome = st.text_input("NOME DO LOCAL")
    endereco = st.text_input("ENDEREÇO / REFERÊNCIA")
    a,b = st.columns(2)
    lat = a.number_input("LATITUDE", min_value=-90.0, max_value=90.0, value=0.0, format="%.7f")
    lon = b.number_input("LONGITUDE", min_value=-180.0, max_value=180.0, value=0.0, format="%.7f")
    c,d = st.columns(2)
    raio = c.number_input("RAIO (METROS)", min_value=10, max_value=10000, value=150)
    precisao = d.number_input("PRECISÃO MÁXIMA GPS (METROS)", min_value=5, max_value=1000, value=50)
    geral = st.checkbox("LIBERAR PARA TODOS OS TÉCNICOS", value=False)
    if st.form_submit_button("+ SALVAR LOCALIZAÇÃO", use_container_width=True):
      if not nome.strip() or (lat == 0 and lon == 0):
        st.error("INFORME NOME E COORDENADAS VÁLIDAS.")
      else:
        try:
          db.table("PONTO_LOCAIS").insert(dict(nome=nome.strip(), endereco=endereco.strip(), latitude=lat, longitude=lon, raio_metros=raio, precisao_max_metros=precisao, liberado_geral=geral, ativo=True)).execute()
          st.success("LOCAL CADASTRADO.")
          st.rerun()
        except Exception as exc:
          st.error(f"ERRO AO SALVAR: {exc}")
  st.markdown('<div class="fin-section">LOCAIS CADASTRADOS</div>', unsafe_allow_html=True)
  for loc in locais:
    with st.expander(f"📍 {loc['nome'].upper()} · {'ATIVO' if loc['ativo'] else 'BLOQUEADO'}"):
      with st.form(f"geo_editar_{loc['id']}"):
        nome_edit = st.text_input("NOME", value=loc['nome'], key=f"nome_{loc['id']}")
        end_edit = st.text_input("ENDEREÇO", value=loc.get('endereco') or '', key=f"end_{loc['id']}")
        x,y = st.columns(2)
        lat_edit = x.number_input("LATITUDE", -90.0, 90.0, float(loc['latitude']), format="%.7f", key=f"lat_{loc['id']}")
        lon_edit = y.number_input("LONGITUDE", -180.0, 180.0, float(loc['longitude']), format="%.7f", key=f"lon_{loc['id']}")
        raio_edit = st.number_input("RAIO EM METROS", 10, 10000, int(loc['raio_metros']), key=f"raio_{loc['id']}")
        precisao_edit = st.number_input("PRECISÃO MÁXIMA", 5, 1000, int(loc['precisao_max_metros']), key=f"prec_{loc['id']}")
        ativo_edit = st.checkbox("LOCAL ATIVO", value=bool(loc['ativo']), key=f"ativo_{loc['id']}")
        geral_edit = st.checkbox("LIBERAÇÃO GERAL", value=bool(loc['liberado_geral']), key=f"geral_{loc['id']}")
        if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
          try:
            db.table("PONTO_LOCAIS").update(dict(nome=nome_edit.strip(), endereco=end_edit.strip(), latitude=lat_edit, longitude=lon_edit, raio_metros=raio_edit, precisao_max_metros=precisao_edit, ativo=ativo_edit, liberado_geral=geral_edit)).eq("id", loc['id']).execute()
            st.rerun()
          except Exception as exc:
            st.error(str(exc))
      if st.button("EXCLUIR LOCAL", key=f"excluir_{loc['id']}"):
        try:
          db.table("PONTO_LOCAIS").delete().eq("id",loc['id']).execute()
          st.rerun()
        except Exception as exc:
          st.error(str(exc))
  st.markdown('<div class="fin-section">PERMISSÕES DOS TÉCNICOS</div>', unsafe_allow_html=True)
  if not tecnicos:
    st.warning("NENHUM TÉCNICO ENCONTRADO.")
    return
  mapa = {f"{t['nome']} · {str(t['cpf']).zfill(11)}": str(t['cpf']).zfill(11) for t in tecnicos}
  with st.form("geo_permissoes"):
    selecionado = st.selectbox("TÉCNICO", list(mapa))
    tipo = st.selectbox("TIPO DE PERMISSÃO", ["LOCAL", "TEMPORARIA", "BLOQUEIO"])
    opcoes = {l['nome'] + ' · ' + str(l['id']): l['id'] for l in locais}
    local_sel = st.selectbox("LOCAL", list(opcoes), disabled=tipo=="BLOQUEIO") if opcoes else None
    dias = st.number_input("DURAÇÃO DA LIBERAÇÃO TEMPORÁRIA (HORAS)", 1, 720, 24, disabled=tipo!="TEMPORARIA")
    if st.form_submit_button("SALVAR PERMISSÃO", use_container_width=True):
      if tipo != "BLOQUEIO" and not local_sel:
        st.error("CADASTRE UM LOCAL PRIMEIRO.")
      else:
        try:
          expiracao = (datetime.now(ZoneInfo("America/Sao_Paulo")) + timedelta(hours=dias)).isoformat() if tipo=="TEMPORARIA" else None
          db.table("PONTO_PERMISSOES").insert(dict(cpf=mapa[selecionado], tipo=tipo, local_id=opcoes.get(local_sel) if tipo!="BLOQUEIO" else None, expira_em=expiracao, ativo=True)).execute()
          st.rerun()
        except Exception as exc:
          st.error(str(exc))
  for r in permissoes:
    c1,c2 = st.columns([5,1])
    c1.caption(f"{r['cpf']} · {r['tipo']} · LOCAL {r.get('local_id') or 'TODOS'} · {'ATIVO' if r['ativo'] else 'INATIVO'} · EXPIRA {r.get('expira_em') or 'NÃO'}")
    if c2.button("REVOGAR", key=f"rev_{r['id']}"):
      try:
        db.table("PONTO_PERMISSOES").update({"ativo":False}).eq("id",r['id']).execute()
        st.rerun()
      except Exception as exc:
        st.error(str(exc))


# --- FUNÇÕES AUXILIARES DE CÁLCULO DE HORAS ---
def parse_horario(horario_str):
  """Converte string de horário (HH:MM ou HH:MM:SS) em timedelta a partir da meia-noite."""
  if not horario_str or pd.isna(horario_str):
    return None
  try:
    partes = str(horario_str).split(":")
    h = int(partes[0])
    m = int(partes[1])
    s = int(partes[2].split(".")[0]) if len(partes) > 2 else 0
    return timedelta(hours=h, minutes=m, seconds=s)
  except Exception:
    return None


def calcular_horas_linha(row):
  """Calcula total trabalhado e hora extra para cada dia (jornada padrão de 8h líquidas)."""
  ent = parse_horario(row.get("ENTRADA"))
  s_alm = parse_horario(row.get("SAÍDA ALMOÇO"))
  r_alm = parse_horario(row.get("RETORNO ALMOÇO"))
  sai = parse_horario(row.get("SAÍDA"))

  if not ent or not sai:
    return "00:00", "00:00", 0.0, 0.0

  if s_alm and r_alm and r_alm > s_alm:
    tempo_almoco = r_alm - s_alm
  else:
    tempo_almoco = timedelta(0)

  total_bruto = sai - ent
  total_liquido = total_bruto - tempo_almoco

  if total_liquido.total_seconds() < 0:
    total_liquido = timedelta(0)

  # Jornada padrão: 8 horas líquidas diárias (08:00 - 17:00 c/ 1h de almoço)
  jornada_padrao = timedelta(hours=8)

  if total_liquido > jornada_padrao:
    he = total_liquido - jornada_padrao
  else:
    he = timedelta(0)

  def format_td(td):
    tot_seg = int(td.total_seconds())
    horas = tot_seg // 3600
    minutos = (tot_seg % 3600) // 60
    return f"{horas:02d}:{minutos:02d}"

  seg_trab = total_liquido.total_seconds()
  seg_he = he.total_seconds()

  return format_td(total_liquido), format_td(he), seg_trab, seg_he


def seletor_data_html5(label: str, key: str):
  val_str = st.text_input(label, key=f"input_{key}", placeholder="DD/MM/AAAA")
  dt_retorno = None
  if val_str:
    try:
      dt_retorno = datetime.strptime(val_str.strip(), "%Y-%m-%d").date()
    except ValueError:
      try:
        dt_retorno = datetime.strptime(val_str.strip(), "%d/%m/%Y").date()
      except ValueError:
        st.caption("⚠️ Formato aceito: YYYY-MM-DD ou DD/MM/AAAA")
  return dt_retorno


# --- CONFIGURAÇÕES DE LOG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES DO SUPABASE ---
SUPABASE_URL = "https://ozcgilhxomoyqaejwyrs.supabase.co"
SUPABASE_KEY = "sb_publishable_lrV26hcUDDuUpG0_pXSmFQ_S2T35_ZK"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURAÇÃO DO TELEGRAM ---
def obter_token_telegram():
  """Lê token do ambiente ou Secrets sem impedir inicialização local."""
  token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
  if token:
    return token
  try:
    return str(st.secrets.get("TELEGRAM_BOT_TOKEN", "") or "").strip()
  except (FileNotFoundError, KeyError):
    return ""


TELEGRAM_BOT_TOKEN = obter_token_telegram()


class TelegramNotifier:

  def __init__(self, token: str):
    self.token = token
    self.base_url = f"https://api.telegram.org/bot{self.token}"

  def enviar_mensagem(self, chat_id: str, mensagem: str) -> bool:
    if not self.token:
      logger.warning("Notificação Telegram ignorada: TELEGRAM_BOT_TOKEN não configurado.")
      return False
    url = f"{self.base_url}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
      response = requests.post(url, json=payload, timeout=10)
      return response.json().get("ok", False)
    except Exception as e:
      logger.error(f"Erro Telegram: {e}")
      return False

  def notificar_ponto(
      self, chat_id: str, tecnico: str, tipo_ponto: str, horario: str, data: str
  ):
    mensagem = (
        f"⚡ *LRVIX — COMPROVANTE DE PONTO*\n\n"
        f"👤 *Técnico:* {tecnico}\n"
        f"📌 *Ação:* `{tipo_ponto}`\n"
        f"📅 *Data:* {data}\n"
        f"⏰ *Horário:* {horario}\n\n"
        f"✅ _Registro sincronizado com sucesso!_"
    )
    return self.enviar_mensagem(chat_id, mensagem)


telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN)

# --- INTERJORNADA: EVENTOS COM DATA E HORA COMPLETAS ---
FUSO_PONTO = ZoneInfo("America/Sao_Paulo")
DESCANSO_INTERJORNADA = timedelta(hours=11)
TIPOS_PONTO = ("ENTRADA", "SAIDA_ALMOCO", "RETORNO_ALMOCO", "SAIDA")

def instante_evento(evento):
  instante = datetime.fromisoformat(str(evento["ocorrido_em"]).replace("Z", "+00:00"))
  return instante.replace(tzinfo=FUSO_PONTO) if instante.tzinfo is None else instante.astimezone(FUSO_PONTO)

def eventos_tecnico(cpf):
  db = cliente_geo()
  if db is None:
    raise RuntimeError("CONFIGURE SUPABASE_SERVICE_ROLE_KEY NOS SECRETS PARA REGISTRAR EVENTOS.")
  # Consulta paginada: não descartar eventos antigos por limite de 1000 linhas.
  resultado = []
  inicio = 0
  while True:
    lote = (db.table("PONTO_EVENTOS").select("id,cpf,tipo,modo,ocorrido_em")
            .eq("cpf", cpf).order("ocorrido_em").range(inicio, inicio + 999).execute().data or [])
    resultado.extend(lote)
    if len(lote) < 1000:
      break
    inicio += 1000
  return resultado

def ultima_saida_legada(cpf):
  # Compatibilidade com pontos anteriores à implantação da tabela de eventos.
  linhas = (supabase.table("CONTROLE_PONTO").select("data,entrada,saida")
            .eq("cpf", cpf).order("data", desc=True).limit(30).execute().data or [])
  for linha in linhas:
    if linha.get("saida"):
      try:
        dia = datetime.strptime(str(linha["data"])[:10], "%Y-%m-%d").date()
        hora_saida = time.fromisoformat(str(linha["saida"]))
        saida = datetime.combine(dia, hora_saida, FUSO_PONTO)
        if linha.get("entrada") and hora_saida < time.fromisoformat(str(linha["entrada"])):
          saida += timedelta(days=1)
        return saida
      except (ValueError, TypeError):
        continue
  return None

def estado_interjornada(eventos, agora, ultima_saida_antiga=None):
  """Define próximo evento; descanso reinicia após cada SAIDA efetiva."""
  ultimo = eventos[-1] if eventos else None
  saida = next((instante_evento(e) for e in reversed(eventos) if e["tipo"] == "SAIDA"), None)
  if saida is None:
    saida = ultima_saida_antiga
  fim_descanso = saida + DESCANSO_INTERJORNADA if saida else None
  em_descanso = bool(fim_descanso and agora < fim_descanso)
  if ultimo and ultimo["tipo"] != "SAIDA":
    modo = ultimo["modo"]
    sequencia = {"ENTRADA":"SAIDA" if modo == "INTERJORNADA" else "SAIDA_ALMOCO",
                 "SAIDA_ALMOCO":"RETORNO_ALMOCO", "RETORNO_ALMOCO":"SAIDA"}
    return sequencia.get(ultimo["tipo"], "SAIDA"), modo, fim_descanso
  return "ENTRADA", "INTERJORNADA" if em_descanso else "NORMAL", fim_descanso

def duracao_formatada(segundos):
  segundos = max(0, int(segundos))
  return f"{segundos // 3600:02d}h {(segundos % 3600) // 60:02d}m"

def resumo_eventos(eventos):
  """Soma períodos efetivos; almoço excluído; extras por jornada >8h e atendimentos de interjornada."""
  aberto = None
  inicio_jornada = None
  total = extra_interjornada = 0.0
  jornadas = {}
  for e in eventos:
    dt = instante_evento(e)
    tipo = e["tipo"]
    modo = e["modo"]
    if tipo == "ENTRADA":
      aberto = dt
      inicio_jornada = dt if modo == "NORMAL" else None
    elif tipo == "SAIDA_ALMOCO" and aberto:
      segundos = max(0, (dt - aberto).total_seconds())
      total += segundos
      if inicio_jornada:
        jornadas[inicio_jornada] = jornadas.get(inicio_jornada, 0) + segundos
      aberto = None
    elif tipo == "RETORNO_ALMOCO":
      aberto = dt
    elif tipo == "SAIDA" and aberto:
      segundos = max(0, (dt - aberto).total_seconds())
      total += segundos
      if modo == "INTERJORNADA":
        extra_interjornada += segundos
      elif inicio_jornada:
        jornadas[inicio_jornada] = jornadas.get(inicio_jornada, 0) + segundos
      aberto = None
      inicio_jornada = None
  extras = sum(max(0, seg - 8 * 3600) for seg in jornadas.values()) + extra_interjornada
  return total, extras

# ==========================================
# CONTROLE DE SESSÃO E LOGIN (COM VALIDAÇÃO OBRIGATÓRIA DE SENHA)
# ==========================================
if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
  st.session_state.usuario_nome = ""
  st.session_state.usuario_perfil = ""
  st.session_state.usuario_cpf = ""

if not st.session_state.autenticado:
  st.markdown("""<div class="lrvix-login-head"><div class="lrvix-brand-mark">LRVIX</div><h1>Bem-vindo ao LRVIX PONTO</h1><p>Gestão inteligente da jornada de trabalho · Acesso seguro</p></div>""",unsafe_allow_html=True)
  _, login_col, _ = st.columns([1, 1.25, 1])


  with login_col:
   with st.form("form_login"):
     cpf_input = st.text_input("CPF (Somente números)")
     senha_input = st.text_input("Senha", type="password")
     botao_login = st.form_submit_button(
         "Entrar", use_container_width=True, type="primary"
     )

     if botao_login:
       if not cpf_input or not cpf_input.strip():
         st.warning("⚠️ Por favor, informe o seu CPF.")
       elif not senha_input or not senha_input.strip():
         st.warning("⚠️ Por favor, informe a sua Senha.")
       else:
         try:
           cpf_limpo = "".join(filter(str.isdigit, cpf_input)).zfill(11)
           senha_limpa = senha_input.strip()

           # Consulta o usuário pelo CPF no banco de dados
           res_login = (
               supabase.table("TECNICOS")
               .select("nome, cpf, email, telefone, senha")
               .eq("cpf", cpf_limpo)
               .execute()
           )

           if res_login.data:
             usuario = res_login.data[0]
             senha_cadastrada = str(usuario.get("senha") or "").strip()

             # Valida se a senha digitada confere com a cadastrada na tabela
             if senha_cadastrada and senha_limpa == senha_cadastrada:
               st.session_state.autenticado = True
               st.session_state.usuario_nome = usuario["nome"]
               st.session_state.usuario_cpf = str(usuario["cpf"]).zfill(11)

               if st.session_state.usuario_cpf == "08429076700":
                 st.session_state.usuario_perfil = "gestor"
               else:
                 st.session_state.usuario_perfil = "tecnico"

               st.session_state.menu_lrvix = "Registrar Ponto" if st.session_state.usuario_perfil == "tecnico" else "🏠 Visão Geral"
               st.success(f"✅ Bem-vindo(a), {st.session_state.usuario_nome}!")
               st.rerun()
             else:
               st.error("❌ Senha incorreta. Tente novamente.")
           else:
             st.error("❌ CPF não encontrado na tabela Técnicos.")
         except Exception as e:
           st.error(f"Erro ao conectar com o banco: {e}")
  st.stop()

# ==========================================
# APLICAÇÃO PRINCIPAL & MENU
# ==========================================

# A aba "Banco de Horas" fica disponível exclusivamente para o perfil gestor
if st.session_state.usuario_perfil == "gestor":
  opcoes_menu = [
      "🏠 Visão Geral",
      "Gestão de Lançamentos",
      "🏦 Banco de Horas",
      "📍 Gestão de Localizações",
      "📅 Calendário de Folgas",
  ]
else:
  opcoes_menu = [
      "Registrar Ponto",
      "🏠 Visão Geral",
      "Gestão de Lançamentos",
      "📅 Calendário de Folgas",
  ]

st.sidebar.markdown("### ◈ LRVIX PONTO")
st.sidebar.markdown(f"**{st.session_state.usuario_nome}**")
st.sidebar.caption(f"Perfil: {st.session_state.usuario_perfil.upper()}")
st.sidebar.divider()

# Navegação em botões com o mesmo padrão visual de "Sair do Sistema".
if st.session_state.get("menu_lrvix") not in opcoes_menu:
  st.session_state.menu_lrvix = opcoes_menu[0]

st.sidebar.markdown("**Navegação**")
for indice, opcao in enumerate(opcoes_menu):
  selecionado = st.session_state.menu_lrvix == opcao
  if st.sidebar.button(
      opcao,
      key=f"nav_lrvix_{indice}",
      use_container_width=True,
      type="primary" if selecionado else "secondary",
  ):
    st.session_state.menu_lrvix = opcao
    st.rerun()

menu = st.session_state.menu_lrvix

st.sidebar.divider()
if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
  st.session_state.autenticado = False
  st.session_state.usuario_nome = ""
  st.session_state.usuario_perfil = ""
  st.session_state.usuario_cpf = ""
  st.rerun()

# ==========================================
# DASHBOARD | CONSULTA SOMENTE LEITURA
# ==========================================
if menu == "📍 Gestão de Localizações" and st.session_state.usuario_perfil == "gestor":
  painel_localizacoes()

if menu == "🏠 Visão Geral":
  from html import escape
  nome_seguro = escape(str(st.session_state.usuario_nome).split()[0])
  gestor = st.session_state.usuario_perfil == "gestor"
  st.markdown('<div class="lrvix-eyebrow">Painel de controle</div>', unsafe_allow_html=True)
  st.markdown(f'<div class="lrvix-hero"><h2>Olá, {nome_seguro} 👋</h2><p>Seu resumo de jornada e atividades em um só lugar.</p></div>',unsafe_allow_html=True)
  try:
    consulta = supabase.table("CONTROLE_PONTO").select("cpf,data,entrada,saida_almoco,retorno_almoco,saida")
    if not gestor:
      consulta = consulta.eq("cpf",st.session_state.usuario_cpf)
    registros = consulta.execute().data or []
    df_home = pd.DataFrame(registros)
    hoje_home = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    if not df_home.empty:
      df_home["data_dt"] = pd.to_datetime(df_home["data"],errors="coerce").dt.date
      df_mes = df_home[df_home["data_dt"].apply(lambda d: d is not None and pd.notna(d) and d.year==hoje_home.year and d.month==hoje_home.month)].copy()
      df_hoje = df_home[df_home["data_dt"]==hoje_home]
      total_trab_seg = total_extra_seg = 0
      for _, registro in df_mes.iterrows():
        _,_,trab,extra = calcular_horas_linha({
          "ENTRADA":registro.get("entrada"),"SAÍDA ALMOÇO":registro.get("saida_almoco"),
          "RETORNO ALMOÇO":registro.get("retorno_almoco"),"SAÍDA":registro.get("saida")})
        total_trab_seg += trab
        total_extra_seg += extra
      def horas_dashboard(seg):
        return f"{int(seg//3600):02d}h {int((seg%3600)//60):02d}m"
      c1,c2,c3,c4=st.columns(4)
      with c1: st.metric("Registros no mês",len(df_mes))
      with c2: st.metric("Horas trabalhadas",horas_dashboard(total_trab_seg))
      with c3: st.metric("Horas extras",horas_dashboard(total_extra_seg))
      with c4: st.metric("Registros hoje",len(df_hoje))
      st.subheader("Atividade recente")
      recentes=df_home.sort_values("data_dt",ascending=False).head(8).copy()
      recentes=recentes[["data","entrada","saida_almoco","retorno_almoco","saida"]]
      recentes.columns=["Data","Entrada","Saída almoço","Retorno almoço","Saída"]
      recentes["Data"]=pd.to_datetime(recentes["Data"]).dt.strftime("%d/%m/%Y")
      st.dataframe(recentes.fillna(""),hide_index=True,use_container_width=True)
    else:
      st.info("Ainda não há registros de ponto para exibir.")
    st.caption("Indicadores calculados com os registros disponíveis. Horas extras seguem a regra atual de 8 horas líquidas diárias.")
  except Exception as erro_home:
    logger.exception("Falha ao carregar dashboard")
    st.error("Não foi possível carregar os indicadores agora. Verifique a conexão e tente novamente.")

# ==========================================
# ABA 1: REGISTRAR PONTO (Apenas Técnicos)
# ==========================================
if menu == "Registrar Ponto":
  st.markdown('<div class="lrvix-eyebrow">Jornada de trabalho</div>',unsafe_allow_html=True)
  st.title("Registrar ponto")
  st.markdown(f"Registrando ponto para: **{st.session_state.usuario_nome}**")

  try:
    tecnico_cpf = st.session_state.usuario_cpf
    tecnico_nome = st.session_state.usuario_nome
    agora = datetime.now(FUSO_PONTO)
    hoje = agora.date()
    res_tec = (supabase.table("TECNICOS").select("telegram_chat_id")
               .eq("cpf", tecnico_cpf).execute())
    chat_id = res_tec.data[0].get("telegram_chat_id") if res_tec.data else None
    eventos = eventos_tecnico(tecnico_cpf)
    ultima_legada = ultima_saida_legada(tecnico_cpf) if not eventos else None
    proximo, modo, fim_descanso = estado_interjornada(eventos, agora, ultima_legada)

    if fim_descanso:
      if modo == "INTERJORNADA" or (eventos and eventos[-1]["modo"] == "INTERJORNADA" and eventos[-1]["tipo"] != "SAIDA"):
        st.warning("⚠️ DESCANSO INTERJORNADA NÃO COMPLETADO. "
                   f"PRÓXIMO DESCANSO PREVISTO ATÉ {fim_descanso.strftime('%d/%m/%Y %H:%M')}. "
                   "O REGISTRO DO TRABALHO CONTINUA PERMITIDO.")
      elif proximo == "ENTRADA":
        st.success("✅ DESCANSO INTERJORNADA CUMPRIDO. JORNADA NORMAL DISPONÍVEL.")
    st.caption("JORNADA NORMAL: ENTRADA, ALMOÇO, RETORNO E SAÍDA. "
               "DURANTE A INTERJORNADA: ENTRADA E SAÍDA, SEM BLOQUEIO POR DESCANSO.")

    exige_gps = proximo in ("ENTRADA", "SAIDA")
    geo_autorizada = False
    posicao_geo = None
    if exige_gps:
      try:
        _, locais_geo, permissoes_geo = geo_dados()
        erro_geo = None
      except Exception as exc:
        locais_geo, permissoes_geo = [], []
        erro_geo = str(exc)
      if streamlit_geolocation is None:
        st.error("INSTALE STREAMLIT-GEOLOCATION PARA HABILITAR O GPS.")
      else:
        st.markdown("### 📍 VALIDAÇÃO DE LOCALIZAÇÃO")
        posicao_geo = streamlit_geolocation()
      geo_autorizada, geo_mensagem = autorizacao_mista(tecnico_cpf, posicao_geo, locais_geo, permissoes_geo)
      if erro_geo:
        geo_autorizada, geo_mensagem = False, "CONFIGURAÇÃO DE LOCALIZAÇÕES INDISPONÍVEL: " + erro_geo
      if geo_autorizada:
        st.success("✅ " + geo_mensagem)
      else:
        st.warning("🔒 " + geo_mensagem)
    else:
      st.info("🍽️ ALMOÇO: GPS NÃO OBRIGATÓRIO.")

    rotulos = {"ENTRADA":"🟢 REGISTRAR ENTRADA", "SAIDA_ALMOCO":"🟡 REGISTRAR SAÍDA ALMOÇO",
               "RETORNO_ALMOCO":"🔵 REGISTRAR RETORNO ALMOÇO", "SAIDA":"🔴 REGISTRAR SAÍDA"}
    intervalo_valido = True
    if eventos and proximo in ("SAIDA_ALMOCO", "RETORNO_ALMOCO", "SAIDA") and modo == "NORMAL":
      # Mantém o intervalo mínimo de uma hora na jornada normal.
      ultimo_dt = instante_evento(eventos[-1])
      if agora - ultimo_dt < timedelta(hours=1):
        intervalo_valido = False
        st.warning("⏳ AGUARDE 1 HORA ENTRE MARCAÇÕES DA JORNADA NORMAL.")
    habilitado = intervalo_valido and (not exige_gps or geo_autorizada)
    if st.button(rotulos[proximo], type="primary", use_container_width=True, disabled=not habilitado):
      # Reconsulta os eventos para evitar registrar um tipo desatualizado.
      atuais = eventos_tecnico(tecnico_cpf)
      novo_proximo, novo_modo, _ = estado_interjornada(atuais, datetime.now(FUSO_PONTO),
                                                       ultima_legada if not atuais else None)
      if (novo_proximo, novo_modo) != (proximo, modo):
        st.warning("O ESTADO DO PONTO MUDOU. ATUALIZE A TELA.")
        st.stop()
      if exige_gps:
        _, locais_atualizados, permissoes_atualizadas = geo_dados()
        autorizado, mensagem = autorizacao_mista(tecnico_cpf, posicao_geo, locais_atualizados, permissoes_atualizadas)
        if not autorizado:
          st.error("REGISTRO BLOQUEADO POR LOCALIZAÇÃO: " + mensagem)
          st.stop()
      instante = datetime.now(FUSO_PONTO)
      cliente_geo().table("PONTO_EVENTOS").insert({
          "cpf": tecnico_cpf, "tipo": proximo, "modo": modo,
          "ocorrido_em": instante.isoformat()
      }).execute()
      if chat_id:
        telegram.notificar_ponto(str(chat_id), tecnico_nome,
                                proximo.replace("_", " ") + (" (INTERJORNADA)" if modo == "INTERJORNADA" else ""),
                                instante.strftime("%H:%M"), instante.strftime("%d/%m/%Y"))
      st.success("PONTO REGISTRADO COM SUCESSO!")
      st.rerun()

    st.divider()
    st.subheader("📊 SEUS REGISTROS DE HOJE")
    recentes = [e for e in eventos if instante_evento(e).date() == hoje]
    if recentes:
      st.dataframe(pd.DataFrame([{
          "DATA": instante_evento(e).strftime("%d/%m/%Y"),
          "HORÁRIO": instante_evento(e).strftime("%H:%M:%S"),
          "REGISTRO": e["tipo"].replace("_", " "), "MODO": e["modo"]
      } for e in recentes]), hide_index=True, use_container_width=True)
    else:
      st.info("NENHUM PONTO REGISTRADO HOJE AINDA.")
    total, extras = resumo_eventos(eventos)
    c1, c2 = st.columns(2)
    c1.metric("HORAS TRABALHADAS (EVENTOS)", duracao_formatada(total))
    c2.metric("HORAS EXTRAS ESTIMADAS (EVENTOS)", duracao_formatada(extras))
  except Exception as e:
    logger.exception("Falha no registro de ponto/interjornada")
    st.error(f"ERRO AO REGISTRAR PONTO: {e}")

# ==========================================
# ABA 2: GESTÃO DE LANÇAMENTOS E HORAS EXTRAS
# ==========================================
elif menu == "Gestão de Lançamentos":
  st.markdown('<div class="lrvix-eyebrow">Administração</div>',unsafe_allow_html=True)
  st.title("Gestão de lançamentos")

  try:
    res_ponto = supabase.table("CONTROLE_PONTO").select("*").execute()
    dados_ponto = res_ponto.data or []

    res_tecnicos = (
        supabase.table("TECNICOS").select("cpf, nome, liberado_ate").execute()
    )
    mapa_tecnicos = {}
    mapa_cpf_por_nome = {}
    mapa_liberacao = {}

    for t in res_tecnicos.data or []:
      if t.get("cpf") and t.get("nome"):
        cpf_limpo = "".join(filter(str.isdigit, str(t["cpf"]))).zfill(11)
        mapa_tecnicos[cpf_limpo] = t["nome"]
        mapa_cpf_por_nome[t["nome"]] = cpf_limpo
        mapa_liberacao[cpf_limpo] = t.get("liberado_ate")

    if dados_ponto:
      for row in dados_ponto:
        cpf_ponto = "".join(filter(str.isdigit, str(row.get("cpf", "")))).zfill(
            11
        )
        row["nome_tecnico"] = mapa_tecnicos.get(cpf_ponto, "Desconhecido")

      df = pd.DataFrame(dados_ponto)

      st.markdown("---")
      st.subheader("🔍 Filtros de Visualização")

      col_f1, col_f2, col_f3 = st.columns(3)
      with col_f1:
        if st.session_state.usuario_perfil == "tecnico":
          filtro_tecnico = st.session_state.usuario_nome
          st.text_input("TÉCNICO", value=filtro_tecnico, disabled=True)
        else:
          lista_tecnicos = sorted(list(df["nome_tecnico"].unique()))
          filtro_tecnico = st.selectbox("TÉCNICO", lista_tecnicos)

      with col_f2:
        filtro_data_inicial = seletor_data_html5("DATA INICIAL", "dt_ini_gestao")
      with col_f3:
        filtro_data_final = seletor_data_html5("DATA FINAL", "dt_fim_gestao")

      if filtro_tecnico:
        df = df[df["nome_tecnico"] == filtro_tecnico]

      if "data" in df.columns and not df.empty:
        df["data_dt"] = pd.to_datetime(df["data"]).dt.date
        if filtro_data_inicial:
          df = df[df["data_dt"] >= filtro_data_inicial]
        if filtro_data_final:
          df = df[df["data_dt"] <= filtro_data_final]
        df = df.drop(columns=["data_dt"])

      if df.empty:
        st.warning("⚠ Nenhum registro encontrado para os filtros selecionados.")
      else:
        df = df.sort_values(by="data", ascending=True)

        tabela_espelho = df[
            ["data", "entrada", "saida_almoco", "retorno_almoco", "saida"]
        ].copy()
        tabela_espelho.columns = [
            "DATA",
            "ENTRADA",
            "SAÍDA ALMOÇO",
            "RETORNO ALMOÇO",
            "SAÍDA",
        ]

        tabela_espelho["DATA"] = pd.to_datetime(
            tabela_espelho["DATA"]
        ).dt.strftime("%d/%m/%Y")
        tabela_espelho = tabela_espelho.fillna("")

        # Cálculo automático de Total Trabalhado e Horas Extras por dia
        totais_trab = []
        totais_he = []
        seg_trab_acum = 0
        seg_he_acum = 0

        for _, r in tabela_espelho.iterrows():
          txt_trab, txt_he, s_trab, s_he = calcular_horas_linha(r)
          totais_trab.append(txt_trab)
          totais_he.append(txt_he)
          seg_trab_acum += s_trab
          seg_he_acum += s_he

        tabela_espelho["TOTAL TRABALHADO"] = totais_trab
        tabela_espelho["HORA EXTRA (EXCEDE 8H)"] = totais_he

        # Exibe métricas consolidadas do período filtrado
        tot_h_trab = int(seg_trab_acum // 3600)
        tot_m_trab = int((seg_trab_acum % 3600) // 60)

        tot_h_he = int(seg_he_acum // 3600)
        tot_m_he = int((seg_he_acum % 3600) // 60)

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
          st.metric("📋 Total de Dias", f"{len(tabela_espelho)} dias")
        with col_m2:
          st.metric(
              "⏱️ Horas Trabalhadas", f"{tot_h_trab:02d}h {tot_m_trab:02d}m"
          )
        with col_m3:
          st.metric("🔥 Total Horas Extras", f"{tot_h_he:02d}h {tot_m_he:02d}m")

        st.markdown("---")

        cpf_tecnico_alvo = mapa_cpf_por_nome.get(filtro_tecnico)
        if (
            st.session_state.usuario_perfil == "tecnico"
            and not cpf_tecnico_alvo
        ):
          cpf_tecnico_alvo = st.session_state.usuario_cpf

        fuso_br = ZoneInfo("America/Sao_Paulo")
        agora_dt = datetime.now(fuso_br)

        res_check = (
            supabase.table("TECNICOS")
            .select("liberado_ate")
            .eq("cpf", cpf_tecnico_alvo)
            .execute()
        )
        liberado_ate_str = (
            res_check.data[0].get("liberado_ate")
            if res_check.data
            else mapa_liberacao.get(cpf_tecnico_alvo)
        )

        edicao_ativa_tecnico = False
        liberado_ate_dt = None

        if liberado_ate_str:
          try:
            liberado_ate_dt = datetime.fromisoformat(
                str(liberado_ate_str).replace("Z", "+00:00")
            )
            if liberado_ate_dt.tzinfo is None:
              liberado_ate_dt = liberado_ate_dt.replace(tzinfo=fuso_br)
            else:
              liberado_ate_dt = liberado_ate_dt.astimezone(fuso_br)

            if agora_dt < liberado_ate_dt:
              edicao_ativa_tecnico = True
          except Exception as ex:
            logger.error(f"Erro ao converter liberado_ate: {ex}")

        sou_gestor = st.session_state.usuario_perfil == "gestor"
        pode_editar = sou_gestor or edicao_ativa_tecnico

        if sou_gestor:
          st.subheader("⚙ Painel de Controle (Gestor)")

          if edicao_ativa_tecnico:
            tempo_restante = liberado_ate_dt - agora_dt
            horas_restantes = int(tempo_restante.total_seconds() // 3600)
            minutos_restantes = int(
                (tempo_restante.total_seconds() % 3600) // 60
            )
            st.success(
                f"🔓 Edição liberada para **{filtro_tecnico}**. Expira em"
                f" {horas_restantes}h {minutos_restantes}m."
            )
            if st.button("🔒 Revogar Liberação", use_container_width=True):
              try:
                supabase.table("TECNICOS").update(
                    {"liberado_ate": None}
                ).eq("cpf", cpf_tecnico_alvo).execute()
                st.success("Liberação revogada!")
                st.rerun()
              except Exception as err:
                st.error(f"Erro: {err}")
          else:
            st.info(f"🔒 Edição bloqueada para **{filtro_tecnico}**.")
            if st.button(
                "🔓 Liberar Edição (24h)",
                type="primary",
                use_container_width=True,
            ):
              novo_limite = (agora_dt + timedelta(hours=24)).isoformat()
              try:
                supabase.table("TECNICOS").update(
                    {"liberado_ate": novo_limite}
                ).eq("cpf", cpf_tecnico_alvo).execute()
                st.success("Edição liberada por 24 horas!")
                st.rerun()
              except Exception as err:
                st.error(f"Erro: {err}")

        if pode_editar:
          if (
              st.session_state.usuario_perfil == "tecnico"
              and edicao_ativa_tecnico
          ):
            tempo_restante = liberado_ate_dt - agora_dt
            horas_restantes = int(tempo_restante.total_seconds() // 3600)
            minutos_restantes = int(
                (tempo_restante.total_seconds() % 3600) // 60
            )
            st.success(
                f"🔓 Seu gestor liberou a edição dos seus lançamentos. Expira"
                f" em {horas_restantes}h {minutos_restantes}m."
            )

          tabela_editada = st.data_editor(
              tabela_espelho, use_container_width=True, hide_index=True
          )

          if st.button(
              "💾 Salvar Alterações", type="primary", use_container_width=True
          ):
            with st.spinner("Salvando alterações..."):
              for _, row in tabela_editada.iterrows():
                data_iso = (
                    datetime.strptime(row["DATA"], "%d/%m/%Y")
                    .date()
                    .isoformat()
                )
                supabase.table("CONTROLE_PONTO").upsert(
                    {
                        "cpf": cpf_tecnico_alvo,
                        "data": data_iso,
                        "entrada": row["ENTRADA"] or None,
                        "saida_almoco": row["SAÍDA ALMOÇO"] or None,
                        "retorno_almoco": row["RETORNO ALMOÇO"] or None,
                        "saida": row["SAÍDA"] or None,
                    },
                    on_conflict="cpf,data",
                ).execute()
              st.success("✅ Salvo com sucesso!")
              st.rerun()
        else:
          if st.session_state.usuario_perfil == "tecnico":
            st.info(
                "🔒 Seus lançamentos estão bloqueados para edição. Exibindo"
                " apenas consulta do histórico."
            )
          st.dataframe(
              tabela_espelho, use_container_width=True, hide_index=True
          )
    else:
      st.info("Nenhum lançamento encontrado.")
  except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")

# ==========================================
# ABA 3: BANCO DE HORAS (Apenas Gestor/Administrador)
# ==========================================
elif menu == "🏦 Banco de Horas":
  st.markdown('<div class="lrvix-eyebrow">Indicadores da equipe</div>',unsafe_allow_html=True)
  st.title("Banco de horas")
  st.markdown("Painel consolidado do saldo de horas extras para o gestor.")

  if st.session_state.usuario_perfil != "gestor":
    st.error("⛔ Acesso negado. Esta página é restrita a administradores.")
    st.stop()

  try:
    res_ponto = supabase.table("CONTROLE_PONTO").select("*").execute()
    dados_ponto = res_ponto.data or []

    res_tecnicos = (
        supabase.table("TECNICOS").select("cpf, nome").execute()
    )
    mapa_tecnicos = {}
    for t in res_tecnicos.data or []:
      if t.get("cpf") and t.get("nome"):
        cpf_limpo = "".join(filter(str.isdigit, str(t["cpf"]))).zfill(11)
        mapa_tecnicos[cpf_limpo] = t["nome"]

    st.markdown("---")
    st.subheader("🔍 Filtro de Período")
    col_bh1, col_bh2 = st.columns(2)
    with col_bh1:
      dt_ini_bh = seletor_data_html5("DATA INICIAL", "dt_ini_bh")
    with col_bh2:
      dt_fim_bh = seletor_data_html5("DATA FINAL", "dt_fim_bh")

    if dados_ponto:
      df_bh = pd.DataFrame(dados_ponto)
      df_bh["data_dt"] = pd.to_datetime(df_bh["data"]).dt.date

      if dt_ini_bh:
        df_bh = df_bh[df_bh["data_dt"] >= dt_ini_bh]
      if dt_fim_bh:
        df_bh = df_bh[df_bh["data_dt"] <= dt_fim_bh]

      if df_bh.empty:
        st.warning("⚠ Nenhum registro de ponto no período selecionado.")
      else:
        df_bh["cpf_clean"] = df_bh["cpf"].apply(
            lambda x: "".join(filter(str.isdigit, str(x))).zfill(11)
        )
        df_bh["TÉCNICO"] = df_bh["cpf_clean"].apply(
            lambda x: mapa_tecnicos.get(x, "Desconhecido")
        )

        df_bh_calc = df_bh.rename(
            columns={
                "entrada": "ENTRADA",
                "saida_almoco": "SAÍDA ALMOÇO",
                "retorno_almoco": "RETORNO ALMOÇO",
                "saida": "SAÍDA",
            }
        )

        resumo_banco = []
        for tec_nome, group in df_bh_calc.groupby("TÉCNICO"):
          tot_seg_trab = 0
          tot_seg_he = 0
          dias_registrados = len(group)

          for _, row in group.iterrows():
            _, _, s_trab, s_he = calcular_horas_linha(row)
            tot_seg_trab += s_trab
            tot_seg_he += s_he

          h_trab = int(tot_seg_trab // 3600)
          m_trab = int((tot_seg_trab % 3600) // 60)

          h_he = int(tot_seg_he // 3600)
          m_he = int((tot_seg_he % 3600) // 60)

          resumo_banco.append({
              "TÉCNICO": tec_nome,
              "DIAS COM PONTO": dias_registrados,
              "TOTAL TRABALHADO": f"{h_trab:02d}h {m_trab:02d}m",
              "SALDO HORA EXTRA": f"{h_he:02d}h {m_he:02d}m",
              "_seg_he": tot_seg_he,
          })

        df_resumo_bh = pd.DataFrame(resumo_banco).sort_values(
            by="_seg_he", ascending=False
        )
        df_resumo_bh = df_resumo_bh.drop(columns=["_seg_he"])

        st.markdown("---")
        st.subheader("📊 Consolidação por Técnico")
        st.dataframe(df_resumo_bh, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🔎 Detalhamento por Técnico")
        tec_detalhe = st.selectbox(
            "Selecione um técnico para ver o extrato diário",
            options=sorted(list(df_bh_calc["TÉCNICO"].unique())),
        )

        if tec_detalhe:
          df_tec = df_bh_calc[df_bh_calc["TÉCNICO"] == tec_detalhe].sort_values(
              by="data", ascending=True
          )
          df_tec_exib = df_tec[
              ["data", "ENTRADA", "SAÍDA ALMOÇO", "RETORNO ALMOÇO", "SAÍDA"]
          ].copy()
          df_tec_exib["DATA"] = pd.to_datetime(
              df_tec_exib["data"]
          ).dt.strftime("%d/%m/%Y")

          totais_trab_det = []
          totais_he_det = []
          for _, r in df_tec_exib.iterrows():
            txt_t, txt_h, _, _ = calcular_horas_linha(r)
            totais_trab_det.append(txt_t)
            totais_he_det.append(txt_h)

          df_tec_exib["TOTAL TRABALHADO"] = totais_trab_det
          df_tec_exib["HORA EXTRA"] = totais_he_det
          df_tec_exib = df_tec_exib[[
              "DATA",
              "ENTRADA",
              "SAÍDA ALMOÇO",
              "RETORNO ALMOÇO",
              "SAÍDA",
              "TOTAL TRABALHADO",
              "HORA EXTRA",
          ]].fillna("")

          st.dataframe(df_tec_exib, use_container_width=True, hide_index=True)
    else:
      st.info("Nenhum lançamento de ponto encontrado para processar o banco de horas.")

  except Exception as e:
    st.error(f"Erro ao carregar banco de horas: {e}")

# ==========================================
# ABA 4: CALENDÁRIO DE FOLGAS
# ==========================================
elif menu == "📅 Calendário de Folgas":
  st.markdown('<div class="lrvix-eyebrow">Planejamento</div>',unsafe_allow_html=True)
  st.title("Calendário de folgas")
  st.markdown("Consulte abaixo as folgas agendadas para os técnicos da equipe.")

  try:
    res_tecnicos = supabase.table("TECNICOS").select("cpf, nome").execute()
    mapa_tecnicos = {}
    mapa_cpf_por_nome = {}
    for t in res_tecnicos.data or []:
      if t.get("cpf") and t.get("nome"):
        cpf_limpo = "".join(filter(str.isdigit, str(t["cpf"]))).zfill(11)
        mapa_tecnicos[cpf_limpo] = t["nome"]
        mapa_cpf_por_nome[t["nome"]] = cpf_limpo

    res_folgas = supabase.table("CALENDARIO_FOLGA").select("*").execute()
    dados_folgas = res_folgas.data or []

    for row in dados_folgas:
      cpf_folga = "".join(filter(str.isdigit, str(row.get("cpf", "")))).zfill(
          11
      )
      row["nome_tecnico"] = mapa_tecnicos.get(cpf_folga, "Desconhecido")

    if st.session_state.usuario_perfil == "gestor":
      st.markdown("---")
      st.subheader("➕ Agendar Folga")
      with st.form("form_cadastrar_folga"):
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
          tec_selecionado = st.selectbox(
              "TÉCNICO", options=sorted(list(mapa_cpf_por_nome.keys()))
          )
        with col_g2:
          data_folga = seletor_data_html5("DATA DA FOLGA", "dt_cad_folga")
        with col_g3:
          motivo_folga = st.text_input("Motivo", value="Folga")

        btn_salvar_folga = st.form_submit_button(
            "💾 Salvar Folga", use_container_width=True, type="primary"
        )

        if btn_salvar_folga:
          if not data_folga:
            st.warning("⚠️ Informe a data da folga.")
          else:
            cpf_alvo = mapa_cpf_por_nome.get(tec_selecionado)
            data_iso = data_folga.isoformat()
            try:
              supabase.table("CALENDARIO_FOLGA").upsert(
                  {
                      "cpf": cpf_alvo,
                      "data": data_iso,
                      "motivo": motivo_folga,
                  },
                  on_conflict="cpf,data",
              ).execute()
              st.success("✅ Folga agendada com sucesso!")
              st.rerun()
            except Exception as err:
              st.error(f"Erro: {err}")

    st.markdown("---")
    st.subheader("📋 Lista de Folgas Cadastradas")

    if dados_folgas:
      df_folgas = pd.DataFrame(dados_folgas)
      df_exibicao = df_folgas[["nome_tecnico", "data", "motivo"]].copy()
      df_exibicao.columns = ["TÉCNICO", "DATA", "MOTIVO"]
      df_exibicao["DATA"] = pd.to_datetime(df_exibicao["DATA"]).dt.strftime(
          "%d/%m/%Y"
      )
      df_exibicao = df_exibicao.sort_values(by="DATA", ascending=True)

      st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

      if st.session_state.usuario_perfil == "gestor":
        st.subheader("🗑️ Remover Folga")
        with st.form("form_remover_folga"):
          opcoes_exclusao = []
          for _, r in df_exibicao.iterrows():
            opcoes_exclusao.append(
                f"{r['TÉCNICO']} - {r['DATA']} ({r['MOTIVO']})"
            )

          folga_selecionada = st.selectbox(
              "Selecione para remover", options=opcoes_exclusao
          )
          btn_remover = st.form_submit_button(
              "❌ Excluir Folga", use_container_width=True
          )

          if btn_remover and folga_selecionada:
            partes = folga_selecionada.split(" - ")
            nome_tec = partes[0]
            data_str = partes[1].split(" ")[0]
            cpf_alvo = mapa_cpf_por_nome.get(nome_tec)
            data_iso = (
                datetime.strptime(data_str, "%d/%m/%Y").date().isoformat()
            )

            try:
              supabase.table("CALENDARIO_FOLGA").delete().eq(
                  "cpf", cpf_alvo
              ).eq("data", data_iso).execute()
              st.success("✅ Folga removida!")
              st.rerun()
            except Exception as err:
              st.error(f"Erro ao remover folga: {err}")
    else:
      st.info("Nenhuma folga cadastrada no sistema.")

  except Exception as e:
    st.error(f"Erro ao carregar folgas: {e}")
