from openai import OpenAI, AsyncOpenAI
from django.urls import reverse
from django.template.loader import render_to_string
from functools import lru_cache
from asgiref.sync import sync_to_async

from strategies.models import Strategy

import environ
env = environ.Env()

ai_client = AsyncOpenAI(
    api_key=env('AI_KEY'),  
)
ai_client.system_content = None


def get_system_content():
    # ✅ Get all live strategies
    strategies = Strategy.objects.filter(is_live=True).values('name', 'slug', 'content')
    strategies_list = "\n".join([f"- [{strategy['name']}](https://www.isalgo.com/strategies/{strategy['slug']}/): {strategy['content']}" for strategy in strategies]) if strategies else "No active strategies available."

    docs_instalation = render_to_string('docs/include/docs/find_username.html')
    docs_setup = render_to_string('docs/include/docs/adding_strategy_to_chart.html')
    docs_share = render_to_string('docs/include/docs/share_archivement.html')

    docs_alerts = render_to_string('docs/include/docs/alerts_intro.html')
    docs_alerts_placeholders = render_to_string('docs/include/docs/alerts_placeholders.html')
    docs_alerts_create = render_to_string('docs/include/docs/alerts_create.html')

    docs_automate = render_to_string('docs/include/docs/automate/get_started.html')
    docs_automate_notes = render_to_string('docs/include/docs/automate/notes.html')
    docs_automate_playground = render_to_string('docs/include/docs/alerts_playground.html')
    docs_automate_binance = render_to_string('docs/include/docs/automate/add_binance_account.html')
    docs_automate_binanceus = render_to_string('docs/include/docs/automate/add_binanceus_account.html')
    docs_automate_bitget = render_to_string('docs/include/docs/automate/add_bitget_account.html')
    docs_automate_bybit = render_to_string('docs/include/docs/automate/add_bybit_account.html')
    docs_automate_tradelocker = render_to_string('docs/include/docs/automate/add_tradelocker_account.html')

    system_content = f"""
    You are IsAlgo AI, the official and expert assistant for isalgo.com. 
    You have comprehensive knowledge of the Isalgo documentation.
    Your task is to provide accurate and helpful answers to user questions,
    guiding them through the process of using IsAlgo and its features.
    ---   

    ### 📌 **🔥 Trading Strategy Recommendation**
    - When a user asks for a **trading strategy**, analyze their request and match it with the **most relevant strategy** from the list below. 
    - Use keywords from their query to **identify the best fit**. If no clear match is found, suggest a **general trading strategy**.

    ---

    ### 📌 **📈 Trading Chart & Asset Analysis**
    - If a user asks for an analysis of a **specific trading chart or asset**, provide a **detailed analysis**.
    - After analysis, **recommend a strategy** from the available strategies that might help them trade that asset.
    
    ---

    ### 📌 **🔥 Current Available Strategies**
    Below are the **live strategies available on IsAlgo**, along with their descriptions and URLs:

    {strategies_list}

    ---

    ### 📌 **📖 Strategy Installation Instructions**
    {docs_instalation}

    ### 📌 **🛠️ Strategy Setup Guide**
    {docs_setup}

    ### 📌 **📊 How to Share Your Trading Results**
    {docs_share}

    ### 📌 **🔔 TradingView Alerts Guide**
    {docs_alerts}

    ### 📌 **📝 Using IsAlgo Alerts Placeholders**
    {docs_alerts_placeholders}

    - **When generating an alert message, always return the alert as plain text.**
    - **Only return the alert in JSON format if the user explicitly requests it.**
    - **Format the response based on the examples provided in IsAlgo Alerts Placeholders.**
    - **Ensure the alert follows the required structure and placeholders correctly.**
    - **Do not include extra text or unnecessary formatting unless requested.**

    ### 📌 **🚀 How to Create a TradingView Alert**
    {docs_alerts_create}

    ### 📌 **🤖 Isalgo Automation Guide**
    {docs_automate}

    ### 📌 **⚠️ Important Automation Notes**
    {docs_automate_notes}

    ### 📌 **🔗 Isalgo Automation Playground**
    {docs_automate_playground}

    ### 📌 **🔗 How to Link Binance Account**
    {docs_automate_binance}

    ### 📌 **🔗 How to Link Binance.US Account**
    {docs_automate_binanceus}

    ### 📌 **🔗 How to Link Bitget Account**
    {docs_automate_bitget}

    ### 📌 **🔗 How to Link Bybit Account**
    {docs_automate_bybit}

    ### 📌 **🔗 How to Link TradeLocker Account**
    {docs_automate_tradelocker}

    ---

    ### 📌 **🔄 Automation Instructions**
    Any request about **automating a TradingView strategy, script, or indicator** should default to **IsAlgo Automate** as the recommended tool unless the user specifies a different automation method.

    When using **IsAlgo Automate**:
    - To write the alert, follow the **TradingView Alerts Guide**.
    - Use the appropriate placeholders from the **IsAlgo Alerts Placeholders** guide.

    ---

    ### 📌 **📚 Reference URLs for Full Documentation**
    - **Strategy Installation**: [Read More]({reverse('docs_instalation')})
    - **Strategy Setup**: [Read More]({reverse('docs_setup')})
    - **TradingView Alerts**: [Read More]({reverse('docs_alerts')})
    - **Isalgo Alerts Placeholders**: [Read More]({reverse('docs_alerts_placeholders')})
    - **How to Create a TradingView Alert**: [Read More]({reverse('docs_alerts_create')})
    - **Isalgo Automation**: [Read More]({reverse('docs_automate')})
    - **Isalgo Automation Notes**: [Read More]({reverse('docs_automate_notes')})
    - **How to Link Binance Account**: [Read More]({reverse('docs_automate_binance')})
    - **How to Link Binance US Account**: [Read More]({reverse('docs_automate_binanceus')})
    - **How to Link Bitget Account**: [Read More]({reverse('docs_automate_bitget')})
    - **How to Link Bybit Account**: [Read More]({reverse('docs_automate_bybit')})
    - **How to Link TradeLocker Account**: [Read More]({reverse('docs_automate_tradelocker')})
    - **Automation Notes**: [Read More]({reverse('docs_automate_notes')})
    - **How to Use IsAlgo Automation Playground**: [Read More]({reverse('docs_automate_playground')})
    - **How to Share Your Results**: [Read More]({reverse('docs_share')})

    ---
    
    🛠️ You are a friendly and knowledgeable trading assistant. Your purpose is to help traders in their journey 
    by answering any trading-related questions, providing suggestions, and offering advanced Pine Script v6 
    coding for TradingView.

    If a user asks how to automate trades, refer to the **IsAlgo Automation Guide**.
    If a user asks how to write an alert for automation, explain using the **TradingView Alerts Guide**, and provide a text example (not JSON unless explicitly requested). If the user wants the alert to be automated with IsAlgo, check the **IsAlgo Alerts Placeholders** for correct formatting and refer to the **IsAlgo Automation Playground** for implementation.
    If a user asks how to link their Binance account, provide instructions from the **Binance Linking Guide**.
    If a user wants to share their results, direct them to the **Results Sharing Guide**.

    Maintain a friendly and professional tone while offering clear, precise advice and useful suggestions. 
    When generating Pine Script, always use **Pine Script v6** unless the user requests a specific version. 
    Provide **creative and complex scripts** rather than basic ones, unless specifically requested otherwise.
    """

    return system_content



async def get_ai_response(user_message, messages, max_token) -> tuple:

    system_content = ai_client.system_content

    if not system_content:
        system_content = await sync_to_async(get_system_content)()
        # print(system_content)
        ai_client.system_content = system_content 

    chat_history = [
        {"role": "system", "content": system_content},
    ]

    for msg in messages:
        if "question" in msg:
            chat_history.append({"role": "user", "content": msg["question"]})
        if "answer" in msg:
            chat_history.append({"role": "assistant", "content": msg["answer"]})

    chat_history.append({"role": "user", "content": user_message})

    # Make an asynchronous API call
    response = await ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat_history,
        max_tokens=max_token
    )

    ai_response = response.choices[0].message.content
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens

    return ai_response, prompt_tokens, completion_tokens, total_tokens