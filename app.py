import streamlit as st
import sqlite3
import pandas as pd
import logging

# ==============================================================================
# 🪵 BACKEND ENGINE: SYSTEM LOGGING CONFIGURATION
# ==============================================================================
logging.basicConfig(
    filename='ecommatrix_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ==============================================================================
# 🎨 FRONTEND CONFIGURATION & VISUAL STYLING
# ==============================================================================
st.set_page_config(page_title="EcomMatrix Pipeline", page_icon="📦", layout="wide")

st.markdown("""
<style>
    .main, .block-container { 
        background-color: #0d1117 !important; 
    }
    [data-testid="stSidebar"] {
        background-color: #333333 !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    div[data-testid="stWidgetLabel"] p, label p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    h1, h2, h3, h4, p, span, label { 
        color: #ffffff !important; 
    }
    div[data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        padding: 15px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🗄️ DATABASE ARCHITECTURE LAYER (SQLite Relational Ecosystem)
# ==============================================================================
def get_db_connection():
    return sqlite3.connect('ecommerce_inventory.db')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create Master Products Table (with cost_price included)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            cost_price REAL DEFAULT 0.0,
            stock_level INTEGER NOT NULL,
            popularity_score REAL DEFAULT 0.0
        )
    ''')
    
    # Dynamic Safe Migration Check
    try:
        cursor.execute("SELECT cost_price FROM products LIMIT 1")
    except sqlite3.OperationalError:
        logging.info("Migrating database schema to include cost_price vector.")
        cursor.execute("ALTER TABLE products ADD COLUMN cost_price REAL DEFAULT 0.0")
        cursor.execute("UPDATE products SET cost_price = price * 0.65")
    
    # 2. Create Standalone Categories Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # 3. Create Many-to-Many Bridge Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_category_map (
            product_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (product_id, category_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    ''')
    
    # Seed values if completely blank
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products_seed = [
            ('Pro Wireless Headphones', 8999.00, 5200.00, 45, 4.8),
            ('UltraBook Laptop 14"', 65000.00, 48000.00, 8, 4.9),
            ('Ergonomic Wireless Mouse', 1599.00, 950.00, 120, 4.2),
            ('Mechanical Gaming Keyboard', 4200.00, 2600.00, 3, 4.6),
            ('Smart Fitness Watch v2', 5499.00, 3400.00, 30, 4.5)
        ]
        cursor.executemany("INSERT INTO products (name, price, cost_price, stock_level, popularity_score) VALUES (?, ?, ?, ?, ?)", products_seed)
        
        categories_seed = [('Electronics',), ('Office Supplies',), ('Gaming',), ('Wearables',)]
        cursor.executemany("INSERT INTO categories (category_name) VALUES (?)", categories_seed)
        
        mappings = [(1, 1), (1, 3), (2, 1), (2, 2), (3, 1), (3, 2), (4, 1), (4, 3), (5, 1), (5, 4)]
        cursor.executemany("INSERT INTO product_category_map (product_id, category_id) VALUES (?, ?)", mappings)
        
    conn.commit()
    conn.close()

init_db()

conn = get_db_connection()
categories_df = pd.read_sql_query("SELECT category_name FROM categories", conn)
category_options = ["All Categories"] + categories_df['category_name'].tolist()
conn.close()

def highlight_low_stock(row):
    return ['background-color: #5c4d12;' if row['stock_level'] < 15 else '' for _ in row]

# ==============================================================================
# 🖥️ VISUAL INTERFACE LAYOUT & SIDEBAR CONTROL PANELS
# ==============================================================================
st.title("📦 EcomMatrix™: Distributed Relational Inventory Architecture")
st.markdown("---")

with st.sidebar:
    st.markdown("### 🛠️ Query Control Panel")
    search_query = st.text_input("Search Product SKU Handle", "")
    selected_category = st.selectbox("Filter Categorical Matrix", category_options)
    max_price = st.slider("Max Budget Ceiling (INR)", min_value=1000, max_value=100000, value=100000)
    min_popularity = st.slider("Minimum Consumer Rating Threshold", min_value=1.0, max_value=5.0, value=1.0)

    # ➕ ADD PRODUCT FORM
    st.markdown("---")
    st.markdown("### ➕ Add New SKU to Inventory")
    new_name = st.text_input("Product Name")
    new_price = st.number_input("Selling Price (INR)", min_value=1.0, value=999.0)
    new_cost = st.number_input("Wholesale Cost Price (INR)", min_value=0.0, value=600.0)
    new_stock = st.number_input("Initial Stock Level", min_value=0, value=10)
    new_rating = st.slider("Product Rating", min_value=1.0, max_value=5.0, value=4.0)
    
    if st.button("Save Product to Database"):
        if new_name.strip() == "":
            st.error("Product name cannot be empty!")
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (name, price, cost_price, stock_level, popularity_score) VALUES (?, ?, ?, ?, ?)",
                (new_name, new_price, new_cost, new_stock, new_rating)
            )
            conn.commit()
            conn.close()
            st.success(f"Successfully added {new_name}!")
            st.rerun()

    # 🗑️ REMOVE SKU FORM
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
            cursor.execute("DELETE FROM product_category_map WHERE product_id = ?", (selected_delete_id,))
            cursor.execute("DELETE FROM products WHERE product_id = ?", (selected_delete_id,))
            conn.commit()
            conn.close()
            st.success("Database records successfully purged!")
            st.rerun()

# ==============================================================================
# ⚙️ DATA PIPELINE ENGINE (SQL RELATIONAL JOIN)
# ==============================================================================
base_sql_query = """
    SELECT 
        p.product_id,
        p.name,
        p.price,
        p.cost_price,
        p.stock_level,
        p.popularity_score,
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

if selected_category != "All Categories":
    raw_inventory_df = raw_inventory_df[raw_inventory_df['associated_categories'].str.contains(selected_category, na=False)]

# FIXED EXPLICIT PANDAS OPERATION FOR ZERO-VALUES
raw_inventory_df.loc[raw_inventory_df['cost_price'] == 0, 'cost_price'] = raw_inventory_df['price'] * 0.65

# ==============================================================================
# 🚨 EMERGENCY ALERT BLOCK SYSTEM
# ==============================================================================
critical_alert_items = raw_inventory_df[raw_inventory_df['stock_level'] < 10]
if not critical_alert_items.empty:
    for _, row in critical_alert_items.iterrows():
        st.error(f"🚨 **CRITICAL STOCK SHORTAGE ALERT**: '{row['name']}' is running dangerously low! Only **{row['stock_level']} units** left.")

# ==============================================================================
# 📊 PRESENTATION LAYER: KPI TILES, CHARTS, AND DATAFRAMES
# ==============================================================================
if raw_inventory_df.empty:
    st.warning("⚠️ Zero SKU allocations match the targeted parameters inside the warehouse engine layer.")
else:
    total_unique_skus = len(raw_inventory_df)
    total_warehouse_valuation = (raw_inventory_df['price'] * raw_inventory_df['stock_level']).sum()
    
    # Calculate potential profit margins safely
    raw_inventory_df['item_profit'] = raw_inventory_df['price'] - raw_inventory_df['cost_price']
    total_projected_profit = (raw_inventory_df['item_profit'] * raw_inventory_df['stock_level']).sum()
    raw_inventory_df['Profit Margin (%)'] = (raw_inventory_df['item_profit'] / raw_inventory_df['price']) * 100
    
    # Scorecards
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Gross Pipeline Valuation", f"₹{total_warehouse_valuation:,.2f}")
    metric_col2.metric("Projected Operational Profit", f"₹{total_projected_profit:,.2f}", delta="📈 NET")
    metric_col3.metric("Monitored Warehouse SKUs", f"{total_unique_skus} Active Handles")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bar Chart tracking profit margins
    st.markdown("#### 📈 Profit Margin Breakdown by Product SKU (%)")
    chart_data = raw_inventory_df[['name', 'Profit Margin (%)']].set_index('name')
    st.bar_chart(chart_data, y="Profit Margin (%)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📄 Real-Time Normalized Architecture Data Stream")
    
    display_df = raw_inventory_df[['product_id', 'name', 'price', 'cost_price', 'stock_level', 'Profit Margin (%)', 'associated_categories']]
    st.dataframe(
        display_df.style.apply(highlight_low_stock, axis=1).format({
            'price': '₹{:.2f}', 
            'cost_price': '₹{:.2f}', 
            'Profit Margin (%)': '{:.1f}%'
        }),
        use_container_width=True
    )

    # Spreadsheet Export
    st.markdown("---")
    st.markdown("### 📥 Administrative Data Export Operations")
    
    csv_bytes = raw_inventory_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Export Filtered Datasets to CSV",
        data=csv_bytes,
        file_name="ecommatrix_financial_export.csv",
        mime="text/csv"
    )