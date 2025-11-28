import streamlit as st
import pandas as pd
import math
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="CS Naves Industriales V2.2",
    page_icon="🏭",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS ---
st.markdown("""
    <style>
    .main-header { font-size: 28px; font-weight: bold; color: #0E4F8F; text-align: center; margin-bottom: 0px; }
    .sub-header { font-size: 18px; color: #666; text-align: center; margin-top: 5px; }
    .highlight { background-color: #E8F4F8; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #0E4F8F; text-align: center; }
    .success-box { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; border: 1px solid #c3e6cb; }
    .warning-box { padding: 10px; background-color: #fff3cd; color: #856404; border-radius: 5px; border: 1px solid #ffeeba; }
    .danger-box { padding: 10px; background-color: #f8d7da; color: #721c24; border-radius: 5px; border: 1px solid #f5c6cb; }
    </style>
""", unsafe_allow_html=True)

# --- 3. INICIALIZACIÓN DE VARIABLES (BLINDADA) ---
if 'project_data' not in st.session_state:
    st.session_state['project_data'] = {'nombre': '', 'ubicacion': '', 'alt': 0, 'temp': 25}
if 'calc_res' not in st.session_state:
    st.session_state['calc_res'] = {} 
if 'louver_res' not in st.session_state:
    st.session_state['louver_res'] = {} 

# --- 4. BASES DE DATOS ---
db_ach = {
    "Almacén General / Logística": [4, 6, 10],
    "Almacén (Papel/Cartón)": [6, 8, 12],
    "Almacén (Productos Químicos)": [10, 15, 20],
    "Nave de Proceso (Ensamble ligero)": [6, 8, 12],
    "Nave de Proceso (Maquinado/CNC)": [10, 15, 20],
    "Nave de Proceso (Plásticos/Inyección)": [15, 20, 30],
    "Fundición y Tratamientos Térmicos": [30, 40, 60],
    "Taller de Soldadura / Pintura": [20, 30, 40],
    "Cuarto de Máquinas / Compresores": [20, 30, 40],
    "Cuarto de Transformadores": [15, 20, 30],
    "Lavanderías Industriales": [15, 20, 30],
    "Gimnasios / Centros Deportivos": [8, 12, 15]
}

db_geo = {
    "Aguascalientes": {"Aguascalientes": {"alt": 1888, "temp": 26}, "Jesus Maria": {"alt": 1890, "temp": 26}},
    "Baja California": {"Tijuana": {"alt": 20, "temp": 26}, "Mexicali": {"alt": 8, "temp": 42}},
    "CDMX": {"Centro": {"alt": 2240, "temp": 24}, "Santa Fe": {"alt": 2500, "temp": 21}},
    "Jalisco": {"Guadalajara": {"alt": 1566, "temp": 28}, "Puerto Vallarta": {"alt": 10, "temp": 32}},
    "Nuevo Leon": {"Monterrey": {"alt": 540, "temp": 35}, "San Pedro": {"alt": 600, "temp": 34}},
    "Puebla": {"Puebla": {"alt": 2135, "temp": 25}, "Cholula": {"alt": 2150, "temp": 25}},
    "Queretaro": {"Queretaro": {"alt": 1820, "temp": 28}, "San Juan del Rio": {"alt": 1920, "temp": 27}},
    "Sinaloa": {"Culiacan": {"alt": 54, "temp": 36}, "Mazatlan": {"alt": 10, "temp": 32}, "Los Mochis": {"alt": 10, "temp": 35}},
    "Sonora": {"Hermosillo": {"alt": 210, "temp": 40}, "Cd Obregon": {"alt": 40, "temp": 39}},
    "Veracruz": {"Veracruz": {"alt": 10, "temp": 30}, "Coatzacoalcos": {"alt": 10, "temp": 32}},
    "Yucatan": {"Merida": {"alt": 10, "temp": 36}, "Valladolid": {"alt": 20, "temp": 34}}
}

def get_louver_free_area(width_in, height_in):
    # Área bruta en ft2
    if width_in < 12 or height_in < 12: return 0
    # Fórmula de regresión ajustada a tabla de L. Galvanizada
    area_val = ((width_in - 4.0) * (height_in - 2.5)) / 144 * 0.67
    return round(area_val, 2)

# --- 5. SIDEBAR ---
with st.sidebar:
    try:
        st.image("LOGO ONLINE.jpg", use_column_width=True) 
    except:
        st.header("CS VENTILACIÓN")
    
    st.markdown("---")
    
    with st.expander("📍 Datos del Proyecto", expanded=True):
        nombre_proyecto = st.text_input("Nombre del Proyecto", placeholder="Ej. Nave Industrial Park 1")
        pais = st.selectbox("País", ["México", "Otro"])
        
        ciudad_selec = ""
        estado_selec = ""
        alt_val = 0
        temp_val = 25
        
        if pais == "México":
            estado_selec = st.selectbox("Estado", sorted(list(db_geo.keys())))
            if estado_selec:
                lista_ciudades = list(db_geo[estado_selec].keys())
                ciudad_selec = st.selectbox("Ciudad", lista_ciudades)
                
                if ciudad_selec:
                    datos = db_geo[estado_selec][ciudad_selec]
                    alt_val = datos['alt']
                    temp_val = datos['temp']
                    
                    c1, c2 = st.columns(2)
                    with c1: st.metric("Altitud", f"{alt_val} m")
                    with c2: st.metric("Temp", f"{temp_val}°C")
        else:
            ciudad_selec = st.text_input("Ciudad / Ubicación", "Generica")
            alt_val = st.number_input("Altitud (msnm)", 0)
            temp_val = st.number_input("Temperatura (°C)", 25)
        
        st.session_state['project_data'] = {
            "nombre": nombre_proyecto,
            "ubicacion": f"{ciudad_selec}, {estado_selec}" if pais == "México" else ciudad_selec,
            "alt": alt_val,
            "temp": temp_val
        }

