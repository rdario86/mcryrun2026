import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# Configuración de página
st.set_page_config(page_title="Dashboard Maracay Run 2026", page_icon="🏅", layout="wide")

st.title("🏅 Análisis de Resultados: Maracay Run 2026 (10K)")
st.markdown("Visualización y estadísticas basadas **exclusivamente en el Tiempo Chip**.")

# 1. Función para cargar y limpiar los datos
@st.cache_data
def cargar_datos():
    # Leer el nuevo archivo generado
    df = pd.read_excel('Maracay_Run_2026_Completa_2.xlsx')
    
    # Descartar la columna T. PISTOLA si existe para no usarla en ningún cálculo
    if 'T. PISTOLA' in df.columns:
        df = df.drop(columns=['T. PISTOLA'])
        
    # Convertir T. CHIP a formato de tiempo timedelta para hacer cálculos
    # (Asume formato HH:MM:SS)
    df['Segundos_Chip'] = pd.to_timedelta(df['T. CHIP']).dt.total_seconds()
    
    # Eliminar corredores sin tiempo de chip válido (por si hay DNF o datos vacíos)
    df = df.dropna(subset=['Segundos_Chip'])
    
    # --- REORDENAMIENTO BASADO EN T. CHIP ---
    # Ordenar todo el DataFrame por el menor tiempo (el ganador real por chip)
    df = df.sort_values(by='Segundos_Chip').reset_index(drop=True)
    
    # Recalcular P. GEN (Posición General) según el nuevo orden
    df['P. GEN'] = df.index + 1
    
    # Recalcular P. CAT. (Posición por Categoría)
    # Rango dentro de su categoría y género
    df['Rank_Cat'] = df.groupby(['CAT.', 'GENERO'])['Segundos_Chip'].rank(method='first').astype(int)
    # Total de corredores en esa categoría
    df['Total_Cat'] = df.groupby(['CAT.', 'GENERO'])['CAT.'].transform('count')
    # Armar el string de posición, ej: "1 DE 64"
    df['P. CAT.'] = df['Rank_Cat'].astype(str) + " DE " + df['Total_Cat'].astype(str)
    
    # Limpiar columnas auxiliares para la tabla de visualización
    df = df.drop(columns=['Rank_Cat', 'Total_Cat'])
    
    return df

df_original = cargar_datos()

# 2. Panel de Filtros y Búsqueda (Sidebar)
st.sidebar.header("Filtros y Búsqueda")

# Barra de búsqueda unificada
termino_busqueda = st.sidebar.text_input("🔍 Buscar (C.I., N# o Nombre):", "")

# Filtros desplegables
generos = st.sidebar.multiselect("Filtrar por Género:", options=df_original['GENERO'].dropna().unique())
categorias = st.sidebar.multiselect("Filtrar por Categoría:", options=df_original['CAT.'].dropna().unique())

# 3. Aplicar Filtros Dinámicos
df_filtrado = df_original.copy()

if termino_busqueda:
    mask = (
        df_filtrado['C.I.'].astype(str).str.contains(termino_busqueda, case=False, na=False) |
        df_filtrado['N#'].astype(str).str.contains(termino_busqueda, case=False, na=False) |
        df_filtrado['APELLIDO & NOMBRE'].astype(str).str.contains(termino_busqueda, case=False, na=False)
    )
    df_filtrado = df_filtrado[mask]

if generos:
    df_filtrado = df_filtrado[df_filtrado['GENERO'].isin(generos)]

if categorias:
    df_filtrado = df_filtrado[df_filtrado['CAT.'].isin(categorias)]

# 4. Tarjetas de Estadísticas Principales
st.markdown("### 📊 Estadísticas del Grupo")
if not df_filtrado.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    total_corredores = len(df_filtrado)
    tiempo_promedio_sec = df_filtrado['Segundos_Chip'].mean()
    mejor_tiempo_sec = df_filtrado['Segundos_Chip'].min()
    
    # Formatear los segundos de vuelta a texto HH:MM:SS
    promedio_str = str(datetime.timedelta(seconds=int(tiempo_promedio_sec)))
    mejor_str = str(datetime.timedelta(seconds=int(mejor_tiempo_sec)))
    
    col1.metric("Corredores Finisher", total_corredores)
    col2.metric("Mejor Tiempo (Chip)", mejor_str)
    col3.metric("Tiempo Promedio", promedio_str)
    
    # Calcular el ritmo promedio general (Pace) asumiendo la distancia de 10K
    pace_promedio_sec = tiempo_promedio_sec / 10
    pace_str = f"{int(pace_promedio_sec // 60)}:{int(pace_promedio_sec % 60):02d} min/km"
    col4.metric("Ritmo Promedio", pace_str)

    st.divider()

    # 5. Visualizaciones (Gráficos interactivos)
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        # Histograma de distribución de tiempos
        df_filtrado['Minutos_Chip'] = df_filtrado['Segundos_Chip'] / 60
        fig_hist = px.histogram(
            df_filtrado, 
            x="Minutos_Chip", 
            nbins=20, 
            title="Distribución de Tiempos (Minutos)",
            labels={"Minutos_Chip": "Tiempo en Minutos"},
            color_discrete_sequence=['#00CC96']
        )
        fig_hist.update_layout(yaxis_title="Cantidad de Corredores")
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_graf2:
        # Gráfico de barras de participación por categoría
        participacion = df_filtrado['CAT.'].value_counts().reset_index()
        participacion.columns = ['Categoría', 'Participantes']
        fig_bar = px.bar(
            participacion, 
            x='Participantes', 
            y='Categoría', 
            orientation='h', 
            title="Participación por Categoría",
            color='Participantes',
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

    # 6. Tabla Final Reordenada
    st.markdown("### 📋 Clasificación Oficial (Por T. Chip)")
    # Ocultamos las columnas auxiliares de cálculo para que la tabla se vea impecable
    columnas_mostrar = [col for col in df_filtrado.columns if col not in ['Segundos_Chip', 'Minutos_Chip']]
    st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True, hide_index=True)

else:
    st.warning("No se encontraron resultados que coincidan con tu búsqueda o filtros.")