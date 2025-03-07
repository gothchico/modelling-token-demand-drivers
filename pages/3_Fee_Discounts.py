import streamlit as st
import pandas as pd
import numpy as np
import random

# ----------------------------------------------------------
# 1) Retrieve parameters from session_state
# ----------------------------------------------------------
params = st.session_state.get("params", {})
# The param dictionary might contain:
#   "monthly_revenue" (float)   e.g. 1_000_000
#   "revenue_growth_rate" (float) e.g. 0.10 => 10% monthly
#   "TGE_price" (float)         e.g. 1.0 => $1/CDX at TGE

base_monthly_revenue = params.get("monthly_revenue", 1_000_000)
monthly_revenue_growth = params.get("revenue_growth_rate", 0.10)
tge_price_default = params.get("TGE_price", 5.0)  # fallback if not in session

st.title("Token Demand from Fee Holidays")

st.markdown("""
This simulation:
1. Builds a **daily baseline** (from monthly revenue + daily growth).
2. Applies **fee holiday surges** (~15 days of exponential decay each).
3. Translates *excess volume* above baseline into **CDX token demand** 
   via a **conversion factor**, then values it at a TGE price.

**Workflow**:
- Pick how many days to simulate (below).
- Adjust discount, elasticity, adoption, etc. in the **sidebar**.
""")

st.header(f"Baseline Setup")
# ----------------------------------------------------------
# 2) Days to Simulate
# ----------------------------------------------------------
days_horizon = st.slider(
    "Days to Simulate",
    min_value=30,
    max_value=365,
    value=120,
    step=10,
    help="Time horizon for daily volume simulation."
)

# ----------------------------------------------------------
# 3) Baseline Setup
# ----------------------------------------------------------

initial_vol_pct = st.slider(
    "Day-1 Volume as % of Monthly Revenue",
    min_value=0.01,
    max_value=1.0,
    value=0.80,
    step=0.01,
    help="If 0.80 => day-1 volume = 80% of monthly_revenue / 30."
)

def monthly_to_daily_growth(mom_rate):
    """
    Approx. daily growth from monthly rate:
      (1 + mom_rate)^(1/30) - 1
    E.g., if monthly=0.10 => daily ~0.32%
    """
    return (1 + mom_rate)**(1/30) - 1

daily_growth = monthly_to_daily_growth(monthly_revenue_growth)
day1_volume = base_monthly_revenue * initial_vol_pct / 30

# ----------------------------------------------------------
# 5) Fee Holidays
# ----------------------------------------------------------
max_holidays = int(0.2 * days_horizon)
num_peaks = st.slider(
    "Number of Fee Holidays",
    min_value=0,
    max_value=max_holidays,
    value=min(5, max_holidays),
    help="Randomly chosen days in the horizon to trigger short surges."
)

# ----------------------------------------------------------
# 4) Sidebar: Discount, Elasticity, Adoption
# ----------------------------------------------------------
st.sidebar.header("Discount & Adoption")

discount_fraction = st.sidebar.slider(
    "Fee Discount (%)",
    min_value=0.0,
    max_value=0.99,
    value=0.60,
    step=0.01,
    help="0 => no discount, 0.99 => 99% discount."
)

market_elasticity = st.sidebar.slider(
    "Market Elasticity (Sensitivity)",
    min_value=0.0,
    max_value=2.0,
    value=1.0,
    step=0.1,
    help="Higher => bigger volume jump from the same discount."
)

adoption_rate = st.sidebar.slider(
    "Adoption Rate (Persistence of Surges)",
    min_value=0.0,
    max_value=1.0,
    value=0.6,
    step=0.1,
    help=(
        "Fraction of traders adopting the discount. "
        "Also influences how slowly the surge decays. "
        "Higher => the surge lasts longer."    ))

# ----------------------------------------------------------
# 7) Build Baseline (Day-by-Day)
# ----------------------------------------------------------
day_indices = np.arange(days_horizon)
baseline_vol = np.zeros(days_horizon)
baseline_vol[0] = day1_volume

for i in range(1, days_horizon):
    baseline_vol[i] = baseline_vol[i-1] * (1 + daily_growth)

