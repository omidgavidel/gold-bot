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

print("ربات رصد طلا با موفقیت استارت شد و وارد حلقه شد...", flush=True)
send_telegram_message("🟢 ربات ترید طلا روشن شد و در حال رصد بازار است.")

last_signal_time = None

while True:
    try:
        print("در حال بررسی بازار طلا...", flush=True)
        df = yf.download(tickers="GC=F", interval="15m", period="2d", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if len(df) > 50:
            close = df['Close']
            _, _, hist_def = calculate_macd(close, 12, 26, 9)
            macd_4x, sig_4x, _ = calculate_macd(close, 48, 104, 36)
            
            curr = df.iloc[-2]
            prev = df.iloc[-3]
            
            m4_curr = macd_4x.iloc[-2]
            s4_curr = sig_4x.iloc[-2]
            
            h_curr = hist_def.iloc[-2]
            h_prev = hist_def.iloc[-3]
            
            is_4x_bullish = m4_curr > s4_curr
            is_4x_bearish = m4_curr < s4_curr
            
            is_first_negative_bar = (h_curr < 0) and (h_prev >= 0)
            is_first_positive_bar = (h_curr > 0) and (h_prev <= 0)
            
            current_time_label = str(df.index[-2])
            
            if is_4x_bullish and is_first_negative_bar:
                if last_signal_time != current_time_label:
                    send_telegram_message("🟢 سیگنال خرید طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر صعودی.\n- اولین میله مک‌دی دیفالت زیر صفر بسته شد.")
                    print("سیگنال خرید ارسال شد.", flush=True)
                    last_signal_time = current_time_label
                    
            elif is_4x_bearish and is_first_positive_bar:
                if last_signal_time != current_time_label:
                    send_telegram_message("🔴 سیگنال فروش طلا (XAUUSD)\n- تایم‌فریم: ۱۵ دقیقه\n- مک‌دی ۴ برابر نزولی.\n- اولین میله مک‌دی دیفالت بالای صفر بسته شد.")
                    print("سیگنال فروش ارسال شد.", flush=True)
                    last_signal_time = current_time_label
                    
        # استراحت ۶۰ ثانیه‌ای قبل از بررسی بعدی
        time.sleep(60)
        
    except Exception as e:
        print(f"خطای غیرمنتظره در حلقه: {e}", flush=True)
        time.sleep(60)
