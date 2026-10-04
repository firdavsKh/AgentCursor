# PB Hierarchy

Detailed PB tables allocated under the rows of the high-level tables (PB1, PB2).

```mermaid
flowchart LR
  root["High-level tables<br/>PB1: Brief analytical BoP presentation<br/>PB2: Brief standard BoP presentation"]
  ca["I. Current account"]
  root --> ca
  gs["1. Goods and services"]
  ca --> gs
  goods["1.1 Goods"]
  gs --> goods
  g_adj["Trade adjustments and balance"]
  goods --> g_adj
  g_adj_pb(["PB3 · PB4"])
  g_adj --> g_adj_pb
  g_cty["Trade by country"]
  goods --> g_cty
  g_cty_pb(["PB5 · PB6 · PB24 · PB27"])
  g_cty --> g_cty_pb
  g_cmd["Trade by commodity"]
  goods --> g_cmd
  g_cmd_pb(["PB10"])
  g_cmd --> g_cmd_pb
  g_exp["Exports by commodity"]
  g_cmd --> g_exp
  g_exp_pb(["PB7 · PB9 · PB11 · PB13 · PB15 · PB17 · PB19 · PB21"])
  g_exp --> g_exp_pb
  g_imp["Imports by commodity"]
  g_cmd --> g_imp
  g_imp_pb(["PB8 · PB12 · PB14 · PB16 · PB18 · PB20 · PB22"])
  g_imp --> g_imp_pb
  serv["1.2 Services"]
  gs --> serv
  serv_pb(["PB23"])
  serv --> serv_pb
  pi["2. Primary income"]
  ca --> pi
  pi_pb(["PB25"])
  pi --> pi_pb
  si["3. Secondary income"]
  ca --> si
  si_pb(["PB26"])
  si --> si_pb
  cap["II. Capital account"]
  root --> cap
  fa["III. Financial account"]
  root --> fa
  di["4. Direct investment"]
  fa --> di
  di_pb(["PB28 · PB30"])
  di --> di_pb
  pf["5. Portfolio investment"]
  fa --> pf
  pf_pb(["PB29"])
  pf --> pf_pb
  der["6. Financial derivatives"]
  fa --> der
  oi["7. Other investment"]
  fa --> oi
  oi_a["7.1 Assets"]
  oi --> oi_a
  oi_a_pb(["PB31"])
  oi_a --> oi_a_pb
  oi_l["7.2 Liabilities"]
  oi --> oi_l
  oi_l_pb(["PB32"])
  oi_l --> oi_l_pb
  res["Reserve assets"]
  fa --> res
  classDef empty stroke-dasharray: 4 4,color:#888
  class cap,der,res empty
```

## Allocation

| PB | BoP item | Basis |
|---:|---|---|
| 1 | High-level table | Brief analytical BoP presentation |
| 2 | High-level table | Brief standard BoP presentation |
| 3 | Trade adjustments and balance | Foreign trade turnover with NBT adjustments (coverage, FOB, processing) |
| 4 | Trade adjustments and balance | Trade balance by main commodities with volumes and world prices |
| 5 | Trade by country | Export / import / surplus by country |
| 6 | Trade by country | Export / import / surplus by country |
| 7 | Exports by commodity | Total on export |
| 8 | Imports by commodity | Total on import |
| 9 | Exports by commodity | Exports: nuts, grapes, dried fruits, oilseeds |
| 10 | Trade by commodity | Trade by commodity section (HS sections) |
| 11 | Exports by commodity | Total on export |
| 12 | Imports by commodity | Total on import |
| 13 | Exports by commodity | Total on export |
| 14 | Imports by commodity | Imports: wheat, oil products, chemicals |
| 15 | Exports by commodity | Total on export |
| 16 | Imports by commodity | Imports: wheat, flour, vegetable oil |
| 17 | Exports by commodity | Total on export |
| 18 | Imports by commodity | Total on import |
| 19 | Exports by commodity | Total on export |
| 20 | Imports by commodity | Total on import |
| 21 | Exports by commodity | Total on export |
| 22 | Imports by commodity | Total on import |
| 23 | 1.2 Services | Services by type, credits and debits |
| 24 | Trade by country | Export / import by country |
| 25 | 2. Primary income | Compensation of employees, investment income |
| 26 | 3. Secondary income | General government and private transfers, remittances |
| 27 | Trade by country | Trade by country, weight and cost |
| 28 | 4. Direct investment | Direct investment inflows and outflows |
| 29 | 5. Portfolio investment | Titled Portfolio Investments in main_config; rows list industries |
| 30 | 4. Direct investment | Direct investment by country, sum and share |
| 31 | 7.1 Assets | Other investment assets by sector |
| 32 | 7.2 Liabilities | Other investment liabilities by sector |
