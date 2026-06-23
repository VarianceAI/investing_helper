# TradeAgent

A personal US stock trading agent built on Robinhood's official Agentic Trading API (MCP), driven by quantitative strategies with the goal of consistent profitability.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Strategies](#strategies)
- [Risk Management](#risk-management)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

---

## Overview

RH-TradeAgent connects an AI agent to a dedicated Robinhood brokerage account via the official **MCP (Model Context Protocol)** server, launched by Robinhood in May 2026. The agent autonomously analyzes markets, generates trade signals, and executes orders — all within a ring-fenced account isolated from your main portfolio.

> **Note:** The Agentic Trading account is fully separated from your primary Robinhood account. The agent can only access funds you explicitly deposit into it.

---

## Features

- 📈 **Pluggable Strategies** — Mean reversion, momentum, ETF rebalancing, and more
- 🔍 **Real-time Signal Analysis** — News sentiment, analyst ratings, and technical indicators
- ⚙️ **Fully Automated Execution** — Places market and limit orders via Robinhood MCP
- 🛡️ **Multi-layer Risk Controls** — Max drawdown stops, position sizing limits, daily loss circuit breakers
- 📊 **Portfolio Monitoring** — Live P&L tracking with auto-pause on anomalies
- 🔄 **Auto Rebalancing** — Periodically realigns holdings to target weights

---

## Architecture

```
┌──────────────────────────────────────────────┐
│             Strategy Layer                    │
│   Mean Reversion │ Momentum │ Rebalancing     │
└─────────────────────┬────────────────────────┘
                      │
┌─────────────────────▼────────────────────────┐
│              Signal Layer                     │
│   News Sentiment │ Technicals │ Analyst Ratings│
└─────────────────────┬────────────────────────┘
                      │
┌─────────────────────▼────────────────────────┐
│             Execution Layer                   │
│       Robinhood MCP Trading Server            │
│   Position Sizing │ Order Management │ Stops  │
└──────────────────────────────────────────────┘

MCP Endpoint: https://agent.robinhood.com/mcp/trading
```

**Core Dependencies**

| Component | Purpose |
|-----------|---------|
| Robinhood Agentic Trading | Official MCP trading interface |
| Claude / GPT (LLM) | Strategy reasoning & signal parsing |
| Robinhood Gold | Full API access ($5/month) |

---

## Getting Started

### Prerequisites

- A Robinhood account with an active **Gold membership**
- A dedicated **Agentic Trading account** created in the Robinhood app
- An MCP-compatible AI platform (Claude Desktop, Cursor, ChatGPT, etc.)

### 1. Configure MCP Connection

Add the following to your AI platform's MCP config:

```json
{
  "mcpServers": {
    "robinhood-trading": {
      "url": "https://agent.robinhood.com/mcp/trading"
    }
  }
}
```

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/rh-trade-agent.git
cd rh-trade-agent
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Strategy Parameters

```bash
cp config/strategy.example.yaml config/strategy.yaml
# Edit strategy.yaml with your preferred strategy and risk thresholds
```

### 5. Run the Agent

```bash
python main.py --strategy mean_reversion --budget 500
```

---

## Strategies

### Mean Reversion

Buys when a stock's price deviates below its moving average by a set threshold, and sells once it reverts. Best suited for range-bound markets.

```yaml
strategy: mean_reversion
lookback_days: 20
entry_threshold: -2.0%   # Buy when price is 2% below MA
exit_threshold: +1.0%    # Sell when price reverts 1% above MA
max_positions: 5
```

### Momentum

Tracks recent top performers — buys the highest-returning stocks over the past N days and holds for a fixed period.

```yaml
strategy: momentum
lookback_days: 30
top_n_stocks: 5
hold_days: 10
```

### ETF Rebalancing

Periodically realigns the portfolio to a fixed target allocation. Best for long-term, passive strategies.

```yaml
strategy: rebalance
target_allocation:
  SPY: 40%
  QQQ: 30%
  VTI: 20%
  CASH: 10%
rebalance_frequency: weekly
```

---

## Risk Management

The agent enforces multiple layers of risk control out of the box:

| Rule | Default Threshold | Description |
|------|-------------------|-------------|
| Max position size | 20% of account | Prevents over-concentration |
| Daily loss limit | 3% of account | Halts trading for the rest of the day |
| Max drawdown circuit breaker | 15% of account | Pauses all strategies until manual review |
| Max trades per day | 10 | Avoids overtrading and excessive fees |
| Abnormal price filter | 5% deviation | Guards against flash crash misfire |

All thresholds are configurable in `config/strategy.yaml`.

---

## Project Structure

```
rh-trade-agent/
├── main.py                   # Entry point
├── config/
│   ├── strategy.example.yaml
│   └── strategy.yaml         # Local config (not committed)
├── agent/
│   ├── core.py               # Core agent loop
│   ├── mcp_client.py         # Robinhood MCP interface wrapper
│   └── prompts.py            # LLM strategy prompts
├── strategies/
│   ├── base.py               # Strategy base class
│   ├── mean_reversion.py
│   ├── momentum.py
│   └── rebalance.py
├── risk/
│   └── manager.py            # Risk management module
├── signals/
│   ├── news_sentiment.py     # News sentiment analysis
│   └── technical.py          # Technical indicator calculations
├── monitor/
│   └── tracker.py            # P&L monitoring and alerts
├── tests/
│   └── backtest.py           # Historical backtesting
├── requirements.txt
└── README.md
```

---

## Roadmap

- [x] MCP connection and account data access
- [x] Mean reversion strategy
- [ ] Momentum strategy
- [ ] News sentiment signal integration
- [ ] Backtesting framework
- [ ] Web monitoring dashboard
- [ ] Options strategy support *(pending Robinhood beta rollout)*
- [ ] Crypto strategy support *(pending Robinhood beta rollout)*

---

## Disclaimer

> This project is intended for personal research and educational purposes only. Stock trading involves substantial risk, including the potential loss of principal. AI agents may make errors or behave unexpectedly. **All trading outcomes are the sole responsibility of the account holder.** Neither Robinhood nor the author of this project accepts any liability for financial losses.
>
> Before committing real capital, make sure to:
> 1. Thoroughly understand the logic and historical behavior of any strategy you deploy
> 2. Test with a small amount of money before scaling up
> 3. Set conservative risk thresholds appropriate to your situation
> 4. Actively monitor the agent's activity and P&L

---

<p align="center">
  Built on Robinhood Agentic Trading MCP
</p>
