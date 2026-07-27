import time
import requests
import pandas as pd
import yfinance as yf

TOKEN = "8724005712:AAHrzvK6BWNKkCx-JZkyqpZpQpvRnFKkybE"
CHAT_ID = "5840426117"

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"خطا در ارسال پیام تلگرام: {e}")

def get_data():
    df = yf.download(tickers="GC=F", interval="15m", period="5d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def calculate_macd(series, fast, slow, signal):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def check_strategy():
    df = get_data()
    if df.empty or len(df) < 150:
        return None

    close = df['Close']

    # مک‌دی دیفالت (۱۲، ۲۶، ۹)
    macd_def, sig_def, hist_def = calculate_macd(close, 12, 26, 9)
    
    # مک‌دی ۴ برابر (۴۸، ۱۰۴، ۳۶)
    macd_4x, sig_4x, hist_4x = calculate_macd(close, 48, 104, 36)
    
    df['macd_4x'] = macd_4x
    df['sig_4x'] = sig_4x
    df['hist_def'] = hist_def

    curr = df.iloc[-2]
    prev = df.iloc[-3]
    
    m4_line_prev = prev['macd_4x']
    m4_sig_prev  = prev['sig_4x']
    m4_line_curr = curr['macd_4x']
    m4_sig_curr  = curr['sig_4x']
    
    bullish_cross_4x = (m4_line_prev <= m4_sig_prev) and (m4_line_curr > m4_sig_curr)
    bearish_cross_4x = (m4_line_prev >= m4_sig_prev) and (m4_line_curr < m4_sig_curr)
    
    hist_prev = prev['hist_def']
    hist_curr = curr['hist_def']
    
    is_first_negative_bar = (hist_curr < 0) and (hist_prev >= 0)
    is_first_positive_bar = (hist_curr > 0) and (hist_prev <= 0)
    
    if bullish_cross_4x and is_first_negative_bar:
        return "BUY"
        
    if bearish_cross_4x and is_first_positive_bar:
        return "SELL"
        
    return None

print("ربات هوشمند ترید طلا (XAUUSD) بدون خطا اجرا شد...")

while True:
    try:
        signal = check_strategy()
        
        if signal == "BUY":
            message = "🟢 سیگنال خرید طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر کراس صعودی داد.\n- اولین میله مک‌دی دیفالت در ناحیه زیر صفر کامل شد."
            send_telegram_message(TOKEN, CHAT_ID, message)
            print("سیگنال خرید ارسال شد.")
            time.sleep(900)
            
        elif signal == "SELL":
            message = "🔴 سیگنال فروش طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر کراس نزولی داد.\n- اولین میله مک‌دی دیفالت در ناحیه بالای صفر کامل شد."
            send_telegram_message(TOKEN, CHAT_ID, message)
            print("سیگنال فروش ارسال شد.")
            time.sleep(900)
            
        else:
            time.sleep(60)
            
    except Exception as e:
        print(f"خطا در پردازش: {e}")
        time.sleep(60)
