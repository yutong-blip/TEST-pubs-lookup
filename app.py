import streamlit as st
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Set Webpage Title and Icon
st.set_page_config(page_title="Publisher Recommendation Tool", page_icon="🏆", layout="wide")
st.title("🏆 Top Publisher Quick Search Tool")
st.markdown("Enter an Offer name or keyword to instantly find the best performing Publishers!")

# ---------------------------------------------------------
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSd4TV-iJMhjObxjm0Ar5WDgPdyMqzBJS10ih7BGF0t4h-J_wG_aLWknCAe4U1LGHWFoVhL8fS92oRb/pub?output=csv"
# ---------------------------------------------------------

print("⏳ Downloading the latest 30 days data from the database automatically...")

try:
    # Fetch data automatically without uploading
    df = pd.read_csv(CSV_URL)
    print("✅ Database loaded successfully! Building Publisher Recommendation Model...\n")

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

    # Apply extraction and filter out invalid geos
    df_filtered[['Geo', 'Model', 'Flow', 'OS']] = df_filtered['Offer'].apply(parse_offer)
    df_filtered = df_filtered[df_filtered['Geo'].str.len() <= 3]

    # Core Logic: Group by 4 dimensions AND Affiliate (Publisher)
    agg_df = df_filtered.groupby(['Geo', 'Model', 'Flow', 'OS', 'Affiliate']).agg({
        'Clicks': 'sum', 'Revenue': 'sum', 'Approved': 'sum'
    }).reset_index()

    # Calculate EPC and Conversion Rate
    agg_df['EPC'] = (agg_df['Revenue'] / agg_df['Clicks']).fillna(0).round(4)
    agg_df['CR(%)'] = (agg_df['Approved'] / agg_df['Clicks'] * 100).fillna(0).round(2)

    print("✅ Model ready! You can now query for publisher recommendations.\n" + "="*85)

    # Interactive Query Loop
    while True:
        print("\n")
        user_input = input("👉 Paste an Offer Title (e.g., 'US - CPE - APP - AOS - Game') or type 'q' to quit: ")

        if user_input.strip().lower() == 'q':
            print("👋 Exiting program. Have a great day!")
            break

        parts = user_input.split(' - ')
        if len(parts) < 4:
            print("⚠️ Invalid format. Ensure the offer name contains ' - ' separators.")
            continue

        req_geo = parts[0].strip()
        req_model = parts[1].strip() # Extract requested model
        req_flow = parts[2].strip()
        req_os = parts[3].strip()

        print(f"\n🔍 Analyzing Segment ---> Geo: [{req_geo}] | Model: [{req_model}] | Flow: [{req_flow}] | OS: [{req_os}]")

        # Find matching segments including Model
        match = agg_df[(agg_df['Geo'] == req_geo) &
                       (agg_df['Model'] == req_model) &
                       (agg_df['Flow'] == req_flow) &
                       (agg_df['OS'] == req_os)]

        if match.empty:
            print(f"👽 No historical data found for segment [{req_geo} / {req_model} / {req_flow} / {req_os}].")
        else:
            # Filter valid publishers and sort by Revenue & EPC
            valid_pubs = match[match['Clicks'] > 0]
            all_pubs = valid_pubs.sort_values(by=['Revenue', 'EPC'], ascending=[False, False])

            if all_pubs.empty:
                 print("No active publishers with clicks found for this specific segment.")
            else:
                print(f"🏆 All Recommended Publishers (Sorted by Revenue & EPC):")
                print("-" * 85)
                print(f"{'Publisher / Affiliate':<35} | {'Clicks':<8} | {'Revenue':<10} | {'CR(%)':<7} | {'EPC'}")
                print("-" * 85)

                # Display results
                for index, row in all_pubs.iterrows():
                    pub_name = str(row['Affiliate'])[:33] # Truncate long names for clean formatting
                    print(f"{pub_name:<35} | {row['Clicks']:<8} | ${row['Revenue']:<9.2f} | {row['CR(%)']:<6.2f}% | ${row['EPC']:.4f}")
                print("-" * 85)
                print(f"Total Publishers Found: {len(all_pubs)}")

except Exception as e:
    print(f"❌ Error loading data. Please check if your Google Sheets CSV link is correct. Details: {e}")
