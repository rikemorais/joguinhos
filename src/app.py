import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote

st.set_page_config(
    page_title="eFootball Dashboard",
    page_icon="⚽",
    layout="wide"
)

# Configuração do Google Sheets
SHEET_ID = "1TG5d3HJ30_tItkz8urWjBxN3S_gYY8KB3zqk2vxcx-g"
SHEET_NAME = "efootball - Dados"

@st.cache_data(ttl=300)  # Recarrega a cada 5 minutos
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(SHEET_NAME)}"
    df = pd.read_csv(url)
    # Remove espaços extras dos nomes das colunas
    df.columns = df.columns.str.strip()
    if 'Data' not in df.columns:
        st.error(f"Coluna 'Data' não encontrada. Colunas disponíveis: {list(df.columns)}")
        st.stop()
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
    return df

df = load_data()

st.title("⚽ eFootball Dashboard")
st.markdown("---")

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

total_jogos = len(df)
total_gols = df['Placar 1'].sum() + df['Placar 2'].sum()
media_gols = total_gols / total_jogos
empates = len(df[df['Vencedor'] == 'Empate'])

col1.metric("Total de Jogos", total_jogos)
col2.metric("Total de Gols", int(total_gols))
col3.metric("Média de Gols/Jogo", f"{media_gols:.2f}")
col4.metric("Empates", empates)

st.markdown("---")

