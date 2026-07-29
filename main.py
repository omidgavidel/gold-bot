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

print("ربات با اصلاح دقیق منطق مک‌دی استارت شد...", flush=True)
send_telegram_message("🟢 ربات ترید طلا با منطق اصلاح‌شده استراتژی روشن شد.")

last_signal_time = None

while True:
    try:
        df = yf.download(tickers="GC=F", interval="15m", period="3d", progress=False, threads=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df is not None and len(df) > 50:
            close = df['Close']
            
            # محاسبات مک‌دی دیفالت (۱۲، ۲۶، ۹)
            _, _, hist_def = calculate_macd(close, 12, 26, 9)
            
            # محاسبات مک‌دی ۴ برابر (۴۸، ۱۰۴، ۳۶)
            macd_4x, sig_4x, _ = calculate_macd(close, 48, 104, 36)
            
            # بررسی کندل‌ها (iloc[-2] کندل تازه بسته شده و iloc[-3] کندل قبل از آن)
            h_curr = hist_def.iloc[-2]
            h_prev = hist_def.iloc[-3]
            
            m4_curr = macd_4x.iloc[-2]
            s4_curr = sig_4x.iloc[-2]
            
            # شرایط صعودی/نزولی مک‌دی ۴ برابر
            is_4x_bullish = m4_curr > s4_curr
            is_4x_bearish = m4_curr < s4_curr
            
            # شرایط اولین میله‌ی بسته شده بعد از عبور از خط صفر در مک‌دی دیفالت
            is_first_negative_bar = (h_curr < 0) and (h_prev >= 0)  # رفتن به زیر صفر و تمام شدن اولین میله منفی
            is_first_positive_bar = (h_curr > 0) and (h_prev <= 0)  # رفتن به بالای صفر و تمام شدن اولین میله مثبت
            
            current_time_label = str(df.index[-2])
            
            # سناریوی خرید: مک‌دی ۴ برابر صعودی + مک‌دی دیفالت اولین میله زیر صفر را بست
            if is_4x_bullish and is_first_negative_bar:
                if last_signal_time != current_time_label:
                    send_telegram_message("🟢 سیگنال خرید طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر: صعودی\n- مک‌دی دیفالت: اولین میله زیر صفر کامل بسته شد.")
                    print("سیگنال خرید ارسال شد.", flush=True)
                    last_signal_time = current_time_label
                    
            # سناریوی فروش: مک‌دی ۴ برابر نزولی + مک‌دی دیفالت اولین میله بالای صفر را بست
            elif is_4x_bearish and is_first_positive_bar:
                if last_signal_time != current_time_label:
                    send_telegram_message("🔴 سیگنال فروش طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر: نزولی\n- مک‌دی دیفالت: اولین میله بالای صفر کامل بسته شد.")
                    print("سیگنال فروش ارسال شد.", flush=True)
                    last_signal_time = current_time_label
                    
        time.sleep(60)
        
    except Exception as e:
        print(f"خطا: {e}", flush=True)
        time.sleep(60)
