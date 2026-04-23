import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Analise torneio de valorant 2022", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("overview.csv")

    mapeamento_colunas = {
        "Tournament": "tournament", "Stage": "stage", "Match Type": "match_type",
        "Match Name": "match_name", "Map": "map", "Player": "player", "Team": "team",
        "Agents": "agent", "Rating": "rating", "Average Combat Score": "acs",
        "Kills": "kills", "Deaths": "deaths", "Assists": "assists",
        "Kills - Deaths (KD)": "kd", "Kill, Assist, Trade, Survive %": "kast",
        "Average Damage Per Round": "adr", "Headshot %": "hs",
        "First Kills": "first_kills", "First Deaths": "first_deaths",
        "Kills - Deaths (FKD)": "fkd_diff", "Side": "side"
    }
    
    df = df.rename(columns=mapeamento_colunas)
    df = df[df["map"] != "All Maps"]
    
    # Limpeza de dados
    for col in ['kast', 'hs']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')
            
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    return df

def get_top_stat(df, group_col, stat_col):
    """Calcula e retorna o nome e valor máximo focado na média de um atributo"""
    stat_series = df.groupby(group_col)[stat_col].mean()
    nome = stat_series.idxmax()
    if isinstance(nome, str):
        nome = nome.title()
    return nome, stat_series.max()

def render_top_metric(col, label, df, group_col, stat_col, delta_suffix=""):
    """Renderiza um card de métrica padrão"""
    nome, score = get_top_stat(df, group_col, stat_col)
    col.metric(label=label, value=nome, delta=f"{score:.2f} {delta_suffix}".strip())

def get_normalized_radar_df(df_agg, group_col):
    """Retorna o DataFrame normalizado de 0 a 100 para o radar chart"""
    df_rad = df_agg.copy()
    cols = df_rad.drop(columns=[group_col]).columns
    for col in cols:
        max_val, min_val = df_rad[col].max(), df_rad[col].min()
        if max_val != min_val:
            df_rad[col] = (df_rad[col] - min_val) / (max_val - min_val) * 100
        else:
            df_rad[col] = 100
    return df_rad, cols

def plot_radar(df_radar, cols_radar, group_col, items, color_map):
    """Plota um radar chart comparativo generalizado"""
    fig = go.Figure()
    for item in items:
        df_item = df_radar[df_radar[group_col] == item]
        if not df_item.empty:
            fig.add_trace(go.Scatterpolar(
                r=df_item[cols_radar].iloc[0].values,
                theta=cols_radar,
                fill='toself',
                name=item,
                line=dict(color=color_map.get(item, 'white'))
            ))
            
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, showticklabels=True, range=[0, 100])
        ),
        margin=dict(l=40, r=40, t=20, b=20),
        showlegend=True
    )
    return fig

def plot_boxplot(df, filter_col, filter_items, y_col, title, color_map):
    """Plota um boxplot comparativo generalizado"""
    df_filtered = df[df[filter_col].isin(filter_items)]
    fig = px.box(
        df_filtered,
        x=filter_col, y=y_col, color=filter_col,
        title=title,
        color_discrete_map=color_map
    )
    fig.update_layout(showlegend=False)
    return fig


# =========================================================
# CARREGAMENTO DE DADOS E FILTROS DIRETOS
# =========================================================
df = load_data()

lista_torneios = sorted(df["tournament"].unique())
torneio_default = "Valorant Champions 2022"

# Sidebar
st.sidebar.title("Filtro")
torneio_sel = st.sidebar.selectbox(
    "Filtrar por Torneio", 
    lista_torneios, 
    index=list(lista_torneios).index(torneio_default)
)

df_torneio = df[df["tournament"] == torneio_sel]

lista_mapas = sorted(df_torneio["map"].unique())
mapas_sel = st.sidebar.multiselect("Filtrar por Mapas", lista_mapas, placeholder="Todos os mapas")

df_final = df_torneio.copy()
if mapas_sel:
    df_final = df_final[df_final["map"].isin(mapas_sel)]

df_stats = df_final[df_final["side"] == "both"].copy()

tab1, tab2, tab3 = st.tabs(["Visão Geral", "Análise por time", "Análise por jogador"])

