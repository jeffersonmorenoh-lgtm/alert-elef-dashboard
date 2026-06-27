import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz

# --- 1. CONFIGURACIÓN DE LA PÁGINA (PWA Ready) ---
st.set_page_config(
    page_title="ALERT ELEF", 
    page_icon="📡", 
    layout="wide"
)

# --- 2. BBDD MAESTRA CON TICKETS REALES ---
BBDD_TICKETS = {
    "USO": {"threshold_m": 3.5, "name": "Petróleo ($USO)"},
    "GLD": {"threshold_m": 5.0, "name": "Oro ($GLD)"},
    "AMD": {"threshold_m": 45.0, "name": "AMD ($AMD)"},
    "IWM": {"threshold_m": 25.0, "name": "Russell 2000 ($IWM)"},
    "QQQ": {"threshold_m": 40.0, "name": "Nasdaq 100 ($QQQ)"},
    "TSLA": {"threshold_m": 70.0, "name": "Tesla ($TSLA)"},
    "AMZN": {"threshold_m": 30.0, "name": "Amazon ($AMZN)"},
    "NVDA": {"threshold_m": 150.0, "name": "Nvidia ($NVDA)"}
}

# --- 3. BARRA LATERAL: CONTROL DE MANDO ---
st.sidebar.header("🎛️ Configuración del Radar")

tickets_seleccionados = st.sidebar.multiselect(
    "Tickets en pantalla:",
    options=list(BBDD_TICKETS.keys()),
    default=["USO", "AMD", "IWM", "QQQ", "TSLA", "AMZN"]
)

segundos_refresco = st.sidebar.slider("Auto-refrescar cada (seg):", min_value=10, max_value=300, value=30)

st.title("📡 ALERT ELEF - G-STATION VIVO")

# --- 4. MOTOR DE CÁLCULO DE MÉTRICAS CON FÓRMULA TC2000 ---
@st.cache_data(ttl=10)
def descargar_y_analizar(lista_tickers):
    datos_analizados = {}
    
    tz_ny = pytz.timezone('America/New_York')
    ahora_ny = datetime.now(tz_ny)
    en_apertura = (ahora_ny.hour == 9 and 30 <= ahora_ny.minute <= 45)

    for ticker in lista_tickers:
        try:
            t_obj = yf.Ticker(ticker)
            
            # Necesitamos descargar al menos 5 o 6 días de datos para tener 100 barras de 15m (cada día tiene 26 barras)
            hist_15m = t_obj.history(period="7d", interval="15m")
            if len(hist_15m) < 100:
                # Si es un ticket con pocos datos o fin de semana, usamos lo que haya disponible
                hist_15m = t_obj.history(period="max", interval="15m")
                
            if hist_15m.empty:
                continue
                
            # --- CÓMPUTO DE BOLLINGER (15m) ---
            ultimas_velas = hist_15m.tail(20)
            ma20 = ultimas_velas['Close'].rolling(window=20).mean().iloc[-1]
            std20 = ultimas_velas['Close'].rolling(window=20).std().iloc[-1]
            banda_sup = ma20 + (2 * std20)
            banda_inf = ma20 - (2 * std20)
            rango_bandas = ((banda_sup - banda_inf) / ma20) * 100 if ma20 > 0 else 5.0
            bollinger = "Comprimiendo 🛑" if rango_bandas < 2.0 else "Expandiendo ↕️"
            
            # --- REPLICACIÓN EXACTA FÓRMULA TC2000: 100 * V / AVGV100 ---
            v_actual = hist_15m['Volume'].iloc[-1] # Volumen de la barra de 15m en curso
            avgv100 = hist_15m['Volume'].tail(100).mean() # Promedio de las últimas 100 barras de 15m
            
            if avgv100 > 0:
                fuerza_elefante = int(100 * v_actual / avgv100)
            else:
                fuerza_elefante = 0
                
            # --- DATOS GENERALES DIARIOS ---
            info = t_obj.info
            precio = info.get("currentPrice") or info.get("regularMarketPrice") or hist_15m['Close'].iloc[-1]
            volumen_diario_m = (info.get("regularMarketVolume") or hist_15m['Volume'].sum()) / 1_000_000
            
            datos_analizados[ticker] = {
                "precio": precio,
                "volumen_m": volumen_diario_m,
                "bollinger": bollinger,
                "fuerza_elefante": fuerza_elefante,
                "en_apertura": en_apertura
            }
        except Exception as e:
            datos_analizados[ticker] = {"precio": 0.0, "volumen_m": 0.0, "bollinger": "Error 🛑", "fuerza_elefante": 0, "en_apertura": False}
            
    return datos_analizados

