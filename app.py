import streamlit as st
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Set Webpage Title and Icon
st.set_page_config(page_title="Publisher Recommendation Tool", page_icon="🏆", layout="wide")
st.title("🏆 Top Publisher Quick Search Tool")
st.markdown("Enter an Offer Title to instantly find the best Publishers for its **Geo, Model, Flow, and OS** segment!")

# ---------------------------------------------------------
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSd4TV-iJMhjObxjm0Ar5WDgPdyMqzBJS10ih7BGF0t4h-J_wG_aLWknCAe4U1LGHWFoVhL8fS92oRb/pub?output=csv"
# ---------------------------------------------------------

# Cache the processed data so it's lightning fast
@st.cache_data(ttl=3600)
def load_and_process_data(url):
    df = pd.read_csv(url)
    
    # Filter out non-standard offers
    df_filtered = df[df['Offer'].str.contains(' - ', na=False)].copy()

    # Parse Geo, Model, Flow, OS from the naming convention
    def parse_offer(offer_name):
        parts = str(offer_name).split(' - ')
        geo, model, flow, os = 'Unknown', 'Unknown', 'Unknown', 'Unknown'
        if len(parts) >= 4:
            geo = parts[0].strip()
            model = parts[1].strip() # Extract CPE, CPA, CPL, etc.
            flow = parts[2].strip()
            os = parts[3].strip()
        return pd.Series([geo, model, flow, os])

    # Apply extraction
    df_filtered[['Geo', 'Model', 'Flow', 'OS']] = df_filtered['Offer'].apply(parse_offer)
    df_filtered = df_filtered[df_filtered['Geo'].str.len() <= 3]

    # Core Logic: Group by 4 dimensions AND Affiliate (NO OFFER COLUMN HERE)
    agg_df = df_filtered.groupby(['Geo', 'Model', 'Flow', 'OS', 'Affiliate']).agg({
        'Clicks': 'sum', 'Revenue': 'sum', 'Approved': 'sum'
    }).reset_index()

    # Calculate EPC and Conversion Rate
    agg_df['EPC'] = (agg_df['Revenue'] / agg_df['Clicks']).fillna(0).round(4)
    agg_df['CR(%)'] = (agg_df['Approved'] / agg_df['Clicks'] * 100).fillna(0).round(2)
    
    return agg_df

try:
    with st.spinner("⏳ Downloading the latest data from the database automatically..."):
        agg_df = load_and_process_data(CSV_URL)
    
    st.success("✅ Database loaded successfully! Model ready.")

    # Interactive Web Input
    user_input = st.text_input("👉 Paste an Offer Title (e.g., 'US - CPE - APP - AOS - Game'):")

    if user_input:
        parts = user_input.split(' - ')
        if len(parts) < 4:
            st.warning("⚠️ Invalid format. Ensure the offer name contains ' - ' separators.")
        else:
            req_geo = parts[0].strip()
            req_model = parts[1].strip()
            req_flow = parts[2].strip()
            req_os = parts[3].strip()

            st.write(f"🔍 Analyzing Segment ---> **Geo: [{req_geo}] | Model: [{req_model}] | Flow: [{req_flow}] | OS: [{req_os}]**")

            # Find matching segments including Model
            match = agg_df[(agg_df['Geo'] == req_geo) & 
                           (agg_df['Model'] == req_model) & 
                           (agg_df['Flow'] == req_flow) & 
                           (agg_df['OS'] == req_os)]

            if match.empty:
                st.warning(f"👽 No historical data found for segment [{req_geo} / {req_model} / {req_flow} / {req_os}].")
            else:
                # Filter valid publishers and sort by Revenue & EPC
                valid_pubs = match[match['Clicks'] > 0]
                all_pubs = valid_pubs.sort_values(by=['Revenue', 'EPC'], ascending=[False, False])

                if all_pubs.empty:
                     st.info("No active publishers with clicks found for this specific segment.")
                else:
                    st.subheader("🏆 All Recommended Publishers (Sorted by Revenue & EPC)")
                    st.write(f"Total Publishers Found: {len(all_pubs)}")
                    
                    # ❌ NO MORE 'Offer' COLUMN, pure data based on your logic
                    display_df = all_pubs[['Affiliate', 'Clicks', 'Revenue', 'CR(%)', 'EPC']]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ Error loading data. Please check if your Google Sheets CSV link is correct. Details: {e}")
