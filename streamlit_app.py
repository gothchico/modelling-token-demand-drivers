import streamlit as st


def main():
    # builds the sidebar menu
    with st.sidebar:
        st.page_link('demand-drivers.py', label='Demand Drivers', icon='📈')
        st.page_link('pages/burn.py', label='Token Burn', icon='🔥')
        st.page_link('pages/fee-discounts.py', label='Fee Discounts', icon='💰')

    st.title(f'📈 Demand Drivers')

    # your content


if __name__ == '__main__':
    main()