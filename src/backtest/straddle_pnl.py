"""Module 3/4: real straddle PnL, net of transaction costs.

All dollar figures use the standard 100x equity option contract multiplier.
Quote-level fields (strike, premium, breakeven) stay in per-share terms to
match how option prices are quoted; PnL figures are converted to per-contract
dollars via CONTRACT_MULTIPLIER so they're not misread as per-share.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.targets.breakeven import StraddleEntry

CONTRACT_MULTIPLIER = 100


@dataclass
class StraddlePnL:
    gross_pnl: float          # per-contract dollars, before transaction costs
    net_pnl: float            # per-contract dollars, after commission (+ slippage)
    return_on_premium: float  # net_pnl / premium paid (dollars)
    target_expiry: int
    target_positive_net_pnl: int


def compute_pnl(entry: StraddleEntry, expiry_price: float, commission_per_contract: float = 0.65,
                 slippage_pct: float = 0.0, use_ask_entry: bool = False) -> StraddlePnL:
    """use_ask_entry=True reproduces the conservative variant from the research
    proposal (buy at ask on both legs) instead of the primary mid-price entry.
    """
    premium_per_share = entry.premium_ask if use_ask_entry else entry.premium_mid
    strike = entry.strike

    intrinsic_per_share = max(expiry_price - strike, 0.0) + max(strike - expiry_price, 0.0)
    gross_pnl_per_share = intrinsic_per_share - premium_per_share
    gross_pnl = gross_pnl_per_share * CONTRACT_MULTIPLIER

    commission = 2 * commission_per_contract  # one call leg + one put leg
    slippage = slippage_pct * premium_per_share * CONTRACT_MULTIPLIER
    net_pnl = gross_pnl - commission - slippage

    premium_dollars = premium_per_share * CONTRACT_MULTIPLIER
    return_on_premium = net_pnl / premium_dollars if premium_dollars > 0 else float("nan")

    target_expiry = int(abs(expiry_price - strike) > premium_per_share)
    target_positive_net_pnl = int(net_pnl > 0)

    return StraddlePnL(
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        return_on_premium=return_on_premium,
        target_expiry=target_expiry,
        target_positive_net_pnl=target_positive_net_pnl,
    )
