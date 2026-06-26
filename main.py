"""
RH-TradeAgent — Main Entry Point
Connects to Robinhood Agentic Trading via MCP and runs the selected strategy.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from agent.core import TradingAgent
from config.loader import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/agent.log"),
    ],
)
logger = logging.getLogger("main")


def parse_args():
    parser = argparse.ArgumentParser(description="RH-TradeAgent: AI-powered trading agent for Robinhood")
    parser.add_argument(
        "--strategy",
        type=str,
        default="mean_reversion",
        choices=["mean_reversion", "momentum", "rebalance"],
        help="Trading strategy to run",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/strategy.yaml",
        help="Path to strategy config file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate trades without placing real orders (uses review_equity_order)",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=None,
        help="Override budget from config (USD)",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # Ensure log dir exists
    Path("logs").mkdir(exist_ok=True)

    logger.info(f"Starting RH-TradeAgent | strategy={args.strategy} | dry_run={args.dry_run}")

    config = load_config(args.config)
    if args.budget:
        config["risk"]["budget_usd"] = args.budget

    agent = TradingAgent(
        strategy_name=args.strategy,
        config=config,
        dry_run=args.dry_run,
    )

    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested — stopping agent gracefully.")
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
