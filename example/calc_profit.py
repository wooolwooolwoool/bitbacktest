import sys, os
sys.path.append(".")
from src.bitbacktest.market import BitflyerMarket
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# # Example usage:
market = BitflyerMarket()
# market.set_apikey(os.environ["API_KEY"], os.environ["API_SECRET"])
# executions = market.get_executions_all()
# with open("executions.json", "w") as f:
#     json.dump(executions, f, indent=2)

with open("executions.json", "r") as f:
    executions = json.load(f)
dates, profits = market.calc_profits(executions)
# print(profits)

total_profits = []
old_profit = 0
for profit in profits:
    total_profits.append(profit + old_profit)
    old_profit += profit
print(total_profits)
fig = plt.figure(figsize=(16, 9))
ax1 = fig.add_subplot()
ax1.plot(dates, total_profits)
fig.savefig("profits.png")