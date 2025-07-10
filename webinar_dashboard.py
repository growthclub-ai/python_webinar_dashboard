import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px

# === CONFIG ===
SERVICE_ACCOUNT_FILE = 'creds.json'
SPREADSHEET_ID = '1Puuto3cRoNyD14Z6DrHXMq4vM9rIMRshKgxyyA4xGNs'
RANGE_NAME = "' Analytics Master Sheet'!A1:AZ200"

# === FUNCTIONS ===
def get_sheet_data():
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        return pd.DataFrame()

    header_row = values[2]  # row 3 in sheet
    data_rows = values[3:]  # rows after header

    df = pd.DataFrame(data_rows, columns=header_row)

    df.rename(columns={df.columns[0]: ""}, inplace=True)


    # Add real sheet row numbers
    df['__sheet_row'] = df.index + 4

    # Keep only target sheet rows
    target_rows = [91, 99, 100, 103]
    filtered = df[df['__sheet_row'].isin(target_rows)].drop(columns=['__sheet_row']).reset_index(drop=True)

    return filtered

# === STREAMLIT APP ===
st.title("📊 Webinar Dashboard")

df = get_sheet_data()

if df.empty:
    st.warning("No data found!")
else:
    st.subheader("POLL RESULTS")
    st.dataframe(df)

    labels = df.iloc[:,0]
    date_columns = df.columns[1:]  # skip first column (metric names)

    # Replace missing values and convert to numbers
    numeric_part = df[date_columns].replace(['', '-', None], 0)
    for col in numeric_part.columns:
        numeric_part[col] = pd.to_numeric(numeric_part[col], errors='coerce').fillna(0).astype(int)

    # === Dropdown ===
    option = st.selectbox("Select Date:", ["All Dates (Total)"] + list(date_columns))

    if option == "All Dates (Total)":
        totals = numeric_part.sum(axis=1)
        chart_df = pd.DataFrame({'Metric': labels, 'Total': totals})
    else:
        values = numeric_part[option]
        chart_df = pd.DataFrame({'Metric': labels, 'Total': values})

    # === Bar chart ===
    st.subheader(f"📊 Metrics on '{option}' (Bar Chart)")
    st.bar_chart(chart_df.set_index('Metric'))

    # === Pie chart ===
    st.subheader(f"🥧 Distribution on '{option}' (Pie Chart)")
    pie_fig = px.pie(chart_df, names='Metric', values='Total', title=f"Distribution on '{option}'")
    st.plotly_chart(pie_fig)




