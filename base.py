"""
strategies/base.py
~~~~~~~~~~~~~~~~~~
Abstract base class for all trading strategies.
Every strategy must implement generate_signals().
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    A strategy receives portfolio state and open positions,
    then returns a list of trade signals for the agent to execute.

    Signal schema:
        {
            "symbol":      str,          # e.g. "AAPL"
            "side":        "buy"|"sell",
            "quantity":    float,        # shares (can be fractional)
            "order_type":  "market"|"limit",
            "limit_price": float|None,   # required if order_type == "limit"
            "reason":      str,          # human-readable rationale for logging
        }
    """

    def __init__(self, config: dict, client, risk):
        self.config = config
        self.client = client   # RobinhoodMCPClient
        self.risk = risk       # RiskManager

    @abstractmethod
    async def generate_signals(self, portfolio: dict, positions: list[dict]) -> list[dict]:
        """
        Analyze market data and current holdings.
        Return a list of trade signals (may be empty).
        """
        ...

    # ------------------------------------------------------------------
    # Shared utilities
    # ------------------------------------------------------------------

    def position_for(self, symbol: str, positions: list[dict]) -> dict | None:
        """Find an existing position by symbol, or None."""
        for p in positions:
            if p.get("symbol") == symbol:
                return p
        return None

    def dollars_to_shares(self, dollars: float, price: float) -> float:
        """Convert a dollar amount to share quantity (supports fractional)."""
        if price <= 0:
            return 0.0
        return round(dollars / price, 6)

    def log_signal(self, signal: dict):
        logger.info(
            f"Signal: {signal['side'].upper()} {signal['quantity']} {signal['symbol']} "
            f"({signal.get('order_type', 'market')}) — {signal.get('reason', '')}"
        )
