# Importação de bibliotecas ----
import os
from shiny import App, ui, render, reactive
import pandas as pd
import plotnine as p9


# Importação de dados ----
dados = (
    pd.read_csv("dados_tratados.csv")
    .assign(
        data = lambda x: pd.to_datetime(x.data),
        index = lambda x: x.data
        )
    .set_index("index")
    )


# Objetos úteis para Interface do Usuário/Servidor
nomes_variaveis = dados.variavel.unique().tolist()
nomes_paises = dados.pais.sort_values().unique().tolist()
datas = dados.data.dt.date


# Interface do Usuário ----
app_ui = ui.page_navbar(
    ui.nav_panel(
        "⚽ Macro Copa",
        ui.layout_sidebar(
            ui.sidebar(

                ui.p(
                    ui.strong(
                        "Entra em campo a seleção de dados" +
                        " macroeconômicos! ⚽"
                        )
                    ),
                ui.p(
                    "Defina os times de países e indicadores, explore o jo" +
                    "go de visualizações e marque gol na análise de dados!"
                    ),

                ui.input_select(
                    id = "btn_variavel",
                    label = ui.strong("Selecione uma variável:"),
                    choices = nomes_variaveis,
                    selected = "PIB (%, cresc. anual)",
                    multiple = False
                ),

                ui.input_date_range(
                    id = "btn_periodo",
                    label = ui.strong("Filtre os anos:"),
                    start = "2000-01-01",
                    end = datas.max(),
                    min = datas.min(),
                    max = datas.max(),
                    format = "yyyy",
                    startview = "year",
                    language = "pt-BR",
                    separator = "-"
                ),

                ui.input_radio_buttons(
                    id = "btn_tipo_grafico",
                    label = ui.strong("Selecione o tipo do gráfico:"),
                    choices = ["Área", "Coluna", "Linha"],
                    selected = "Linha"
                ),

                ui.strong(ui.tags.label("Baixar dados:")),
                ui.download_button(
                    id = "btn_download",
                    label = "Download CSV"
                    ),

                ui.markdown(
                    """
                    Dados: Banco Mundial
                    Elaboração: [Análise Macro](https://analisemacro.com.br/)
                    """
                ),
                width = 250
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        ui.row(
                            ui.column(4, ui.strong("Selecione o 1º país:")),
                            ui.column(
                                8,
                                ui.input_select(
                                    id = "btn_pais1",
                                    label = "",
                                    choices = nomes_paises,
                                    selected = "Brazil",
                                    multiple = False,
                                    width = "100%"
                                )
                            )
                        )
                    ),
                    ui.card(ui.output_data_frame("resumo_pais1"), height = "360px"),
                    ui.card(ui.output_plot("plt_pais1"), max_height = "300px")
                    ),
                ui.card(
                    ui.card_header(
                        ui.row(
                            ui.column(4, ui.strong("Selecione o 2º país:")),
                            ui.column(
                                8,
                                ui.input_select(
                                    id = "btn_pais2",
                                    label = "",
                                    choices = nomes_paises,
                                    selected = "Argetina",
                                    multiple = False,
                                    width = "100%"
                                )
                            )
                        )
                    ),
                    ui.card(ui.output_data_frame("resumo_pais2"), height = "360px"),
                    ui.card(ui.output_plot("plt_pais2"), max_height = "300px")
                    ),
                max_height = "600px"
            )
        )
    ),
    title = ui.img(src = "https://aluno.analisemacro.com.br/wp-content/uploads/dlm_uploads/2023/05/logo_am_45.png", width = 65)
)



# Servidor ----
def server(input, output, session):

    
    def tabela_pais(pais):
        df = (
            dados
            .query("pais == @pais")
            .groupby("variavel")
            .tail(1)
            .filter(
                items = ["data", "variavel", "valor"],
                axis = "columns"
                )
            .assign(
                data = lambda x: x.data.dt.year,
                valor = lambda x: x.valor.round(2)
                )
            .rename(
                columns = {
                    "data": "Ano",
                    "variavel": "Indicador",
                    "valor": "Valor"
                    }
                )
            )
        return df


    @reactive.Calc
    def tabela_pais1():
        return tabela_pais(input.btn_pais1())


    @reactive.Calc
    def tabela_pais2():
        return tabela_pais(input.btn_pais2())


    @output
    @render.data_frame
    def resumo_pais1():
        return render.DataGrid(
            data = tabela_pais1(),
            width = "100%",
            summary = False
            )


    @output
    @render.plot
    def plt_pais1():

        var = input.btn_variavel()
        pais1 = input.btn_pais1()
        tipo_plt = input.btn_tipo_grafico()
        dt_inic = input.btn_periodo()[0]
        dt_fim = input.btn_periodo()[1]

        df1 = dados.query(
            "variavel == @var and data >= @dt_inic and data <= @dt_fim and pais == @pais1"
            )

        plt1 = (
            p9.ggplot(data = df1) +
            p9.aes(x = "data", y = "valor") +
            p9.scale_x_date(date_labels = "%Y") +
            p9.ggtitle(pais1 + " - " + var) +
            p9.ylab("") +
            p9.xlab("Ano") +
            p9.labs(caption = "Dados: Banco Mundial | Elaboração: Análise Macro")
        )
        if tipo_plt == "Área":
            plt1 = (plt1 + p9.geom_area())
        elif tipo_plt == "Coluna":
            plt1 = (plt1 + p9.geom_col())
        elif tipo_plt == "Linha":
            plt1 = (plt1 + p9.geom_line())

        return plt1
    
    
    @output
    @render.data_frame
    def resumo_pais2():
        return render.DataGrid(
            data = tabela_pais2(),
            width = "100%",
            summary = False
            )
    

    @output
    @render.plot
    def plt_pais2():

        var = input.btn_variavel()
        pais2 = input.btn_pais2()
        tipo_plt = input.btn_tipo_grafico()
        dt_inic = input.btn_periodo()[0]
        dt_fim = input.btn_periodo()[1]

        df2 = dados.query(
            "variavel == @var and data >= @dt_inic and data <= @dt_fim and pais == @pais2"
            )

        plt2 = (
            p9.ggplot(data = df2) +
            p9.aes(x = "data", y = "valor") +
            p9.scale_x_date(date_labels = "%Y") +
            p9.ggtitle(pais2 + " - " + var) +
            p9.ylab("") +
            p9.xlab("Ano") +
            p9.labs(caption = "Dados: Banco Mundial | Elaboração: Análise Macro")
        )
        if tipo_plt == "Área":
            plt2 = (plt2 + p9.geom_area())
        elif tipo_plt == "Coluna":
            plt2 = (plt2 + p9.geom_col())
        elif tipo_plt == "Linha":
            plt2 = (plt2 + p9.geom_line())

        return plt2
    

    @session.download()
    def btn_download():
        return os.path.join(os.path.dirname(__file__), "dados_tratados.csv")


# Shiny Dashboard
app = App(app_ui, server)
