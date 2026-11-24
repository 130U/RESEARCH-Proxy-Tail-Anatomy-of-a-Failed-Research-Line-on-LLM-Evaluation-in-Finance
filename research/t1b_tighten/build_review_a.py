"""Compile source-review annotations. Judgments are source-reviewed, not inferred by code."""
import json
from pathlib import Path
from fractions import Fraction as F
P = Path(__file__).resolve().parent
xs = json.loads((P/'packets_a.json').read_text(encoding='utf8'))
notes = '''
2010 pension minimum contributions are monetary estimates; approximately460m has no more precise disclosure here. Statutory minimum does not make a reported million-dollar aggregate exact.
2010/2009 slot-and-route carrying amounts708/736m match. The28m impairment concerns certain routes plus other slots/routes, not an exhaustive carrying-value rollforward.
2013/2012 fuel cost3.09/3.20 per gallon matches growth. Cost/gallons disclosures do not establish a valid linear identity on average prices.
Hedge effect naturally means reduction from unhedged104m, but gold divides104-87 by hedged87m; comparison base is ambiguous.
Ending retirement liability7.2m less1.2m accretion matches question. Opening5.5m+new0.5m+accretion is documented reconciliation; row0 is data.
Risk-free rates2.56/2.92 are Black-Scholes assumptions; context does not establish whether fixed parameter settings or rounded estimates. Quantity uncertain.
Cash requirement1.8m applies to remaining combined11.2m contingent payments, while5.6m is one milestone. Precise contractual5583333-dollar amount appears in P20. Rounded-independent assumptions and June-specific cash allocation are unsupported.
Rent expenses1.6/2.7/2.2m correspond to2012/2011/2010; future lease payments and particular-property base rent are different quantities.
Severance0.3m+lease termination0.1m are requested balances; with canceled-contract0.4m they exhaust remaining0.772m accrual.
Canceled contracts0.4m is component of remaining1998-program accrual. Table772thousand equals text0.8m because P12 says older merger accruals are zero.
Notional undesignated hedges42.1/38m match2010/2009; designated swaps and fixed debt elsewhere differ.
Discontinued-operation14m/all169m lease commitments matches; both columns sum over maturity buckets.
2003 commitments30m/all169m matches; complete maturity sum valid, arbitrary equalities between years invalid.
2015 disposed-site remediation2.8m is subset of15.2m reserve;2014 amounts and expenses are distinct.
2014 reserve8.8m minus expense2.9m matches requested difference; deliberately compares stock and flow.
2016/2015 facility lease obligation136/133 is millions per P1; table debt maturities concern other liabilities.
Accrued interest4.8m/aggregate redemption221.9m matches. Documented contractual redemption factor also links principal, total and interest.
Gold computes accrued-interest/principal for partial accrual period; question asks interest rate explicitly stated as6.25% coupon.
2005/2004 non-core impairment/net losses16.8/17.7m match gold-supported metric; construction-in-progress is separate component of total.
2004/2003 non-core17.7/19.1m match;19.1m total for2005 elsewhere is a different metric/year.
2006/2005/2004 construction-in-progress1.0/2.3/4.6m match, mean uses exact count3; significant-component list is not assumed exhaustive.
2008/2007 non-core net10.5/7.1m match. Passage is duplicated verbatim; gross losses less gains constrain net amounts.
2014/2013 impairment11.2/15.9m match and equal carrying values before minus after each write-down.
1.3m is stated for each of3years. Multiplying interval by3 gives same sum range as three separately rounded years, without claiming equal latent residuals.
2007/2006 derivative OCI gains24/15m match; four OCI categories sum to accumulated OCI loss.
2007 expense,signed cash payments,FX are complete movements in liability bridge.
2006 expense,signed cash payments,FX are complete movements in liability bridge.
57m tax-rate-impact subset/70m total matches; complete signed rollforward constrains total.
24m prior-year additions minus4m current-year additions matches; both in2007 rollforward.
411636 is exact issued-share count, not rounded scaled count.9m compensation expense/share is not employee purchase price under85%-of-market plan.
Interest/penalty liabilities77/55m match2018/2017.22m accrual is not established as sole movement; no equality imposed from arithmetic coincidence.
2017prior-year tax additions12m less2018 10m is requested decrease; each belongs to complete rollforward.
Question asks decrease of fair value without saying percentage; gold returns relative change. Binding correct, requested answer dimension ambiguous.
Quarterly dividends are board-declared per-share amounts; annual4.25/3.71 are exact payouts, not uncertain independently rounded aggregates.
2017/2016 average borrowings779/850 match; maximum/year-end borrowings are different measures.
Daily weighted-average rates1.24/0.78 are computed averages, plausibly rounded, not fixed contract terms; December-end rates differ.
2017repurchase cost54m/shares0.7million yields dollars/share; scaled shares are rounded counts.
2018repurchase cost45m/shares0.6million yields dollars/share; authorization and unpurchased shares differ.
Repurchased shares0.6+0.7million sum2018/2017; these are rounded million-scaled counts.
2014/2013 rent-office expense132/137m matches; future lease commitments differ.
2013/2012 rent-office expense137/133m matches; no higher precision of historical expense appears.
PennyMac fair values348/259m match2017/2016; carrying342/301m are distinct.
PennyMac carrying342/301m match2017/2016; fair348/259m are distinct.
Approximately50percent of approximately897m backlog is requested fixed-price share; percentage is empirical composition.
Tax rate on pretax impairment normally(9.6-8.7)/9.6; gold divides by aftertax8.7, a different ratio.
5bn increase/6.2bn net transfer matches. Narrative driven-by and offset-by1.4 is not exhaustive; no5=6.2-1.4 assumption.
2009cost2.5bn/fair1.6bn matches; fair value splits into Level2+Level3.
Adjacent sentences establish both160m pension and72m postretirement contributions as non-US2010. Included in purchase obligations but no exhaustive composition.
Multiheader identifies treasury market values2075/2068m as2010/2009; percentage columns differ. Two classifications partition same total portfolio.
2010/2009 hedge-instrument fair21/47m matches difference; realized hedge losses and guarantee liabilities differ.
2010/2009 hedge-instrument fair21/47m matches growth; realized hedge losses and guarantee liabilities differ.
Gold divides shares/expenses each year; question requests expense/share. Both ratios inverted.
2013/2012 cash dividends received92/83m are aggregate receipts, not declared per-share amounts.
2012/2011 cash dividends received83/78m are aggregate receipts, not declared per-share amounts.
2015/2014R&D119/86m matches difference; ownership percentages in table unrelated.
2016/2015R&D78/119m matches signed difference; ownership percentages unrelated.
End2015/2014 unrecognized benefits1136/1171m match;1171 also opening2015 and all years have complete bridges.
2.9 is billion,900.1 is million; gold misses factor1000. Issuance also2008, not question2009.
1.4bn senior facility and945.5m revolver match with correct1000 conversion. P44 says including term420.5m and revolver, but does not establish an exhaustive partition; their exact sum is optional sensitivity only.
2010/2009broker receivables11.2/8.8m match; both components of other-current-asset totals.
Denominator literal3 is exact year count, but T1 binds it to2015 3.0% state tax cell as independent noisy input. Binding/type error.
34/23/13m are2003/2004/2005pipeline-storage commitments; electric-capacity schedule differs.
2002/2001rent84/75m matches; projected lease payments are not historical expense duplicates.
2001/2000rent75/107m matches; projected lease payments differ.
Feb2006/Jan2005 LIFO excess5.8/6.3m matches. Fiscal2005 separately disclosed0.5m reserve decrease constrains difference.
0.2m explicitly2007 predecessor period, not whole2007. Question omits scope qualification; annual comparison uncertain.
2007component explicitly predecessor-period only; complete2005-2007 total scope not established.
2001/2000G&A15.6/21.1m matches; property gain table unrelated.
2001/2000service earnings35.1/32.8m matches; service revenue and expense-change disclosures give further linear relation.
30/164m are maturity buckets of contractual credit facility; whether nominal limits exact rather than rounded is unresolved.
Rate0.44percent is multiplied as0.44 without/100. Result does not yield implied dollar interest; weighted-value question ill-defined.
Volatility28.8/30.3 are valuation assumptions based on history. Whether rounded estimate or exact setting unestablished; question also omits years.
2018/2017total tax156/15m matches ratio; each total=current+deferred.
2018/2017total tax156/15m matches percentage growth; each total=current+deferred.
Duplicate benchmark question/program retained for benchmark denominator, not independent economic evidence; total=current+deferred.
Gold tax(2.6-2.2)/aftertax2.2 differs from conventional pretax tax rate; wording on net earnings ambiguous.
1.7m is25bp pension expense sensitivity, not level of expected return; dividing by7.75% cannot recover plan assets.47m expected return differs in scope.
34m is deferred loss subject to future amortization, not annual amortization expense. Fraction-subject-to-amortization interpretation plausible; wording expenses ambiguous.
12m earnings-impact subset/29m unrecognized benefits matches; valuation allowance167142thousand is distinct.
Question asks2010collateral19.3m but gold selects2011 2.3m and2010borrowings0.5m. Wrong year.
Question asks2003 O&M increase;6.6+3.7 are2004vs2003 gross drivers and omit7.1offset. Not requested2003 net increase.
13/24/49m are all positive2011 net-revenue bridge movements; full bridge constrains favorable-variance sum.
2015/2014revenues5829/5735m and baseline match; complete revenue bridge applies.
Same2015/2014revenue bridge and baseline; second question on same economic facts.
Question regulatory-liability/tax-liability ratio differs from gold(107-66)/66 tax benefit/net liability.
All5NewOrleans2017-2021expected payments are included; Texas transition-bond table is different entity.
Question next3years, gold adds only2017 10.6m+2018 11m, omitting2019 11.2m.
2015/2014Entergy revenue growth matches full bridge; repeated economic facts from prior report remain separate benchmark context.
2015/2014Entergy revenue difference matches full bridge.
Typo20016 clearly2016given table;705.4/696.3 and base correct; full bridge applies.
Typo20016 clearly2016given table;705.4-696.3 correct; full bridge applies.
Decrease2016to2017 should use2016base705.4. Gold705.4/703.1-1 uses ending denominator; incorrect baseline despite small difference.
Question earnings but table lacks preceding metric explanation; nearby text distinguishes insignificant earnings effect from revenue effect. Metric identity unverified.
Generic euro impact question matches table2011/2012 values, without the earnings-target conflict of adjacent questions.
Question labels table impact earnings but surrounding text distinguishes earnings/revenue and lead-in absent. Metric identity unverified.
2015/2014cashflows1131/1165m match. Separately stated34mdecrease and2016 794mincrease constrain differences.
Euro38m/total129m sensitivity2016 matches; four currency components sum total.
Euro35m/total130m sensitivity2017 matches; four currency components sum total.
'''.strip().splitlines()
assert len(notes)==98
invalid={6,17,29,33,44,51,57,60,70,76,79,80,84,86,91}
uncertain={3,5,32,65,66,69,71,75,77,92,94}
R=[]
for k,x in enumerate(xs):
 v='invalid' if k in invalid else 'uncertain' if k in uncertain else 'valid'
 R.append(dict(id=x['id'],binding_ok=k not in {60,79},quantity_ok=k not in {5,6,29,33,69,71},program_ok=k not in (invalid|uncertain)-{5,33,69,71},verdict=v,reason=notes[k],input_review=[dict(variable=n,location=z['location'],judgment='source matched; see question-level caveats' if v!='valid' else 'source matched',reason=z['context'],duplicate_search='All supplied table and pre/post context screened by metric,period,unit; any confirmed extra occurrence is listed in duplicates.') for n,z in x['audit']['input_provenance'].items()],duplicates=[],extra_bounds={},equations=[],rejected_relations=[],context_reviewed=True,sample40=x['sample40'],review_method='LLM-assisted source inspection; not human signoff'))
