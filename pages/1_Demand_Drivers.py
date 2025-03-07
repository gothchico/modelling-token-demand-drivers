import streamlit as st
import pandas as pd
import numpy as np
import time

st.title("Token Demand Drivers Modelling")
st.markdown("""
Modeling the demand drivers for an AMM DEX token: CDX
We quantify the demand generated through this token's utilities
This simulation computes estimated dollar value generated over time (in months) for selected demand drivers
""")


st.sidebar.header("Demand Drivers")

init_supply = st.number_input("Initial Token Supply", value=1_000_000)
TGE_price = float(st.text_input("Token Price at TGE", value='4'))
revenue_growth_rate = st.slider("Revenue Growth Rate: Month over Month (m-o-m)", 
                                min_value=0.0, max_value=0.1, value=0.02)
use_target_revenue = st.toggle("Use Target Revenue", value=False)
if use_target_revenue:
    target_revenue = float(st.text_input("Target Monthly Revenue", value='3000000'))
    initial_revenue = 200_000
else:
    initial_revenue = float(st.text_input("Initial Monthly Revenue", value='200000'))
    target_revenue = None
months = st.number_input("Number of Months", value=60)

params = {
    "init_supply": init_supply,
    "TGE_price": TGE_price,
    "initial_revenue": initial_revenue,
    "revenue_growth_rate": revenue_growth_rate,
    "use_target_revenue": use_target_revenue,
    "target_revenue": target_revenue,
    "months": months
}
st.session_state.params = params

progress_bar = st.sidebar.progress(0)
status_text = st.sidebar.empty()
last_rows = np.random.randn(1, 1)
chart = st.line_chart(last_rows)

for i in range(1, 101):
    new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
    status_text.text("%i%% Complete" % i)
    chart.add_rows(new_rows)
    progress_bar.progress(i)
    last_rows = new_rows
    time.sleep(0.005)

progress_bar.empty()

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")

