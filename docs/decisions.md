# Engineering decisions

1. **Local ZIP as input.** The tool reads a data set ZIP you download from SEC. It does not
   fetch it, because I could not verify a stable download URL pattern and a wrong guess would fail silently.
2. **Amendments supersede originals.** For each (`SERIESID`, `REPORTDATE`) only the most
   recently filed submission is analysed. `NT` notices carry no data and are dropped.
3. **Nothing is silently fixed.** `validate.py` returns findings (missing values, WAL below
   WAM, holdings that do not sum to roughly 100%, matured holdings, liquid-asset percentages out of range). They are
   printed in the memo; they never alter a number.
4. **No cross-agency rating mapping.** Rating scales differ and the short-term scales do
   not line up one-to-one, so ratings are reported as coverage per agency and never converted to a single score.
5. **Concentration excludes US government securities.** They carry no issuer-diversification
   limit, so including them would flag every government fund. The 10% flag is an analyst screening threshold, not a rule.
6. **Limits are configuration.** WAM, WAL and liquid-asset minimums live in `config.py` so
   they can change with the rule. They must be verified against current Rule 2a-7 text (see limitations).
7. **Stress is deliberately simple.** Two views: worst cumulative net outflow over a rolling window
   (default five reported days) against weekly liquid assets, and instantaneous redemption shocks (10-40% of net assets) against daily and weekly liquid assets. No price impact, no liquidity fees.
8. **Tax-exempt funds skip the liquid-asset tests.** Applied by category keyword; verify against the rule.
