# bot.py
# Telegram ATR Levels Bot — asks inputs and returns ONLY Long OR Short table per your answer.

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# ---- CONFIG ----
BOT_TOKEN = "8371786634:AAFf4rWfUWxGbBgY-0jPfaOEUjbVkDlK4RY"   # <-- yahan BotFather ka token daalo
POSITIVE_MAX = 2
NEGATIVE_MAX = 50
DECIMALS = 2
# ----------------

# Conversation states
CURRENCY, DIRECTION, ATR, ENTRY = range(4)

def _is_float(text: str) -> bool:
    try:
        float(text.replace(",", ""))
        return True
    except Exception:
        return False

def _fmt(num: float) -> str:
    return f"{num:,.{DECIMALS}f}"

def _build_table(entry_price: float, atr_val: float, direction: str) -> str:
    """Table banaata hai sirf LONG ya SHORT ke liye"""
    n_values = [2, 1, 0] + list(range(-1, -NEGATIVE_MAX - 1, -1))

    lines = []
    if direction == "Long":
        header = "ATR Value | For Long position"
        sep    = "---------+-------------------"
    else:
        header = "ATR Value | For Short position"
        sep    = "---------+-------------------"

    lines.append(header)
    lines.append(sep)

    for n in n_values:
        if direction == "Long":
            level = entry_price + (n * atr_val)
        else:
            level = entry_price + (-n * atr_val)

        label = f"{n:+d} ATR" if n != 0 else "0 ATR "
        lines.append(f"{label:>8} | {_fmt(level):>17}")

    table = "\n".join(lines)
    return f"<pre>{table}</pre>"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Welcome! 👋\nMain tumse 4 inputs loonga aur ATR table banaaunga.\n\n"
        "1) Which currency?\n"
        "2) Entry position (Long/Short)?\n"
        "3) ATR Value at entry?\n"
        "4) Exact entry price?\n\n"
        "Chalo shuru karein — *Which currency?* (e.g., BTCUSDT, XAUUSD, NIFTY)",
    )
    return CURRENCY

async def get_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["currency"] = update.message.text.strip()
    await update.message.reply_text("Entry position — Long or Short?")
    return DIRECTION

async def get_direction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip().lower()
    if txt in ("long", "l", "buy"):
        context.user_data["direction"] = "Long"
    elif txt in ("short", "s", "sell"):
        context.user_data["direction"] = "Short"
    else:
        await update.message.reply_text("Please type exactly *Long* or *Short* 🙂")
        return DIRECTION
    await update.message.reply_text("ATR value at the time of entry? (number, e.g., 22.56)")
    return ATR

async def get_atr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.replace(" ", "")
    if not _is_float(txt):
        await update.message.reply_text("ATR number sahi bhejo (e.g., 18.25). Try again:")
        return ATR
    context.user_data["atr"] = float(txt.replace(",", ""))
    await update.message.reply_text("Exact entry price? (e.g., 24863.70)")
    return ENTRY

async def get_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.replace(" ", "")
    if not _is_float(txt):
        await update.message.reply_text("Entry price number sahi bhejo (e.g., 24863.70). Try again:")
        return ENTRY

    entry_price = float(txt.replace(",", ""))
    atr_val = float(context.user_data["atr"])
    currency = context.user_data["currency"]
    direction = context.user_data["direction"]

    # Build table based on chosen direction only
    table_html = _build_table(entry_price, atr_val, direction)

    header = (
        f"Below is your {direction} position table\n\n"
        f"Currency: {currency}\n"
        f"Direction: {direction}\n"
        f"ATR: {_fmt(atr_val)} | Entry: {_fmt(entry_price)}\n"
        f"(+{POSITIVE_MAX} ATR se -{NEGATIVE_MAX} ATR tak)\n"
    )
    await update.message.reply_text(header)
    await update.message.reply_text(table_html, parse_mode=ParseMode.HTML)

    await update.message.reply_text(
        "Done ✅  — /start type karke naya calc kar sakte ho ya /cancel se exit."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelled. Kabhi bhi /start kar dena. 👋")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CURRENCY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_currency)],
            DIRECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_direction)],
            ATR:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_atr)],
            ENTRY:     [MessageHandler(filters.TEXT & ~filters.COMMAND, get_entry)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("cancel", cancel))

    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
