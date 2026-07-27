import time
import requests
import pandas as pd
import pandas_ta as ta
import yfinance as yf

# تنظیمات تلگرام
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
    df = yf.download(tickers="GC=F", interval="15m", period="5d")
    return df

def check_strategy():
    df = get_data()
    if df.empty or len(df) < 120:
        return None

    # محاسبه مک‌دی‌ها با پیشوند مشخص تا خطا ندهد
    macd_def = ta.macd(df['Close'], fast=12, slow=26, signal=9, prefix="def")
    macd_4x = ta.macd(df['Close'], fast=48, slow=104, signal=36, prefix="m4x")
    
    df = pd.concat([df, macd_def, macd_4x], axis=1)
    
    curr = df.iloc[-2]
    prev = df.iloc[-3]
    
    # بررسی کراس مک‌دی ۴ برابر
    m4_line_prev = prev['MACD_48_104_36_m4x']
    m4_sig_prev  = prev['MACDs_48_104_36_m4x']
    m4_line_curr = curr['MACD_48_104_36_m4x']
    m4_sig_curr  = curr['MACDs_48_104_36_m4x']
    
    bullish_cross_4x = (m4_line_prev <= m4_sig_prev) and (m4_line_curr > m4_sig_curr)
    bearish_cross_4x = (m4_line_prev >= m4_sig_prev) and (m4_line_curr < m4_sig_curr)
    
    # بررسی هیستوگرام مک‌دی دیفالت
    hist_prev = prev['MACDh_12_26_9_def']
    hist_curr = curr['MACDh_12_26_9_def']
    
    is_first_negative_bar = (hist_curr < 0) and (hist_prev >= 0)
    is_first_positive_bar = (hist_curr > 0) and (hist_prev <= 0)
    
    if bullish_cross_4x and is_first_negative_bar:
        return "BUY"
        
    if bearish_cross_4x and is_first_positive_bar:
        return "SELL"
        
    return None

print("ربات هوشمند ترید طلا (XAUUSD) با موفقیت روشن شد...")

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
