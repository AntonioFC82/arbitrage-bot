# arbitrage-bot

### Arbitrage bonds

The bot operates based on the ratio between two bonds, b1/b2. Using this value, identified as 'rM' (average ratio),
two lower levels (N1 and N2) and two upper levels (N3 and N4) are defined, with a predefined deviation of 0.15.
When a buy operation is performed at any level (IDA), the arbitrage is closed when the lower level is reached (VUELTA).
However, there may be multiple buy operations open if, for example, the ratio starts below N2 and rises to N4. In this case,
there would be four IDA operations (N2, rM, N3, and N4), which would be closed as b1/b2 returns to its mean value,
as determined by prior analysis of the chosen pair's behavior.

1.  Parameter settings include the bond pair, average ratio, deviation between levels, and quantity to sell.
2.  It must be specified whether nominal values are accumulated or the quantity sold is repurchased (in the latter case, the profit would be the difference in $).
3.  With these settings, the bot can be initiated.
4.  Upon initiation, the bot enters the 'opeIdaVuelta()' function.
4.  When conditions are met, two IDA operations are executed: selling B1 and buying B2, and the variable 'paso1' is set to 1. This prevents new operations from being
executed until the other level (upper or lower) is reached, regardless of whether the remaining conditions are met.
5.  Whenever an IDA operation is completed, the values of the 'paso1' to 'paso4' variables are displayed on the screen. For example, if two IDA operations were executed,
one at level N2 and one at level 'rM', the display would read: "steps1-2-3-4 after the 1st while: 1, 1, 0, 0".
If the ratio falls back below N2 at this point, a VUELTA operation is executed, and the value of the 'paso2' variable is reset to 0. "steps1-2-3-4 after the 1st while: 1, 0, 0, 0".
