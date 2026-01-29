<<<<<<< HEAD
# 📊 Virtual Trading Dashboard – Your Safe Gateway Into the Markets

Imagine this: the market is live, prices are flashing, options are moving tick by tick, and you have the power to buy or sell instantly — but with zero fear of losing money.  
That’s exactly what this Virtual Trading Dashboard gives you.  
It’s like a flight simulator for traders — you experience everything from entries, exits, profits, losses, margin, and even brokerage deductions… but without risking a single rupee.

---

## 🕹 Step Into the Market Like a Real Trader

With this dashboard, you can trade **Nifty, BankNifty, or Sensex options** (Current Expiry) in real time. Want to buy a Call? Sell a Put? Try a Straddle? One click and you’re in.  
The dashboard lights up in green to show your active position, and when you exit, it resets back — just like flattening your book on a broker’s terminal.  

**Golden Rule:**  
👉 You can only trade **one index at a time**.  
If you’re trading Nifty, finish your trade there before switching to BankNifty or Sensex. Forgetting this rule will make the dashboard show funny numbers (even simulators need discipline).

---

## 📡 Experience the Market Pulse, Tick by Tick

- Streams **live option prices** continuously as the market moves.  
- Trade the suggested **ATM strike** or experiment with your own.  
- Switching tabs takes you from Nifty’s battleground to BankNifty’s arena — but remember, finish one fight before starting another.

---

## 💹 Feel the Thrill of Profits (and the Sting of Costs)

- Every point in your favor instantly reflects as **profit**.  
- Every trade automatically deducts **brokerage and charges**, so you see your net result, not just the gross number.  
- Shows how much **margin** you’d need in a real account before placing a trade.  

In short: it teaches you the **real economics of trading**, not just the theory.

---

## 📊 Track Your Journey Like a Pro

The dashboard maintains a **live scoreboard**:  
- Number of trades taken  
- Wins vs losses  
- Net points gained  
- Total brokerage paid  
- Cumulative profit or loss  

At the end of the day, every trade is logged in a separate file — so you can **review your day**, just like professionals do.

---

## 🎯 Build Discipline, Not Just Trades

- Set your **Target and Stop Loss** in advance — once hit, the position auto-closes.  
- Use the **Exit All** shortcut to instantly flatten your book.  

This way, you don’t just practice trading — you **practice trading with rules**.

---

## ⏱ Simulated Market Latency

To make the experience more realistic, all trades (Entry & Exit) execute **2 seconds after you give the command**.  
The **LTP you see on screen may have already moved**, teaching you how to manage **slippage and timing**, just like in a live market.

---

## ⚡ Trade at the Speed of the Market

- Buy and Sell commands are mapped to **quick shortcuts** for instant execution.  
- Feels exactly like being inside a **live terminal** — but safer.  

---

## 🌍 Who Should Try This?

- **Newcomers** → Feel the rush of trading without the fear of loss.  
- **Learners** → Understand how margin, brokerage, and costs shape your trades.  
- **Strategy Builders** → Test ideas in real market conditions.  
- **Experienced Traders** → Sharpen execution and discipline before risking capital.

---

## ✨ Why This Stands Out

This dashboard is more than a tool — it’s a **mentor in disguise**.  
It teaches you the real lessons of trading:  
- How **brokerage eats into profit**  
- Why **margin management** matters  
- How quickly trades can **flip**  
- Why **discipline** keeps you alive in the market  

All this, while keeping your **money safe**.

---

## ✨ The Unique Edge

Unlike broker terminals that only show net P&L on an instrument (mixing all entries and exits together), this dashboard **breaks it down trade by trade**:  

✅ Every trade shows its **own Profit/Loss** after deducting brokerage, taxes, and charges — for both **entry and exit**.  
👉 No more guessing how much each trade really made (or lost). You see the **true picture per trade**, no matter how many times you’ve traded the same instrument.

---

## 🔥 In One Line

It’s the **safest way to feel the thrill of live trading** — free, real-time, and built for the trading community.  
=======
# 📊 Virtual Options Trading Dashboard (Intraday – Current Expiry)

![Virtual Options Trading Dashboard](Images/Dashboard.png)

## Overview
This Excel-based **Virtual Options Trading Dashboard** is a **real-time intraday simulator** designed to test and evaluate **options trading strategies** without risking real capital.

