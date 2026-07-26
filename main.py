import time
import requests
import pandas as pd
import pandas_ta as ta
import yfinance as yf

# تنظیمات تلگرام (توکن و چت آیدی خود را اینجا قرار دهید)
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
    # دریافت داده‌های کندل 15 دقیقه‌ای طلا از یاهو فایننس (نماد GC=F)
    df = yf.download(tickers="GC=F", interval="15m", period="5d")
    return df

def check_strategy():
    df = get_data()
    if df.empty or len(df) < 120:
        return None

    # ۱. محاسبه مک‌دی دیفالت (12, 26, 9)
    macd_def = ta.macd(df['Close'], fast=12, slow=26, signal=9)
    
    # ۲. محاسبه مک‌دی 4 برابر (48, 104, 36)
    macd_4x = ta.macd(df['Close'], fast=48, slow=104, signal=36)
    
    df = pd.concat([df, macd_def, macd_4x], axis=1)
    
    # بررسی کندل بسته‌شده قبلی (-2) برای قطعی شدن وضعیت و کندل قبل‌تر از آن (-3)
    curr = df.iloc[-2] # کندل کامل‌شده اخیر
    prev = df.iloc[-3] # کندل ماقبل آن
    
    # --- بررسی کراس مک‌دی ۴ برابر روی کندل اخیر ---
    m4_line_prev = prev['MACD_48_104_36']
    m4_sig_prev  = prev['MACDs_48_104_36']
    m4_line_curr = curr['MACD_48_104_36']
    m4_sig_curr  = curr['MACDs_48_104_36']
    
    bullish_cross_4x = (m4_line_prev <= m4_sig_prev) and (m4_line_curr > m4_sig_curr)
    bearish_cross_4x = (m4_line_prev >= m4_sig_prev) and (m4_line_curr < m4_sig_curr)
    
    # --- بررسی هیستوگرام مک‌دی دیفالت (MACDh) برای تشخیص "اولین میله کامل شده" ---
    hist_prev = prev['MACDh_12_26_9']
    hist_curr = curr['MACDh_12_26_9']
    
    # شرایط اولین میله تکمیل شده در زیر صفر (برای خرید):
    # یعنی میله قبلی بالای صفر یا صفر بوده (یا منفیِ قبلی تمام شده و این اولین میله منفیِ جدید یا شروع حرکت زیر صفر است)
    # به عبارت دقیق‌تر: تغییر علامت از مثبت/صفر به منفی، یا شروع اولین میله منفیِ کامل‌شده
    is_first_negative_bar = (hist_curr < 0) and (hist_prev >= 0)
    
    # شرایط اولین میله تکمیل شده در بالای صفر (برای فروش):
    # یعنی میله قبلی زیر صفر یا صفر بوده و این اولین میله مثبت است
    is_first_positive_bar = (hist_curr > 0) and (hist_prev <= 0)
    
    if bullish_cross_4x and is_first_negative_bar:
        return "BUY"
        
    if bearish_cross_4x and is_first_positive_bar:
        return "SELL"
        
    return None

# حلقه اصلی اجرای ربات
print("ربات هوشمند ترید طلا (XAUUSD) با شرط 'اولین میله کامل‌شده' فعال شد...")

while Thread_running := True:
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
