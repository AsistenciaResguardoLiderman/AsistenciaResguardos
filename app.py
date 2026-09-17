import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
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

# Inyección de CSS: Identidad Liderman (Rojo/Gris/Negro) + Neumorfismo 3D
st.markdown("""
    <style>
    /* Fondo general - Gris muy claro para resaltar el 3D */
    .stApp {
        background-color: #F0F2F5;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Ocultar elementos de Streamlit para efecto App Nativa */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tarjetas 3D Neumórficas */
    .card-3d {
        background: #F0F2F5;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 10px 10px 20px #D1D5DB, -10px -10px 20px #FFFFFF;
        margin-bottom: 25px;
        border-left: 5px solid #D31124; /* Rojo Liderman */
    }
    
    /* Botones Corporativos de Alta Jerarquía */
    .stButton>button {
        width: 100%;
        background-color: #D31124; /* Rojo Liderman */
        color: white;
        font-weight: bold;
        font-size: 16px;
        padding: 0.8rem;
        border-radius: 12px;
        border: none;
        box-shadow: 5px 5px 15px rgba(211, 17, 36, 0.4), -5px -5px 15px rgba(255,255,255,0.8);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #B00D1C;
        color: white;
        transform: scale(0.98);
        box-shadow: inset 3px 3px 10px rgba(0,0,0,0.3);
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #1F2937;
        font-weight: 800;
    }
    .subtext {
        color: #6B7280;
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
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

try:
    client = init_connection()
    # Tu enlace exacto
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

# Captura de GPS (Se ejecuta de forma silenciosa en el navegador)
loc = get_geolocation()
lat, lon = (loc['coords']['latitude'], loc['coords']['longitude']) if loc else (0.0, 0.0)

if menu == "🟢 Inicio de Labores (I/L)":
    st.markdown("### 📝 Registrar Ingreso (I/L)")
    
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
                    # Validamos convirtiendo a string para evitar errores de tipo en pandas
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
                    ""                        # L (Queda vacío hasta el T/L)
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
            # Filtrar activos para este DNI
            activos = df_ops[(df_ops['DNI'].astype(str) == str(dni_tl)) & (df_ops['ESTADO'] == "ACTIVO")]
            
            if activos.empty:
                st.warning("No tienes servicios marcados como 'ACTIVO' en este momento.")
            else:
                # Crear diccionario visual para el selectbox
                opciones = {}
                for idx, row in activos.iterrows():
                    # idx en pandas empieza en 0. Si la fila 1 son los encabezados, la fila de GSheets es idx + 2
                    fila_sheet = idx + 2 
                    opciones[fila_sheet] = f"{row['CLIENTE_UNIDAD']} - Iniciado a las: {row['HORA_DECLARADA']}"
                
                seleccion = st.selectbox("Seleccione el servicio a cerrar:", options=list(opciones.keys()), format_func=lambda x: opciones[x])
                
                if st.button("Registrar T/L y Cerrar"):
                    hora_cierre_sis = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Actualizar celda de ESTADO (Columna K, que es la 11)
                    ws_operaciones.update_cell(seleccion, 11, "CERRADO")
                    # Actualizar celda de HORA_TERMINO (Columna L, que es la 12)
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
                    
                    # Generación de la Tarjeta 3D en HTML
                    st.markdown(f"""
                        <div class="card-3d">
                            <h3 style="margin-top: 0; color: #D31124;">{row['CLIENTE_UNIDAD']}</h3>
                            <p style="margin: 5px 0;"><b>Estado:</b> {estado_badge}</p>
                            <p style="margin: 5px 0;"><b>Hora Ingreso (Declarada):</b> {row['HORA_DECLARADA']}</p>
                            <p style="margin: 5px 0; font-size: 12px; color: #6B7280;"><b>Log Sistema (I/L):</b> {row['FECHA_SISTEMA']}</p>
                            <p style="margin: 5px 0; font-size: 12px; color: #6B7280;"><b>Log Sistema (T/L):</b> {row.get('HORA_TERMINO_SISTEMA', 'Pendiente')}</p>
                            <hr style="border: 1px solid #E5E7EB;">
                            <a href="{row['MAPA_URL']}" target="_blank" style="color: #0044CC; font-weight: bold; text-decoration: none;">📍 Ver posición GPS del reporte</a>
                        </div>
                    """, unsafe_allow_html=True)
