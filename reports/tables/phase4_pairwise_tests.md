| ticker   | strategy_a         | strategy_b             |   n_a |   n_b |   mean_diff |   welch_p_value |   mannwhitney_p_value |
|:---------|:-------------------|:-----------------------|------:|------:|------------:|----------------:|----------------------:|
| SPY      | A_unconditional    | B_compression_rule     |   378 |    46 |    316.812  |          0.0153 |                0.0862 |
| SPY      | A_unconditional    | C_probability_filtered |   378 |   234 |      3.9557 |          0.967  |                0.7815 |
| SPY      | B_compression_rule | C_probability_filtered |    46 |   234 |   -312.856  |          0.0212 |                0.0783 |
| QQQ      | A_unconditional    | B_compression_rule     |   378 |    52 |    101.656  |          0.499  |                0.842  |
| QQQ      | A_unconditional    | C_probability_filtered |   378 |   172 |   -127.328  |          0.3703 |                0.4389 |
| QQQ      | B_compression_rule | C_probability_filtered |    52 |   172 |   -228.984  |          0.2105 |                0.5247 |