import streamlit as st
import sqlite3
import pandas as pd
import logging

# ==============================================================================
# 🪵 BACKEND ENGINE: SYSTEM LOGGING CONFIGURATION
# ==============================================================================
# This creates a hidden file named 'ecommatrix_pipeline.log' to record app activity.
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
    .main, .block-container { background-color: #0d1117 !important; }
    h1, h2, h3, h4, p, span, label { color: #ffffff !important; }
    div[data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        padding: 15px;
        border-radius: 8px;
    }
    div[data-testid="stWidgetLabel"] p, label p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🗄️ DATABASE ARCHITECTURE LAYER (SQLite)
# ==============================================================================
def get_db_connection():
    # Logs every time our Python backend talks to the SQLite database file
    logging.info("Opening a secure connection to ecommerce_inventory.db")
    return sqlite3.connect('ecommerce_inventory.db')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create Products Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock_level INTEGER NOT NULL,
            popularity_score REAL DEFAULT 0.0
        )
    ''')
    
    # 2. Create Categories Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # 3. Create Many-to-Many Junction Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_category_map (
            product_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (product_id, category_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    ''')
    
    # Seed sample rows if database is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        logging.info("Database empty. Seeding initial marketplace data models...")
        products_seed = [
            ('Pro Wireless Headphones', 8999.00, 45, 4.8),
            ('UltraBook Laptop 14"', 65000.00, 12, 4.9),
            ('Ergonomic Wireless Mouse', 1599.00, 120, 4.2),
            ('Mechanical Gaming Keyboard', 4200.00, 0, 4.6),
            ('Smart Fitness Watch v2', 5499.00, 30, 4.5)
        ]
        cursor.executemany("INSERT INTO products (name, price, stock_level, popularity_score) VALUES (?, ?, ?, ?)", products_seed)
        
        categories_seed = [('Electronics',), ('Office Supplies',), ('Gaming',), ('Wearables',)]
        cursor.executemany("INSERT INTO categories (category_name) VALUES (?)", categories_seed)
        
        mappings = [
            (1, 1), (1, 3),
            (2, 1), (2, 2),
            (3, 1), (3, 2),
            (4, 1), (4, 3),
            (5, 1), (5, 4)
        ]
        cursor.executemany("INSERT INTO product_category_map (product_id, category_id) VALUES (?, ?)", mappings)
        
    conn.commit()
    conn.close()

# Start up database
init_db()

# Fetch active categories for dropdown filters
conn = get_db_connection()
categories_df = pd.read_sql_query("SELECT category_name FROM categories", conn)
category_options = ["All Categories"] + categories_df['category_name'].tolist()
conn.close()

# Helper function to highlight rows where stock level is under 15 units
def highlight_low_stock(row):
    return ['background-color: #5c4d12;' if row['stock_level'] < 15 else '' for _ in row]

# ==============================================================================
# 🖥️ VISUAL INTERFACE LAYOUT (UI)
# ==============================================================================
st.title("📦 EcomMatrix™: Distributed Relational Inventory Architecture")
st.markdown("---")

# 🔍 SIDEBAR PANEL CONTROLS
with st.sidebar:
    st.markdown("### 🛠️ Query Control Panel")
    search_query = st.text_input("Search Product SKU Handle", "")
    selected_category = st.selectbox("Filter Categorical Matrix", category_options)
    max_price = st.slider("Max Budget Ceiling (INR)", min_value=1000, max_value=100000, value=100000)
    min_popularity = st.slider("Minimum Consumer Rating Threshold", min_value=1.0, max_value=5.0, value=1.0)

    # ➕ CONTROL 1: ADD NEW SKU FORM
    st.markdown("---")
    st.markdown("### ➕ Add New SKU to Inventory")
    new_name = st.text_input("Product Name")
    new_price = st.number_input("Price (INR)", min_value=1.0, value=999.0)
    new_stock = st.number_input("Initial Stock Level", min_value=0, value=10)
    new_rating = st.slider("Product Rating", min_value=1.0, max_value=5.0, value=4.0)
    
    if st.button("Save Product to Database"):
        if new_name.strip() == "":
            st.error("Product name cannot be empty!")
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (name, price, stock_level, popularity_score) VALUES (?, ?, ?, ?)",
                (new_name, new_price, new_stock, new_rating)
            )
            conn.commit()
            conn.close()
            logging.info(f"New product created successfully: {new_name}")
            st.success(f"Successfully added {new_name}!")
            st.rerun()

    # 🗑️ CONTROL 2: REMOVE SKU INTERFACE
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
            logging.info(f"Purged database records for item ID: {selected_delete_id}")
            st.success("Database records successfully purged!")
            st.rerun()
    else:
        st.info("No records present to delete.")

# ==============================================================================
# ⚙️ DATA PIPELINE ENGINE (SQL JOIN)
# ==============================================================================
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

# Run the query against our active SQLite storage
conn = get_db_connection()
raw_inventory_df = pd.read_sql_query(base_sql_query, conn, params=params)
conn.close()

# Apply secondary category filtering if selected
if selected_category != "All Categories":
    raw_inventory_df = raw_inventory_df[raw_inventory_df['associated_categories'].str.contains(selected_category, na=False)]

# ==============================================================================
# 📊 PRESENTATION LAYER: KPI METRICS & GRAPHICS
# ==============================================================================
if raw_inventory_df.empty:
    st.warning("⚠️ Zero SKU allocations match the targeted parameters inside the warehouse engine layer.")
else:
    # Calculations for scorecard blocks
    total_unique_skus = len(raw_inventory_df)
    total_warehouse_valuation = (raw_inventory_df['price'] * raw_inventory_df['stock_level']).sum()
    critical_stockouts = len(raw_inventory_df[raw_inventory_df['stock_level'] == 0])
    
    # Display scorecard row
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Monitored Warehouse SKUs", f"{total_unique_skus} Active Units")
    metric_col2.metric("Total Asset Inventory Value", f"₹{total_warehouse_valuation:,.2f}")
    
    if critical_stockouts > 0:
        metric_col3.metric("🚨 System Stockout Warnings", f"{critical_stockouts} Critical SKUs", delta="-ALERT")
    else:
        metric_col3.metric("✅ Pipeline Logistics Health", "All SKUs Active", delta="NOMINAL")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 📈 Real-time Stock Visualizer Chart
    st.markdown("#### 📊 Current Warehouse Stock Level Distribution")
    chart_data = raw_inventory_df[['name', 'stock_level']].set_index('name')
    st.bar_chart(chart_data, y="stock_level")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📄 Real-Time Normalized Architecture Data Stream")
    
    # Dynamic grid view table with low stock golden highlight tracking row styles
    st.dataframe(
        raw_inventory_df.style.apply(highlight_low_stock, axis=1).format({'price': '₹{:.2f}', 'popularity_score': '{:.1f} ★'}),
        use_container_width=True
    )

    # ==============================================================================
    # 💾 DATA EXPORT PIPELINE 
    # ==============================================================================
    st.markdown("---")
    st.markdown("### 📥 Administrative Data Export Operations")
    
    csv_data = raw_inventory_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Export Filtered Datasets to CSV",
        data=csv_data,
        file_name="ecommatrix_operational_export.csv",
        mime="text/csv",
        help="Extract current visual metrics straight into an Excel-ready CSV sheet structure."
    )