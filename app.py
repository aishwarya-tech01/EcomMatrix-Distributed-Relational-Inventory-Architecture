
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==============================================================================
# 1. FRONTEND CONFIGURATION & VISUAL STYLING (HEALTH DASHBOARD CSS)
# ==============================================================================
st.set_page_config(page_title="EcomMatrix Pipeline", page_icon="📦", layout="wide")

# Custom Dark Matrix Theme + High Contrast Card Components Styling
st.markdown("""
<style>
    .main, .block-container { background-color: #0d1117 !important; }
    [data-testid="stSidebar"] { background-color: #333333 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    div[data-testid="stWidgetLabel"] p, label p { color: #ffffff !important; font-weight: 600 !important; }
    h1, h2, h3, h4, p, span, label { color: #ffffff !important; }
    
    /* Sleek Custom Metric Presentation Boxes */
    .metric-container {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .metric-title {
        color: #8b949e !important;
        font-size: 14px !important;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #ffffff !important;
        font-size: 28px !important;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE INITIALIZATION & RELATIONAL SEEDING
# ==============================================================================
def get_db_connection():
    return sqlite3.connect('ecommerce_inventory.db')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Core products schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            cost_price REAL DEFAULT 0.0,
            stock_level INTEGER NOT NULL,
            popularity_score REAL DEFAULT 0.0,
            supplier_name TEXT DEFAULT 'Global Logistics Corp'
        )
    ''')
    
    # Standalone categories schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Many-to-Many bridge table schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_category_map (
            product_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (product_id, category_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    ''')
    
    # FEATURE 3 schema: Chronological Audit Trail Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_node TEXT NOT NULL,
            action_event TEXT NOT NULL,
            details TEXT NOT NULL
        )
    ''')
    
    # Seed values dynamically if database is currently empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products_seed = [
            ('Pro Wireless Headphones', 8999.00, 5200.00, 45, 4.8, 'NexGen Electronics Ltd'),
            ('UltraBook Laptop 14"', 65000.00, 48000.00, 12, 4.9, 'NexGen Electronics Ltd'),
            ('Ergonomic Wireless Mouse', 1599.00, 950.00, 120, 4.2, 'Alpha Supply Chain'),
            ('Mechanical Gaming Keyboard', 4200.00, 2600.00, 3, 4.6, 'NexGen Electronics Ltd'),
            ('Smart Fitness Watch v2', 5499.00, 3400.00, 30, 4.5, 'WearableTech Distributors')
        ]
        cursor.executemany("INSERT INTO products (name, price, cost_price, stock_level, popularity_score, supplier_name) VALUES (?, ?, ?, ?, ?, ?)", products_seed)
        
        categories_seed = [('Electronics',), ('Office Supplies',), ('Gaming',), ('Wearables',)]
        cursor.executemany("INSERT INTO categories (category_name) VALUES (?)", categories_seed)
        
        mappings = [(1, 1), (1, 3), (2, 1), (2, 2), (3, 1), (3, 2), (4, 1), (4, 3), (5, 1), (5, 4)]
        cursor.executemany("INSERT INTO product_category_map (product_id, category_id) VALUES (?, ?)", mappings)
        
    conn.commit()
    conn.close()

init_db()

# ==============================================================================
# 3. FEATURE 1: SECURE USER AUTHENTICATION LAYER
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("## 🔒 EcomMatrix™ Administrative Security Gateway")
    st.markdown("Please verify your infrastructure system access credentials below:")
    
    login_col1, login_col2 = st.columns(2)
    with login_col1:
        input_user = st.text_input("User Core Handle ID")
        input_pass = st.text_input("Security Passphrase Key", type="password")
        
        if st.button("Authenticate System Initialization", type="primary"):
            if input_user == "admin" and input_pass == "matrix99":
                st.session_state["authenticated"] = True
                st.success("Access Authorized.")
                st.rerun()
            else:
                st.error("Access Denied: Invalid handle combination match.")
    st.stop()

# ==============================================================================
# 4. SIDEBAR PANEL CONTROL WORKSPACE
# ==============================================================================
conn = get_db_connection()
categories_df = pd.read_sql_query("SELECT category_name FROM categories", conn)
category_options = ["All Categories"] + categories_df['category_name'].tolist()
conn.close()

st.title("📦 EcomMatrix™: Distributed Relational Inventory Architecture")
st.markdown("---")

with st.sidebar:
    st.markdown(f"👤 **Active Node Identity:** `admin`")
    if st.button("Log Out of Node", type="secondary"):
        st.session_state["authenticated"] = False
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🛠️ Query Control Panel")
    search_query = st.text_input("Search Product SKU Handle", "")
    selected_category = st.selectbox("Filter Categorical Matrix", category_options)
    max_price = st.slider("Max Budget Ceiling (INR)", min_value=1000, max_value=100000, value=100000)
    min_popularity = st.slider("Minimum Consumer Rating Threshold", min_value=1.0, max_value=5.0, value=1.0)

    st.markdown("---")
    st.markdown("### 🚨 Logistical Alerts Panel")
    alert_threshold = st.slider("Stock Alert Warning Threshold", min_value=5, max_value=50, value=15)

    st.markdown("---")
    st.markdown("### 🌐 Market Currency Engine")
    selected_currency = st.selectbox("Select Display Currency", ["INR (₹)", "USD ($)", "EUR (€)"])
    currency_rates = {"INR (₹)": (1.0, "₹"), "USD ($)": (0.012, "$"), "EUR (€)": (0.011, "€")}
    exchange_rate, currency_symbol = currency_rates[selected_currency]

    # FEATURE 2: Dynamic Add Product Form with Smart Markup Pricing
    st.markdown("---")
    st.markdown("### ➕ Add New SKU to Inventory")
    new_name = st.text_input("Product Name")
    new_cost = st.number_input("Wholesale Cost Price (INR)", min_value=0.0, value=600.0)
    
    enable_markup = st.checkbox("Enable Automated Smart Markup Pricing", value=False)
    if enable_markup:
        markup_percent = st.slider("Target Profit Margin Markup (%)", min_value=10, max_value=150, value=40)
        calculated_selling_price = new_cost * (1 + (markup_percent / 100))
        st.info(f"💡 Calculated Selling Price: INR {calculated_selling_price:,.2f}")
        new_price = calculated_selling_price
    else:
        new_price = st.number_input("Selling Price (INR)", min_value=1.0, value=999.0)
        
    new_stock = st.number_input("Initial Stock Level", min_value=0, value=10)
    new_rating = st.slider("Product Rating", min_value=1.0, max_value=5.0, value=4.0)
    new_supplier = st.selectbox("Assign Supplier Partner", ["NexGen Electronics Ltd", "Alpha Supply Chain", "WearableTech Distributors", "Global Logistics Corp"])
    
    # Category Assignment Sub-selection
    conn = get_db_connection()
    available_cats = pd.read_sql_query("SELECT * FROM categories", conn)
    conn.close()
    cat_mapping_opts = {row['category_id']: row['category_name'] for _, row in available_cats.iterrows()}
    chosen_cat_id = st.selectbox("Assign Core Category Mapping", options=list(cat_mapping_opts.keys()), format_func=lambda x: cat_mapping_opts[x])

    if st.button("Save Product to Database"):
        if new_name.strip() == "":
            st.error("Product name cannot be empty!")
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Save product record
            cursor.execute(
                "INSERT INTO products (name, price, cost_price, stock_level, popularity_score, supplier_name) VALUES (?, ?, ?, ?, ?, ?)",
                (new_name, new_price, new_cost, new_stock, new_rating, new_supplier)
            )
            generated_prod_id = cursor.lastrowid
            
            # Save many-to-many link map
            cursor.execute("INSERT INTO product_category_map (product_id, category_id) VALUES (?, ?)", (generated_prod_id, chosen_cat_id))
            
            # Write transaction to FEATURE 3 Audit trail
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO system_logs (timestamp, user_node, action_event, details) VALUES (?, ?, ?, ?)",
                (timestamp_str, "admin", "SKU_ADDITION", f"Added item '{new_name}' (ID: {generated_prod_id}) to mapping group '{cat_mapping_opts[chosen_cat_id]}'")
            )
            conn.commit()
            conn.close()
            st.success(f"Successfully added {new_name} and logged transaction!")
            st.rerun()

    # Remove SKU Purge Form
    st.markdown("---")
    st.markdown("### 🗑️ Remove SKU from Ecosystem")
    delete_conn = get_db_connection()
    items_df = pd.read_sql_query("SELECT product_id, name FROM products", delete_conn)
    delete_conn.close()
    
    if not items_df.empty:
        item_options = {row['product_id']: f"ID {row['product_id']} | {row['name']}" for _, row in items_df.iterrows()}
        selected_delete_id = st.selectbox("Select Target SKU to Purge", options=list(item_options.keys()), format_func=lambda x: item_options[x])
        
        if st.button("Execute Transactional Delete", type="primary"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM products WHERE product_id = ?", (selected_delete_id,))
            target_name = cursor.fetchone()[0]
            
            cursor.execute("DELETE FROM product_category_map WHERE product_id = ?", (selected_delete_id,))
            cursor.execute("DELETE FROM products WHERE product_id = ?", (selected_delete_id,))
            
            # Write transaction to FEATURE 3 Audit trail
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO system_logs (timestamp, user_node, action_event, details) VALUES (?, ?, ?, ?)",
                (timestamp_str, "admin", "SKU_PURGE", f"Deleted item '{target_name}' (ID: {selected_delete_id}) from database relational tables")
            )
            conn.commit()
            conn.close()
            st.success("Database records successfully purged and logged!")
            st.rerun()

# ==============================================================================
# 5. DATA PIPELINE ENGINE (SQL JOINS OPTIMIZED)
# ==============================================================================
base_sql_query = """
    SELECT 
        p.product_id, p.name, p.price, p.cost_price, p.stock_level, p.popularity_score, p.supplier_name,
        GROUP_CONCAT(c.category_name, ', ') AS associated_categories
    FROM products p
    LEFT JOIN product_category_map pcm ON p.product_id = pcm.product_id
    LEFT JOIN categories c ON pcm.category_id = c.category_id
    WHERE p.price <= ? AND p.popularity_score >= ?
"""
params = [max_price, min_popularity]

if search_query:
    base_sql_query += " AND p.name LIKE ?"
    params.append(f"%{search_query}%")

base_sql_query += " GROUP BY p.product_id"

conn = get_db_connection()
raw_inventory_df = pd.read_sql_query(base_sql_query, conn, params=params)
conn.close()

if selected_category != "All Categories" and not raw_inventory_df.empty:
    raw_inventory_df = raw_inventory_df[raw_inventory_df['associated_categories'].str.contains(selected_category, na=False)]

# ==============================================================================
# 6. BUSINESS ANALYTICS & REORDER FORECASTING CALCULATIONS
# ==============================================================================
if not raw_inventory_df.empty:
    daily_sales_rate = 2.0
    raw_inventory_df['Days_to_Stockout'] = (raw_inventory_df['stock_level'] / daily_sales_rate).round(1)
    
    raw_inventory_df['item_profit'] = raw_inventory_df['price'] - raw_inventory_df['cost_price']
    raw_inventory_df['Profit Margin (%)'] = (raw_inventory_df['item_profit'] / raw_inventory_df['price']) * 100
    
    # Currency Conversion Engine + 12% Tax Integration
    raw_inventory_df['Display Price'] = raw_inventory_df['price'] * exchange_rate * 1.12
    raw_inventory_df['Display Cost'] = raw_inventory_df['cost_price'] * exchange_rate
    raw_inventory_df['Stock Valuation'] = raw_inventory_df['Display Price'] * raw_inventory_df['stock_level']

critical_alert_items = raw_inventory_df[raw_inventory_df['stock_level'] < alert_threshold] if not raw_inventory_df.empty else pd.DataFrame()
if not critical_alert_items.empty:
    for _, row in critical_alert_items.iterrows():
        st.error(f"🚨 **LOGISTICAL ALERT**: '{row['name']}' has fallen below warning ceiling! Current Stock: **{row['stock_level']} units**.")

# ==============================================================================
# 7. FEATURE 4: VISUAL INVENTORY HEALTH DASHBOARD PRESENTATION LAYER
# ==============================================================================
if raw_inventory_df.empty:
    st.warning("⚠️ Zero SKU allocations match the targeted filters.")
else:
    total_valuation = raw_inventory_df['Stock Valuation'].sum()
    total_projected_profit = ((raw_inventory_df['Display Price'] - raw_inventory_df['Display Cost']) * raw_inventory_df['stock_level']).sum()
    avg_stockout = raw_inventory_df['Days_to_Stockout'].mean()
    
    # Custom Structured Grid Summary Cards
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"""<div class='metric-container'>
            <div class='metric-title'>Pipeline Asset Valuation</div>
            <div class='metric-value'>{currency_symbol}{total_valuation:,.2f}</div>
        </div>""", unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""<div class='metric-container'>
            <div class='metric-title'>Projected Pipeline Profit</div>
            <div class='metric-value'>{currency_symbol}{total_projected_profit:,.2f}</div>
        </div>""", unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""<div class='metric-container'>
            <div class='metric-title'>Average Pipeline Stockout</div>
            <div class='metric-value'>{avg_stockout:.1f} Days</div>
        </div>""", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabbed Interface Layout
    tab1, tab2, tab3 = st.tabs(["📊 Inventory Products View", "🏭 Supplier Performance Analytics", "📜 FEATURE 3: System Transaction Logs"])
    
    with tab1:
        st.markdown("#### 📈 Profit Margin Breakdown by Product SKU (%)")
        
        # High-Contrast White Layout with Neon Yellow Bars Chart
        fig_margin = px.bar(
            raw_inventory_df, 
            x='name', 
            y='Profit Margin (%)',
            labels={'name': 'Product Name', 'Profit Margin (%)': 'Margin (%)'}
        )
        fig_margin.update_traces(marker_color='#CCFF00', marker_line_color='#CCFF00')
        fig_margin.update_layout(
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff',
            font_color='#000000',
            xaxis={'categoryorder':'total descending'}
        )
        st.plotly_chart(fig_margin, use_container_width=True)
        
        st.markdown("#### 📄 Real-Time Inventory View Data Grid")
        display_df = raw_inventory_df[['product_id', 'name', 'Display Price', 'Display Cost', 'stock_level', 'Days_to_Stockout', 'Profit Margin (%)', 'associated_categories']]
        st.dataframe(
            display_df.style.format({
                'Display Price': f'{currency_symbol}' + '{:.2f}',
                'Display Cost': f'{currency_symbol}' + '{:.2f}',
                'Profit Margin (%)': '{:.1f}%'
            }),
            use_container_width=True
        )

    with tab2:
        st.markdown("#### 🏭 Strategic Vendor Matrix Metrics")
        
        supplier_summary = raw_inventory_df.groupby('supplier_name').agg(
            Total_SKUs=('product_id', 'count'),
            Total_Stock_Units=('stock_level', 'sum'),
            Financial_Exposure=('Stock Valuation', 'sum')
        ).reset_index()
        
        st.markdown("##### 📈 Supplier Share Contribution (By Asset Value)")
        
        fig_supplier = px.bar(
            supplier_summary,
            x='supplier_name',
            y='Financial_Exposure',
            labels={'supplier_name': 'Supplier Partner', 'Financial_Exposure': 'Asset Value'}
        )
        fig_supplier.update_traces(marker_color='#CCFF00', marker_line_color='#CCFF00')
        fig_supplier.update_layout(
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff',
            font_color='#000000',
            xaxis={'categoryorder':'total descending'}
        )
        st.plotly_chart(fig_supplier, use_container_width=True)
        
        st.dataframe(
            supplier_summary.style.format({'Financial_Exposure': f'{currency_symbol}' + '{:,.2f}'}),
            use_container_width=True
        )

    # --- FEATURE 3 DISPLAY: DATA AUDITING RENDER TAB ---
    with tab3:
        st.markdown("#### 📜 Relational Core Administration Event Logs")
        log_conn = get_db_connection()
        logs_df = pd.read_sql_query("SELECT log_id AS 'Log ID', timestamp AS 'Timestamp', action_event AS 'Event Type', details AS 'Operation Details' FROM system_logs ORDER BY log_id DESC", log_conn)
        log_conn.close()
        
        if logs_df.empty:
            st.info("No management transactions recorded in audit database during current initialization sequence.")
        else:
            st.dataframe(logs_df, use_container_width=True, hide_index=True)

# ==============================================================================
# 8. AUTOMATED PROCUREMENT REORDER ENGINE
# ==============================================================================
    st.markdown("---")
    st.sidebar.markdown("---")
    st.markdown("### 🤖 Automated Procurement Reorder Engine")
    
    if not critical_alert_items.empty:
        st.write(f"The system has auto-generated a purchase order draft to restore items below {alert_threshold} units:")
        
        po_df = critical_alert_items[['name', 'supplier_name', 'Display Cost']].copy()
        po_df['Reorder Quantity'] = 50
        po_df['Estimated Cost'] = po_df['Display Cost'] * po_df['Reorder Quantity']
        
        st.dataframe(
            po_df[['name', 'supplier_name', 'Display Cost', 'Reorder Quantity', 'Estimated Cost']].style.format({
                'Display Cost': f'{currency_symbol}' + '{:.2f}', 
                'Estimated Cost': f'{currency_symbol}' + '{:.2f}'
            }),
            use_container_width=True
        )
        
        po_csv = po_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Dispatch Draft Purchase Order to CSV",
            data=po_csv,
            file_name="automated_supplier_reorder_po.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.success("✅ Logistical Equilibrium Maintained. No purchase orders required right now.")