# ----------------------------------------------------------
# 8) Add Surges (~5-day Decay) On Random Days
# ----------------------------------------------------------
def add_fee_holiday_peaks(baseline_arr, discount, elasticity, adoption, peaks=3):
    """
    Each holiday triggers an ~15-day surge:
      amplitude ~ avg_of_past_30days * (1/(1-discount))^elasticity
    Then multiply by adoption in the time constant or amplitude 
    to slow the decay if adoption is high.
    
    base_decay_days = 5 => each surge decays over 5 days
    we do: final_vol[d] += (amplitude - final_vol[d]) * dec_factor
    """
    final_vol = baseline_arr.copy()
    length = len(final_vol)
    if length == 0 or peaks < 1:
        return final_vol
    
    elasticity_factor = (1.0 / (1.0 - discount)) ** elasticity
    base_decay_days = 15  # ~15-day surges
    
    chosen_days = sorted(random.sample(range(length), k=min(peaks, length)))
    
    for pd in chosen_days:
        # average of preceding 30 days
        start_idx = max(0, pd - 30)
        window = final_vol[start_idx:pd]
        avg_past = np.mean(window) if len(window) > 0 else final_vol[pd]
        
        # amplitude => base surge
        amplitude = avg_past * elasticity_factor
        
        # time_constant => bigger if adoption is high => slower decay
        time_constant = 3.0 * max(0.01, adoption)
        
        for d in range(pd, min(pd + base_decay_days, length)):
            dt = d - pd
            dec_factor = np.exp(-dt / time_constant)
            final_vol[d] += (amplitude - final_vol[d]) * dec_factor
    
    return final_vol

final_vol = add_fee_holiday_peaks(
    baseline_vol,
    discount=discount_fraction,
    elasticity=market_elasticity,
    adoption=adoption_rate,
    peaks=num_peaks
)

# ----------------------------------------------------------
# 9) Plot Final Daily Volume in Thousands
# ----------------------------------------------------------
st.subheader("Daily Trading Volume")
df_volume = pd.DataFrame({
    "Day": day_indices + 1,
    "Volume (k$)": final_vol / 1000
}).set_index("Day")

# This bar chart highlights the peaks
st.bar_chart(df_volume, y_label=f"in thousands of dollars")


# ----------------------------------------------------------
# 6) Conversion to Token Demand
# ----------------------------------------------------------
st.header("Token Demand Conversion")

st.markdown(r"""
- It **peaks** when surges occur, 
- Then **decays** in a smooth curve (creating “U” shapes) until the next peak. This can be assumed to model the worst case or the most confirmed case of CDX tokens being staked for availing fee discounts. Ideally, if a flurry of fee discounts occur, some traders might want to retain and hold onto their CDX tokens in favour of subsequent benefits.
""")


conversion_factor = st.slider(
    "Conversion Factor (Volume -> CDX)",
    min_value=0.0,
    max_value=100.0,
    value=15.0,
    step=0.1,
    help=r'E.g. if 1 => $1 of excess volume generated by how many CDX tokens? If 15 => $1 => 15 tokens.'
)

tge_price_input = st.slider(
    "TGE Price of 1 CDX (USD)",
    min_value=0.0,
    max_value=100.0,
    value=tge_price_default,
    step=0.01,
    help="Used to convert tokens into USD demand."
)

# ----------------------------------------------------------
# 10) Excess Volume => Token Demand => USD
# ----------------------------------------------------------



excess_vol = final_vol - day1_volume
excess_vol[excess_vol < 0] = 0.0  # no negative excess

# Convert $ -> #CDX tokens
excess_tokens = excess_vol / conversion_factor

# Multiply by TGE price => USD demand
dollar_demand = excess_tokens * tge_price_input

# We line-chart daily token demand, so it forms "U" shapes between peaks
st.subheader("Daily CDX Token Demand")

df_demand = pd.DataFrame({
    "Day": day_indices + 1,
    "Token Demand (USD)": dollar_demand
}).set_index("Day")

st.line_chart(df_demand)

# Sum total demand over the entire period
total_demand = dollar_demand.sum()

st.metric(
    label="**Total CDX Demand Over Chosen Period**",
    value=f"${total_demand:,.0f}"
)

# ----------------------------------------------------------
# 11) Discussion & Corner Cases
# ----------------------------------------------------------
st.markdown(r"""
# Edge Cases and Extremities

- **Days to Simulate** (30–365):  
  - **Short** run => Surges may overlap.  
  - **Long** run => Surges may be sparse unless you choose many peaks.

- **Discount Fraction** (0–0.99):  
  - 0 => No discount => No elasticity effect.  
  - 0.99 => Very large discount => potential huge surges assumed, but also elasticity is a more dominating factor in this case.

- **Elasticity** (0–2):  
  - 0 => No sensitivity => discount has minimal effect.  
  - 2 => Very high => modest discount can cause big volume jumps.

- **Adoption Rate** (0–1):  
  - 0 => Surges vanish quickly.  
  - 1 => Surges last longer (slow decay).  

- **Fee Holidays**:  
  - 0 => No surges, baseline only.  
  - Many => Possibly overlapping surges => near‐continuous high volume.
  - We've assumed fee holidays to be implemented for only 20% of the chosen horizon

- **Conversion Factor** (0–100):  
  - 0 => No tokens minted.  
  - 1 => \$1 is generated by 1 token.  
  - Larger => e.g. 100 => \$1 is generated by 100 tokens => Every 100 tokens staked will generate $1 excess revenue.

- **TGE Price** (0–100):  
  - 0 => worthless => $0 demand.  
  - Large => each token is expensive => big total demand in USD.

""")
