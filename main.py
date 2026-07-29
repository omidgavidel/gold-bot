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

print("ربات با اصلاح دقیق جایگاه مک‌دی‌ها (بالا ۴برابر، پایین دیفالت) استارت شد...", flush=True)
send_telegram_message("🟢 **ربات ترید طلا با چیدمان صحیح مک‌دی‌ها روشن شد.**")

last_signal_time = None

while True:
    try:
        df = yf.download(tickers="GC=F", interval="15m", period="1d", progress=False, threads=False)
        
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            if len(df) > 30:
                close = df['Close']
                
                # مک‌دی پایین: دیفالت (12, 26, 9)
                _, _, hist_def = calculate_macd(close, 12, 26, 9)
                
                # مک‌دی بالا: ۴ برابر (48, 104, 36)
                macd_4x, sig_4x, _ = calculate_macd(close, 48, 104, 36)
                
                # بررسی میله‌های مک‌دی پایینی (دیفالت)
                h_curr = float(hist_def.iloc[-2])
                h_prev = float(hist_def.iloc[-3])
                
                # بررسی مک‌دی بالایی (۴ برابر)
                m4_curr = float(macd_4x.iloc[-2])
                s4_curr = float(sig_4x.iloc[-2])
                
                # مک‌دی ۴ برابر صعودی یا نزولی
                is_4x_bullish = m4_curr > s4_curr
                is_4x_bearish = m4_curr < s4_curr
                
                # مک‌دی دیفالت: عبور از خط صفر و بسته شدن اولین میله
                is_first_negative_bar = (h_curr < 0) and (h_prev >= 0)
                is_first_positive_bar = (h_curr > 0) and (h_prev <= 0)
                
                current_time_label = str(df.index[-2])
                
                # سناریو خرید
                if is_4x_bullish and is_first_negative_bar:
                    if last_signal_time != current_time_label:
                        send_telegram_message("🟢 **سیگنال خرید طلا (XAUUSD)**\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی بالا (۴برابر): صعودی\n- مک‌دی پایین (دیفالت): اولین میله زیر صفر کامل بسته شد.")
                        print("سیگنال خرید ارسال شد.", flush=True)
                        last_signal_time = current_time_label
                        
                # سناریو فروش
                elif is_4x_bearish and is_first_positive_bar:
                    if last_signal_time != current_time_label:
                        send_telegram_message("🔴 **سیگنال فروش طلا (XAUUSD)**\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی بالا (۴برابر): نزولی\n- مک‌دی پایین (دیفالت): اولین میله بالای صفر کامل بسته شد.")
                        print("سیگنال فروش ارسال شد.", flush=True)
                        last_signal_time = current_time_label
                        
        time.sleep(60)
        
    except Exception as e:
        print(f"خطا: {e}", flush=True)
        time.sleep(60)
