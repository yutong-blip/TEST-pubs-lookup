import streamlit as st
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Set Webpage Title and Icon
st.set_page_config(page_title="Publisher Recommendation Tool", page_icon="🏆", layout="wide")
st.title("🏆 Top Publisher Quick Search Tool")
st.markdown("Enter an Offer name or keyword to instantly find the best performing Publishers!")

# ---------------------------------------------------------
# The real CSV URL
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSd4TV-iJMhjObxjm0Ar5WDgPdyMqzBJS10ih7BGF0t4h-J_wG_aLWknCAe4U1LGHWFoVhL8fS92oRb/pub?output=csv"
# ---------------------------------------------------------

# Cache the data so it loads instantly for your colleagues
@st.cache_data(ttl=3600)
def load_data(url):
    df = pd.read_csv(url)
    return df[df['Offer'].notna()].copy()

try:
    with st.spinner("Downloading the latest data from the database..."):
        df_filtered = load_data(CSV_URL)
    
    st.success("✅ Database loaded successfully! Ready for search.")

    # Interactive Search Box for Web
    user_input = st.text_input("👉 Paste FULL Offer Title OR a Keyword (e.g., 'Finderish' or 'ALL - CPL...'):")

    if user_input:
        st.write(f"🔍 Searching database for offers containing: **[{user_input}]** ...")
        
        # Search Logic
        match_raw = df_filtered[df_filtered['Offer'].str.contains(user_input, case=False, na=False)]
        
        if match_raw.empty:
            st.warning(f"👽 No historical data found for offer or keyword [{user_input}].")
        else:
            # Group by Affiliate and Offer
            offer_agg = match_raw.groupby(['Affiliate', 'Offer']).agg({
                'Clicks': 'sum', 'Revenue': 'sum', 'Approved': 'sum'
            }).reset_index()
            
            offer_agg['EPC'] = (offer_agg['Revenue'] / offer_agg['Clicks']).fillna(0).round(4)
            offer_agg['CR(%)'] = (offer_agg['Approved'] / offer_agg['Clicks'] * 100).fillna(0).round(2)
            
            # Filter and Sort
            valid_pubs = offer_agg[offer_agg['Clicks'] > 0]
            all_pubs = valid_pubs.sort_values(by=['Revenue', 'EPC'], ascending=[False, False])
            
            if all_pubs.empty:
                 st.info("No active publishers with clicks found for this search.")
            else:
                st.subheader(f"🏆 Top Publishers for [{user_input}] (Sorted by Revenue & EPC)")
                st.write(f"Total Records Found: {len(all_pubs)}")
                
                # Reorder columns for better web display
                display_df = all_pubs[['Affiliate', 'Offer', 'Clicks', 'Revenue', 'CR(%)', 'EPC']]
                
                # Display Interactive Table
                st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ Error loading data. Please check if your Google Sheets CSV link is correct. Details: {e}")
