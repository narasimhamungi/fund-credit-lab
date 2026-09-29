# Data dictionary

Source: SEC DERA *Form N-MFP Data Sets* (tab-delimited, one file per table). Definitions
below are taken from the SEC readme (`nmfp_readme.pdf`); only fields this project reads are listed.

## SUBMISSION
| Field | Meaning |
|---|---|
| `ACCESSION_NUMBER` | SEC-assigned unique id of the EDGAR submission (primary key) |
| `FILING_DATE` | Date filed. Used to pick the latest version when a report is amended |
| `SUBMISSIONTYPE` | `N-MFP*`, `N-MFP*/A` (amendment) or `NT N-MFP*` (notice of late filing, no data) |
| `REPORTDATE` | Month-end date the report covers |
| `SERIESID` | EDGAR series identifier (`S` plus nine digits) |
| `NAMEOFSERIES` / `SERIES_NAME` | Series name as filed / as held by EDGAR |

## SERIESLEVELINFO
| Field | Meaning |
|---|---|
| `MONEYMARKETFUNDCATEGORY` | Government, Prime, Single State or Other Tax Exempt |
| `AVERAGEPORTFOLIOMATURITY` | Dollar-weighted average portfolio maturity, WAM (days) |
| `AVERAGELIFEMATURITY` | Dollar-weighted average life maturity, WAL (days) |
| `NETASSETOFSERIES` | Net assets of the series (USD) |

## SCHPORTFOLIOSECURITIES
| Field | Meaning |
|---|---|
| `SECURITY_ID` | Surrogate key for the security within the filing |
| `NAMEOFISSUER` | Issuer name |
| `INVESTMENTCATEGORY` | Category that most closely identifies the instrument |
| `INVESTMENTMATURITYDATEWAM` | Maturity date used for WAM |
| `PERCENTAGEOFMONEYMARKETFUNDNET` | Position as % of the fund's net assets |

## NRSRO
| Field | Meaning |
|---|---|
| `SECURITY_ID` | Links to SCHPORTFOLIOSECURITIES |
| `TYPE` | `SECURITY`, `DEMAND FEATURE`, `ENHANCEMENT` or `GUARANTOR` |
| `NAMEOFNRSRO` | Rating agency |
| `RATING` | Rating code as filed |

## LIQUIDASSETSDETAILS (one row per reported business day)
| Field | Meaning |
|---|---|
| `TOTLIQUIDASSETSNEARPCTDATE` | Date of the observation |
| `TOTVALUEDAILYLIQUIDASSETS`, `TOTVALUEWEEKLYLIQUIDASSETS` | Daily / weekly liquid assets (USD); weekly includes daily |
| `PCTDAILYLIQUIDASSETS`, `PCTWEEKLYLIQUIDASSETS` | The same as % of total assets |

## DLYSHAREHOLDERFLOWREPORT (class level, one row per class per day)
| Field | Meaning |
|---|---|
| `CLASSESID` | Share class id |
| `DAILYGROSSSUBSCRIPTIONS`, `DAILYGROSSREDEMPTIONS` | Gross subscriptions and redemptions (USD) |
| `DAILYSHAREHOLDERFLOWDATE` | Date |
