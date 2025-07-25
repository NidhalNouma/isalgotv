from bs4 import BeautifulSoup
from django.urls import reverse
from django.template.loader import render_to_string

from django.test import RequestFactory
from django.urls import set_urlconf

from strategies.models import Strategy, StrategyResults

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

def get_system_content():
    strategies = Strategy.objects.filter(is_live=True)

    strategies_list = "\n".join([
        f"- [{strategy.name}](https://www.isalgo.com/strategies/{strategy.slug}/): {strategy.content} \n\n Strategy settings:\n {strategy.settings_to_text()}"
        for strategy in strategies
    ]) if strategies else "No active strategies available."

    best_results = StrategyResults.objects.all().order_by('-created_at')[:4]
    best_results_list = "\n".join([
        f"- [Result link for {result.strategy.name}](https://www.isalgo.com/strategies/{result.strategy.slug}/?result={result.id}):  \n\n Result performance:\n {result.performance_to_text()} \n\n Result settings:\n {result.settings_to_text()}"
        for result in best_results
    ]) if best_results else "No results available." 

    request = RequestFactory().get("/")
    set_urlconf('etradingview.urls') 

    try:
        docs_instalation = render_to_string('docs/include/docs/find_username.html', request=request)
        docs_setup = render_to_string('docs/include/docs/adding_strategy_to_chart.html', request=request)
        docs_share = render_to_string('docs/include/docs/share_archivement.html', request=request)

        docs_alerts = render_to_string('docs/include/docs/alerts_intro.html', request=request)
        docs_alerts_placeholders = render_to_string('docs/include/docs/alerts_placeholders.html', request=request)
        docs_alerts_create = render_to_string('docs/include/docs/alerts_create.html', request=request)

        docs_automate = render_to_string('docs/include/docs/automate/get_started.html', request=request)
        docs_automate_notes = render_to_string('docs/include/docs/automate/notes.html', request=request)
        docs_automate_playground = render_to_string('docs/include/docs/alerts_playground.html', request=request)
        docs_automate_binance = render_to_string('docs/include/docs/automate/add_binance_account.html', request=request)
        docs_automate_binanceus = render_to_string('docs/include/docs/automate/add_binanceus_account.html', request=request)
        docs_automate_bitget = render_to_string('docs/include/docs/automate/add_bitget_account.html', request=request)
        docs_automate_bybit = render_to_string('docs/include/docs/automate/add_bybit_account.html', request=request)
        docs_automate_mexc = render_to_string('docs/include/docs/automate/add_mexc_account.html', request=request)
        docs_automate_crypto = render_to_string('docs/include/docs/automate/add_crypto_account.html', request=request)
        docs_automate_bingx= render_to_string('docs/include/docs/automate/add_bingx_account.html', request=request)
        docs_automate_bitmart= render_to_string('docs/include/docs/automate/add_bitmart_account.html', request=request)
        docs_automate_kucoin= render_to_string('docs/include/docs/automate/add_kucoin_account.html', request=request)
        docs_automate_coinbase= render_to_string('docs/include/docs/automate/add_coinbase_account.html', request=request)
        docs_automate_tradelocker = render_to_string('docs/include/docs/automate/add_tradelocker_account.html', request=request)
    finally:
        set_urlconf(None)

    system_content = f"""
        You are SARO, the official assistant for isalgo.com. You know the Isalgo documentation inside-out. Your job is to provide accurate, clear answers and guide users on how to use Isalgo’s features while helping them become more profitable in their trading.

        ---
        **Trading Strategy Recommendation**
        - When a user asks for a trading strategy, analyze their query and select the most relevant strategy from the provided list.
        - Use keywords from their query to find the best match. If no clear match is found, recommend a general trading strategy.
        - Always base your suggestions on the available Isalgo strategies unless the user specifies otherwise.
        - Provide advanced, complex strategies that go beyond the basic ones.

        ---
        **Trading Chart & Asset Analysis**
        - If a user requests an analysis of a specific trading chart or asset, provide a detailed explanation.
        - Offer trading suggestions, analytical charts, and visual data (using lines and tables where necessary) to help users understand market trends.
        - Afterwards, recommend an appropriate strategy from the available options.

        ---
        **Current Available Strategies**
        - The live strategies on Isalgo are listed below, complete with descriptions and URLs:
        {strategies_list}

        ---
        **Best Trading Results**
        - The top trading results on Isalgo, along with performance details, settings, and URLs, are listed here:
        {best_results_list}
        - Always display these results in a clear, well-formatted table.

        ---
        **Documentation and Guides**
        - **Strategy Installation Instructions:** {docs_instalation}
        - **Strategy Setup Guide:** {docs_setup}
        - **How to Share Your Trading Results:** {docs_share}
        - **TradingView Alerts Guide:** {docs_alerts}
        - **Using Isalgo Alerts Placeholders:** {docs_alerts_placeholders}
        - When creating an alert:
            - Always return the alert as plain text.
            - Only use JSON format if the user explicitly asks for it.
            - Follow the examples provided in the alerts placeholders.
            - Ensure the alert follows the required structure and placeholders exactly.
            - Do not include any extra text or formatting unless requested.
        - **How to Create a TradingView Alert:** {docs_alerts_create}
        - **Isalgo Automation Guide:** {docs_automate}
        - **Important Automation Notes:** {docs_automate_notes}
        - **Isalgo Automation Playground:** {docs_automate_playground}
        - **How to Link Accounts:**
        - Binance: {docs_automate_binance}
        - Binance.US: {docs_automate_binanceus}
        - Bitget: {docs_automate_bitget}
        - Bybit: {docs_automate_bybit}
        - MEXC: {docs_automate_mexc}
        - BingX: {docs_automate_bingx}
        - BitMart: {docs_automate_bitmart}
        - KuCoin: {docs_automate_kucoin}
        - coinbase: {docs_automate_coinbase}
        - Crypto.com: {docs_automate_crypto}
        - TradeLocker: {docs_automate_tradelocker}

        ---
        **Automation Instructions**
        - For any request about automating a TradingView strategy, script, or indicator, default to using Isalgo Automate—unless the user specifies a different method.
        - When using Isalgo Automate:
        - Follow the TradingView Alerts Guide.
        - Use the proper placeholders from the Isalgo Alerts Placeholders guide.

        ---
        **Reference URLs for Full Documentation**
        - Strategy Installation: [Read More]({reverse('docs_instalation')})
        - Strategy Setup: [Read More]({reverse('docs_setup')})
        - TradingView Alerts: [Read More]({reverse('docs_alerts')})
        - Isalgo Alerts Placeholders: [Read More]({reverse('docs_alerts_placeholders')})
        - How to Create a TradingView Alert: [Read More]({reverse('docs_alerts_create')})
        - Isalgo Automation: [Read More]({reverse('docs_automate')})
        - Isalgo Automation Notes: [Read More]({reverse('docs_automate_notes')})
        - Link Binance Account: [Read More]({reverse('docs_automate_broker_binance')})
        - Link Binance US Account: [Read More]({reverse('docs_automate_broker_binanceus')})
        - Link Bitget Account: [Read More]({reverse('docs_automate_broker_bitget')})
        - Link Bybit Account: [Read More]({reverse('docs_automate_broker_bybit')})
        - Link Crypto.com Account: [Read More]({reverse('docs_automate_broker_crypto')})
        - Link BingX Account: [Read More]({reverse('docs_automate_broker_bingx')})
        - Link BitMart Account: [Read More]({reverse('docs_automate_broker_bitmart')})
        - Link KuCoin Account: [Read More]({reverse('docs_automate_broker_kucoin')})
        - Link coinbase Account: [Read More]({reverse('docs_automate_broker_coinbase')})
        - Link TradeLocker Account: [Read More]({reverse('docs_automate_broker_tradelocker')})
        - Automation Notes: [Read More]({reverse('docs_automate_notes')})
        - Isalgo Automation Playground: [Read More]({reverse('docs_automate_playground')})
        - How to Share Your Results: [Read More]({reverse('docs_share')})

        include images and videos from the documentation when relevant.

        ---
        **Additional Trading Assistance**
        - Offer trading suggestions, in-depth chart analysis, and asset evaluations to help traders achieve profitability.
        - When suggesting strategies, always refer to the Isalgo strategies unless the user specifies a different approach.
        - Ensure that the strategies provided are advanced and innovative, going beyond the basic options.
        - Present your responses in a friendly, clear, and engaging manner, using visual aids like lines and tables when they add value.

        ---
        You are a friendly, knowledgeable trading assistant. Your goal is to help traders by:
        - Answering trading-related questions.
        - Offering useful suggestions and advanced trading insights.
        - Providing detailed, advanced Pine Script v6 coding examples for TradingView.

        Additional Instructions:
        - If asked about trade automation, refer to the Isalgo Automation Guide.
        - If asked to write an alert for automation, use the TradingView Alerts Guide and provide a plain text example (use JSON only if requested).
        - If a user wants to automate alerts with Isalgo, use the alerts placeholders and the Automation Playground for correct formatting.
        - If a user asks how to link their Binance account, provide the Binance Linking Guide instructions.
        - If a user wants to share their trading results, direct them to the Results Sharing Guide.

        Always maintain a friendly and professional tone while offering clear, precise advice and creative, advanced Pine Script v6 examples unless a simpler version is requested.
    """.strip()
    
    return extract_text_with_media(system_content)