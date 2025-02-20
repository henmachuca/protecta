# region Import Statements
import streamlit as st
import pandas as pd
import altair as alt
# endregion


# region Global Variables
custom_order = [
    "Sep-23",
    "Oct-23",
    "Nov-23",
    "Dec-23",
    "Jan-24",
    "Feb-24",
    "Mar-24",
    "Apr-24",
    "May-24",
    "Jun-24",
    "Jul-24",
    "Aug-24",
    "Sep-24",
    "Oct-24",
    "Nov-24",
    "Dec-24",
    "Jan-25",
]

month_mapping = {
    "jan": "01",
    "fev": "02",
    "mar": "03",
    "abr": "04",
    "mai": "05",
    "jun": "06",
    "jul": "07",
    "ago": "08",
    "set": "09",
    "out": "10",
    "nov": "11",
    "dez": "12",
}
# endregion


# region ---- Functions ----
# Função para converter data ex: 'set-23' para '2023-09-01'
def convert_to_datetime(periodo_str):
    # Dividir a string em mês e ano
    month, year = periodo_str.split("-")
    # Obter o número do mês a partir do mapeamento
    month_num = month_mapping[month]
    # Adicionar '20' ao início do ano
    year_full = "20" + year
    # Combinar no formato 'YYYY-MM-DD'
    date_str = f"{year_full}-{month_num}-01"
    # Converter para datetime
    return pd.to_datetime(date_str)


def convert_string_to_float(df, column_name):
    """
    Limpa e converte valores monetários da coluna especificada de um DataFrame.

    Parâmetros:
        df (pd.DataFrame): O DataFrame contendo os dados.
        column_name (str): O nome da coluna a ser processada.

    Retorna:
        pd.Series: Uma série com os valores limpos e convertidos para float.
    """
    return (
        df[column_name]
        .astype(str)  # Garante que os valores são strings
        .str.replace(r"R\$", "", regex=True)  # Remove 'R$'
        .str.strip()  # Remove espaços extras
        .str.replace(",", ".")  # Substitui ',' por '.'
        .apply(
            lambda x: -float(x.replace("-", "")) if "-" in x else float(x)
        )  # Converte para float, mantendo sinal negativo
    )


@st.cache_data
def load_data():
    df = pd.read_csv("Files/consorcio_set23_jan25.csv", sep=";", engine="python")

    # Remove espaços em branco dos cabeçalhos no DataFrame
    df.rename(columns=lambda x: x.strip(), inplace=True)

    # Aplicar a função na coluna 'Período' para conversão
    df["Período"] = df["Período"].apply(convert_to_datetime)
    return df


# endregion

# region ---- StreamLit Page Configs ----
st.set_page_config(
    layout="wide",
    page_title="Comissões Protecta-Servopa | Consórcio",
)

