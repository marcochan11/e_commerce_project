import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000/api"
st.set_page_config(page_title="Real-Time Retail Intelligence", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
    .metric-card {
        background-color: #0E1117;
        border: 1px solid #30333F;
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_api_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        return None
    return None

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🎮 Controls")
status_data = get_api_data("simulation/status")
is_running = status_data.get("running", False) if status_data else False

if st.sidebar.button("🟢 Start Simulation" if not is_running else "🔴 Stop Simulation"):
    new_state = not is_running
    requests.post(f"{API_URL}/simulation/toggle", params={"running": new_state})
    st.rerun()

st.sidebar.markdown("---")
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 2)
auto_refresh = st.sidebar.checkbox("Auto-Refresh Live Data", value=True)

# --- MAIN DASHBOARD ---
st.title("📊 E-commerce Sales & Inventory Intelligence")
placeholder = st.empty()

while True:
    with placeholder.container():
        stats = get_api_data("dashboard/stats")
        recent_orders = get_api_data("dashboard/recent-orders")
        chart_data = get_api_data("dashboard/sales-chart")
        cat_data = get_api_data("dashboard/category-dist")
        
        if not stats:
            st.warning("Backend is offline. Run 'uvicorn main:app --reload'")
            time.sleep(5)
            continue

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Today's Revenue", f"${stats['total_revenue']:,.2f}")
        col2.metric("Orders Processed", stats['total_orders'])
        col3.metric("Top Category", stats['top_category'])
        col4.metric("Low Stock Alerts", stats['low_stock_count'], delta_color="inverse")

        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("Real-Time Sales Velocity")
            if chart_data:
                df_chart = pd.DataFrame(chart_data)
                df_chart['timestamp'] = pd.to_datetime(df_chart['timestamp'])
                fig_line = px.line(df_chart, x='timestamp', y='total_price', 
                                   title="Sales Stream (Last 50 Orders)", markers=True)
                st.plotly_chart(fig_line, use_container_width=True)

        with col_right:
            st.subheader("Category Mix")
            if cat_data:
                df_cat = pd.DataFrame(cat_data)
                fig_pie = px.pie(df_cat, names='name', values='value', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📋 Live Transaction Log")
        if recent_orders:
            df_orders = pd.DataFrame(recent_orders)
            st.dataframe(df_orders[['timestamp', 'product_name', 'category', 'region', 'quantity', 'total_price']], hide_index=True, use_container_width=True)

        with st.expander("📦 Inventory Management (Click to Expand)"):
            inventory = get_api_data("inventory")
            if inventory:
                df_inv = pd.DataFrame(inventory)
                df_inv = df_inv.sort_values('stock') 
                st.dataframe(df_inv.style.map(lambda x: 'color: red' if isinstance(x, int) and x < 15 else '', subset=['stock']), use_container_width=True)
                
                col_restock, col_submit = st.columns([3, 1])
                product_to_restock = col_restock.selectbox("Select Product", df_inv['name'].unique())
                if col_submit.button("Restock Item"):
                    prod_id = df_inv[df_inv['name'] == product_to_restock]['id'].values[0]
                    requests.post(f"{API_URL}/inventory/restock/{prod_id}")
                    st.success(f"Restocked {product_to_restock}!")

    if not auto_refresh:
        break
    time.sleep(refresh_rate)