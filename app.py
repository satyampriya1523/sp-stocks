import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import ta
import yfinance as yf

# Page Layout Config (Mobile Responsive)
st.set_page_config(
page_title='AI Stock Analyzer', page_icon='📈', layout='wide'
)

st.title('📈 Automated AI Stock Analysis & Screener')
st.caption(
'Deep Fundamental & Technical Analysis Engine | Access from Laptop &'
' Mobile'
)

# Sidebar Tickers Input
st.sidebar.header('⚙️ Analysis Controls')
default_tickers = (
'RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS, ITC.NS, SBIN.NS'
)
user_input = st.sidebar.text_area(
'Enter NSE Tickers (comma separated):', default_tickers
)
tickers = [t.strip() for t in user_input.split(',') if t.strip()]


# Main Analysis Function
@st.cache_data(ttl=3600)
def analyze_data(ticker_list):
results = []
for t in ticker_list:
try:
stock = yf.Ticker(t)
info = stock.info

# Technical Data (1 Year)
hist = stock.history(period='1y')
if hist.empty:
continue

current_price = hist['Close'].iloc[-1]

# Technical Indicators
hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
rsi_series = ta.momentum.RSIIndicator(close=hist['Close']).rsi()
current_rsi = rsi_series.iloc[-1] if not rsi_series.empty else 50

# Fundamentals
pe = info.get('trailingPE', 0) or 0
roe = (info.get('returnOnEquity', 0) or 0) * 100
debt_eq = (info.get('debtToEquity', 100) or 100) / 100

# Scoring Logic (Max 100)
score = 0
reasons = []

if 0 < pe < 30:
score += 25
reasons.append('Healthy P/E')
if roe > 15:
score += 25
reasons.append('High ROE')
if debt_eq < 1.0:
score += 20
reasons.append('Low Debt')
if current_price > hist['SMA_50'].iloc[-1]:
score += 15
reasons.append('Above 50 SMA')
if 40 <= current_rsi <= 65:
score += 15
reasons.append('Balanced RSI')

results.append({
'Ticker': t.replace('.NS', ''),
'Full Ticker': t,
'Price (₹)': round(current_price, 2),
'P/E': round(pe, 2),
'ROE (%)': round(roe, 2),
'RSI': round(current_rsi, 2),
'Score': score,
'Signals': ', '.join(reasons),
'History': hist,
})
except Exception as e:
continue
return results


# Run Screener Button
if st.button('🚀 Analyze Market Now') or 'market_data' in st.session_state:
if 'market_data' not in st.session_state or st.button('Refresh Data'):
with st.spinner('Fetching & analyzing stocks...'):
st.session_state.market_data = analyze_data(tickers)

data = st.session_state.market_data
if data:
df = pd.DataFrame(data)
df_sorted = df.sort_values(by='Score', ascending=False)

# Top Recommended Overview
st.subheader('🏆 Top Rated Stocks')
st.dataframe(
df_sorted[[
'Ticker',
'Price (₹)',
'Score',
'P/E',
'ROE (%)',
'RSI',
'Signals',
]],
use_container_width=True,
)

# Detailed Interactive Charting
st.divider()
st.subheader('🔍 Deep Dive Stock Inspection')
selected_stock = st.selectbox(
'Select Stock for Technical & Fundamental Chart:',
df_sorted['Ticker'].tolist(),
)

stock_detail = next(
item for item in data if item['Ticker'] == selected_stock
)
hist_df = stock_detail['History']

# Plotly Candlestick Chart
fig = go.Figure()
fig.add_trace(
go.Candlestick(
x=hist_df.index,
open=hist_df['Open'],
high=hist_df['High'],
low=hist_df['Low'],
close=hist_df['Close'],
name='Price',
)
)
fig.add_trace(
go.Scatter(
x=hist_df.index,
y=hist_df['SMA_50'],
line=dict(color='orange', width=2),
name='50-day Moving Avg',
)
)
fig.update_layout(
title=f'{selected_stock} Price Chart & Trend',
xaxis_rangeslider_visible=False,
height=450,
)

st.plotly_chart(fig, use_container_width=True)