def eq(k,terms,why):R[k]['equations'].append(dict(terms={n:str(c) for n,c in terms.items()},reason=why))
def aux(k,n,v,h='0.05'):
 v,h=F(str(v)),F(str(h));R[k]['extra_bounds'][n]=[str(v-h),str(v+h)];return n
def sr(k,rows,target,cols,why):
 for c in cols:eq(k,{**{f'table_{r}:{c}':1 for r in rows},f'table_{target}:{c}':-1},why)
def bc(k,row,start,moves,end,why):eq(k,{**{f'table_{row}:{c}':1 for c in [start]+moves},f'table_{row}:{end}':-1},why)
def dup(k,var,lo,hi,source,why,**kw):R[k]['duplicates'].append(dict(variable=var,lo=str(F(str(lo))),hi=str(F(str(hi))),source=source,reason=why,**kw))
sr(4,[0,1,2],3,[1],'Retirement liability opening+additions+accretion=ending.')
sr(6,[0,1],2,[1],'Tax-benefit beginning+signed reductions=ending; separate from Impella question.')
sr(7,list(range(1,7)),7,[1],'Complete lease-maturity schedule.')
for k in [11,12]:sr(k,list(range(1,7)),7,[1,2],'Complete lease-maturity schedule in total/discontinued columns.')
for k in [16,17]:
 sr(k,list(range(0,6)),6,[1],'Complete cash-obligation maturities.')
 sr(k,[6,7,8],9,[1],'Cash obligations plus signed original discounts and warrants equals total.')
