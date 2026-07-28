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

try:
    print("شروع اجرای برنامه...", flush=True)
    # تست دریافت دیتا برای اطمینان از سلامت اتصال
    df_test = yf.download(tickers="GC=F", interval="15m", period="1d", progress=False)
    print(f"تست موفق دیتا، تعداد سطرها: {len(df_test)}", flush=True)
except Exception as e:
    send_telegram_message(f"🚨 خطای بحرانی در شروع ربات: {e}")
    print(f"خطای بحرانی: {e}", flush=True)

def calculate_macd(series, fast, slow, signal):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

print("ربات رصد طلا با منطق جدید روشن شد...", flush=True)

# متغیری برای اینکه برای یک کراس، تکراری پیام نفرستد
last_signal_time = None

while True:
    try:
        df = yf.download(tickers="GC=F", interval="15m", period="2d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if len(df) > 100:
            close = df['Close']
            _, _, hist_def = calculate_macd(close, 12, 26, 9)
            macd_4x, sig_4x, _ = calculate_macd(close, 48, 104, 36)
            
            # بررسی کندل‌های آخر (در حال بسته شدن و بسته شده)
            curr = df.iloc[-2] # کندل تازه بسته شده
            prev = df.iloc[-3] # کندل ماقبل آخر
            
            # مقادیر مک‌دی ۴ برابر
            m4_curr = macd_4x.iloc[-2]
            s4_curr = sig_4x.iloc[-2]
            
            # مقادیر هیستوگرام مک‌دی دیفالت برای تشخیص اولین میله منفی
            h_curr = hist_def.iloc[-2]
            h_prev = hist_def.iloc[-3]
            
            # شرط صعودی بودن مک‌دی 4 برابر (خط مک‌دی بالاتر از سیگنال باشد)
            is_4x_bullish = m4_curr > s4_curr
            
            # شرط اولین میله منفی مک‌دی دیفالت: کندل قبل مثبت یا صفر بوده، کندل فعلی منفی شده
            is_first_negative_bar = (h_curr < 0) and (h_prev >= 0)
            
            # شرط اولین میله مثبت مک‌دی دیفالت (برای فروش): کندل قبل منفی یا صفر بوده، کندل فعلی مثبت شده
            is_first_positive_bar = (h_curr > 0) and (h_prev <= 0)
            
            current_time_label = df.index[-2]
            
            if is_4x_bullish and is_first_negative_bar:
                if last_signal_time != current_time_label:
                    send_telegram_message("🟢 سیگنال خرید طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر در حالت صعودی قرار دارد.\n- اولین میله مک‌دی دیفالت در ناحیه زیر صفر کامل بسته شد.")
                    print("سیگنال خرید ارسال شد.", flush=True)
                    last_signal_time = current_time_label
                    
            elif (m4_curr < s4_curr) and is_first_positive_bar:
                if last_signal_time != current_time_label:
                    send_telegram_message("🔴 سیگنال فروش طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر در حالت نزولی قرار دارد.\n- اولین میله مک‌دی دیفالت در ناحیه بالای صفر کامل بسته شد.")
                    print("سیگنال فروش ارسال شد.", flush=True)
                    last_signal_time = current_time_label
                    
        time.sleep(60)
    except Exception as e:
        print(f"خطا: {e}", flush=True)
        time.sleep(60)
