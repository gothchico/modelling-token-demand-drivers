import streamlit as st


def main():
    # builds the sidebar menu
    with st.sidebar:
        st.page_link('Demand_Drivers.py', label='Demand Drivers', icon='📈')
        st.page_link('pages/2_Burn.py', label='Token Burn', icon='🔥')
        st.page_link('pages/3_Fee_Discounts.py', label='Fee Discounts', icon='💰')

    st.title(f'📈 Demand Drivers')

    # your content


if __name__ == '__main__':
    main()