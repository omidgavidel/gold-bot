import time
import requests
import pandas as pd
import pandas_ta as ta
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
    df = yf.download(tickers="GC=F", interval="15m", period="5d")
    return df

def check_strategy():
    df = get_data()
    if df.empty or len(df) < 120:
        return None

    macd_def = ta.macd(df['Close'], fast=12, slow=26, signal=9)
    macd_4x = ta.macd(df['Close'], fast=48, slow=104, signal=36)
    
    df = pd.concat([df, macd_def, macd_4x], axis=1)
    
    # پیدا کردن خودکار نام ستون‌ها بر اساس خروجی واقعی کتابخانه
    cols = df.columns.tolist()
    macd_4x_col = [c for c in cols if 'MACD_' in c and '48' in c and '104' in c and not 's' in c and not 'h' in c][0]
    macds_4x_col = [c for c in cols if 'MACDs_' in c and '48' in c][0]
    macdh_def_col = [c for c in cols if 'MACDh_' in c and '12' in c][0]

    curr = df.iloc[-2]
    prev = df.iloc[-3]
    
    m4_line_prev = prev[macd_4x_col]
    m4_sig_prev  = prev[macds_4x_col]
    m4_line_curr = curr[macd_4x_col]
    m4_sig_curr  = curr[macds_4x_col]
    
    bullish_cross_4x = (m4_line_prev <= m4_sig_prev) and (m4_line_curr > m4_sig_curr)
    bearish_cross_4x = (m4_line_prev >= m4_sig_prev) and (m4_line_curr < m4_sig_curr)
    
    hist_prev = prev[macdh_def_col]
    hist_curr = curr[macdh_def_col]
    
    is_first_negative_bar = (hist_curr < 0) and (hist_prev >= 0)
    is_first_positive_bar = (hist_curr > 0) and (hist_prev <= 0)
    
    if bullish_cross_4x and is_first_negative_bar:
        return "BUY"
        
    if bearish_cross_4x and is_first_positive_bar:
        return "SELL"
        
    return None

print("ربات هوشمند ترید طلا (XAUUSD) آپدیت شد و در حال اجراست...")

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
