import streamlit as st


def main():
    # builds the sidebar menu
    with st.sidebar:
        st.page_link('pages/1_Demand_Drivers.py', label='Demand Drivers', icon='📈')
        st.page_link('pages/2_Burn.py', label='Token Burn', icon='🔥')
        st.page_link('pages/3_Fee_Discounts.py', label='Fee Discounts', icon='💰')

if __name__ == '__main__':
    main()