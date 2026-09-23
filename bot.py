import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

class DummyHandler(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(200)
self.send_header('Content-type', 'text/plain')
self.end_headers()
self.wfile.write(b"Bot is alive!")

def run_dummy_server():
port = int(os.environ.get("PORT", 10000))
server = HTTPServer(('0.0.0.0', port), DummyHandler)
server.serve_forever()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

server_params = StdioServerParameters(
command="npx",
args=["-y", "@mmdju/divar-mcp"],
env=os.environ.copy()
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
status_msg = await update.message.reply_text("🤖 در حال جستجو...")
try:
async with stdio_client(server_params) as (read, write):
async with ClientSession(read, write) as session:
await session.initialize()

            extraction_prompt = f'کاربر: "{update.message.text}"\nفقط یک JSON بده شامل "query" و "city" (پیش‌فرض tehran). متن اضافه ننویس.'
            response = model.generate_content(extraction_prompt)
            json_text = response.text.replace('```json', '').replace('```', '').strip()
            search_params = json.loads(json_text)
            
            mcp_result = await session.call_tool("search", arguments=search_params)
            
            summary_prompt = f'کاربر: {update.message.text}\nنتایج خام: {mcp_result.content}\nنتایج را به فارسی روان و خلاصه برای تلگرام با ایموجی قالب‌بندی کن.'
            final_answer = model.generate_content(summary_prompt)
            await status_msg.edit_text(final_answer.text)
except Exception as e:
    await status_msg.edit_text("❌ خطایی رخ داد.")


def main():
threading.Thread(target=run_dummy_server, daemon=True).start()
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()

if name == "main":
main()