for k in [18,19,20]:
 sr(k,[1,2],3,list(range(1,11)),'Employee and facility categories sum to restructuring total.')
 for row in [1,2,3]:
  for start,moves,end in [(1,[2,3],4),(4,[5,6],7),(7,[8,9],10)]:bc(k,row,start,moves,end,'Complete annual liability reconciliation including signed expenses and cash payments.')
for start,moves,end in [(1,[2,3,4],5),(5,[6,7,8],9),(9,[10,11,12],13)]:bc(21,1,start,moves,end,'Complete annual merger employee-liability reconciliation.')
R[21]['extra_bounds']['table_1:13']=['0','0']
for c in [1,2]:
 if c==2:R[22]['extra_bounds']['table_6:2']=['-1/2','1/2']
 sr(22,list(range(1,7)),7,[c],'Complete contingent-consideration balance bridge. Dash conservatively rounded zero.')
sr(23,list(range(2,8)),8,[1,2,3],'Geographic revenue categories exhaust total.')
sr(24,[1,2,3,4],5,[1,2,3],'Four OCI components sum to accumulated OCI.')
for k in [25,26]:
 R[k]['extra_bounds']['table_0:1']=['0','0']
 for start,moves,end in [(0,[1,2,3],4),(4,[5,6,7],8),(8,[9,10,11],12)]:eq(k,{**{f'table_{r}:1':1 for r in [start]+moves},f'table_{end}:1':-1},'Complete annual restructuring bridge. Beginning2005 plan balance structural zero.')
