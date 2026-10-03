from datetime import datetime, timedelta
import logging
import pandas as pd
import requests
import streamlit as st
from supabase import create_client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="LRVIX - CONTROLE DE PONTO", page_icon="⚡", layout="centered"
)
# Injeção de PWA e ícone personalizado para forçar o telemóvel a reconhecer
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
    botao_login = st.form_submit_button("Entrar", use_container_width=True)

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
            st.error("❌ CPF não encontrado na tabela TECNICOS.")
        except Exception as e:
          st.error(f"Erro ao conectar com o banco: {e}")
  st.stop()

# ==========================================
# APLICAÇÃO PRINCIPAL
# ==========================================
st.sidebar.title(f"⚡ Olá, {st.session_state.usuario_nome}")
st.sidebar.caption(f"Perfil: {st.session_state.usuario_perfil.upper()}")
if st.sidebar.button("🚪 Sair / Logout", use_container_width=True):
  st.session_state.autenticado = False
  st.session_state.usuario_nome = ""
  st.session_state.usuario_perfil = ""
  st.session_state.usuario_cpf = ""
  st.rerun()

# Define o menu de acordo com o perfil (Gestor não vê "Registrar Ponto")
if st.session_state.usuario_perfil == "gestor":
  opcoes_menu = ["Gestão de Lançamentos", "📅 Calendário de Folgas"]
else:
  opcoes_menu = [
      "Registrar Ponto",
      "Gestão de Lançamentos",
      "📅 Calendário de Folgas",
  ]

menu = st.sidebar.radio("Navegação", opcoes_menu)

