import streamlit as st
import pandas as pd
import math
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="CS Naves Industriales",
    page_icon="🏭",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS ---
st.markdown("""
    <style>
    .main-header { font-size: 28px; font-weight: bold; color: #0E4F8F; text-align: center; margin-bottom: 0px; }
    .sub-header { font-size: 18px; color: #666; text-align: center; margin-top: 5px; }
    .highlight { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #0E4F8F; }
    .success-box { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; border: 1px solid #c3e6cb; }
    .warning-box { padding: 10px; background-color: #fff3cd; color: #856404; border-radius: 5px; border: 1px solid #ffeeba; }
    .danger-box { padding: 10px; background-color: #f8d7da; color: #721c24; border-radius: 5px; border: 1px solid #f5c6cb; }
    </style>
""", unsafe_allow_html=True)

# --- 3. BASE DE DATOS (ACH y CIUDADES) ---

# Base de Datos de ACH (Extraída de tu imagen)
# Formato: "Aplicación": [Min, Med, Max]
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

# Base de Datos Geográfica (Simplificada Vertical)
db_geo = {}
db_geo["Aguascalientes"] = {"Aguascalientes": {"alt": 1888, "temp": 26}}
db_geo["Baja California"] = {"Tijuana": {"alt": 20, "temp": 26}, "Mexicali": {"alt": 8, "temp": 42}}
db_geo["CDMX"] = {"Centro": {"alt": 2240, "temp": 24}, "Santa Fe": {"alt": 2500, "temp": 21}}
db_geo["Chihuahua"] = {"Chihuahua": {"alt": 1435, "temp": 30}, "Cd Juarez": {"alt": 1120, "temp": 32}}
db_geo["Jalisco"] = {"Guadalajara": {"alt": 1566, "temp": 28}, "Puerto Vallarta": {"alt": 10, "temp": 32}}
db_geo["Nuevo Leon"] = {"Monterrey": {"alt": 540, "temp": 35}, "Apodaca": {"alt": 400, "temp": 36}}
db_geo["Puebla"] = {"Puebla": {"alt": 2135, "temp": 25}}
db_geo["Queretaro"] = {"Queretaro": {"alt": 1820, "temp": 28}}
db_geo["Sinaloa"] = {"Culiacan": {"alt": 54, "temp": 36}, "Mazatlan": {"alt": 10, "temp": 32}, "Los Mochis": {"alt": 10, "temp": 35}}
db_geo["Sonora"] = {"Hermosillo": {"alt": 210, "temp": 40}, "Nogales": {"alt": 1200, "temp": 30}}
db_geo["Veracruz"] = {"Veracruz": {"alt": 10, "temp": 30}, "Coatzacoalcos": {"alt": 10, "temp": 32}}
db_geo["Yucatan"] = {"Merida": {"alt": 10, "temp": 36}}

