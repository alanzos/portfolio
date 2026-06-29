# SP500 Shiny App with Solarized Dark Theme
# Load required libraries
library(shiny)
library(quantmod)
library(xts)
library(dygraphs)

# UI with bslib Solarized Dark theme
library(bslib)
solarized_dark <- bs_theme(
  version = 5,
  bg = "#002b36",
  fg = "#93a1a1",
  primary = "#b58900",
  secondary = "#268bd2",
  success = "#859900",
  info = "#2aa198",
  warning = "#cb4b16",
  danger = "#dc322f",
  base_font = font_google("Fira Mono")
)

ui <- fluidPage(
  theme = solarized_dark,
  titlePanel("S&P 500 Index Viewer (Solarized Dark)"),
  sidebarLayout(
    sidebarPanel(
      dateInput("start", "Start Date", value = Sys.Date() - 365),
      dateInput("end", "End Date", value = Sys.Date()),
      actionButton("update", "Update Chart")
    ),
    mainPanel(
      dygraphOutput("sp500_plot")
    )
  )
)

# Server
server <- function(input, output, session) {
  sp500_data <- eventReactive(input$update, {
    getSymbols("^GSPC", src = "yahoo", from = input$start, to = input$end, auto.assign = FALSE)
  }, ignoreNULL = FALSE)

  output$sp500_plot <- renderDygraph({
    data <- sp500_data()
    dygraph(Cl(data), main = "S&P 500 Closing Price") %>%
      dyOptions(colors = "#b58900", gridLineColor = "#073642", axisLineColor = "#586e75", axisLabelColor = "#93a1a1", fillGraph = TRUE)
  })
}

# Run the app
shinyApp(ui, server)