# ==========================================
# ABA 1: REGISTRAR PONTO (Apenas Técnicos)
# ==========================================
if menu == "Registrar Ponto":
  st.title("⚡ LRVIX - CONTROLE DE PONTO")
  st.write(
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

    agora = datetime.now()
    hoje = agora.date().isoformat()
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
      ultimo_dt = datetime.strptime(
          f"{hoje} {ultimo_horario_str}", "%Y-%m-%d %H:%M:%S"
      )
      diferenca = agora - ultimo_dt
      if diferenca < timedelta(hours=1):
        tempo_faltando = timedelta(hours=1) - diferenca
        minutos_restantes = int(tempo_faltando.total_seconds() // 60)
        return (
            False,
            f"⏳ Aguarde mais {minutos_restantes} minuto(s) para bater o"
            " próximo ponto (intervalo mínimo de 1 hora).",
        )
      return True, ""


    if not tem_entrada:
      if st.button("🟢 REGISTRAR ENTRADA", use_container_width=True):
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
      ):
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
      ):
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
          "🔴 REGISTRAR SAÍDA", use_container_width=True, disabled=not valido
      ):
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

    res_tecnicos = supabase.table("TECNICOS").select("cpf, nome").execute()
    mapa_tecnicos = {}
    mapa_cpf_por_nome = {}
    for t in res_tecnicos.data or []:
      if t.get("cpf") and t.get("nome"):
        cpf_limpo = "".join(filter(str.isdigit, str(t["cpf"]))).zfill(11)
        mapa_tecnicos[cpf_limpo] = t["nome"]
        mapa_cpf_por_nome[t["nome"]] = cpf_limpo

    if dados_ponto:
      for row in dados_ponto:
        cpf_ponto = "".join(filter(str.isdigit, str(row.get("cpf", "")))).zfill(
            11
        )
        row["nome_tecnico"] = mapa_tecnicos.get(cpf_ponto, "Desconhecido")

      df = pd.DataFrame(dados_ponto)

      st.divider()
      st.subheader("🔍 Filtros de Visualização")

      col_f1, col_f2, col_f3 = st.columns(3)
      with col_f1:
        if st.session_state.usuario_perfil == "tecnico":
          filtro_tecnico = st.session_state.usuario_nome
          st.text_input("Técnico", value=filtro_tecnico, disabled=True)
        else:
          lista_tecnicos = sorted(list(df["nome_tecnico"].unique()))
          filtro_tecnico = st.selectbox("Selecione o Técnico", lista_tecnicos)

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
        st.warning("⚠ Nenhum registro encontrado para os filtros.")
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

        # Chave de liberação baseada no CPF do técnico selecionado (garante unicidade)
        cpf_tecnico_alvo = (
            st.session_state.usuario_cpf
            if st.session_state.usuario_perfil == "tecnico"
            else mapa_cpf_por_nome.get(filtro_tecnico)
        )
        chave_liberacao = f"liberado_ate_cpf_{cpf_tecnico_alvo}"
        agora_dt = datetime.now()
        liberado_ate = st.session_state.get(chave_liberacao)
        edicao_ativa = liberado_ate is not None and agora_dt < liberado_ate

        # Controles exclusivos para o GESTOR gerenciar a liberação
        if st.session_state.usuario_perfil == "gestor":
          st.divider()
          st.subheader("⚙ Controle de Edição (Gestor)")

          if edicao_ativa:
            tempo_restante = liberado_ate - agora_dt
            horas_restantes = int(tempo_restante.total_seconds() // 3600)
            minutos_restantes = int(
                (tempo_restante.total_seconds() % 3600) // 60
            )
            st.success(
                f"🔓 Edição liberada para **{filtro_tecnico}**. Expira em"
                f" {horas_restantes}h {minutos_restantes}m."
            )
            if st.button("🔒 Revogar Liberação Agora"):
              st.session_state[chave_liberacao] = None
              st.rerun()
          else:
            st.info(
                f"🔒 A edição para **{filtro_tecnico}** está bloqueada. O"
                " gestor pode liberar por 24 horas."
            )
            if st.button("🔓 Liberar Edição por 24 Horas", type="primary"):
              st.session_state[chave_liberacao] = agora_dt + timedelta(hours=24)
              st.success(f"Edição liberada para {filtro_tecnico} por 24 horas!")
              st.rerun()

        # Se a edição estiver ativa (seja logado como técnico ou gestor visualizando o técnico liberado)
        if edicao_ativa:
          if st.session_state.usuario_perfil == "tecnico":
            tempo_restante = liberado_ate - agora_dt
            horas_restantes = int(tempo_restante.total_seconds() // 3600)
            minutos_restantes = int(
                (tempo_restante.total_seconds() % 3600) // 60
            )
            st.success(
                f"🔓 Seu gestor liberou a edição dos seus lançamentos."
                f" Expira em {horas_restantes}h {minutos_restantes}m."
            )

          tabela_editada = st.data_editor(
              tabela_espelho, use_container_width=True, hide_index=True
          )

          if st.button("💾 Salvar Alterações", type="primary"):
            with st.spinner("Salvando..."):
              tec_cpf = cpf_tecnico_alvo
              for _, row in tabela_editada.iterrows():
                data_iso = (
                    datetime.strptime(row["DATA"], "%d/%m/%Y")
                    .date()
                    .isoformat()
                )
                supabase.table("CONTROLE_PONTO").upsert(
                    {
                        "cpf": tec_cpf,
                        "data": data_iso,
                        "entrada": row["ENTRADA"] or None,
                        "saida_almoco": row["SAÍDA ALMOÇO"] or None,
                        "retorno_almoco": row["RETORNO ALMOÇO"] or None,
                        "saida": row["SAÍDA"] or None,
                    },
                    on_conflict="cpf,data",
                ).execute()
              st.success("✅ Alterações salvas com sucesso!")
              st.rerun()
        else:
          if st.session_state.usuario_perfil == "tecnico":
            st.info(
                "🔒 Seus lançamentos estão bloqueados para edição. Solicite"
                " liberação ao gestor se precisar alterar algo."
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
  st.write(
      "Consulte abaixo as folgas agendadas para os técnicos da equipe."
      + (
          " Como gestor, você pode adicionar ou remover folgas."
          if st.session_state.usuario_perfil == "gestor"
          else ""
      )
  )

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
      st.divider()
      st.subheader("➕ Agendar Nova Folga")
      with st.form("form_cadastrar_folga"):
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
          tec_selecionado = st.selectbox(
              "Técnico", options=sorted(list(mapa_cpf_por_nome.keys()))
          )
        with col_g2:
          data_folga = st.date_input("Data da Folga")
        with col_g3:
          motivo_folga = st.text_input("Motivo / Descrição", value="Folga")

        btn_salvar_folga = st.form_submit_button(
            "💾 Salvar Folga", use_container_width=True
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
            st.success(
                f"✅ Folga agendada com sucesso para {tec_selecionado} em"
                f" {data_folga.strftime('%d/%m/%Y')}!"
            )
            st.rerun()
          except Exception as err:
            st.error(f"Erro ao salvar folga: {err}")

    st.divider()
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
              "Selecione a folga para remover", options=opcoes_exclusao
          )
          btn_remover = st.form_submit_button(
              "❌ Excluir Folga Selecionada", use_container_width=True
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
              st.success("✅ Folga removida com sucesso!")
              st.rerun()
            except Exception as err:
              st.error(f"Erro ao remover folga: {err}")
    else:
      st.info("Nenhuma folga cadastrada no sistema.")

  except Exception as e:
    st.error(f"Erro ao carregar o calendário de folgas: {e}")