for k in [27,28]:sr(k,[0,1,2,3,4],5,[1],'Complete unrecognized-tax-benefit balance bridge.')
for k in [30,31]:
 for c in [1,2]:
  for i in range(1,9):
   if xs[k]['document']['table_ori'][i][c]=='—':R[k]['extra_bounds'][f'table_{i}:{c}']=['-1/2','1/2']
  sr(k,list(range(1,9)),9,[c],'Complete uncertain-tax-position bridge. Dashes conservatively rounded zeros.')
 eq(k,{'table_1:1':1,'table_9:2':-1},'Beginning2018 is same fact as ending2017.')
sr(32,[1,2],3,[1],'Restricted-share opening+signed vested=closing; thousands of shares.')
sr(33,[1,2,3,4],5,[1,2],'Declared quarterly dividends sum to annual total. Excluded from rounding inference as exact per-share declarations.')
for k in [39,40]:sr(k,list(range(1,7)),7,[1],'Complete future operating-lease schedule, distinct from historical rent expense.')
for k in [41,42]:
 sr(k,list(range(1,7)),7,[1,2,3,4],'Debt issues exhaust total in each monetary column.')
 for r in range(1,8):eq(k,{f'table_{r}:1':1,f'table_{r}:2':1,f'table_{r}:3':-1},'Maturity plus signed discount and issuance costs equals carrying amount.')
for k in [45,46]:
 for r in [1,2]:eq(k,{f'table_{r}:2':-1,f'table_{r}:3':1,f'table_{r}:4':1},'Fair value is sum of Level2 and Level3.')
sr(47,[2,3,4,5],6,list(range(1,7)),'Contractual obligation categories exhaust each maturity total.')
for c in [1,3]:
 sr(48,list(range(2,9)),9,[c],'Asset-class market values sum to portfolio total.')
 sr(48,list(range(10,17)),17,[c],'Rating-class market values sum to same portfolio total.')
 eq(48,{f'table_9:{c}':1,f'table_17:{c}':-1},'Same portfolio total repeated for two classifications.')
for k in [49,50]:
 sr(k,list(range(1,10)),10,[1],'Eligibility-period proportions exhaust total account value, in percent units.')
 for rr in range(1,11):
  vv=F(xs[k]['document']['table_ori'][rr][1].replace('%',''))
  R[k]['extra_bounds'][f'table_{rr}:1']=[str(max(F(0),vv-F(1,2))),str(vv+F(1,2))] if rr<10 else ['100','100']
