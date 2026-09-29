"""Thresholds and table definitions.

Regulatory limits are configuration, not hard-wired logic, so they can be changed
when the rule changes. VERIFY every value against the current text of SEC Rule
2a-7 before relying on a flag; see docs/limitations.md.
"""
from dataclasses import dataclass

# Tables read from the SEC Form N-MFP data set ZIP (tab-delimited).
REQUIRED_TABLES = ("SUBMISSION", "SERIESLEVELINFO", "SCHPORTFOLIOSECURITIES")
OPTIONAL_TABLES = ("NRSRO", "LIQUIDASSETSDETAILS", "DLYSHAREHOLDERFLOWREPORT")


@dataclass(frozen=True)
class Limits:
    wam_max_days: float = 60.0    # Rule 2a-7(d)(1)(ii): dollar-weighted average maturity
    wal_max_days: float = 120.0   # Rule 2a-7(d)(1)(iii): dollar-weighted average life
    dla_min_pct: float = 25.0     # daily liquid assets, % of total assets (verify)
    wla_min_pct: float = 50.0     # weekly liquid assets, % of total assets (verify)
    concentration_flag_pct: float = 10.0  # analyst screening threshold, NOT a rule
    thin_wam_days: float = 10.0   # analyst screening: headroom below this is flagged 'thin'
    thin_wal_days: float = 20.0
    thin_liquidity_pp: float = 5.0  # percentage points of headroom on DLA/WLA
    stress_window_days: int = 5   # rolling business-day window for net outflows
    shock_levels_pct: tuple = (10.0, 20.0, 30.0, 40.0)  # instantaneous redemption shocks


DEFAULT_LIMITS = Limits()

# Tax-exempt categories are not tested against the liquid-asset minimums here.
LIQUIDITY_EXEMPT_CATEGORY_KEYWORD = "tax exempt"

# Issuer-concentration screening excludes US government securities: they are not subject
# to issuer diversification limits, so counting them would flag every government fund.
GOVERNMENT_CATEGORY_KEYWORDS = ("treasury", "government agency")
