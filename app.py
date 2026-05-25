import streamlit as st
import sqlite3
import pandas as pd

# Configure the web application layout canvas
st.set_page_config(page_title="EcomMatrix Pipeline", page_icon="📦", layout="wide")

# Custom Styling to keep the platform looking sleek, dark, and professional
st.markdown("""
    <style>
    .main, .block-container { background-color: #0d1117 !important; }
    h1, h2, h3, h4, p, span, label { color: #ffffff !important; }
    div[data-testid="stMetric"] { 
        background-color: #161b22 !important; 
        border: 1px solid #30363d !important; 
        padding: 15px; 
        border-radius: 8px; 
    }
    /* Explicitly force widget label texts to high-contrast white */
    div[data-testid="stWidgetLabel"] p, label p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 🗄️ DATABASE ARCHITECTURE SERVICE LAYER (SQLite)
# =====================================================================
def get_db_connection():
    return sqlite3.connect('ecommerce_inventory.db')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create Products Master Infrastructure Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock_level INTEGER NOT NULL,
            popularity_score REAL DEFAULT 0.0
        )
    ''')
    
    # 2. Create Categories Independent Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # 3. Create Multi-Table Intersection Junction Table (Many-to-Many Bridge)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_category_map (
            product_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (product_id, category_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    ''')
    
    # Seed core architectural dataset records if tables are blank
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products_seed = [
            ('Pro Wireless Headphones', 8999.00, 45, 4.8),
            ('UltraBook Laptop 14"', 65000.00, 12, 4.9),
            ('Ergonomic Wireless Mouse', 1599.00, 120, 4.2),
            ('Mechanical Gaming Keyboard', 4200.00, 0, 4.6),  # Out of stock asset tracker
            ('Smart Fitness Watch v2', 5499.00, 30, 4.5)
        ]
        cursor.executemany("INSERT INTO products (name, price, stock_level, popularity_score) VALUES (?, ?, ?, ?)", products_seed)
        
        categories_seed = [('Electronics',), ('Office Supplies',), ('Gaming',), ('Wearables',)]
        cursor.executemany("INSERT INTO categories (category_name) VALUES (?)", categories_seed)
        
        mappings = [
            (1, 1), (1, 3),  # Headphones -> Electronics, Gaming
            (2, 1), (2, 2),  # Laptop -> Electronics, Office Supplies
            (3, 1), (3, 2),  # Mouse -> Electronics, Office Supplies
            (4, 1), (4, 3),  # Keyboard -> Electronics, Gaming
            (5, 1), (5, 4)   # Smart Watch -> Electronics, Wearables
        ]
        cursor.executemany("INSERT INTO product_category_map (product_id, category_id) VALUES (?, ?)", mappings)
        
    conn.commit()
    conn.close()

init_db()

# Fetch active dynamic categories straight from database strings for filters
conn = get_db_connection()
categories_df = pd.read_sql_query("SELECT category_name FROM categories", conn)
category_options = ["All Categories"] + categories_df['category_name'].tolist()
conn.close()

# =====================================================================
# 🖥️ CORE INTERFACE DESIGN & LAYOUT SUB-SYSTEM
# =====================================================================
st.title("📦 EcomMatrix™: Distributed Relational Inventory Architecture")
st.markdown("---")

# 🔍 SIDEBAR PIPELINE CONTROLLER FILTERS
with st.sidebar:
    st.markdown("### 🛠️ Query Control Panel")
    search_query = st.text_input("Search Product SKU Handle", "")
    selected_category = st.selectbox("Filter Categorical Matrix", category_options)
    max_price = st.slider("Max Budget Ceiling (INR)", min_value=1000, max_value=100000, value=100000, step=500)
    min_popularity = st.slider("Minimum Consumer Rating Threshold", min_value=1.0, max_value=5.0, value=1.0, step=0.1)

# =====================================================================
# 🧮 INTERACTIVE INFRASTRUCTURE ENGINE & MULTI-TABLE SQL JOIN PIPELINE
# =====================================================================
# This advanced relational query safely concatenates categories associated with an item on-the-fly
base_sql_query = """
    SELECT 
        p.product_id,
        p.name,
        p.price,
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

# Run data queries across active database tunnels
conn = get_db_connection()
raw_inventory_df = pd.read_sql_query(base_sql_query, conn, params=params)
conn.close()

# Handle complex multi-category logic directly over memory-mapped frames
if selected_category != "All Categories":
    raw_inventory_df = raw_inventory_df[raw_inventory_df['associated_categories'].str.contains(selected_category, na=False, case=False)]

# =====================================================================
# 📊 SUPPLY-CHAIN PERFORMANCE LOGISTICS DASHBOARD MATRIX
# =====================================================================
if raw_inventory_df.empty:
    st.warning("⚠️ Zero SKU allocations match the targeted parameters inside the warehouse engine layer.")
else:
    # 🧮 Macro Financial Vector Math Calculations
    total_unique_skus = len(raw_inventory_df)
    total_warehouse_valuation = (raw_inventory_df['price'] * raw_inventory_df['stock_level']).sum()
    critical_stockouts = len(raw_inventory_df[raw_inventory_df['stock_level'] == 0])
    
    # Render analytical dashboard row framework blocks
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Monitored Warehouse SKUs", f"{total_unique_skus} Active Units")
    metric_col2.metric("Total Asset Inventory Value", f"₹{total_warehouse_valuation:,.2f}")
    
    # System alert logic checking for supply chain runouts
    if critical_stockouts > 0:
        metric_col3.metric("🚨 System Stockout Warnings", f"{critical_stockouts} Critical SKUs", delta="-CRITICAL", delta_color="inverse")
    else:
        metric_col3.metric("✅ Pipeline Logistics Health", "All SKUs Active", delta="NOMINAL")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📑 Real-Time Normalized Architecture Data Stream")
    
    # Output pristine operational data fields cleanly to screen grids
    st.dataframe(
        raw_inventory_df.style.format({'price': '₹{:,.2f}', 'popularity_score': '{:.1f} ★'}),
        use_container_width=True
    )