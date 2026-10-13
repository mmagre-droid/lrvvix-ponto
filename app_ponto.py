from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
import pandas as pd
import requests
import streamlit as st
from supabase import create_client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="LRVIX - CONTROLE DE PONTO", page_icon="⚡", layout="wide"
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA (LAYOUT CENTRALIZADO + SEM CORTES) ---
st.markdown(
    """
    <style>
        /* Força todos os textos da aplicação em letras maiúsculas */
        html, body, [class*="css"] {
            text-transform: uppercase !important;
        }

        /* Fundo geral e da aplicação inteira */
        .stApp, body, html {
            background-color: #1E293B !important;
            color: #F8FAFC !important;
        }
        
        /* Ajuste de espaçamento superior do container central */
        .block-container {
            background-color: #1E293B !important;
            padding-top: 3rem !important;
            padding-bottom: 2rem !important;
            max-width: 1100px !important;
            margin: 0 auto !important;
            color: #F8FAFC !important;
        }

        /* Títulos e textos com bom contraste */
        h1, h2, h3, h4, h5, h6, span, p, label {
            color: #F8FAFC !important;
        }

        /* Botões padronizados e centralizados */
        .stButton>button {
            border-radius: 10px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.3);
            transition: all 0.2s ease-in-out;
        }
        
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        }

        /* Botão Primário */
        button[kind="primary"] {
            background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%) !important;
            color: white !important;
            border: none;
        }

        /* Campos de texto e caixas de seleção legíveis */
        .stTextInput input, .stSelectbox input, div[data-baseweb="select"] span {
            color: #0F172A !important;
            background-color: #FFFFFF !important;
        }
        
        .stTextInput>div>div>input, .stSelectbox>div>div>div, div[data-baseweb="input"] {
            border-radius: 8px !important;
            border: 1px solid #475569 !important;
            background-color: #FFFFFF !important;
        }

        /* Estilização da navegação por Radio Horizontal/Centralizado */
        div[data-testid="stRadio"] > div {
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
        }

        /* Sidebar escura e padronizada */
        section[data-testid="stSidebar"] {
            background-color: #0F172A !important;
            color: #FFFFFF !important;
        }
        section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] span {
            color: #F1F5F9 !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)

pwa_code = """
<link rel="manifest" href="https://raw.githubusercontent.com/mmagre-droid/lrvix-ponto/main/manifest.json">
<link rel="icon" href="https://raw.githubusercontent.com/mmagre-droid/lrvix-ponto/main/icone.png">
<link rel="apple-touch-icon" href="https://raw.githubusercontent.com/mmagre-droid/lrvix-ponto/main/icone.png">
"""
st.markdown(pwa_code, unsafe_allow_html=True)

# --- CONFIGURAÇÕES DE LOG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES DO SUPABASE ---
SUPABASE_URL = "https://ozcgilhxomoyqaejwyrs.supabase.co"
SUPABASE_KEY = "sb_publishable_lrV26hcUDDuUpG0_pXSmFQ_S2T35_ZK"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURAÇÃO DO TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8795798031:AAEjelcTRk_XQvKWak0-QCgDsl54PMq25l8"


class TelegramNotifier:

  def __init__(self, token: str):
    self.token = token
    self.base_url = f"https://api.telegram.org/bot{self.token}"

  def enviar_mensagem(self, chat_id: str, mensagem: str) -> bool:
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

# ==========================================
# CONTROLE DE SESSÃO E LOGIN
# ==========================================
if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
  st.session_state.usuario_nome = ""
  st.session_state.usuario_perfil = ""
  st.session_state.usuario_cpf = ""

if not st.session_state.autenticado:
  st.title("🔐 LRVIX - ACESSO AO SISTEMA")
  st.write("Insira seu CPF cadastrado na tabela de Técnicos para entrar.")

  with st.form("form_login"):
    cpf_input = st.text_input("CPF (Somente números)")
    senha_input = st.text_input("Senha", type="password")
    botao_login = st.form_submit_button(
        "Entrar", use_container_width=True, type="primary"
    )

    if botao_login:
      if not cpf_input:
        st.warning("⚠️ Por favor, informe o seu CPF.")
      else:
        try:
          cpf_limpo = "".join(filter(str.isdigit, cpf_input)).zfill(11)
          res_login = (
              supabase.table("TECNICOS")
              .select("nome, cpf, email, telefone")
              .eq("cpf", cpf_limpo)
              .execute()
          )

          if res_login.data:
            usuario = res_login.data[0]
            st.session_state.autenticado = True
            st.session_state.usuario_nome = usuario["nome"]
            st.session_state.usuario_cpf = str(usuario["cpf"]).zfill(11)

            if st.session_state.usuario_cpf == "08429076700":
              st.session_state.usuario_perfil = "gestor"
            else:
              st.session_state.usuario_perfil = "tecnico"

            st.success(
                f"✅ Bem-vindo(a), {st.session_state.usuario_nome}!"
            )
            st.rerun()
          else:
            st.error("❌ CPF não encontrado na tabela Técnicos.")
        except Exception as e:
          st.error(f"Erro ao conectar com o banco: {e}")
  st.stop()

# ==========================================
# APLICAÇÃO PRINCIPAL & NAVEGAÇÃO CENTRALIZADA
# ==========================================

# Define as opções de abas
if st.session_state.usuario_perfil == "gestor":
  opcoes_menu = ["Gestão de Lançamentos", "📅 Calendário de Folgas"]
else:
  opcoes_menu = [
      "Registrar Ponto",
      "Gestão de Lançamentos",
      "📅 Calendário de Folgas",
  ]

# Sidebar
st.sidebar.title(f"⚡ Olá,\n{st.session_state.usuario_nome}")
st.sidebar.caption(f"Perfil: {st.session_state.usuario_perfil.upper()}")
st.sidebar.divider()

if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
  st.session_state.autenticado = False
  st.session_state.usuario_nome = ""
  st.session_state.usuario_perfil = ""
  st.session_state.usuario_cpf = ""
  st.rerun()

# Menu Centralizado no topo sem cortes
if "menu_selecionado" not in st.session_state:
  st.session_state.menu_selecionado = opcoes_menu[0]

menu = st.radio(
    "Navegação",
    options=opcoes_menu,
    horizontal=True,
    label_visibility="collapsed",
    key="menu_navegacao_principal",
)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# ABA 1: REGISTRAR PONTO (Apenas Técnicos)
# ==========================================
if menu == "Registrar Ponto":
  st.title("⚡ LRVIX - CONTROLE DE PONTO")
  st.markdown(
      f"Registrando ponto para: **{st.session_state.usuario_nome}**"
  )

  try:
    tecnico_cpf = st.session_state.usuario_cpf
    tecnico_nome = st.session_state.usuario_nome

    res_tec = (
        supabase.table("TECNICOS")
        .select("telegram_chat_id")
        .eq("cpf", tecnico_cpf)
        .execute()
    )
    chat_id = res_tec.data[0].get("telegram_chat_id") if res_tec.data else None

    fuso_br = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_br)

    hoje = agora.strftime("%Y-%m-%d")
    horario_atual_str = agora.strftime("%H:%M:%S")
    horario_exibicao = agora.strftime("%H:%M")
    data_formatada = agora.strftime("%d/%m/%Y")

    res_hoje = (
        supabase.table("CONTROLE_PONTO")
        .select("*")
        .eq("cpf", tecnico_cpf)
        .eq("data", hoje)
        .execute()
    )

    registro_atual = res_hoje.data[0] if res_hoje.data else {}

    tem_entrada = bool(registro_atual.get("entrada"))
    tem_saida_almoco = bool(registro_atual.get("saida_almoco"))
    tem_retorno_almoco = bool(registro_atual.get("retorno_almoco"))
    tem_saida = bool(registro_atual.get("saida"))


    def validar_intervalo(ultimo_horario_str):
      if not ultimo_horario_str:
        return True, ""
      try:
        partes = str(ultimo_horario_str).split(":")
        h, m, s = int(partes[0]), int(partes[1]), int(partes[2].split(".")[0])
        dt_ultimo = agora.replace(
            hour=h, minute=m, second=s, microsecond=0
        )
        diferenca = agora - dt_ultimo

        if diferenca < timedelta(hours=1):
          tempo_faltando = timedelta(hours=1) - diferenca
          minutos_restantes = int(tempo_faltando.total_seconds() // 60)
          return (
              False,
              f"⏳ Aguarde mais {minutos_restantes} minuto(s) para bater o"
              " próximo ponto (intervalo mínimo de 1 hora).",
          )
      except Exception as err:
        logger.error(f"Erro ao validar intervalo: {err}")
      return True, ""


    if not tem_entrada:
      if st.button(
          "🟢 REGISTRAR ENTRADA", use_container_width=True, type="primary"
      ):
        dados_upsert = {
            "cpf": tecnico_cpf,
            "data": hoje,
            "entrada": horario_atual_str,
        }
        supabase.table("CONTROLE_PONTO").upsert(
            dados_upsert, on_conflict="cpf,data"
        ).execute()
        if chat_id:
          telegram.notificar_ponto(
              str(chat_id),
              tecnico_nome,
              "ENTRADA",
              horario_exibicao,
              data_formatada,
          )
        st.success(f"ENTRADA registrada às {horario_exibicao}!")
        st.rerun()

    elif not tem_saida_almoco:
      valido, aviso = validar_intervalo(registro_atual.get("entrada"))
      if not valido:
        st.warning(aviso)
      if st.button(
          "🟡 REGISTRAR SAÍDA ALMOÇO",
          use_container_width=True,
          disabled=not valido,
          type="primary",
      ):
        if valido:
          dados_upsert = {
              "cpf": tecnico_cpf,
              "data": hoje,
              "saida_almoco": horario_atual_str,
          }
          supabase.table("CONTROLE_PONTO").upsert(
              dados_upsert, on_conflict="cpf,data"
          ).execute()
          if chat_id:
            telegram.notificar_ponto(
                str(chat_id),
                tecnico_nome,
                "SAÍDA ALMOÇO",
                horario_exibicao,
                data_formatada,
            )
          st.success(f"SAÍDA ALMOÇO registrada às {horario_exibicao}!")
          st.rerun()

    elif not tem_retorno_almoco:
      valido, aviso = validar_intervalo(registro_atual.get("saida_almoco"))
      if not valido:
        st.warning(aviso)
      if st.button(
          "🔵 REGISTRAR RETORNO ALMOÇO",
          use_container_width=True,
          disabled=not valido,
          type="primary",
      ):
        if valido:
          dados_upsert = {
              "cpf": tecnico_cpf,
              "data": hoje,
              "retorno_almoco": horario_atual_str,
          }
          supabase.table("CONTROLE_PONTO").upsert(
              dados_upsert, on_conflict="cpf,data"
          ).execute()
          if chat_id:
            telegram.notificar_ponto(
                str(chat_id),
                tecnico_nome,
                "RETORNO ALMOÇO",
                horario_exibicao,
                data_formatada,
            )
          st.success(f"RETORNO ALMOÇO registrado às {horario_exibicao}!")
          st.rerun()

    elif not tem_saida:
      valido, aviso = validar_intervalo(registro_atual.get("retorno_almoco"))
      if not valido:
        st.warning(aviso)
      if st.button(
          "🔴 REGISTRAR SAÍDA",
          use_container_width=True,
          disabled=not valido,
          type="primary",
      ):
        if valido:
          dados_upsert = {
              "cpf": tecnico_cpf,
              "data": hoje,
              "saida": horario_atual_str,
          }
          supabase.table("CONTROLE_PONTO").upsert(
              dados_upsert, on_conflict="cpf,data"
          ).execute()
          if chat_id:
            telegram.notificar_ponto(
                str(chat_id),
                tecnico_nome,
                "SAÍDA",
                horario_exibicao,
                data_formatada,
            )
          st.success(f"SAÍDA registrada às {horario_exibicao}!")
          st.rerun()
    else:
      st.success("✅ Todos os pontos de hoje já foram registrados!")

    st.markdown("---")
    st.subheader("📊 Seus Registros de Hoje")
    if registro_atual:
      df_regs = pd.DataFrame([registro_atual])
      colunas_desejadas = [
          c
          for c in [
              "data",
              "entrada",
              "saida_almoco",
              "retorno_almoco",
              "saida",
          ]
          if c in df_regs.columns
      ]
      df_regs = df_regs[colunas_desejadas].copy()
      df_regs.columns = [
          c.upper().replace("_", " ") for c in df_regs.columns
      ]
      if "DATA" in df_regs.columns:
        df_regs["DATA"] = pd.to_datetime(df_regs["DATA"]).dt.strftime(
            "%d/%m/%Y"
        )
      st.dataframe(df_regs, use_container_width=True, hide_index=True)
    else:
      st.info("Nenhum ponto registrado hoje ainda.")

  except Exception as e:
    st.error(f"Erro ao registrar ponto: {e}")

# ==========================================
# ABA 2: GESTÃO DE LANÇAMENTOS
# ==========================================
elif menu == "Gestão de Lançamentos":
  st.title("🛠️ Gestão de Lançamentos e Espelho de Ponto")

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
          st.text_input("Técnico", value=filtro_tecnico, disabled=True)
        else:
          lista_tecnicos = sorted(list(df["nome_tecnico"].unique()))
          filtro_tecnico = st.selectbox("Técnico", lista_tecnicos)

      with col_f2:
        filtro_data_inicial = st.date_input("Data Inicial", value=None)
      with col_f3:
        filtro_data_final = st.date_input("Data Final", value=None)

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
          st.markdown("---")
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
          st.dataframe(tabela_espelho, use_container_width=True, hide_index=True)
    else:
      st.info("Nenhum lançamento encontrado.")
  except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")

# ==========================================
# ABA 3: CALENDÁRIO DE FOLGAS
# ==========================================
elif menu == "📅 Calendário de Folgas":
  st.title("📅 Calendário de Folgas dos Técnicos")
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
      cpf_folga = "".join(filter(str.isdigit, str(row.get("cpf", "")))).zfill(11)
      row["nome_tecnico"] = mapa_tecnicos.get(cpf_folga, "Desconhecido")

    if st.session_state.usuario_perfil == "gestor":
      st.markdown("---")
      st.subheader("➕ Agendar Folga")
      with st.form("form_cadastrar_folga"):
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
          tec_selecionado = st.selectbox(
              "Técnico", options=sorted(list(mapa_cpf_por_nome.keys()))
          )
        with col_g2:
          data_folga = st.date_input("Data da Folga")
        with col_g3:
          motivo_folga = st.text_input("Motivo", value="Folga")

        btn_salvar_folga = st.form_submit_button(
            "💾 Salvar Folga", use_container_width=True, type="primary"
        )

        if btn_salvar_folga:
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
            opcoes_exclusao.append(f"{r['TÉCNICO']} - {r['DATA']} ({r['MOTIVO']})")

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
