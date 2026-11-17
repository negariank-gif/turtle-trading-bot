import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(text):
    if not TOKEN or not CHAT_ID:
        print("❌ توکن یا چت آیدی تنظیم نشده است.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ پیام با موفقیت به تلگرام ارسال شد.")
    except Exception as e:
        print(f"❌ خطا در ارسال پیام: {e}")

def check_turtle_signal():
    print("⏳ در حال دریافت داده‌های بازار...")
    # لیست ارتقا یافته: طلا، نقره، بیت‌کوین، دوج، ریپل، سولانا، اتریوم، آوالانچ
    assets = {
        "🥇 طلا": "GC=F", 
        "🥈 نقره": "SI=F", 
        "₿ بیت‌کوین": "BTC-USD", 
        "🐕 دوج کوین": "DOGE-USD", 
        "💧 ریپل": "XRP-USD",
        "☀️ سولانا": "SOL-USD",
        "💎 اتریوم": "ETH-USD",
        "🏔️ آوالانچ": "AVAX-USD"
    }
    
    message_body = "📊 **گزارش روزانه بازار (الگوریتم لاک‌پشت)**\n\n"
    signal_found = False

    for name, ticker in assets.items():
        try:
            data = yf.download(ticker, period="1y", interval="1d", auto_adjust=False, progress=False)
            if data.empty: continue

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            df = data[["High", "Low", "Close"]].copy()
            df.columns = ["high", "low", "close"]
            df = df.dropna()

            df['high_20'] = df['high'].rolling(window=20).max().shift(1)
            df['tr'] = np.maximum(df['high'] - df['low'], 
                                  np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                             abs(df['low'] - df['close'].shift(1))))
            df['atr'] = df['tr'].rolling(window=14).mean()
            df = df.dropna()

            last_row = df.iloc[-1]
            current_price = float(last_row['close'])
            recent_high = float(last_row['high_20'])
            current_atr = float(last_row['atr'])

            if current_price > recent_high:
                signal_found = True
                stop_loss = current_price - (3 * current_atr)
                message_body += f"🟢 **{name}** | سیگنال خرید!\n"
                message_body += f"قیمت: `{current_price:,.2f}`\n"
                message_body += f"حد ضرر: `{stop_loss:,.2f}`\n\n"
            else:
                distance = ((recent_high / current_price) - 1) * 100
                message_body += f"🔴 **{name}** | صبر کنید ({distance:.1f}% تا خرید)\n\n"

        except Exception as e:
            message_body += f"⚠️ **{name}** | خطا در تحلیل: {str(e)}\n\n"

    if signal_found:
        send_telegram_message("🚨 **هشدار سیگنال خرید!**\n\n" + message_body)
    else:
        send_telegram_message("📊 **گزارش وضعیت روزانه (بدون سیگنال خرید)**\n\n" + message_body)

if __name__ == "__main__":
    check_turtle_signal()