sr(51,[2,3],4,[1,2,3],'Basic shares+dilutive effect=diluted shares.')
for c in [1,2,3]:
 if c in [1,2]:R[56]['extra_bounds'][f'table_4:{c}']=['-1/2','1/2']
 sr(56,list(range(1,8)),8,[c],'Complete tax-benefit rollforward; dash conservatively rounded zero.')
eq(56,{'table_1:1':1,'table_8:2':-1},'End2014=beginning2015.')
eq(56,{'table_1:2':1,'table_8:3':-1},'End2013=beginning2014.')
for c in [1,2]:
 if c==1:R[59]['extra_bounds']['table_8:1']=['-1/20','1/20']
 sr(59,list(range(1,10)),10,[c],'All current-asset components exhaust total; missing CBOE amount conservatively rounded zero.')
for c in [1,2,3]:
 for i in range(1,9):
  if xs[60]['document']['table_ori'][i][c]=='—':R[60]['extra_bounds'][f'table_{i}:{c}']=['-1/20','1/20']
 sr(60,list(range(1,9)),9,[c],'Statutory rate plus signed tax reconciliations=effective rate, in percentage points.')
 R[60]['extra_bounds'][f'table_1:{c}']=['35','35']
 raw=xs[60]['document']['table_ori'][9][c].replace('%',''); val=F(raw.strip('()'))*(-1 if '(' in raw else 1)
 R[60]['extra_bounds'][f'table_9:{c}']=[str(val-F(1,20)),str(val+F(1,20))]
for k in [61,62,63]:sr(k,list(range(2,8)),8,[1,2],'Electric-capacity and other commitments exhaust their maturity totals; not gas/rent questions.')
for k in [67,68]:sr(k,[1,2,3],4,[1,2],'Property gain+land gain+signed impairment=total.')
for k in [69,70]:
 R[k]['extra_bounds']['table_2:1']=['-1/2','1/2'];sr(k,list(range(0,6)),6,[1],'Debt maturities exhaust total; dash conservatively rounded zero.')
for k in [72,73,74,75]:sr(k,[1,2],3,[1,2],'Current+deferred tax expense/benefit=total.')
sr(78,[1,2,3,4],5,[1,2,3],'Complete deferred-tax valuation allowance bridge, distinct from questioned tax benefit.')
sr(79,list(range(1,9)),9,[1],'Trust face amounts exhaust total; maturity and rate columns are not monetary sums.')
sr(80,[1,2,3],4,[1],'Opening net revenue+base rates+other=ending.')
sr(81,list(range(1,9)),9,[1],'Complete bridge of all favorable/unfavorable net-revenue movements.')
for k in [82,83,84,87,88]:sr(k,list(range(1,8)),8,[1],'Complete2014-to2015net-revenue bridge; no arbitrary subset.')
for k in [85,86]:sr(k,[2,3,4],5,[1],'Texas transition-bond tranches exhaust total; not NewOrleans question.')
for k in [89,90]:sr(k,list(range(1,7)),7,[1],'Complete2015-to2016Mississippi net-revenue bridge.')
sr(91,[1,2,3,4],5,[1],'Complete2016-to2017Mississippi net-revenue bridge.')
for k in [92,93,94,96,97]:sr(k,[1,2,3,4],5,[1,2,3],'Four currency components exhaust total for each year.')
sr(95,[2,3,4,5,6],7,[1,2,3,4,5],'Five contractual-obligation categories exhaust each maturity-column total.')
for r in range(2,8):eq(95,{f'table_{r}:1':-1,**{f'table_{r}:{c}':1 for c in range(2,6)}},'Four maturity buckets exhaust obligation-category total.')
# Same economic fact at different displayed precision.
dup(6,'x1','5.583333','5.583333','text_20:263, $5583333 Impella2.5 milestone','Same contractual milestone dollar amount, exact stated obligation. Impella5.0 is a separate milestone.')
dup(9,'x1','0.7715','0.7725','table_1:5, $772 thousand','Remaining1998-program accrual equals all remaining prior restructuring accrual because P12 states older-program residuals zero.',location='table_1:5',scale='1/1000')
eq(9,{'x1':1,'table_1:5':'-1/1000'},'Same ending accrual with million/thousand unit conversion.')
for k in [8,9]:
 R[k]['extra_bounds']['table_1:2']=['0','0']
 bc(k,1,1,[2,3,4],5,'Prior-restructuring accrual reconciliation; no new charges is structural zero.')
 s=aux(k,'text_severance','0.3');l=aux(k,'text_lease','0.1');c=aux(k,'text_canceled','0.4')
 eq(k,{s:1,l:1,c:1,'table_1:5':'-1/1000'},'P3 exhaustive residual components; P12 removes older-program scope discrepancy.')
 if k==8:
  eq(k,{'x0':1,s:-1},'Same severance fact.');eq(k,{'x1':1,l:-1},'Same lease termination fact.')
 else:eq(k,{'x0':1,c:-1},'Same canceled-contract balance.')
