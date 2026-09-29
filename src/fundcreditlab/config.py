"""Thresholds and table definitions.

Regulatory limits are configuration, not hard-wired logic, so they can change with the
rule. Sources for every regulatory value are listed in docs/limitations.md.
"""
from dataclasses import dataclass

# Tables read from the SEC Form N-MFP data set ZIP (tab-delimited). Live files are named
# NMFP_<TABLE>.tsv; the prefix is stripped when matching.
MEMBER_PREFIX = "NMFP_"
REQUIRED_TABLES = ("SUBMISSION", "SERIESLEVELINFO", "SCHPORTFOLIOSECURITIES")
OPTIONAL_TABLES = ("NRSRO", "LIQUIDASSETSDETAILS", "DLYSHAREHOLDERFLOWREPORT")


@dataclass(frozen=True)
class Limits:
    wam_max_days: float = 60.0    # rule 2a-7(d)(1)(ii)
    wal_max_days: float = 120.0   # rule 2a-7(d)(1)(iii)
    # Acquisition tests, rule 2a-7(d)(4)(ii)-(iii): below these a fund may only buy liquid
    # assets. Falling below is not itself a breach. The daily test does not apply to
    # tax-exempt funds; the weekly test applies to all funds.
    dla_min_pct: float = 25.0
    wla_min_pct: float = 50.0
    # Board notification within one business day (2023 amendments, Release 33-11211).
    dla_notify_pct: float = 12.5
    wla_notify_pct: float = 25.0
    concentration_flag_pct: float = 10.0  # analyst screening threshold, NOT a rule
    thin_wam_days: float = 10.0   # analyst screening: headroom below this is flagged 'thin'
    thin_wal_days: float = 20.0
    thin_liquidity_pp: float = 5.0  # percentage points of headroom on DLA/WLA
    stress_window_days: int = 5   # rolling reported-day window for net outflows
    shock_levels_pct: tuple = (10.0, 20.0, 30.0, 40.0)  # instantaneous redemption shocks


DEFAULT_LIMITS = Limits()

# MONEYMARKETFUNDCATEGORY values that are tax-exempt funds (rule 2a-7(a)(23)): the daily
# liquid asset minimum does not apply to them.
TAX_EXEMPT_CATEGORIES = ("single state", "other tax exempt")
