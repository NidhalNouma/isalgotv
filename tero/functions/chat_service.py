from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.messages import ToolMessage
from langchain.callbacks import get_openai_callback
from langchain_core.tools import tool

from .docs import (
    automate_broker_docs,
    alerts_docs,
    strategy_install_and_setup_docs,
    get_strategies_info,
    get_best_results_info,
    get_automation_guide,
)
from .accounts import (
    get_automate_account,
    get_saved_trade_info,
    get_saved_open_trades,
    get_account_balance,
    get_symbol_info,
    get_current_price,
    get_available_trading_pairs,
    get_order_book_data,
    get_market_candles,
    open_trade_for_account,
    close_trade_for_account,
    get_order_info_for_account,
)


# ── Tool definitions ──


@tool
def get_broker_setup_guide(broker_name: str) -> str:
    """Get the setup guide for linking a specific broker account to IsAlgo.
    Use this when the user asks how to connect, link, or set up a broker account.

    Available brokers: binance, binanceus, bitget, bybit, mexc, bingx, bitmart,
    kucoin, coinbase, crypto, metatrader4, metatrader5, tradelocker, kraken, okx,
    apex, hyperliquid, ctrader, deriv, hankotrade, alpaca, tastytrade, bitmex,
    dxtrade, ninjatrader.
    """
    return automate_broker_docs(broker_name.lower().strip())


@tool
def get_alerts_guide() -> str:
    """Get the complete TradingView alerts documentation including how to create alerts,
    alert placeholders, and the alerts playground. Use this when the user asks about
    alerts, webhooks, alert messages, or alert placeholders."""
    return alerts_docs()


@tool
def get_strategy_install_guide() -> str:
    """Get documentation on how to install strategies on TradingView, add them to charts,
    and share achievements. Use this when the user asks about installing, setting up,
    or adding a strategy to their TradingView chart."""
    return strategy_install_and_setup_docs()


@tool
def get_available_strategies() -> str:
    """Get the list of all currently available trading strategies on IsAlgo with their
    descriptions, settings, and URLs. Use this when the user asks about available
    strategies, what strategies exist, or wants strategy recommendations."""
    return get_strategies_info()


@tool
def get_best_trading_results() -> str:
    """Get the top recent trading results on IsAlgo with performance details and settings.
    Use this when the user asks about best results, trading performance, or wants to see
    how strategies have performed."""
    return get_best_results_info()


@tool
def get_automation_getting_started() -> str:
    """Get the IsAlgo automation getting started guide and important notes.
    Use this when the user asks about trade automation, how automation works,
    or how to get started with automated trading on IsAlgo."""
    return get_automation_guide()


# Documentation-only tools (no account needed)
DOCUMENTATION_TOOLS = [
    get_broker_setup_guide,
    get_alerts_guide,
    get_strategy_install_guide,
    get_available_strategies,
    get_best_trading_results,
    get_automation_getting_started,
]

SYSTEM_PROMPT = (
    "You are TERO, the official AI assistant for isalgo.com \u2014 a platform for "
    "automated trading strategies on TradingView.\n\n"
    "Your role:\n"
    "- Help users understand and use IsAlgo's features\n"
    "- Guide users on linking broker accounts, setting up strategies, creating alerts, "
    "and automating trades\n"
    "- Provide accurate information from IsAlgo's documentation\n"
    "- Retrieve live market data and account information when requested\n"
    "- Help users become more profitable in their trading\n\n"
    "Important rules:\n"
    "- Always use your tools to fetch relevant documentation before answering questions "
    "about brokers, strategies, alerts, automation, or setup\n"
    "- When a user has a broker account selected, use broker tools to get live data:\n"
    "  * Account balance and wallet information\n"
    "  * Current prices for specific symbols\n"
    "  * Symbol specifications and trading requirements\n"
    "  * Available trading pairs\n"
    "  * Market depth (order book)\n"
    "  * Historical candlestick data for analysis\n"
    "  * Open, close, and manage trades\n"
    "- Display images if they are relevant to the question and the retrieved context\n"
    "- When creating an alert, return it as plain text unless the user explicitly asks "
    "for JSON format\n"
    "- Be helpful, concise, and accurate\n"
    "- If you're unsure about something, say so rather than guessing\n\n"
    "You have access to tools that let you look up:\n"
    "- Broker setup guides (for all supported brokers)\n"
    "- TradingView alerts documentation\n"
    "- Strategy installation instructions\n"
    "- Available strategies list\n"
    "- Best trading results\n"
    "- Automation getting started guide\n"
    "- Live broker data (when account is connected):\n"
    "  * Account balance\n"
    "  * Symbol information and specifications\n"
    "  * Current market prices\n"
    "  * Available trading pairs\n"
    "  * Order book data\n"
    "  * Historical candle data for technical analysis\n"
    "  * Open and close trades\n"
    "  * Order information lookup"
)


