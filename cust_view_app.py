import gradio as gr
import pandas as pd
import requests
from supabase import create_client, Client

# --- 1. ASSETS & CREDENTIALS ---
SUPABASE_URL = "https://ifijqybgqraiivxjptaw.supabase.co"
SUPABASE_KEY = "sb_publishable_6szlWQmDYNxn6JM6XYvpRg_SyiRHYpw"
LOGO_URL = "https://github.com/ananya-padhi/mishtee-magic/blob/main/Gemini_Generated_Image_lx5evulx5evulx5e.png?raw=true"
CSS_URL = "https://raw.githubusercontent.com/ananya-padhi/mishtee-magic/refs/heads/main/style.css"

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch Custom CSS from GitHub
try:
    mishtee_css = requests.get(CSS_URL).text
except:
    mishtee_css = ""  # Fallback

# --- 2. BACKEND FUNCTIONS ---

def get_customer_portal_data(phone_number):
    """Verifies customer and fetches order history."""
    if not phone_number or len(phone_number) < 10:
        return "Please enter a valid 10-digit mobile number.", pd.DataFrame()

    # Fetch Customer Name
    cust_res = supabase.table("customers").select("full_name").eq("phone", phone_number).execute()
    
    if not cust_res.data:
        return "Namaste! It looks like you're new to the magic. Please register to indulge.", pd.DataFrame()

    customer_name = cust_res.data[0]['full_name']
    greeting = f"## Namaste, {customer_name} ji! \nGreat to see you again."

    # Fetch Order History with Product Join
    order_res = supabase.table("orders").select(
        "order_id, order_date, qty_kg, status, products(sweet_name)"
    ).eq("cust_phone", phone_number).execute()

    if order_res.data:
        df = pd.DataFrame(order_res.data)
        df['Sweet Name'] = df['products'].apply(lambda x: x['sweet_name'] if x else "Unknown")
        df = df[['order_id', 'order_date', 'Sweet Name', 'qty_kg', 'status']]
        df.columns = ["Order ID", "Date", "Item", "Qty (kg)", "Status"]
    else:
        df = pd.DataFrame(columns=["Order ID", "Date", "Item", "Qty (kg)", "Status"])

    return greeting, df

def get_trending_products():
    """Retrieves top 4 best sellers."""
    res = supabase.table("orders").select("qty_kg, products(sweet_name, variant_type)").execute()
    
    if not res.data:
        return pd.DataFrame(columns=["Sweet Name", "Collection", "Total Sold (kg)"])

    raw_df = pd.DataFrame(res.data)
    raw_df['Sweet Name'] = raw_df['products'].apply(lambda x: x['sweet_name'] if x else "N/A")
    raw_df['Collection'] = raw_df['products'].apply(lambda x: x['variant_type'] if x else "N/A")
    
    trending_df = raw_df.groupby(['Sweet Name', 'Collection'])['qty_kg'].sum().reset_index()
    trending_df = trending_df.sort_values(by='qty_kg', ascending=False).head(4)
    trending_df.columns = ["Sweet Name", "Collection", "Total Sold (kg)"]
    return trending_df

# --- 3. GRADIO UI LAYOUT ---

with gr.Blocks(css=mishtee_css, title="MishTee-Magic Portal") as demo:
    
    # HEADER SECTION
    with gr.Row():
        with gr.Column(elem_id="header_container"):
            gr.Image(LOGO_URL, show_label=False, container=False, width=280)
            gr.Markdown("<center><h3>Heritage in Every Bite • Purity in Every Grain</h3></center>")

    gr.HTML("<hr style='border: 0.5px solid #C06C5C; opacity: 0.3; margin: 20px 0;'>")

    # LOGIN SECTION
    with gr.Row():
        with gr.Column(scale=2):
            phone_input = gr.Textbox(label="Mobile Number", placeholder="Enter your 10-digit number", lines=1)
            login_btn = gr.Button("ENTER THE MAGIC", variant="primary")
        with gr.Column(scale=3):
            greeting_output = gr.Markdown("### Welcome to MishTee-Magic\nPlease login to view your artisanal dashboard.")

    # DATA SECTION (Tabbed View for Professional Cleanliness)
    with gr.Tabs():
        with gr.TabItem("My Order History"):
            history_table = gr.Dataframe(interactive=False)
            
        with gr.TabItem("Trending Today"):
            trending_table = gr.Dataframe(interactive=False)

    # FOOTER
    gr.Markdown("<center><small>MishTee-Magic © 2025 | Organic A2 Purity | Built for Artisanal Indulgence</small></center>")

    # --- 4. EVENT TRIGGERS ---
    
    def login_sequence(phone):
        greeting, history = get_customer_portal_data(phone)
        trending = get_trending_products()
        return greeting, history, trending

    login_btn.click(
        fn=login_sequence,
        inputs=phone_input,
        outputs=[greeting_output, history_table, trending_table]
    )

if __name__ == "__main__":
    demo.launch()
