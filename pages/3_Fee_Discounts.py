import streamlit as st
import pandas as pd
import numpy as np

st.title("Modeling Fee Discounts on a DEX as a Demand Driver")
st.markdown("""
This simulation models the impact of fee discounts on trading volume and token demand.

**How it works:**
- **Discounted Fee:** A slider lets you set a “% Discount Factor” that is multiplied with the standard fee. For example, a factor of 0.5 implies a 50% discount.
- **Trading Volume Increase:** Trading volume increases as fees drop. We use an elasticity model:

- **Staking Simulation (Optional):** If staking is required for the discount, you can set a staking adoption rate. The staking volume is assumed to grow linearly over time, and a simulated token price (which increases as more tokens are staked) is used to compute the “demand generated.”
""")

#   \[
#   V_{\text{new}} = V_{\text{base}} \times \Bigg(\frac{\text{Standard Fee}}{\text{Discounted Fee}}\Bigg)^{\text{Elasticity}}
#   \]

# st.markdown("# Fee Discounts")
st.sidebar.header("Fee Discounts")
st.sidebar.progress(100)
st.sidebar.text("%i%% Complete" % 50)
# st.markdown("""
# Modeling the demand generated for a token that enables fee discounts.
# This simulation computes the projected token supply and estimated dollar value of the demand generated over time (in months) for a fee discount model.
# """)

# --- Input Parameters for Trading Volume Simulation ---
st.subheader("Trading Volume & Fee Discounts")
base_volume = st.number_input("Base Trading Volume", value=1_000_000, step=10_000)

# Standard fee is provided as a percent (e.g., 0.3 for 0.3%)
standard_fee = st.number_input("Standard Fee (%)", value=0.3, step=0.05, format="%.2f")

# Slider for discount factor: this value multiplies the standard fee to give the discounted fee.
discount_factor_slider = st.slider(
    "% Discount Factor",
    min_value=0.1,
    max_value=1.0,
    value=0.5,
    step=0.01,
    help="Multiplier for the standard fee. For example, 0.5 means the discounted fee is 50% of the standard fee."
)
discounted_fee = standard_fee * discount_factor_slider
st.markdown(f"**Discounted Fee (%)**: {discounted_fee:.3f}")

volume_elasticity = st.slider("Volume Elasticity", min_value=0.0, max_value=5.0, value=1.5, step=0.1)
num_months = st.number_input("Number of Months", value=12, step=1)

# --- Trading Volume Calculation ---
# New trading volume based on the elasticity model:
if discounted_fee > 0:
    new_volume = base_volume * (standard_fee / discounted_fee)**(volume_elasticity)
else:
    new_volume = base_volume

# Simulate trading volume over time as a linear growth from base_volume to new_volume.
months_array = np.arange(1, num_months + 1)
trading_volume = base_volume + (new_volume - base_volume) * (months_array / num_months)

df_volume = pd.DataFrame({
    "Month": months_array,
    "Trading Volume": trading_volume
})

st.subheader("Trading Volume vs. Time")
st.line_chart(df_volume.set_index("Month"))
st.metric("Final Trading Volume", f"{trading_volume[-1]:,.0f}")

# --- Optional Staking Simulation ---
staking_toggle = st.checkbox("Simulate Staking Requirement for Fee Discount")

if staking_toggle:
    st.subheader("Staking & Demand Generation Simulation")
    
    # Slider for staking adoption rate (as a percentage).
    adoption_pct = st.slider("Staking Adoption Rate (%)", min_value=0, max_value=100, value=50, step=5)
    adoption_rate = adoption_pct / 100.0
    
    # Additional inputs for price simulation.
    base_token_price = st.number_input("Base Token Price", value=1.0, step=0.1)
    market_cap_constant = st.number_input("Market Cap Constant", value=10_000_000, step=100_000)
    
    # Simulate staking volume over time.
    # Assume staking volume grows linearly to a maximum of (base_volume * adoption_rate).
    staking_volume = base_volume * adoption_rate * (months_array / num_months)
    
    # Simulate token price as increasing inversely with the available circulating supply:
    token_price = base_token_price * (1 + staking_volume / market_cap_constant)
    
    # Demand generated: staking volume multiplied by token price.
    demand_generated = staking_volume * token_price
    
    df_staking = pd.DataFrame({
        "Month": months_array,
        "Staking Volume": staking_volume,
        "Token Price": token_price,
        "Demand Generated": demand_generated
    })
    
    st.line_chart(df_staking.set_index("Month"))
    st.metric("Final Demand Generated", f"{demand_generated[-1]:,.0f}")

