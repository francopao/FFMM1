"""
================================================================================
GLOBAL MARKETS & MACRO INTELLIGENCE TERMINAL
Python + Streamlit | Institutional Investment Research Tool
================================================================================

QUE CONTIENE ESTE ARCHIVO
--------------------------------------------------------------------------------
Una aplicacion Streamlit de un solo archivo con cinco pestanas (COMMODITIES,
PERU, USA, WORLD, FFMM) que combina monitoreo de mercados, investigacion
macro, analisis cross-asset y "data storytelling" (interpretacion automatica
tipo Portfolio Manager / CIO, inspirada en el formato de weekly reports
institucionales como el "CIO Market Pulse" de DBS, y en general el formato de
HSBC/BlackRock/Goldman Sachs: bloques cortos de texto en negrita + 2-3
oraciones con el mecanismo, tablas de performance por periodo con codigo de
color, y graficos de atribucion) sobre datos descargados en tiempo real de
fuentes gratuitas y publicas (FRED -via fredapi con fallback a su CSV
publico-, Yahoo Finance via yfinance, Stooq como respaldo).

La pestana FFMM cubre el portafolio de fondos mutuos/ETFs tematicos de
"Portafolio_FFMM.xlsx": performance WTD/MTD/YTD/1Y/3Y y ultimo precio/retorno
de cada fondo via Yahoo Finance, y un performance attribution estilo CFA por
Top Holdings (p.ej. explicar el retorno WTD de SOXX a partir de cuanto
contribuyo cada uno de sus principales holdings: NVIDIA, Broadcom, AMD,
Texas Instruments, etc.).

COMO EJECUTARLA
--------------------------------------------------------------------------------
1) Instalar dependencias (un solo comando):

   pip install streamlit pandas numpy plotly yfinance requests scipy openpyxl fredapi

2) Ejecutar:

   streamlit run global_macro_terminal.py

No se requiere ninguna API key para que la app funcione: FRED se consulta
primero via la libreria oficial `fredapi` (mas robusta) y, si la API key no
es valida o fredapi no esta instalado, cae automaticamente al endpoint
publico de CSV de FRED (fredgraph.csv), que no requiere autenticacion. Para
usar fredapi con tu propia cuenta, reemplaza la constante FRED_API_KEY (mas
abajo, seccion 1 CONFIG) por tu API key real y gratuita, obtenida en
https://fred.stlouisfed.org/docs/api/api_key.html — la que trae el archivo
por defecto es un placeholder de ejemplo y no funcionara hasta que la
reemplaces.

LIMITACIONES CONOCIDAS (documentadas segun lo solicitado, no se fabrican datos)
--------------------------------------------------------------------------------
- Varios instrumentos peruanos listados UNICAMENTE en la Bolsa de Valores de
  Lima (BVL) -no como ADR en NYSE- (ej. UNACEM, Pacasmayo, Ferreycorp,
  Alicorp, Volcan, Minsur, Backus, InRetail, etc.) no tienen cobertura
  confiable y gratuita fuera de Bloomberg/Bloomberg-like terminals. La app
  intenta Yahoo Finance con el sufijo ".LM" (Lima) y, si falla, lo declara
  explicitamente como "no disponible" en vez de inventar un valor. Los
  nombres que SI cotizan como ADR/listing internacional (BAP, IFS, BVN,
  NEXA, AUNA, SCCO, HBM, HOC) si tienen datos confiables via Yahoo Finance.
- El indice general de la BVL (S&P/BVL Peru General, "SPBLPGPT Index" en
  Bloomberg) no tiene una fuente gratuita y confiable en tiempo real. Como
  alternativa funcional se usa el ETF iShares MSCI Peru (EPU), que es el
  proxy liquido mas usado por la industria para exposicion a renta variable
  peruana. Se documenta esto en la UI.
- COLCAP (Colombia) y, en general, la profundidad de datos de mercado de
  Colombia en fuentes gratuitas es limitada; se usa un ETF proxy (GXG) y se
  declara la limitacion. Los datos macro de China via fuentes OECD/FRED son
  mas escasos que los de economias OECD por la naturaleza de sus
  publicaciones oficiales; se documenta en la pestana WORLD.
- Taiwan no es miembro del Banco Mundial, por lo que la serie de
  crecimiento del PBI (World Bank, via FRED) no existe para Taiwan; se
  omite con una nota en vez de mostrar un dato falso.
- Todas las descargas usan cache con TTL y manejo de errores: si una fuente
  falla, el componente correspondiente se marca como "dato no disponible"
  en lugar de interrumpir la aplicacion o mostrar un valor inventado.
- El storytelling es generado por un motor de reglas (patrones
  cuantitativos: direccion, magnitud, percentil historico, aceleracion de
  tendencia, divergencias entre indicadores) a partir de los datos
  observados en tiempo de ejecucion. No es un modelo de lenguaje ni usa
  IA generativa: es determinista y reproducible, y evita afirmar
  causalidad a partir de correlacion.
- Universo FFMM: "Portafolio_FFMM.xlsx" trae NOMBRES de fondos, no tickers.
  Muchos son fondos mutuos offshore (SICAVs de Luxemburgo, OEICs del Reino
  Unido, fondos de gestoras indias) que NO tienen ticker gratuito en Yahoo
  Finance; para esos casos la app muestra "N/D" en vez de adivinar un
  ticker que podria traer datos de OTRO instrumento por error. Los ETFs
  liquidos (ej. SOXX, SMH, GDX, VGT, XLK, EWY, EWT) si tienen cobertura
  confiable. Algunos tickers (marcados "estimado" en el mapeo) se infirieron
  del nombre del fondo con confianza media y deben verificarse antes de
  usarse en una decision de inversion; la app permite subir un mapeo propio
  de Nombre->Ticker (dos columnas) para corregir o completar el catalogo sin
  tocar el codigo.
- El performance attribution por Top Holdings usa los PESOS VIGENTES mas
  recientes de cada holding (los unicos que expone Yahoo Finance de forma
  gratuita), no los pesos vigentes al INICIO del periodo analizado. Es una
  aproximacion razonable para explicar la direccion y los principales
  drivers del movimiento, pero no es una atribucion exacta tipo Brinson con
  pesos diarios; la app lo declara explicitamente en cada lectura.

ARQUITECTURA (resumen)
--------------------------------------------------------------------------------
1. CONFIG            -> catalogos de series FRED / tickers yfinance por pestana,
                         incluyendo el mapeo Fondo FFMM -> ticker Yahoo
2. DATA FETCH LAYER   -> fetch_fred() (fredapi + fallback CSV), fetch_yf(),
                         fetch_stooq(), fetch_top_holdings() con cache y
                         manejo de errores, devuelven un FetchResult uniforme
3. ANALYTICS LAYER    -> retornos, volatilidad, drawdown, z-score, percentil,
                         correlaciones, pendiente de curva de rendimientos,
                         retornos WTD/MTD/YTD/1Y/3Y y CAGR
4. STORYTELLING ENGINE-> biblioteca de patrones interpretativos reutilizables
                         + interpretes compuestos (labor, inflacion, etc.) +
                         performance attribution estilo CFA por holdings
5. UI HELPERS         -> tarjetas de metricas, badges de frescura, graficos
                         Plotly estandarizados, tablas con codigo de color,
                         heatmap de correlaciones, scatter riesgo/retorno
6. LOADERS DINAMICOS  -> lee dinamicamente la hoja "Parametria" de un
                         ZODA.xlsx y las hojas de Portafolio_FFMM.xlsx
                         (subidos por el usuario) para refrescar los
                         universos de instrumentos; si no se sube nada, usa
                         los universos ya identificados por defecto
7. TABS               -> render_commodities_tab / render_peru_tab /
                         render_usa_tab / render_world_tab / render_ffmm_tab
8. MAIN               -> page config, sidebar, orquestacion de pestanas
================================================================================
"""

from __future__ import annotations

import io
import logging
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

warnings.filterwarnings("ignore")

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None

try:
    from fredapi import Fred
except ImportError:  # pragma: no cover
    Fred = None

# ==============================================================================
# 1. CONFIG / CONSTANTS
# ==============================================================================

APP_TITLE = "Global Markets & Macro Intelligence Terminal"
CACHE_TTL_INTRADAY = 60 * 30        # 30 min para precios de mercado
CACHE_TTL_MACRO = 60 * 60 * 6       # 6 horas para series macro (mensuales/trimestrales)
REQUEST_TIMEOUT = 15
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (MacroTerminal/1.0; research use)"}

DEFAULT_LOOKBACK_YEARS = 5

# <<< REEMPLAZA ESTO POR TU API KEY REAL Y GRATUITA DE FRED >>>
# Se obtiene en https://fred.stlouisfed.org/docs/api/api_key.html
# El valor de abajo es un PLACEHOLDER de ejemplo: con el no funcionara
# fredapi, pero la app sigue operando igual gracias al fallback automatico
# al endpoint publico de CSV de FRED (ver fetch_fred() mas abajo).
FRED_API_KEY = "762e2ee1c8fab5d038ce317929d47226"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("macro_terminal")


# ------------------------------------------------------------------------------
# 1.1 COMMODITIES catalog (Yahoo Finance front-month continuous futures)
# ------------------------------------------------------------------------------
COMMODITIES = {
    "WTI Crude Oil":   {"ticker": "CL=F", "unit": "USD/bbl", "asset_class": "energy",
                          "peru_relevance": "baja"},
    "Brent Crude Oil": {"ticker": "BZ=F", "unit": "USD/bbl", "asset_class": "energy",
                          "peru_relevance": "baja"},
    "Natural Gas":     {"ticker": "NG=F", "unit": "USD/MMBtu", "asset_class": "energy",
                          "peru_relevance": "baja"},
    "Gold":            {"ticker": "GC=F", "unit": "USD/oz", "asset_class": "precious_metal",
                          "peru_relevance": "alta"},
    "Silver":          {"ticker": "SI=F", "unit": "USD/oz", "asset_class": "precious_metal",
                          "peru_relevance": "alta"},
    "Copper":          {"ticker": "HG=F", "unit": "USD/lb", "asset_class": "industrial_metal",
                          "peru_relevance": "muy alta"},
}

# ------------------------------------------------------------------------------
# 1.2 PERU instrument universe, derivado de ZODA.xlsx -> hoja "Parametria"
#     (BBG = ticker Bloomberg original; yahoo_candidates = intentos en orden)
# ------------------------------------------------------------------------------
PERU_INSTRUMENTS_DEFAULT = [
    {"empresa": "BAP",     "bbg": "BAP US Equity",      "yahoo_candidates": ["BAP"],
     "sector": "Financiero (Credicorp)",            "listing": "ADR / NYSE"},
    {"empresa": "IFS",     "bbg": "IFS PE Equity",      "yahoo_candidates": ["IFS"],
     "sector": "Financiero (Intercorp)",             "listing": "NYSE / BVL"},
    {"empresa": "BBVA",    "bbg": "BBVAC1 PE Equity",   "yahoo_candidates": ["BBVAC1.LM"],
     "sector": "Financiero",                          "listing": "BVL (local)"},
    {"empresa": "UNACEM",  "bbg": "UNACEMC1 PE Equity", "yahoo_candidates": ["UNACEMC1.LM"],
     "sector": "Cemento / Construccion",              "listing": "BVL (local)"},
    {"empresa": "PACAS",   "bbg": "CPACASC1 PE Equity", "yahoo_candidates": ["CPACASC1.LM"],
     "sector": "Cemento (Pacasmayo)",                 "listing": "BVL (local)"},
    {"empresa": "AENZA",   "bbg": "AENZAC1 PE Equity",  "yahoo_candidates": ["AENZAC1.LM"],
     "sector": "Construccion / Infraestructura",      "listing": "BVL (local)"},
    {"empresa": "FERREY",  "bbg": "FERREYC1 PE Equity", "yahoo_candidates": ["FERREYC1.LM"],
     "sector": "Industrial / Distribucion (Ferreycorp)", "listing": "BVL (local)"},
    {"empresa": "CORARE",  "bbg": "CORAREC1 PE Equity", "yahoo_candidates": ["CORAREI1.LM", "CORAREC1.LM"],
     "sector": "Siderurgia (Aceros Arequipa)",        "listing": "BVL (local)"},
    {"empresa": "BVN",     "bbg": "BVN US Equity",      "yahoo_candidates": ["BVN"],
     "sector": "Mineria - Oro/Plata (Buenaventura)",  "listing": "ADR / NYSE"},
    {"empresa": "CVERDE",  "bbg": "CVERDEC1 PE Equity", "yahoo_candidates": ["CVERDEC1.LM"],
     "sector": "Mineria - Cobre (Cerro Verde)",        "listing": "BVL (local)"},
    {"empresa": "NEXAPE",  "bbg": "NEXAPEC1 PE Equity", "yahoo_candidates": ["NEXAPEC1.LM"],
     "sector": "Mineria - Zinc/Cobre (Nexa Peru)",     "listing": "BVL (local)"},
    {"empresa": "NEXAUS",  "bbg": "NEXA US Equity",     "yahoo_candidates": ["NEXA"],
     "sector": "Mineria - Zinc/Cobre (Nexa Resources)", "listing": "NYSE"},
    {"empresa": "MINSUR",  "bbg": "MINSURI1 PE Equity", "yahoo_candidates": ["MINSURI1.LM"],
     "sector": "Mineria - Estano/Oro (Minsur)",        "listing": "BVL (local)"},
    {"empresa": "VOLCAN",  "bbg": "VOLCABC1 PE Equity", "yahoo_candidates": ["VOLCABC1.LM"],
     "sector": "Mineria - Zinc/Plomo/Plata (Volcan)",  "listing": "BVL (local)"},
    {"empresa": "ORYGEN",  "bbg": "ORYGENC1 PE Equity", "yahoo_candidates": ["ORYGENC1.LM"],
     "sector": "Energia",                              "listing": "BVL (local)"},
    {"empresa": "PLUZEN",  "bbg": "PLUZENC1 PE Equity", "yahoo_candidates": ["PLUZENC1.LM"],
     "sector": "Energia (generacion)",                 "listing": "BVL (local)"},
    {"empresa": "ENGIE",   "bbg": "ENGIEC1 PE Equity",  "yahoo_candidates": ["ENGIEC1.LM"],
     "sector": "Energia (Engie Peru)",                  "listing": "BVL (local)"},
    {"empresa": "ALICORP", "bbg": "ALICORC1 PE Equity", "yahoo_candidates": ["ALICORC1.LM"],
     "sector": "Consumo masivo",                        "listing": "BVL (local)"},
    {"empresa": "INRETAIL","bbg": "INRETC1 PE Equity",  "yahoo_candidates": ["INRETC1.LM"],
     "sector": "Retail",                                "listing": "BVL (local)"},
    {"empresa": "BACKUS",  "bbg": "BACKUSI1 PE Equity", "yahoo_candidates": ["BACKUSI1.LM"],
     "sector": "Bebidas (AB InBev Peru)",                "listing": "BVL (local)"},
    {"empresa": "AUNA",    "bbg": "AUNA US Equity",     "yahoo_candidates": ["AUNA"],
     "sector": "Salud",                                  "listing": "NYSE"},
    {"empresa": "ELCOMEI", "bbg": "ELCOMEI1 PE Equity", "yahoo_candidates": ["ELCOMEI1.LM"],
     "sector": "Medios (El Comercio)",                   "listing": "BVL (local)"},
]

# Indices / benchmarks regionales que acompanan al universo peruano (de la
# hoja Parametria): se usan proxies liquidos donde no hay fuente gratuita
# directa para el indice "puro".
PERU_REGIONAL_BENCHMARKS = [
    {"nombre": "BVL (proxy: iShares MSCI Peru ETF)", "bbg": "SPBLPGPT Index",
     "yahoo_candidates": ["EPU"], "nota": "Proxy por falta de fuente gratuita del indice BVL puro."},
    {"nombre": "IPSA (Chile)",   "bbg": "IPSA Index",   "yahoo_candidates": ["^IPSA"], "nota": ""},
    {"nombre": "IBOV (Brasil)",  "bbg": "IBOV Index",   "yahoo_candidates": ["^BVSP"], "nota": ""},
    {"nombre": "MEXBOL (Mexico)","bbg": "MEXBOL Index", "yahoo_candidates": ["^MXX"], "nota": ""},
    {"nombre": "COLCAP (Colombia, proxy ETF)", "bbg": "COLCAP Index",
     "yahoo_candidates": ["GXG", "ICOL"], "nota": "Proxy ETF por baja cobertura gratuita de COLCAP."},
    {"nombre": "MSCI Latam (proxy ETF)", "bbg": "MXLA Index",
     "yahoo_candidates": ["ILF"], "nota": "Proxy ETF (iShares Latin America 40)."},
]

