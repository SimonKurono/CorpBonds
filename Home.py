from utils import ui

ui.set_page_config("Raffles Bond Platform Home", "wide")

ui.section("Welcome to Raffles Bond Platform", "Fixed-income intelligence, unified.", show_rule=True)

ui.kpi_group([
    {"label": "IG OAS", "value": "114 bp"},
    {"label": "2s10s", "value": "-28 bp"},
    {"label": "Sentiment (IG)", "value": "+0.21"},
])

ui.verticalSpace(20)
ui.section("Explore the toolkit", "Everything you need for credit & cross-asset workflows.")
ui.feature_grid([
    {"icon":"📊","title":"Market Dashboard","desc":"Curves, OAS & sector heatmaps at a glance."},
    {"icon":"🧮","title":"Quant / RV","desc":"z-scores, beta/alpha, tracking error, correlations."},
    {"icon":"💼","title":"Portfolio + Benchmarks","desc":"TWR returns, drawdowns; SPY/LQD/HYG one-click."},
    {"icon":"📰","title":"News","desc":"Curated feed with issuer/sector filters + AI summaries."},
    {"icon":"📈","title":"Stats","desc":"Treasuries, OAS/CDS, curve spreads — CSV downloads."},
    {"icon":"🤖","title":"AI Sentiment","desc":"Daily IG/HY scores with confidence & trend."},
], columns=3)