# --- 4. INICIALIZACIÓN ---
if 'naves_data' not in st.session_state: st.session_state['naves_data'] = {}
if 'calc_nav' not in st.session_state: st.session_state['calc_nav'] = {}
if 'louvers_nav' not in st.session_state: st.session_state['louvers_nav'] = {}

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
            
        st.session_state['naves_data'] = {
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
        altura = st.number_input("Altura Promedio (m)", 3.0, 25.0, 8.0, 0.5)
        
    volumen = area * altura
    
    st.markdown(f"""
    <div class="highlight" style="text-align:center; padding: 10px;">
        Volumen Total del Recinto: <strong>{volumen:,.0f} m³</strong>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### Determinación de Cambios por Hora")
    
    app_selec = st.selectbox("Aplicación / Actividad", list(db_ach.keys()))
    
    # Lógica de Sugerencia Térmica
    rangos = db_ach[app_selec] # [Min, Med, Max]
    t_ref = st.session_state['naves_data']['temp']
    
    sug_val = rangos[1] # Default medio
    msg = ""
    
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
    
    # Resultados Caudal
    q_m3hr = volumen * ach_input
    q_cfm = q_m3hr / 1.699
    
    st.markdown("---")
    st.markdown("#### Configuración de Equipos")
    
    cc1, cc2 = st.columns(2)
    with cc1:
        st.metric("Caudal Total Requerido", f"{int(q_cfm):,} CFM")
        
    with cc2:
        qty_eq = st.number_input("Cantidad de Extractores", 1, 100, 4)
        cfm_unit = q_cfm / qty_eq
        st.metric("Caudal por Equipo", f"{int(cfm_unit):,} CFM")
        
    if st.button("✅ Confirmar Caudal"):
        st.session_state['calc_nav'] = {
            "volumen": volumen,
            "ach": ach_input,
            "q_total": int(q_cfm),
            "qty": qty_eq,
            "q_unit": int(cfm_unit),
            "app": app_selec
        }
        st.success("Caudal Calculado Correctamente.")

# --- TAB 2: LOUVERS (Lógica de tus PDFs) ---
with tab2:
    if st.session_state['calc_nav']:
        q_total = st.session_state['calc_nav']['q_total']
        st.info(f"Caudal Total a Reponer: **{q_total:,} CFM**")
        
        tipo_ent = st.radio("Entrada de Aire", ["Louvers de Admisión", "Entrada Natural (Portones/Huecos)"])
        
        vel_louver = 0
        sp_louver = 0.0
        area_libre_total = 0
        
        if "Louvers" in tipo_ent:
            mat_louver = st.radio("Material", ["Lámina Galvanizada", "Aluminio Extruido"], horizontal=True)
            
            cl1, cl2 = st.columns(2)
            with cl1: width_l = st.number_input("Ancho Louver (m)", 0.5, 5.0, 1.0, 0.05)
            with cl2: height_l = st.number_input("Alto Louver (m)", 0.5, 5.0, 1.0, 0.05)
            
            qty_l = st.number_input("Cantidad de Louvers", 1, 200, 1)
            
            # --- CÁLCULO ÁREA LIBRE (Basado en tus PDFs) ---
            # Galvanizado: Aprox 40-45% eficiencia. Aluminio: Aprox 50-55%
            area_bruta_ft2 = (width_l * height_l) * 10.764
            
            factor_area = 0.45 # Default Galv
            if mat_louver == "Aluminio Extruido": factor_area = 0.52
            
            area_libre_unit = area_bruta_ft2 * factor_area
            area_libre_total = area_libre_unit * qty_l
            
            st.caption(f"Área Libre Estimada por pza: {area_libre_unit:.2f} ft² (Factor {int(factor_area*100)}%)")
            
            if area_libre_total > 0:
                vel_louver = q_total / area_libre_total
            
            # Semáforo Velocidad (900 FPM Default)
            st.metric("Velocidad de Paso (Free Area)", f"{int(vel_louver)} FPM")
            
            if vel_louver <= 900:
                st.markdown('<div class="success-box">✅ <strong>VELOCIDAD CORRECTA</strong><br>Sin arrastre de agua.</div>', unsafe_allow_html=True)
            elif 900 < vel_louver <= 1050:
                st.markdown('<div class="warning-box">⚠️ <strong>VELOCIDAD ALTA</strong><br>Riesgo leve de arrastre de agua.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="danger-box">⛔ <strong>VELOCIDAD EXCESIVA (>1050)</strong><br>Entrará agua de lluvia. Aumenta tamaño o cantidad.</div>', unsafe_allow_html=True)
            
            # Cálculo Presión (Curvas PDFs)
            # Galvanizado es más restrictivo. Pe = K * (V/4005)^2
            # Galv: K aprox 2.8 | Alum: K aprox 2.3
            k_factor = 2.8 if mat_louver == "Lámina Galvanizada" else 2.3
            sp_louver = k_factor * ((vel_louver / 4005)**2)
            
            st.write(f"Caída de Presión Louver: **{sp_louver:.3f} in wg**")
            
        else:
            st.info("Se asume entrada libre (presión despreciable).")
            sp_louver = 0.05 # Mínimo seguridad
            
        if st.button("✅ Guardar Entrada"):
            st.session_state['louvers_nav'] = {
                "tipo": tipo_ent,
                "material": mat_louver if "Louvers" in tipo_ent else "N/A",
                "dims": f"{qty_l} pzas de {width_l}x{height_l}m" if "Louvers" in tipo_ent else "Natural",
                "vel": int(vel_louver),
                "sp": sp_louver
            }
            st.success("Configuración guardada.")
            
    else:
        st.info("Calcula el caudal primero.")

# --- TAB 3: SELECCIÓN Y CORREO ---
with tab3:
    if st.session_state['louvers_nav']:
        res_q = st.session_state['calc_nav']
        res_l = st.session_state['louvers_nav']
        
        st.markdown("#### 1. Cálculo de Presión Estática Total")
        sp_base = res_l['sp']
        st.write(f"Presión Louvers/Entrada: **{sp_base:.3f} in wg**")
        
        st.markdown("**Accesorios del Extractor:**")
        c1, c2 = st.columns(2)
        with c1:
            malla = st.checkbox("Malla de Protección", value=True) # 0.05
            persiana = st.checkbox("Persiana de Gravedad", value=True) # 0.10
        with c2:
            copete = st.checkbox("Cubierta Intemperie (Tejado)", value=False) # 0.12
            ducto = st.checkbox("Tramo corto de ducto", value=False) # 0.05
            
        sp_acc = 0.0
        if malla: sp_acc += 0.05
        if persiana: sp_acc += 0.10
        if copete: sp_acc += 0.12
        if ducto: sp_acc += 0.05
        
        sp_total = sp_base + sp_acc
        
        st.markdown(f"""
        <div class="highlight">
            <h3 style="margin:0; color:#333;">Presión Estática Total (SP): {sp_total:.3f} in wg</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 2. Especificación del Equipo")
        
        cs1, cs2 = st.columns(2)
        with cs1:
            montaje = st.radio("Montaje", ["Muro (Axial)", "Tejado (Hongo/Axial)", "Ducto"])
            voltaje = st.radio("Voltaje", ["Trifásico 220/440V", "Monofásico 127V"])
        with cs2:
            prioridad = st.radio("Prioridad de Selección", ["Costo Inicial", "Bajo Ruido", "Eficiencia Energética"])
            aire = st.selectbox("Tipo de Aire", ["Limpio (Estándar)", "Corrosivo (Inox/Recubierto)", "Explosivo (Motor XP)"])
            
        st.markdown("---")
        
        # --- CORREO FINAL ---
        st.markdown("### 📤 Enviar Solicitud")
        
        p = st.session_state['naves_data']
        
        subject_raw = f"Cotización Nave: {p['nombre']}"
        
        body_raw = f"""Hola Ing. Sotelo,

Solicito cotización para ventilación de Nave Industrial:

1. DATOS DEL PROYECTO:
- Proyecto: {p['nombre']}
- Ubicación: {p['ubicacion']} (Alt: {p['alt']}m | Temp: {p['temp']}C)

2. CÁLCULO DE INGENIERÍA (ACH):
- Aplicación: {res_q['app']}
- Dimensiones: {area} m2 x {altura} m (Vol: {volumen:,.0f} m3)
- Renovaciones: {res_q['ach']} ACH (Base Temp: {p['temp']}C)
- CAUDAL TOTAL: {res_q['q_total']:,} CFM
- Entrada Aire: {res_l['tipo']} ({res_l['dims']}) | Vel: {res_l['vel']} FPM

3. SELECCIÓN DE EQUIPOS:
- Cantidad: {res_q['qty']} Equipos
- Capacidad c/u: {res_q['q_unit']:,} CFM
- PRESIÓN ESTÁTICA: {sp_total:.3f} in wg
- Montaje: {montaje}
- Voltaje: {voltaje}
- Tipo Aire: {aire}
- Prioridad: {prioridad}

Accesorios: Malla={malla}, Persiana={persiana}, Copete={copete}.

Quedo atento a su propuesta."""

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