# --- 5. EJECUCIÓN DEL RADAR TÁCTICO ---
if tickets_seleccionados:
    with st.spinner("Sincronizando con algoritmos institucionales..."):
        datos_actuales = descargar_y_analizar(tickets_seleccionados)
    
    if "USO" in datos_actuales and datos_actuales["USO"]["precio"] >= 123.00:
        st.error(f"🚨 **ALERTA YUNQUE TRIGERED:** $USO está en ${datos_actuales['USO']['precio']:.2f}. ¡Tecnológicas bajo presión extrema!")

    tabla_radar = []
    for ticker in tickets_seleccionados:
        if ticker not in datos_actuales: continue
        
        vol_m = datos_actuales[ticker]["volumen_m"]
        precio = datos_actuales[ticker]["precio"]
        bandas = datos_actuales[ticker]["bollinger"]
        fuerza = datos_actuales[ticker]["fuerza_elefante"]
        umbral_m = BBDD_TICKETS[ticker]["threshold_m"]
        
        umbral_ajustado = umbral_m * 0.15 if datos_actuales[ticker]["en_apertura"] else umbral_m

        # Sistema de alertas acoplado a tu indicador TC2000
        if bandas == "Comprimiendo 🛑" and (vol_m >= umbral_ajustado or fuerza >= 140):
            estado = "⚠️ EXHAUSTION (No Entry)"
        elif fuerza >= 300 or vol_m >= umbral_ajustado:
            estado = "🚨 FUCSIA (Elefante)"
        elif fuerza >= 140:
            estado = "⚡ Institucional Entrando"
        else:
            estado = "🔵 Azul (Retail)"
            
        # Formato visual adaptado
        if fuerza >= 300:
            fuerza_str = f"🔥 {fuerza}"
        elif fuerza >= 200:
            fuerza_str = f"⏳ {fuerza}"
        elif fuerza >= 140:
            fuerza_str = f"🐘 {fuerza}"
        else:
            fuerza_str = f"🔹 {fuerza}"
            
        tabla_radar.append({
            "Ticket": ticker,
            "Fuerza (15m)": fuerza_str,
            "Precio": f"${precio:.2f}",
            "Vol. Hoy (M)": f"{vol_m:.2f}M",
            "Umbral Act.": f"{umbral_ajustado:.1f}M",
            "Bandas (15m)": bandas,
            "Estado": estado
        })

    df = pd.DataFrame(tabla_radar)

    def colorear_estado(val):
        if "FUCSIA" in val:
            return 'background-color: #ff007f; color: white; font-weight: bold;'
        elif "EXHAUSTION" in val:
            return 'background-color: #b22222; color: white; font-weight: bold;'
        elif "Institucional" in val:
            return 'background-color: #4b5563; color: #f3f4f6; font-weight: bold;'
        return 'background-color: #1e293b; color: #94a3b8;'

    df_styled = df.style.map(colorear_estado, subset=["Estado"])
    
    st.subheader("📊 Radar de Elefantes")
    st.dataframe(df_styled, use_container_width=True, hide_index=True)
    st.caption(f"Fórmula TC2000 en uso: 100 * V / AVGV100 (15m). Sincronización completa.")

# --- 6. AUTO-REFRESCO OPTIMIZADO PARA MÓVIL ---
st.fragment(run_every=segundos_refresco)(lambda: st.rerun())()
