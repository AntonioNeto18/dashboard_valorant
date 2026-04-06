import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Analise torneio de valorant", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("overview.csv")

    mapeamento_colunas = {
        "Tournament": "tournament",
        "Stage": "stage",
        "Match Type": "match_type",
        "Match Name": "match_name",
        "Map": "map",
        "Player": "player",
        "Team": "team",
        "Agents": "agent",
        "Rating": "rating",
        "Average Combat Score": "acs",
        "Kills": "kills",
        "Deaths": "deaths",
        "Assists": "assists",
        "Kills - Deaths (KD)": "kd_diff",
        "Kill, Assist, Trade, Survive %": "kast",
        "Average Damage Per Round": "adr",
        "Headshot %": "hs_pct",
        "First Kills": "first_kills",
        "First Deaths": "first_deaths",
        "Kills - Deaths (FKD)": "fkd_diff",
        "Side": "side"
    }
    
    df = df.rename(columns=mapeamento_colunas)
    df = df[df["map"] != "All Maps"]
    
    # Limpeza de dados (removendo % e convertendo para float)
    for col in ['kast', 'hs_pct']:
        if col in df.columns:
            # Garante que tratamos como string antes de substituir o %
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')
            
    # Preencher NAs em colunas numéricas para não quebrar cálculos
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    return df

df = load_data()

lista_torneios = sorted(df["tournament"].unique())
torneio_default = "Valorant Champions 2025"

# Sidebar
st.sidebar.title("Filtro")
torneio_sel = st.sidebar.selectbox(
    label="Filtrar por Torneio",
    options=lista_torneios,
    index=list(lista_torneios).index(torneio_default)
)

df_torneio = df[df["tournament"] == torneio_sel]

lista_mapas = sorted(df_torneio["map"].unique())
mapas_sel = st.sidebar.multiselect(
    label="Filtrar por Mapas",
    options=lista_mapas,
    placeholder="Todos os mapas"
)

lista_times = sorted(df_torneio["team"].unique())
times_sel = st.sidebar.multiselect(
    label="Filtrar por Times",
    options=lista_times,
    placeholder="Todos os times"
)

df_final = df_torneio.copy()

if mapas_sel:
    df_final = df_final[df_final["map"].isin(mapas_sel)]
if times_sel:
    df_final = df_final[df_final["team"].isin(times_sel)]

st.title(f"Visão geral do {torneio_sel}")

# Métricas
df_stats = df_final[df_final["side"] == "both"]
col1, col2, col3, col4 = st.columns(4)

# MVP do Torneio
ranking_mvp = df_stats.groupby("player")["rating"].mean()
    
mvp_nome = ranking_mvp.idxmax().title()
mvp_score = ranking_mvp.max()

col1.metric(
    label="MVP do Torneio",
    value=mvp_nome,
    delta=f"{mvp_score:.2f} rating"
)

# Agente Popular
ranking_agente = df_stats["agent"].value_counts()

agente_nome = ranking_agente.idxmax().title()
agente_count = ranking_agente.max()

col2.metric(
    label="Agente Popular",
    value=agente_nome,
    delta=f"{agente_count} picks"
)

# Quantidade de Jogadores no Torneio
col3.metric(
    label="Jogadores",
    value=df_stats["player"].nunique()
)

# Quantidade de Times no Torneio
col4.metric(
    label="Times",
    value=df_stats["team"].nunique()
)

col1, col2 = st.columns(2)

# Gráfico top 10 players
top10_players = df_stats.groupby(["player", "team"])["rating"].mean().sort_values(ascending=False).head(10).reset_index()
top10_players["player"] = top10_players["player"].str.title()

fig_top_players = px.bar(
    top10_players,
    x="rating",               
    y="player",               
    color="team",             
    orientation='h',          
    text="rating",           
    title="Top 10 Jogadores por Rating Médio",
    labels={"rating": "Rating Médio", "player": "Jogador", "team": "Time"},
    color_discrete_sequence=px.colors.qualitative.Prism
)

fig_top_players.update_layout(
    yaxis={'categoryorder':'total ascending'},
    showlegend=True
)

fig_top_players.update_traces(texttemplate='%{text:.2f}', textposition='outside')

col1.plotly_chart(fig_top_players, use_container_width=True)

# Gráfico top 10 picks
top10_agentes = df_stats["agent"].value_counts().head(10).reset_index()
top10_agentes.columns = ["agent", "picks"]
top10_agentes["agent"] = top10_agentes["agent"].str.title()

fig_picks = px.bar(
    top10_agentes,
    x="picks",               
    y="agent",               
    color="picks",          
    orientation='h',          
    text="picks",           
    title="Top 10 Agentes mais Pickados",
    labels={"picks": "Total de Escolhas", "agent": "Agente"},
    color_continuous_scale="Reds"
)

fig_picks.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
col2.plotly_chart(fig_picks, use_container_width=True)