for k in [16,17]:
 a=aux(k,'redemption_principal','212.7');b=aux(k,'redemption_price','221.9');c=aux(k,'redemption_interest','4.8')
 eq(k,{b:1,a:'-102083/100000',c:-1},'P7 contractual redemption at102.083%principal plus accrued interest; stated coefficient treated exact contractual term.')
 eq(k,{'x0':1,c:-1},'Same accrued-interest fact.')
 eq(k,{'x1':1,(b if k==16 else a):-1},'Same aggregate redemption or principal fact.')
# 'Significant components ... include' does not assert an exhaustive partition.
# Do not turn matching reported centers into total=noncore+CIP equalities.
for k in [18,19,20]:
 R[k]['rejected_relations'].append(dict(kind='non_exhaustive_text_components',reason='AMT text lists significant components that include noncore and construction-in-progress impairment, but does not state these exhaust total impairment/net losses. Exact equality removed after independent review.'))
aux(20,'noncore_0','2.0')
gl=aux(20,'gross_noncore_loss_2006','7.0');gg=aux(20,'noncore_gains_2006','5.1');eq(20,{'noncore_0':-1,gl:1,gg:-1},'P13 further decomposes2006noncore net losses into7.0gross losses less5.1gains; rounded centers differ0.1 but intervals overlap.')
for i,loss,gain in [(0,'10.7','0.2'),(1,'7.8','0.7')]:
 l=aux(21,f'gross_loss_{i}',loss);g=aux(21,f'gain_{i}',gain);eq(21,{f'x{i}':-1,l:1,g:-1},'P7/P8net loss=gross losses and impairments less asset gains.')
 z=xs[21]['audit']['input_provenance'][f'x{i}'];dup(21,f'x{i}',F(z['value'])-F(z['half']),F(z['value'])+F(z['half']),'text_6 repeats text_26','Identical paragraph, same metric/year; no precision gain.')
for i,before,after in [(0,'8900.0','8888.8'),(1,'8554.5','8538.6')]:
 b=aux(22,f'carrying_before_{i}',before);a=aux(22,f'carrying_after_{i}',after);eq(22,{b:1,a:-1,f'x{i}':-1},'P6/P7impairment writes carrying value down to net realizable value.')
z=xs[56]['audit']['input_provenance']['x1'];dup(56,'x1',F(z['value'])-F(z['half']),F(z['value'])+F(z['half']),'table_1:1','Same ending2014/beginning2015tax-benefit balance.',location='table_1:1',scale='1')
dup(56,'x0','1050','1150','text_7:$1.1billion','Same total at coarser precision; no marginal tightening.')
t=aux(58,'term_loan','420.5')
R[58]['optional_sensitivity_equations']=[dict(terms={'x0':'1000',t:'-1','x1':'-1'},reason='Extra assumption: the two facilities named by including in combined text_44 exhaust the1.4billion senior credit facility. Surrounding text_45-52 does not establish this, so excluded from primary constraints.')]
R[58]['rejected_relations'].append(dict(kind='non_exhaustive_text_components',reason='Credit facility including term loan and revolver does not conclusively assert exhaustiveness; available context does not rule out another component or a commitment-versus-outstanding-balance distinction. Exact total=term+revolver kept only as optional sensitivity.'))
eq(58,{t:1,'table_1:1':-1},'Same term loan in P44 and debt table.')
d=aux(64,'lifo_decrease','0.5');eq(64,{'x0':1,'x1':-1,d:1},'P5fiscal2005 LIFOreserve decrease is change Jan2005toFeb2006.')
r0=aux(68,'service_revenue_2001','80.5');r1=aux(68,'service_revenue_2000','82.8');e=aux(68,'service_expense_decrease','4.7');eq(68,{'x0':1,'x1':-1,r0:-1,r1:1,e:-1},'Earnings change=revenue change minus expense change; P5/P14same-segment totals.')
a=aux(77,'expected_return','47.0');b=aux(77,'actual_loss','19.3');eq(77,{'x1':-1,a:1,b:1},'P26deferred loss=expected return minus negative actual return.')
dup(84,'x0','106.5','107.5','text_9 and table_4:1 absolute customer-credit amount','P9/P10regulatory liability is customer credits; table revenue effect is opposite signed.')
eq(84,{'x0':1,'table_4:1':1},'Customer-credit revenue change is negative of positive regulatory liability.')
d=aux(95,'cashflow_decrease_2015','34','0.5');eq(95,{'x0':1,'x1':-1,d:1},'P12separately discloses2015operating cashflow decrease.')
c=aux(95,'cashflow_2016','1925','0.5');e=aux(95,'cashflow_increase_2016','794','0.5');eq(95,{c:1,'x0':-1,e:-1},'P10/P12link2016cashflow and increase to2015.')