if df_stats.empty or "rating" not in df_stats.columns or not (df_stats["rating"] != 0).any():
    st.error("Dados inexistentes para os filtros utilizados.")
    st.stop()

# ================= TAB 1: VISÃO GERAL =================
with tab1:
    st.title(f"Visão geral do {torneio_sel}")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    render_top_metric(c1, "MVP do Torneio (KD)", df_stats, "player", "kd", "KD médio")
    render_top_metric(c2, "MVP do Torneio (Rating)", df_stats, "player", "rating", "Rating médio")
    render_top_metric(c3, "Jogador com mais precisão", df_stats, "player", "hs", "%")

    ranking_agente = df_stats["agent"].value_counts()
    c4.metric("Agente Popular", ranking_agente.idxmax().title(), f"{ranking_agente.max()} picks")
    c5.metric("Jogadores", df_stats["player"].nunique())
    c6.metric("Times", df_stats["team"].nunique())

    c1, c2 = st.columns(2)

    top10_players = df_stats.groupby(["player", "team"])["rating"].mean().sort_values(ascending=False).head(10).reset_index()
    top10_players["player"] = top10_players["player"].str.title()
    fig_top_players = px.bar(
        top10_players, x="rating", y="player", color="team", orientation='h', text="rating",
        title="Top 10 Jogadores por Rating Médio",
        labels={"rating": "Rating Médio", "player": "Jogador", "team": "Time"},
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_top_players.update_layout(yaxis={'categoryorder':'total ascending'})
    fig_top_players.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    c1.plotly_chart(fig_top_players, use_container_width=True)

    top10_agentes = df_stats["agent"].value_counts().head(10).reset_index()
    top10_agentes.columns = ["agent", "picks"]
    top10_agentes["agent"] = top10_agentes["agent"].str.title()
    
    fig_picks = px.bar(
        top10_agentes, x="picks", y="agent", color="picks", orientation='h', text="picks",
        title="Top 10 Agentes mais Pickados", labels={"picks": "Total de Escolhas", "agent": "Agente"},
        color_continuous_scale="Reds"
    )
    fig_picks.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    c2.plotly_chart(fig_picks, use_container_width=True)

# ================= TAB 2: ANÁLISE POR TIME =================
with tab2:
    st.title("Análise por Time")
    
    df_stats_time = df_stats.groupby("team").agg({
        "rating": "mean", "kills": "mean", "deaths": "mean", "assists": "mean",
        "kd": "mean", "hs": "mean", "adr": "mean"
    }).reset_index().sort_values(by="rating", ascending=False)
    
    df_radar_team, cols_radar_team = get_normalized_radar_df(df_stats_time, "team")

    c1, c2, c3, c4 = st.columns(4)
    render_top_metric(c1, "Time com maior KD médio", df_stats, "team", "kd", "KD médio")
    render_top_metric(c2, "Time com maior rating médio", df_stats, "team", "rating", "rating médio")
    render_top_metric(c3, "Time com maior precisão média", df_stats, "team", "hs", "%")
    render_top_metric(c4, "Time com maior dano médio por round", df_stats, "team", "adr", "Dano")

    st.divider()
    st.subheader("Estatísticas por time")

    team_filter = st.selectbox("Selecione um time", df_stats_time["team"], index=0)
    
    c1, c2 = st.columns(2)
    fig_radar_single = plot_radar(df_radar_team, cols_radar_team, "team", [team_filter], {team_filter: 'green'})
    fig_radar_single.update_layout(title="Estatísticas do time")
    c1.plotly_chart(fig_radar_single, use_container_width=True)

    df_players = df_stats[df_stats["team"] == team_filter][["player", "kills"]].sort_values(by="kills", ascending=False)
    df_players["player"] = df_players["player"].str.title()
    fig_players = px.bar(df_players, x="kills", y="player", orientation='h', color="player", title="Jogadores com mais abates")
    c2.plotly_chart(fig_players, use_container_width=True)

    c1, c2 = st.columns(2)
    df_maps = df_stats[df_stats["team"] == team_filter]["map"].value_counts().reset_index()
    df_maps.columns = ["map", "plays"]
    df_maps["map"] = df_maps["map"].str.title()
    
    fig_maps = px.bar(df_maps, x="plays", y="map", orientation='h', color="map", title="Mapas mais jogados")
    c1.plotly_chart(fig_maps, use_container_width=True)

    df_agents = df_stats[df_stats["team"] == team_filter]["agent"].value_counts().reset_index()
    df_agents.columns = ["agent", "picks"]
    df_agents["agent"] = df_agents["agent"].str.title()
    
    fig_agents = px.pie(df_agents, values="picks", names="agent", title="Distribuição de Picks por Agente", color_discrete_sequence=px.colors.qualitative.Prism)
    c2.plotly_chart(fig_agents, use_container_width=True)

    st.divider()
    st.subheader(f"Desempenho do time {team_filter} por mapa")

    c1, c2 = st.columns(2)
    opcoes_mapas = df_maps["map"].tolist()
    idx_second_map = 1 if len(opcoes_mapas) > 1 else 0
    
    first_map = c1.selectbox("Selecione um mapa", opcoes_mapas, index=0)
    second_map = c2.selectbox("Selecione outro mapa", opcoes_mapas, index=idx_second_map)

    df_team_all_matches = df_stats[df_stats["team"] == team_filter].copy()
    df_team_all_matches["map"] = df_team_all_matches["map"].str.title()
    
    if not df_team_all_matches.empty and len(opcoes_mapas) > 0:
        df_stats_map = df_team_all_matches.groupby("map").agg({
            "rating": "mean", "kills": "mean", "deaths": "mean", "assists": "mean",
            "kd": "mean", "hs": "mean", "adr": "mean"
        }).reset_index()

        df_radar_map, cols_radar_map = get_normalized_radar_df(df_stats_map, "map")

        c1_map, c2_map, c3_map = st.columns(3)
        
        map_colors = {first_map: 'purple', second_map: 'yellow'}
        map_items = [first_map] if first_map == second_map else [first_map, second_map]
        
        fig_radar_map = plot_radar(df_radar_map, cols_radar_map, "map", map_items, map_colors)
        c1_map.plotly_chart(fig_radar_map, use_container_width=True)

        fig_box_map_hs = plot_boxplot(df_team_all_matches, "map", map_items, "hs", "Precisão por Mapa (HS %)", map_colors)
        c2_map.plotly_chart(fig_box_map_hs, use_container_width=True)
        
        fig_box_map_kills = plot_boxplot(df_team_all_matches, "map", map_items, "kills", "Abates por Mapa", map_colors)
        c3_map.plotly_chart(fig_box_map_kills, use_container_width=True)

    st.divider()
    st.subheader("Comparação entre times")

    c1, c2 = st.columns(2)
    first_team = c1.selectbox("Escolha um time", df_stats_time["team"], index=0)
    second_team = c2.selectbox("Escolha outro time", df_stats_time["team"], index=len(df_stats_time)-2)

    c1, c2, c3 = st.columns(3)
    
    team_colors = {first_team: 'red', second_team: 'blue'}
    team_items = [first_team] if first_team == second_team else [first_team, second_team]

    fig_radar_comp = plot_radar(df_radar_team, cols_radar_team, "team", team_items, team_colors)
    c1.plotly_chart(fig_radar_comp, use_container_width=True)

    fig_box_hs = plot_boxplot(df_stats, "team", team_items, "hs", "Comparação de Precisão (HS %)", team_colors)
    c2.plotly_chart(fig_box_hs, use_container_width=True)

    fig_box_kills = plot_boxplot(df_stats, "team", team_items, "kills", "Comparação de Abates", team_colors)
    c3.plotly_chart(fig_box_kills, use_container_width=True) 

    with st.expander("Legenda do Gráfico"):
        st.markdown("""
        - **ADR (Average Damage Per Round):** Dano médio causado por round.
        - **KD_DIFF:** Saldo de Kills menos Deaths (Abates vs Mortes).
        - **hs:** Porcentagem de acertos na cabeça (Headshot).
        - **Kills / Deaths / Assists:** Média de Abates, Mortes ou Assistências feitas pelo time.
        """)

# ================= TAB 3: ANÁLISE POR JOGADOR =================
with tab3:
    st.title("Análise por Jogador")
    
    

    df_stats_player = df_stats.groupby("player").agg({
        "rating": "mean", "kills": "mean", "deaths": "mean", "assists": "mean",
        "kd": "mean", "hs": "mean", "adr": "mean"
    }).reset_index().sort_values(by="rating", ascending=False)
    
    df_radar_player, cols_radar_player = get_normalized_radar_df(df_stats_player, "player")

    c1, c2, c3, c4 = st.columns(4)
    render_top_metric(c1, "Jogador com maior KD médio", df_stats, "player", "kd", "KD médio")
    render_top_metric(c2, "Jogador com maior rating médio", df_stats, "player", "rating", "rating médio")
    render_top_metric(c3, "Jogador com maior precisão média", df_stats, "player", "hs", "%")
    render_top_metric(c4, "Jogador com maior dano médio por round", df_stats, "player", "adr", "Dano")

    st.divider()
    st.subheader("Estatísticas por jogador")

    player_filter = st.selectbox("Selecione um jogador", df_stats_player["player"], index=0)
    
    c1, c2, c3 = st.columns(3)
    fig_radar_single = plot_radar(df_radar_player, cols_radar_player, "player", [player_filter], {player_filter: 'green'})
    fig_radar_single.update_layout(title="Estatísticas do jogador")
    c1.plotly_chart(fig_radar_single, use_container_width=True)

    df_agents_picks = df_stats[df_stats["player"] == player_filter]["agent"].value_counts().reset_index()
    df_agents_picks.columns = ["agent", "picks"]
    df_agents_picks["agent"] = df_agents_picks["agent"].str.title()
    
    fig_agents = px.pie(df_agents_picks, values="picks", names="agent", title="Distribuição de Picks por Agente", color_discrete_sequence=px.colors.qualitative.Prism)
    c2.plotly_chart(fig_agents, use_container_width=True)

    df_agents_kills = df_stats[df_stats["player"] == player_filter][["agent", "kills"]].sort_values(by="kills", ascending=False)
    df_agents_kills["agent"] = df_agents_kills["agent"].str.title()
    fig_agents = px.bar(df_agents_kills, x="kills", y="agent", orientation='h', color="agent", title="Agentes com mais abates")
    c3.plotly_chart(fig_agents, use_container_width=True)

    st.divider()
    st.subheader(f"Desempenho do jogador {player_filter} por mapa")
    c1, c2 = st.columns(2)
    opcoes_mapas = df_maps["map"].tolist()
    idx_second_map = 1 if len(opcoes_mapas) > 1 else 0
    
    first_map = c1.selectbox("Selecione um mapa", opcoes_mapas, index=0, key="player_first_map")
    second_map = c2.selectbox("Selecione outro mapa", opcoes_mapas, index=idx_second_map, key="player_second_map")

    df_player_all_matches = df_stats[df_stats["player"] == player_filter].copy()
    df_player_all_matches["map"] = df_player_all_matches["map"].str.title()
    
    if not df_player_all_matches.empty and len(opcoes_mapas) > 0:
        df_stats_map = df_player_all_matches.groupby("map").agg({
            "rating": "mean", "kills": "mean", "deaths": "mean", "assists": "mean",
            "kd": "mean", "hs": "mean", "adr": "mean"
        }).reset_index()

    df_radar_map, cols_radar_map = get_normalized_radar_df(df_stats_map, "map")

    c1_map, c2_map, c3_map = st.columns(3)
        
    map_colors = {first_map: 'purple', second_map: 'yellow'}
    map_items = [first_map] if first_map == second_map else [first_map, second_map]
        
    fig_radar_map = plot_radar(df_radar_map, cols_radar_map, "map", map_items, map_colors)
    c1_map.plotly_chart(fig_radar_map, use_container_width=True)

    fig_box_map_hs = plot_boxplot(df_player_all_matches, "map", map_items, "hs", "Precisão por Mapa (HS %)", map_colors)
    c2_map.plotly_chart(fig_box_map_hs, use_container_width=True)
        
    fig_box_map_kills = plot_boxplot(df_player_all_matches, "map", map_items, "kills", "Abates por Mapa", map_colors)
    c3_map.plotly_chart(fig_box_map_kills, use_container_width=True)