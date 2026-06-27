"""
agent/mcp_client.py
~~~~~~~~~~~~~~~~~~~
Thin wrapper around the Robinhood Trading MCP endpoint.

MCP URL: https://agent.robinhood.com/mcp/trading

All MCP tools are called via the Anthropic API's mcp_servers parameter so
that the LLM can reason about and invoke them naturally. This module handles:
  - Sending MCP-enabled requests to claude-sonnet-4-6
  - Parsing the multi-block response (text / mcp_tool_use / mcp_tool_result)
  - Exposing typed helper methods for every tool group

Official tools (from Robinhood docs):
  Account & Portfolio:  get_accounts, get_portfolio, search
  Watchlist:            get_watchlists, get_watchlist_items, add_to_watchlist, ...
  Market data:          get_equity_historicals, get_indexes, get_indexes_quotes
  Equities:             get_equity_positions, get_equity_quotes, get_equity_orders,
                        get_equity_tradability, review_equity_order,
                        place_equity_order, cancel_equity_order
  Options (beta):       get_option_chains, get_option_quotes, place_option_order, ...
"""

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MCP_SERVER_URL = "https://agent.robinhood.com/mcp/trading"
MODEL = "claude-sonnet-4-6"


class RobinhoodMCPClient:
    """
    Sends natural-language or structured prompts to Claude with the
    Robinhood MCP server attached. Claude decides which tools to call;
    this client collects and returns the results.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._mcp_config = [
            {
                "type": "url",
                "url": MCP_SERVER_URL,
                "name": "robinhood-trading",
            }
        ]

    # ------------------------------------------------------------------
    # Core request
    # ------------------------------------------------------------------

    async def _call(self, prompt: str, system: str | None = None) -> dict[str, Any]:
        """
        Send a prompt to Claude with the Robinhood MCP server and return
        a parsed response dict with keys: text, tool_calls, tool_results.
        """
        payload = {
            "model": MODEL,
            "max_tokens": 1000,
            "mcp_servers": self._mcp_config,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                ANTHROPIC_API_URL,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        return self._parse_response(data)

    @staticmethod
    def _parse_response(data: dict) -> dict[str, Any]:
        """
        Split the multi-block response into typed sections.
        Blocks can be: text | mcp_tool_use | mcp_tool_result
        """
        text_parts = []
        tool_calls = []
        tool_results = []

        for block in data.get("content", []):
            btype = block.get("type")
            if btype == "text":
                text_parts.append(block.get("text", ""))
            elif btype == "mcp_tool_use":
                tool_calls.append({"name": block.get("name"), "input": block.get("input", {})})
            elif btype == "mcp_tool_result":
                raw = block.get("content", [{}])
                text = raw[0].get("text", "") if raw else ""
                try:
                    result_data = json.loads(text)
                except (json.JSONDecodeError, TypeError):
                    result_data = text
                tool_results.append(result_data)

        return {
            "text": "\n".join(text_parts),
            "tool_calls": tool_calls,
            "tool_results": tool_results,
        }

    # ------------------------------------------------------------------
    # Account & Portfolio
    # ------------------------------------------------------------------

    async def get_accounts(self) -> dict:
        """Return all Robinhood accounts (primary + agentic)."""
        result = await self._call("Call get_accounts and return the raw JSON.")
        return result["tool_results"][0] if result["tool_results"] else {}

    async def get_portfolio(self) -> dict:
        """Snapshot of portfolio value, buying power, and positions by asset class."""
        result = await self._call("Call get_portfolio and return the raw JSON snapshot.")
        return result["tool_results"][0] if result["tool_results"] else {}

    async def search_ticker(self, query: str) -> list[dict]:
        """Fuzzy-search a company name or partial ticker."""
        result = await self._call(f'Call search with query="{query}" and return the raw JSON list.')
        return result["tool_results"][0] if result["tool_results"] else []

    # ------------------------------------------------------------------
    # Market Data
    # ------------------------------------------------------------------

    async def get_historicals(self, symbol: str, interval: str = "day", span: str = "3month") -> list[dict]:
        """
        OHLCV bars for a symbol.
        interval: "5minute" | "10minute" | "hour" | "day" | "week"
        span:     "day" | "week" | "month" | "3month" | "year" | "5year"
        """
        prompt = (
            f"Call get_equity_historicals for symbol={symbol}, "
            f"interval={interval}, span={span}. Return the raw JSON array of bars."
        )
        result = await self._call(prompt)
        return result["tool_results"][0] if result["tool_results"] else []

    async def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Real-time quotes for up to 20 symbols."""
        syms = ", ".join(symbols)
        result = await self._call(f"Call get_equity_quotes for symbols [{syms}] and return the raw JSON.")
        return result["tool_results"][0] if result["tool_results"] else []

    async def get_indexes(self, symbols: list[str] | None = None) -> list[dict]:
        """Market index values (SPX, NDX, DJI, etc.)."""
        prompt = "Call get_indexes_quotes for the major US indexes and return raw JSON."
        if symbols:
            prompt = f"Call get_indexes_quotes for {', '.join(symbols)} and return raw JSON."
        result = await self._call(prompt)
        return result["tool_results"][0] if result["tool_results"] else []

    # ------------------------------------------------------------------
    # Equity Positions & Orders
    # ------------------------------------------------------------------

    async def get_positions(self) -> list[dict]:
        """Open equity positions in the agentic account."""
        result = await self._call("Call get_equity_positions and return the raw JSON list.")
        return result["tool_results"][0] if result["tool_results"] else []

    async def get_order_history(self) -> list[dict]:
        """Full equity order history for the agentic account."""
        result = await self._call("Call get_equity_orders and return the raw JSON list.")
        return result["tool_results"][0] if result["tool_results"] else []

    async def check_tradability(self, symbol: str) -> dict:
        """Check if a symbol is tradeable and whether fractional shares are supported."""
        result = await self._call(
            f"Call get_equity_tradability for symbol={symbol} and return the raw JSON."
        )
        return result["tool_results"][0] if result["tool_results"] else {}

    # ------------------------------------------------------------------
    # Order Execution
    # ------------------------------------------------------------------

    async def review_order(self, symbol: str, side: str, quantity: float, order_type: str = "market", limit_price: float | None = None) -> dict:
        """
        Simulate an order via review_equity_order (no real trade).
        Always call this before place_order for safety checks.
        """
        prompt = (
            f"Call review_equity_order with symbol={symbol}, side={side}, "
            f"quantity={quantity}, order_type={order_type}"
        )
        if limit_price:
            prompt += f", limit_price={limit_price}"
        prompt += ". Return the full pre-trade warning JSON."
        result = await self._call(prompt)
        return result["tool_results"][0] if result["tool_results"] else {}

    async def place_order(
        self,
        symbol: str,
        side: str,          # "buy" | "sell"
        quantity: float,
        order_type: str = "market",
        limit_price: float | None = None,
        time_in_force: str = "gfd",  # "gfd" | "gtc" | "ioc" | "opg"
    ) -> dict:
        """
        Place a real equity order via place_equity_order.
        In dry_run mode, falls back to review_equity_order only.
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would place {side} {quantity} {symbol} @ {order_type}")
            return await self.review_order(symbol, side, quantity, order_type, limit_price)

        prompt = (
            f"Call place_equity_order with symbol={symbol}, side={side}, "
            f"quantity={quantity}, order_type={order_type}, time_in_force={time_in_force}"
        )
        if limit_price:
            prompt += f", limit_price={limit_price}"
        prompt += ". Return the full order confirmation JSON."

        result = await self._call(prompt)
        order = result["tool_results"][0] if result["tool_results"] else {}
        logger.info(f"Order placed: {side} {quantity} {symbol} → {order}")
        return order

    async def cancel_order(self, order_id: str) -> dict:
        """Cancel an open equity order by ID."""
        result = await self._call(
            f"Call cancel_equity_order with order_id={order_id} and return the result JSON."
        )
        return result["tool_results"][0] if result["tool_results"] else {}

    # ------------------------------------------------------------------
    # Free-form agentic analysis
    # ------------------------------------------------------------------

    async def analyze(self, prompt: str, system: str | None = None) -> str:
        """
        Send any free-form prompt to Claude+Robinhood MCP for open-ended
        market analysis (news sentiment, bull/bear thesis, sector screening, etc.)
        Returns Claude's text response.
        """
        result = await self._call(prompt, system=system)
        return result["text"]
