# PB Global-to-Thematic Mapping Diagram

Generated from `report_configs/pb_t*.json`.

## Global tables mapped to thematic groups

```mermaid
flowchart LR
  hub["First Global Tables"]
  g_1["PB 1: Brief analytical description of Balance of Payments of the Republic of Tajikista..."]
  hub --> g_1
  g_2["PB 2: Brief standard description of Balance of Payments of the Republic of Tajikistan ..."]
  hub --> g_2
  g_3["PB 3: Brief standard description of Balance of Payments of the Republic of Tajikistan ..."]
  hub --> g_3
  th_1["Core Balance of Payments (0)"]
  g_1 --> th_1
  g_2 --> th_1
  g_3 --> th_1
  th_empty_1["No mapped PB tables"]
  th_1 --> th_empty_1
  th_2["Detailed Services Breakdown (1)"]
  g_1 --> th_2
  g_2 --> th_2
  g_3 --> th_2
  pb_23["PB 23: Table 23<br/>rules=246"]
  th_2 --> pb_23
  th_3["Income Accounts (2)"]
  g_1 --> th_3
  g_2 --> th_3
  g_3 --> th_3
  pb_25["PB 25: Primary income<br/>rules=9"]
  th_3 --> pb_25
  pb_26["PB 26: Secondary income<br/>rules=0"]
  th_3 --> pb_26
  th_4["Investment & Financial Accounts (5)"]
  g_1 --> th_4
  g_2 --> th_4
  g_3 --> th_4
  pb_28["PB 28: Foreign Direct Investments<br/>rules=11"]
  th_4 --> pb_28
  pb_29["PB 29: Portfolio Investments<br/>rules=11"]
  th_4 --> pb_29
  pb_30["PB 30: Table 30<br/>rules=0"]
  th_4 --> pb_30
  pb_31["PB 31: Other Investments - Assets<br/>rules=5"]
  th_4 --> pb_31
  pb_32["PB 32: Other Investments - Liabilities<br/>rules=5"]
  th_4 --> pb_32
  th_5["Reference / Minimal Templates (21)"]
  g_1 --> th_5
  g_2 --> th_5
  g_3 --> th_5
  pb_4["PB 4: Table 4<br/>rules=0"]
  th_5 --> pb_4
  pb_5["PB 5: Table 5<br/>rules=0"]
  th_5 --> pb_5
  pb_6["PB 6: Table 6<br/>rules=0"]
  th_5 --> pb_6
  pb_7["PB 7: Table 7<br/>rules=1"]
  th_5 --> pb_7
  pb_8["PB 8: Table 8<br/>rules=1"]
  th_5 --> pb_8
  pb_9["PB 9: Table 9<br/>rules=1"]
  th_5 --> pb_9
  pb_10["PB 10: Table 10<br/>rules=1"]
  th_5 --> pb_10
  pb_11["PB 11: Table 11<br/>rules=1"]
  th_5 --> pb_11
  pb_12["PB 12: Table 12<br/>rules=1"]
  th_5 --> pb_12
  pb_13["PB 13: Table 13<br/>rules=1"]
  th_5 --> pb_13
  pb_14["PB 14: Table 14<br/>rules=1"]
  th_5 --> pb_14
  pb_15["PB 15: Table 15<br/>rules=1"]
  th_5 --> pb_15
  pb_16["PB 16: Table 16<br/>rules=1"]
  th_5 --> pb_16
  pb_17["PB 17: Table 17<br/>rules=1"]
  th_5 --> pb_17
  pb_18["PB 18: Table 18<br/>rules=1"]
  th_5 --> pb_18
  pb_19["PB 19: Table 19<br/>rules=1"]
  th_5 --> pb_19
  pb_20["PB 20: Table 20<br/>rules=1"]
  th_5 --> pb_20
  pb_21["PB 21: Table 21<br/>rules=1"]
  th_5 --> pb_21
  pb_22["PB 22: Table 22<br/>rules=1"]
  th_5 --> pb_22
  pb_24["PB 24: Table 24<br/>rules=1"]
  th_5 --> pb_24
  pb_27["PB 27: Table 27<br/>rules=0"]
  th_5 --> pb_27
  th_6["Others / Supplementary Tables (0)"]
  g_1 --> th_6
  g_2 --> th_6
  g_3 --> th_6
  th_empty_6["No mapped PB tables"]
  th_6 --> th_empty_6
```

## Mapping matrix

| Global PB | Global title | Thematic group | Mapped PBs |
|---:|---|---|---|
| 1 | Brief analytical description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Core Balance of Payments | (none) |
| 1 | Brief analytical description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Detailed Services Breakdown | PB23 |
| 1 | Brief analytical description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Income Accounts | PB25, PB26 |
| 1 | Brief analytical description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Investment & Financial Accounts | PB28, PB29, PB30, PB31, PB32 |
| 1 | Brief analytical description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Reference / Minimal Templates | PB4, PB5, PB6, PB7, PB8, PB9, PB10, PB11, PB12, PB13, PB14, PB15, PB16, PB17, PB18, PB19, PB20, PB21, PB22, PB24, PB27 |
| 1 | Brief analytical description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Others / Supplementary Tables | (none) |
| 2 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Core Balance of Payments | (none) |
| 2 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Detailed Services Breakdown | PB23 |
| 2 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Income Accounts | PB25, PB26 |
| 2 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Investment & Financial Accounts | PB28, PB29, PB30, PB31, PB32 |
| 2 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Reference / Minimal Templates | PB4, PB5, PB6, PB7, PB8, PB9, PB10, PB11, PB12, PB13, PB14, PB15, PB16, PB17, PB18, PB19, PB20, PB21, PB22, PB24, PB27 |
| 2 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Others / Supplementary Tables | (none) |
| 3 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Core Balance of Payments | (none) |
| 3 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Detailed Services Breakdown | PB23 |
| 3 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Income Accounts | PB25, PB26 |
| 3 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Investment & Financial Accounts | PB28, PB29, PB30, PB31, PB32 |
| 3 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Reference / Minimal Templates | PB4, PB5, PB6, PB7, PB8, PB9, PB10, PB11, PB12, PB13, PB14, PB15, PB16, PB17, PB18, PB19, PB20, PB21, PB22, PB24, PB27 |
| 3 | Brief standard description of Balance of Payments of the Republic of Tajikistan (in thousand of USD) | Others / Supplementary Tables | (none) |

## Theme summary

| Theme | PB count | PB list |
|---|---:|---|
| Core Balance of Payments | 0 | (none) |
| Detailed Services Breakdown | 1 | PB23 |
| Income Accounts | 2 | PB25, PB26 |
| Investment & Financial Accounts | 5 | PB28, PB29, PB30, PB31, PB32 |
| Reference / Minimal Templates | 21 | PB4, PB5, PB6, PB7, PB8, PB9, PB10, PB11, PB12, PB13, PB14, PB15, PB16, PB17, PB18, PB19, PB20, PB21, PB22, PB24, PB27 |
| Others / Supplementary Tables | 0 | (none) |
