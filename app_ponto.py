from datetime import datetime, timedelta
import logging
import pandas as pd
import requests
import streamlit as st
from supabase import create_client

# --- CONFIGURAÇÕES DE LOG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES DO SUPABASE ---
SUPABASE_URL = "https://ozcgilhxomoyqaejwyrs.supabase.co"
SUPABASE_KEY = "sb_publishable_lrV26hcUDDuUpG0_pXSmFQ_S2T35_ZK"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURAÇÃO DO TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8795798031:AAEjelcTRk_XQvKWak0-QCgDsl54PMq25l8"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="LRVIX - CONTROLE DE PONTO", page_icon="⚡", layout="centered"
)


# --- CLASSE PROFISSIONAL DO TELEGRAM ---
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
      response_data = response.json()
      if response_data.get("ok"):
        return True
      else:
        logger.error(f"Erro do Telegram: {response_data.get('description')}")
        return False
    except Exception as e:
      logger.error(f"Erro de conexão com o Telegram: {e}")
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

# --- CONTROLE DE SESSÃO PARA LOGIN ---
if "logado" not in st.session_state:
  st.session_state.logado = False
if "usuario_nome" not in st.session_state:
  st.session_state.usuario_nome = ""
if "usuario_perfil" not in st.session_state:
  st.session_state.usuario_perfil = ""
if "usuario_cpf" not in st.session_state:
  st.session_state.usuario_cpf = ""

# --- TELA DE LOGIN ---
if not st.session_state.logado:
  st.title("⚡ LRVIX - ACESSO AO SISTEMA")
  st.write("Digite seu CPF ou Nome para acessar o sistema de ponto.")

  input_login = st.text_input("Nome ou CPF do Usuário")

  if st.button("Entrar", type="primary"):
    if input_login.strip():
      try:
        # Tenta buscar por CPF ou Nome na tabela TECNICOS
        res = (
            supabase.table("TECNICOS")
            .select("nome, cpf, perfil, telegram_chat_id")
            .or_(f"nome.ilike.%{input_login}%,cpf.eq.{input_login}")
            .execute()
        )

        if res.data:
          user_data = res.data[0]
          st.session_state.logado = True
          st.session_state.usuario_nome = user_data["nome"]
          st.session_state.usuario_cpf = user_data["cpf"]
          # Se a coluna perfil existir, usa ela; senão, define TÉCNICO por padrão
          st.session_state.usuario_perfil = user_data.get("perfil", "TECNICO")
          st.session_state.telegram_chat_id = user_data.get(
              "telegram_chat_id"
          )
          st.success(
              f"Bem-vindo(a), {st.session_state.usuario_nome}! Entrando..."
          )
          st.rerun()
        else:
          st.error(
              "⚠️ Usuário não encontrado. Verifique os dados informados."
          )
      except Exception as e:
        st.error(f"Erro ao realizar login: {e}")
    else:
      st.warning("Por favor, digite seu nome ou CPF.")

