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
    df_display = df_filtrado[['Data', 'Partida', 'Nome 1', 'Time 1', 'Placar 1', 'Nome 2', 'Time 2', 'Placar 2', 'Vencedor']].copy()
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

        max_jogos = max((stats[j]['total'] for j in jogadores), default=1)
        saldos = [stats[j]['saldo_gols'] for j in jogadores]
        min_saldo, max_saldo = min(saldos), max(saldos)

        ranking = []
        for jogador in jogadores:
            s = stats[jogador]
            total = s['total']
            vitorias = s['vitorias']

            # Peso 1: Taxa de Vitórias
            w1 = (vitorias / total * 20) if total > 0 else 0.0

            # Peso 2: Head-to-Head (média das taxas de vitória contra cada adversário)
            outros = [j for j in jogadores if j != jogador]
            h2h_rates = []
            for oponente in outros:
                conf = _df[
                    ((_df['Nome 1'] == jogador) & (_df['Nome 2'] == oponente)) |
                    ((_df['Nome 1'] == oponente) & (_df['Nome 2'] == jogador))
                ]
                if len(conf) > 0:
                    wins_vs = len(conf[conf['Vencedor'] == jogador])
                    h2h_rates.append(wins_vs / len(conf))
            w2 = (sum(h2h_rates) / len(h2h_rates) * 20) if h2h_rates else 0.0

            # Peso 3: Participação Relativa
            w3 = (total / max_jogos * 20) if max_jogos > 0 else 0.0

            # Peso 4: Momento Recente (últimas 30 partidas)
            ultimas = s['jogos'].sort_values('Data', ascending=False).head(30)
            n = len(ultimas)
            wins_rec = len(ultimas[ultimas['Vencedor'] == jogador])
            w4 = (wins_rec / n * 20) if n > 0 else 0.0

            # Peso 5: Saldo de Gols (normalizado 0–20)
            saldo = s['saldo_gols']
            if max_saldo != min_saldo:
                w5 = (saldo - min_saldo) / (max_saldo - min_saldo) * 20
            else:
                w5 = 10.0

            ranking.append({
                'Jogador': jogador,
                'Jogos': total,
                'Vitórias': vitorias,
                'Saldo': s['saldo_gols'],
                'W1': round(w1, 1),
                'W2': round(w2, 1),
                'W3': round(w3, 1),
                'W4': round(w4, 1),
                'W5': round(w5, 1),
                'Total': round(w1 + w2 + w3 + w4 + w5, 1)
            })

        return pd.DataFrame(ranking).sort_values('Total', ascending=False).reset_index(drop=True)

    ranking_df = calcular_ranking(df)

    # ── RANKING ─────────────────────────────────────────────────────────────
    st.subheader("🏆 Ranking do Campeonato")

    medals = ['🥇', '🥈', '🥉']
    podium_cols = st.columns(min(3, len(ranking_df)))
    for i, col in enumerate(podium_cols):
        row = ranking_df.iloc[i]
        col.metric(
            label=f"{medals[i]} {row['Jogador']}",
            value=f"{row['Total']:.1f} pts",
            help=f"Jogos: {row['Jogos']} | Vitórias: {row['Vitórias']} | Saldo de gols: {row['Saldo']:+d}"
        )

    pos_labels = medals + [str(i) for i in range(4, len(ranking_df) + 1)]
    tabela = ranking_df.copy()
    tabela.insert(0, '#', pos_labels[:len(tabela)])
    st.dataframe(
        tabela[['#', 'Jogador', 'W1', 'W2', 'W3', 'W4', 'W5', 'Total', 'Jogos', 'Vitórias', 'Saldo']],
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
    fig.update_layout(showlegend=False, xaxis_title='Pontuação Total (max 100)')
    st.plotly_chart(fig, use_container_width=True)

    # ── DETALHAMENTO ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Detalhamento por Indicador")
    st.caption("Cada indicador vale até 20 pontos. Clique para expandir e ver o detalhamento.")

    pesos = [
        {
            'col': 'W1',
            'emoji': '🎯',
            'titulo': 'Peso 1 — Taxa de Vitórias',
            'info': (
                "Mede a **eficiência** do jogador: quantos % das suas partidas ele venceu. "
                "Não depende do volume de jogos — quem jogou pouco mas ganhou muito é valorizado. "
                "\n\n**Fórmula:** (vitórias ÷ total de jogos) × 20"
            ),
            'cor': 'Blues'
        },
        {
            'col': 'W2',
            'emoji': '⚔️',
            'titulo': 'Peso 2 — Head-to-Head',
            'info': (
                "Mede o desempenho em **confrontos diretos** contra cada adversário do grupo. "
                "Calcula a taxa de vitória de cada jogador contra cada oponente individualmente, "
                "depois tira a média. Quem bate os mais fortes pontua melhor. "
                "\n\n**Fórmula:** média das taxas de vitória vs. cada oponente × 20"
            ),
            'cor': 'Oranges'
        },
        {
            'col': 'W3',
            'emoji': '📅',
            'titulo': 'Peso 3 — Participação Relativa',
            'info': (
                "Mede a **presença e dedicação** ao campeonato. "
                "O jogador com mais partidas recebe 20 pontos; os demais são proporcionais. "
                "Incentiva participação sem eliminar quem faltou em alguns dias. "
                "\n\n**Fórmula:** (jogos do jogador ÷ máximo de jogos do grupo) × 20"
            ),
            'cor': 'Purples'
        },
        {
            'col': 'W4',
            'emoji': '🔥',
            'titulo': 'Peso 4 — Momento Recente',
            'info': (
                "Mede a **forma atual** do jogador com base nas últimas 30 partidas. "
                "Evita que resultados antigos congelem o ranking e dá dinamismo à disputa — "
                "quem estiver em alta sobe, quem estiver em baixa cai. "
                "\n\n**Fórmula:** (vitórias nas últimas 30 partidas ÷ 30) × 20"
            ),
            'cor': 'Reds'
        },
        {
            'col': 'W5',
            'emoji': '⚽',
            'titulo': 'Peso 5 — Saldo de Gols',
            'info': (
                "Mede o **domínio** do jogador além do placar: diferença entre gols marcados e sofridos, "
                "normalizada entre o melhor e pior saldo do grupo. "
                "Premia quem vence com folga e penaliza quem perde por goleada. "
                "\n\n**Fórmula:** (saldo − min_saldo) ÷ (max_saldo − min_saldo) × 20"
            ),
            'cor': 'Greens'
        }
    ]

    for peso in pesos:
        with st.expander(f"{peso['emoji']} {peso['titulo']}"):
            st.info(peso['info'])

            peso_df = ranking_df[['Jogador', peso['col']]].sort_values(peso['col'], ascending=False)
            fig = px.bar(
                peso_df,
                x='Jogador',
                y=peso['col'],
                color=peso['col'],
                color_continuous_scale=peso['cor'],
                text=peso['col'],
                range_y=[0, 22]
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(
                showlegend=False,
                yaxis_title='Pontos (max 20)',
                xaxis_title=''
            )
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Dashboard eFootball - Dados de 2026")