# Tabs principais
tab1, tab2, tab3, tab4, tab5, tab_camp = st.tabs([
    "📊 Visão Geral",
    "🏆 Rankings",
    "📈 Estatísticas por Jogador",
    "⚔️ Confrontos Diretos",
    "📅 Histórico",
    "🥇 Campeonato"
])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Jogos por Data")
        jogos_por_dia = df.groupby('Data').size().reset_index(name='Jogos')
        fig = px.bar(
            jogos_por_dia,
            x='Data',
            y='Jogos',
            color='Jogos',
            color_continuous_scale='Blues'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Distribuição de Resultados")
        df_sem_empate = df[df['Vencedor'] != 'Empate']
        vitorias = df_sem_empate['Vencedor'].value_counts().reset_index()
        vitorias.columns = ['Jogador', 'Vitórias']
        fig = px.pie(
            vitorias,
            values='Vitórias',
            names='Jogador',
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Gols por Jogador")
        # Calcular gols de cada jogador (tanto como Nome 1 quanto Nome 2)
        gols_nome1 = df.groupby('Nome 1')['Placar 1'].sum().reset_index()
        gols_nome1.columns = ['Jogador', 'Gols']
        gols_nome2 = df.groupby('Nome 2')['Placar 2'].sum().reset_index()
        gols_nome2.columns = ['Jogador', 'Gols']
        gols_total = pd.concat([gols_nome1, gols_nome2]).groupby('Jogador')['Gols'].sum().reset_index()
        gols_total = gols_total.sort_values('Gols', ascending=True)

        fig = px.bar(
            gols_total,
            x='Gols',
            y='Jogador',
            orientation='h',
            color='Gols',
            color_continuous_scale='Greens'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Times Mais Usados")
        times1 = df['Time 1'].value_counts().reset_index()
        times1.columns = ['Time', 'Uso']
        times2 = df['Time 2'].value_counts().reset_index()
        times2.columns = ['Time', 'Uso']
        times_total = pd.concat([times1, times2]).groupby('Time')['Uso'].sum().reset_index()
        times_total = times_total.sort_values('Uso', ascending=False).head(10)

        fig = px.bar(
            times_total,
            x='Time',
            y='Uso',
            color='Uso',
            color_continuous_scale='Reds'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── CHORD DIAGRAM ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🎯 Confrontos entre Jogadores")
    st.caption("Cada arco representa um jogador. As faixas conectando dois jogadores mostram quantas vezes se enfrentaram — quanto mais grossa, mais jogos. A cor indica o time mais usado pelo jogador.")

    def make_chord(jogadores_list, data):
        import numpy as np

        n = len(jogadores_list)
        idx = {j: i for i, j in enumerate(jogadores_list)}

        # Matriz de confrontos
        flow = [[0] * n for _ in range(n)]
        for _, row in data.iterrows():
            i = idx.get(row['Nome 1'])
            j = idx.get(row['Nome 2'])
            if i is not None and j is not None and i != j:
                flow[i][j] += 1
                flow[j][i] += 1

        # Time mais usado por cada jogador
        player_teams = {}
        for jogador in jogadores_list:
            t1 = data[data['Nome 1'] == jogador]['Time 1']
            t2 = data[data['Nome 2'] == jogador]['Time 2']
            all_t = pd.concat([t1, t2]).dropna()
            player_teams[jogador] = all_t.mode()[0] if len(all_t) > 0 else '?'

        # Cores por time
        unique_teams = list(dict.fromkeys(player_teams[j] for j in jogadores_list))
        palette = px.colors.qualitative.Plotly + px.colors.qualitative.D3
        team_color = {t: palette[i % len(palette)] for i, t in enumerate(unique_teams)}

        row_sums = [sum(flow[i]) for i in range(n)]
        total = sum(row_sums)
        if total == 0:
            return go.Figure()

        gap = 0.04
        arc_sizes = [row_sums[i] / total * (2 * np.pi - n * gap) for i in range(n)]

        starts = [0.0] * n
        ends = [0.0] * n
        angle = 0.0
        for i in range(n):
            starts[i] = angle
            ends[i] = angle + arc_sizes[i]
            angle = ends[i] + gap

        # Sub-arcos para as faixas
        sub_start = [[0.0] * n for _ in range(n)]
        sub_end = [[0.0] * n for _ in range(n)]
        for i in range(n):
            if row_sums[i] == 0:
                continue
            cur = starts[i]
            for j in range(n):
                if i == j:
                    continue
                span = flow[i][j] / total * (2 * np.pi - n * gap)
                sub_start[i][j] = cur
                sub_end[i][j] = cur + span
                cur += span

        def arc_pts(a0, a1, r=1.0, pts=60):
            t = np.linspace(a0, a1, pts)
            return r * np.cos(t), r * np.sin(t)

        def bezier(p0, p1, pts=60):
            t = np.linspace(0, 1, pts)
            cx, cy = 0.0, 0.0
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t ** 2 * p1[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t ** 2 * p1[1]
            return x, y

        fig_chord = go.Figure()

        # Faixas (ribbons)
        for i in range(n):
            for j in range(i + 1, n):
                if flow[i][j] == 0:
                    continue
                color = team_color[player_teams[jogadores_list[i]]]
                ax1, ay1 = arc_pts(sub_start[i][j], sub_end[i][j], r=0.97)
                ax2, ay2 = arc_pts(sub_end[j][i], sub_start[j][i], r=0.97)
                bx1, by1 = bezier((ax1[0], ay1[0]), (ax2[-1], ay2[-1]))
                bx2, by2 = bezier((ax1[-1], ay1[-1]), (ax2[0], ay2[0]))
                rx = np.concatenate([ax1, bx1, ax2, bx2[::-1]])
                ry = np.concatenate([ay1, by1, ay2, by2[::-1]])
                fig_chord.add_trace(go.Scatter(
                    x=rx, y=ry,
                    fill='toself',
                    fillcolor=color,
                    opacity=0.25,
                    line=dict(width=0),
                    mode='lines',
                    hovertemplate=f"<b>{jogadores_list[i]}</b> vs <b>{jogadores_list[j]}</b><br>{flow[i][j]} jogos<extra></extra>",
                    showlegend=False
                ))

        # Arcos dos jogadores
        legend_shown = set()
        for i, jogador in enumerate(jogadores_list):
            color = team_color[player_teams[jogador]]
            team = player_teams[jogador]
            ax, ay = arc_pts(starts[i], ends[i], r=1.0)
            iax, iay = arc_pts(ends[i], starts[i], r=0.90)
            seg_x = np.concatenate([ax, iax, [ax[0]]])
            seg_y = np.concatenate([ay, iay, [ay[0]]])
            show_leg = team not in legend_shown
            legend_shown.add(team)
            fig_chord.add_trace(go.Scatter(
                x=seg_x, y=seg_y,
                fill='toself',
                fillcolor=color,
                opacity=0.9,
                line=dict(width=1, color='white'),
                mode='lines',
                name=team,
                legendgroup=team,
                showlegend=show_leg,
                hovertemplate=f"<b>{jogador}</b><br>Time favorito: {team}<extra></extra>"
            ))
            mid = (starts[i] + ends[i]) / 2
            lx = 1.15 * np.cos(mid)
            ly = 1.15 * np.sin(mid)
            fig_chord.add_annotation(
                x=lx, y=ly,
                text=jogador,
                showarrow=False,
                font=dict(size=12, color='white'),
                xanchor='left' if np.cos(mid) >= 0 else 'right'
            )

        fig_chord.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.5, 1.5]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.5, 1.5], scaleanchor='x'),
            height=580,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend_title_text='Time mais usado',
            margin=dict(l=60, r=60, t=20, b=20)
        )
        return fig_chord

    jogadores_chord = sorted(list(set(df['Nome 1'].unique()) | set(df['Nome 2'].unique())))
    st.plotly_chart(make_chord(jogadores_chord, df), use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🥇 Top Vencedores")
        df_sem_empate = df[df['Vencedor'] != 'Empate']
        top_vencedores = df_sem_empate['Vencedor'].value_counts().reset_index()
        top_vencedores.columns = ['Jogador', 'Vitórias']

        fig = px.bar(
            top_vencedores,
            x='Jogador',
            y='Vitórias',
            color='Vitórias',
            color_continuous_scale='Greens',
            text='Vitórias'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(top_vencedores, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("💀 Top Perdedores")
        df_sem_empate = df[df['Perdedor'] != 'Empate']
        top_perdedores = df_sem_empate['Perdedor'].value_counts().reset_index()
        top_perdedores.columns = ['Jogador', 'Derrotas']

        fig = px.bar(
            top_perdedores,
            x='Jogador',
            y='Derrotas',
            color='Derrotas',
            color_continuous_scale='Reds',
            text='Derrotas'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(top_perdedores, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📊 Ranking Geral (Saldo de Gols)")

    # Calcular saldo de gols para cada jogador
    saldo_vencedor = df[df['Vencedor'] != 'Empate'].groupby('Vencedor')['Saldo Vencedor'].sum().reset_index()
    saldo_vencedor.columns = ['Jogador', 'Saldo']
    saldo_perdedor = df[df['Perdedor'] != 'Empate'].groupby('Perdedor')['Saldo Perdedor'].sum().reset_index()
    saldo_perdedor.columns = ['Jogador', 'Saldo']
    saldo_total = pd.concat([saldo_vencedor, saldo_perdedor]).groupby('Jogador')['Saldo'].sum().reset_index()
    saldo_total = saldo_total.sort_values('Saldo', ascending=False)

    fig = px.bar(
        saldo_total,
        x='Jogador',
        y='Saldo',
        color='Saldo',
        color_continuous_scale='RdYlGn',
        text='Saldo'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    jogadores = sorted(list(set(df['Nome 1'].unique()) | set(df['Nome 2'].unique())))
    jogador_selecionado = st.selectbox("Selecione um jogador:", jogadores)

    # Filtrar jogos do jogador
    jogos_jogador = df[(df['Nome 1'] == jogador_selecionado) | (df['Nome 2'] == jogador_selecionado)]

    col1, col2, col3, col4 = st.columns(4)

    total_jogos_j = len(jogos_jogador)
    vitorias_j = len(jogos_jogador[jogos_jogador['Vencedor'] == jogador_selecionado])
    derrotas_j = len(jogos_jogador[jogos_jogador['Perdedor'] == jogador_selecionado])
    empates_j = len(jogos_jogador[jogos_jogador['Vencedor'] == 'Empate'])

    col1.metric("Jogos", total_jogos_j)
    col2.metric("Vitórias", vitorias_j)
    col3.metric("Derrotas", derrotas_j)
    col4.metric("Empates", empates_j)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Aproveitamento")
        if total_jogos_j > 0:
            aproveitamento = (vitorias_j * 3 + empates_j) / (total_jogos_j * 3) * 100
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = aproveitamento,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Aproveitamento (%)"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 33], 'color': "lightcoral"},
                        {'range': [33, 66], 'color': "lightyellow"},
                        {'range': [66, 100], 'color': "lightgreen"}
                    ]
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Resultados")
        fig = px.pie(
            values=[vitorias_j, derrotas_j, empates_j],
            names=['Vitórias', 'Derrotas', 'Empates'],
            color_discrete_sequence=['green', 'red', 'gray']
        )
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Times Mais Usados")
        times_j1 = jogos_jogador[jogos_jogador['Nome 1'] == jogador_selecionado]['Time 1']
        times_j2 = jogos_jogador[jogos_jogador['Nome 2'] == jogador_selecionado]['Time 2']
        times_j = pd.concat([times_j1, times_j2]).value_counts().reset_index()
        times_j.columns = ['Time', 'Uso']

        fig = px.bar(times_j.head(5), x='Time', y='Uso', color='Uso', color_continuous_scale='Blues')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Gols Marcados vs Sofridos")
        gols_marcados = jogos_jogador[jogos_jogador['Nome 1'] == jogador_selecionado]['Placar 1'].sum() + \
                        jogos_jogador[jogos_jogador['Nome 2'] == jogador_selecionado]['Placar 2'].sum()
        gols_sofridos = jogos_jogador[jogos_jogador['Nome 1'] == jogador_selecionado]['Placar 2'].sum() + \
                        jogos_jogador[jogos_jogador['Nome 2'] == jogador_selecionado]['Placar 1'].sum()

        fig = px.bar(
            x=['Gols Marcados', 'Gols Sofridos'],
            y=[gols_marcados, gols_sofridos],
            color=['Gols Marcados', 'Gols Sofridos'],
            color_discrete_map={'Gols Marcados': 'green', 'Gols Sofridos': 'red'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Histórico de Jogos")
    jogos_display = jogos_jogador[['Data', 'Nome 1', 'Time 1', 'Placar 1', 'Nome 2', 'Time 2', 'Placar 2', 'Vencedor']].copy()
    jogos_display['Data'] = jogos_display['Data'].dt.strftime('%d/%m/%Y')
    st.dataframe(jogos_display, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("⚔️ Confronto Direto")

    col1, col2 = st.columns(2)
    jogadores = sorted(list(set(df['Nome 1'].unique()) | set(df['Nome 2'].unique())))

    with col1:
        jogador1 = st.selectbox("Jogador 1:", jogadores, key='j1')
    with col2:
        jogador2 = st.selectbox("Jogador 2:", [j for j in jogadores if j != jogador1], key='j2')

    # Filtrar confrontos diretos
    confrontos = df[
        ((df['Nome 1'] == jogador1) & (df['Nome 2'] == jogador2)) |
        ((df['Nome 1'] == jogador2) & (df['Nome 2'] == jogador1))
    ]

    if len(confrontos) > 0:
        vitorias_j1 = len(confrontos[confrontos['Vencedor'] == jogador1])
        vitorias_j2 = len(confrontos[confrontos['Vencedor'] == jogador2])
        empates_conf = len(confrontos[confrontos['Vencedor'] == 'Empate'])

        col1, col2, col3 = st.columns(3)
        col1.metric(f"Vitórias {jogador1}", vitorias_j1)
        col2.metric("Empates", empates_conf)
        col3.metric(f"Vitórias {jogador2}", vitorias_j2)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribuição dos Confrontos")
            fig = px.pie(
                values=[vitorias_j1, empates_conf, vitorias_j2],
                names=[jogador1, 'Empate', jogador2],
                color_discrete_sequence=['blue', 'gray', 'red']
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Gols nos Confrontos")
            gols_j1 = confrontos[confrontos['Nome 1'] == jogador1]['Placar 1'].sum() + \
                      confrontos[confrontos['Nome 2'] == jogador1]['Placar 2'].sum()
            gols_j2 = confrontos[confrontos['Nome 1'] == jogador2]['Placar 1'].sum() + \
                      confrontos[confrontos['Nome 2'] == jogador2]['Placar 2'].sum()

            fig = px.bar(
                x=[jogador1, jogador2],
                y=[gols_j1, gols_j2],
                color=[jogador1, jogador2],
                text=[gols_j1, gols_j2]
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Histórico dos Confrontos")
        confrontos_display = confrontos[['Data', 'Nome 1', 'Time 1', 'Placar 1', 'Nome 2', 'Time 2', 'Placar 2', 'Vencedor']].copy()
        confrontos_display['Data'] = confrontos_display['Data'].dt.strftime('%d/%m/%Y')
        st.dataframe(confrontos_display, use_container_width=True, hide_index=True)
    else:
        st.info(f"Não há confrontos diretos entre {jogador1} e {jogador2}")

with tab5:
    st.subheader("📅 Histórico Completo")

    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Início", df['Data'].min())
    with col2:
        data_fim = st.date_input("Data Fim", df['Data'].max())

    df_filtrado = df[(df['Data'].dt.date >= data_inicio) & (df['Data'].dt.date <= data_fim)]

    st.metric("Jogos no período", len(df_filtrado))

    st.subheader("Evolução de Vitórias ao Longo do Tempo")
    df_sem_empate = df_filtrado[df_filtrado['Vencedor'] != 'Empate'].copy()
    df_sem_empate['Data_str'] = df_sem_empate['Data'].dt.strftime('%Y-%m-%d')
    vitorias_tempo = df_sem_empate.groupby(['Data_str', 'Vencedor']).size().reset_index(name='Vitórias')

    fig = px.line(
        vitorias_tempo,
        x='Data_str',
        y='Vitórias',
        color='Vencedor',
        markers=True
    )
    fig.update_layout(xaxis_title='Data', yaxis_title='Vitórias')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Todos os Jogos")
    col_f1, col_f2 = st.columns(2)
    todos_jogadores = sorted(set(df_filtrado['Nome 1'].dropna()) | set(df_filtrado['Nome 2'].dropna()))
    todos_times = sorted(set(df_filtrado['Time 1'].dropna()) | set(df_filtrado['Time 2'].dropna()))
    with col_f1:
        jogador_filtro = st.selectbox("Filtrar por jogador", options=['Todos'] + todos_jogadores)
    with col_f2:
        time_filtro = st.selectbox("Filtrar por time", options=['Todos'] + todos_times)

    df_display = df_filtrado[['Data', 'Partida', 'Nome 1', 'Time 1', 'Placar 1', 'Nome 2', 'Time 2', 'Placar 2', 'Vencedor']].copy()
    if jogador_filtro != 'Todos' and time_filtro != 'Todos':
        df_display = df_display[
            ((df_display['Nome 1'] == jogador_filtro) & (df_display['Time 1'] == time_filtro)) |
            ((df_display['Nome 2'] == jogador_filtro) & (df_display['Time 2'] == time_filtro))
        ]
    elif jogador_filtro != 'Todos':
        df_display = df_display[(df_display['Nome 1'] == jogador_filtro) | (df_display['Nome 2'] == jogador_filtro)]
    elif time_filtro != 'Todos':
        df_display = df_display[(df_display['Time 1'] == time_filtro) | (df_display['Time 2'] == time_filtro)]
    st.caption(f"Total de partidas: **{len(df_display)}**")
    df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_display, use_container_width=True, hide_index=True)

with tab_camp:
    @st.cache_data(ttl=300)
    def calcular_ranking(_df):
        jogadores = sorted(list(set(_df['Nome 1'].unique()) | set(_df['Nome 2'].unique())))
        stats = {}

        for jogador in jogadores:
            jogos = _df[(_df['Nome 1'] == jogador) | (_df['Nome 2'] == jogador)]
            total = len(jogos)
            vitorias = len(jogos[jogos['Vencedor'] == jogador])
            gols_marcados = (
                jogos[jogos['Nome 1'] == jogador]['Placar 1'].sum() +
                jogos[jogos['Nome 2'] == jogador]['Placar 2'].sum()
            )
            gols_sofridos = (
                jogos[jogos['Nome 1'] == jogador]['Placar 2'].sum() +
                jogos[jogos['Nome 2'] == jogador]['Placar 1'].sum()
            )
            stats[jogador] = {
                'total': total,
                'vitorias': vitorias,
                'saldo_gols': int(gols_marcados - gols_sofridos),
                'jogos': jogos
            }

        ranking = []
        for jogador in jogadores:
            s = stats[jogador]
            total = s['total']
            vitorias = s['vitorias']

            # W2: Média das taxas de vitória contra cada adversário
            outros = [j for j in jogadores if j != jogador]
            h2h_rates = []
            for oponente in outros:
                conf = _df[
                    ((_df['Nome 1'] == jogador) & (_df['Nome 2'] == oponente)) |
                    ((_df['Nome 1'] == oponente) & (_df['Nome 2'] == jogador))
                ]
                if len(conf) > 0:
                    wins_vs = len(conf[conf['Vencedor'] == jogador])
                    decisivos = len(conf[conf['Vencedor'] != 'Empate'])
                    if decisivos > 0:
                        h2h_rates.append(wins_vs / decisivos)
            media_vitorias = (sum(h2h_rates) / len(h2h_rates) * 100) if h2h_rates else 0.0

            ranking.append({
                'Jogador': jogador,
                'Jogos': total,
                'Vitórias': vitorias,
                'Saldo': s['saldo_gols'],
                'Média de Vitórias': round(media_vitorias, 1),
                'Total': round(media_vitorias, 1)
            })

        from functools import cmp_to_key

        def comparar(a, b):
            if a['Total'] != b['Total']:
                return -1 if a['Total'] > b['Total'] else 1
            # Desempate: confronto direto entre os dois
            conf = _df[
                ((_df['Nome 1'] == a['Jogador']) & (_df['Nome 2'] == b['Jogador'])) |
                ((_df['Nome 1'] == b['Jogador']) & (_df['Nome 2'] == a['Jogador']))
            ]
            decisivos = len(conf[conf['Vencedor'] != 'Empate'])
            if decisivos == 0:
                return 0
            wins_a = len(conf[conf['Vencedor'] == a['Jogador']])
            wins_b = len(conf[conf['Vencedor'] == b['Jogador']])
            return -1 if wins_a > wins_b else (1 if wins_b > wins_a else 0)

        return pd.DataFrame(sorted(ranking, key=cmp_to_key(comparar))).reset_index(drop=True)

    ranking_df = calcular_ranking(df)

    # ── RANKING ─────────────────────────────────────────────────────────────
    st.subheader("🏆 Ranking do Campeonato")

    medals = ['🥇', '🥈', '🥉']
    podium_cols = st.columns(min(3, len(ranking_df)))
    for i, col in enumerate(podium_cols):
        row = ranking_df.iloc[i]
        col.metric(
            label=f"{medals[i]} {row['Jogador']}",
            value=f"{row['Média de Vitórias']:.1f}%",
            help=f"Jogos: {row['Jogos']} | Vitórias: {row['Vitórias']} | Saldo de gols: {row['Saldo']:+d}"
        )

    pos_labels = medals + [str(i) for i in range(4, len(ranking_df) + 1)]
    tabela = ranking_df.copy()
    tabela.insert(0, '#', pos_labels[:len(tabela)])
    st.dataframe(
        tabela[['#', 'Jogador', 'Média de Vitórias', 'Jogos', 'Vitórias', 'Saldo']],
        use_container_width=True,
        hide_index=True
    )

    fig = px.bar(
        ranking_df.sort_values('Total'),
        x='Total',
        y='Jogador',
        orientation='h',
        color='Total',
        color_continuous_scale='RdYlGn',
        text='Total',
        range_x=[0, 100]
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False, xaxis_title='Média de Vitórias H2H (%)')
    st.plotly_chart(fig, use_container_width=True)

    # ── EVOLUÇÃO DO RANKING ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Evolução do Ranking por Dia")
    st.caption("Posição de cada jogador no ranking ao longo do tempo, recalculada a cada dia jogado.")

    @st.cache_data(ttl=300)
    def calcular_evolucao(_df):
        jogadores = sorted(list(set(_df['Nome 1'].unique()) | set(_df['Nome 2'].unique())))
        datas = sorted(_df['Data'].dt.date.unique())
        registros = []

        for data in datas:
            df_ate = _df[_df['Data'].dt.date <= data]
            # Calcula ranking acumulado até essa data
            h2h_scores = {}
            for jogador in jogadores:
                outros = [j for j in jogadores if j != jogador]
                h2h_rates = []
                for oponente in outros:
                    conf = df_ate[
                        ((_df['Nome 1'] == jogador) & (_df['Nome 2'] == oponente)) |
                        ((_df['Nome 1'] == oponente) & (_df['Nome 2'] == jogador))
                    ]
                    if len(conf) > 0:
                        wins = len(conf[conf['Vencedor'] == jogador])
                        decisivos = len(conf[conf['Vencedor'] != 'Empate'])
                        if decisivos > 0:
                            h2h_rates.append(wins / decisivos)
                h2h_scores[jogador] = (sum(h2h_rates) / len(h2h_rates) * 100) if h2h_rates else 0.0

            from functools import cmp_to_key

            def comparar_dia(a, b):
                if a[1] != b[1]:
                    return -1 if a[1] > b[1] else 1
                conf = df_ate[
                    ((df_ate['Nome 1'] == a[0]) & (df_ate['Nome 2'] == b[0])) |
                    ((df_ate['Nome 1'] == b[0]) & (df_ate['Nome 2'] == a[0]))
                ]
                decisivos = len(conf[conf['Vencedor'] != 'Empate'])
                if decisivos == 0:
                    return 0
                wins_a = len(conf[conf['Vencedor'] == a[0]])
                wins_b = len(conf[conf['Vencedor'] == b[0]])
                return -1 if wins_a > wins_b else (1 if wins_b > wins_a else 0)

            ranking_dia = sorted(h2h_scores.items(), key=cmp_to_key(comparar_dia))
            for pos, (jogador, _) in enumerate(ranking_dia, start=1):
                registros.append({'Data': data, 'Jogador': jogador, 'Posição': pos})

        return pd.DataFrame(registros)

    evolucao_df = calcular_evolucao(df)

    fig_evo = px.line(
        evolucao_df,
        x='Data',
        y='Posição',
        color='Jogador',
        markers=True,
    )
    fig_evo.update_yaxes(autorange='reversed', dtick=1, title='Posição no Ranking')
    fig_evo.update_xaxes(title='Data')
    fig_evo.update_layout(legend_title_text='Jogador')
    st.plotly_chart(fig_evo, use_container_width=True)

    # ── DETALHAMENTO ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Detalhamento — Média de Vitórias")

    with st.expander("⚔️ Média de Vitórias H2H", expanded=True):
        st.info(
            "Mede o desempenho em **confrontos diretos** contra cada adversário do grupo. "
            "Calcula a taxa de vitória contra cada oponente individualmente e tira a média. "
            "Quem bate mais adversários consistentemente fica no topo. "
            "\n\n**Fórmula:** média das taxas de vitória vs. cada oponente × 100"
        )

        mv_df = ranking_df[['Jogador', 'Média de Vitórias']].sort_values('Média de Vitórias', ascending=False)
        fig = px.bar(
            mv_df,
            x='Jogador',
            y='Média de Vitórias',
            color='Média de Vitórias',
            color_continuous_scale='Oranges',
            text='Média de Vitórias',
            range_y=[0, 110]
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(
            showlegend=False,
            yaxis_title='Média de Vitórias (%)',
            xaxis_title=''
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── MATRIZ H2H ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔢 Como a Média foi Calculada")
    st.caption("Cada célula mostra o % de vitórias do jogador da **linha** contra o jogador da **coluna**. A última coluna é a média — que define o ranking.")

    jogadores_ord = ranking_df['Jogador'].tolist()
    matriz = {}
    for j in jogadores_ord:
        matriz[j] = {}
        h2h_rates = []
        for oponente in jogadores_ord:
            if j == oponente:
                matriz[j][oponente] = None
                continue
            conf = df[
                ((df['Nome 1'] == j) & (df['Nome 2'] == oponente)) |
                ((df['Nome 1'] == oponente) & (df['Nome 2'] == j))
            ]
            if len(conf) > 0:
                wins = len(conf[conf['Vencedor'] == j])
                decisivos = len(conf[conf['Vencedor'] != 'Empate'])
                if decisivos > 0:
                    rate = round(wins / decisivos * 100, 1)
                    matriz[j][oponente] = rate
                    h2h_rates.append(rate)
                else:
                    matriz[j][oponente] = None
            else:
                matriz[j][oponente] = None
    # Tabela visual com cores
    heatmap_vals = []
    heatmap_text = []
    for j in jogadores_ord:
        row_vals = []
        row_text = []
        for oponente in jogadores_ord:
            val = matriz[j][oponente]
            if j == oponente:
                row_vals.append(None)
                row_text.append("—")
            elif val is None:
                row_vals.append(None)
                row_text.append("s/j")
            else:
                row_vals.append(val)
                row_text.append(f"{val:.0f}%")
        # Adiciona coluna da média
        rates = [matriz[j][op] for op in jogadores_ord if op != j and matriz[j][op] is not None]
        media = round(sum(rates) / len(rates), 1) if rates else 0.0
        row_vals.append(media)
        row_text.append(f"{media:.0f}%")
        heatmap_vals.append(row_vals)
        heatmap_text.append(row_text)

    colunas = jogadores_ord + ['Média ⭐']
    fig_heat = go.Figure(data=go.Heatmap(
        z=heatmap_vals,
        x=colunas,
        y=jogadores_ord,
        text=heatmap_text,
        texttemplate="%{text}",
        colorscale='RdYlGn',
        zmin=0,
        zmax=100,
        showscale=True,
        colorbar=dict(title='% Vitórias')
    ))
    fig_heat.update_layout(
        xaxis_title='Adversário',
        yaxis_title='Jogador',
        yaxis=dict(autorange='reversed'),
        height=max(300, len(jogadores_ord) * 55)
    )
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")
st.caption("Dashboard eFootball - Dados de 2026")
