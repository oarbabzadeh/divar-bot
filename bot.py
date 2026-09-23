import os
import json
import logging
import asyncio
import threading
from typing import Optional, Dict, Any
from http.server import BaseHTTPRequestHandler, HTTPServer
from contextlib import AsyncExitStack

from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import google.generativeai as genai
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# ---------------------------------------------------------
# ۱. تنظیمات لاگ‌گیری استاندارد (Logging)
# ---------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("DivarTelegramBot")

# ---------------------------------------------------------
# ۲. خواندن متغیرهای محیطی
# ---------------------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PORT = int(os.environ.get("PORT", 10000))

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logger.critical("❌ لطفاً متغیرهای TELEGRAM_TOKEN و GEMINI_API_KEY را در تنظیمات Render تنظیم کنید.")
    exit(1)

# پیکربندی Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------------------------------------------------
# ۳. وب‌سرور سبک جهت عبور از Health Check رندر
# ---------------------------------------------------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Divar Bot is healthy and running!")

    def log_message(self, format, *args):
        # جلوگیری از پر شدن لاگ‌ها با درخواست‌های مکرر Health check
        return

def run_health_check_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthCheckHandler)
    logger.info(f"🌐 Health check HTTP server is listening on port {PORT}")
    server.serve_forever()

# ---------------------------------------------------------
# ۴. مدیریت کانکشن پای
