# here we r importing all the dependencies which are required for making this SalesEcho Project  - 

import streamlit as st
import pandas as pd
import plotly.express as px
import cohere
from gtts import gTTS
import tempfile
import base64
from dotenv import load_dotenv
import os

# Loading thee dotenv so to get the api key from the env . without this ai part will not work.
load_dotenv()
cohere_api_key = os.getenv("COHERE_API_KEY")
co = cohere.Client(cohere_api_key)

# setting the page configuration here in order to make the titlee
st.set_page_config(page_title="Sales Board", page_icon="📊", layout="wide")

st.title("📊 Monthly Sales Dashboard with AI Summary + Voice")

# uploading the csv file here for the analysis 

uploaded_file = st.file_uploader("📁 Upload Your CSV or Excel File", type=["csv", "xlsx"])



if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("🧾 Raw Uploaded Data")
    st.dataframe(df)

    # Auto-cleaning steps
    original_shape = df.shape
    df.drop_duplicates(inplace=True)
    df.dropna(inplace=True)
    df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce')
    df.dropna(subset=['Sales'], inplace=True)
    cleaned_shape = df.shape
    rows_removed = original_shape[0] - cleaned_shape[0]

    if rows_removed > 0:
        st.success(f"✅ Data cleaned automatically: {rows_removed} row(s) removed (duplicates, missing values, or invalid Sales).")
    else:
        st.info("🔍 Data is already clean. No rows were removed.")

    # Date & Month setup
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')
    monthly_sales = df.groupby('Month')['Sales'].sum().reset_index()
    monthly_sales['Month'] = monthly_sales['Month'].astype(str)

    # Top product, region, best month
    top_product = df.groupby('Product')['Sales'].sum().idxmax()
    top_region = df.groupby('Region')['Sales'].sum().idxmax()
    best_month = monthly_sales.loc[monthly_sales['Sales'].idxmax()]

    # AI Prompt
    prompt = f"""
    Write a short business-style sales summary based on:
    - Best month: {best_month['Month']} with sales of ₹{best_month['Sales']}
    - Top product: {top_product}
    - Top region: {top_region}
    Make it professional, clear, and in bullet points.
    """

    # AI Summary
    with st.spinner("🧠 Generating AI Summary..."):
        try:
            response = co.generate(
                model='command',
                prompt=prompt,
                max_tokens=200,
                temperature=0.6
            )
            summary = response.generations[0].text.strip()
        except Exception as e:
            summary = f"❌ Error from Cohere API: {e}"

    st.subheader("📢 AI Sales Summary")
    st.markdown(summary)

    # Voice summary
    if st.button("🔊 Speak Summary"):
        if summary:
            try:
                tts = gTTS(text=summary, lang='en')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tts.save(tmp_file.name)
                    audio_path = tmp_file.name
                with open(audio_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    b64 = base64.b64encode(audio_bytes).decode()
                    st.markdown(f"""
                        <audio autoplay controls>
                        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                        </audio>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error generating voice: {e}")
        else:
            st.warning("⚠️ No summary available to speak.")

    # Charts
    top_products = df.groupby('Product')['Sales'].sum().sort_values(ascending=False)
    top_regions = df.groupby('Region')['Sales'].sum().sort_values(ascending=False)

    st.subheader("📈 Monthly Sales Trend")
    st.bar_chart(monthly_sales.set_index('Month'))

    st.subheader("🏆 Top Performing Products")
    st.bar_chart(top_products)

    st.subheader("📍 Top Performing Regions")
    st.bar_chart(top_regions)

    st.subheader("📊 Region-wise Sales Distribution")
    pie_fig = px.pie(
        values=top_regions.values,
        names=top_regions.index,
        title="Sales by Region"
    )
    st.plotly_chart(pie_fig)

else:
    st.warning("⚠️ Please upload a CSV or Excel file to begin.")