It simulates **live market behavior tick-by-tick**, exactly as if you were trading in the actual market.  
The dashboard supports **option buying, option selling, and multi-leg strategies**, and automatically analyzes performance, risk, and profitability.

> ⚠️ **Scope**
- Intraday only  
- Current expiry only  
- One strategy at a time  
- One index at a time  

---

## 🎯 Supported Instruments
You can virtually trade strategies on:
- **NIFTY**
- **BANK NIFTY**
- **SENSEX**

---

## 🧠 Supported Strategies
The system **automatically identifies** the strategy based on selected option legs.

### Single-Leg Strategies
- Naked Call Buy  
- Naked Call Sell  
- Naked Put Buy  
- Naked Put Sell  

### Spread Strategies
- Debit Spread (Call / Put)
- Credit Spread (Call / Put)

### Neutral & Advanced Strategies
- Long Strangle  
- Short Strangle  
- Long Straddle  
- Short Straddle  
- Iron Butterfly  
- Iron Condor  
- Reverse Iron Butterfly  
- Reverse Iron Condor  
- Synthetic Long  
- Synthetic Short  

🟡 If a combination does **not match any predefined logic**, it will be marked as:
> **`Unknown Strategy`**

---

## 📌 Key Dashboard Features

### 🔹 Live Trade Monitoring
- Tick-by-tick P&L movement
- Real-time points tracking
- Live strategy graph (points vs time)

### 🔹 Risk & Reward Metrics
Displayed **live** on the dashboard:
- **Max Profit**
- **Max Loss**
- **Margin Required**
- **Breakeven Levels**
- **Biasness** (Bullish / Bearish / Neutral)
- **Index Spot Price**
- **Strategy Name**

### 🔹 Accurate P&L Calculation
- Gross P&L
- **Total Brokerage** (including statutory charges)
- **Net P&L = Actual Profit / Loss**
- Gain % (calculated **w.r.t margin used**)

---

## 🎯 Target & Stop Loss Management

You can set **Target** and **Stop Loss** for the *entire strategy* in:

### ✔ Points
- Leave Rupee cells blank
- System prioritizes points

### ✔ Rupees (₹)
- Enter value in rupee cells
- Rupees get priority over points

### ✔ Special Rules
- `0` value → Target & SL **Not Set**
- Blank cells → Preference given to **Points**
- Manual Exit option available anytime

---

## 🧾 Trade Logging & History

At the **end of each trade**, detailed logs are automatically saved.

### 📂 Monthly Trade Logs
Maintained **month-wise**, accessible anytime.

### 🧾 Each Trade Log Contains:
- Trade Date & Day
- Entry Time & Exit Time
- Trade Duration
- Exit Method (Target / SL / Manual)
- Index Traded
- Expiry Used
- DTE (Days to Expiry)
- Strategy Name
- Lot × Quantity
- Lowest & Highest Points during trade
- Gross P&L
- Brokerage
- Net P&L
- Margin Used
- Gain % (w.r.t margin)

📁 **Each trade is also saved as a separate file** for post-trade analysis and evaluation.

---

## 🔁 Trading Workflow (Step-by-Step)

1. Select **Index** (NIFTY / BANK NIFTY / SENSEX)
2. Option Chain opens for **current expiry**
3. Select option legs (Buy / Sell) to build strategy
4. System auto-detects the strategy
5. Set **Target & Stop Loss** (Points or ₹)
6. Start the trade
7. Trade exits when:
   - Target hit  
   - Stop Loss hit  
   - Manual exit
8. Current Excel closes automatically
9. Choose:
   - **Yes** → Take next trade  
   - **No** → Exit program

➡️ In **one single program run**, you can take **up to 10 trades sequentially**.

---

## 📈 Why Use This Dashboard?
- Practice strategies **without real money**
- Validate strategy behavior in **live market conditions**
- Understand **risk, margin, and drawdowns**
- Improve discipline with predefined exits
- Perfect for **strategy testing before going live**

---

## ⚠️ Disclaimer
This tool is strictly for **educational and simulation purposes only**.  
It does **not place real trades** and should not be considered financial advice.

---
>>>>>>> 33363a57e57ffeb463bdb33ca9f585788ab1d82d
