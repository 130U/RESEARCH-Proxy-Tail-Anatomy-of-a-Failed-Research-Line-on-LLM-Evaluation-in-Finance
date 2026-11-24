# T1B source review A

Scope: 98 sorted cohort questions, complete FinQA supplied context. This is LLM-assisted source inspection, not human signoff and not review of entire original annual reports. References Pn mean zero-based combined pre_text + post_text index n (equivalently text_n), not a post_text-only index.

Judgments: {'valid': 72, 'uncertain': 11, 'invalid': 15}. Fixed-seed sample subset: {'valid': 12, 'uncertain': 2, 'invalid': 3}.

Every question was read for metric, entity, period, unit, quantitative type and gold-program meaning. Numeric/unit candidates were checked against economic identity. No unlisted higher-precision input occurrence was confirmed. Supplemental equations include text-defined component sums; numerical near-equalities alone were rejected. Uncertain cases are conservatively excluded from clean retained conclusions. Structural zeros and rounded dashes are explicitly distinguished in annotations. Independent review removed seven AMT2005/2006 total=noncore+CIP equalities because the source enumeration is not explicitly exhaustive. Explicit comprised-of gross-loss-minus-gain equations remain.

| Question | Sample | Judgment | Reason |
|---|---|---|---|
| AAL/2010/page_72.pdf-2 |  | valid | 2010 pension minimum contributions are monetary estimates; approximately460m has no more precise disclosure here. Statutory minimum does not make a reported million-dollar aggregate exact. |
| AAL/2010/page_72.pdf-4 | yes | valid | 2010/2009 slot-and-route carrying amounts708/736m match. The28m impairment concerns certain routes plus other slots/routes, not an exhaustive carrying-value rollforward. |
| AAL/2013/page_18.pdf-2 |  | valid | 2013/2012 fuel cost3.09/3.20 per gallon matches growth. Cost/gallons disclosures do not establish a valid linear identity on average prices. |
| AAL/2013/page_18.pdf-3 | yes | uncertain | Hedge effect naturally means reduction from unhedged104m, but gold divides104-87 by hedged87m; comparison base is ambiguous. |
| AAPL/2003/page_48.pdf-1 |  | valid | Ending retirement liability7.2m less1.2m accretion matches question. Opening5.5m+new0.5m+accretion is documented reconciliation; row0 is data. |
| ABMD/2005/page_29.pdf-3 |  | uncertain | Risk-free rates2.56/2.92 are Black-Scholes assumptions; context does not establish whether fixed parameter settings or rounded estimates. Quantity uncertain. |
| ABMD/2008/page_86.pdf-2 |  | invalid | Cash requirement1.8m applies to remaining combined11.2m contingent payments, while5.6m is one milestone. Precise contractual5583333-dollar amount appears in P20. Rounded-independent assumptions and June-specific cash allocation are unsupported. |
| ABMD/2012/page_79.pdf-1 |  | valid | Rent expenses1.6/2.7/2.2m correspond to2012/2011/2010; future lease payments and particular-property base rent are different quantities. |
| ADBE/1999/page_64.pdf-1 |  | valid | Severance0.3m+lease termination0.1m are requested balances; with canceled-contract0.4m they exhaust remaining0.772m accrual. |
| ADBE/1999/page_64.pdf-2 | yes | valid | Canceled contracts0.4m is component of remaining1998-program accrual. Table772thousand equals text0.8m because P12 says older merger accruals are zero. |
| ADI/2010/page_60.pdf-1 |  | valid | Notional undesignated hedges42.1/38m match2010/2009; designated swaps and fixed debt elsewhere differ. |
| AES/2002/page_128.pdf-1 |  | valid | Discontinued-operation14m/all169m lease commitments matches; both columns sum over maturity buckets. |
| AES/2002/page_128.pdf-3 |  | valid | 2003 commitments30m/all169m matches; complete maturity sum valid, arbitrary equalities between years invalid. |
| ALLE/2015/page_24.pdf-1 |  | valid | 2015 disposed-site remediation2.8m is subset of15.2m reserve;2014 amounts and expenses are distinct. |
| ALLE/2015/page_24.pdf-2 |  | valid | 2014 reserve8.8m minus expense2.9m matches requested difference; deliberately compares stock and flow. |
| ALXN/2016/page_153.pdf-3 |  | valid | 2016/2015 facility lease obligation136/133 is millions per P1; table debt maturities concern other liabilities. |
| AMT/2003/page_102.pdf-1 |  | valid | Accrued interest4.8m/aggregate redemption221.9m matches. Documented contractual redemption factor also links principal, total and interest. |
| AMT/2003/page_102.pdf-4 |  | invalid | Gold computes accrued-interest/principal for partial accrual period; question asks interest rate explicitly stated as6.25% coupon. |
| AMT/2005/page_102.pdf-2 |  | valid | 2005/2004 non-core impairment/net losses16.8/17.7m match gold-supported metric; construction-in-progress is separate component of total. |
| AMT/2005/page_102.pdf-3 |  | valid | 2004/2003 non-core17.7/19.1m match;19.1m total for2005 elsewhere is a different metric/year. |
| AMT/2006/page_113.pdf-4 |  | valid | 2006/2005/2004 construction-in-progress1.0/2.3/4.6m match, mean uses exact count3; significant-component list is not assumed exhaustive. |
| AMT/2008/page_107.pdf-1 |  | valid | 2008/2007 non-core net10.5/7.1m match. Passage is duplicated verbatim; gross losses less gains constrain net amounts. |
| AMT/2014/page_149.pdf-1 |  | valid | 2014/2013 impairment11.2/15.9m match and equal carrying values before minus after each write-down. |
| ANSS/2012/page_93.pdf-4 |  | valid | 1.3m is stated for each of3years. Multiplying interval by3 gives same sum range as three separately rounded years, without claiming equal latent residuals. |
| AON/2007/page_171.pdf-4 |  | valid | 2007/2006 derivative OCI gains24/15m match; four OCI categories sum to accumulated OCI loss. |
| AON/2007/page_175.pdf-1 |  | valid | 2007 expense,signed cash payments,FX are complete movements in liability bridge. |
| AON/2007/page_175.pdf-2 |  | valid | 2006 expense,signed cash payments,FX are complete movements in liability bridge. |
| AON/2007/page_188.pdf-2 |  | valid | 57m tax-rate-impact subset/70m total matches; complete signed rollforward constrains total. |
| AON/2007/page_188.pdf-4 |  | valid | 24m prior-year additions minus4m current-year additions matches; both in2007 rollforward. |
| AON/2015/page_96.pdf-4 |  | invalid | 411636 is exact issued-share count, not rounded scaled count.9m compensation expense/share is not employee purchase price under85%-of-market plan. |
| AON/2018/page_87.pdf-1 |  | valid | Interest/penalty liabilities77/55m match2018/2017.22m accrual is not established as sole movement; no equality imposed from arithmetic coincidence. |
| AON/2018/page_87.pdf-2 | yes | valid | 2017prior-year tax additions12m less2018 10m is requested decrease; each belongs to complete rollforward. |
| APD/2018/page_121.pdf-2 |  | uncertain | Question asks decrease of fair value without saying percentage; gold returns relative change. Binding correct, requested answer dimension ambiguous. |
| APD/2018/page_30.pdf-2 |  | invalid | Quarterly dividends are board-declared per-share amounts; annual4.25/3.71 are exact payouts, not uncertain independently rounded aggregates. |
| AWK/2017/page_148.pdf-1 |  | valid | 2017/2016 average borrowings779/850 match; maximum/year-end borrowings are different measures. |
| AWK/2017/page_148.pdf-4 |  | valid | Daily weighted-average rates1.24/0.78 are computed averages, plausibly rounded, not fixed contract terms; December-end rates differ. |
| AWK/2018/page_146.pdf-2 |  | valid | 2017repurchase cost54m/shares0.7million yields dollars/share; scaled shares are rounded counts. |
| AWK/2018/page_146.pdf-3 |  | valid | 2018repurchase cost45m/shares0.6million yields dollars/share; authorization and unpurchased shares differ. |
| AWK/2018/page_146.pdf-4 |  | valid | Repurchased shares0.6+0.7million sum2018/2017; these are rounded million-scaled counts. |
| BLK/2014/page_120.pdf-3 |  | valid | 2014/2013 rent-office expense132/137m matches; future lease commitments differ. |
| BLK/2014/page_120.pdf-4 |  | valid | 2013/2012 rent-office expense137/133m matches; no higher precision of historical expense appears. |
| BLK/2017/page_121.pdf-1 |  | valid | PennyMac fair values348/259m match2017/2016; carrying342/301m are distinct. |
| BLK/2017/page_121.pdf-3 |  | valid | PennyMac carrying342/301m match2017/2016; fair348/259m are distinct. |
| BLL/2011/page_32.pdf-3 |  | valid | Approximately50percent of approximately897m backlog is requested fixed-price share; percentage is empirical composition. |
| C/2009/page_197.pdf-1 |  | invalid | Tax rate on pretax impairment normally(9.6-8.7)/9.6; gold divides by aftertax8.7, a different ratio. |
| C/2009/page_243.pdf-1 |  | valid | 5bn increase/6.2bn net transfer matches. Narrative driven-by and offset-by1.4 is not exhaustive; no5=6.2-1.4 assumption. |
| C/2009/page_243.pdf-2 |  | valid | 2009cost2.5bn/fair1.6bn matches; fair value splits into Level2+Level3. |
| C/2009/page_63.pdf-1 | yes | valid | Adjacent sentences establish both160m pension and72m postretirement contributions as non-US2010. Included in purchase obligations but no exhaustive composition. |
| CB/2010/page_103.pdf-2 | yes | valid | Multiheader identifies treasury market values2075/2068m as2010/2009; percentage columns differ. Two classifications partition same total portfolio. |
| CB/2010/page_83.pdf-1 |  | valid | 2010/2009 hedge-instrument fair21/47m matches difference; realized hedge losses and guarantee liabilities differ. |
| CB/2010/page_83.pdf-2 |  | valid | 2010/2009 hedge-instrument fair21/47m matches growth; realized hedge losses and guarantee liabilities differ. |
| CDW/2015/page_93.pdf-2 |  | invalid | Gold divides shares/expenses each year; question requests expense/share. Both ratios inverted. |
| CE/2013/page_16.pdf-1 | yes | valid | 2013/2012 cash dividends received92/83m are aggregate receipts, not declared per-share amounts. |
| CE/2013/page_16.pdf-2 | yes | valid | 2012/2011 cash dividends received83/78m are aggregate receipts, not declared per-share amounts. |
| CE/2016/page_19.pdf-2 | yes | valid | 2015/2014R&D119/86m matches difference; ownership percentages in table unrelated. |
| CE/2016/page_19.pdf-3 |  | valid | 2016/2015R&D78/119m matches signed difference; ownership percentages unrelated. |
| CMCSA/2015/page_112.pdf-2 |  | valid | End2015/2014 unrecognized benefits1136/1171m match;1171 also opening2015 and all years have complete bridges. |
| CME/2010/page_69.pdf-1 | yes | invalid | 2.9 is billion,900.1 is million; gold misses factor1000. Issuance also2008, not question2009. |
| CME/2010/page_69.pdf-2 | yes | valid | 1.4bn senior facility and945.5m revolver match with correct1000 conversion. P44 says including term420.5m and revolver, but does not establish an exhaustive partition; their exact sum is optional sensitivity only. |
| CME/2010/page_91.pdf-1 |  | valid | 2010/2009broker receivables11.2/8.8m match; both components of other-current-asset totals. |
| CME/2017/page_89.pdf-4 |  | invalid | Denominator literal3 is exact year count, but T1 binds it to2015 3.0% state tax cell as independent noisy input. Binding/type error. |
| D/2002/page_87.pdf-1 |  | valid | 34/23/13m are2003/2004/2005pipeline-storage commitments; electric-capacity schedule differs. |
| D/2002/page_87.pdf-3 | yes | valid | 2002/2001rent84/75m matches; projected lease payments are not historical expense duplicates. |
| D/2002/page_87.pdf-4 |  | valid | 2001/2000rent75/107m matches; projected lease payments differ. |
| DG/2005/page_44.pdf-1 |  | valid | Feb2006/Jan2005 LIFO excess5.8/6.3m matches. Fiscal2005 separately disclosed0.5m reserve decrease constrains difference. |
| DG/2007/page_67.pdf-1 | yes | uncertain | 0.2m explicitly2007 predecessor period, not whole2007. Question omits scope qualification; annual comparison uncertain. |
| DG/2007/page_67.pdf-2 |  | uncertain | 2007component explicitly predecessor-period only; complete2005-2007 total scope not established. |
| DRE/2002/page_15.pdf-2 |  | valid | 2001/2000G&A15.6/21.1m matches; property gain table unrelated. |
| DRE/2002/page_15.pdf-4 |  | valid | 2001/2000service earnings35.1/32.8m matches; service revenue and expense-change disclosures give further linear relation. |
| DVN/2014/page_87.pdf-1 |  | uncertain | 30/164m are maturity buckets of contractual credit facility; whether nominal limits exact rather than rounded is unresolved. |
| DVN/2014/page_87.pdf-2 |  | invalid | Rate0.44percent is multiplied as0.44 without/100. Result does not yield implied dollar interest; weighted-value question ill-defined. |
| DVN/2015/page_79.pdf-3 |  | uncertain | Volatility28.8/30.3 are valuation assumptions based on history. Whether rounded estimate or exact setting unestablished; question also omits years. |
| DVN/2018/page_35.pdf-1 |  | valid | 2018/2017total tax156/15m matches ratio; each total=current+deferred. |
| DVN/2018/page_35.pdf-2 |  | valid | 2018/2017total tax156/15m matches percentage growth; each total=current+deferred. |
| DVN/2018/page_35.pdf-3 |  | valid | Duplicate benchmark question/program retained for benchmark denominator, not independent economic evidence; total=current+deferred. |
| DVN/2018/page_35.pdf-4 |  | uncertain | Gold tax(2.6-2.2)/aftertax2.2 differs from conventional pretax tax rate; wording on net earnings ambiguous. |
| EL/2008/page_59.pdf-1 |  | invalid | 1.7m is25bp pension expense sensitivity, not level of expected return; dividing by7.75% cannot recover plan assets.47m expected return differs in scope. |
| EL/2008/page_59.pdf-2 |  | uncertain | 34m is deferred loss subject to future amortization, not annual amortization expense. Fraction-subject-to-amortization interpretation plausible; wording expenses ambiguous. |
| EOG/2018/page_75.pdf-2 |  | valid | 12m earnings-impact subset/29m unrecognized benefits matches; valuation allowance167142thousand is distinct. |
| ETFC/2011/page_144.pdf-2 |  | invalid | Question asks2010collateral19.3m but gold selects2011 2.3m and2010borrowings0.5m. Wrong year. |
| ETR/2004/page_239.pdf-4 |  | invalid | Question asks2003 O&M increase;6.6+3.7 are2004vs2003 gross drivers and omit7.1offset. Not requested2003 net increase. |
| ETR/2011/page_17.pdf-2 |  | valid | 13/24/49m are all positive2011 net-revenue bridge movements; full bridge constrains favorable-variance sum. |
| ETR/2015/page_17.pdf-1 | yes | valid | 2015/2014revenues5829/5735m and baseline match; complete revenue bridge applies. |
| ETR/2015/page_17.pdf-2 |  | valid | Same2015/2014revenue bridge and baseline; second question on same economic facts. |
| ETR/2015/page_17.pdf-4 |  | invalid | Question regulatory-liability/tax-liability ratio differs from gold(107-66)/66 tax benefit/net liability. |
| ETR/2016/page_150.pdf-3 |  | valid | All5NewOrleans2017-2021expected payments are included; Texas transition-bond table is different entity. |
| ETR/2016/page_150.pdf-4 | yes | invalid | Question next3years, gold adds only2017 10.6m+2018 11m, omitting2019 11.2m. |
| ETR/2016/page_23.pdf-1 |  | valid | 2015/2014Entergy revenue growth matches full bridge; repeated economic facts from prior report remain separate benchmark context. |
| ETR/2016/page_23.pdf-2 |  | valid | 2015/2014Entergy revenue difference matches full bridge. |
| ETR/2016/page_374.pdf-2 |  | valid | Typo20016 clearly2016given table;705.4/696.3 and base correct; full bridge applies. |
| ETR/2016/page_374.pdf-3 |  | valid | Typo20016 clearly2016given table;705.4-696.3 correct; full bridge applies. |
| ETR/2017/page_372.pdf-3 | yes | invalid | Decrease2016to2017 should use2016base705.4. Gold705.4/703.1-1 uses ending denominator; incorrect baseline despite small difference. |
| FIS/2012/page_48.pdf-1 |  | uncertain | Question earnings but table lacks preceding metric explanation; nearby text distinguishes insignificant earnings effect from revenue effect. Metric identity unverified. |
| FIS/2012/page_48.pdf-2 | yes | valid | Generic euro impact question matches table2011/2012 values, without the earnings-target conflict of adjacent questions. |
| FIS/2012/page_48.pdf-3 |  | uncertain | Question labels table impact earnings but surrounding text distinguishes earnings/revenue and lead-in absent. Metric identity unverified. |
| FIS/2016/page_45.pdf-4 |  | valid | 2015/2014cashflows1131/1165m match. Separately stated34mdecrease and2016 794mincrease constrain differences. |
| FIS/2017/page_64.pdf-2 |  | valid | Euro38m/total129m sensitivity2016 matches; four currency components sum total. |
| FIS/2017/page_64.pdf-4 |  | valid | Euro35m/total130m sensitivity2017 matches; four currency components sum total. |
