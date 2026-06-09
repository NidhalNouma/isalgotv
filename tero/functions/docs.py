from bs4 import BeautifulSoup
import html2text

from django.urls import reverse
from django.template.loader import render_to_string

from django.test import RequestFactory
from django.urls import set_urlconf

from strategies.models import Strategy, StrategyResults

def html_to_markdown(html_content):
    # Convert the modified HTML to markdown using html2text
    html_converter = html2text.HTML2Text()
    html_converter.ignore_links = False  # Preserve links
    html_converter.ignore_images = False
    html_converter.body_width = 0        # No forced line breaks

    return html_converter.handle(html_content)

def extract_text_with_media(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    # Replace images with [image](URL)
    for img in soup.find_all("img"):
        src = img.get("src")
        alt = img.get("alt", "Not specified")
        if src:
            img.replace_with(f"![image]({src}) (image for :{alt})")

    # Replace videos with [video](URL)
    for video in soup.find_all("video"):
        for source in video.find_all("source"):
            src = source.get("src")
            if src:
                video.replace_with(f"[Whatch video]({src})")

    # Extract text with replacements
    return soup.get_text(separator="\n", strip=True)
    
def automate_broker_docs(broker_name):
    broker_docs_map = {
        "binance": ("docs/include/docs/automate/add_binance_account.html", "docs_automate_broker_binance"),
        "binanceus": ("docs/include/docs/automate/add_binanceus_account.html", "docs_automate_broker_binanceus"),
        "bitget": ("docs/include/docs/automate/add_bitget_account.html", "docs_automate_broker_bitget"),
        "bybit": ("docs/include/docs/automate/add_bybit_account.html", "docs_automate_broker_bybit"),
        "mexc": ("docs/include/docs/automate/add_mexc_account.html", "docs_automate_broker_mexc"),
        "bingx": ("docs/include/docs/automate/add_bingx_account.html", "docs_automate_broker_bingx"),
        "bitmart": ("docs/include/docs/automate/add_bitmart_account.html", "docs_automate_broker_bitmart"),
        "kucoin": ("docs/include/docs/automate/add_kucoin_account.html", "docs_automate_broker_kucoin"),
        "coinbase": ("docs/include/docs/automate/add_coinbase_account.html", "docs_automate_broker_coinbase"),
        "crypto": ("docs/include/docs/automate/add_crypto_account.html", "docs_automate_broker_crypto"),
        "metatrader4": ("docs/include/docs/automate/add_metatrader4_account.html", "docs_automate_broker_metatrader4"),
        "metatrader5": ("docs/include/docs/automate/add_metatrader5_account.html", "docs_automate_broker_metatrader5"),
        "tradelocker": ("docs/include/docs/automate/add_tradelocker_account.html", "docs_automate_broker_tradelocker"),
        "kraken": ("docs/include/docs/automate/add_kraken_account.html", "docs_automate_broker_kraken"),
        "okx": ("docs/include/docs/automate/add_okx_account.html", "docs_automate_broker_okx"),
        "apex": ("docs/include/docs/automate/add_apex_account.html", "docs_automate_broker_apex"),
        "hyperliquid": ("docs/include/docs/automate/add_hyperliquid_account.html", "docs_automate_broker_hyperliquid"),
        "ctrader": ("docs/include/docs/automate/add_ctrader_account.html", "docs_automate_broker_ctrader"),
        "deriv": ("docs/include/docs/automate/add_deriv_account.html", "docs_automate_broker_deriv"),
        "hankotrade": ("docs/include/docs/automate/add_hankotrade_account.html", "docs_automate_broker_hankotrade"),
        "alpaca": ("docs/include/docs/automate/add_alpaca_account.html", "docs_automate_broker_alpaca"),
        "tastytrade": ("docs/include/docs/automate/add_tastytrade_account.html", "docs_automate_broker_tastytrade"),
        "bitmex": ("docs/include/docs/automate/add_bitmex_account.html", None),
        "dxtrade": ("docs/include/docs/automate/add_dxtrade_account.html", None),
        "ninjatrader": ("docs/include/docs/automate/add_ninjatrader_account.html", None),
    }

    if broker_name not in broker_docs_map:
        return f"⚠️ No automation guide available for broker: {broker_name}"

    template_path, reverse_name = broker_docs_map[broker_name]

    request = RequestFactory().get("/")
    set_urlconf('main_app.urls')

    try:
        doc_content = render_to_string(template_path, request=request)
    finally:
        set_urlconf(None)

    markdown_content = html_to_markdown(doc_content)

    if reverse_name:
        return f"""
        ### 🔗 How to Link a {broker_name.capitalize()} Account to IsAlgo
        {markdown_content}
        Link {broker_name.capitalize()} Account: [Read More]({reverse(reverse_name)})
        """
    else:
        return f"""
        ### 🔗 How to Link a {broker_name.capitalize()} Account to IsAlgo
        {markdown_content}
        """

def alerts_docs():
    request = RequestFactory().get("/")
    set_urlconf('main_app.urls')

    try:
        docs_alerts = render_to_string('docs/include/docs/alerts_intro.html', request=request)
        docs_alerts_placeholders = render_to_string('docs/include/docs/alerts_placeholders.html', request=request)
        docs_alerts_create = render_to_string('docs/include/docs/alerts_create.html', request=request)

        docs_automate_playground = render_to_string('docs/include/docs/alerts_playground.html', request=request)
    finally:
        set_urlconf(None)

    return f"""
        ### 🚨 Alerts Guide
        {html_to_markdown(docs_alerts)}
        For more details checkout this link: [Read More]({reverse('docs_alerts')})

        ### 📝 Alerts Placeholders
        {html_to_markdown(docs_alerts_placeholders)}
        For more details checkout this link: [Read More]({reverse('docs_alerts_placeholders')})
        
        ### 🔔 Create a TradingView Alert
       {html_to_markdown(docs_alerts_create)} 

        When creating an alert:
            - Always return the alert as plain text.
            - Only use JSON format if the user explicitly asks for it.
            - Follow the examples provided in the alerts placeholders.
            - Ensure the alert follows the required structure and placeholders exactly.
            - Do not include any extra text or formatting unless requested.
        For more details checkout this link: [Read More]({reverse('docs_alerts_create')})


        ### 🕹️ Isalgo Automation Playground
        {html_to_markdown(docs_automate_playground)}
        For more details checkout this link: [Read More]({reverse('docs_automate_playground')})
    """
    
def strategy_install_and_setup_docs():
    request = RequestFactory().get("/")
    set_urlconf('main_app.urls')

    try:
        docs_instalation = render_to_string('docs/include/docs/find_username.html', request=request)
        docs_setup = render_to_string('docs/include/docs/adding_strategy_to_chart.html', request=request)
        docs_share = render_to_string('docs/include/docs/share_archivement.html', request=request)
    finally:
        set_urlconf(None)

    return f"""
        ### 🛠️ Strategy Installation Instructions
        {html_to_markdown(docs_instalation)}
        For more details checkout this link: [Read More]({reverse('docs_instalation')})

        ### ⚙️ Strategy Setup Guide
        {html_to_markdown(docs_setup)}
        For more details checkout this link: [Read More]({reverse('docs_setup')})


        ### 📤 Strategy Result Sharing
        {html_to_markdown(docs_share)}
        For more details checkout this link: [Read More]({reverse('docs_share')})
    """


def get_strategies_info():
    strategies = Strategy.objects.all()
    if not strategies:
        return "No active strategies available."

    strategies_list = "\n".join([
        f"- [{s.name}](https://www.isalgo.com/strategies/{s.slug}/): {s.content}\n  Strategy settings:\n  {s.settings_to_text()}\n"
        for s in strategies
    ])
    return f"## Current Available Strategies\n{strategies_list}"


def get_best_results_info():
    best_results = StrategyResults.objects.all().order_by('-created_at')[:4]
    if not best_results:
        return "No results available."

    results_list = "\n".join([
        f"- [Result for {r.strategy.name}](https://www.isalgo.com/strategies/{r.strategy.slug}/?result={r.id}):\n  Performance: {r.performance_to_text()}\n  Settings: {r.settings_to_text()}\n"
        for r in best_results
    ])
    return f"## Best Trading Results\n{results_list}"


def get_automation_guide():
    request = RequestFactory().get("/")
    set_urlconf('main_app.urls')

    try:
        docs_automate = render_to_string('docs/include/docs/automate/get_started.html', request=request)
        docs_automate_notes = render_to_string('docs/include/docs/automate/notes.html', request=request)
    finally:
        set_urlconf(None)

    return f"""## Automation Guide
{html_to_markdown(docs_automate)}
For more details: [Read More]({reverse('docs_automate')})

## Important Automation Notes
{html_to_markdown(docs_automate_notes)}
For more details: [Read More]({reverse('docs_automate_notes')})"""


def get_system_content():
    strategies = Strategy.objects.all()

    strategies_list = "<br/>".join([
        f"- [{strategy.name}](https://www.isalgo.com/strategies/{strategy.slug}/): {strategy.content} <br/> Strategy settings:<br/><br/> {strategy.settings_to_text()} <br/><br/>"
        for strategy in strategies
    ]) if strategies else "No active strategies available."

    best_results = StrategyResults.objects.all().order_by('-created_at')[:4]
    best_results_list = "<br/>".join([
        f"- [Result link for {result.strategy.name}](https://www.isalgo.com/strategies/{result.strategy.slug}/?result={result.id}):  <br/><br/> Result performance:<br/> {result.performance_to_text()} <br/> Result settings:<br/> {result.settings_to_text()} <br/><br/>"
        for result in best_results
    ]) if best_results else "No results available." 

    request = RequestFactory().get("/")
    set_urlconf('main_app.urls') 

    try:
        docs_automate = render_to_string('docs/include/docs/automate/get_started.html', request=request)
        docs_automate_notes = render_to_string('docs/include/docs/automate/notes.html', request=request)
        docs_automate_playground = render_to_string('docs/include/docs/alerts_playground.html', request=request)
    finally:
        set_urlconf(None)

    system_content = f"""
        ---
        ## 📈 CURRENT AVAILABLE STRATEGIES
        ### Description:
        The live strategies on Isalgo are listed below, complete with descriptions and URLs:

        {html_to_markdown(strategies_list)}

        ---
        ## 🏆 BEST TRADING RESULTS
        ### Description:
        The top trading results on Isalgo, along with performance details, settings, and URLs, are listed here:

        {html_to_markdown(best_results_list)}

        ---
        ## 📚 DOCUMENTATION AND GUIDES

        {strategy_install_and_setup_docs()}

        {alerts_docs()}

        ### 🤖 Isalgo Automation Guide
        {html_to_markdown(docs_automate)}
        For more details checkout this link: [Read More]({reverse('docs_automate')})
        ### ⚠️ Important Automation Notes
        {html_to_markdown(docs_automate_notes)}
        For more details checkout this link: [Read More]({reverse('docs_automate_notes')})
        ### 🕹️ Isalgo Automation Playground
        {html_to_markdown(docs_automate_playground)}
        For more details checkout this link: [Read More]({reverse('docs_automate_playground')})

        {automate_broker_docs('binance')}

        {automate_broker_docs('binanceus')}

        {automate_broker_docs('bitget')}

        {automate_broker_docs('bybit')}

        {automate_broker_docs('mexc')}

        {automate_broker_docs('bingx')}

        {automate_broker_docs('bitmart')}

        {automate_broker_docs('kucoin')}

        {automate_broker_docs('coinbase')}

        {automate_broker_docs('crypto')}

        {automate_broker_docs('metatrader4')}

        {automate_broker_docs('metatrader5')}

        {automate_broker_docs('tradelocker')}

        {automate_broker_docs('kraken')}

        {automate_broker_docs('okx')}

        {automate_broker_docs('apex')}

        {automate_broker_docs('hyperliquid')}

        {automate_broker_docs('ctrader')}

        {automate_broker_docs('deriv')}

        {automate_broker_docs('hankotrade')}

        {automate_broker_docs('alpaca')}

        {automate_broker_docs('tastytrade')}

        {automate_broker_docs('bitmex')}

        {automate_broker_docs('dxtrade')}

        {automate_broker_docs('ninjatrader')}
    """
    
    return system_content