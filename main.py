import time
import requests
import pandas as pd
import yfinance as yf

TOKEN = "8724005712:AAHrzvK6BWNKkCx-JZkyqpZpQpvRnFKkybE"
CHAT_ID = "5840426117"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except Exception:
        pass

def calculate_macd(series, fast, slow, signal):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

print("ربات روشن شد.")

while True:
    try:
        df = yf.download(tickers="GC=F", interval="15m", period="2d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if len(df) > 100:
            close = df['Close']
            
            _, _, hist_def = calculate_macd(close, 12, 26, 9)
            macd_4x, sig_4x, _ = calculate_macd(close, 48, 104, 36)
            
            curr = df.iloc[-2]
            prev = df.iloc[-3]
            
            m4_prev = prev.get('macd_4x', macd_4x.iloc[-3])
            s4_prev = prev.get('sig_4x', sig_4x.iloc[-3])
            m4_curr = curr.get('macd_4x', macd_4x.iloc[-2])
            s4_curr = curr.get('sig_4x', sig_4x.iloc[-2])
            
            h_prev = prev.get('hist_def', hist_def.iloc[-3])
            h_curr = curr.get('hist_def', hist_def.iloc[-2])
            
            bullish = (m4_prev <= s4_prev) and (m4_curr > s4_curr) and (h_curr < 0) and (h_prev >= 0)
            bearish = (m4_prev >= s4_prev) and (m4_curr < s4_curr) and (h_curr > 0) and (h_prev <= 0)
            
            if bullish:
                send_telegram_message("🟢 سیگنال خرید طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر کراس صعودی داد.\n- اولین میله مک‌دی دیفالت در ناحیه زیر صفر کامل شد.")
                time.sleep(900)
            elif bearish:
                send_telegram_message("🔴 سیگنال فروش طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر کراس نزولی داد.\n- اولین میله مک‌دی دیفالت در ناحیه بالای صفر کامل شد.")
                time.sleep(900)
                
        time.sleep(60)
    except Exception:
        time.sleep(60)