PERU_MINING_PEERS = [
    {"nombre": "Hochschild Mining", "bbg": "HOC LN Equity", "yahoo_candidates": ["HOC.L"]},
    {"nombre": "Southern Copper",   "bbg": "SCCO US Equity", "yahoo_candidates": ["SCCO"]},
    {"nombre": "Hudbay Minerals",   "bbg": "HBM CN Equity",  "yahoo_candidates": ["HBM"]},
]

PERU_FX = {"ticker": "PEN=X", "nombre": "USD/PEN"}

# Series macro de Peru disponibles gratuitamente via FRED (World Bank mirror /
# OECD). Son de baja frecuencia (anual); se documentan como tales.
PERU_MACRO_FRED = {
    "Inflacion (CPI, var. % anual)": "FPCPITOTLZGPER",
    "Crecimiento del PBI real (var. % anual)": "NYGDPMKTPKDZGPER",
}

# ------------------------------------------------------------------------------
# 1.3 USA macro catalog (FRED series IDs, todas de acceso publico sin API key)
# ------------------------------------------------------------------------------
USA_LABOR = {
    "Nonfarm Payrolls (miles, nivel)":   "PAYEMS",
    "Tasa de desempleo (%)":             "UNRATE",
    "Solicitudes iniciales de desempleo":"ICSA",
    "Tasa de participacion laboral (%)": "CIVPART",
    "Salario promedio por hora (USD)":   "CES0500000003",
}

USA_INFLATION = {
    "CPI headline (indice)":      "CPIAUCSL",
    "CPI core (indice)":          "CPILFESL",
    "PCE headline (indice)":      "PCEPI",
    "PCE core (indice)":          "PCEPILFE",
    "Breakeven inflacionario 5Y (%)": "T5YIE",
}

USA_FED_POLICY = {
    "Fed Funds Rate (%)":          "FEDFUNDS",
    "Balance de la Fed (USD mill)":"WALCL",
    "Reverse Repo overnight (USD mill)": "RRPONTSYD",
}

USA_RATES = {
    "UST 2 anos (%)":  "DGS2",
    "UST 10 anos (%)": "DGS10",
    "UST 30 anos (%)": "DGS30",
    "Spread 10Y-2Y (pp)": "T10Y2Y",
}

USA_FISCAL = {
    "Deuda publica federal (USD mill)":        "GFDEBTN",
    "Deuda publica / PBI (%)":                 "GFDEGDQ188S",
    "Resultado fiscal mensual (USD mill)":      "MTSDS133FMS",
}

USA_STRESS = {
    "Chicago Fed Financial Conditions (NFCI)": "NFCI",
    "St. Louis Fed Financial Stress Index":    "STLFSI4",
}
USA_VIX_TICKER = "^VIX"

# ------------------------------------------------------------------------------
# 1.4 WORLD country scorecards
#     cpi: OECD MEI "CPI, all items, YoY %"; rate: central bank policy proxy
#     y10: long-term govt bond yield (OECD MEI); gdp: World Bank GDP growth
#     fx: par Yahoo vs USD; equity: indice bursatil Yahoo
# ------------------------------------------------------------------------------
WORLD_COUNTRIES = {
    "Japon": {
        "cpi": "CPALTT01JPM657N", "rate": "IRSTCB01JPM156N", "y10": "IRLTLT01JPM156N",
        "gdp": "NYGDPMKTPKDZGJPN", "fx": "JPY=X", "equity": "^N225",
    },
    "China": {
        "cpi": "CHNCPIALLMINMEI", "rate": None, "y10": None,
        "gdp": "NYGDPMKTPKDZGCHN", "fx": "CNY=X", "equity": "^HSI",
        "nota": "Profundidad limitada: China publica con menor frecuencia/transparencia que economias OECD; se usa Hang Seng (^HSI) como proxy bursatil de referencia regional y CPI via fuente alterna.",
    },
    "Zona Euro": {
        "cpi": "CP0000EZ19M086NEST", "rate": "IRSTCB01EZM156N", "y10": "IRLTLT01EZM156N",
        "gdp": "NYGDPMKTPKDZGEMU", "fx": "EURUSD=X", "equity": "^STOXX50E",
    },
    "Reino Unido": {
        "cpi": "CPALTT01GBM657N", "rate": "IRSTCB01GBM156N", "y10": "IRLTLT01GBM156N",
        "gdp": "NYGDPMKTPKDZGGBR", "fx": "GBPUSD=X", "equity": "^FTSE",
    },
    "Brasil": {
        "cpi": "CPALTT01BRM657N", "rate": "IRSTCB01BRM156N", "y10": None,
        "gdp": "NYGDPMKTPKDZGBRA", "fx": "BRL=X", "equity": "^BVSP",
    },
    "Mexico": {
        "cpi": "CPALTT01MXM657N", "rate": "IRSTCB01MXM156N", "y10": "IRLTLT01MXM156N",
        "gdp": "NYGDPMKTPKDZGMEX", "fx": "MXN=X", "equity": "^MXX",
    },
    "Chile": {
        "cpi": "CPALTT01CLM657N", "rate": "IRSTCB01CLM156N", "y10": "IRLTLT01CLM156N",
        "gdp": "NYGDPMKTPKDZGCHL", "fx": "CLP=X", "equity": "^IPSA",
    },
    "Taiwan": {
        "cpi": "CPALTT01TWM657N", "rate": None, "y10": None,
        "gdp": None, "fx": "TWD=X", "equity": "^TWII",
        "nota": "Taiwan no es miembro del Banco Mundial: no existe serie oficial de crecimiento del PBI en esta fuente.",
    },
    "Colombia": {
        "cpi": "CPALTT01COM657N", "rate": "IRSTCB01COM156N", "y10": None,
        "gdp": "NYGDPMKTPKDZGCOL", "fx": "COP=X", "equity": "GXG",
    },
}

ASSET_CLASS_LABELS = {
    "energy": "energia", "precious_metal": "metal precioso",
    "industrial_metal": "metal industrial", "equity": "renta variable",
    "fx": "tipo de cambio", "rate": "tasa de interes", "macro": "indicador macro",
}

