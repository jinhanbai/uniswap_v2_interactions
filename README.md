# 🧪 Uniswap V2 Interactions Python Toolkit

This repository provides a Python implementation template for modeling, querying, and simulating trades with Uniswap V2-style liquidity pools. It is designed for research, prototyping, and integration into DeFi execution pipelines.

---

## 📦 Module Overview

### `uniswapv2_pool_model.py`

**Purpose**: Core logic for pool state management and quote computation.

- Represents a Uniswap V2 liquidity pool as a Python class.
- Computes token swap output/input using the constant-product formula with fees.
- Stores token metadata, reserves, and precomputed bid references.
- Utility functions:
  - `get_amount_out`, `get_amount_in` — price computation
  - `to_dict` — export pool metadata
  - `get_state_calls` — build JSON-RPC payloads for reserve fetching

---

### `uniswapv2_pool_helper.py`

**Purpose**: Data fetching via GraphQL and RPC.

- Interfaces with The Graph to fetch Uniswap V2 pair metadata.
- Encodes and decodes `eth_call` RPCs to query live pool data:
  - `getReserves()` — for current liquidity
  - `getAmountsOut()` — for on-chain quotes
- Functions:
  - `get_pools_query`, `get_pair_pools_query` — GraphQL fetchers
  - `get_balances_call`, `process_balances_call` — RPC for reserve data
  - `get_amounts_out_call` — price estimation logic

---

### `uniswapv2_encoder.py`

**Purpose**: EVM-compatible encoding of Uniswap trades.

- Encodes calldata for swap execution via:
  - Uniswap V2 pools (flash swaps)
  - Third-party routers: **1inch**, **0x (ZeroEx)**, **Otex** (GlueX)
- Implements slippage handling and token path routing.
- Functions:
  - `encode_hop_single_pool` — direct pool swap
  - `OneInchTokenForToken`, `ZeroExTokenForToken`, `OtexTokenForToken` — router integrations
  - `_to_pool` — deterministic Uniswap V2 pool address computation

---

## 🔧 Dependencies

- [`web3.py`](https://github.com/ethereum/web3.py)
- [`eth-abi`](https://github.com/ethereum/eth-abi)
- [`eth-utils`](https://github.com/ethereum/eth-utils)

---

## 🧪 Example Use Cases

- Simulate a swap via Uniswap V2 router or direct pool contract
- Fetch reserve data for a pair and compute expected output
- Encode a trade path for execution with slippage controls
- Compare routing efficiency between different protocols
