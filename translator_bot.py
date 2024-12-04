import argparse

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from translator.Translator import Translator

parser = argparse.ArgumentParser(prog="Translator", description="Well-format and sentencewise translate text")
parser.add_argument("-t", "--token", required=True, help="Telegram bot token")
parser.add_argument("-w", "--whitelist", required=True, type=int, nargs="+", help="Allowed users' IDs")

args = parser.parse_args()


def _translate(text: str):
    batch = []
    for pair in Translator(text, "ru").translated:
        batch.append(f"<blockquote>{pair[0]}</blockquote>\n<code>{pair[1]}</code>")
        if (sum(len(p) for p in batch) + (len(batch) - 1)) >= 4096:
            next_batch = [batch.pop()]
            yield "\n".join(batch)
            batch = next_batch

    if batch:
        yield "\n".join(batch)


async def translate(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if update.message.from_user is None:
        return
    if update.message.from_user["id"] not in args.whitelist:
        return

    if update.message.text is not None:
        for chunk in _translate(update.message.text):
            await update.message.reply_html(chunk)

    if update.message.document is not None:
        file = await update.message.document.get_file()
        data = await file.download_as_bytearray()
        for chunk in _translate(data.decode("utf-8-sig")):
            await update.message.reply_html(chunk)


app = ApplicationBuilder().token(args.token).build()
app.add_handler(MessageHandler(filters.ALL, translate))
app.run_polling()
