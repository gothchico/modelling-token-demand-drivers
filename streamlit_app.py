import streamlit as st
import pandas as pd
import numpy as np

def simulate_buyback_burn(S0, TGE_price, initial_revenue, beta, revenue_growth_rate, price_growth_rate, target_revenue, use_target_revenue, months):
    supply = np.zeros(months)
    supply[0] = S0
    P_t = TGE_price
    R_t = initial_revenue
    demand_value = np.zeros(months)
    discount_factor = 0.95
    for t in range(1, months):
        P_t *= (1 + price_growth_rate)
        if use_target_revenue:
            R_t = target_revenue * (1 - np.exp(-revenue_growth_rate * t))
        else:
            R_t *= (1 + revenue_growth_rate)
        burn_buy = (beta * R_t) / P_t
        supply[t] = max(supply[t-1] - burn_buy, 0)
        demand_value[t] = (- (S0 * TGE_price) + (supply[t] * P_t)) * (discount_factor ** t)
    return pd.DataFrame({"Month": np.arange(1, months+1), "Supply": supply, "Demand Value": demand_value})

def simulate_exponential(S0, lambda_burn, months, TGE_price):
    supply = np.zeros(months)
    demand_value = np.zeros(months)
    lambda_burn = lambda_burn*0.01
    discount_factor = 0.95
    for t in range(months):
        supply[t] = S0 * np.exp(-lambda_burn * t)
        supply[t] = max(supply[t], 0)
        demand_value[t] = ((S0 * TGE_price) - (supply[t] * TGE_price)) * (discount_factor ** t)
    return pd.DataFrame({"Month": np.arange(1, months+1), "Supply": supply, "Demand Value": demand_value})

def simulate_logarithmic(S0, alpha, months, TGE_price):
    supply = np.zeros(months)
    demand_value = np.zeros(months)
    discount_factor = 0.95
    for t in range(months):
        supply[t] = S0 - alpha * np.log(1 + t)
        supply[t] = max(supply[t], 0)
        demand_value[t] = ((S0 * TGE_price) - (supply[t] * TGE_price)) * (discount_factor ** t)
    return pd.DataFrame({"Month": np.arange(1, months+1), "Supply": supply, "Demand Value": demand_value})

def simulate_schedule(S0, burn_schedule, months, TGE_price):
    supply = np.zeros(months)
    demand_value = np.zeros(months)
    discount_factor = 0.95
    supply[0] = S0
    for t in range(1, months):
        if burn_schedule and t in burn_schedule:
            supply[t] = supply[t-1] * (1 - burn_schedule[t])
        else:
            supply[t] = supply[t-1]
        supply[t] = max(supply[t], 0)
        demand_value[t] = ((S0 * TGE_price) - (supply[t] * TGE_price)) * (discount_factor ** t)
    return pd.DataFrame({"Month": np.arange(1, months+1), "Supply": supply, "Demand Value": demand_value})

def simulate_supply(model, params):
    if model == "Buyback + Burn Model":
        return simulate_buyback_burn(params["S0"], params["TGE_price"], params["initial_revenue"], params["beta"],
                                     params["revenue_growth_rate"], params["price_growth_rate"],
                                     params["target_revenue"], params["use_target_revenue"], params["months"])
    elif model == "Exponential Decay":
        return simulate_exponential(params["S0"], params["lambda_burn"], params["months"], params["TGE_price"])
    elif model == "Logarithmic Burn":
        return simulate_logarithmic(params["S0"], params["alpha"], params["months"], params["TGE_price"])
    elif model == "Schedule-Based Burn":
        return simulate_schedule(params["S0"], params["burn_schedule"], params["months"], params["TGE_price"])
    else:
        return pd.DataFrame(columns=["Month", "Supply", "Demand Value"])

st.title("Token Demand Drivers Modelling")
st.markdown("""
Modeling the demand drivers for an AMM DEX token.
This simulation computes the projected token supply and estimated dollar value generated over time (in months) for selected burn models.
""")

init_supply = st.number_input("Initial Supply", value=1_000_000)
TGE_price = float(st.text_input("TGE Token Price", value='2'))
revenue_growth_rate = st.slider("Revenue Growth Rate month over month (m-o-m)", 
                                min_value=0.0, max_value=0.1, value=0.02)
use_target_revenue = st.toggle("Use Target Revenue", value=False)
if use_target_revenue:
    target_revenue = float(st.text_input("Target Revenue", value='300000'))
    initial_revenue = 20_000
else:
    initial_revenue = float(st.text_input("Initial Revenue", value='20000'))
    target_revenue = None
months = st.number_input("Number of Months", value=60)

burn_model_options = [
    "Buyback + Burn Model",
    "Exponential Decay",
    "Logarithmic Burn",
    "Schedule-Based Burn"
]
selected_burn_model = st.selectbox("Select Burn Model to Simulate", options=burn_model_options)

delta = beta = lambda_burn = alpha = burn_schedule = None
if selected_burn_model == "Buyback + Burn Model":
    beta = st.slider("Buyback Rate", min_value=0.0, max_value=1.0, value=0.5)
if selected_burn_model == "Exponential Decay":
    lambda_burn = st.slider("Exponential Decay Rate", min_value=0.0, max_value=1.0, value=0.5)
if selected_burn_model == "Logarithmic Burn":
    alpha = st.number_input("Logarithmic Burn Rate", value=50_000, step=1000)
if selected_burn_model == "Schedule-Based Burn":
    schedule_rate = st.slider("Schedule Burn Rate", min_value=0.0, max_value=0.1, value=0.01)
    schedule_interval = st.number_input("Schedule Interval", min_value=1, max_value=months, value=5)
    burn_schedule = {m: schedule_rate for m in range(schedule_interval, int(months), int(schedule_interval))}

params = {
    "S0": init_supply,
    "TGE_price": TGE_price,
    "initial_revenue": initial_revenue,
    "beta": beta,
    "lambda_burn": lambda_burn,
    "alpha": alpha,
    "burn_schedule": burn_schedule,
    "revenue_growth_rate": revenue_growth_rate,
    "price_growth_rate": 0.03,
    "target_revenue": target_revenue,
    "use_target_revenue": use_target_revenue,
    "months": months
}

df_sim = simulate_supply(selected_burn_model, params)
df_renamed = df_sim.rename(columns={
    "Month": "months",
    "Supply": "supply",
    "Demand Value": "estimated demand dollar value",
})
if not df_sim.empty:
    col1, col2 = st.columns(2)
    st.line_chart(df_sim.set_index("Month")[["Supply", "Demand Value"]])
    with col1:
        st.bar_chart(df_renamed, x="months", y="supply", use_container_width=True)
    with col2:
        st.bar_chart(df_renamed, x="months", y="estimated demand dollar value", use_container_width=True)
    st.metric(label=f"{selected_burn_model} Final Supply", value=f"{df_sim['Supply'].iloc[-1]:,.0f}")