# ------------------------------------------------------------------------------
# 1.5 FFMM: universo de fondos mutuos / ETFs tematicos, derivado de
#     "Portafolio_FFMM.xlsx" (hoja FFMM: columnas Nombre, Asset Class, Mercado,
#     Cat, SubCat, Sub Cat2). El archivo trae NOMBRES, no tickers: el mapeo a
#     Yahoo Finance de abajo es la parte que se construyo manualmente.
#
#     confianza:
#       "alta"      -> ETF liquido, ticker bien conocido, usar con confianza
#       "estimada"  -> ticker inferido del nombre del fondo con buena
#                      probabilidad de acierto, pero sin verificacion en vivo
#                      (sin acceso a internet en el entorno de diseno); se
#                      recomienda confirmarlo una vez antes de decisiones de
#                      inversion
#       "no_disponible" -> fondo mutuo offshore (SICAV de Luxemburgo, OEIC del
#                      Reino Unido, fondo de una gestora india, etc.) sin
#                      ticker gratuito conocido en Yahoo Finance. Se deja
#                      yahoo_candidates vacio a proposito: es preferible
#                      mostrar "N/D" a arriesgarse a traer el precio de OTRO
#                      instrumento por una coincidencia de ticker.
#
#     El usuario puede corregir o completar cualquier fila subiendo, en la
#     barra lateral, un archivo de 2 columnas (Nombre, Ticker).
# ------------------------------------------------------------------------------
FFMM_PORTFOLIO_DEFAULT = [
    # --- Commodities: Metales ---
    {"nombre": "VanEck - Gold Miners ETF", "mercado": "Commodities", "cat": "Metales Preciosos",
     "subcat": "Global", "subcat2": None, "yahoo_candidates": ["GDX"], "confianza": "alta", "nota": ""},
    {"nombre": "Global X - Silvers Miners ETF", "mercado": "Commodities", "cat": "Metales Preciosos",
     "subcat": "Global", "subcat2": None, "yahoo_candidates": ["SIL"], "confianza": "alta", "nota": ""},
    {"nombre": "Jupiter Gold & Silver", "mercado": "Commodities", "cat": "Metales Preciosos",
     "subcat": "Global", "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Fondo OEIC (Reino Unido); sin ticker gratuito confiable en Yahoo Finance."},
    {"nombre": "Global X - Copper Miners ETF", "mercado": "Commodities", "cat": "Metales Base",
     "subcat": "Global", "subcat2": None, "yahoo_candidates": ["COPX"], "confianza": "alta", "nota": ""},
    # --- EM Asia: China ---
    {"nombre": "Jupiter Unit Trust - Asian Income Fund I GBP", "mercado": "EM", "cat": "Asia",
     "subcat": "Ex Japan", "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Unit Trust UK; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "UBS - China Opportunity - A3", "mercado": "EM", "cat": "Asia", "subcat": "China",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "Robeco - Chinese A-Share", "mercado": "EM", "cat": "Asia", "subcat": "China",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Fondo offshore Robeco; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "Schroder - International Selection Fund China A", "mercado": "EM", "cat": "Asia",
     "subcat": "China", "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo (Schroder ISF); sin ticker gratuito en Yahoo Finance."},
    {"nombre": "Allianz - China-A", "mercado": "EM", "cat": "Asia", "subcat": "China",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo (AllianzGI); sin ticker gratuito en Yahoo Finance."},
    {"nombre": "Matthews - China Small Caps", "mercado": "EM", "cat": "Asia", "subcat": "China",
     "subcat2": None, "yahoo_candidates": ["MCSMX"], "confianza": "estimada",
     "nota": "Fondo '40 Act de EE.UU. (Matthews Asia). Ticker estimado (clase Investor); verificar clase exacta."},
    {"nombre": "BNP Paribas - China Equity Class", "mercado": "EM", "cat": "Asia", "subcat": "China",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "Robeco - Chinese Equities", "mercado": "EM", "cat": "Asia", "subcat": "China",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Fondo offshore Robeco; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "JP Morgan - Greater China Fund", "mercado": "EM", "cat": "Asia", "subcat": "China",
     "subcat2": None, "yahoo_candidates": ["JFC"], "confianza": "estimada",
     "nota": "Ticker estimado asumiendo que se refiere al closed-end fund JPMorgan China Region Fund "
             "(NYSE: JFC); el nombre no calza exacto ('Greater China' vs 'China Region') -> verificar."},
    # --- EM Asia: Ex Japan (broad / tematico) ---
    {"nombre": "Schroders - Asian Opportunities", "mercado": "EM", "cat": "Asia", "subcat": "Ex Japan",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "Baillie Gifford & Co Ltd - Overseas Growth Funds ICVC - Pacific Fund", "mercado": "EM",
     "cat": "Asia", "subcat": "Ex Japan", "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "ICVC del Reino Unido; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "MSIM - Asia Opportunity", "mercado": "EM", "cat": "Asia", "subcat": "Ex Japan",
     "subcat2": None, "yahoo_candidates": ["MSAQX"], "confianza": "estimada",
     "nota": "Fondo '40 Act de EE.UU. (Morgan Stanley Institutional Fund). Ticker estimado; verificar clase."},
    {"nombre": "Pinebridge - Asia Ex-Japan Small Caps", "mercado": "EM", "cat": "Asia", "subcat": "Ex Japan",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Fondo offshore PineBridge; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "Veritas - Asian Fund", "mercado": "EM", "cat": "Asia", "subcat": "Ex Japan",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "UCITS irlandes (Veritas AM); sin ticker gratuito en Yahoo Finance."},
    {"nombre": "Wellington Luxembourg - Asia Technology Fund", "mercado": "EM", "cat": "Asia",
     "subcat": "Ex Japan", "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo; sin ticker gratuito en Yahoo Finance."},
    # --- EM Asia: India ---
    {"nombre": "Goldman Sachs - India Equity Portfolio", "mercado": "EM", "cat": "Asia", "subcat": "India",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Fondo offshore; sin ticker gratuito confirmado en Yahoo Finance."},
    {"nombre": "Rams UT - India Equities Portfolio Fund II", "mercado": "EM", "cat": "Asia", "subcat": "India",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Fondo local sin cobertura en Yahoo Finance."},
    {"nombre": "Nomura - Indian Equity", "mercado": "EM", "cat": "Asia", "subcat": "India",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Fondo offshore Nomura; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "UTI - Indian Equity", "mercado": "EM", "cat": "Asia", "subcat": "India",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Fondo de gestora india (UTI MF); los fondos mutuos indios no cotizan en Yahoo Finance."},
    # --- EM Asia: Korea / Taiwan ---
    {"nombre": "JP Morgan - Korea Equity Fund", "mercado": "EM", "cat": "Asia", "subcat": "Korea",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo; sin ticker gratuito en Yahoo Finance."},
    {"nombre": "BlackRock - iShares Korea", "mercado": "EM", "cat": "Asia", "subcat": "Korea",
     "subcat2": None, "yahoo_candidates": ["EWY"], "confianza": "alta",
     "nota": "Se asume iShares MSCI South Korea ETF (NYSE Arca), version US del exposure a Korea."},
    {"nombre": "Franklin Templeton - South Korea ETF", "mercado": "EM", "cat": "Asia", "subcat": "Korea",
     "subcat2": None, "yahoo_candidates": ["FLKR"], "confianza": "estimada",
     "nota": "Ticker estimado (Franklin FTSE South Korea ETF); verificar."},
    {"nombre": "Roundhill Memory ETF", "mercado": "EM", "cat": "Asia", "subcat": "Korea",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Ticker no confirmado con suficiente certeza; completar via mapeo manual."},
    {"nombre": "iShares MSCI Korea UCITS ETF", "mercado": "EM", "cat": "Asia", "subcat": "Korea",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Version UCITS (Europa) de iShares Korea; el equivalente US (EWY) si esta cubierto arriba. "
             "Completar ticker europeo via mapeo manual si se requiere."},
    {"nombre": "Amundi Global Memory Chips UCITS ETF", "mercado": "EM", "cat": "Asia", "subcat": "Korea",
     "subcat2": None, "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "ETF listado en Europa (Euronext/Xetra); sin ticker Yahoo confirmado. Completar via mapeo manual."},
    {"nombre": "BlackRock - iShares Taiwan", "mercado": "EM", "cat": "Asia", "subcat": "Taiwan",
     "subcat2": None, "yahoo_candidates": ["EWT"], "confianza": "alta", "nota": ""},
    # --- DM US Tecnologia ---
    {"nombre": "AXA - World Funds Framligton Digital Economy", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Core", "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo (AXA WF); sin ticker gratuito en Yahoo Finance."},
    {"nombre": "State Street - Semiconductors Select Sector", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Semiconductors", "yahoo_candidates": ["XSD"], "confianza": "alta", "nota": ""},
    {"nombre": "State Street - Technology Select Sector", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Core", "yahoo_candidates": ["XLK"], "confianza": "alta", "nota": ""},
    {"nombre": "Vanguard - Information Technology", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Core", "yahoo_candidates": ["VGT"], "confianza": "alta", "nota": ""},
    {"nombre": "Pictet - Digital", "mercado": "DM", "cat": "US", "subcat": "Tecnologia",
     "subcat2": "Software & Internet", "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo (Pictet); sin ticker gratuito en Yahoo Finance."},
    {"nombre": "First Trust - Nasdaq Cybersecurity ETF", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Thematic", "yahoo_candidates": ["CIBR"], "confianza": "alta", "nota": ""},
    {"nombre": "Allianz - Artificial Intelligence", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Thematic", "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "SICAV Luxemburgo (AllianzGI Artificial Intelligence); sin ticker gratuito en Yahoo Finance."},
    {"nombre": "First Trust Cloud Computing ETF", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Software & Internet", "yahoo_candidates": ["SKYY"], "confianza": "alta", "nota": ""},
    {"nombre": "BlackRock - iShares S&P NA Technology-Software Fund", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Software & Internet", "yahoo_candidates": ["IGV"], "confianza": "alta",
     "nota": "iShares Expanded Tech-Software Sector ETF."},
    {"nombre": "VanEck Semiconductor ETF", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Semiconductors", "yahoo_candidates": ["SMH"], "confianza": "alta", "nota": ""},
    {"nombre": "Invesco Semiconductors ETF", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Semiconductors", "yahoo_candidates": ["PSI"], "confianza": "alta",
     "nota": "Invesco Dynamic Semiconductors ETF."},
    {"nombre": "VistaShares Artificial Intelligence Supercycle ETF", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Semiconductors", "yahoo_candidates": ["AIS"], "confianza": "estimada",
     "nota": "ETF de lanzamiento reciente (2024); ticker estimado, verificar."},
    {"nombre": "BlackRock - iShares PHLX Semiconductor ETF", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Semiconductors", "yahoo_candidates": ["SOXX"], "confianza": "alta", "nota": ""},
    {"nombre": "Black Rock - World Technology Fund", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Core", "yahoo_candidates": [], "confianza": "no_disponible",
     "nota": "Probable SICAV Luxemburgo 'BGF World Technology Fund'; sin ticker gratuito en Yahoo Finance. "
             "No confundir con el closed-end fund 'BlackRock Science and Technology Trust' (NYSE: BST), "
             "que es un vehiculo distinto."},
    {"nombre": "WisdomTree - Artificial Intelligence and Innovation ETF", "mercado": "DM", "cat": "US",
     "subcat": "Tecnologia", "subcat2": "Thematic", "yahoo_candidates": ["WTAI"], "confianza": "alta", "nota": ""},
]


# ==============================================================================
# 2. DATA FETCH LAYER
# ==============================================================================

@dataclass
class FetchResult:
    label: str
    series: Optional[pd.Series] = None
    source: str = ""
    status: str = "error"          # ok | stale | error | empty
    asof: Optional[pd.Timestamp] = None
    error: Optional[str] = None
    frequency_days: Optional[int] = None  # cadencia tipica esperada, para flag de "stale"
    resolved_ticker: Optional[str] = None  # cual candidato de la lista funciono (fetch_with_candidates)

    @property
    def ok(self) -> bool:
        return self.status in ("ok", "stale") and self.series is not None and len(self.series) > 0


def _infer_staleness(last_date: pd.Timestamp, expected_gap_days: int) -> str:
    if last_date is None or pd.isna(last_date):
        return "error"
    gap = (pd.Timestamp(datetime.utcnow().date()) - pd.Timestamp(last_date).normalize()).days
    return "stale" if gap > expected_gap_days else "ok"


@st.cache_resource(show_spinner=False)
def _get_fred_client():
    """Crea (una sola vez, cacheado) el cliente fredapi si la libreria esta
    instalada y hay una API key configurada. Si falla, devuelve None y el
    resto de la app sigue funcionando via el fallback de CSV publico."""
    if Fred is None or not FRED_API_KEY or not FRED_API_KEY.strip():
        return None
    try:
        return Fred(api_key=FRED_API_KEY.strip())
    except Exception as exc:  # noqa: BLE001
        logger.info("No se pudo inicializar fredapi: %s", exc)
        return None


def _fetch_fred_via_api(series_id: str, label: str, expected_gap_days: int) -> Optional[FetchResult]:
    """Intenta la descarga via fredapi (requiere API key valida). Devuelve
    None si fredapi no esta disponible o la consulta falla, para que el
    llamador pueda caer al metodo de CSV publico."""
    client = _get_fred_client()
    if client is None:
        return None
    try:
        raw = client.get_series(series_id)
        series = pd.Series(raw).dropna()
        series.index = pd.to_datetime(series.index)
        if series.empty:
            return None
        asof = series.index.max()
        status = _infer_staleness(asof, expected_gap_days)
        return FetchResult(label=label, series=series, source=f"FRED (fredapi):{series_id}",
                            status=status, asof=asof, frequency_days=expected_gap_days)
    except Exception as exc:  # noqa: BLE001
        logger.info("fredapi fallo para %s (se usara el fallback de CSV publico): %s", series_id, exc)
        return None


def _fetch_fred_via_csv(series_id: str, label: str, expected_gap_days: int) -> FetchResult:
    """Descarga una serie de FRED via su endpoint publico de CSV (sin API key).
    Es el metodo original de esta app y sirve de respaldo cuando fredapi no
    esta disponible o la API key no es valida."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        resp = requests.get(url, headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        if df.shape[1] < 2:
            raise ValueError("Respuesta de FRED sin columnas esperadas")
        date_col, val_col = df.columns[0], df.columns[1]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        # FRED usa "." como marcador de dato faltante; errors="coerce" lo convierte en NaN.
        df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
        df = df.dropna(subset=[date_col]).set_index(date_col)[val_col].dropna()
        if df.empty:
            return FetchResult(label=label, status="empty", error="Sin observaciones", source="FRED (CSV)")
        asof = df.index.max()
        status = _infer_staleness(asof, expected_gap_days)
        return FetchResult(label=label, series=df, source=f"FRED (CSV):{series_id}", status=status,
                            asof=asof, frequency_days=expected_gap_days)
    except Exception as exc:  # noqa: BLE001
        logger.warning("FRED (CSV) fetch failed for %s: %s", series_id, exc)
        return FetchResult(label=label, status="error", error=str(exc), source="FRED (CSV)")


@st.cache_data(ttl=CACHE_TTL_MACRO, show_spinner=False)
def fetch_fred(series_id: str, label: str = "", expected_gap_days: int = 60) -> FetchResult:
    """Descarga una serie de FRED. Intenta primero fredapi (requiere
    FRED_API_KEY valida, ver seccion 1 CONFIG); si no esta disponible o
    falla, cae automaticamente al endpoint publico de CSV (sin API key)."""
    label = label or series_id
    if not series_id:
        return FetchResult(label=label, status="error", error="Serie no configurada", source="FRED")
    via_api = _fetch_fred_via_api(series_id, label, expected_gap_days)
    if via_api is not None:
        return via_api
    return _fetch_fred_via_csv(series_id, label, expected_gap_days)


@st.cache_data(ttl=CACHE_TTL_INTRADAY, show_spinner=False)
def fetch_yf(ticker: str, label: str = "", period: str = "5y",
             interval: str = "1d", expected_gap_days: int = 7) -> FetchResult:
    """Descarga precios de Yahoo Finance via yfinance, con manejo de errores."""
    label = label or ticker
    if yf is None:
        return FetchResult(label=label, status="error", error="yfinance no instalado", source="Yahoo Finance")
    if not ticker:
        return FetchResult(label=label, status="error", error="Ticker no configurado", source="Yahoo Finance")
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df is None or df.empty:
            return FetchResult(label=label, status="empty", error="Sin datos en Yahoo Finance",
                                source=f"Yahoo Finance:{ticker}")
        close_col = "Close"
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        series = df[close_col].dropna()
        series.index = pd.to_datetime(series.index)
        if series.empty:
            return FetchResult(label=label, status="empty", error="Serie vacia tras limpieza",
                                source=f"Yahoo Finance:{ticker}")
        asof = series.index.max()
        status = _infer_staleness(asof, expected_gap_days)
        return FetchResult(label=label, series=series, source=f"Yahoo Finance:{ticker}",
                            status=status, asof=asof, frequency_days=expected_gap_days,
                            resolved_ticker=ticker)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Yahoo Finance fetch failed for %s: %s", ticker, exc)
        return FetchResult(label=label, status="error", error=str(exc), source=f"Yahoo Finance:{ticker}")


@st.cache_data(ttl=CACHE_TTL_INTRADAY, show_spinner=False)
def fetch_stooq(symbol: str, label: str = "", expected_gap_days: int = 7) -> FetchResult:
    """Respaldo via Stooq (CSV publico) para simbolos sin cobertura en Yahoo Finance."""
    label = label or symbol
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    try:
        resp = requests.get(url, headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        if "Close" not in df.columns or "Date" not in df.columns or df.empty:
            return FetchResult(label=label, status="empty", error="Sin datos en Stooq",
                                source=f"Stooq:{symbol}")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        series = df.dropna(subset=["Date"]).set_index("Date")["Close"].dropna()
        if series.empty:
            return FetchResult(label=label, status="empty", error="Serie vacia tras limpieza",
                                source=f"Stooq:{symbol}")
        asof = series.index.max()
        status = _infer_staleness(asof, expected_gap_days)
        return FetchResult(label=label, series=series, source=f"Stooq:{symbol}", status=status,
                            asof=asof, frequency_days=expected_gap_days)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Stooq fetch failed for %s: %s", symbol, exc)
        return FetchResult(label=label, status="error", error=str(exc), source=f"Stooq:{symbol}")


def fetch_with_candidates(candidates: Sequence[str], label: str, period: str = "5y",
                           expected_gap_days: int = 7) -> FetchResult:
    """Intenta Yahoo Finance con una lista de tickers candidatos en orden; si todos
    fallan, intenta Stooq con el primer candidato como ultimo recurso."""
    last_result = FetchResult(label=label, status="error", error="Sin candidatos configurados")
    for cand in candidates:
        res = fetch_yf(cand, label=label, period=period, expected_gap_days=expected_gap_days)
        if res.ok:
            return res
        last_result = res
    if candidates:
        stooq_symbol = candidates[0].lower().replace("=x", "").replace("^", "")
        res = fetch_stooq(stooq_symbol, label=label, expected_gap_days=expected_gap_days)
        if res.ok:
            return res
    return last_result


@st.cache_data(ttl=CACHE_TTL_MACRO, show_spinner=False)
def fetch_top_holdings(ticker: str) -> Optional[pd.DataFrame]:
    """Top holdings de un ETF/fondo via yfinance (Ticker.funds_data.top_holdings).
    Devuelve un DataFrame indexado por simbolo con columnas 'Name' y
    'Holding Percent' (fraccion, ej. 0.085 = 8.5%), o None si no esta
    disponible (fondo sin modulo de holdings, o fuente caida). No todos los
    ETFs ni fondos mutuos exponen este modulo en Yahoo Finance; se maneja
    como una limitacion mas, sin inventar holdings."""
    if yf is None or not ticker:
        return None
    try:
        fd = yf.Ticker(ticker).funds_data
        df = fd.top_holdings
        if df is None or df.empty:
            return None
        return df
    except Exception as exc:  # noqa: BLE001
        logger.info("No se pudieron obtener los top holdings de %s: %s", ticker, exc)
        return None


@st.cache_data(ttl=CACHE_TTL_MACRO, show_spinner=False)
def fetch_fund_sector_weightings(ticker: str) -> Optional[dict]:
    """Ponderacion sectorial de un ETF/fondo (yfinance funds_data.sector_weightings).
    Devuelve None si no esta disponible."""
    if yf is None or not ticker:
        return None
    try:
        fd = yf.Ticker(ticker).funds_data
        sw = fd.sector_weightings
        if not sw:
            return None
        return sw
    except Exception as exc:  # noqa: BLE001
        logger.info("No se pudo obtener sector_weightings de %s: %s", ticker, exc)
        return None


# ==============================================================================
# 3. ANALYTICS LAYER
# ==============================================================================

def pct_change_over(series: pd.Series, periods: int) -> Optional[float]:
    if series is None or len(series) <= periods:
        return None
    base = series.iloc[-1 - periods]
    last = series.iloc[-1]
    if base == 0 or pd.isna(base) or pd.isna(last):
        return None
    return (last / base - 1.0) * 100.0


def level_change_over(series: pd.Series, periods: int) -> Optional[float]:
    if series is None or len(series) <= periods:
        return None
    base = series.iloc[-1 - periods]
    last = series.iloc[-1]
    if pd.isna(base) or pd.isna(last):
        return None
    return last - base


def rolling_zscore(series: pd.Series, window: int = 252) -> Optional[float]:
    if series is None or len(series) < max(20, window // 5):
        return None
    w = min(window, len(series))
    recent = series.iloc[-w:]
    mu, sigma = recent.mean(), recent.std()
    if sigma == 0 or pd.isna(sigma):
        return None
    return float((series.iloc[-1] - mu) / sigma)


def percentile_rank(series: pd.Series, window: Optional[int] = None) -> Optional[float]:
    if series is None or series.empty:
        return None
    hist = series if window is None else series.iloc[-window:]
    if len(hist) < 10:
        return None
    return float((hist <= hist.iloc[-1]).mean() * 100.0)


def annualized_vol(series: pd.Series, window: int = 63, trading_days: int = 252) -> Optional[float]:
    if series is None or len(series) < window + 1:
        return None
    rets = series.pct_change().dropna().iloc[-window:]
    if rets.empty:
        return None
    return float(rets.std() * np.sqrt(trading_days) * 100.0)


def max_drawdown(series: pd.Series, window: Optional[int] = None) -> Optional[float]:
    if series is None or series.empty:
        return None
    hist = series if window is None else series.iloc[-window:]
    running_max = hist.cummax()
    dd = (hist / running_max - 1.0) * 100.0
    return float(dd.min())


def trend_acceleration(series: pd.Series, short: int = 3, long_: int = 6) -> str:
    """Compara el cambio reciente (short) vs el cambio previo (long_-short) para
    detectar aceleracion/desaceleracion de una tendencia. Devuelve 'acelerando',
    'desacelerando' o 'estable'."""
    if series is None or len(series) < long_ + 1:
        return "sin_datos"
    recent_chg = series.iloc[-1] - series.iloc[-1 - short]
    prior_chg = series.iloc[-1 - short] - series.iloc[-1 - long_]
    if pd.isna(recent_chg) or pd.isna(prior_chg):
        return "sin_datos"
    if abs(prior_chg) < 1e-9:
        return "estable"
    same_sign = np.sign(recent_chg) == np.sign(prior_chg)
    if same_sign and abs(recent_chg) > abs(prior_chg) * 1.1:
        return "acelerando"
    if not same_sign or abs(recent_chg) < abs(prior_chg) * 0.6:
        return "desacelerando"
    return "estable"


def correlation_matrix(series_dict: dict) -> pd.DataFrame:
    df = pd.DataFrame({k: v for k, v in series_dict.items() if v is not None})
    df = df.dropna(how="all")
    if df.shape[1] < 2:
        return pd.DataFrame()
    return df.pct_change().dropna().corr()


def resample_monthly(series: pd.Series) -> pd.Series:
    if series is None or series.empty:
        return series
    return series.resample("MS").last().dropna()


# ------------------------------------------------------------------------------
# 3.1 Retornos por periodo calendario (WTD/MTD/YTD/1Y/3Y) y CAGR, usados
#     intensivamente en la pestana FFMM pero reutilizables en toda la app.
# ------------------------------------------------------------------------------

def period_return(series: pd.Series, anchor: str) -> Optional[float]:
    """Retorno (%) desde el cierre de referencia de 'anchor' hasta el ultimo
    dato disponible. anchor in {'WTD','MTD','YTD','1Y','3Y'}.
    - WTD/MTD/YTD: toman como base el ULTIMO cierre ESTRICTAMENTE ANTERIOR al
      inicio de la semana/mes/anio en curso (convencion estandar: 'cambio
      desde el cierre del periodo anterior'), evaluado sobre la ultima fecha
      disponible en la serie (no sobre la fecha de hoy), para que funcione
      igual de bien con datos de cierre de ayer que con datos de hace dias.
    - 1Y/3Y: toman como base el ultimo cierre disponible en o antes de
      (ultima_fecha - 1 o 3 anios).
    Devuelve None si no hay suficiente historia para construir la base.
    """
    if series is None or series.empty:
        return None
    series = series.dropna()
    if series.empty:
        return None
    last_date = series.index.max()
    last_val = series.iloc[-1]

    if anchor == "WTD":
        period_start = (last_date - pd.Timedelta(days=int(last_date.weekday()))).normalize()
        base_pool = series[series.index < period_start]
    elif anchor == "MTD":
        period_start = last_date.replace(day=1).normalize()
        base_pool = series[series.index < period_start]
    elif anchor == "YTD":
        period_start = last_date.replace(month=1, day=1).normalize()
        base_pool = series[series.index < period_start]
    elif anchor == "1Y":
        cutoff = last_date - pd.DateOffset(years=1)
        base_pool = series[series.index <= cutoff]
    elif anchor == "3Y":
        cutoff = last_date - pd.DateOffset(years=3)
        base_pool = series[series.index <= cutoff]
    else:
        raise ValueError(f"anchor desconocido: {anchor}")

    if base_pool.empty:
        return None
    base_val = base_pool.iloc[-1]
    if base_val == 0 or pd.isna(base_val) or pd.isna(last_val):
        return None
    return float((last_val / base_val - 1.0) * 100.0)


def cagr_from_cumulative(cum_return_pct: Optional[float], years: float) -> Optional[float]:
    """Convierte un retorno acumulado (%) en una tasa anualizada compuesta (%)."""
    if cum_return_pct is None or pd.isna(cum_return_pct) or years <= 0:
        return None
    growth = 1.0 + cum_return_pct / 100.0
    if growth <= 0:
        return None
    return float((growth ** (1.0 / years) - 1.0) * 100.0)


def fund_metrics(series: pd.Series) -> dict:
    """Bloque estandar de metricas de performance para un fondo/ETF/accion:
    ultimo precio, ultimo retorno diario y retornos WTD/MTD/YTD/1Y/3Y
    (acumulado y anualizado), mas volatilidad anualizada 1Y, usado tanto en
    la tabla resumen como en la ficha de detalle de la pestana FFMM."""
    if series is None or series.empty:
        return {}
    series = series.dropna()
    last_price = float(series.iloc[-1])
    daily_ret = None
    if len(series) >= 2:
        prev = series.iloc[-2]
        if prev != 0 and not pd.isna(prev):
            daily_ret = float((series.iloc[-1] / prev - 1.0) * 100.0)
    r3y_cum = period_return(series, "3Y")
    return {
        "ultimo_precio": last_price,
        "ultimo_retorno_%": daily_ret,
        "wtd_%": period_return(series, "WTD"),
        "mtd_%": period_return(series, "MTD"),
        "ytd_%": period_return(series, "YTD"),
        "r1y_%": period_return(series, "1Y"),
        "r3y_acum_%": r3y_cum,
        "r3y_cagr_%": cagr_from_cumulative(r3y_cum, 3.0),
        "vol_1y_%": annualized_vol(series, window=min(len(series) - 1, 252)) if len(series) > 20 else None,
        "fecha_ultimo_dato": series.index.max(),
    }


def dispersion_stats(returns: Sequence[float]) -> dict:
    """Dispersion simple (max-min, desv. estandar) de un conjunto de retornos
    de pares/categoria: util para destacar que tan homogeneo o heterogeneo
    se movio un grupo tematico en la pestana FFMM."""
    vals = [v for v in returns if v is not None and not pd.isna(v)]
    if len(vals) < 2:
        return {}
    arr = np.array(vals, dtype=float)
    return {"max": float(arr.max()), "min": float(arr.min()), "spread": float(arr.max() - arr.min()),
            "std": float(arr.std()), "mean": float(arr.mean()), "n": len(arr)}


# ==============================================================================
# 4. STORYTELLING ENGINE  (biblioteca de patrones interpretativos reutilizables)
# ==============================================================================

def _direction_word(delta: Optional[float], flat_eps: float = 0.05) -> str:
    if delta is None or pd.isna(delta):
        return "sin variacion clara"
    if delta > flat_eps:
        return "al alza"
    if delta < -flat_eps:
        return "a la baja"
    return "lateral"


def _magnitude_word(abs_pct: Optional[float]) -> str:
    if abs_pct is None or pd.isna(abs_pct):
        return ""
    a = abs(abs_pct)
    if a < 1:
        return "marginal"
    if a < 3:
        return "moderado"
    if a < 8:
        return "significativo"
    return "muy marcado"


def _percentile_phrase(pct: Optional[float]) -> str:
    if pct is None or pd.isna(pct):
        return ""
    if pct >= 90:
        return "en zona de maximos historicos recientes (percentil >90)"
    if pct >= 70:
        return "en la parte alta de su rango reciente"
    if pct <= 10:
        return "en zona de minimos historicos recientes (percentil <10)"
    if pct <= 30:
        return "en la parte baja de su rango reciente"
    return "cerca de niveles medios de su rango reciente"


def _trend_phrase(trend: str) -> str:
    return {
        "acelerando": "el movimiento se esta acelerando",
        "desacelerando": "el movimiento muestra senales de desaceleracion",
        "estable": "el ritmo de cambio se mantiene relativamente estable",
        "sin_datos": "",
    }.get(trend, "")


def interpret_market_series(label: str, series: pd.Series, asset_class: str,
                             extra_note: str = "") -> str:
    """Interprete generico para un instrumento de mercado (commodity, equity,
    FX, yield) a partir de direccion, magnitud, percentil historico y
    aceleracion de tendencia. Satisface el patron What/Why/Investment implication
    de forma natural, sin forzar las tres preguntas en cada texto."""
    if series is None or series.empty or len(series) < 10:
        return f"**{label}**: datos insuficientes para generar una interpretacion confiable."

    chg_1m = pct_change_over(series, 21)
    chg_3m = pct_change_over(series, 63)
    chg_12m = pct_change_over(series, 252)
    z = rolling_zscore(series, window=min(len(series), 252))
    pct_rank = percentile_rank(series, window=min(len(series), 252 * 2))
    trend = trend_acceleration(series)
    dd = max_drawdown(series, window=min(len(series), 252))
    vol = annualized_vol(series)

    ref_chg = chg_3m if chg_3m is not None else chg_1m
    direction = _direction_word(ref_chg)
    magnitude = _magnitude_word(ref_chg)
    pct_phrase = _percentile_phrase(pct_rank)
    trend_phrase = _trend_phrase(trend)

    cls_label = ASSET_CLASS_LABELS.get(asset_class, "activo")
    parts = []

    headline = f"**{label}** se mueve {direction}"
    if magnitude:
        headline += f" de forma {magnitude}"
    if chg_3m is not None:
        headline += f" en los ultimos 3 meses ({chg_3m:+.1f}%)"
    headline += "."
    parts.append(headline)

    if chg_12m is not None and chg_3m is not None and np.sign(chg_12m) != np.sign(chg_3m) and abs(chg_12m) > 2:
        parts.append(f"Esto contrasta con la variacion de los ultimos 12 meses ({chg_12m:+.1f}%), lo que sugiere un "
                     f"posible cambio de regimen en curso mas que una simple continuacion de la tendencia anual.")
    elif chg_12m is not None:
        parts.append(f"En el acumulado de 12 meses la variacion es de {chg_12m:+.1f}%.")

    if pct_phrase:
        s = f"El nivel actual se ubica {pct_phrase}"
        if z is not None and abs(z) >= 1.5:
            s += f", con una desviacion de {z:+.1f} veces su volatilidad reciente respecto al promedio"
        s += "."
        parts.append(s)

    if trend_phrase and trend != "sin_datos":
        parts.append(f"En el margen, {trend_phrase}, lo que sugiere vigilar si el patron se mantiene en las proximas lecturas antes de extrapolarlo.")

    if vol is not None and asset_class in ("equity", "fx", "energy", "precious_metal", "industrial_metal"):
        if vol > 30:
            parts.append(f"La volatilidad anualizada reciente ({vol:.0f}%) es elevada, lo que exige posiciones mas conservadoras en terminos de tamano de riesgo.")
        elif vol < 10:
            parts.append(f"La volatilidad anualizada reciente ({vol:.0f}%) es baja para un {cls_label}, lo que puede estar comprimiendo las primas de riesgo asociadas.")

    if dd is not None and dd < -15:
        parts.append(f"El drawdown desde el maximo de los ultimos 12 meses es de {dd:.1f}%, una correccion relevante que condiciona el punto de entrada actual.")

    if extra_note:
        parts.append(extra_note)

    return " ".join(parts)


def interpret_labor_market(unrate: pd.Series, payrolls: pd.Series,
                            claims: pd.Series) -> str:
    """Interprete compuesto siguiendo el ejemplo del punto 3.C: combina 3
    senales (tasa de desempleo, creacion de empleo, solicitudes de desempleo)
    en lugar de leerlas de forma aislada, y evita concluir deterioro cuando
    las senales son contradictorias."""
    signals = []

    unrate_chg = level_change_over(unrate, 6) if unrate is not None else None   # ~6 meses
    payrolls_trend_now = (payrolls.diff().iloc[-3:].mean() if payrolls is not None and len(payrolls) > 4 else None)
    payrolls_trend_prior = (payrolls.diff().iloc[-9:-3].mean() if payrolls is not None and len(payrolls) > 9 else None)
    claims_chg = pct_change_over(claims, 8) if claims is not None else None     # ~2 meses de datos semanales

    cooling_votes = 0
    resilient_votes = 0

    if unrate_chg is not None:
        if unrate_chg > 0.1:
            cooling_votes += 1
            signals.append(f"la tasa de desempleo subio {unrate_chg:+.1f} pp en los ultimos ~6 meses")
        elif unrate_chg < -0.1:
            resilient_votes += 1
            signals.append(f"la tasa de desempleo bajo {unrate_chg:+.1f} pp en los ultimos ~6 meses")

    if payrolls_trend_now is not None and payrolls_trend_prior is not None:
        if payrolls_trend_now < payrolls_trend_prior * 0.7:
            cooling_votes += 1
            signals.append("el ritmo de creacion de empleo se ha desacelerado frente al trimestre previo")
        elif payrolls_trend_now > payrolls_trend_prior * 1.1:
            resilient_votes += 1
            signals.append("la creacion de empleo se mantiene solida o incluso se acelera")

    if claims_chg is not None:
        if claims_chg > 10:
            cooling_votes += 1
            signals.append(f"las solicitudes de desempleo subieron {claims_chg:+.0f}% en ~2 meses")
        elif claims_chg < -10:
            resilient_votes += 1
            signals.append(f"las solicitudes de desempleo cayeron {claims_chg:+.0f}% en ~2 meses")

    if not signals:
        return "**Mercado laboral (EE.UU.)**: datos insuficientes o sin variaciones relevantes para construir una lectura integrada."

    detail = "; ".join(signals) + "."

    if cooling_votes >= 2 and resilient_votes == 0:
        verdict = ("El conjunto de senales apunta a un enfriamiento consistente del mercado laboral. "
                   "Esto reduce la presion salarial sobre la inflacion y amplia el margen de la Fed para "
                   "flexibilizar su politica monetaria; el riesgo principal es que el enfriamiento se acelere "
                   "mas alla de un ajuste ordenado.")
    elif resilient_votes >= 2 and cooling_votes == 0:
        verdict = ("El conjunto de senales sugiere que el mercado laboral se mantiene resiliente. "
                   "Esto sostiene el consumo privado pero tambien limita el espacio para recortes de tasas "
                   "en el corto plazo si la inflacion no converge con suficiente rapidez.")
    else:
        verdict = ("Las senales son mixtas o contradictorias entre si, por lo que no corresponde concluir de "
                   "forma automatica que el mercado laboral se esta deteriorando o fortaleciendo: conviene "
                   "esperar mas lecturas antes de ajustar convicciones de asset allocation ligadas al ciclo laboral.")

    return f"**Mercado laboral (EE.UU.)**: {detail} {verdict}"


def interpret_inflation(cpi: pd.Series, core_cpi: pd.Series,
                         breakeven_5y: Optional[pd.Series] = None) -> str:
    """Interprete compuesto de inflacion: nivel YoY, tendencia (acelera/desacelera)
    y, si esta disponible, la expectativa de mercado (breakeven) para contrastar
    inflacion observada vs. inflacion esperada."""
    if cpi is None or len(cpi) < 14:
        return "**Inflacion (EE.UU.)**: datos insuficientes para una lectura confiable."

    cpi_m = resample_monthly(cpi)
    yoy = pct_change_over(cpi_m, 12)
    yoy_prior = pct_change_over(cpi_m.iloc[:-1], 12) if len(cpi_m) > 13 else None
    core_m = resample_monthly(core_cpi) if core_cpi is not None else None

    core_yoy = pct_change_over(core_m, 12) if core_m is not None else None

    parts = []
    if yoy is not None:
        txt = f"La inflacion headline se ubica en {yoy:.1f}% interanual"
        if yoy_prior is not None:
            delta = yoy - yoy_prior
            if delta > 0.05:
                txt += f", acelerando frente al mes previo (+{delta:.1f} pp)"
            elif delta < -0.05:
                txt += f", desacelerando frente al mes previo ({delta:.1f} pp)"
            else:
                txt += ", sin cambios relevantes frente al mes previo"
        txt += "."
        parts.append(txt)

    if core_yoy is not None and yoy is not None:
        gap = core_yoy - yoy
        if abs(gap) > 0.3:
            direction = "por encima" if gap > 0 else "por debajo"
            parts.append(f"La inflacion core ({core_yoy:.1f}%) corre {direction} de la headline, lo que senala que "
                         f"componentes volatiles (energia/alimentos) estan {'atenuando' if gap>0 else 'presionando'} "
                         f"la lectura total, un matiz relevante para la trayectoria de politica monetaria.")

    if breakeven_5y is not None and not breakeven_5y.empty and yoy is not None:
        be = breakeven_5y.iloc[-1]
        if not pd.isna(be):
            gap2 = yoy - be
            if gap2 > 0.5:
                parts.append(f"La inflacion observada (header {yoy:.1f}%) supera a la expectativa de mercado a 5 anos "
                             f"({be:.1f}%), lo que sugiere que el mercado sigue asignando alta probabilidad a una "
                             f"normalizacion gradual sin necesidad de un ciclo de endurecimiento adicional.")
            elif gap2 < -0.5:
                parts.append(f"La inflacion observada ({yoy:.1f}%) esta por debajo de la expectativa de mercado a 5 anos "
                             f"({be:.1f}%), una divergencia que vale la pena monitorear para detectar cambios de regimen.")

    if not parts:
        return "**Inflacion (EE.UU.)**: sin senales suficientemente claras para una interpretacion."

    return "**Inflacion (EE.UU.)**: " + " ".join(parts)


def interpret_fed_policy(fed_funds: pd.Series, balance_sheet: pd.Series) -> str:
    if fed_funds is None or fed_funds.empty:
        return "**Politica de la Fed**: datos insuficientes."
    rate = fed_funds.iloc[-1]
    rate_chg_6m = level_change_over(resample_monthly(fed_funds), 6)
    parts = [f"La Fed Funds Rate se ubica en {rate:.2f}%."]
    if rate_chg_6m is not None:
        if rate_chg_6m > 0.1:
            parts.append(f"En los ultimos ~6 meses la tasa subio {rate_chg_6m:+.2f} pp, consistente con un sesgo de politica restrictivo o de pausa alta.")
        elif rate_chg_6m < -0.1:
            parts.append(f"En los ultimos ~6 meses la tasa bajo {rate_chg_6m:+.2f} pp, consistente con un ciclo de flexibilizacion en curso.")
        else:
            parts.append("La tasa se ha mantenido estable en los ultimos meses, en linea con una postura de 'esperar y ver' (data-dependent).")

    if balance_sheet is not None and not balance_sheet.empty and len(balance_sheet) > 12:
        bs_m = resample_monthly(balance_sheet)
        chg_6m = pct_change_over(bs_m, 6)
        if chg_6m is not None:
            if chg_6m < -1.0:
                parts.append(f"El balance de la Fed se ha contraido {chg_6m:.1f}% en ~6 meses (Quantitative Tightening en curso), lo que retira liquidez del sistema de forma gradual.")
            elif chg_6m > 1.0:
                parts.append(f"El balance de la Fed se ha expandido {chg_6m:+.1f}% en ~6 meses, una senal de provision de liquidez que contrasta con el discurso de normalizacion.")

    return "**Politica de la Fed**: " + " ".join(parts)


def interpret_yield_curve(y2: pd.Series, y10: pd.Series, y30: pd.Series) -> str:
    if y2 is None or y10 is None or y2.empty or y10.empty:
        return "**Curva de rendimientos (UST)**: datos insuficientes."
    spread = y10.iloc[-1] - y2.iloc[-1]
    spread_hist = (y10 - y2).dropna()
    spread_3m_ago = spread_hist.iloc[-63] if len(spread_hist) > 63 else None

    parts = [f"El spread 10Y-2Y se ubica en {spread:+.2f} pp."]
    if spread < 0:
        parts.append("La curva permanece invertida, una senal historicamente asociada a riesgo de recesion dentro de los siguientes 12-24 meses, aunque con rezagos variables.")
    else:
        parts.append("La curva se mantiene en pendiente positiva (no invertida).")

    if spread_3m_ago is not None:
        delta = spread - spread_3m_ago
        if delta > 0.1:
            parts.append(f"El empinamiento de {delta:+.2f} pp en 3 meses es consistente con un proceso de 'bull steepening' o 'bear steepening' segun si domino la baja del tramo corto o la suba del tramo largo; conviene revisar el nivel absoluto de cada tramo para distinguir el tipo de empinamiento.")
        elif delta < -0.1:
            parts.append(f"El aplanamiento de {delta:+.2f} pp en 3 meses reduce el margen de carry positivo en estrategias de pendiente.")

    if y30 is not None and not y30.empty:
        term_premium_proxy = y30.iloc[-1] - y10.iloc[-1]
        parts.append(f"El tramo largo (30Y) cotiza a {y30.iloc[-1]:.2f}%, con un spread de {term_premium_proxy:+.2f} pp sobre el 10Y, relevante para fondos con pasivos de muy largo plazo.")

    return "**Curva de rendimientos (UST)**: " + " ".join(parts)


def interpret_fiscal(debt_gdp: pd.Series, deficit: pd.Series) -> str:
    parts = []
    if debt_gdp is not None and not debt_gdp.empty:
        lvl = debt_gdp.iloc[-1]
        chg = level_change_over(resample_monthly(debt_gdp), 4)
        s = f"La deuda publica federal equivale a {lvl:.0f}% del PBI"
        if chg is not None:
            s += f", {'en ascenso' if chg > 0.5 else 'relativamente estable' if abs(chg) <= 0.5 else 'en descenso'} en el ultimo ano"
        s += "."
        parts.append(s)
    if deficit is not None and not deficit.empty:
        last12 = deficit.iloc[-12:].sum() if len(deficit) >= 12 else None
        if last12 is not None:
            parts.append(f"El resultado fiscal acumulado de los ultimos 12 meses es de {last12:,.0f} USD millones "
                         f"({'deficit' if last12 < 0 else 'superavit'}), un factor que sostiene la oferta neta de Treasuries "
                         f"y, en el margen, presiona al alza el tramo largo de la curva vía prima por plazo.")
    if not parts:
        return "**Situacion fiscal (EE.UU.)**: datos insuficientes."
    return "**Situacion fiscal (EE.UU.)**: " + " ".join(parts)


def interpret_stress_index(series: pd.Series, label: str, zero_centered: bool = True) -> str:
    if series is None or series.empty:
        return f"**{label}**: datos insuficientes."
    last = series.iloc[-1]
    z = rolling_zscore(series, window=min(len(series), 260))
    if zero_centered:
        if last > 0.5:
            level_txt = "en niveles de estres financiero claramente por encima del promedio historico"
        elif last < -0.5:
            level_txt = "en niveles que reflejan condiciones financieras holgadas (por debajo del promedio historico)"
        else:
            level_txt = "cerca de su promedio historico, sin senales de tension inusual"
    else:
        level_txt = "en el nivel mostrado"
    txt = f"**{label}** se ubica {level_txt} ({last:.2f})."
    if z is not None and abs(z) >= 1.5:
        txt += f" La desviacion respecto a su media reciente ({z:+.1f}x) sugiere un movimiento fuera de lo habitual que merece seguimiento."
    return txt


def interpret_commodity_with_context(name: str, series: pd.Series, peru_relevance: str) -> str:
    base = interpret_market_series(name, series, COMMODITIES.get(name, {}).get("asset_class", "energy"))
    if peru_relevance in ("alta", "muy alta"):
        extra = (f" Dada la relevancia {peru_relevance} de este commodity para la economia y el mercado de capitales "
                 f"peruano (mineria), este movimiento tiene traslado directo a los terminos de intercambio, la "
                 f"recaudacion fiscal minera y el desempeno relativo de las mineras listadas en la pestana PERU.")
        return base + extra
    return base


def interpret_fx(label: str, series: pd.Series, is_usd_base: bool = False) -> str:
    """is_usd_base=True cuando el par se cotiza como 'moneda local por USD'
    (ej. USD/PEN): una suba de la serie implica DEPRECIACION de la moneda local."""
    base = interpret_market_series(label, series, "fx")
    if series is None or len(series) < 30:
        return base
    chg_3m = pct_change_over(series, 63)
    if chg_3m is None:
        return base
    if is_usd_base:
        verb = "depreciandose" if chg_3m > 0 else "apreciandose"
    else:
        verb = "apreciandose" if chg_3m > 0 else "depreciandose"
    extra = f" En terminos de moneda local, esto implica que la divisa se viene {verb} frente al dolar en el trimestre, con implicancias directas sobre inflacion importada, costo de deuda en moneda extranjera y competitividad externa."
    return base + extra


def interpret_country_scorecard(country: str, cpi_yoy: Optional[float], rate: Optional[float],
                                 y10: Optional[float], gdp: Optional[float],
                                 fx_chg_3m: Optional[float]) -> str:
    parts = []
    if cpi_yoy is not None and rate is not None:
        real_rate = rate - cpi_yoy
        parts.append(f"La tasa de politica monetaria ({rate:.2f}%) frente a una inflacion de {cpi_yoy:.1f}% interanual "
                     f"implica una tasa real aproximada de {real_rate:+.1f} pp, "
                     f"{'claramente restrictiva' if real_rate > 2 else 'restrictiva' if real_rate > 0 else 'acomodaticia'}.")
    elif cpi_yoy is not None:
        parts.append(f"La inflacion interanual se ubica en {cpi_yoy:.1f}%.")

    if y10 is not None and rate is not None:
        slope = y10 - rate
        if slope < -0.3:
            parts.append(f"La curva local esta invertida ({slope:+.2f} pp entre el 10Y y la tasa de politica), una senal de expectativas de recorte de tasas o de preocupacion por el ciclo.")

    if gdp is not None:
        parts.append(f"El crecimiento del PBI real anual mas reciente disponible es de {gdp:.1f}%.")

    if fx_chg_3m is not None and abs(fx_chg_3m) > 3:
        direction = "depreciado" if fx_chg_3m > 0 else "apreciado"
        parts.append(f"La moneda local se ha {direction} {abs(fx_chg_3m):.1f}% frente al USD en el trimestre, un movimiento relevante para la narrativa de bonos y equity local.")

    if not parts:
        return f"**{country}**: datos insuficientes para un scorecard completo con las fuentes gratuitas disponibles."
    return f"**{country}**: " + " ".join(parts)


# ------------------------------------------------------------------------------
# 4.1 FFMM: resumen de performance por periodo + performance attribution por
#     Top Holdings, estilo CFA (ver nota de aproximacion de pesos en la
#     cabecera del archivo).
# ------------------------------------------------------------------------------

def fund_periods_summary(label: str, metrics: dict) -> str:
    """Resumen corto del desempeno de un fondo en todos los horizontes
    pedidos (WTD/MTD/YTD/1Y/3Y), en tono PM, mas el ultimo precio/retorno."""
    if not metrics:
        return f"**{label}**: datos insuficientes para resumir su performance."
    wtd, mtd, ytd = metrics.get("wtd_%"), metrics.get("mtd_%"), metrics.get("ytd_%")
    r1y, r3y_cum, r3y_cagr = metrics.get("r1y_%"), metrics.get("r3y_acum_%"), metrics.get("r3y_cagr_%")
    last_price, last_ret = metrics.get("ultimo_precio"), metrics.get("ultimo_retorno_%")

    def _fmt(x):
        return f"{x:+.1f}%" if x is not None else "N/D"

    txt = f"**{label}** cotiza en {last_price:,.2f}"
    if last_ret is not None:
        txt += f" ({last_ret:+.1f}% en la ultima sesion)"
    txt += f". Retornos: WTD {_fmt(wtd)} · MTD {_fmt(mtd)} · YTD {_fmt(ytd)} · 1Y {_fmt(r1y)} · " \
           f"3Y acumulado {_fmt(r3y_cum)} (CAGR {_fmt(r3y_cagr)})."

    if wtd is not None and r1y is not None:
        if np.sign(wtd) != 0 and np.sign(r1y) != 0 and np.sign(wtd) != np.sign(r1y) and abs(wtd) > 2:
            txt += (" El movimiento de la ultima semana va en sentido contrario a la tendencia de 12 meses, "
                   "lo que amerita revisar si es ruido de corto plazo o el inicio de un cambio de regimen.")
    return txt


def performance_attribution_story(fund_label: str, period_label: str, fund_return: Optional[float],
                                   attrib_df: pd.DataFrame, residual_pp: Optional[float]) -> str:
    """Narrativa de performance attribution estilo CFA: explica el retorno de
    un fondo/ETF en un periodo a partir de la contribucion (peso x retorno)
    de sus principales holdings. attrib_df debe tener columnas 'Name',
    'Weight_%', 'Return_%', 'Contribution_pp', ordenado por contribucion."""
    if fund_return is None:
        return f"**{fund_label}**: no fue posible calcular el retorno del periodo {period_label} para construir la atribucion."
    if attrib_df is None or attrib_df.empty:
        return (f"**{fund_label}** registro un retorno {period_label} de {fund_return:+.1f}%, pero no hay datos de "
                f"Top Holdings disponibles en Yahoo Finance para este instrumento, por lo que no es posible "
                f"descomponer el movimiento por activo subyacente.")

    sorted_df = attrib_df.sort_values("Contribution_pp")
    detractors = sorted_df[sorted_df["Contribution_pp"] < 0].head(2)
    contributors = sorted_df[sorted_df["Contribution_pp"] > 0].sort_values("Contribution_pp", ascending=False).head(2)

    def _holding_phrase(row):
        return (f"{row['Name']} ({row.name}, peso {row['Weight_%']:.1f}%, retorno {row['Return_%']:+.1f}%, "
                f"contribucion {row['Contribution_pp']:+.2f} pp)")

    parts = [f"**{fund_label}** registro un retorno {period_label} de {fund_return:+.1f}%."]

    if not detractors.empty and fund_return < 0:
        phrases = "; ".join(_holding_phrase(r) for _, r in detractors.iterrows())
        parts.append(f"Los principales detractores dentro del Top Holdings fueron {phrases}.")
    elif not contributors.empty and fund_return > 0:
        phrases = "; ".join(_holding_phrase(r) for _, r in contributors.iterrows())
        parts.append(f"Los principales contribuyentes dentro del Top Holdings fueron {phrases}.")

    if fund_return < 0 and not contributors.empty:
        phrases = "; ".join(_holding_phrase(r) for _, r in contributors.iterrows())
        parts.append(f"Como contrapeso parcial, {phrases} aportaron positivamente.")
    elif fund_return > 0 and not detractors.empty:
        phrases = "; ".join(_holding_phrase(r) for _, r in detractors.iterrows())
        parts.append(f"En contraste, {phrases} resto(aron) parte de la ganancia.")

    if residual_pp is not None and abs(residual_pp) > 0.3:
        parts.append(f"El resto de holdings fuera del Top 10 (y efectos de caja/rebalanceo) explican "
                     f"aproximadamente {residual_pp:+.2f} pp adicionales del retorno total.")

    parts.append("Nota metodologica: la atribucion usa los pesos VIGENTES mas recientes de cada holding "
                 "(los unicos que expone Yahoo Finance de forma gratuita), no los pesos exactos al inicio "
                 "del periodo analizado, por lo que es una aproximacion razonable del driver principal del "
                 "movimiento, no una atribucion Brinson exacta con pesos diarios.")

    return " ".join(parts)


def category_theme_commentary(theme_label: str, returns_in_group: dict) -> str:
    """Comentario tipo 'Weekly Top of Mind' para un grupo tematico (ej. todos
    los fondos de SubCat2='Semiconductors'): identifica el mejor y peor
    performer del grupo y la dispersion, en 2-3 oraciones."""
    clean = {k: v for k, v in returns_in_group.items() if v is not None and not pd.isna(v)}
    if len(clean) < 2:
        return f"**{theme_label}**: datos insuficientes para comparar el grupo."
    best_name, best_val = max(clean.items(), key=lambda kv: kv[1])
    worst_name, worst_val = min(clean.items(), key=lambda kv: kv[1])
    stats = dispersion_stats(list(clean.values()))

    txt = (f"**{theme_label}**: dentro de este grupo ({stats['n']} fondos con datos), {best_name} lidera con "
           f"{best_val:+.1f}%, mientras que {worst_name} es el rezagado con {worst_val:+.1f}% "
           f"(dispersion de {stats['spread']:.1f} pp entre el mejor y el peor).")

    if stats["spread"] > 15:
        txt += (" Una dispersion tan amplia dentro de un mismo tema sugiere que el driver del movimiento es mas "
               "idiosincratico (fundamentales especificos, flujos, posicionamiento) que puramente macro/sectorial; "
               "conviene mirar cada fondo individualmente antes de generalizar sobre el tema.")
    elif stats["spread"] < 5:
        txt += (" La baja dispersion indica que el grupo se mueve de forma cohesionada, consistente con un driver "
               "macro o sectorial comun dominando por encima de las diferencias idiosincraticas entre fondos.")

    return txt


# ==============================================================================
# 5. UI HELPERS
# ==============================================================================

def freshness_badge(result: FetchResult) -> str:
    if result.status == "ok":
        return "🟢 actualizado"
    if result.status == "stale":
        return f"🟡 desactualizado (ult. dato: {result.asof.date() if result.asof is not None else 'N/D'})"
    if result.status == "empty":
        return "⚪ sin observaciones"
    return "🔴 no disponible"


def source_caption(result: FetchResult) -> str:
    cap = f"Fuente: {result.source} · {freshness_badge(result)}"
    if result.error and not result.ok:
        cap += f" · motivo: {result.error}"
    return cap


def plot_line(series: pd.Series, title: str, y_title: str = "", ma_windows: Sequence[int] = ()) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines",
                              name=title, line=dict(width=2)))
    for w in ma_windows:
        if len(series) > w:
            ma = series.rolling(w).mean()
            fig.add_trace(go.Scatter(x=ma.index, y=ma.values, mode="lines",
                                      name=f"MA{w}", line=dict(width=1, dash="dot")))
    fig.update_layout(title=title, yaxis_title=y_title, margin=dict(l=10, r=10, t=40, b=10),
                       height=320, template="plotly_white", legend=dict(orientation="h", y=-0.2))
    return fig


def plot_multi(series_dict: dict, title: str, normalize: bool = True) -> go.Figure:
    fig = go.Figure()
    for name, s in series_dict.items():
        if s is None or s.empty:
            continue
        y = (s / s.iloc[0] * 100.0) if normalize else s
        fig.add_trace(go.Scatter(x=y.index, y=y.values, mode="lines", name=name))
    fig.update_layout(title=title, margin=dict(l=10, r=10, t=40, b=10), height=380,
                       template="plotly_white", yaxis_title="Base 100" if normalize else "",
                       legend=dict(orientation="h", y=-0.25))
    return fig


def metric_row(items: Sequence[tuple]):
    """items: lista de (label, value_str, delta_str_or_None)"""
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        col.metric(label, value, delta)


def render_result_block(result: FetchResult, chart: bool = True, ma_windows: Sequence[int] = (),
                         y_title: str = "", story_fn=None, **story_kwargs):
    st.markdown(f"#### {result.label}")
    if not result.ok:
        st.warning(f"Dato no disponible. {source_caption(result)}")
        return
    c1, c2 = st.columns([2, 1])
    with c1:
        if chart:
            st.plotly_chart(plot_line(result.series, result.label, y_title, ma_windows),
                             use_container_width=True)
    with c2:
        last = result.series.iloc[-1]
        chg_1m = pct_change_over(result.series, 21)
        chg_12m = pct_change_over(result.series, 252)
        st.metric("Ultimo valor", f"{last:,.2f}",
                   f"{chg_1m:+.1f}% (1M)" if chg_1m is not None else None)
        if chg_12m is not None:
            st.caption(f"Var. 12M: {chg_12m:+.1f}%")
        st.caption(source_caption(result))
    if story_fn is not None:
        st.info(story_fn(result.label, result.series, **story_kwargs))


def _sign_color(value: Optional[float], light: bool = False) -> str:
    if value is None or pd.isna(value):
        return "#f0f0f0" if light else "#ffffff"
    if value > 0:
        return "#e6f4ea" if light else "#1e7e34"
    if value < 0:
        return "#fbe9e7" if light else "#c62828"
    return "#f0f0f0" if light else "#555555"


def styled_returns_table(df: pd.DataFrame, pct_cols: Sequence[str], price_cols: Sequence[str] = ()):
    """Renderiza una tabla con celdas coloreadas (verde/rojo segun signo) para
    las columnas de retorno indicadas, al estilo de las tablas de 'Market
    Performance' de los weekly reports institucionales (DBS/HSBC/BlackRock/
    Goldman Sachs: codigo de color + valor numerico, sin adornos extra)."""
    def _color_col(s: pd.Series):
        return [f"background-color: {_sign_color(v, light=True)}" for v in s]

    def _pct_fmt(x):
        return f"{x:+.1f}%" if pd.notna(x) else "N/D"

    def _price_fmt(x):
        return f"{x:,.2f}" if pd.notna(x) else "N/D"

    fmt = {c: _pct_fmt for c in pct_cols}
    fmt.update({c: _price_fmt for c in price_cols})
    styled = df.style.apply(_color_col, subset=list(pct_cols), axis=0).format(fmt)
    st.dataframe(styled, use_container_width=True, hide_index=True)


def plot_winners_losers(returns: dict, title: str, top_n: int = 5) -> go.Figure:
    """Barra horizontal con los top N ganadores y top N perdedores de un
    conjunto de retornos {nombre: retorno_%}."""
    clean = {k: v for k, v in returns.items() if v is not None and not pd.isna(v)}
    ordered = sorted(clean.items(), key=lambda kv: kv[1])
    losers = ordered[:top_n]
    winners = ordered[-top_n:]
    combo = losers + [w for w in winners if w not in losers]
    combo.sort(key=lambda kv: kv[1])
    names = [c[0] for c in combo]
    vals = [c[1] for c in combo]
    colors = [_sign_color(v) for v in vals]
    fig = go.Figure(go.Bar(x=vals, y=names, orientation="h", marker_color=colors,
                            text=[f"{v:+.1f}%" for v in vals], textposition="outside"))
    fig.update_layout(title=title, height=max(300, 28 * len(names)), template="plotly_white",
                       margin=dict(l=10, r=40, t=40, b=10), xaxis_title="%")
    return fig


def plot_attribution_bars(attrib_df: pd.DataFrame, residual_pp: Optional[float], title: str) -> go.Figure:
    """Barras de contribucion (peso x retorno) por holding, estilo CFA
    performance attribution, mas una barra de 'Resto del portafolio'."""
    df = attrib_df.sort_values("Contribution_pp")
    names = list(df["Name"] + " (" + df.index.astype(str) + ")")
    vals = list(df["Contribution_pp"])
    if residual_pp is not None:
        names = ["Resto del portafolio / caja"] + names
        vals = [residual_pp] + vals
    colors = [_sign_color(v) for v in vals]
    fig = go.Figure(go.Bar(x=vals, y=names, orientation="h", marker_color=colors,
                            text=[f"{v:+.2f} pp" for v in vals], textposition="outside"))
    fig.update_layout(title=title, height=max(320, 32 * len(names)), template="plotly_white",
                       margin=dict(l=10, r=60, t=40, b=10), xaxis_title="Contribucion (pp)")
    return fig


def plot_heatmap(corr_df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure(go.Heatmap(z=corr_df.values, x=list(corr_df.columns), y=list(corr_df.index),
                                colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
                                text=np.round(corr_df.values, 2), texttemplate="%{text}",
                                colorbar=dict(title="corr")))
    fig.update_layout(title=title, height=max(400, 28 * len(corr_df)), template="plotly_white",
                       margin=dict(l=10, r=10, t=40, b=10))
    return fig


def plot_risk_return_scatter(df: pd.DataFrame, title: str) -> go.Figure:
    """Scatter clasico riesgo/retorno: eje X = volatilidad anualizada 1Y,
    eje Y = retorno 1Y, color por categoria, tamano fijo. df debe tener
    columnas 'Nombre', 'vol_1y_%', 'r1y_%', 'cat'."""
    fig = go.Figure()
    for cat, sub in df.groupby("cat"):
        fig.add_trace(go.Scatter(x=sub["vol_1y_%"], y=sub["r1y_%"], mode="markers", name=cat,
                                  text=sub["Nombre"], marker=dict(size=11, opacity=0.85),
                                  hovertemplate="%{text}<br>Vol 1Y: %{x:.1f}%<br>Retorno 1Y: %{y:.1f}%<extra></extra>"))
    fig.update_layout(title=title, xaxis_title="Volatilidad anualizada 1Y (%)",
                       yaxis_title="Retorno 1Y (%)", height=460, template="plotly_white",
                       margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.25))
    return fig


# ==============================================================================
# 6. LOADERS DINAMICOS (ZODA.xlsx y Portafolio_FFMM.xlsx, opcionales)
# ==============================================================================

# ------------------------------------------------------------------------------
# 6.1 ZODA LOADER (lectura dinamica opcional de ZODA.xlsx -> hoja Parametria)
# ------------------------------------------------------------------------------

def load_zoda_parametria(uploaded_file) -> Optional[list]:
    """Lee dinamicamente la hoja 'Parametria' de un ZODA.xlsx subido por el
    usuario y construye el universo de instrumentos peruanos a partir de las
    columnas 'Empresa' / 'BBG'. Si falla, devuelve None y la app usa el
    universo por defecto (ya identificado en el diseno de esta aplicacion)."""
    if uploaded_file is None:
        return None
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet = next((s for s in xls.sheet_names if s.strip().lower() == "parametria"), None)
        if sheet is None:
            st.sidebar.warning("No se encontro la hoja 'Parametria' en el archivo subido.")
            return None
        df = pd.read_excel(xls, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        if "Empresa" not in df.columns or "BBG" not in df.columns:
            st.sidebar.warning("La hoja 'Parametria' no tiene las columnas esperadas ('Empresa', 'BBG').")
            return None
        instruments = []
        index_keywords = ("index",)
        for _, row in df.dropna(subset=["Empresa", "BBG"]).iterrows():
            empresa, bbg = str(row["Empresa"]).strip(), str(row["BBG"]).strip()
            if not empresa or empresa.lower() == "nan":
                continue
            if bbg.lower().endswith(index_keywords):
                continue  # los indices se tratan aparte (PERU_REGIONAL_BENCHMARKS)
            guess = bbg.split(" ")[0]
            bbg_u = f" {bbg.upper()} "
            if " US " in bbg_u:
                candidates = [guess]
            elif " LN " in bbg_u:
                candidates = [f"{guess}.L", guess]
            elif " CN " in bbg_u:
                candidates = [guess, f"{guess}.TO"]
            else:
                candidates = [f"{guess}.LM", guess]  # default: supone listado local BVL (Lima)
            instruments.append({"empresa": empresa, "bbg": bbg, "yahoo_candidates": candidates,
                                 "sector": "(desde ZODA.xlsx subido)", "listing": "detectado dinamicamente"})
        return instruments or None
    except Exception as exc:  # noqa: BLE001
        st.sidebar.warning(f"No se pudo leer el ZODA.xlsx subido: {exc}")
        return None


# ------------------------------------------------------------------------------
# 6.2 FFMM LOADERS: Portafolio_FFMM.xlsx (nombres + categorias) no trae
#     tickers, asi que se separan dos actualizaciones opcionales:
#     a) refrescar categorias (Mercado/Cat/SubCat/SubCat2) re-subiendo el xlsx
#     b) corregir/completar el mapeo Nombre -> Ticker Yahoo con un archivo
#        propio de 2 columnas (mas practico que intentar adivinar tickers)
# ------------------------------------------------------------------------------

def load_ffmm_categories(uploaded_file) -> Optional[list]:
    """Lee dinamicamente la hoja 'FFMM' (o la primera hoja disponible) de un
    Portafolio_FFMM.xlsx subido por el usuario. El archivo puede traer mas de
    un bloque de tabla separado por filas en blanco y con el encabezado
    repetido (como el archivo original); ambos casos se filtran."""
    if uploaded_file is None:
        return None
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet = next((s for s in xls.sheet_names if s.strip().lower() == "ffmm"), xls.sheet_names[0])
        df = pd.read_excel(xls, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        required = {"Nombre", "Mercado", "Cat", "SubCat"}
        if not required.issubset(set(df.columns)):
            st.sidebar.warning(f"'{sheet}' no tiene las columnas esperadas (Nombre, Mercado, Cat, SubCat, [Sub Cat2]).")
            return None
        subcat2_col = "Sub Cat2" if "Sub Cat2" in df.columns else None
        rows = []
        for _, row in df.dropna(subset=["Nombre"]).iterrows():
            nombre = str(row["Nombre"]).strip()
            if not nombre or nombre.lower() == "nan" or nombre == "Nombre":
                continue  # fila en blanco o encabezado repetido
            rows.append({
                "nombre": nombre,
                "mercado": str(row.get("Mercado", "")).strip() if pd.notna(row.get("Mercado")) else "",
                "cat": str(row.get("Cat", "")).strip() if pd.notna(row.get("Cat")) else "",
                "subcat": str(row.get("SubCat", "")).strip() if pd.notna(row.get("SubCat")) else "",
                "subcat2": (str(row.get(subcat2_col, "")).strip()
                            if subcat2_col and pd.notna(row.get(subcat2_col)) else None),
            })
        return rows or None
    except Exception as exc:  # noqa: BLE001
        st.sidebar.warning(f"No se pudo leer el Portafolio_FFMM.xlsx subido: {exc}")
        return None


def load_ffmm_ticker_overrides(uploaded_file) -> Optional[dict]:
    """Lee un archivo propio (xlsx o csv) de 2 columnas para corregir o
    completar el mapeo Nombre->Ticker. Acepta nombres de columna flexibles:
    'Nombre'/'Name' y 'Ticker'/'Yahoo'/'Ticker Yahoo'."""
    if uploaded_file is None:
        return None
    try:
        fname = getattr(uploaded_file, "name", None) or (uploaded_file if isinstance(uploaded_file, str) else "")
        if str(fname).lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        name_col = next((c for c in df.columns if c.lower() in ("nombre", "name")), None)
        ticker_col = next((c for c in df.columns if "ticker" in c.lower() or c.lower() == "yahoo"), None)
        if name_col is None or ticker_col is None:
            st.sidebar.warning("El mapeo de tickers debe tener columnas 'Nombre' y 'Ticker'.")
            return None
        overrides = {}
        for _, row in df.dropna(subset=[name_col, ticker_col]).iterrows():
            name, ticker = str(row[name_col]).strip(), str(row[ticker_col]).strip()
            if name and ticker and name.lower() != "nan" and ticker.lower() != "nan":
                overrides[name] = ticker
        return overrides or None
    except Exception as exc:  # noqa: BLE001
        st.sidebar.warning(f"No se pudo leer el mapeo de tickers subido: {exc}")
        return None


def build_ffmm_universe(categories_override: Optional[list], ticker_overrides: Optional[dict]) -> list:
    """Combina el universo FFMM por defecto con las actualizaciones opcionales
    subidas por el usuario (categorias y/o mapeo de tickers)."""
    base = {item["nombre"]: dict(item) for item in FFMM_PORTFOLIO_DEFAULT}

    if categories_override:
        for item in categories_override:
            name = item["nombre"]
            if name in base:
                base[name].update({k: v for k, v in item.items() if k != "nombre"})
            else:
                base[name] = {**item, "yahoo_candidates": [], "confianza": "no_disponible",
                               "nota": "Fondo nuevo detectado en el xlsx subido; agregar su ticker via mapeo manual."}

    if ticker_overrides:
        for raw_name, ticker in ticker_overrides.items():
            match = next((n for n in base if n.strip().lower() == raw_name.strip().lower()), None)
            if match:
                existing = [c for c in base[match].get("yahoo_candidates", []) if c != ticker]
                base[match]["yahoo_candidates"] = [ticker] + existing
                base[match]["confianza"] = "manual (definido por el usuario)"
                base[match]["nota"] = "Ticker definido manualmente por el usuario."
            else:
                base[raw_name] = {"nombre": raw_name, "mercado": "(definido por el usuario)",
                                   "cat": "(definido por el usuario)", "subcat": "", "subcat2": None,
                                   "yahoo_candidates": [ticker], "confianza": "manual (definido por el usuario)",
                                   "nota": "Fondo agregado via mapeo manual de tickers."}

    return list(base.values())


# ==============================================================================
# 7. TAB RENDERERS
# ==============================================================================

def render_commodities_tab():
    st.subheader("Commodities internacionales")
    st.caption("Futuros continuos (front-month) via Yahoo Finance. Relevancia para Peru indicada por metal.")

    results = {name: fetch_yf(meta["ticker"], label=name) for name, meta in COMMODITIES.items()}

    ok_series = {name: r.series for name, r in results.items() if r.ok}
    if ok_series:
        st.plotly_chart(plot_multi(ok_series, "Desempeno normalizado (base 100)"), use_container_width=True)

    metric_items = []
    for name, r in results.items():
        if r.ok:
            chg = pct_change_over(r.series, 21)
            metric_items.append((name, f"{r.series.iloc[-1]:,.2f}", f"{chg:+.1f}% (1M)" if chg is not None else None))
        else:
            metric_items.append((name, "N/D", None))
    for i in range(0, len(metric_items), 3):
        metric_row(metric_items[i:i + 3])

    st.markdown("---")
    st.markdown("##### Lectura de Portfolio Manager, por commodity")
    for name, meta in COMMODITIES.items():
        r = results[name]
        if not r.ok:
            st.warning(f"**{name}**: {source_caption(r)}")
            continue
        with st.expander(f"{name} ({meta['unit']})", expanded=(meta["peru_relevance"] in ("alta", "muy alta"))):
            st.plotly_chart(plot_line(r.series, name, meta["unit"], ma_windows=(50, 200)), use_container_width=True)
            st.info(interpret_commodity_with_context(name, r.series, meta["peru_relevance"]))
            st.caption(source_caption(r))

    gold = results.get("Gold")
    copper = results.get("Copper")
    if gold and copper and gold.ok and copper.ok:
        ratio = (gold.series / copper.series).dropna()
        if len(ratio) > 60:
            st.markdown("##### Ratio Oro/Cobre (proxy de apetito por riesgo macro)")
            st.plotly_chart(plot_line(ratio, "Oro/Cobre", ""), use_container_width=True)
            chg = pct_change_over(ratio, 63)
            if chg is not None:
                direction = "subiendo" if chg > 0 else "bajando"
                st.caption(f"El ratio viene {direction} {abs(chg):.1f}% en 3 meses: una suba suele asociarse a mayor "
                           f"aversion al riesgo / expectativas de desaceleracion global, y una baja a mayor apetito "
                           f"por crecimiento ciclico (positivo para economias de base minera como Peru).")


def render_peru_tab(peru_instruments: list):
    st.subheader("Mercado de capitales peruano")
    st.caption("Universo identificado a partir de ZODA.xlsx (hoja Parametria). "
               "Instrumentos ADR/listados internacionalmente tienen datos confiables; "
               "los listados unicamente en BVL dependen de cobertura limitada en fuentes gratuitas (ver notas).")

    fx_res = fetch_yf(PERU_FX["ticker"], label=PERU_FX["nombre"])
    c1, c2 = st.columns([2, 1])
    with c1:
        if fx_res.ok:
            st.plotly_chart(plot_line(fx_res.series, "USD/PEN", "PEN por USD", ma_windows=(50, 200)),
                             use_container_width=True)
        else:
            st.warning(source_caption(fx_res))
    with c2:
        if fx_res.ok:
            st.info(interpret_fx("USD/PEN", fx_res.series, is_usd_base=True))
        st.caption(source_caption(fx_res))

    st.markdown("##### Contexto macro de Peru (fuentes gratuitas, frecuencia anual)")
    macro_cols = st.columns(len(PERU_MACRO_FRED))
    for col, (label, series_id) in zip(macro_cols, PERU_MACRO_FRED.items()):
        r = fetch_fred(series_id, label=label, expected_gap_days=420)
        with col:
            if r.ok:
                col.metric(label, f"{r.series.iloc[-1]:.1f}%", None)
                col.caption(source_caption(r))
            else:
                col.warning(f"{label}: no disponible")

    st.markdown("---")
    st.markdown("##### Equities peruanas (ZODA universe)")
    rows = []
    ok_equity_series = {}
    for inst in peru_instruments:
        r = fetch_with_candidates(inst["yahoo_candidates"], label=inst["empresa"])
        chg_1m = pct_change_over(r.series, 21) if r.ok else None
        chg_ytd = None
        if r.ok:
            this_year = r.series[r.series.index.year == r.series.index.max().year]
            if len(this_year) > 1:
                chg_ytd = (this_year.iloc[-1] / this_year.iloc[0] - 1.0) * 100.0
        rows.append({
            "Empresa": inst["empresa"], "BBG": inst["bbg"], "Sector": inst.get("sector", ""),
            "Listing": inst.get("listing", ""),
            "Ultimo precio": f"{r.series.iloc[-1]:,.2f}" if r.ok else "N/D",
            "Var. 1M": f"{chg_1m:+.1f}%" if chg_1m is not None else "N/D",
            "Var. YTD": f"{chg_ytd:+.1f}%" if chg_ytd is not None else "N/D",
            "Estado dato": freshness_badge(r),
        })
        if r.ok:
            ok_equity_series[inst["empresa"]] = r.series

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    n_ok = len(ok_equity_series)
    st.caption(f"{n_ok} de {len(peru_instruments)} instrumentos con datos disponibles via Yahoo Finance en este momento. "
               "Los que muestran 'N/D' corresponden, en su mayoria, a acciones listadas unicamente en BVL sin cobertura "
               "gratuita confiable (limitacion documentada al inicio del archivo).")

    if ok_equity_series:
        top_names = list(ok_equity_series.keys())[:6]
        st.plotly_chart(plot_multi({k: ok_equity_series[k] for k in top_names}, "Desempeno normalizado (base 100)"),
                         use_container_width=True)

    st.markdown("---")
    st.markdown("##### Benchmarks regionales (proxies donde aplica)")
    bench_series = {}
    for b in PERU_REGIONAL_BENCHMARKS:
        r = fetch_with_candidates(b["yahoo_candidates"], label=b["nombre"])
        if r.ok:
            bench_series[b["nombre"]] = r.series
        cols = st.columns([3, 1, 2])
        cols[0].write(f"**{b['nombre']}**")
        cols[1].write(freshness_badge(r))
        if b["nota"]:
            cols[2].caption(b["nota"])
    if bench_series:
        st.plotly_chart(plot_multi(bench_series, "Indices/ETFs regionales (base 100)"), use_container_width=True)

    st.markdown("---")
    st.markdown("##### Pares mineros internacionales (comparables de Peru)")
    peer_series = {}
    for p in PERU_MINING_PEERS:
        r = fetch_with_candidates(p["yahoo_candidates"], label=p["nombre"])
        if r.ok:
            peer_series[p["nombre"]] = r.series
    bvn_res = ok_equity_series.get("BVN")
    if bvn_res is not None:
        peer_series["BVN (Buenaventura)"] = bvn_res
    if peer_series:
        st.plotly_chart(plot_multi(peer_series, "Mineras: Peru vs. pares internacionales (base 100)"),
                         use_container_width=True)
        st.caption("Comparar BVN contra Hochschild, Southern Copper y Hudbay ayuda a distinguir si un movimiento en "
                   "la minera peruana responde a un factor sectorial global (commodity, risk-on/off) o a un factor "
                   "idiosincratico local.")


def render_usa_tab():
    st.subheader("Estados Unidos: economia real, mercado laboral, inflacion, Fed y fiscal")

    st.markdown("##### Mercado laboral")
    unrate = fetch_fred(USA_LABOR["Tasa de desempleo (%)"], "Tasa de desempleo (%)", expected_gap_days=55)
    payrolls = fetch_fred(USA_LABOR["Nonfarm Payrolls (miles, nivel)"], "Nonfarm Payrolls", expected_gap_days=55)
    claims = fetch_fred(USA_LABOR["Solicitudes iniciales de desempleo"], "Initial Claims", expected_gap_days=14)
    participation = fetch_fred(USA_LABOR["Tasa de participacion laboral (%)"], "Tasa de participacion (%)", expected_gap_days=55)

    c1, c2 = st.columns(2)
    with c1:
        if unrate.ok:
            st.plotly_chart(plot_line(unrate.series.iloc[-120:], "Tasa de desempleo (%)"), use_container_width=True)
        else:
            st.warning(source_caption(unrate))
    with c2:
        if claims.ok:
            st.plotly_chart(plot_line(claims.series.iloc[-260:], "Solicitudes iniciales de desempleo"), use_container_width=True)
        else:
            st.warning(source_caption(claims))

    st.info(interpret_labor_market(
        unrate.series if unrate.ok else None,
        payrolls.series if payrolls.ok else None,
        claims.series if claims.ok else None,
    ))
    if participation.ok:
        st.caption(f"Tasa de participacion laboral mas reciente: {participation.series.iloc[-1]:.1f}% "
                   f"({source_caption(participation)}).")

    st.markdown("---")
    st.markdown("##### Inflacion")
    cpi = fetch_fred(USA_INFLATION["CPI headline (indice)"], "CPI headline", expected_gap_days=55)
    core_cpi = fetch_fred(USA_INFLATION["CPI core (indice)"], "CPI core", expected_gap_days=55)
    breakeven = fetch_fred(USA_INFLATION["Breakeven inflacionario 5Y (%)"], "Breakeven 5Y", expected_gap_days=10)

    if cpi.ok:
        yoy_series = resample_monthly(cpi.series).pct_change(12).dropna() * 100.0
        st.plotly_chart(plot_line(yoy_series.iloc[-84:], "CPI headline YoY (%)"), use_container_width=True)
    st.info(interpret_inflation(cpi.series if cpi.ok else None, core_cpi.series if core_cpi.ok else None,
                                 breakeven.series if breakeven.ok else None))

    st.markdown("---")
    st.markdown("##### Politica de la Fed y balance")
    fed_funds = fetch_fred(USA_FED_POLICY["Fed Funds Rate (%)"], "Fed Funds Rate (%)", expected_gap_days=55)
    balance = fetch_fred(USA_FED_POLICY["Balance de la Fed (USD mill)"], "Balance de la Fed", expected_gap_days=14)
    c1, c2 = st.columns(2)
    with c1:
        if fed_funds.ok:
            st.plotly_chart(plot_line(fed_funds.series.iloc[-260:], "Fed Funds Rate (%)"), use_container_width=True)
    with c2:
        if balance.ok:
            st.plotly_chart(plot_line(balance.series.iloc[-260:], "Balance de la Fed (USD mill)"), use_container_width=True)
    st.info(interpret_fed_policy(fed_funds.series if fed_funds.ok else None, balance.series if balance.ok else None))

    st.markdown("---")
    st.markdown("##### Curva de rendimientos del Tesoro")
    y2 = fetch_fred(USA_RATES["UST 2 anos (%)"], "UST 2Y", expected_gap_days=10)
    y10 = fetch_fred(USA_RATES["UST 10 anos (%)"], "UST 10Y", expected_gap_days=10)
    y30 = fetch_fred(USA_RATES["UST 30 anos (%)"], "UST 30Y", expected_gap_days=10)
    if y2.ok and y10.ok:
        curve_df = pd.DataFrame({"2Y": y2.series, "10Y": y10.series})
        if y30.ok:
            curve_df["30Y"] = y30.series
        curve_df = curve_df.dropna().iloc[-260:]
        fig = go.Figure()
        for col in curve_df.columns:
            fig.add_trace(go.Scatter(x=curve_df.index, y=curve_df[col], mode="lines", name=col))
        fig.update_layout(title="Rendimientos UST", height=340, template="plotly_white",
                           margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)
    st.info(interpret_yield_curve(y2.series if y2.ok else None, y10.series if y10.ok else None,
                                   y30.series if y30.ok else None))

    st.markdown("---")
    st.markdown("##### Situacion fiscal")
    debt_gdp = fetch_fred(USA_FISCAL["Deuda publica / PBI (%)"], "Deuda/PBI (%)", expected_gap_days=200)
    deficit = fetch_fred(USA_FISCAL["Resultado fiscal mensual (USD mill)"], "Resultado fiscal mensual", expected_gap_days=55)
    c1, c2 = st.columns(2)
    with c1:
        if debt_gdp.ok:
            st.plotly_chart(plot_line(debt_gdp.series, "Deuda publica / PBI (%)"), use_container_width=True)
    with c2:
        if deficit.ok:
            st.plotly_chart(plot_line(deficit.series.iloc[-120:], "Resultado fiscal mensual (USD mill)"),
                             use_container_width=True)
    st.info(interpret_fiscal(debt_gdp.series if debt_gdp.ok else None, deficit.series if deficit.ok else None))

    st.markdown("---")
    st.markdown("##### Estres financiero y volatilidad")
    nfci = fetch_fred(USA_STRESS["Chicago Fed Financial Conditions (NFCI)"], "NFCI", expected_gap_days=14)
    vix = fetch_yf(USA_VIX_TICKER, "VIX", expected_gap_days=7)
    c1, c2 = st.columns(2)
    with c1:
        if nfci.ok:
            st.plotly_chart(plot_line(nfci.series.iloc[-260:], "NFCI"), use_container_width=True)
            st.info(interpret_stress_index(nfci.series, "NFCI (Chicago Fed)"))
    with c2:
        if vix.ok:
            st.plotly_chart(plot_line(vix.series.iloc[-260:], "VIX"), use_container_width=True)
            st.info(interpret_market_series("VIX", vix.series, "macro",
                     extra_note="Niveles de VIX por debajo de 15 suelen asociarse a complacencia; por encima de 25-30, a estres agudo."))


def render_world_tab():
    st.subheader("Mapa macro global por pais")
    st.caption("CPI interanual, tasa de politica, rendimiento 10Y, crecimiento del PBI y tipo de cambio. "
               "Fuentes: FRED (series OECD/World Bank espejadas) y Yahoo Finance. Ver notas por pais.")

    scorecard_rows = []
    equity_series = {}
    fx_series = {}

    for country, cfg in WORLD_COUNTRIES.items():
        cpi_r = fetch_fred(cfg["cpi"], f"{country} CPI", expected_gap_days=55) if cfg.get("cpi") else None
        rate_r = fetch_fred(cfg["rate"], f"{country} tasa", expected_gap_days=55) if cfg.get("rate") else None
        y10_r = fetch_fred(cfg["y10"], f"{country} 10Y", expected_gap_days=55) if cfg.get("y10") else None
        gdp_r = fetch_fred(cfg["gdp"], f"{country} PBI", expected_gap_days=420) if cfg.get("gdp") else None
        fx_r = fetch_yf(cfg["fx"], f"{country} FX", expected_gap_days=7) if cfg.get("fx") else None
        eq_r = fetch_yf(cfg["equity"], f"{country} equity", expected_gap_days=7) if cfg.get("equity") else None

        cpi_val = cpi_r.series.iloc[-1] if cpi_r and cpi_r.ok else None
        rate_val = rate_r.series.iloc[-1] if rate_r and rate_r.ok else None
        y10_val = y10_r.series.iloc[-1] if y10_r and y10_r.ok else None
        gdp_val = gdp_r.series.iloc[-1] if gdp_r and gdp_r.ok else None
        fx_chg = pct_change_over(fx_r.series, 63) if fx_r and fx_r.ok else None
        eq_chg = pct_change_over(eq_r.series, 63) if eq_r and eq_r.ok else None

        if eq_r and eq_r.ok:
            equity_series[country] = eq_r.series
        if fx_r and fx_r.ok:
            fx_series[country] = fx_r.series

        scorecard_rows.append({
            "Pais": country,
            "CPI YoY %": f"{cpi_val:.1f}" if cpi_val is not None else "N/D",
            "Tasa politica %": f"{rate_val:.2f}" if rate_val is not None else "N/D",
            "Bono 10Y %": f"{y10_val:.2f}" if y10_val is not None else "N/D",
            "PBI real YoY %": f"{gdp_val:.1f}" if gdp_val is not None else "N/D",
            "FX 3M %": f"{fx_chg:+.1f}" if fx_chg is not None else "N/D",
            "Equity 3M %": f"{eq_chg:+.1f}" if eq_chg is not None else "N/D",
        })

    st.dataframe(pd.DataFrame(scorecard_rows), use_container_width=True, hide_index=True)

    if equity_series:
        st.plotly_chart(plot_multi(equity_series, "Indices bursatiles globales (base 100)"), use_container_width=True)
    if fx_series:
        st.plotly_chart(plot_multi(fx_series, "Tipos de cambio vs. USD (base 100)"), use_container_width=True)

    st.markdown("---")
    st.markdown("##### Lectura de PM, por pais")
    for country, cfg in WORLD_COUNTRIES.items():
        with st.expander(country):
            cpi_r = fetch_fred(cfg["cpi"], f"{country} CPI") if cfg.get("cpi") else None
            rate_r = fetch_fred(cfg["rate"], f"{country} tasa") if cfg.get("rate") else None
            y10_r = fetch_fred(cfg["y10"], f"{country} 10Y") if cfg.get("y10") else None
            gdp_r = fetch_fred(cfg["gdp"], f"{country} PBI") if cfg.get("gdp") else None
            fx_r = fetch_yf(cfg["fx"], f"{country} FX") if cfg.get("fx") else None

            cpi_val = cpi_r.series.iloc[-1] if cpi_r and cpi_r.ok else None
            rate_val = rate_r.series.iloc[-1] if rate_r and rate_r.ok else None
            y10_val = y10_r.series.iloc[-1] if y10_r and y10_r.ok else None
            gdp_val = gdp_r.series.iloc[-1] if gdp_r and gdp_r.ok else None
            fx_chg = pct_change_over(fx_r.series, 63) if fx_r and fx_r.ok else None

            st.write(interpret_country_scorecard(country, cpi_val, rate_val, y10_val, gdp_val, fx_chg))
            if cfg.get("nota"):
                st.caption(f"Nota de cobertura de datos: {cfg['nota']}")


def _ffmm_group_label(inst: dict) -> str:
    parts = [p for p in [inst.get("mercado"), inst.get("cat"), inst.get("subcat"), inst.get("subcat2")] if p]
    return " · ".join(parts)


def render_ffmm_tab(ffmm_instruments: list):
    st.subheader("FFMM: fondos mutuos y ETFs tematicos")
    st.caption(
        "Universo identificado a partir de Portafolio_FFMM.xlsx. El formato de las tablas de performance por "
        "periodo (codigo de color) y el tono de las lecturas esta inspirado en weekly reports institucionales "
        "tipo 'CIO Market Pulse' (DBS) y, en general, HSBC/BlackRock/Goldman Sachs: encabezado corto en negrita "
        "+ 2-3 oraciones con el mecanismo, no solo el numero."
    )

    # --- 1) Resolver precios + metricas de TODOS los fondos del universo ---
    rows = []
    resolved = {}  # nombre -> (FetchResult, metrics dict)
    for inst in ffmm_instruments:
        candidates = inst.get("yahoo_candidates") or []
        if candidates:
            r = fetch_with_candidates(candidates, label=inst["nombre"], period="5y", expected_gap_days=10)
        else:
            r = FetchResult(label=inst["nombre"], status="error", error="Sin ticker mapeado todavia", source="N/A")
        m = {}
        if r.ok:
            m = fund_metrics(r.series)
            resolved[inst["nombre"]] = (r, m)
        rows.append({
            "Nombre": inst["nombre"], "Mercado": inst.get("mercado", ""), "Cat": inst.get("cat", ""),
            "SubCat": inst.get("subcat", ""), "SubCat2": inst.get("subcat2") or "",
            "Ticker": r.resolved_ticker or "N/D", "Confianza": inst.get("confianza", ""),
            "Ultimo precio": m.get("ultimo_precio"), "Ultimo ret. %": m.get("ultimo_retorno_%"),
            "WTD %": m.get("wtd_%"), "MTD %": m.get("mtd_%"), "YTD %": m.get("ytd_%"),
            "1Y %": m.get("r1y_%"), "3Y acum %": m.get("r3y_acum_%"), "3Y CAGR %": m.get("r3y_cagr_%"),
        })
    df_all = pd.DataFrame(rows)
    n_ok, n_total = len(resolved), len(ffmm_instruments)

    c1, c2, c3 = st.columns(3)
    c1.metric("Fondos con datos", f"{n_ok} / {n_total}")
    n_estimada = sum(1 for i in ffmm_instruments if i.get("confianza") == "estimada")
    c2.metric("Tickers estimados (verificar)", n_estimada)
    c3.metric("Sin cobertura gratuita", sum(1 for i in ffmm_instruments if not i.get("yahoo_candidates")))

    st.markdown("##### Tabla de performance (estilo Market Performance)")
    styled_returns_table(
        df_all.sort_values(["Mercado", "Cat", "SubCat", "SubCat2", "Nombre"]),
        pct_cols=["Ultimo ret. %", "WTD %", "MTD %", "YTD %", "1Y %", "3Y acum %", "3Y CAGR %"],
        price_cols=["Ultimo precio"],
    )
    st.caption("WTD/MTD/YTD: retorno desde el ultimo cierre antes del inicio de la semana/mes/anio en curso. "
               "1Y/3Y: retorno desde el cierre disponible hace 1/3 anios respecto a la ultima fecha con dato. "
               "3Y CAGR: tasa anualizada compuesta del retorno acumulado a 3 anios.")

    with st.expander(f"Fondos sin cobertura gratuita en Yahoo Finance ({n_total - n_ok} sin datos) y tickers estimados"):
        for inst in ffmm_instruments:
            if inst["nombre"] in resolved and inst.get("confianza") not in ("estimada",):
                continue
            tag = "🟡 estimado" if inst.get("confianza") == "estimada" else "🔴 sin ticker"
            st.write(f"{tag} · **{inst['nombre']}** — {inst.get('nota', '') or 'sin nota adicional.'}")
        st.caption("Puedes corregir o completar cualquiera de estos subiendo un mapeo Nombre/Ticker en la barra lateral.")

    if not resolved:
        st.warning("No se pudo resolver ningun fondo con datos de Yahoo Finance en este momento.")
        return

    # --- 2) Winners / Losers WTD ---
    st.markdown("---")
    st.markdown("##### Ganadores y rezagados de la semana (WTD)")
    wtd_returns = {name: m.get("wtd_%") for name, (_, m) in resolved.items()}
    st.plotly_chart(plot_winners_losers(wtd_returns, "Top 5 / Bottom 5 WTD"), use_container_width=True)

    # --- 3) Grupos tematicos: grafico comparado + comentario tipo CIO ---
    st.markdown("---")
    st.markdown("##### Lectura por grupo tematico")
    groups = {}
    for inst in ffmm_instruments:
        if inst["nombre"] not in resolved:
            continue
        groups.setdefault(_ffmm_group_label(inst), []).append(inst["nombre"])
    groups = {g: names for g, names in groups.items() if len(names) >= 2}
    if groups:
        group_choice = st.selectbox("Selecciona un grupo tematico", sorted(groups.keys()))
        names_in_group = groups[group_choice]
        series_dict = {n: resolved[n][0].series for n in names_in_group}
        st.plotly_chart(plot_multi(series_dict, f"{group_choice} — desempeno normalizado (base 100)"),
                         use_container_width=True)
        returns_in_group = {n: resolved[n][1].get("wtd_%") for n in names_in_group}
        st.info(category_theme_commentary(group_choice, returns_in_group))
    else:
        st.caption("Aun no hay suficientes fondos resueltos en un mismo grupo para comparar (minimo 2).")

    # --- 4) Ficha de detalle por fondo + performance attribution por Top Holdings ---
    st.markdown("---")
    st.markdown("##### Ficha de detalle y performance attribution (estilo CFA)")
    selected = st.selectbox("Selecciona un fondo/ETF", sorted(resolved.keys()), key="ffmm_detail_select")
    r_sel, m_sel = resolved[selected]

    c1, c2 = st.columns([2, 1])
    with c1:
        st.plotly_chart(plot_line(r_sel.series, selected, "Precio", ma_windows=(50, 200)), use_container_width=True)
    with c2:
        metric_row([("WTD", f"{m_sel['wtd_%']:+.1f}%" if m_sel.get("wtd_%") is not None else "N/D", None),
                    ("MTD", f"{m_sel['mtd_%']:+.1f}%" if m_sel.get("mtd_%") is not None else "N/D", None)])
        metric_row([("YTD", f"{m_sel['ytd_%']:+.1f}%" if m_sel.get("ytd_%") is not None else "N/D", None),
                    ("1Y", f"{m_sel['r1y_%']:+.1f}%" if m_sel.get("r1y_%") is not None else "N/D", None)])
        metric_row([("3Y acum.", f"{m_sel['r3y_acum_%']:+.1f}%" if m_sel.get("r3y_acum_%") is not None else "N/D", None),
                    ("3Y CAGR", f"{m_sel['r3y_cagr_%']:+.1f}%" if m_sel.get("r3y_cagr_%") is not None else "N/D", None)])
        st.caption(source_caption(r_sel))

    st.info(fund_periods_summary(selected, m_sel))
    st.info(interpret_market_series(selected, r_sel.series, "equity"))

    st.markdown("###### Top Holdings y performance attribution")
    holdings_df = fetch_top_holdings(r_sel.resolved_ticker) if r_sel.resolved_ticker else None
    if holdings_df is None or holdings_df.empty:
        st.warning("Yahoo Finance no expone el modulo de Top Holdings para este instrumento (comun en fondos "
                   "mutuos offshore o en algunos ETFs de nicho). No es posible construir la atribucion por holding.")
    else:
        display_holdings = holdings_df.copy()
        display_holdings["Holding Percent"] = (display_holdings["Holding Percent"] * 100).round(2)
        st.dataframe(display_holdings.rename(columns={"Holding Percent": "Peso %"}),
                     use_container_width=True)

        period_map = {"WTD": "wtd_%", "MTD": "mtd_%", "YTD": "ytd_%", "1Y": "r1y_%"}
        period_choice = st.radio("Periodo para la atribucion", list(period_map.keys()), horizontal=True,
                                  key="ffmm_attrib_period")
        fund_period_ret = m_sel.get(period_map[period_choice])

        attrib_rows = []
        with st.spinner("Calculando retornos de los holdings..."):
            for symbol, hrow in holdings_df.iterrows():
                hres = fetch_yf(symbol, label=str(hrow["Name"]), period="2y", expected_gap_days=10)
                h_ret = period_return(hres.series, period_choice) if hres.ok else None
                weight_pct = float(hrow["Holding Percent"]) * 100.0
                contribution = (weight_pct / 100.0) * h_ret if h_ret is not None else None
                attrib_rows.append({"Symbol": symbol, "Name": hrow["Name"], "Weight_%": weight_pct,
                                     "Return_%": h_ret, "Contribution_pp": contribution})
        attrib_df = pd.DataFrame(attrib_rows).set_index("Symbol")
        attrib_df_valid = attrib_df.dropna(subset=["Contribution_pp"])

        if attrib_df_valid.empty:
            st.warning("No se pudieron calcular retornos individuales para los holdings en este periodo.")
        else:
            explained_pp = float(attrib_df_valid["Contribution_pp"].sum())
            residual_pp = (fund_period_ret - explained_pp) if fund_period_ret is not None else None
            st.plotly_chart(
                plot_attribution_bars(attrib_df_valid, residual_pp,
                                       f"Performance attribution — {selected} ({period_choice})"),
                use_container_width=True,
            )
            st.info(performance_attribution_story(selected, period_choice, fund_period_ret, attrib_df_valid, residual_pp))
            n_missing = len(attrib_df) - len(attrib_df_valid)
            if n_missing:
                st.caption(f"{n_missing} holding(s) sin retorno disponible en Yahoo Finance para este periodo "
                           f"(excluidos de la atribucion numerica, pero listados en la tabla de arriba).")

    sector_w = fetch_fund_sector_weightings(r_sel.resolved_ticker) if r_sel.resolved_ticker else None
    if sector_w:
        sw_df = pd.DataFrame({"Sector": list(sector_w.keys()),
                               "Peso %": [v * 100 for v in sector_w.values()]}).sort_values("Peso %", ascending=True)
        fig = go.Figure(go.Bar(x=sw_df["Peso %"], y=sw_df["Sector"], orientation="h", marker_color="#4472C4"))
        fig.update_layout(title=f"Ponderacion sectorial — {selected}", height=max(280, 26 * len(sw_df)),
                           template="plotly_white", margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # --- 5) Diversificacion: correlaciones + riesgo/retorno ---
    st.markdown("---")
    st.markdown("##### Diversificacion: correlaciones y riesgo/retorno")
    corr_universe = {n: resolved[n][0].series for n in resolved}
    if len(corr_universe) >= 3:
        corr_df = correlation_matrix(corr_universe)
        if not corr_df.empty:
            st.plotly_chart(plot_heatmap(corr_df, "Correlacion de retornos diarios (todo el universo resuelto)"),
                             use_container_width=True)
            st.caption("Una correlacion alta entre dos fondos del portafolio implica poca diversificacion efectiva "
                       "entre ellos, incluso si estan en categorias nominalmente distintas.")

    rr_rows = []
    for name, (res_fund, met) in resolved.items():
        if met.get("vol_1y_%") is not None and met.get("r1y_%") is not None:
            cat_lookup = next((i.get("mercado", "") for i in ffmm_instruments if i["nombre"] == name), "")
            rr_rows.append({"Nombre": name, "vol_1y_%": met["vol_1y_%"], "r1y_%": met["r1y_%"], "cat": cat_lookup})
    if len(rr_rows) >= 3:
        st.plotly_chart(plot_risk_return_scatter(pd.DataFrame(rr_rows), "Riesgo (vol. 1Y) vs. Retorno (1Y)"),
                         use_container_width=True)

    st.caption(
        "Aviso: las lecturas de esta pestana son generadas por reglas cuantitativas deterministas a partir de "
        "datos de Yahoo Finance, no son un consejo de inversion, y la atribucion por holdings es una "
        "aproximacion (pesos vigentes, no historicos). Verificar siempre contra la ficha oficial del fondo."
    )


# ==============================================================================
# 8. MAIN
# ==============================================================================

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🌐")
    st.title("🌐 " + APP_TITLE)
    st.caption("Terminal personal de research Top-Down · Market Monitoring + Macro Research + "
               "Cross-Asset Analysis + Investment Interpretation. Datos gratuitos, publicos, con cache local.")

    with st.sidebar:
        st.header("Configuracion")
        st.caption("Universo de instrumentos peruanos (ZODA.xlsx)")
        uploaded = st.file_uploader("Subir ZODA.xlsx para refrescar dinamicamente la pestana PERU (opcional)",
                                     type=["xlsx"])
        dynamic_instruments = load_zoda_parametria(uploaded)
        if dynamic_instruments:
            st.success(f"{len(dynamic_instruments)} instrumentos detectados dinamicamente en el archivo subido.")
        peru_instruments = dynamic_instruments or PERU_INSTRUMENTS_DEFAULT

        st.markdown("---")
        st.caption("Universo de fondos/ETFs tematicos (Portafolio_FFMM.xlsx)")
        ffmm_xlsx = st.file_uploader("Subir Portafolio_FFMM.xlsx para refrescar categorias (opcional)",
                                      type=["xlsx"], key="ffmm_xlsx_uploader")
        ffmm_ticker_map_file = st.file_uploader(
            "Subir mapeo de tickers Nombre/Ticker (xlsx o csv, opcional — para corregir o completar)",
            type=["xlsx", "csv"], key="ffmm_ticker_uploader")
        ffmm_categories = load_ffmm_categories(ffmm_xlsx)
        ffmm_overrides = load_ffmm_ticker_overrides(ffmm_ticker_map_file)
        if ffmm_categories:
            st.success(f"{len(ffmm_categories)} fondos detectados en el Portafolio_FFMM.xlsx subido.")
        if ffmm_overrides:
            st.success(f"{len(ffmm_overrides)} tickers actualizados manualmente.")
        ffmm_instruments = build_ffmm_universe(ffmm_categories, ffmm_overrides)

        st.markdown("---")
        if st.button("🔄 Forzar refresco de datos (limpiar cache)"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        with st.expander("Limitaciones de datos conocidas"):
            st.markdown(
                "- Varias acciones peruanas listadas solo en BVL no tienen fuente gratuita confiable; se "
                "marcan como 'N/D' en vez de inventar un precio.\n"
                "- El indice BVL puro no tiene fuente gratuita; se usa el ETF EPU como proxy.\n"
                "- COLCAP usa un ETF proxy (GXG) por baja cobertura gratuita.\n"
                "- Taiwan no tiene serie de PBI del Banco Mundial (no es miembro).\n"
                "- China tiene menor profundidad de series macro gratuitas que economias OECD.\n"
                "- En FFMM, varios fondos mutuos offshore (SICAVs, OEICs, fondos de gestoras indias) no tienen "
                "ticker gratuito en Yahoo Finance; se muestran como 'N/D' en vez de arriesgar un ticker "
                "incorrecto. Algunos tickers de ETFs menos liquidos estan marcados como 'estimados' y conviene "
                "verificarlos antes de usarlos en una decision de inversion.\n"
                "- El performance attribution por Top Holdings usa los pesos VIGENTES mas recientes de cada "
                "holding (no los pesos exactos al inicio del periodo analizado): es una aproximacion razonable "
                "del driver principal del movimiento, no una atribucion Brinson exacta con pesos diarios.\n"
                "- Las interpretaciones son generadas por reglas cuantitativas deterministas, no por un "
                "modelo de lenguaje; no deben tomarse como recomendacion de inversion."
            )
        st.caption(f"Ultima recarga de la app: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    tab_commodities, tab_peru, tab_usa, tab_world, tab_ffmm = st.tabs(
        ["🛢️ COMMODITIES", "🇵🇪 PERU", "🇺🇸 USA", "WORLD", "FFMM"]
    )

    with tab_commodities:
        render_commodities_tab()
    with tab_peru:
        render_peru_tab(peru_instruments)
    with tab_usa:
        render_usa_tab()
    with tab_world:
        render_world_tab()
    with tab_ffmm:
        render_ffmm_tab(ffmm_instruments)

    st.markdown("---")
    st.caption(
        "Aviso: esta herramienta es de uso personal/educativo para desarrollar criterio de inversion Top-Down. "
        "No constituye recomendacion de inversion. Verificar siempre cifras criticas contra la fuente oficial "
        "antes de tomar decisiones de portafolio."
    )


if __name__ == "__main__":
    main()