class ChatService:
    def __init__(
        self,
        model_name: str = "gpt-4.1",
        temperature: float = 0.5,
    ):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.account = None
        self.tools = DOCUMENTATION_TOOLS
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def _create_account_aware_tools(self, account):
        """Create account-aware tool functions for broker operations."""
        tools = []

        @tool
        def get_account_balance_tool() -> str:
            """Get the current account balance including available balance,
            used/locked balance, and total balance in the broker currency.
            Use this when the user asks about their account balance."""
            try:
                balance = get_account_balance(account)
                return str(balance)
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def get_symbol_info_tool(symbol: str) -> str:
            """Get detailed information about a trading symbol including
            minimum order size, maximum order size, price precision, and quantity precision.
            Example symbols: BTC/USDT, ETH/USDT, EUR/USD
            Use this when the user asks about symbol specs or trading requirements."""
            try:
                info = get_symbol_info(account, symbol)
                return str(info)
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def get_price_tool(symbol: str) -> str:
            """Get the current market price for a specific trading symbol.
            Example: BTC/USDT, ETH/USDT
            Use this when the user asks for current price or market data."""
            try:
                price = get_current_price(account, symbol)
                return f"{symbol} current price: {price}"
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def get_trading_pairs_tool() -> str:
            """Get the list of all available trading pairs on this broker.
            Use this when the user asks what symbols are available to trade."""
            try:
                pairs = get_available_trading_pairs(account)
                if isinstance(pairs, list):
                    return f"Available pairs: {', '.join(pairs[:20])}{'... and more' if len(pairs) > 20 else ''}"
                return str(pairs)
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def get_order_book_tool(symbol: str, limit: int = 20) -> str:
            """Get the current order book (bid/ask levels) for a trading symbol.
            Shows current market depth with buy and sell orders.
            Example: BTC/USDT with limit of 20
            Use this when the user wants to see market depth or liquidity."""
            try:
                order_book = get_order_book_data(account, symbol, limit)
                return str(order_book)
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def get_candles_tool(symbol: str, interval: str, limit: int = 100) -> str:
            """Get historical candlestick data for technical analysis.
            Intervals: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
            Limit: number of candles to retrieve (max 500)
            Example: BTC/USDT, 1h, 100
            Use this when the user wants historical price data or technical analysis."""
            try:
                candles = get_market_candles(account, symbol, interval, limit)
                return str(candles)
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def open_trade_tool(symbol: str, side: str, quantity: float, custom_id: str = None) -> str:
            """Open a new trade on the broker.
            symbol: trading pair (e.g. BTC/USDT)
            side: 'BUY' to go long, 'SELL' to go short
            quantity: amount to trade
            custom_id: optional custom order identifier
            Use this when the user asks to open, place, or enter a trade."""
            try:
                result = open_trade_for_account(account, symbol, side, quantity, custom_id)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def close_trade_tool(symbol: str, side: str, quantity: float) -> str:
            """Close an existing open trade position on the broker.
            symbol: trading pair (e.g. BTC/USDT)
            side: 'SELL' to close a long, 'BUY' to close a short
            quantity: amount to close
            Use this when the user asks to close, exit, or cancel a position."""
            try:
                result = close_trade_for_account(account, symbol, side, quantity)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def get_order_info_tool(symbol: str, order_id: str) -> str:
            """Get detailed information for a specific order by its order ID.
            symbol: trading pair (e.g. BTC/USDT)
            order_id: the broker order ID to look up
            Returns order status, fill price, volume, fees, and profit/loss.
            Use this when the user asks about a specific order or trade by ID."""
            try:
                result = get_order_info_for_account(account, symbol, order_id)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def get_saved_trade_info_tool(trade_id: Optional[int] = None) -> str:
            """Get saved trade information from IsAlgo database.
            trade_id: optional numeric ID of the trade record.
            If trade_id is not provided, returns all currently open saved trades for this account.
            Use this when the user asks about saved/open DB trades with or without a specific ID."""
            try:
                if trade_id is None:
                    result = get_saved_open_trades(account)
                    return str(result)
                result = get_saved_trade_info(trade_id)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def get_saved_open_trades_tool() -> str:
            """Get currently open trades saved in IsAlgo database for the selected account.
            Use this when the user asks for all open/saved DB trades for this account."""
            try:
                result = get_saved_open_trades(account)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        tools = [
            get_account_balance_tool,
            get_symbol_info_tool,
            get_price_tool,
            get_trading_pairs_tool,
            get_order_book_tool,
            get_candles_tool,
            open_trade_tool,
            close_trade_tool,
            get_order_info_tool,
            get_saved_trade_info_tool,
            get_saved_open_trades_tool,
        ]
        return tools

    def _build_tool_map(self, tools):
        """Build a map of tool names to tool functions."""
        tool_map = {t.name: t for t in tools}
        return tool_map

    def stream_response(
        self,
        user_question: str,
        message_history: List[Dict[str, str]],
        token_tracker: Optional[dict] = None,
        msg_context: Optional[dict] = None,
    ):
        """Stream AI response with tool-calling support.

        The model decides which docs functions and broker functions to call based on the user's
        question. Tool results are fed back so the model can compose an
        answer grounded in the retrieved documentation or live broker data.
        """
        system_prompt = SYSTEM_PROMPT
        
        # Determine which tools to use
        current_tools = list(DOCUMENTATION_TOOLS)
        account = None

        if msg_context and msg_context.get("account"):
            acct_data = msg_context["account"]
            
            # Extract account_id and broker_type from context.
            # Support both legacy and current payload keys sent by frontend.
            account_id = None
            broker_type = None
            if isinstance(acct_data, dict):
                account_id = acct_data.get("account_id") or acct_data.get("id")
                broker_type = acct_data.get("broker_type") or acct_data.get("broker")
            
            # Resolve selected account if we have at least an id.
            if account_id:
                account = get_automate_account(account_id, broker_type)
            
            # Extract display information for system prompt
            account_name = acct_data.get("name", "Unknown") if isinstance(acct_data, dict) else "Unknown"
            
            system_prompt += (
                f"\n\nThe user currently has the broker account "
                f"\"{account_name}\" (broker: {broker_type or 'unknown'}) "
                f"selected. When relevant, tailor your answers to this broker. "
                f"You have access to live market data and trading tools for this account.\n"
                f"- Use get_account_balance_tool to check the account balance\n"
                f"- Use get_symbol_info_tool to get symbol specifications\n"
                f"- Use get_price_tool to get current market prices\n"
                f"- Use get_trading_pairs_tool to see available trading pairs\n"
                f"- Use get_order_book_tool to view market depth\n"
                f"- Use get_candles_tool to get historical price data for analysis\n"
                f"- Use open_trade_tool to open a new trade (requires symbol, side, quantity)\n"
                f"- Use close_trade_tool to close an existing position (requires symbol, side, quantity)\n"
                f"- Use get_order_info_tool to get details for a specific order by ID\n"
                f"- Use get_saved_trade_info_tool with trade_id when the user provides a specific trade ID\n"
                f"- If no trade ID is provided, use get_saved_open_trades_tool (or get_saved_trade_info_tool without trade_id)"
            )
            
            # Add account-aware tools if account object was successfully retrieved
            if account is not None:
                account_tools = self._create_account_aware_tools(account)
                current_tools.extend(account_tools)

        # Bind the current set of tools to the LLM
        llm_with_tools = self.llm.bind_tools(current_tools)
        tool_map = self._build_tool_map(current_tools)

        messages = [SystemMessage(content=system_prompt)]

        for msg in message_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_question))

        max_tool_rounds = 5
        response_complete = False
        final_attempt = False

        with get_openai_callback() as cb:
            for round_num in range(max_tool_rounds):
                collected = None
                has_content = False

                try:
                    # Emit "thinking" state before streaming
                    yield "<|AGENT_STATE:thinking|>"
                    
                    for chunk in llm_with_tools.stream(messages):
                        if collected is None:
                            collected = chunk
                        else:
                            collected = collected + chunk

                        if chunk.content:
                            has_content = True
                            yield chunk.content

                    # If we got no response at all, something went wrong
                    if collected is None:
                        if not final_attempt:
                            # Try to get a fallback response
                            yield "\n\nI encountered an issue processing your request. Let me try once more..."
                            final_attempt = True
                            continue
                        else:
                            break

                    # If no tool calls in the response, we're done
                    if not collected.tool_calls:
                        response_complete = True
                        break

                    # Emit "processing_result" state before executing tools
                    yield "<|AGENT_STATE:processing_result|>"
                    
                    # Execute tool calls and add results back to messages for next round
                    messages.append(collected)
                    
                    for tool_call in collected.tool_calls:
                        tool_fn = tool_map.get(tool_call["name"])
                        tool_result = None
                        
                        try:
                            if tool_fn:
                                tool_result = tool_fn.invoke(tool_call["args"])
                            else:
                                tool_result = f"Unknown tool: {tool_call['name']}"
                        except Exception as e:
                            import traceback
                            error_details = traceback.format_exc()
                            tool_result = f"Error executing tool {tool_call['name']}: {str(e)}\n\nDetails: {error_details}"
                        
                        # Add tool result to messages
                        messages.append(
                            ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_call["id"],
                            )
                        )
                    
                    # Continue to next round to get LLM response with tool results
                    continue

                except Exception as e:
                    import traceback
                    # If streaming itself fails, try to yield an error response
                    yield f"\n\nSorry, I encountered an error while processing your request: {str(e)}"
                    break

            # If we exhausted all rounds but aren't done, send a completion message
            if not response_complete and round_num == max_tool_rounds - 1:
                yield "\n\nI've attempted to process your request through multiple steps. If the issue persists, please try again or select a different action."

            # Capture token usage across all rounds
            if token_tracker is not None:
                token_tracker.update({
                    "prompt_tokens": cb.prompt_tokens,
                    "completion_tokens": cb.completion_tokens,
                    "total_tokens": cb.total_tokens,
                })