# --- 6. MAIN UI ---
st.markdown('<div class="main-header">CALCULADORA NAVES INDUSTRIALES</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Método: Cambios de Aire por Hora (ACH)</div>', unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["1️⃣ Caudal (ACH)", "2️⃣ Entrada Aire", "3️⃣ Selección"])

# --- TAB 1: CÁLCULO ACH ---
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        area = st.number_input("Área de la Nave (m²)", 50.0, 50000.0, 1000.0, 10.0)
    with c2:
        altura = st.number_input("Altura Promedio (m)", 2.0, 30.0, 8.0, 0.25)
        
    volumen = area * altura
    
    st.markdown(f"""
    <div class="highlight">
        <h3 style="margin:0; color:#0E4F8F;">Volumen Total:</h3>
        <h2 style="margin:0; color:#333;">{volumen:,.2f} m³</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### Selección de Cambios de Aire")
    app_selec = st.selectbox("Aplicación / Actividad", list(db_ach.keys()))
    
    rangos = db_ach[app_selec] # [Min, Med, Max]
    t_ref = st.session_state['project_data']['temp']
    
    if t_ref < 25:
        sug_val = rangos[0]
        msg = f"❄️ Clima Fresco (<25°C): Se sugiere el **Mínimo ({sug_val} ACH)**."
        st.info(msg)
    elif 25 <= t_ref <= 32:
        sug_val = rangos[1]
        msg = f"☀️ Clima Templado (25-32°C): Se sugiere el **Medio ({sug_val} ACH)**."
        st.warning(msg)
    else:
        sug_val = rangos[2]
        msg = f"🔥 Clima Cálido (>32°C): Se sugiere el **Máximo ({sug_val} ACH)**."
        st.error(msg)
        
    ach_input = st.number_input("Cambios/Hora a utilizar:", 1, 100, sug_val)
    
    q_m3hr = volumen * ach_input
    q_cfm = q_m3hr / 1.699
    
    st.markdown("---")
    st.markdown("#### Configuración de Equipos")
    
    cc1, cc2 = st.columns(2)
    with cc1:
        st.metric("Caudal Total Requerido", f"{int(q_cfm):,} CFM")
        
    with cc2:
        qty_eq = st.number_input("Número de Extractores", 1, 100, 4)
        cfm_unit = q_cfm / qty_eq
        st.metric("Caudal por Equipo", f"{int(cfm_unit):,} CFM")
        
    if st.button("✅ Confirmar Caudal"):
        st.session_state['calc_res'] = {
            "volumen": volumen,
            "ach": ach_input,
            "q_total": int(q_cfm),
            "qty": qty_eq,
            "q_unit": int(cfm_unit),
            "app": app_selec
        }
        st.success("Datos guardados.")

# --- TAB 2: LOUVERS ---
with tab2:
    # Verificación segura con .get()
    if st.session_state['calc_res'].get('q_total', 0) > 0:
        q_total = st.session_state['calc_res']['q_total']
        num_ex = st.session_state['calc_res']['qty'] 
        
        st.info(f"Caudal Total a Reponer: **{q_total:,} CFM**")
        
        tipo_entrada = st.radio("Tipo de Entrada de Aire", ["Louvers de Admisión", "Entrada Natural (Portones/Huecos)"])
        
        vel_louver = 0
        sp_louver = 0.0
        
        if tipo_entrada == "Louvers de Admisión":
            default_qty_l = num_ex * 2
            
            st.markdown("**Dimensiones del Louver (Pulgadas)**")
            dims_options = [12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96]
            
            c_dim1, c_dim2, c_qty = st.columns(3)
            with c_dim1:
                w_louver = st.selectbox("Ancho (in)", dims_options, index=6)
            with c_dim2:
                h_louver = st.selectbox("Alto (in)", dims_options, index=6)
            with c_qty:
                cant_louvers = st.number_input("Cantidad Pzas", 1, 500, default_qty_l)
            
            area_libre_unit = get_louver_free_area(w_louver, h_louver)
            area_libre_total = area_libre_unit * cant_louvers
            
            st.caption(f"Área Libre por pza (Tabla): {area_libre_unit} ft² | Total: {area_libre_total:.1f} ft²")
            
            if area_libre_total > 0:
                vel_louver = q_total / area_libre_total
            else:
                vel_louver = 0
            
            st.metric("Velocidad de Paso Resultante", f"{int(vel_louver)} FPM")
            
            if vel_louver <= 1050:
                st.markdown('<div class="success-box">✅ <strong>VELOCIDAD CORRECTA</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="danger-box">⛔ <strong>VELOCIDAD EXCESIVA (>1050)</strong></div>', unsafe_allow_html=True)
            
            # Fórmula cuadrática ajustada
            sp_louver = (vel_louver / 2350) ** 2
            st.caption(f"Caída de Presión Estimada: {sp_louver:.3f} in wg")
            
        else:
            st.info("Entrada natural.")
            sp_louver = 0.05
            
        if st.button("✅ Confirmar Entrada"):
            st.session_state['louver_res'] = {
                "tipo": tipo_entrada,
                "dims": f"{cant_louvers} pzas de {w_louver}\"x{h_louver}\"" if tipo_entrada == "Louvers de Admisión" else "Natural",
                "vel": int(vel_louver),
                "sp": sp_louver
            }
            st.success("Configuración guardada.")
            
    else:
        st.warning("Calcula el caudal primero.")

# --- TAB 3: SELECCIÓN ---
with tab3:
    # Verificación segura de existencia
    if st.session_state['louver_res'].get('sp', 0) > 0 or st.session_state['louver_res'].get('tipo') == "Entrada Natural (Portones/Huecos)":
        
        res_q = st.session_state['calc_res']
        res_l = st.session_state['louver_res']
        
        st.markdown("#### 1. Caída de Presión Total")
        sp_base = res_l['sp']
        st.write(f"Presión Louvers/Entrada: **{sp_base:.3f} in wg**")
        
        st.markdown("**Accesorios del Extractor:**")
        c1, c2 = st.columns(2)
        with c1:
            malla = st.checkbox("Malla de Protección", value=True)
            persiana = st.checkbox("Persiana de Gravedad", value=True)
        with c2:
            copete = st.checkbox("Cubierta Intemperie", value=False)
        
        sp_acc = 0.0
        if malla: sp_acc += 0.05
        if persiana: sp_acc += 0.10
        if copete: sp_acc += 0.12
        
        sp_total = sp_base + sp_acc
        
        st.markdown(f"""
        <div class="highlight">
            <h3 style="margin:0; color:#333;">Presión Estática Total (SP): {sp_total:.3f} in wg</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 2. Especificación del Equipo")
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            montaje = st.radio("Montaje", ["Muro", "Tejado"])
            alimentacion = st.radio("Alimentación Eléctrica", ["1.- Monofásico", "2.- Trifásico"])
        
        with col_sel2:
            prioridad = st.radio("Prioridad", ["Costo Inicial", "Bajo Ruido", "Eficiencia Energética"])
            ambiente = st.selectbox("Tipo de Aire", ["Limpio", "Corrosivo", "Explosivo (ATEX)"])
            
        st.markdown("---")
        st.markdown("### 📤 Enviar Solicitud")
        
        loc = st.session_state['project_data']
        subject_raw = f"Cotización Nave: {loc['nombre']}"
        
        body_raw = f"""Hola Ing. Sotelo,

Solicito cotización para ventilación de Nave Industrial:

1. DATOS DEL PROYECTO:
- Proyecto: {loc['nombre']}
- Ubicación: {loc['ubicacion']} (Alt: {loc['alt']}m | Temp: {loc['temp']}C)

2. CÁLCULO DE INGENIERÍA (ACH):
- Aplicación: {res_q['app']}
- Volumen: {res_q['volumen']:,.0f} m3
- Renovaciones: {res_q['ach']} ACH (Base Temp: {loc['temp']}C)
- CAUDAL TOTAL: {res_q['q_total']:,} CFM
- Entrada Aire: {res_l['tipo']} ({res_l.get('dims','')}) 
- Vel. Paso: {res_l.get('vel',0)} FPM

3. SELECCIÓN DE EQUIPOS:
- Cantidad: {res_q['qty']} Equipos
- Capacidad c/u: {res_q['q_unit']:,} CFM
- PRESIÓN ESTÁTICA: {sp_total:.3f} in wg
- Montaje: {montaje}
- Alimentación: {alimentacion}
- Tipo Aire: {ambiente}
- Prioridad: {prioridad}

Accesorios: Malla={malla}, Persiana={persiana}, Copete={copete}.

Quedo atento."""

        safe_sub = urllib.parse.quote(subject_raw)
        safe_body = urllib.parse.quote(body_raw)
        mailto = f"mailto:ventas@csventilacion.mx?subject={safe_sub}&body={safe_body}"
        
        st.markdown(f"""
        <a href="{mailto}" target="_blank" style="
            display: block;
            background-color: #28a745;
            color: white;
            padding: 15px;
            text-align: center;
            text-decoration: none;
            font-weight: bold;
            border-radius: 5px;
            font-size: 18px;">
            📧 GENERAR CORREO DE SOLICITUD
        </a>
        """, unsafe_allow_html=True)
        
    else:
        st.info("Completa los pasos 1 y 2.")
