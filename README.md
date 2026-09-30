Interest Rate Swap Hedging Dashboard — EUR

Pricing and DV01 of a payer interest rate swap used by a corporate to hedge a floating-rate loan (EUR 50m, Euribor + margin).

What it does
Bootstraps a EUR discount curve from market swap rates (close of 25 Sep 2026)
Prices the swap from the client's side (pay fixed / receive floating) and computes the par rate
Shows the proposed fixed rate and DV01 by maturity (3, 5, 7, 10 years) to help the client choose
Runs parallel shocks (±50 bp) and curve steepening / flattening scenarios
Interactive Streamlit dashboard for the client pitch
Key results (5-year swap, EUR 50m)
Maturity	Par rate	DV01
3 years	3.172%	€14,363 / bp
5 years	3.600%	€22,967 / bp
7 years	3.624%	€31,026 / bp
10 years	3.659%	€42,015 / bp

A +50 bp parallel shift adds about €1.13m to the client's hedge, offsetting the higher cost of the loan.

Files
irs_hedging_pricer.ipynb — step-by-step analysis
app.py — Streamlit dashboard (streamlit run app.py)
requirements.txt — dependencies
