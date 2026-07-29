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

print("ربات با استراتژی دقیقِ کراس ۴برابر و اولین میله دیفالت استارت شد...", flush=True)

last_signal_time = None

while True:
    try:
        df = yf.download(tickers="GC=F", interval="15m", period="2d", progress=False, threads=False, auto_adjust=True)
        
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            if len(df) > 30:
                close = df['Close']
                
                # مک‌دی دیفالت (پایینی)
                _, _, hist_def = calculate_macd(close, 12, 26, 9)
                
                # مک‌دی ۴ برابر (بالایی)
                macd_4x, sig_4x, _ = calculate_macd(close, 48, 104, 36)
                
                # بررسی میله‌های مک‌دی دیفالت روی کندل بسته شده
                h_curr = float(hist_def.iloc[-2])
                h_prev = float(hist_def.iloc[-3])
                
                # بررسی کراس در مک‌دی ۴ برابر
                m4_curr = float(macd_4x.iloc[-2])
                s4_curr = float(sig_4x.iloc[-2])
                m4_prev = float(macd_4x.iloc[-3])
                s4_prev = float(sig_4x.iloc[-3])
                
                # کراس صعودی یا قرار داشتن در روند صعودی مک‌دی ۴ برابر
                is_4x_bullish_cross = (m4_curr > s4_curr)
                # کراس نزولی یا قرار داشتن در روند نزولی مک‌دی ۴ برابر
                is_4x_bearish_cross = (m4_curr < s4_curr)
                
                # مک‌دی دیفالت: عبور از خط صفر و بسته شدن اولین میله
                is_first_negative_bar = (h_curr < 0) and (h_prev >= 0)
                is_first_positive_bar = (h_curr > 0) and (h_prev <= 0)
                
                current_time_label = str(df.index[-2])
                
                # شرط خرید: مک‌دی ۴برابر صعودی + مک‌دی دیفالت اولین میله زیر صفر
                if is_4x_bullish_cross and is_first_negative_bar:
                    if last_signal_time != current_time_label:
                        send_telegram_message("🟢 **سیگنال خرید طلا (XAUUSD)**\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴برابر: صعودی\n- مک‌دی دیفالت: اولین میله زیر صفر بسته شد.")
                        print("سیگنال خرید ارسال شد.", flush=True)
                        last_signal_time = current_time_label
                        
                # شرط فروش: مک‌دی ۴برابر نزولی + مک‌دی دیفالت اولین میله بالای صفر
                elif is_4x_bearish_cross and is_first_positive_bar:
                    if last_signal_time != current_time_label:
                        send_telegram_message("🔴 **سیگنال فروش طلا (XAUUSD)**\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴برابر: نزولی\n- مک‌دی دیفالت: اولین میله بالای صفر بسته شد.")
                        print("سیگنال فروش ارسال شد.", flush=True)
                        last_signal_time = current_time_label
                        
        time.sleep(60)
        
    except Exception as e:
        print(f"خطا: {e}", flush=True)
        time.sleep(60)
