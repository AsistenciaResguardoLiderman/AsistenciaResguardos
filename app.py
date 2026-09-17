import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from streamlit_js_eval import get_geolocation

# ==========================================
# 1. CONFIGURACIÓN DEL SERVIDOR Y UX/UI
# ==========================================
st.set_page_config(
    page_title="App Resguardos | Liderman",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inyección de CSS: Identidad Liderman Adaptable + Neumorfismo 3D
st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit para efecto App Nativa */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tarjetas 3D Neumórficas Adaptables (Modo Oscuro/Claro) */
    .card-3d {
        background-color: var(--secondary-background-color);
        padding: 25px;
        border-radius: 16px;
        box-shadow: 4px 4px 15px rgba(0,0,0,0.1), -4px -4px 15px rgba(255,255,255,0.05);
        margin-bottom: 25px;
        border-left: 5px solid #D31124;
        color: var(--text-color);
    }
    
    /* Botones Corporativos de Alta Jerarquía */
    .stButton>button {
        width: 100%;
        background-color: #D31124;
        color: white !important;
        font-weight: bold;
        font-size: 16px;
        padding: 0.8rem;
        border-radius: 12px;
        border: none;
        box-shadow: 3px 3px 10px rgba(211, 17, 36, 0.3);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #B00D1C;
        transform: scale(0.98);
    }
    
    /* Títulos Adaptables */
    h1, h2, h3 {
        color: var(--text-color) !important;
        font-weight: 800;
    }
    .subtext {
        color: var(--text-color);
        opacity: 0.7;
        font-size: 14px;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE BASE DE DATOS (GOOGLE SHEETS)
# ==========================================
@st.cache_resource
def init_connection():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Cargamos los secretos directamente como diccionario seguro
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

try:
    client = init_connection()
    sheet_url = "https://docs.google.com/spreadsheets/d/1JISC5gwxN1sowk29E26FBCR6EfmA5bzfd9OdDVpU4yE/edit"
    sh = client.open_by_url(sheet_url)
    ws_personal = sh.worksheet("MAESTRO_PERSONAL")
    ws_operaciones = sh.worksheet("REGISTROS_OPERACIONES")
except Exception as e:
    st.error(f"Error crítico en el backend: No se pudo conectar a la base de datos. Detalles: {e}")
    st.stop()

# ==========================================
# 3. INTERFAZ Y NAVEGACIÓN
# ==========================================
st.markdown("<h1 style='text-align: center;'>🛡️ LIDERMAN OPs</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Portal de Control de Resguardos y Auditoría de Campo</div>", unsafe_allow_html=True)

menu = st.radio(
    "Menú de Operaciones:",
    ["🟢 Inicio de Labores (I/L)", "🔴 Término de Labores (T/L)", "📊 Mis Servicios (Historial)"],
    horizontal=True
)

st.markdown("---")

# ==========================================
# 4. LÓGICA DE NEGOCIO Y OPERACIONES
# ==========================================

if menu == "🟢 Inicio de Labores (I/L)":
    st.markdown("### 📝 Registrar Ingreso (I/L)")
    
    # Captura de GPS condicionada y segura a prueba de fallos
    loc = get_geolocation()
    
    if isinstance(loc, dict) and 'coords' in loc:
        lat = loc['coords'].get('latitude', 0.0)
        lon = loc['coords'].get('longitude', 0.0)
    else:
        lat, lon = 0.0, 0.0
    
    with st.form("form_il", clear_on_submit=True):
        dni_input = st.text_input("Nº de DNI del Resguardo", max_chars=8)
        cliente_input = st.text_input("Cliente y/o Unidad (Ej. Minera Ares)")
        hora_declarada = st.time_input("Hora declarada de ingreso", value=datetime.now().time())
        
        submit_il = st.form_submit_button("Registrar I/L")
        
        if submit_il:
            if not dni_input or not cliente_input:
                st.error("⚠️ El DNI y la Unidad son campos obligatorios.")
            else:
                # 1. Búsqueda en Maestro de Personal
                df_personal = pd.DataFrame(ws_personal.get_all_records())
                nombre_resguardo = "USUARIO NO REGISTRADO"
                codigo_resguardo = "S/C"
                
                if not df_personal.empty:
                    match = df_personal[df_personal['DNI'].astype(str) == str(dni_input)]
                    if not match.empty:
                        nombre_resguardo = match.iloc[0].get('NOMBRES', 'Sin Nombre')
                        codigo_resguardo = match.iloc[0].get('CODIGO', 'S/C')
                
                # 2. Variables de Auditoría
                fecha_hora_sis = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                mapa_url = f"https://www.google.com/maps?q={lat},{lon}" if lat != 0.0 else "Ubicación Bloqueada"
                
                # 3. Inserción en Base de Datos
                ws_operaciones.append_row([
                    fecha_hora_sis,           # A
                    str(dni_input),           # B
                    str(nombre_resguardo),    # C
                    str(codigo_resguardo),    # D
                    "I/L",                    # E
                    str(cliente_input.upper()), # F
                    str(hora_declarada),      # G
                    str(lat),                 # H
                    str(lon),                 # I
                    mapa_url,                 # J
                    "ACTIVO",                 # K
                    ""                        # L
                ])
                
                st.success(f"✅ I/L registrado exitosamente para: **{nombre_resguardo}**")
                st.info(f"Auditoría: Hora de sistema capturada a las {fecha_hora_sis}")

elif menu == "🔴 Término de Labores (T/L)":
    st.markdown("### 🔒 Cerrar Servicio (T/L)")
    
    dni_tl = st.text_input("Ingrese su DNI para buscar servicios abiertos", max_chars=8)
    
    if dni_tl:
        registros = ws_operaciones.get_all_records()
        df_ops = pd.DataFrame(registros)
        
        if not df_ops.empty:
            activos = df_ops[(df_ops['DNI'].astype(str) == str(dni_tl)) & (df_ops['ESTADO'] == "ACTIVO")]
            
            if activos.empty:
                st.warning("No tienes servicios marcados como 'ACTIVO' en este momento.")
            else:
                opciones = {}
                for idx, row in activos.iterrows():
                    fila_sheet = idx + 2 
                    opciones[fila_sheet] = f"{row['CLIENTE_UNIDAD']} - Iniciado a las: {row['HORA_DECLARADA']}"
                
                seleccion = st.selectbox("Seleccione el servicio a cerrar:", options=list(opciones.keys()), format_func=lambda x: opciones[x])
                
                if st.button("Registrar T/L y Cerrar"):
                    hora_cierre_sis = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ws_operaciones.update_cell(seleccion, 11, "CERRADO")
                    ws_operaciones.update_cell(seleccion, 12, hora_cierre_sis)
                    
                    st.success("✅ Servicio finalizado y tareado correctamente.")
        else:
            st.info("La base de datos de operaciones está limpia.")

elif menu == "📊 Mis Servicios (Historial)":
    st.markdown("### 📋 Historial y Auditoría Personal")
    
    dni_hist = st.text_input("Ingrese DNI para ver el registro histórico", max_chars=8)
    
    if dni_hist:
        df_ops = pd.DataFrame(ws_operaciones.get_all_records())
        
        if not df_ops.empty:
            historial = df_ops[df_ops['DNI'].astype(str) == str(dni_hist)].sort_values(by="FECHA_SISTEMA", ascending=False)
            
            if historial.empty:
                st.warning("No hay registros previos para este DNI.")
            else:
                st.markdown(f"**Total de registros encontrados:** {len(historial)}")
                
                for _, row in historial.iterrows():
                    estado_badge = "🟢 ACTIVO" if row['ESTADO'] == "ACTIVO" else "🔴 CERRADO"
                    
                    st.markdown(f"""
                        <div class="card-3d">
                            <h3 style="margin-top: 0; color: #D31124;">{row['CLIENTE_UNIDAD']}</h3>
                            <p style="margin: 5px 0;"><b>Estado:</b> {estado_badge}</p>
                            <p style="margin: 5px 0;"><b>Hora Ingreso (Declarada):</b> {row['HORA_DECLARADA']}</p>
                            <p style="margin: 5px 0; font-size: 12px; opacity: 0.8;"><b>Log Sistema (I/L):</b> {row['FECHA_SISTEMA']}</p>
                            <p style="margin: 5px 0; font-size: 12px; opacity: 0.8;"><b>Log Sistema (T/L):</b> {row.get('HORA_TERMINO_SISTEMA', 'Pendiente')}</p>
                            <hr style="border: 1px solid rgba(128,128,128,0.2);">
                            <a href="{row['MAPA_URL']}" target="_blank" style="color: #D31124; font-weight: bold; text-decoration: none;">📍 Ver posición GPS del reporte</a>
                        </div>
                    """, unsafe_allow_html=True)
