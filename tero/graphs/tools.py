from langchain_core.tools import tool
from tero.functions.docs import automate_broker_docs, alerts_docs, strategy_install_and_setup_docs

@tool
def how_to_create_and_write_tradingview_alert():
    """
    Builds the Alerts documentation section by rendering multiple HTML templates,
    converting them to markdown, and composing a single markdown string with helpful links.

    Args:
        None

    Returns:
        str: A formatted markdown block containing the Alerts introduction, placeholders,
             creation guide, and playground sections, each followed by a "Read More" link.
    """
    return alerts_docs()

@tool
def how_to_link_broker_context(broker_name: str):
    """
    Loads the documentation for linking a broker account, converts it to markdown format,
    and returns a formatted instruction guide for the specified broker.

    Args:
        broker_name (str): The name of the broker for which to load the documentation.

        Available options include:
            - binance
            - binanceus
            - bitget
            - bybit
            - mexc
            - bingx
            - bitmart
            - kucoin
            - coinbase
            - crypto
            - metatrader4
            - metatrader5
            - tradelocker

    Returns:
        str: A formatted markdown guide for linking the broker account to IsAlgo,
             or a warning message if no guide is available for the specified broker.
    """

    return automate_broker_docs(broker_name)

@tool
def how_to_install_and_setup_tradingview_strategy():
    """
    Renders and composes the documentation sections for strategy installation, setup, and result sharing.
    This function loads the relevant HTML templates for each topic, converts them to markdown format,
    and returns a single formatted markdown guide containing instructions and helpful links.

    Args:
        None

    Returns:
        str: A markdown-formatted string containing installation, setup, and sharing documentation
             for strategies, each section followed by a relevant link for more details.
    """

    return strategy_install_and_setup_docs()