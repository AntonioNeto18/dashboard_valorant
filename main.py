import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

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

tab1, tab2, tab3 = st.tabs(["Visão Geral", "Análise por time", "Análise por jogador"])

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

df_final = df_torneio.copy()

if mapas_sel:
    df_final = df_final[df_final["map"].isin(mapas_sel)]

df_stats = df_final[df_final["side"] == "both"]

with tab1:
    st.title(f"Visão geral do {torneio_sel}")

    # Métricas
    if (not df_stats.empty and "rating" in df_stats.columns and (df_stats["rating"] != 0).any()):
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        # MVP do Torneio (KD)
        kd_mvp = df_stats.groupby("player")["kd_diff"].mean()
            
        mvp_nome = kd_mvp.idxmax().title()
        mvp_score = kd_mvp.max()

        col1.metric(
            label="MVP do Torneio (KD)",
            value=mvp_nome,
            delta=f"{mvp_score:.2f} KD médio"
        )

        # MVP do Torneio (rating)
        rating_mvp = df_stats.groupby("player")["rating"].mean()
        rating_mvp_nome = rating_mvp.idxmax().title()
        rating_mvp_score = rating_mvp.max()

        col2.metric(
            label="MVP do Torneio (Rating)",
            value=rating_mvp_nome,
            delta=f"{rating_mvp_score:.2f} Rating médio"
        )

        # Jogador com mais precisão
        hs_mvp = df_stats.groupby("player")["hs_pct"].mean()
        hs_mvp_nome = hs_mvp.idxmax().title()
        hs_mvp_score = hs_mvp.max()

        col3.metric(
            label="Jogador com mais precisão",
            value=hs_mvp_nome,
            delta=f"{hs_mvp_score:.2f} %"
        )

        # Agente Popular
        ranking_agente = df_stats["agent"].value_counts()

        agente_nome = ranking_agente.idxmax().title()
        agente_count = ranking_agente.max()

        col4.metric(
            label="Agente Popular",
            value=agente_nome,
            delta=f"{agente_count} picks"
        )

        # Quantidade de Jogadores no Torneio
        col5.metric(
            label="Jogadores",
            value=df_stats["player"].nunique()
        )

        # Quantidade de Times no Torneio
        col6.metric(
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
    else:
        st.error("Dados inexistentes.")

with tab2:

    st.title("Análise por Time")
    df_stats_time = df_stats.groupby("team").agg({
        "rating": "mean",
        "kills": "mean",
        "deaths": "mean",
        "assists": "mean",
        "kd_diff": "mean",
        "hs_pct": "mean",
        "adr": "mean"
    }).reset_index()
    df_stats_time = df_stats_time.sort_values(by="rating", ascending=False)

    col1, col2, col3, col4 = st.columns(4)

    # MVP torneio (KD)
    kd_mvp = df_stats.groupby("team")["kd_diff"].mean()
    mvp_nome = kd_mvp.idxmax()
    mvp_score = kd_mvp.max()

    col1.metric(
        label="Time com maior KD médio",
        value=mvp_nome,
        delta=f"{mvp_score:.2f} KD médio"
    )

    # MVP torneio (rating)
    rating_mvp = df_stats.groupby("team")["rating"].mean()
    rating_mvp_nome = rating_mvp.idxmax()
    rating_mvp_score = rating_mvp.max()

    col2.metric(
        label="Time com maior rating médio",
        value=rating_mvp_nome,
        delta=f"{rating_mvp_score:.2f} rating médio"
    )
    
    # Time com maior precisão
    hs_mvp = df_stats.groupby("team")["hs_pct"].mean()
    hs_mvp_nome = hs_mvp.idxmax()
    hs_mvp_score = hs_mvp.max()

    col3.metric(
        label="Time com maior precisão média",
        value=hs_mvp_nome,
        delta=f"{hs_mvp_score:.2f} %"
    )

    # Time com maior dano por round
    adr_mvp = df_stats.groupby("team")["adr"].mean()
    adr_mvp_nome = adr_mvp.idxmax()
    adr_mvp_score = adr_mvp.max()

    col4.metric(
        label="Time com maior dano médio por round",
        value=adr_mvp_nome,
        delta=f"{adr_mvp_score:.2f} Dano"
    )

    st.divider()
    st.subheader("Estaísticas por time")

    team_filter = st.selectbox("Selecione um time", df_stats_time["team"], index=0)
    
    # Para o gráfico de radar ficar visualmente útil, precisamos NORMALIZAR 
    # os dados (0 a 100). Senão o ACS (~250) esconde o K/D (~1.5) e tudo 
    # fica visualmente idêntico e esticado nos mesmos lugares.
    df_radar = df_stats_time.copy()
    cols_radar = df_radar.drop(columns=["team"]).columns

    for col in cols_radar:
        max_val = df_radar[col].max()
        min_val = df_radar[col].min()
        if max_val != min_val:
            df_radar[col] = (df_radar[col] - min_val) / (max_val - min_val) * 100
        else:
            df_radar[col] = 100

    col1, col2, col3 = st.columns(3)

    # Gráfico de radar
    df_team = df_radar[df_radar["team"] == team_filter]
    df_team = df_team[cols_radar].iloc[0].values

    fig_radar = go.Figure()

    fig_radar.add_trace(go.Scatterpolar(
        r=df_team,
        theta=cols_radar,
        fill='toself',
        name=team_filter,
        line=dict(color='green')
    ))

    fig_radar.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", # Fundo transparente para incorporar no dashboard
        polar=dict(
            bgcolor="rgba(0,0,0,0)", # Fundo transparente da teia
            radialaxis=dict(
                visible=True,
                showticklabels=True,
                range=[0, 100]
            )
        ),
        showlegend=True
    )

    # Gráfico de pizza com os picls de agentes por time selecionado
    df_agents = df_stats[df_stats["team"] == team_filter]["agent"].value_counts().reset_index()
    df_agents.columns = ["agent", "picks"]
    df_agents["agent"] = df_agents["agent"].str.title()

    fig_pizza = px.pie(
        df_agents,
        values="picks",
        names="agent",
        title="Distribuição de Picks por Agente",
        color_discrete_sequence=px.colors.qualitative.Prism
    )

    # Gráfico de pizza com os mapas mais jogados por time selecionado
    df_maps = df_stats[df_stats["team"] == team_filter]["map"].value_counts().reset_index()
    df_maps.columns = ["map", "plays"]
    df_maps["map"] = df_maps["map"].str.title()

    fig_maps = px.pie(
        df_maps,
        values="plays",
        names="map",
        title="Mapas mais jogados",
        color_discrete_sequence=px.colors.qualitative.Prism
    )

    col1.plotly_chart(fig_radar, use_container_width=True)
    col2.plotly_chart(fig_pizza, use_container_width=True)
    col3.plotly_chart(fig_maps, use_container_width=True)

    st.divider()
    st.subheader("Comparação entre times")

    col1, col2 = st.columns(2)

    first_team = col1.selectbox("Escolha um time", df_stats_time["team"], index=0)
    second_team = col2.selectbox("Escolha outro time", df_stats_time["team"], index=len(df_stats_time)-2)

    df_first_team = df_stats_time[df_stats_time["team"] == first_team]
    df_second_team = df_stats_time[df_stats_time["team"] == second_team]

    r_first = df_radar[df_radar["team"] == first_team][cols_radar].iloc[0].values
    r_second = df_radar[df_radar["team"] == second_team][cols_radar].iloc[0].values

    fig_radar = go.Figure()

    fig_radar.add_trace(go.Scatterpolar(
        r=r_first,
            theta=cols_radar,
            fill='toself',
            name=first_team,
            line=dict(color='red')
        ))

    fig_radar.add_trace(go.Scatterpolar(
        r=r_second,
        theta=cols_radar,
        fill='toself',
        name=second_team,
        line=dict(color='blue')
    ))

    fig_radar.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", # Fundo transparente para incorporar no dashboard
        polar=dict(
            bgcolor="rgba(0,0,0,0)", # Fundo transparente da teia
            radialaxis=dict(
                visible=True,
                showticklabels=True,
                range=[0, 100]
            )
        ),
        showlegend=True
    )

    st.plotly_chart(fig_radar, use_container_width=True)
        
    with st.expander("Legenda do Gráfico"):
        st.markdown("""
        - **ADR (Average Damage Per Round):** Dano médio causado por round.
        - **KD_DIFF:** Saldo de Kills menos Deaths (Abates vs Mortes).
        - **HS_PCT:** Porcentagem de acertos na cabeça (Headshot).
        - **Kills / Deaths / Assists:** Média de Abates, Mortes ou Assistências feitas pelo time.
        """)