else:
  # --- MENU LATERAL ---
  st.sidebar.title(f"⚡ Olá, {st.session_state.usuario_nome}")
  st.sidebar.write(f"Perfil: **{st.session_state.usuario_perfil}**")

  if st.sidebar.button("🚪 Sair / Logout"):
    st.session_state.logado = False
    st.session_state.usuario_nome = ""
    st.session_state.usuario_perfil = ""
    st.session_state.usuario_cpf = ""
    st.rerun()

  st.sidebar.divider()
  st.sidebar.title("Navegação")

  # Define as opções do menu com base no perfil
  opcoes_menu = ["Gestão de Lançamentos", "Calendário de Folgas"]
  if st.session_state.usuario_perfil == "GESTOR":
    opcoes_menu.insert(0, "Registrar Ponto")
  else:
    opcoes_menu.insert(0, "Registrar Ponto")

  menu = st.sidebar.radio("Ir para", opcoes_menu)

  # ==========================================
  # ABA 1: REGISTRAR PONTO
  # ==========================================
  if menu == "Registrar Ponto":
    st.title("⚡ LRVIX - CONTROLE DE PONTO")
    st.write(
        f"Registrando ponto para: **{st.session_state.usuario_nome}**"
    )

    tecnico_nome = st.session_state.usuario_nome
    tecnico_cpf = st.session_state.usuario_cpf
    chat_id = st.session_state.get("telegram_chat_id")

    if not chat_id:
      st.warning(
          "⚠️ O seu 'telegram_chat_id' não está configurado no cadastro."
      )

    agora = datetime.now()
    hoje = agora.date().isoformat()
    horario_atual_str = agora.strftime("%H:%M")
    data_formatada = agora.strftime("%d/%m/%Y")

    try:
      res_logs = (
          supabase.table("controle_ponto")
          .select("tipo_ponto, horario, data")
          .eq("cpf", tecnico_cpf)
          .eq("data", hoje)
          .order("horario", desc=True)
          .execute()
      )

      registros = res_logs.data or []
      tipos_registrados = [
          item["tipo_ponto"].upper()
          for item in registros
          if item.get("tipo_ponto")
      ]

      pode_bater = True
      tempo_restante_msg = ""

      if registros:
        ultima_batida_str = str(registros[0]["horario"])
        partes_horario = ultima_batida_str.split(":")
        h, m = int(partes_horario[0]), int(partes_horario[1])
        ultima_batida_dt = agora.replace(
            hour=h, minute=m, second=0, microsecond=0
        )
        diferenca = agora - ultima_batida_dt

        if diferenca < timedelta(hours=1):
          pode_bater = False
          minutos_restantes = int((timedelta(hours=1) - diferenca).seconds / 60)
          tempo_restante_msg = (
              f"⏳ Você registrou um ponto recentemente às"
              f" `{partes_horario[0]}:{partes_horario[1]}`. Aguarde mais"
              f" **{minutos_restantes} minutos** (intervalo mínimo de 1 hora)."
          )

      if not pode_bater and len(tipos_registrados) < 4:
        st.warning(tempo_restante_msg)

      if "ENTRADA" not in tipos_registrados:
        if st.button("🟢 REGISTRAR ENTRADA", use_container_width=True):
          if pode_bater:
            supabase.table("controle_ponto").insert({
                "cpf": tecnico_cpf,
                "tipo_ponto": "ENTRADA",
                "horario": horario_atual_str,
                "data": hoje,
            }).execute()
            if chat_id:
              telegram.notificar_ponto(
                  str(chat_id),
                  tecnico_nome,
                  "ENTRADA",
                  horario_atual_str,
                  data_formatada,
              )
            st.success(f"ENTRADA registrada às {horario_atual_str}!")
            st.rerun()
          else:
            st.error("Ação bloqueada: Respeite o intervalo mínimo de 1 hora.")

      elif "SAÍDA ALMOÇO" not in tipos_registrados:
        if st.button("🟡 REGISTRAR SAÍDA ALMOÇO", use_container_width=True):
          if pode_bater:
            supabase.table("controle_ponto").insert({
                "cpf": tecnico_cpf,
                "tipo_ponto": "SAÍDA ALMOÇO",
                "horario": horario_atual_str,
                "data": hoje,
            }).execute()
            if chat_id:
              telegram.notificar_ponto(
                  str(chat_id),
                  tecnico_nome,
                  "SAÍDA ALMOÇO",
                  horario_atual_str,
                  data_formatada,
              )
            st.success(f"SAÍDA ALMOÇO registrada às {horario_atual_str}!")
            st.rerun()
          else:
            st.error("Ação bloqueada: Respeite o intervalo mínimo de 1 hora.")

      elif "RETORNO ALMOÇO" not in tipos_registrados:
        if st.button("🔵 REGISTRAR RETORNO ALMOÇO", use_container_width=True):
          if pode_bater:
            supabase.table("controle_ponto").insert({
                "cpf": tecnico_cpf,
                "tipo_ponto": "RETORNO ALMOÇO",
                "horario": horario_atual_str,
                "data": hoje,
            }).execute()
            if chat_id:
              telegram.notificar_ponto(
                  str(chat_id),
                  tecnico_nome,
                  "RETORNO ALMOÇO",
                  horario_atual_str,
                  data_formatada,
              )
            st.success(f"RETORNO ALMOÇO registrado às {horario_atual_str}!")
            st.rerun()
          else:
            st.error("Ação bloqueada: Respeite o intervalo mínimo de 1 hora.")

      elif "SAÍDA" not in tipos_registrados:
        if st.button("🔴 REGISTRAR SAÍDA", use_container_width=True):
          if pode_bater:
            supabase.table("controle_ponto").insert({
                "cpf": tecnico_cpf,
                "tipo_ponto": "SAÍDA",
                "horario": horario_atual_str,
                "data": hoje,
            }).execute()
            if chat_id:
              telegram.notificar_ponto(
                  str(chat_id),
                  tecnico_nome,
                  "SAÍDA",
                  horario_atual_str,
                  data_formatada,
              )
            st.success(f"SAÍDA registrada às {horario_atual_str}!")
            st.rerun()
          else:
            st.error("Ação bloqueada: Respeite o intervalo mínimo de 1 hora.")
      else:
        st.success("✅ Todos os pontos de hoje já foram registrados!")

      st.subheader("📊 Seus Registros de Hoje")
      if registros:
        st.dataframe(registros, use_container_width=True)
      else:
        st.info("Nenhum ponto registrado hoje ainda.")

    except Exception as e:
      st.error(f"Erro ao carregar os registros: {e}")

  # ==========================================
  # ABA 2: GESTÃO DE LANÇAMENTOS (COM EDIÇÃO ATIVADA)
  # ==========================================
  elif menu == "Gestão de Lançamentos":
    st.title("🛠️ Gestão de Lançamentos e Espelho de Ponto")

    try:
      # Busca técnicos cadastrados
      res_tec = supabase.table("TECNICOS").select("nome, cpf").execute()
      lista_tecnicos = res_tec.data or []
      mapa_cpfs = {t["nome"]: t["cpf"] for t in lista_tecnicos if t.get("nome")}
      nomes_tecnicos = list(mapa_cpfs.keys())

      st.markdown("### 🔍 Filtros de Visualização")
      col1, col2, col3 = st.columns(3)

      with col1:
        # Se for técnico, fixa o nome dele; se for gestor, permite selecionar qualquer um
        if st.session_state.usuario_perfil == "GESTOR":
          tec_selecionado = st.selectbox(
              "Selecione o Técnico", ["Todos"] + nomes_tecnicos
          )
        else:
          tec_selecionado = st.selectbox(
              "Selecione o Técnico", [st.session_state.usuario_nome]
          )

      with col2:
        data_inicial = st.date_input(
            "Data Inicial", value=None, format="DD/MM/YYYY"
        )

      with col3:
        data_final = st.date_input(
            "Data Final", value=None, format="DD/MM/YYYY"
        )

      # Botão para habilitar a edição
      habilitar_edicao = st.toggle("✏️ Habilitar Edição de Horários no Espelho")

      # Consulta base na tabela controle_ponto
      query = supabase.table("controle_ponto").select("*")

      if tec_selecionado != "Todos":
        cpf_filtro = mapa_cpfs.get(tec_selecionado)
        if cpf_filtro:
          query = query.eq("cpf", cpf_filtro)

      res_pontos = query.execute()
      dados = res_pontos.data or []

      if dados:
        df = pd.DataFrame(dados)

        # Filtro por data via pandas se informado
        if data_inicial:
          df = df[df["data"] >= str(data_inicial)]
        if data_final:
          df = df[df["data"] <= str(data_final)]

        if not df.empty:
          # Adiciona nome legível do técnico
          mapa_nomes_rev = {v: k for k, v in mapa_cpfs.items()}
          df["nome_tecnico"] = df["cpf"].map(mapa_nomes_rev)

          if habilitar_edicao:
            st.info(
                "💡 Altere os horários ou dados diretamente na tabela abaixo e"
                " clique em salvar."
            )
            # Tabela interativa para edição completa
            df_editado = st.data_editor(
                df, use_container_width=True, key="editor_ponto_gestao"
            )

            if st.button("💾 Salvar Alterações", type="primary"):
              with st.spinner("Salvando alterações no Supabase..."):
                try:
                  registros_atualizados = df_editado.to_dict(orient="records")
                  for row in registros_atualizados:
                    row_limpo = {
                        k: v
                        for k, v in row.items()
                        if k
                        in [
                            "id",
                            "cpf",
                            "data",
                            "horario",
                            "tipo_ponto",
                            "created_at",
                        ]
                        and pd.notna(v)
                    }
                    if "id" in row_limpo and pd.notna(row_limpo["id"]):
                      rid = row_limpo.pop("id")
                      supabase.table("controle_ponto").update(row_limpo).eq(
                          "id", rid
                      ).execute()
                  st.success(
                      "✅ Alterações salvas e sincronizadas com sucesso!"
                  )
                  st.rerun()
                except Exception as ex:
                  st.error(f"Erro ao salvar alterações: {ex}")
          else:
            # Exibição padrão em formato de tabela limpa
            colunas_exibir = [
                col
                for col in [
                    "id",
                    "nome_tecnico",
                    "data",
                    "horario",
                    "tipo_ponto",
                ]
                if col in df.columns
            ]
            st.dataframe(df[colunas_exibir], use_container_width=True)
        else:
          st.info("Nenhum registro encontrado para os filtros selecionados.")
      else:
        st.info("Nenhum lançamento de ponto cadastrado.")

    except Exception as e:
      st.error(f"Erro ao carregar dados de gestão: {e}")

  # ==========================================
  # ABA 3: CALENDÁRIO DE FOLGAS
  # ==========================================
  elif menu == "Calendário de Folgas":
    st.title("📅 Calendário de Folgas")
    st.info("Módulo de folgas integrado ao sistema.")