def norm(d):
 dd={a:F(str(b)) for a,b in d.items()};first=next(iter(sorted(dd)));sgn=1 if dd[first]>0 else -1
 return tuple(sorted((a,b*sgn) for a,b in dd.items()))
cs=json.loads((P/'sum_candidates_a.json').read_text(encoding='utf8'))
dc=json.loads((P/'duplicate_candidates_a.json').read_text(encoding='utf8'))
for k,x in enumerate(xs):
 r=R[k]; accepted={norm(e['terms']) for e in r['equations']}
 for idx,z in enumerate(cs[x['id']]):
  matches=[norm({f'table_{i}:{c}':v for i,v in z['rows'].items()}) in accepted for c in z['columns']]
  if not all(matches):r['rejected_relations'].append(dict(kind='sum_candidate',candidate_index=idx,rows=z['rows'],columns=z['columns'],reason='No additional semantic identity beyond complete documented totals/bridges listed in equations; arbitrary subsets may match numerically. Algebraic consequences of accepted bridges are redundant.'))
 for idx,z in enumerate(dc.get(x['id'],[])):
  confirmed=(k==6 and z['candidate_location']=='text_20:263') or k==9
  r.setdefault('duplicate_candidate_review',[]).append(dict(candidate_index=idx,variable=z['variable'],location=z['candidate_location'],judgment='confirmed' if confirmed else 'rejected',reason='Same metric,period,unit as documented duplicate.' if confirmed else ('Other Impella5.0 milestone, not JuneImpella2.5.' if k==6 else 'Different metric/year/unit or metadata numeral; numerical overlap under arbitrary scaling is not identity.')))
 if k in [1,2,30,45]:r['rejected_relations'].append(dict(reason=notes[k]))
(P/'review_a.json').write_text(json.dumps(R,ensure_ascii=False,indent=2),encoding='utf8')
from collections import Counter
summary=Counter(r['verdict'] for r in R); sample=Counter(r['verdict'] for r in R if r['sample40'])
md=['# T1B source review A','', 'Scope: 98 sorted cohort questions, complete FinQA supplied context. This is LLM-assisted source inspection, not human signoff and not review of entire original annual reports. References Pn mean zero-based combined pre_text + post_text index n (equivalently text_n), not a post_text-only index.', '',f'Judgments: {dict(summary)}. Fixed-seed sample subset: {dict(sample)}.', '', 'Every question was read for metric, entity, period, unit, quantitative type and gold-program meaning. Numeric/unit candidates were checked against economic identity. No unlisted higher-precision input occurrence was confirmed. Supplemental equations include text-defined component sums; numerical near-equalities alone were rejected. Uncertain cases are conservatively excluded from clean retained conclusions. Structural zeros and rounded dashes are explicitly distinguished in annotations. Independent review removed seven AMT2005/2006 total=noncore+CIP equalities because the source enumeration is not explicitly exhaustive. Explicit comprised-of gross-loss-minus-gain equations remain.','', '| Question | Sample | Judgment | Reason |','|---|---|---|---|']
md.extend(f"| {r['id']} | {'yes' if r['sample40'] else ''} | {r['verdict']} | {r['reason']} |" for r in R)
(P/'review_a.md').write_text('\n'.join(md)+'\n',encoding='utf8')
print(summary, 'sample',sample,'equations',sum(len(r['equations']) for r in R),'duplicates',sum(len(r['duplicates']) for r in R))