# Aplicando a cor de fundo via CSS
st.markdown(
    """
    <style>
    body {
        background-color: #FFFFFF;  # Altere para a cor desejada
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# endregion


df = load_data()

# Filtra somente colunas necessárias
df_dados = df.loc[:, ["Período", "SUBGRUPO", "COMISSÃO TOTAL", "CPF"]]
df_dados["COMISSÃO TOTAL"] = convert_string_to_float(df, "COMISSÃO TOTAL")


# region ---- Criação de DATAFRAMES ----

# DF agrupada por Período e SUBGRUPO retornando a soma de COMISSÃO TOTAL para o agrupamento
df_groupedby_periodo_subgrupo = (
    df_dados.groupby(["Período", "SUBGRUPO"])["COMISSÃO TOTAL"].sum().reset_index()
)

# DF agrupada por Período retornando a soma de COMISSÃO TOTAL para o agrupamento
df_soma_comissao = df_dados.groupby(["Período"])["COMISSÃO TOTAL"].sum().reset_index()
df_soma_comissao.rename(columns={"COMISSÃO TOTAL": "SOMA TOTAL"}, inplace=True)

# DF agrupada por Período retornando CPFs únicos
df_contagem_cpf = (
    # Converte cada data para o período do mês correspondente
    # Em vez de 2024-01-10, 2024-01-15 e 2024-01-25, todos viram "2024-01".
    df_dados.groupby(df["Período"].dt.to_period("M"))["CPF"]
    # Conta os CPFs únicos dentro de cada grupo
    .nunique()
    # transforma isso de volta em um DataFrame, com colunas normais.
    .reset_index()
)

# Certificar-se de que a coluna 'Período' esteja como string, ou uma coluna normal.
df_contagem_cpf["Período"] = df_contagem_cpf["Período"].astype(str)

df_contagem_cpf.columns = ["Período", "Contagem de CPFs"]
# endregion


# Transpor as informações que Subgrupos de linhas para Colunas separadas para cada tipo de subgrupo
df_groupedby_periodo_subgrupo_tratada = df_groupedby_periodo_subgrupo.pivot_table(
    index="Período", columns="SUBGRUPO", values="COMISSÃO TOTAL"
)

# Adicionar uma nova coluna para exibir as datas formatadas
df_groupedby_periodo_subgrupo_tratada["formatted_date"] = (
    df_groupedby_periodo_subgrupo_tratada.index.strftime(r"%b-%y")
)

# Criar um novo DataFrame para o gráfico, mantendo a coluna original de 'Período'
df_chart = (
    df_groupedby_periodo_subgrupo_tratada.reset_index()
    .set_index("formatted_date")
    .sort_values("Período")
)
df_chart = df_chart.drop("Período", axis=1).reset_index()

# Melt the DataFrame for Altair
df_melted = df_chart.melt(
    id_vars=["formatted_date"], var_name="SUBGRUPO", value_name="COMISSÃO TOTAL"
)


# region ---- Gráfico_01 ----
# Gráfico de barras
chart_01 = (
    alt.Chart(df_melted)
    .mark_bar(size=20)
    .encode(
        x=alt.X(
            "formatted_date:N",
            sort=custom_order,
            title="Período",
            axis=alt.Axis(labelAngle=45),
        ),
        y=alt.Y("COMISSÃO TOTAL:Q", title="Comissão Total"),
        color=alt.Color(
            "SUBGRUPO:N",
            legend=alt.Legend(
                title="Subgrupo",
                orient="bottom",  # Mover a legenda para baixo
                padding=10,  # Ajuste do espaçamento
                titleFontSize=12,  # Tamanho da fonte do título da legenda
                labelFontSize=10,  # Tamanho da fonte das legendas
            ),
        ),
        tooltip=[
            alt.Tooltip("formatted_date:N", title="Data"),
            alt.Tooltip("SUBGRUPO:N", title="Subgrupo"),
            alt.Tooltip("COMISSÃO TOTAL:Q", title="Comissão Total", format=",.1f"),
        ],
        xOffset="SUBGRUPO:N",
    )
)

# Rótulo de dados
text_chart_01 = (
    alt.Chart(df_melted)
    .mark_text(
        align="center",
        baseline="middle",
        dy=-10,  # Ajuste de deslocamento vertical
        color="black",
    )
    .transform_calculate(label=alt.datum["COMISSÃO TOTAL"] / 1000)
    .encode(
        x=alt.X(
            "formatted_date:N",
            sort=custom_order,
            title="Período",
            axis=alt.Axis(labelAngle=45),
        ),
        y=alt.Y("COMISSÃO TOTAL:Q"),
        text=alt.Text("label:Q", format=",.1f"),
        xOffset="SUBGRUPO:N",
    )
)

# Combinar os gráficos
# final_chart = chart3 + text
final_chart_01 = (
    alt.layer(chart_01, text_chart_01)
    .configure_axis(grid=False)
    .configure_view(continuousWidth=600, continuousHeight=400, step=10)
    .configure_title(
        fontSize=20,  # Ajusta o tamanho da fonte do título
        font="Arial",  # Ajusta o tipo de fonte
        anchor="middle",  # Posiciona o título no meio
        color="blue",  # Define a cor do título
    )
    .properties(
        title="Comissão Total e Soma por Período",  # Título principal
    )
)

# final_chart = (
#     alt.layer(chart3, text)
#     .configure_axis(grid=False)
#     .configure_view(continuousWidth=600, continuousHeight=400, step=10)
# )

# endregion

# region ---- Gráfico 02 ----

chart_02 = (
    alt.Chart(df_contagem_cpf)
    .mark_bar(size=35)
    .encode(
        x=alt.X("Período:N", title="Período"),
        y=alt.Y("Contagem de CPFs:Q", title="Contagem de CPFs"),
    )
)

text_chart_02 = (
    alt.Chart(df_contagem_cpf)
    .mark_text(
        align="center",
        baseline="middle",
        dy=-10,  # Ajuste do deslocamento vertical para o texto
        color="black",
    )
    .encode(
        x=alt.X("Período:N"),
        y=alt.Y("Contagem de CPFs:Q"),
        text=alt.Text(
            "Contagem de CPFs:Q", format=","
        ),  # Formatação de números com vírgula
    )
)

final_chart_02 = (
    alt.layer(chart_02, text_chart_02)
    .configure_axis(grid=False)
    .configure_title(
        fontSize=20,  # Ajuste do tamanho da fonte do título
        anchor="middle",  # Centraliza o título
        color="blue",  # Muda a cor do título para azul (pode ser qualquer cor)
    )
    .properties(title="Contagem de CPFs por Mês", width=600, height=400)
)

# endregion

# # Criando 2 colunas no Streamlit
# col1, col2 = st.columns(2)

# # Exibindo os gráficos nas colunas
# with col1:
#     st.altair_chart(final_chart_01, use_container_width=True)

# with col2:
#     st.altair_chart(final_chart_02, use_container_width=True)

st.altair_chart(final_chart_01, use_container_width=True)
st.altair_chart(final_chart_02, use_container_width=True)
