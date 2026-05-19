#!/usr/bin/env python3
"""diyzu Bot — Telegram Shop Bot (Fixed v3)"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import subprocess
import uuid
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
    PicklePersistence
)
from telegram.error import Conflict, NetworkError, TimedOut

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
BOT_TOKEN       = os.environ.get("BOT_TOKEN", "8564888521:AAHt0S7HHT5ksKEmUWCo6cUc0qyAq-t6xMY")

# Super admin — full access including viewing raw key values
SUPER_ADMIN_ID  = 8503115617

# These are hardcoded fallback admins (added here so they work before any DB admin is added)
# They have regular admin access (cannot view raw keys)
HARDCODED_ADMINS: list[int] = [7248702461]

DEFAULT_SHOP_NAME      = "diyzu Bot"
DEFAULT_SUPPORT        = "@support"
DEFAULT_VERIFY_CHANNEL = 0   # Set to your channel ID (negative number) or 0 to skip verify

DATA_FILE = "bot_data.json"

BINANCE_QR_PATHS = ["binance_qr.jpg", "binance_qr.png", "binance.jpg", "binance.png"]

def find_image(paths: list) -> str | None:
    for p in paths:
        if Path(p).exists():
            return p
    return None

# ═══════════════════════════════════════════════════════════════════════════════
#  CUSTOM EMOJIS
# ═══════════════════════════════════════════════════════════════════════════════
def ce(eid: str, fb: str) -> str:
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

CE_FF       = ce("6228904568747465283", "🔥")
CE_FLUORITE = ce("5292158397465005457", "💎")
CE_MIGUL    = ce("6233248412771295068", "⭐")
CE_PROXY    = ce("5796407074346767851", "🔷")
CE_DRIP     = ce("6212942266957310140", "💧")
CE_HG       = ce("6210499577322151683", "🎯")
CE_iOSCERT  = ce("5965079210383907241", "📜")

CE_ANIM     = ce("5456140674028019486", "⏳")
CE_WELCOME  = ce("5429245339712391471", "👋")
CE_SHOP     = ce("5258021357446268553", "🏪")
CE_WALLET   = "💰"
CE_ADMIN    = "🔧"
CE_STATUS   = "✅"
CE_AVAIL    = ce("5445195276291693508", "🟢")
CE_UNAVAIL  = ce("5445102217235292298", "🔴")
CE_STATS    = "📊"
CE_DENY     = "❌"
CE_SUCCESS  = "🎉"
CE_PROD_LBL = "📦"
CE_DUR_LBL  = "⏱️"
CE_KEY_LBL  = "🔑"
CE_SETTINGS = "⚙️"
CE_RESELLER = "🏷️"
CE_LOCK     = "🔒"
CE_SHIELD   = "🛡️"

CE_RES_LOGIN  = ce("5429405838345265327", "🔐")
CE_ACCT       = ce("5190577236889053608", "👤")
CE_BAL_ICON   = ce("5764706418951200101", "💰")
CE_VERIFIED   = ce("5764725626044948428", "✅")
CE_STOCK_HDR  = ce("5203993413346680064", "📊")
CE_ADDKEYS    = ce("5767421783175076360", "🔑")
CE_ADDFILE    = ce("5357315181649076022", "📁")
CE_BAL_UPD    = ce("6001434068435079689", "💸")
CE_PURCH_OK   = ce("5953810354365538566", "🎉")
CE_KEY_ICO    = ce("5278573677900752088", "🗝️")
CE_DUR_ICO    = ce("5257977213772400201", "⏱️")
CE_PRICE_ICO  = ce("5951784276558093439", "💵")
CE_IMPORT     = ce("6147734574525848830", "⚠️")
CE_STATUS_ICO = ce("6059653892025618055", "✅")
CE_STOCK_ICO  = ce("5323289282499064033", "📦")
CE_UPI_ICO    = ce("6242055415010429981", "🏦")
CE_BNB_ICO    = ce("5285185333376325970", "₿")

# ═══════════════════════════════════════════════════════════════════════════════
#  PRODUCT MENU
# ═══════════════════════════════════════════════════════════════════════════════
BASE_MENU = {
    "ff_ios": {
        "label": "Free Fire (iOS)",
        "ce":    CE_FF,
        "products": [
            {
                "id": "fluorite",
                "name": "Fluorite",
                "ce": CE_FLUORITE,
                "prices": [
                    ("7 Day",  "13.00"),
                    ("31 Day", "22.00"),
                ],
            },
            {
                "id": "migul",
                "name": "Migul",
                "ce": CE_MIGUL,
                "prices": [
                    ("7 Day",  "12.00"),
                    ("31 Day", "20.00"),
                ],
            },
            {
                "id": "proxy",
                "name": "Proxy",
                "ce": CE_PROXY,
                "prices": [
                    ("7 Day",  "6.00"),
                    ("31 Day", "10.00"),
                ],
            },
            {
                "id": "ios_cert",
                "name": "iOS Cert",
                "ce": CE_iOSCERT,
                "prices": [
                    ("1 Year", "12.00"),
                ],
            },
        ],
    },
    "ff_android": {
        "label": "Free Fire (Android)",
        "ce":    CE_FF,
        "products": [
            {
                "id": "drip",
                "name": "Drip",
                "ce": CE_DRIP,
                "prices": [
                    ("7 Day",  "8.00"),
                    ("31 Day", "15.00"),
                ],
            },
            {
                "id": "hg",
                "name": "HG",
                "ce": CE_HG,
                "prices": [
                    ("7 Day",  "6.00"),
                    ("31 Day", "12.00"),
                ],
            },
        ],
    },
}
CAT_ORDER = ["ff_ios", "ff_android"]

# ═══════════════════════════════════════════════════════════════════════════════
#  RESELLER MENU
# ═══════════════════════════════════════════════════════════════════════════════
RESELLER_MENU = [
    {
        "id":    "fluorite",
        "name":  "Fluorite",
        "ce":    CE_FLUORITE,
        "prices": [
            ("1 Day",  "2.00"),
            ("7 Day",  "6.00"),
            ("31 Day", "10.00"),
        ],
    },
    {
        "id":    "migul_pro",
        "name":  "Migul Pro",
        "ce":    CE_MIGUL,
        "prices": [
            ("31 Day", "7.50"),
        ],
    },
    {
        "id":    "migul_basic",
        "name":  "Migul Basic",
        "ce":    CE_MIGUL,
        "prices": [
            ("Fixed", "5.00"),
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
#  DATA HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
_MEM_DATA:  dict = {}
_MEM_STATE: dict = {}

def load() -> dict:
    global _MEM_DATA
    d = None
    if Path(DATA_FILE).exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            pass
    if d is None:
        d = dict(_MEM_DATA) if _MEM_DATA else {}
    d.setdefault("verified", [])
    d.setdefault("admin_ids", [])
    d.setdefault("keys", {})
    d.setdefault("res_keys", {})
    d.setdefault("files", {})
    d.setdefault("balances", {})
    d.setdefault("pending_orders", {})
    d.setdefault("_state", {})
    d.setdefault("config", {})
    d.setdefault("resellers", {})
    d.setdefault("reseller_sessions", {})
    return d

def save(d: dict):
    global _MEM_DATA
    _MEM_DATA = d
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)
    except Exception:
        pass

def get_state(d: dict, uid: int):
    key = str(uid)
    return d.get("_state", {}).get(key) or _MEM_STATE.get(key)

def set_state(d: dict, uid: int, state):
    key = str(uid)
    _MEM_STATE[key] = state
    d.setdefault("_state", {})[key] = state
    save(d)

def clear_state(d: dict, uid: int):
    key = str(uid)
    _MEM_STATE.pop(key, None)
    d.setdefault("_state", {}).pop(key, None)
    save(d)

def is_super_admin(uid: int) -> bool:
    return uid == SUPER_ADMIN_ID

def is_admin(uid: int, d: dict) -> bool:
    return uid == SUPER_ADMIN_ID or uid in HARDCODED_ADMINS or uid in d.get("admin_ids", [])

def can_view_keys(uid: int, d: dict) -> bool:
    return uid == SUPER_ADMIN_ID or uid in d.get("key_view_admins", [])

def is_verified(uid: int, d: dict) -> bool:
    return is_admin(uid, d) or uid in d.get("verified", [])

def get_balance(uid: int, d: dict) -> float:
    return round(float(d.get("balances", {}).get(str(uid), 0.0)), 2)

def get_reseller_balance(username: str, d: dict) -> float:
    info = d.get("resellers", {}).get(username, {})
    return round(float(info.get("balance", 0.0)), 2)

def set_reseller_balance(username: str, amount: float, d: dict):
    d.setdefault("resellers", {}).setdefault(username, {})["balance"] = round(amount, 2)
    save(d)

def get_reseller_session(uid: int, d: dict) -> str | None:
    return d.get("reseller_sessions", {}).get(str(uid))

def set_reseller_session(uid: int, username: str, d: dict):
    d.setdefault("reseller_sessions", {})[str(uid)] = username
    save(d)

def clear_reseller_session(uid: int, d: dict):
    d.setdefault("reseller_sessions", {}).pop(str(uid), None)
    save(d)

def esc(t) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def cfg(d: dict, key: str, default):
    return d.get("config", {}).get(key, default)

def shop_name(d: dict) -> str:
    return cfg(d, "shop_name", DEFAULT_SHOP_NAME)

def support(d: dict) -> str:
    return cfg(d, "support", DEFAULT_SUPPORT)

def verify_channel(d: dict) -> int:
    return int(cfg(d, "verify_channel", DEFAULT_VERIFY_CHANNEL))

def prod_name(cat_key: str, idx: int, d: dict) -> str:
    key = f"{cat_key}_{idx}_name"
    return cfg(d, key, BASE_MENU[cat_key]["products"][idx]["name"])

def prod_prices(cat_key: str, idx: int, d: dict) -> list[tuple[str, str]]:
    base = BASE_MENU[cat_key]["products"][idx]["prices"]
    overrides = d.get("config", {}).get("prices", {}).get(f"{cat_key}_{idx}", {})
    if not overrides:
        return base
    return [(dur, overrides.get(dur, price)) for dur, price in base]

def set_price(cat_key: str, idx: int, dur: str, new_price: str, d: dict):
    d.setdefault("config", {}).setdefault("prices", {}).setdefault(f"{cat_key}_{idx}", {})[dur] = new_price
    save(d)

def reseller_prod_prices(idx: int, d: dict) -> list[tuple[str, str]]:
    base = RESELLER_MENU[idx]["prices"]
    overrides = d.get("config", {}).get("reseller_prices", {}).get(str(idx), {})
    if not overrides:
        return base
    return [(dur, overrides.get(dur, price)) for dur, price in base]

def set_reseller_price(idx: int, dur: str, new_price: str, d: dict):
    d.setdefault("config", {}).setdefault("reseller_prices", {}).setdefault(str(idx), {})[dur] = new_price
    save(d)

# ═══════════════════════════════════════════════════════════════════════════════
#  KEY / FILE / STOCK HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def key_slot(cat: str, idx: int, dur: str) -> str:
    return f"{cat}_{idx}_{dur}"

def file_slot(cat: str, idx: int) -> str:
    return f"file_{cat}_{idx}"

def keys_count(cat: str, idx: int, dur: str, d: dict) -> int:
    return len(d.get("keys", {}).get(key_slot(cat, idx, dur), []))

def files_count(cat: str, idx: int, d: dict) -> int:
    return len(d.get("files", {}).get(file_slot(cat, idx), []))

def slot_stock(cat: str, idx: int, dur: str, d: dict) -> int:
    return keys_count(cat, idx, dur, d)

def total_product_stock(k: str, i: int, d: dict) -> int:
    return sum(slot_stock(k, i, dur, d) for dur, _ in prod_prices(k, i, d))

def pop_key(cat: str, idx: int, dur: str, d: dict):
    slot = key_slot(cat, idx, dur)
    lst  = d.get("keys", {}).get(slot, [])
    if not lst:
        return None
    k = lst.pop(0)
    d["keys"][slot] = lst
    save(d)
    return k

def pop_file(cat: str, idx: int, d: dict):
    slot = file_slot(cat, idx)
    lst  = d.get("files", {}).get(slot, [])
    if not lst:
        return None
    f = lst.pop(0)
    d["files"][slot] = lst
    save(d)
    return f

def peek_file(cat: str, idx: int, d: dict):
    slot = file_slot(cat, idx)
    lst  = d.get("files", {}).get(slot, [])
    return lst[0] if lst else None

# ═══════════════════════════════════════════════════════════════════════════════
#  RESELLER KEY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def res_key_slot(idx: int, dur: str) -> str:
    return f"res_{idx}_{dur}"

def res_keys_count(idx: int, dur: str, d: dict) -> int:
    return len(d.get("res_keys", {}).get(res_key_slot(idx, dur), []))

def res_total_stock(idx: int, d: dict) -> int:
    return sum(res_keys_count(idx, dur, d) for dur, _ in reseller_prod_prices(idx, d))

def res_pop_key(idx: int, dur: str, d: dict) -> str | None:
    slot = res_key_slot(idx, dur)
    lst  = d.get("res_keys", {}).get(slot, [])
    if not lst:
        return None
    k = lst.pop(0)
    d["res_keys"][slot] = lst
    save(d)
    return k

# ═══════════════════════════════════════════════════════════════════════════════
#  ENCODE / DECODE DUR (keeps callback_data safe and short)
# ═══════════════════════════════════════════════════════════════════════════════
def enc_dur(dur: str) -> str:
    return dur.replace(" ", "~").replace("(", "").replace(")", "").replace("/", "-")

def dec_dur(dur_enc: str) -> str:
    return dur_enc.replace("~", " ")

async def send_long(target, text: str, **kwargs):
    limit = 4096
    if len(text) <= limit:
        await target.reply_text(text, **kwargs)
        return
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        chunks.append(current)
    for chunk in chunks:
        await target.reply_text(chunk, **kwargs)
        await asyncio.sleep(0.15)

# ═══════════════════════════════════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════════
def kb_main(uid: int, d: dict) -> ReplyKeyboardMarkup:
    rows = [
        ["Shop"],
        ["Account", "Stock"],
        ["Reseller"],
    ]
    if is_admin(uid, d):
        rows.append(["Admin Panel"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def kb_verify() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅  Verify Access", callback_data="verify")
    ]])

def kb_cat(k: str, d: dict) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            prod_name(k, i, d),
            callback_data=f"prod|{k}|{i}"
        )]
        for i in range(len(BASE_MENU[k]["products"]))
    ]
    return InlineKeyboardMarkup(rows)

def kb_durations(k: str, idx: int, d: dict) -> InlineKeyboardMarkup:
    rows = []
    for dur, price in prod_prices(k, idx, d):
        qty    = slot_stock(k, idx, dur, d)
        status = "✅" if qty > 0 else "❌"
        dur_enc = enc_dur(dur)
        rows.append([InlineKeyboardButton(
            f"{status}  {dur}  —  ${price}",
            callback_data=f"dur|{k}|{idx}|{dur_enc}|{price}"
        )])
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data=f"cat|{k}")])
    return InlineKeyboardMarkup(rows)

def kb_buy_methods(k: str, idx: int, dur_enc: str, price: str, d: dict) -> InlineKeyboardMarkup:
    base = f"{k}|{idx}|{dur_enc}|{price}"
    binance_id = cfg(d, "binance_id", "")
    upi_qr     = cfg(d, "upi_qr_file_id", "")
    rows = [
        [InlineKeyboardButton(f"💰  Balance  (${price})", callback_data=f"pay|bal|{base}")],
    ]
    if upi_qr:
        rows.append([InlineKeyboardButton("🏦  UPI Payment", callback_data=f"pay|upi|{base}")])
    if binance_id:
        rows.append([InlineKeyboardButton("₿  Binance Pay", callback_data=f"pay|bnb|{base}")])
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data=f"prod|{k}|{idx}")])
    return InlineKeyboardMarkup(rows)

def kb_approve_deny(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅  Approve", callback_data=f"approve|{order_id}"),
        InlineKeyboardButton("❌  Deny",    callback_data=f"deny|{order_id}"),
    ]])

def kb_cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌  Cancel", callback_data="adm|cancel")
    ]])

def kb_admin_panel(uid: int, d: dict) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔑  Add Keys",         callback_data="adm|add_keys"),
         InlineKeyboardButton("📁  Add File",         callback_data="adm|add_files")],
        [InlineKeyboardButton("📦  View Stock",       callback_data="adm|view_keys"),
         InlineKeyboardButton("📁  View Files Stock", callback_data="adm|view_files")],
        [InlineKeyboardButton("🗑️  Remove File",      callback_data="adm|remove_file"),
         InlineKeyboardButton("🗑️  Remove Keys",      callback_data="adm|clear")],
        [InlineKeyboardButton("💰  Add Balance",      callback_data="adm|add_bal"),
         InlineKeyboardButton("💰  Deduct Balance",   callback_data="adm|ded_bal")],
        [InlineKeyboardButton("💰  Check Balance",    callback_data="adm|chk_bal"),
         InlineKeyboardButton("👑  Add Admin",        callback_data="adm|add_admin")],
        [InlineKeyboardButton("🗑️  Remove Admin",     callback_data="adm|remove_admin")],
        [InlineKeyboardButton("📢  Broadcast",        callback_data="adm|broadcast")],
        [InlineKeyboardButton("🗑️  Clear Pending Orders", callback_data="adm|clear_pending")],
        [InlineKeyboardButton(f"{CE_RESELLER}  Reseller Mgmt", callback_data="adm|reseller_mgmt")],
        [InlineKeyboardButton(f"{CE_SETTINGS}  Settings",      callback_data="cfg|menu")],
    ]
    if can_view_keys(uid, d):
        rows.insert(2, [InlineKeyboardButton("🔑  View Raw Keys", callback_data="adm|view_raw_keys")])
    if is_super_admin(uid):
        rows.insert(-1, [InlineKeyboardButton("🛡️  Grant Key-View Access", callback_data="adm|grant_key_view")])
    return InlineKeyboardMarkup(rows)

def kb_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏪  Shop Name",        callback_data="cfg|shop_name"),
         InlineKeyboardButton("📞  Support",          callback_data="cfg|support")],
        [InlineKeyboardButton("📦  Product Prices",   callback_data="cfg|prices_menu")],
        [InlineKeyboardButton(f"{CE_RESELLER}  Reseller Prices", callback_data="cfg|rprices_menu")],
        [InlineKeyboardButton("🏦  Set UPI QR Image", callback_data="cfg|set_upi"),
         InlineKeyboardButton("₿  Set Binance ID",   callback_data="cfg|set_bnb")],
        [InlineKeyboardButton("🖼  Set Binance Image", callback_data="cfg|set_bnb_img")],
        [InlineKeyboardButton("⬅️  Back",             callback_data="adm|back")],
    ])

def kb_cfg_prices_cats(d: dict) -> InlineKeyboardMarkup:
    rows = []
    for k in CAT_ORDER:
        for i, p in enumerate(BASE_MENU[k]["products"]):
            name = prod_name(k, i, d)
            rows.append([InlineKeyboardButton(
                name, callback_data=f"cfg|pp|{k}|{i}"
            )])
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data="cfg|menu")])
    return InlineKeyboardMarkup(rows)

def kb_cfg_prices_durs(k: str, idx: int, d: dict) -> InlineKeyboardMarkup:
    rows = []
    for dur, price in prod_prices(k, idx, d):
        dur_enc = enc_dur(dur)
        rows.append([InlineKeyboardButton(
            f"{dur}  — ${price}",
            callback_data=f"cfg|ppd|{k}|{idx}|{dur_enc}"
        )])
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data="cfg|prices_menu")])
    return InlineKeyboardMarkup(rows)

def kb_cfg_rprices(d: dict) -> InlineKeyboardMarkup:
    rows = []
    for i, p in enumerate(RESELLER_MENU):
        rows.append([InlineKeyboardButton(
            p['name'], callback_data=f"cfg|rpp|{i}"
        )])
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data="cfg|menu")])
    return InlineKeyboardMarkup(rows)

def kb_cfg_rprices_durs(idx: int, d: dict) -> InlineKeyboardMarkup:
    rows = []
    for dur, price in reseller_prod_prices(idx, d):
        dur_enc = enc_dur(dur)
        rows.append([InlineKeyboardButton(
            f"{dur}  — ${price}",
            callback_data=f"cfg|rppd|{idx}|{dur_enc}"
        )])
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data="cfg|rprices_menu")])
    return InlineKeyboardMarkup(rows)

def kb_adm_cats_keys(d: dict) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(BASE_MENU[k]["label"], callback_data=f"akc|{k}")]
        for k in CAT_ORDER
    ]
    rows.append([InlineKeyboardButton("❌  Cancel", callback_data="adm|cancel")])
    return InlineKeyboardMarkup(rows)

def kb_adm_cats_files(prefix: str, d: dict) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(BASE_MENU[k]["label"], callback_data=f"{prefix}fc|{k}")]
        for k in CAT_ORDER
    ]
    rows.append([InlineKeyboardButton("❌  Cancel", callback_data="adm|cancel")])
    return InlineKeyboardMarkup(rows)

def kb_adm_prods_keys(cat_key: str, d: dict) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(prod_name(cat_key, i, d), callback_data=f"akp|{cat_key}|{i}")]
        for i in range(len(BASE_MENU[cat_key]["products"]))
    ]
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data="adm|add_keys")])
    return InlineKeyboardMarkup(rows)

def kb_adm_prods_files(prefix: str, cat_key: str, d: dict) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(prod_name(cat_key, i, d), callback_data=f"{prefix}fp|{cat_key}|{i}")]
        for i in range(len(BASE_MENU[cat_key]["products"]))
    ]
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data=f"{prefix}fc|{cat_key}")])
    return InlineKeyboardMarkup(rows)

def kb_adm_durs_keys(cat_key: str, idx: int, d: dict) -> InlineKeyboardMarkup:
    rows = []
    for dur, _ in prod_prices(cat_key, idx, d):
        dur_enc = enc_dur(dur)
        rows.append([InlineKeyboardButton(dur, callback_data=f"akd|{cat_key}|{idx}|{dur_enc}")])
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data=f"akc|{cat_key}")])
    return InlineKeyboardMarkup(rows)

# ── Reseller keyboards ─────────────────────────────────────────────────────────
def kb_reseller_products(d: dict) -> InlineKeyboardMarkup:
    rows = []
    for i, p in enumerate(RESELLER_MENU):
        total = res_total_stock(i, d)
        dot   = "✅" if total > 0 else "❌"
        rows.append([InlineKeyboardButton(
            f"{dot}  {p['name']}  ({total} keys)", callback_data=f"res_prod|{i}"
        )])
    rows.append([InlineKeyboardButton("💰  My Balance",    callback_data="res_balance")])
    rows.append([InlineKeyboardButton("🚪  Logout",        callback_data="res_logout")])
    return InlineKeyboardMarkup(rows)

def kb_reseller_durs(idx: int, d: dict) -> InlineKeyboardMarkup:
    rows = []
    for dur, price in reseller_prod_prices(idx, d):
        dur_enc = enc_dur(dur)
        qty     = res_keys_count(idx, dur, d)
        dot     = "✅" if qty > 0 else "❌"
        rows.append([InlineKeyboardButton(
            f"{dot}  {dur}  —  ${price}  ({qty} left)", callback_data=f"res_dur|{idx}|{dur_enc}|{price}"
        )])
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data="res_menu")])
    return InlineKeyboardMarkup(rows)

def kb_reseller_buy(idx: int, dur_enc: str, price: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💰  Buy (${price})", callback_data=f"res_buy|{idx}|{dur_enc}|{price}")],
        [InlineKeyboardButton("⬅️  Back", callback_data=f"res_prod|{idx}")],
    ])

# ── Reseller admin keyboards ───────────────────────────────────────────────────
def kb_res_add_keys_prods() -> InlineKeyboardMarkup:
    rows = []
    for i, p in enumerate(RESELLER_MENU):
        rows.append([InlineKeyboardButton(p["name"], callback_data=f"rakp|{i}")])
    rows.append([InlineKeyboardButton("❌  Cancel", callback_data="adm|cancel")])
    return InlineKeyboardMarkup(rows)

def kb_res_add_keys_durs(idx: int, d: dict) -> InlineKeyboardMarkup:
    rows = []
    for dur, _ in reseller_prod_prices(idx, d):
        dur_enc = enc_dur(dur)
        rows.append([InlineKeyboardButton(dur, callback_data=f"rakd|{idx}|{dur_enc}")])
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data="adm|res_add_keys")])
    return InlineKeyboardMarkup(rows)

# ═══════════════════════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def cat_msg(k: str, d: dict) -> str:
    cat = BASE_MENU[k]
    lines = [f"{CE_SHOP} <b>{esc(cat['label'])}</b>\n"]
    for i, p in enumerate(cat["products"]):
        pname  = prod_name(k, i, d)
        prices = prod_prices(k, i, d)
        lines.append(f"{p['ce']} <b>{esc(pname)}</b>")
        for dur, pr in prices:
            lines.append(f"   ‣ {esc(dur)}  —  <b>${esc(pr)}</b>")
        lines.append("")
    return "\n".join(lines)

def reseller_menu_msg(username: str, d: dict) -> str:
    bal = get_reseller_balance(username, d)
    lines = [
        f"{CE_RESELLER} <b>Reseller Menu — diyzu Bot</b>",
        f"{CE_WALLET} Balance: <b>${bal:.2f}</b>\n",
        f"<b>Products</b>",
    ]
    for i, p in enumerate(RESELLER_MENU):
        prices = reseller_prod_prices(i, d)
        total  = res_total_stock(i, d)
        dot    = CE_AVAIL if total > 0 else CE_UNAVAIL
        lines.append(f"{dot} {p['ce']} <b>{esc(p['name'])}</b>  [{total} keys]")
        for dur, pr in prices:
            qty = res_keys_count(i, dur, d)
            lines.append(f"   ‣ {esc(dur)}  —  <b>${esc(pr)}</b>  ({qty} left)")
        lines.append("")
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
#  VERIFY ANIMATION
# ═══════════════════════════════════════════════════════════════════════════════
async def run_verify(query, uid: int, ctx: ContextTypes.DEFAULT_TYPE, d: dict):
    frames = [
        f"{CE_ANIM} <b>Verifying your access...</b>",
        f"{CE_ANIM} <b>Checking membership .</b>",
        f"{CE_ANIM} <b>Checking membership ..</b>",
        f"{CE_ANIM} <b>Checking membership ...</b>",
        f"{CE_ANIM} <b>Almost done ...</b>",
    ]
    msg = await query.message.reply_text(frames[0], parse_mode="HTML")
    for frame in frames[1:]:
        await asyncio.sleep(0.7)
        try:
            await msg.edit_text(frame, parse_mode="HTML")
        except Exception:
            pass

    ch = verify_channel(d)
    verified = False
    if ch == 0:
        verified = True
    else:
        try:
            member = await ctx.bot.get_chat_member(chat_id=ch, user_id=uid)
            if member.status in ("member", "administrator", "creator", "restricted"):
                verified = True
        except Exception:
            verified = True

    return msg, verified

# ═══════════════════════════════════════════════════════════════════════════════
#  DELIVER PRODUCT
# ═══════════════════════════════════════════════════════════════════════════════
async def deliver_product(user_id: int, order: dict, ctx: ContextTypes.DEFAULT_TYPE, is_reseller: bool = False):
    k     = order["k"]
    i     = order["i"]
    dur   = order["dur"]
    price = order["price"]

    d   = load()
    cat = BASE_MENU.get(k)
    if not cat or i >= len(cat["products"]):
        return False
    if keys_count(k, i, dur, d) == 0:
        return False

    pname   = prod_name(k, i, d)
    key_val = pop_key(k, i, dur, d)
    file_val = pop_file(k, i, d) if files_count(k, i, d) > 0 else None
    sup     = support(d)

    label = "RESELLER PURCHASE" if is_reseller else "PURCHASE SUCCESSFUL!"
    await ctx.bot.send_message(
        chat_id=user_id,
        text=(
            f"━━━━━━━━━━━━━━━━\n"
            f"{CE_PURCH_OK} <b>{label}</b>\n\n"
            f"{CE_KEY_ICO} <b>Key:</b> <code>{esc(key_val)}</code>\n"
            f"{CE_DUR_ICO} <b>Duration:</b> {esc(dur)}\n"
            f"{CE_PRICE_ICO} <b>Price:</b> ${esc(price)}\n\n"
            f"{CE_IMPORT} <b>IMPORTANT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Don't share your key\n\n"
            f"Support: {sup}"
        ),
        parse_mode="HTML"
    )

    if file_val:
        ft, fv, fn = file_val.get("type", "link"), file_val.get("value", ""), file_val.get("name", "file")
        if ft == "document":
            await ctx.bot.send_document(chat_id=user_id, document=fv,
                                        caption=f"📁 <b>{esc(fn)}</b>", parse_mode="HTML")
        elif ft == "photo":
            await ctx.bot.send_photo(chat_id=user_id, photo=fv,
                                     caption=f"🖼 <b>{esc(fn)}</b>", parse_mode="HTML")
        else:
            await ctx.bot.send_message(chat_id=user_id,
                                       text=f"📁 <b>Download Link:</b>\n{esc(fv)}", parse_mode="HTML")
    else:
        await ctx.bot.send_message(chat_id=user_id,
                                   text=f"📁 <b>File coming soon.</b>\nContact admin: {sup}", parse_mode="HTML")

    d2 = load()
    all_admins = list(set([SUPER_ADMIN_ID] + HARDCODED_ADMINS + d2.get("admin_ids", [])))
    for aid in all_admins:
        try:
            await ctx.bot.send_message(
                chat_id=aid,
                text=(
                    f"🛒 <b>{'Reseller ' if is_reseller else ''}Purchase Delivered</b>\n\n"
                    f"User: <code>{user_id}</code>\n"
                    f"Product: {esc(pname)}\n"
                    f"Duration: {esc(dur)}\n"
                    f"Price: ${esc(price)}\n"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
    return True

# ═══════════════════════════════════════════════════════════════════════════════
#  DELIVER RESELLER PRODUCT
# ═══════════════════════════════════════════════════════════════════════════════
async def deliver_reseller_product(user_id: int, res_idx: int, dur: str, price: str,
                                   ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    d = load()
    if res_keys_count(res_idx, dur, d) == 0:
        return False

    p       = RESELLER_MENU[res_idx]
    key_val = res_pop_key(res_idx, dur, d)
    sup     = support(d)

    await ctx.bot.send_message(
        chat_id=user_id,
        text=(
            f"━━━━━━━━━━━━━━━━\n"
            f"{CE_PURCH_OK} <b>RESELLER PURCHASE</b>\n\n"
            f"{CE_KEY_ICO} <b>Key:</b> <code>{esc(key_val)}</code>\n"
            f"{CE_DUR_ICO} <b>Duration:</b> {esc(dur)}\n"
            f"{CE_PRICE_ICO} <b>Price:</b> ${esc(price)}\n\n"
            f"{CE_IMPORT} <b>IMPORTANT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Don't share your key\n\n"
            f"Support: {sup}"
        ),
        parse_mode="HTML"
    )

    d2 = load()
    all_admins = list(set([SUPER_ADMIN_ID] + HARDCODED_ADMINS + d2.get("admin_ids", [])))
    for aid in all_admins:
        try:
            await ctx.bot.send_message(
                chat_id=aid,
                text=(
                    f"🛒 <b>Reseller Purchase Delivered</b>\n\n"
                    f"User: <code>{user_id}</code>\n"
                    f"Product: {esc(p['name'])}\n"
                    f"Duration: {esc(dur)}\n"
                    f"Price: ${esc(price)}\n"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
    return True

# ═══════════════════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d    = load()
    uid  = update.effective_user.id
    name = esc(update.effective_user.first_name or "there")
    sn   = shop_name(d)

    # Clear any stuck state on /start
    clear_state(d, uid)

    if is_verified(uid, d):
        await update.message.reply_text(
            f"{CE_WELCOME} <b>Welcome back, {name}!</b>\n\n"
            f"{CE_SHOP} <b>{esc(sn)}</b>\n\n"
            f"Tap <b>Shop</b> to browse products.",
            parse_mode="HTML", reply_markup=kb_main(uid, d)
        )
    else:
        await update.message.reply_text(
            f"{CE_SHOP} <b>{esc(sn)}</b>\n\n"
            f"Hello, <b>{name}</b>!\n\n"
            f"Press the button below to verify your access and start shopping.",
            parse_mode="HTML", reply_markup=kb_verify()
        )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = load()
    await update.message.reply_text(
        f"<b>{esc(shop_name(d))} — Help</b>\n\n"
        "/start — Main menu (also clears stuck state)\n"
        "/help — This message\n\n"
        f"Support: {support(d)}",
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════════════════════
#  MEDIA HANDLER
# ═══════════════════════════════════════════════════════════════════════════════
async def handle_media(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d   = load()
    uid = update.effective_user.id

    if not is_verified(uid, d):
        await update.message.reply_text(
            "Please verify first. Use /start",
            reply_markup=kb_verify()
        )
        return

    state = get_state(d, uid)

    if state and state.startswith("add_file_item|") and is_admin(uid, d):
        parts = state.split("|", 2)
        if len(parts) != 3:
            await update.message.reply_text("State error. Use /start to reset.")
            return
        _, cat, idx_str = parts
        idx  = int(idx_str)
        slot = file_slot(cat, idx)
        d.setdefault("files", {}).setdefault(slot, [])

        if update.message.document:
            fobj      = update.message.document
            fname     = fobj.file_name or "file"
            file_item = {"type": "document", "value": fobj.file_id, "name": fname}
        elif update.message.photo:
            fobj      = update.message.photo[-1]
            file_item = {"type": "photo", "value": fobj.file_id, "name": "image"}
        else:
            await update.message.reply_text(
                "⚠️ Unsupported file type.\n"
                "Send a <b>file</b> (APK/IPA/ZIP/any) or use /start and send the link as text.",
                parse_mode="HTML"
            )
            return

        d["files"][slot].append(file_item)
        clear_state(d, uid)
        save(d)
        pname = prod_name(cat, idx, d)
        await update.message.reply_text(
            f"✅ <b>File Added!</b>\n\n"
            f"Product: <b>{esc(pname)}</b>\n"
            f"File: <b>{esc(file_item['name'])}</b>\n"
            f"Total in slot: <b>{len(d['files'][slot])}</b>",
            parse_mode="HTML"
        )
        return

    # ── Admin sets UPI QR image ────────────────────────────────────────────────
    if state == "cfg_set_upi" and is_admin(uid, d):
        if update.message.photo:
            fobj = update.message.photo[-1]
            d["config"]["upi_qr_file_id"] = fobj.file_id
            clear_state(d, uid); save(d)
            await update.message.reply_text("✅ <b>UPI QR image set!</b>", parse_mode="HTML")
        else:
            await update.message.reply_text("Please send a <b>photo</b> of the UPI QR code.", parse_mode="HTML")
        return

    # ── Admin sets Binance Pay image ───────────────────────────────────────────
    if state == "cfg_set_bnb_img" and is_admin(uid, d):
        if update.message.photo:
            fobj = update.message.photo[-1]
            d.setdefault("config", {})["binance_img_file_id"] = fobj.file_id
            d["config"]["binance_img_type"] = "photo"
            clear_state(d, uid); save(d)
            await update.message.reply_text("✅ Binance Pay image set!")
        elif update.message.document:
            fobj = update.message.document
            d.setdefault("config", {})["binance_img_file_id"] = fobj.file_id
            d["config"]["binance_img_type"] = "document"
            clear_state(d, uid); save(d)
            await update.message.reply_text("✅ Binance Pay image set!")
        else:
            await update.message.reply_text("Please send the Binance Pay image as a photo or file.")
        return

    # ── User sends payment screenshot (UPI) ────────────────────────────────────
    if state and state.startswith("awaiting_upi_ss|"):
        order_id = state.split("|", 1)[1]
        order    = d.get("pending_orders", {}).get(order_id)
        if not order:
            clear_state(d, uid)
            await update.message.reply_text(
                "⚠️ Order not found or expired. Please start a new purchase."
            )
            return
        if not (update.message.photo or update.message.document):
            await update.message.reply_text("📸 Please send your payment <b>screenshot as a photo</b>.", parse_mode="HTML")
            return
        clear_state(d, uid)
        pname = prod_name(order["k"], order["i"], d)
        await update.message.reply_text(
            f"✅ <b>Screenshot received!</b>\n\nYour order is pending admin approval.\n"
            f"Product: <b>{esc(pname)}</b> — {esc(order['dur'])}",
            parse_mode="HTML"
        )
        all_admins = list(set([SUPER_ADMIN_ID] + HARDCODED_ADMINS + d.get("admin_ids", [])))
        caption = (
            f"💳 <b>UPI Payment Proof</b>\n\n"
            f"User: <code>{uid}</code>\n"
            f"Product: {esc(pname)}\n"
            f"Duration: {esc(order['dur'])}\n"
            f"Amount: ${esc(order['price'])}\n"
            f"Order ID: <code>{order_id}</code>"
        )
        kb_ad = kb_approve_deny(order_id)
        for aid in all_admins:
            try:
                if update.message.photo:
                    await ctx.bot.send_photo(
                        chat_id=aid,
                        photo=update.message.photo[-1].file_id,
                        caption=caption, parse_mode="HTML",
                        reply_markup=kb_ad
                    )
                else:
                    await ctx.bot.send_document(
                        chat_id=aid,
                        document=update.message.document.file_id,
                        caption=caption, parse_mode="HTML",
                        reply_markup=kb_ad
                    )
            except Exception:
                pass
        return

    # ── User sends payment screenshot (Binance — waiting_ss flow) ──────────────
    if state and state.startswith("waiting_ss|"):
        parts = state.split("|", 5)
        if len(parts) != 6:
            await update.message.reply_text("Error in state. Please try again.")
            return
        _, wk, wsi, wdur, wprice, wmethod = parts
        wi = int(wsi)
        if not (update.message.photo or update.message.document):
            await update.message.reply_text(
                "📸 Please send a <b>screenshot</b> (photo) of your payment.", parse_mode="HTML"
            )
            return
        order_id = uuid.uuid4().hex[:12]
        d.setdefault("pending_orders", {})[order_id] = {
            "user_id": uid, "k": wk, "i": wi,
            "dur": wdur, "price": wprice, "method": wmethod
        }
        save(d)
        clear_state(d, uid)
        pname = prod_name(wk, wi, d)
        method_label = {"upi": "UPI", "bnb": "Binance", "other": "Other"}.get(wmethod, wmethod)
        user_info = (
            f"👤 User: <code>{uid}</code>\n"
            f"📦 Product: <b>{esc(pname)}</b>\n"
            f"⏱ Duration: <b>{esc(wdur)}</b>\n"
            f"💰 Price: <b>${esc(wprice)}</b>\n"
            f"💳 Method: <b>{method_label}</b>\n"
            f"🆔 Order ID: <code>{order_id}</code>"
        )
        approve_kb = kb_approve_deny(order_id)
        all_admins = list(set([SUPER_ADMIN_ID] + HARDCODED_ADMINS + d.get("admin_ids", [])))
        for aid in all_admins:
            try:
                if update.message.photo:
                    await ctx.bot.send_photo(
                        chat_id=aid,
                        photo=update.message.photo[-1].file_id,
                        caption=f"📸 <b>Payment Screenshot</b>\n\n{user_info}",
                        parse_mode="HTML", reply_markup=approve_kb
                    )
                else:
                    await ctx.bot.send_document(
                        chat_id=aid,
                        document=update.message.document.file_id,
                        caption=f"📸 <b>Payment Screenshot</b>\n\n{user_info}",
                        parse_mode="HTML", reply_markup=approve_kb
                    )
            except Exception as e:
                logger.warning(f"Could not notify admin {aid}: {e}")
        await update.message.reply_text(
            "✅ <b>Screenshot received!</b>\n\nYour payment is being reviewed. "
            "You will receive your product shortly after approval.",
            parse_mode="HTML"
        )
        return

    if not state:
        await update.message.reply_text("Use /start to open the main menu.")

# ═══════════════════════════════════════════════════════════════════════════════
#  TEXT HANDLER
# ═══════════════════════════════════════════════════════════════════════════════
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d    = load()
    uid  = update.effective_user.id
    text = (update.message.text or "").strip()

    if not is_verified(uid, d):
        await update.message.reply_text("Please verify first. Use /start", reply_markup=kb_verify())
        return

    state = get_state(d, uid)

    # Clear state on main menu buttons
    menu_buttons = ["Shop", "Account", "Stock", "Reseller", "Admin Panel"]
    if text in menu_buttons:
        if state:
            clear_state(d, uid)
        state = None

    # ── Awaiting payment screenshot but user sends text ────────────────────────
    if state and (state.startswith("waiting_ss|") or state.startswith("awaiting_upi_ss|")):
        await update.message.reply_text(
            "📸 Please send a <b>screenshot</b> (photo) of your payment to proceed.\n\n"
            "If you want to cancel this order, use /start",
            parse_mode="HTML"
        )
        return

    # ── Reseller login ─────────────────────────────────────────────────────────
    if state == "reseller_login_user":
        set_state(d, uid, f"reseller_login_pass|{text}")
        await update.message.reply_text(
            f"{CE_LOCK} <b>Enter Password:</b>",
            parse_mode="HTML"
        )
        return

    if state and state.startswith("reseller_login_pass|"):
        reseller_user = state.split("|", 1)[1]
        resellers     = d.get("resellers", {})
        if reseller_user in resellers and resellers[reseller_user].get("pass") == text:
            set_reseller_session(uid, reseller_user, d)
            clear_state(d, uid)
            msg = reseller_menu_msg(reseller_user, d)
            await update.message.reply_text(
                msg, parse_mode="HTML",
                reply_markup=kb_reseller_products(d)
            )
        else:
            clear_state(d, uid)
            await update.message.reply_text(
                f"{CE_DENY} <b>Invalid credentials.</b>\nTry again from the Reseller menu.",
                parse_mode="HTML"
            )
        return

    # ── Admin: add keys (BASE_MENU) ────────────────────────────────────────────
    if state and state.startswith("add_keys_item|") and is_admin(uid, d):
        parts = state.split("|", 4)
        if len(parts) != 4:
            await update.message.reply_text("State error. Use /start to reset.")
            return
        _, cat, idx_str, dur = parts
        idx  = int(idx_str)
        slot = key_slot(cat, idx, dur)
        d.setdefault("keys", {}).setdefault(slot, [])
        new_keys = [k.strip() for k in text.splitlines() if k.strip()]
        d["keys"][slot].extend(new_keys)
        clear_state(d, uid)
        save(d)
        pname = prod_name(cat, idx, d)
        await update.message.reply_text(
            f"✅ <b>{len(new_keys)} key(s) added!</b>\n\n"
            f"Product: <b>{esc(pname)}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\n"
            f"Total in slot: <b>{len(d['keys'][slot])}</b>",
            parse_mode="HTML"
        )
        return

    # ── Admin: add reseller keys ──────────────────────────────────────────────
    # FIX: was split("|", 3) checking len == 4 — state only has 3 parts
    if state and state.startswith("res_add_keys_item|") and is_admin(uid, d):
        parts = state.split("|", 2)
        if len(parts) != 3:
            await update.message.reply_text("State error. Use /start to reset.")
            return
        _, idx_str, dur = parts
        idx  = int(idx_str)
        slot = res_key_slot(idx, dur)
        d.setdefault("res_keys", {}).setdefault(slot, [])
        new_keys = [k.strip() for k in text.splitlines() if k.strip()]
        d["res_keys"][slot].extend(new_keys)
        clear_state(d, uid)
        save(d)
        p = RESELLER_MENU[idx]
        await update.message.reply_text(
            f"✅ <b>{len(new_keys)} reseller key(s) added!</b>\n\n"
            f"Product: <b>{esc(p['name'])}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\n"
            f"Total in slot: <b>{len(d['res_keys'][slot])}</b>",
            parse_mode="HTML"
        )
        return

    # ── Admin: add file link (IPA / ZIP / APK / any URL) ─────────────────────
    if state and state.startswith("add_file_item|") and is_admin(uid, d):
        parts = state.split("|", 2)
        if len(parts) != 3:
            await update.message.reply_text("State error.")
            return
        _, cat, idx_str = parts
        idx  = int(idx_str)
        slot = file_slot(cat, idx)
        d.setdefault("files", {}).setdefault(slot, [])
        file_item = {"type": "link", "value": text, "name": text[:80]}
        d["files"][slot].append(file_item)
        clear_state(d, uid)
        save(d)
        pname = prod_name(cat, idx, d)
        await update.message.reply_text(
            f"✅ <b>Link Added!</b>\nProduct: <b>{esc(pname)}</b>\n"
            f"Link: <code>{esc(text[:80])}</code>\n"
            f"Total in slot: <b>{len(d['files'][slot])}</b>",
            parse_mode="HTML"
        )
        return

    # ── Admin: broadcast ───────────────────────────────────────────────────────
    if state == "broadcast" and is_admin(uid, d):
        users = list(set(d.get("verified", []) + d.get("admin_ids", []) + [SUPER_ADMIN_ID]))
        clear_state(d, uid)
        sent = failed = 0
        for u in users:
            try:
                await ctx.bot.send_message(chat_id=u, text=text, parse_mode="HTML")
                sent += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.05)
        await update.message.reply_text(
            f"📢 <b>Broadcast sent!</b>\n\n✅ Delivered: <b>{sent}</b>\n❌ Failed: <b>{failed}</b>",
            parse_mode="HTML"
        )
        return

    # ── Admin: balance ─────────────────────────────────────────────────────────
    if state == "add_bal" and is_admin(uid, d):
        try:
            parts = text.split(); tid = int(parts[0]); amt = float(parts[1]); assert amt > 0
        except Exception:
            await update.message.reply_text("Send: <code>USER_ID AMOUNT</code>", parse_mode="HTML")
            return
        new = round(get_balance(tid, d) + amt, 2)
        d.setdefault("balances", {})[str(tid)] = new
        clear_state(d, uid); save(d)
        await update.message.reply_text(
            f"{CE_BAL_UPD} Balance updated.\nUser: <code>{tid}</code>\n"
            f"Added: <b>+${amt:.2f}</b>\nNew balance: <b>${new:.2f}</b>",
            parse_mode="HTML"
        )
        return

    if state == "ded_bal" and is_admin(uid, d):
        try:
            parts = text.split(); tid = int(parts[0]); amt = float(parts[1]); assert amt > 0
        except Exception:
            await update.message.reply_text("Send: <code>USER_ID AMOUNT</code>", parse_mode="HTML")
            return
        new = max(0.0, round(get_balance(tid, d) - amt, 2))
        d.setdefault("balances", {})[str(tid)] = new
        clear_state(d, uid); save(d)
        await update.message.reply_text(
            f"{CE_BAL_UPD} Balance updated.\nUser: <code>{tid}</code>\n"
            f"Deducted: <b>-${amt:.2f}</b>\nNew balance: <b>${new:.2f}</b>",
            parse_mode="HTML"
        )
        return

    if state == "chk_bal" and is_admin(uid, d):
        try:
            tid = int(text.strip())
        except ValueError:
            await update.message.reply_text("Send a valid numeric Telegram User ID.")
            return
        bal = get_balance(tid, d)
        clear_state(d, uid)
        await update.message.reply_text(
            f"User: <code>{tid}</code>\n{CE_WALLET} Balance: <b>${bal:.2f}</b>",
            parse_mode="HTML"
        )
        return

    if state == "admin_id" and is_admin(uid, d):
        try:
            new_id = int(text.strip())
        except ValueError:
            await update.message.reply_text("Send a valid numeric Telegram User ID.")
            return
        admins = d.setdefault("admin_ids", [])
        if new_id not in admins and new_id != SUPER_ADMIN_ID:
            admins.append(new_id)
        clear_state(d, uid); save(d)
        await update.message.reply_text(
            f"✅ <b>Admin added!</b>\nUser ID: <code>{new_id}</code>\n"
            f"<i>This admin cannot view raw key values unless granted by super admin.</i>",
            parse_mode="HTML"
        )
        return

    if state == "remove_admin_id" and is_super_admin(uid):
        try:
            target_id = int(text.strip())
        except ValueError:
            await update.message.reply_text("Send a valid numeric Telegram User ID.")
            return
        if target_id == SUPER_ADMIN_ID:
            await update.message.reply_text("❌ Cannot remove the super admin.")
            clear_state(d, uid)
            return
        admins = d.setdefault("admin_ids", [])
        if target_id in admins:
            admins.remove(target_id)
            d.setdefault("key_view_admins", [])
            if target_id in d["key_view_admins"]:
                d["key_view_admins"].remove(target_id)
            save(d)
            await update.message.reply_text(
                f"✅ <b>Admin removed!</b>\nUser ID: <code>{target_id}</code>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"❌ User <code>{target_id}</code> is not in the admin list.",
                parse_mode="HTML"
            )
        clear_state(d, uid)
        return

    if state == "grant_key_view" and is_super_admin(uid):
        try:
            target_id = int(text.strip())
        except ValueError:
            await update.message.reply_text("Send a valid numeric Telegram User ID.")
            return
        if target_id == SUPER_ADMIN_ID:
            await update.message.reply_text("Super admin already has full access.")
            clear_state(d, uid)
            return
        if not (target_id in d.get("admin_ids", []) or target_id in HARDCODED_ADMINS):
            await update.message.reply_text(
                f"❌ User <code>{target_id}</code> is not an admin yet.\n"
                f"Add them as admin first, then grant key-view access.",
                parse_mode="HTML"
            )
            clear_state(d, uid)
            return
        kva = d.setdefault("key_view_admins", [])
        if target_id not in kva:
            kva.append(target_id)
        clear_state(d, uid); save(d)
        await update.message.reply_text(
            f"{CE_KEY_LBL} <b>Key-view access granted!</b>\nAdmin: <code>{target_id}</code>",
            parse_mode="HTML"
        )
        return

    if state == "revoke_key_view" and is_super_admin(uid):
        try:
            target_id = int(text.strip())
        except ValueError:
            await update.message.reply_text("Send a valid numeric Telegram User ID.")
            return
        kva = d.setdefault("key_view_admins", [])
        if target_id in kva:
            kva.remove(target_id)
            save(d)
            await update.message.reply_text(
                f"✅ Key-view access <b>revoked</b> for: <code>{target_id}</code>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"User <code>{target_id}</code> didn't have key-view access.",
                parse_mode="HTML"
            )
        clear_state(d, uid)
        return

    # ── Settings states ────────────────────────────────────────────────────────
    if state == "cfg_shop_name" and is_admin(uid, d):
        d["config"]["shop_name"] = text
        clear_state(d, uid); save(d)
        await update.message.reply_text(f"✅ Shop name updated to: <b>{esc(text)}</b>", parse_mode="HTML")
        return

    if state == "cfg_support" and is_admin(uid, d):
        d["config"]["support"] = text
        clear_state(d, uid); save(d)
        await update.message.reply_text(f"✅ Support updated to: <code>{esc(text)}</code>", parse_mode="HTML")
        return

    if state == "cfg_set_bnb" and is_admin(uid, d):
        d.setdefault("config", {})["binance_id"] = text.strip()
        clear_state(d, uid); save(d)
        await update.message.reply_text(
            f"₿ <b>Binance ID set!</b>\nID: <code>{esc(text.strip())}</code>",
            parse_mode="HTML"
        )
        return

    if state and state.startswith("cfg_price|") and is_admin(uid, d):
        _, k, idx_str, dur = state.split("|", 3)
        idx = int(idx_str)
        try:
            price_f = float(text.strip().replace("$", ""))
            assert price_f > 0
        except Exception:
            await update.message.reply_text("Send a valid price (e.g. <code>12.00</code>).", parse_mode="HTML")
            return
        new_price = f"{price_f:.2f}"
        set_price(k, idx, dur, new_price, d)
        clear_state(d, uid)
        pname = prod_name(k, idx, d)
        await update.message.reply_text(
            f"✅ Price updated!\n<b>{esc(pname)}</b> — {esc(dur)}: <b>${new_price}</b>",
            parse_mode="HTML"
        )
        return

    if state and state.startswith("cfg_rprice|") and is_admin(uid, d):
        _, idx_str, dur = state.split("|", 2)
        idx = int(idx_str)
        try:
            price_f = float(text.strip().replace("$", ""))
            assert price_f > 0
        except Exception:
            await update.message.reply_text("Send a valid price (e.g. <code>5.00</code>).", parse_mode="HTML")
            return
        new_price = f"{price_f:.2f}"
        set_reseller_price(idx, dur, new_price, d)
        clear_state(d, uid)
        await update.message.reply_text(
            f"✅ Reseller price updated!\n<b>{esc(RESELLER_MENU[idx]['name'])}</b> — {esc(dur)}: <b>${new_price}</b>",
            parse_mode="HTML"
        )
        return

    # ── Reseller mgmt states ───────────────────────────────────────────────────
    if state == "adm_res_add" and is_admin(uid, d):
        try:
            parts    = text.split()
            res_user = parts[0]
            res_pass = parts[1]
        except IndexError:
            await update.message.reply_text("Send: <code>USERNAME PASSWORD</code>", parse_mode="HTML")
            return
        d.setdefault("resellers", {})[res_user] = {"pass": res_pass, "balance": 0.0}
        clear_state(d, uid); save(d)
        await update.message.reply_text(
            f"✅ Reseller <b>{esc(res_user)}</b> created.",
            parse_mode="HTML"
        )
        return

    if state == "adm_res_bal" and is_admin(uid, d):
        try:
            parts    = text.split()
            res_user = parts[0]
            amt      = float(parts[1])
            assert amt > 0
        except Exception:
            await update.message.reply_text("Send: <code>USERNAME AMOUNT</code>", parse_mode="HTML")
            return
        if res_user not in d.get("resellers", {}):
            await update.message.reply_text(f"Reseller <code>{esc(res_user)}</code> not found.", parse_mode="HTML")
            return
        new = round(get_reseller_balance(res_user, d) + amt, 2)
        set_reseller_balance(res_user, new, d)
        clear_state(d, uid)
        await update.message.reply_text(
            f"✅ Added <b>${amt:.2f}</b> to <b>{esc(res_user)}</b>.\nNew balance: <b>${new:.2f}</b>",
            parse_mode="HTML"
        )
        return

    if state == "adm_res_del" and is_admin(uid, d):
        res_user = text.strip()
        if res_user in d.get("resellers", {}):
            del d["resellers"][res_user]
            save(d)
            await update.message.reply_text(f"✅ Reseller <b>{esc(res_user)}</b> deleted.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"Reseller <code>{esc(res_user)}</code> not found.", parse_mode="HTML")
        clear_state(d, uid)
        return

    # ── Menu buttons ──────────────────────────────────────────────────────────
    if text == "Shop":
        kb_cats = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                BASE_MENU[k]['label'],
                callback_data=f"cat|{k}"
            )]
            for k in CAT_ORDER
        ])
        await update.message.reply_text(
            f"{CE_SHOP} <b>Select a category:</b>",
            parse_mode="HTML", reply_markup=kb_cats
        )
        return

    if text == "Account":
        bal   = get_balance(uid, d)
        role  = "Super Admin" if is_super_admin(uid) else ("Admin" if is_admin(uid, d) else "User")
        uname = update.effective_user.username or "N/A"
        await update.message.reply_text(
            f"{CE_ACCT} <b>Account Info</b>\n\n"
            f"Name: {esc(update.effective_user.full_name or 'N/A')}\n"
            f"Username: @{esc(uname)}\n"
            f"ID: <code>{uid}</code>\n"
            f"Role: <b>{role}</b>\n"
            f"{CE_BAL_ICON} Balance: <b>${bal:.2f}</b>\n"
            f"Status: Verified {CE_VERIFIED}",
            parse_mode="HTML"
        )
        return

    if text == "Stock":
        d2    = load()
        lines = [f"{CE_STOCK_HDR} <b>{esc(shop_name(d2))} — Stock</b>\n"]
        for k in CAT_ORDER:
            cat = BASE_MENU[k]
            lines.append(f"<b>{esc(cat['label'])}</b>")
            for i, p in enumerate(cat["products"]):
                pname = prod_name(k, i, d2)
                total = sum(keys_count(k, i, dur, d2) for dur, _ in prod_prices(k, i, d2))
                dot   = CE_AVAIL if total > 0 else CE_UNAVAIL
                lines.append(f"  {dot} {esc(pname)} — <b>{total} keys</b>")
            lines.append("")
        await send_long(update.message, "\n".join(lines), parse_mode="HTML")
        return

    if text == "Reseller":
        res_user = get_reseller_session(uid, d)
        if res_user and res_user in d.get("resellers", {}):
            msg = reseller_menu_msg(res_user, d)
            await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb_reseller_products(d))
        else:
            set_state(d, uid, "reseller_login_user")
            await update.message.reply_text(
                f"{CE_RES_LOGIN} <b>Reseller Login</b>\n\nEnter your username:",
                parse_mode="HTML"
            )
        return

    if text == "Admin Panel":
        if not is_admin(uid, d):
            await update.message.reply_text("Admins only.")
            return
        await update.message.reply_text(
            f"{CE_ADMIN} <b>Admin Panel — {esc(shop_name(d))}</b>\n\nChoose an action:",
            parse_mode="HTML", reply_markup=kb_admin_panel(uid, d)
        )
        return


# ═══════════════════════════════════════════════════════════════════════════════
#  SETTINGS HANDLER
# ═══════════════════════════════════════════════════════════════════════════════
async def _handle_cfg(action: str, q, uid: int, d: dict):
    async def reply(text: str, kb=None):
        kwargs = {"parse_mode": "HTML"}
        if kb:
            kwargs["reply_markup"] = kb
        await q.message.reply_text(text, **kwargs)

    if action == "menu":
        sn = shop_name(d)
        bnb_id     = cfg(d, "binance_id", "")
        upi_set    = "✅ Set" if cfg(d, "upi_qr_file_id", "") else "❌ Not set"
        bnb_img    = "✅ Set" if cfg(d, "binance_img_file_id", "") else "❌ Not set"
        bnb_status = f"✅ <code>{esc(bnb_id)}</code>" if bnb_id else "❌ Not set"
        await reply(
            f"<b>{CE_SETTINGS} Settings — {esc(sn)}</b>\n\n"
            f"🏪 Shop Name: <b>{esc(sn)}</b>\n"
            f"📞 Support: <code>{esc(support(d))}</code>\n"
            f"🏦 UPI QR: {upi_set}\n"
            f"₿ Binance ID: {bnb_status}\n"
            f"🖼 Binance Image: {bnb_img}\n\n"
            f"Choose what to edit:",
            kb_settings()
        )
        return

    if action == "shop_name":
        set_state(d, uid, "cfg_shop_name")
        await reply(
            f"🏪 <b>Edit Shop Name</b>\n\nCurrent: <b>{esc(shop_name(d))}</b>\n\nSend the new shop name:",
            kb_cancel()
        )
        return

    if action == "support":
        set_state(d, uid, "cfg_support")
        await reply(
            f"📞 <b>Edit Support</b>\n\nCurrent: <code>{esc(support(d))}</code>\n\nSend the new support (e.g. @user):",
            kb_cancel()
        )
        return

    if action == "prices_menu":
        await reply("📦 <b>Edit Product Prices</b>\n\nSelect a product:", kb_cfg_prices_cats(d))
        return

    if action.startswith("pp|"):
        _, k, idx_str = action.split("|", 2)
        idx   = int(idx_str)
        pname = prod_name(k, idx, d)
        await reply(f"💰 <b>Edit Prices — {esc(pname)}</b>\n\nSelect a duration:", kb_cfg_prices_durs(k, idx, d))
        return

    if action.startswith("ppd|"):
        parts   = action.split("|")
        k       = parts[1]
        idx     = int(parts[2])
        dur_enc = parts[3]
        dur     = dec_dur(dur_enc)
        pname   = prod_name(k, idx, d)
        current = dict(prod_prices(k, idx, d)).get(dur, "?")
        set_state(d, uid, f"cfg_price|{k}|{idx}|{dur}")
        await reply(
            f"💰 <b>Edit Price</b>\n\nProduct: <b>{esc(pname)}</b>\nDuration: <b>{esc(dur)}</b>\n"
            f"Current: <b>${current}</b>\n\nSend the new price (e.g. <code>12.00</code>):",
            kb_cancel()
        )
        return

    if action == "rprices_menu":
        await reply(f"{CE_RESELLER} <b>Edit Reseller Prices</b>\n\nSelect a product:", kb_cfg_rprices(d))
        return

    if action.startswith("rpp|"):
        idx = int(action.split("|")[1])
        p   = RESELLER_MENU[idx]
        await reply(f"{CE_RESELLER} <b>Reseller Prices — {esc(p['name'])}</b>\n\nSelect a duration:",
                    kb_cfg_rprices_durs(idx, d))
        return

    if action.startswith("rppd|"):
        parts   = action.split("|")
        idx     = int(parts[1])
        dur_enc = parts[2]
        dur     = dec_dur(dur_enc)
        p       = RESELLER_MENU[idx]
        current = dict(reseller_prod_prices(idx, d)).get(dur, "?")
        set_state(d, uid, f"cfg_rprice|{idx}|{dur}")
        await reply(
            f"{CE_RESELLER} <b>Edit Reseller Price</b>\n\nProduct: <b>{esc(p['name'])}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\nCurrent: <b>${current}</b>\n\n"
            f"Send the new price (e.g. <code>6.00</code>):",
            kb_cancel()
        )
        return

    if action == "set_upi":
        upi_qr = cfg(d, "upi_qr_file_id", "")
        status = "✅ Set" if upi_qr else "❌ Not set"
        set_state(d, uid, "cfg_set_upi")
        await reply(
            f"🏦 <b>Set UPI QR Image</b>\n\nCurrent: <b>{status}</b>\n\n"
            f"Send the UPI QR code as a <b>photo</b>:",
            kb_cancel()
        )
        return

    if action == "set_bnb":
        current_id = cfg(d, "binance_id", "")
        status     = f"<code>{esc(current_id)}</code>" if current_id else "❌ Not set"
        set_state(d, uid, "cfg_set_bnb")
        await reply(
            f"₿ <b>Set Binance ID</b>\n\nCurrent: {status}\n\n"
            f"Send your Binance Pay ID or UID (numbers only, e.g. <code>865770026</code>):",
            kb_cancel()
        )
        return

    if action == "set_bnb_img":
        bnb_img = cfg(d, "binance_img_file_id", "")
        status  = "✅ Set" if bnb_img else "❌ Not set"
        set_state(d, uid, "cfg_set_bnb_img")
        await reply(
            f"🖼 <b>Set Binance Pay Image</b>\n\nCurrent: <b>{status}</b>\n\n"
            f"Send the Binance payment instruction image as a <b>photo</b>.\n"
            f"<i>(This image is shown to buyers when they choose Binance Pay.)</i>",
            kb_cancel()
        )
        return

# ═══════════════════════════════════════════════════════════════════════════════
#  CALLBACK HANDLER
# ═══════════════════════════════════════════════════════════════════════════════
async def handle_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    await q.answer()
    d   = load()
    uid = q.from_user.id
    cb  = q.data
    try:
        await _handle_cb_inner(q, uid, cb, d, ctx)
    except Exception as e:
        logger.error(f"handle_cb error [{cb}]: {e}", exc_info=e)
        try:
            await q.message.reply_text(
                f"⚠️ Something went wrong processing your request.\n"
                f"Use /start to return to the main menu.\n"
                f"If this keeps happening, contact: {d.get('config', {}).get('support', '@support')}"
            )
        except Exception:
            pass

async def _handle_cb_inner(q, uid: int, cb: str, d: dict, ctx: ContextTypes.DEFAULT_TYPE):

    # ── Verify ────────────────────────────────────────────────────────────────
    if cb == "verify":
        msg, ok = await run_verify(q, uid, ctx, d)
        if ok:
            if uid not in d.get("verified", []):
                d.setdefault("verified", []).append(uid)
                save(d)
            name = esc(q.from_user.first_name or "there")
            try:
                await msg.edit_text(
                    f"<b>Access Granted!</b>\n\nWelcome, <b>{name}</b>! ✅",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            await q.message.reply_text(
                f"{CE_WELCOME} <b>Welcome, {name}!</b>\n\n"
                f"{CE_SHOP} <b>{esc(shop_name(d))}</b>\n\n"
                f"Tap <b>Shop</b> to browse products.",
                parse_mode="HTML", reply_markup=kb_main(uid, d)
            )
        else:
            try:
                await msg.edit_text(
                    f"<b>Verification Failed</b>\n\nJoin our channel first, then tap /start.",
                    parse_mode="HTML"
                )
            except Exception:
                await q.message.reply_text(
                    "❌ <b>Verification Failed.</b>\nJoin our channel first, then use /start.",
                    parse_mode="HTML"
                )
        return

    if not is_verified(uid, d):
        await q.message.reply_text(
            "Please verify first. Use /start",
            reply_markup=kb_verify()
        )
        return

    # ── Approve order ─────────────────────────────────────────────────────────
    if cb.startswith("approve|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        order_id = cb[8:]
        order    = d.get("pending_orders", {}).get(order_id)
        if not order:
            try:
                await q.edit_message_caption(
                    caption="⚠️ Order already processed or not found.",
                    reply_markup=None
                )
            except Exception:
                try: await q.edit_message_text("⚠️ Order already processed or not found.", reply_markup=None)
                except Exception: pass
            return
        success = await deliver_product(order["user_id"], order, ctx)
        d2      = load()
        d2.get("pending_orders", {}).pop(order_id, None)
        save(d2)
        result_line = "✅ Approved — product delivered!" if success else "❌ No stock — could not deliver. Add keys first!"
        try:
            await q.edit_message_caption(
                caption=(q.message.caption or "") + f"\n\n{result_line}",
                reply_markup=None
            )
        except Exception:
            try: await q.edit_message_text(result_line, reply_markup=None)
            except Exception: await q.message.reply_text(result_line)
        return

    # ── Deny order ────────────────────────────────────────────────────────────
    if cb.startswith("deny|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        order_id = cb[5:]
        order    = d.get("pending_orders", {}).get(order_id)
        if not order:
            try: await q.edit_message_text("⚠️ Order already processed or not found.", reply_markup=None)
            except Exception: pass
            return
        d.get("pending_orders", {}).pop(order_id, None)
        save(d)
        result_line = "❌ Order denied."
        try:
            await q.edit_message_caption(
                caption=(q.message.caption or "") + f"\n\n{result_line}",
                reply_markup=None
            )
        except Exception:
            try: await q.edit_message_text(result_line, reply_markup=None)
            except Exception: await q.message.reply_text(result_line)
        try:
            await ctx.bot.send_message(
                chat_id=order["user_id"],
                text=f"{CE_DENY} <b>Order Denied.</b>\nContact admin: {support(d)}",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    # ── Shop browsing ─────────────────────────────────────────────────────────
    if cb.startswith("cat|"):
        k   = cb[4:]
        cat = BASE_MENU.get(k)
        if not cat: return
        txt = cat_msg(k, d)
        try:
            await q.edit_message_text(txt, parse_mode="HTML", reply_markup=kb_cat(k, d))
        except Exception:
            await q.message.reply_text(txt, parse_mode="HTML", reply_markup=kb_cat(k, d))
        return

    if cb.startswith("prod|"):
        _, k, si = cb.split("|"); i = int(si)
        cat = BASE_MENU.get(k)
        if not cat or i >= len(cat["products"]): return
        pname = prod_name(k, i, d)
        total = total_product_stock(k, i, d)
        txt   = (
            f"{cat['products'][i]['ce']} <b>{esc(pname)}</b>\n\n"
            f"{CE_STATUS_ICO} Status: Good &amp; Safe\n"
            f"{CE_STOCK_ICO} In stock: <b>{total}</b>\n\n"
            f"{CE_DUR_ICO} <b>Select a duration:</b>"
        )
        try:
            await q.edit_message_text(txt, parse_mode="HTML", reply_markup=kb_durations(k, i, d))
        except Exception:
            await q.message.reply_text(txt, parse_mode="HTML", reply_markup=kb_durations(k, i, d))
        return

    if cb.startswith("dur|"):
        parts = cb.split("|", 4)
        _, k, si, dur_enc, price = parts; i = int(si)
        dur = dec_dur(dur_enc)
        cat = BASE_MENU.get(k)
        if not cat or i >= len(cat["products"]): return
        pname = prod_name(k, i, d)
        qty   = slot_stock(k, i, dur, d)
        bal   = get_balance(uid, d)
        _ce = cat['products'][i]['ce']

        binance_id = cfg(d, "binance_id", "")
        upi_qr     = cfg(d, "upi_qr_file_id", "")
        has_alt_pay = bool(binance_id or upi_qr)

        if qty == 0:
            txt = (
                f"{_ce} <b>{esc(pname)}</b>\n"
                f"{CE_DUR_ICO} Duration: <b>{esc(dur)}</b>  |  {CE_PRICE_ICO} Price: <b>${esc(price)}</b>\n\n"
                f"❌ <b>Out of stock.</b> Contact admin: {support(d)}"
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️  Back", callback_data=f"prod|{k}|{i}")]])
        elif bal < float(price) and not has_alt_pay:
            txt = (
                f"{_ce} <b>{esc(pname)}</b>\n"
                f"{CE_DUR_ICO} Duration: <b>{esc(dur)}</b>  |  {CE_PRICE_ICO} Price: <b>${esc(price)}</b>\n"
                f"{CE_BAL_ICON} Your balance: <b>${bal:.2f}</b>\n\n"
                f"⚠️ <b>Insufficient balance.</b>\nContact admin to top up: {support(d)}"
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️  Back", callback_data=f"prod|{k}|{i}")]])
        else:
            if bal < float(price) and has_alt_pay:
                note = f"\n⚠️ Balance low — pay via Binance/UPI below"
            else:
                note = ""
            txt = (
                f"{_ce} <b>{esc(pname)}</b>\n"
                f"{CE_DUR_ICO} Duration: <b>{esc(dur)}</b>  |  {CE_PRICE_ICO} Price: <b>${esc(price)}</b>\n"
                f"{CE_STOCK_ICO} In stock: <b>{qty}</b>\n"
                f"{CE_BAL_ICON} Your balance: <b>${bal:.2f}</b>{note}\n\n"
                f"Choose payment method:"
            )
            kb = kb_buy_methods(k, i, dur_enc, price, d)
        try:
            await q.edit_message_text(txt, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await q.message.reply_text(txt, parse_mode="HTML", reply_markup=kb)
        return

    if cb.startswith("pay|"):
        parts  = cb.split("|", 5)
        method = parts[1]
        k, si, dur_enc, price = parts[2], parts[3], parts[4], parts[5]
        i = int(si)
        dur = dec_dur(dur_enc)
        cat = BASE_MENU.get(k)
        if not cat or i >= len(cat["products"]): return
        pname = prod_name(k, i, d)

        if method == "bal":
            try:
                price_f = float(price)
            except ValueError:
                await q.message.reply_text("⚠️ Invalid price. Contact admin.")
                return
            bal = get_balance(uid, d)
            if bal < price_f:
                await q.message.reply_text(
                    f"💰 <b>Insufficient Balance</b>\n\n"
                    f"Required: <b>${price_f:.2f}</b>\n"
                    f"Your balance: <b>${bal:.2f}</b>\n\n"
                    f"Contact admin to top up: {support(d)}",
                    parse_mode="HTML"
                )
                return
            if slot_stock(k, i, dur, d) == 0:
                await q.message.reply_text(
                    f"❌ <b>Out of Stock</b>\n\nContact admin: {support(d)}",
                    parse_mode="HTML"
                )
                return
            d["balances"][str(uid)] = round(bal - price_f, 2)
            save(d)
            order   = {"k": k, "i": i, "dur": dur, "price": price, "method": "bal", "user_id": uid}
            success = await deliver_product(uid, order, ctx)
            if success:
                try:
                    await q.edit_message_text(
                        f"{CE_SUCCESS} <b>Purchase Successful!</b>\n\n"
                        f"${price_f:.2f} deducted. Remaining: <b>${d['balances'][str(uid)]:.2f}</b>",
                        parse_mode="HTML")
                except Exception: pass
            else:
                d2 = load()
                d2["balances"][str(uid)] = round(get_balance(uid, d2) + price_f, 2)
                save(d2)
                await q.message.reply_text(
                    f"❌ <b>Out of Stock</b>\n\nNo keys available. Your balance has been <b>refunded</b>.\n"
                    f"Contact admin: {support(d)}",
                    parse_mode="HTML"
                )
            return

        if method == "upi":
            upi_qr = cfg(d, "upi_qr_file_id", "")
            if not upi_qr:
                await q.message.reply_text(
                    f"🏦 <b>UPI Not Configured</b>\n\n"
                    f"The admin has not set up UPI payments yet.\n"
                    f"Contact admin: {support(d)}",
                    parse_mode="HTML"
                )
                return
            # Cancel any previous pending order for this user
            _cancel_user_pending(uid, d)
            order_id = str(uuid.uuid4())[:8]
            d.setdefault("pending_orders", {})[order_id] = {
                "user_id": uid, "k": k, "i": i, "dur": dur, "price": price, "method": "upi"
            }
            save(d)
            set_state(d, uid, f"awaiting_upi_ss|{order_id}")
            try:
                await q.message.reply_photo(
                    photo=upi_qr,
                    caption=(
                        f"{CE_UPI_ICO} <b>UPI Payment</b>\n\n"
                        f"Product: <b>{esc(pname)}</b>\n"
                        f"Duration: <b>{esc(dur)}</b>\n"
                        f"Amount: <b>${esc(price)}</b>\n\n"
                        f"Pay the amount via UPI and send your <b>payment screenshot (photo)</b> here.\n"
                        f"Order ID: <code>{order_id}</code>"
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                await q.message.reply_text(
                    f"{CE_UPI_ICO} <b>UPI Payment</b>\n\nAmount: <b>${esc(price)}</b>\n\n"
                    f"Pay and send your <b>payment screenshot (photo)</b> here.\n"
                    f"Order ID: <code>{order_id}</code>",
                    parse_mode="HTML"
                )
            return

        if method == "bnb":
            bnb_id = cfg(d, "binance_id", "")
            if not bnb_id:
                await q.message.reply_text(
                    f"🔶 Binance Pay not configured yet.\n"
                    f"Contact admin: {support(d)}"
                )
                return
            if slot_stock(k, i, dur, d) == 0:
                await q.message.reply_text(
                    f"❌ Out of stock for {pname} — {dur}.\n"
                    f"Contact admin: {support(d)}"
                )
                return

            order_text = (
                f"<b>Order:</b> {esc(pname)}\n"
                f"<b>Duration:</b> {esc(dur)}\n"
                f"<b>Amount:</b> <b>${esc(price)}</b>"
            )
            caption = (
                f"🔶 <b>Pay via Binance</b>\n\n{order_text}\n\n"
                f"Send <b>${esc(price)} USDT</b> to:\n"
                f"<b>Binance ID:</b> <code>{esc(bnb_id)}</code>\n\n"
                f"After sending, click the button below."
            )
            kb_bnb = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "✅  I've Sent Payment",
                    callback_data=f"paid|{k}|{i}|{dur}|{price}|bnb"
                )
            ]])

            img = find_image(BINANCE_QR_PATHS)
            if img:
                await q.message.reply_photo(
                    photo=open(img, "rb"),
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb_bnb
                )
            else:
                await q.message.reply_text(caption, parse_mode="HTML", reply_markup=kb_bnb)
            return

    # ── User clicked "I've Sent Payment" (Binance) ────────────────────────────
    if cb.startswith("paid|"):
        parts = cb.split("|", 5)
        if len(parts) != 6:
            await q.answer("Invalid data.", show_alert=True)
            return
        _, pk, psi, pdur, pprice, pmethod = parts
        set_state(d, uid, f"waiting_ss|{pk}|{psi}|{pdur}|{pprice}|{pmethod}")
        try:
            await q.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await q.message.reply_text(
            "📸 Please send a <b>screenshot</b> (photo) of your payment.\n\n"
            "An admin will review and approve your order.",
            parse_mode="HTML"
        )
        return

    # ── Reseller flow ──────────────────────────────────────────────────────────
    if cb == "res_menu":
        res_user = get_reseller_session(uid, d)
        if not res_user or res_user not in d.get("resellers", {}):
            await q.message.reply_text("⚠️ Not logged in. Tap Reseller to log in again.")
            return
        msg = reseller_menu_msg(res_user, d)
        try:
            await q.edit_message_text(msg, parse_mode="HTML", reply_markup=kb_reseller_products(d))
        except Exception:
            await q.message.reply_text(msg, parse_mode="HTML", reply_markup=kb_reseller_products(d))
        return

    if cb == "res_balance":
        res_user = get_reseller_session(uid, d)
        if not res_user:
            await q.message.reply_text("⚠️ Not logged in. Tap Reseller to log in again.")
            return
        bal = get_reseller_balance(res_user, d)
        txt = (
            f"{CE_WALLET} <b>Reseller Balance</b>\n\n"
            f"Account: <b>{esc(res_user)}</b>\n"
            f"Balance: <b>${bal:.2f}</b>\n\n"
            f"Contact admin to top up your balance."
        )
        try:
            await q.edit_message_text(
                txt, parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️  Back", callback_data="res_menu")]
                ])
            )
        except Exception:
            await q.message.reply_text(
                txt, parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️  Back", callback_data="res_menu")]
                ])
            )
        return

    if cb == "res_logout":
        clear_reseller_session(uid, d)
        try:
            await q.edit_message_text(f"{CE_LOCK} Logged out of reseller panel.")
        except Exception:
            await q.message.reply_text(f"{CE_LOCK} Logged out.")
        return

    if cb.startswith("res_prod|"):
        res_user = get_reseller_session(uid, d)
        if not res_user:
            await q.message.reply_text("⚠️ Not logged in. Tap Reseller to log in again.")
            return
        idx = int(cb.split("|")[1])
        p   = RESELLER_MENU[idx]
        txt = (
            f"<b>{esc(p['name'])}</b>\n\n"
            f"{CE_WALLET} Your balance: <b>${get_reseller_balance(res_user, d):.2f}</b>\n\n"
            f"<b>Select a duration:</b>"
        )
        try:
            await q.edit_message_text(txt, parse_mode="HTML", reply_markup=kb_reseller_durs(idx, d))
        except Exception:
            await q.message.reply_text(txt, parse_mode="HTML", reply_markup=kb_reseller_durs(idx, d))
        return

    if cb.startswith("res_dur|"):
        res_user = get_reseller_session(uid, d)
        if not res_user:
            await q.message.reply_text("⚠️ Not logged in. Tap Reseller to log in again.")
            return
        parts   = cb.split("|")
        idx     = int(parts[1])
        dur_enc = parts[2]
        price   = parts[3]
        dur     = dec_dur(dur_enc)
        p       = RESELLER_MENU[idx]
        bal     = get_reseller_balance(res_user, d)
        qty     = res_keys_count(idx, dur, d)
        txt = (
            f"<b>{esc(p['name'])}</b>\n"
            f"Duration: <b>{esc(dur)}</b>  |  Price: <b>${esc(price)}</b>\n"
            f"{CE_STOCK_ICO} In stock: <b>{qty}</b>\n"
            f"{CE_WALLET} Your balance: <b>${bal:.2f}</b>"
        )
        try:
            await q.edit_message_text(txt, parse_mode="HTML", reply_markup=kb_reseller_buy(idx, dur_enc, price))
        except Exception:
            await q.message.reply_text(txt, parse_mode="HTML", reply_markup=kb_reseller_buy(idx, dur_enc, price))
        return

    if cb.startswith("res_buy|"):
        res_user = get_reseller_session(uid, d)
        if not res_user:
            await q.message.reply_text("⚠️ Not logged in. Tap Reseller to log in again.")
            return
        parts   = cb.split("|")
        idx     = int(parts[1])
        dur_enc = parts[2]
        price   = parts[3]
        dur     = dec_dur(dur_enc)
        p       = RESELLER_MENU[idx]

        try:
            price_f = float(price)
        except ValueError:
            await q.message.reply_text("⚠️ Invalid price. Contact admin.")
            return

        bal = get_reseller_balance(res_user, d)
        if bal < price_f:
            await q.message.reply_text(
                f"💰 <b>Insufficient Balance</b>\n\n"
                f"Required: <b>${price_f:.2f}</b>\n"
                f"Your balance: <b>${bal:.2f}</b>\n\n"
                f"Contact admin to top up.",
                parse_mode="HTML"
            )
            return

        if res_keys_count(idx, dur, d) == 0:
            await q.message.reply_text(
                f"❌ <b>Out of Stock</b>\n\n"
                f"<b>{esc(p['name'])}</b> — {esc(dur)} is currently out of stock.\n"
                f"Contact admin: {support(d)}",
                parse_mode="HTML"
            )
            return

        success = await deliver_reseller_product(uid, idx, dur, price, ctx)
        if success:
            d2      = load()
            new_bal = round(get_reseller_balance(res_user, d2) - price_f, 2)
            set_reseller_balance(res_user, new_bal, d2)
            try:
                await q.edit_message_text(
                    f"{CE_SUCCESS} <b>Reseller Purchase Done!</b>\n\n"
                    f"Product: <b>{esc(p['name'])}</b>\n"
                    f"Duration: <b>{esc(dur)}</b>\n"
                    f"Cost: <b>${price_f:.2f}</b>\n"
                    f"Remaining balance: <b>${new_bal:.2f}</b>\n\n"
                    f"Key sent above ↑",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️  Back to Menu", callback_data="res_menu")]
                    ])
                )
            except Exception:
                pass
        else:
            await q.message.reply_text(
                f"❌ <b>Out of Stock</b>\n\n"
                f"No keys for <b>{esc(p['name'])}</b> — {esc(dur)}.\n"
                f"<b>No balance was deducted.</b>\n"
                f"Contact admin: {support(d)}",
                parse_mode="HTML"
            )
        return

    # ── Reseller admin: add reseller keys ─────────────────────────────────────
    if cb.startswith("rakp|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        idx = int(cb.split("|")[1])
        p   = RESELLER_MENU[idx]
        await q.message.reply_text(
            f"{CE_ADDKEYS} <b>Add Reseller Keys — {esc(p['name'])}</b>\n\nSelect a duration:",
            parse_mode="HTML", reply_markup=kb_res_add_keys_durs(idx, d)
        )
        return

    if cb.startswith("rakd|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        parts   = cb.split("|"); idx = int(parts[1]); dur_enc = parts[2]
        dur     = dec_dur(dur_enc)
        p       = RESELLER_MENU[idx]
        existing = res_keys_count(idx, dur, d)
        set_state(d, uid, f"res_add_keys_item|{idx}|{dur}")
        await q.edit_message_text(
            f"🔑 <b>Add Reseller Keys</b>\n\n"
            f"Product: <b>{esc(p['name'])}</b>\nDuration: <b>{esc(dur)}</b>\n"
            f"Current stock: <b>{existing}</b>\n\nSend keys — <b>one per line</b>:",
            parse_mode="HTML"
        )
        return

    # ── Settings ──────────────────────────────────────────────────────────────
    if cb.startswith("cfg|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        action = cb[4:]
        try:
            await _handle_cfg(action, q, uid, d)
        except Exception as e:
            logger.error(f"Settings error: {e}", exc_info=e)
        return

    # ── Admin: file/key ops ───────────────────────────────────────────────────
    if cb.startswith("afc|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        cat_key = cb[4:]
        cat     = BASE_MENU.get(cat_key)
        if not cat: return
        await q.edit_message_text(
            f"{CE_ADDFILE} <b>Add File — {esc(cat['label'])}</b>\n\nSelect a product:",
            parse_mode="HTML", reply_markup=kb_adm_prods_files("a", cat_key, d))
        return

    if cb.startswith("afp|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        cat = BASE_MENU.get(cat_key)
        if not cat or idx >= len(cat["products"]): return
        pname    = prod_name(cat_key, idx, d)
        existing = files_count(cat_key, idx, d)
        set_state(d, uid, f"add_file_item|{cat_key}|{idx}")
        await q.edit_message_text(
            f"📁 <b>Add File — {esc(pname)}</b>\n\n"
            f"Currently in stock: <b>{existing} file(s)</b>\n\n"
            f"Send a <b>file</b> (APK / IPA / ZIP / any) <b>or a download link</b> as text:",
            parse_mode="HTML")
        return

    if cb.startswith("rfc|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        cat_key = cb[4:]
        cat     = BASE_MENU.get(cat_key)
        if not cat: return
        await q.edit_message_text(
            f"🗑️ <b>Remove File — {esc(cat['label'])}</b>\n\nSelect a product:",
            parse_mode="HTML", reply_markup=kb_adm_prods_files("r", cat_key, d))
        return

    if cb.startswith("rfp|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        cat = BASE_MENU.get(cat_key)
        if not cat or idx >= len(cat["products"]): return
        pname    = prod_name(cat_key, idx, d)
        existing = files_count(cat_key, idx, d)
        if existing == 0:
            await q.edit_message_text(
                f"📁 <b>{esc(pname)}</b> has no files.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="adm|remove_file")
                ]]))
            return
        nf        = peek_file(cat_key, idx, d)
        file_desc = f"\nNext: <code>{esc(nf.get('name','?'))}</code>" if nf else ""
        await q.edit_message_text(
            f"🗑️ <b>Remove File — {esc(pname)}</b>\n\nFiles: <b>{existing}</b>{file_desc}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑️ Remove Next", callback_data=f"rfc_confirm|{cat_key}|{idx}")],
                [InlineKeyboardButton("🗑️ Clear ALL",   callback_data=f"rfc_all|{cat_key}|{idx}")],
                [InlineKeyboardButton("⬅️ Back",        callback_data="adm|remove_file")],
            ]))
        return

    if cb.startswith("rfc_confirm|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        removed = pop_file(cat_key, idx, d)
        if removed:
            await q.edit_message_text(
                f"✅ File removed: <code>{esc(removed.get('name','?'))}</code>",
                parse_mode="HTML")
        else:
            await q.edit_message_text("No files to remove.")
        return

    if cb.startswith("rfc_all|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        d.setdefault("files", {})[file_slot(cat_key, idx)] = []
        save(d)
        await q.edit_message_text(
            f"✅ All files cleared for <b>{esc(prod_name(cat_key, idx, d))}</b>.", parse_mode="HTML")
        return

    if cb.startswith("akc|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        cat_key = cb[4:]
        cat     = BASE_MENU.get(cat_key)
        if not cat: return
        await q.edit_message_text(
            f"🔑 <b>Add Keys — {esc(cat['label'])}</b>\n\nSelect a product:",
            parse_mode="HTML", reply_markup=kb_adm_prods_keys(cat_key, d))
        return

    if cb.startswith("akp|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        cat = BASE_MENU.get(cat_key)
        if not cat or idx >= len(cat["products"]): return
        pname = prod_name(cat_key, idx, d)
        await q.edit_message_text(
            f"{CE_ADDKEYS} <b>Add Keys — {esc(pname)}</b>\n\nSelect a duration:",
            parse_mode="HTML", reply_markup=kb_adm_durs_keys(cat_key, idx, d))
        return

    if cb.startswith("akd|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        parts   = cb.split("|"); cat_key = parts[1]; idx = int(parts[2]); dur_enc = parts[3]
        dur     = dec_dur(dur_enc)
        cat     = BASE_MENU.get(cat_key)
        if not cat or idx >= len(cat["products"]): return
        pname    = prod_name(cat_key, idx, d)
        existing = keys_count(cat_key, idx, dur, d)
        set_state(d, uid, f"add_keys_item|{cat_key}|{idx}|{dur}")
        await q.edit_message_text(
            f"🔑 <b>Add Keys</b>\n\n"
            f"Product: <b>{esc(pname)}</b>\nDuration: <b>{esc(dur)}</b>\n"
            f"Current stock: <b>{existing}</b>\n\nSend keys — <b>one per line</b>:",
            parse_mode="HTML")
        return

    # ── Admin panel main actions ───────────────────────────────────────────────
    if cb.startswith("adm|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        action = cb[4:]

        if action == "back":
            await q.message.reply_text(
                f"{CE_ADMIN} <b>Admin Panel — {esc(shop_name(d))}</b>\n\nChoose an action:",
                parse_mode="HTML", reply_markup=kb_admin_panel(uid, d))

        elif action == "add_keys":
            clear_state(d, uid)
            await q.message.reply_text(
                "🔑 <b>Add Keys</b>\n\nSelect a category:",
                parse_mode="HTML", reply_markup=kb_adm_cats_keys(d))

        elif action == "add_files":
            clear_state(d, uid)
            await q.message.reply_text(
                "📁 <b>Add File</b>\n\nSelect a category:",
                parse_mode="HTML", reply_markup=kb_adm_cats_files("a", d))

        elif action == "remove_file":
            clear_state(d, uid)
            await q.message.reply_text(
                "🗑️ <b>Remove File</b>\n\nSelect a category:",
                parse_mode="HTML", reply_markup=kb_adm_cats_files("r", d))

        elif action == "view_keys":
            DOT_ON = CE_AVAIL; DOT_OFF = CE_UNAVAIL
            lines  = ["📦 <b>Stock Overview</b>\n"]
            for k in CAT_ORDER:
                cat = BASE_MENU[k]
                lines.append(f"<b>{esc(cat['label'])}</b>")
                for i in range(len(cat["products"])):
                    pname = prod_name(k, i, d)
                    for dur, _ in prod_prices(k, i, d):
                        qty = keys_count(k, i, dur, d)
                        dot = DOT_ON if qty > 0 else DOT_OFF
                        lines.append(f"  {dot} {esc(pname)} — {esc(dur)}: <b>{qty} keys</b>")
                lines.append("")
            lines.append(f"\n{CE_RESELLER} <b>Reseller Stock</b>")
            for i, p in enumerate(RESELLER_MENU):
                for dur, _ in reseller_prod_prices(i, d):
                    qty = res_keys_count(i, dur, d)
                    dot = DOT_ON if qty > 0 else DOT_OFF
                    lines.append(f"  {dot} {esc(p['name'])} — {esc(dur)}: <b>{qty} keys</b>")
            await send_long(q.message, "\n".join(lines), parse_mode="HTML")

        elif action == "view_raw_keys":
            if not can_view_keys(uid, d):
                await q.message.reply_text("⚠️ Only the super admin can view raw keys.")
                return
            lines = [f"{CE_KEY_LBL} <b>Raw Keys (Super Admin Only)</b>\n"]
            for k in CAT_ORDER:
                cat = BASE_MENU[k]
                lines.append(f"<b>{esc(cat['label'])}</b>")
                for i in range(len(cat["products"])):
                    pname = prod_name(k, i, d)
                    for dur, _ in prod_prices(k, i, d):
                        slot     = key_slot(k, i, dur)
                        raw_keys = d.get("keys", {}).get(slot, [])
                        lines.append(f"\n<b>{esc(pname)} — {esc(dur)}</b> ({len(raw_keys)} keys)")
                        for kv in raw_keys:
                            lines.append(f"  <code>{esc(kv)}</code>")
                lines.append("")
            lines.append(f"\n{CE_RESELLER} <b>Reseller Raw Keys</b>")
            for i, p in enumerate(RESELLER_MENU):
                for dur, _ in reseller_prod_prices(i, d):
                    slot     = res_key_slot(i, dur)
                    raw_keys = d.get("res_keys", {}).get(slot, [])
                    lines.append(f"\n<b>{esc(p['name'])} — {esc(dur)}</b> ({len(raw_keys)} keys)")
                    for kv in raw_keys:
                        lines.append(f"  <code>{esc(kv)}</code>")
            await send_long(q.message, "\n".join(lines), parse_mode="HTML")

        elif action == "view_files":
            DOT_ON = CE_AVAIL; DOT_OFF = CE_UNAVAIL
            lines  = ["📁 <b>Files Stock</b>\n"]
            for k in CAT_ORDER:
                cat = BASE_MENU[k]
                lines.append(f"<b>{esc(cat['label'])}</b>")
                for i in range(len(cat["products"])):
                    pname = prod_name(k, i, d)
                    fqty  = files_count(k, i, d)
                    dot   = DOT_ON if fqty > 0 else DOT_OFF
                    lines.append(f"  {dot} {esc(pname)}: <b>{fqty} file(s)</b>")
                lines.append("")
            await send_long(q.message, "\n".join(lines), parse_mode="HTML")

        elif action == "add_bal":
            set_state(d, uid, "add_bal")
            await q.message.reply_text(
                "<b>Add Balance</b>\n\nSend: <code>USER_ID AMOUNT</code>",
                parse_mode="HTML", reply_markup=kb_cancel())

        elif action == "ded_bal":
            set_state(d, uid, "ded_bal")
            await q.message.reply_text(
                "<b>Deduct Balance</b>\n\nSend: <code>USER_ID AMOUNT</code>",
                parse_mode="HTML", reply_markup=kb_cancel())

        elif action == "chk_bal":
            set_state(d, uid, "chk_bal")
            await q.message.reply_text(
                "<b>Check Balance</b>\n\nSend the Telegram User ID:",
                parse_mode="HTML", reply_markup=kb_cancel())

        elif action == "add_admin":
            set_state(d, uid, "admin_id")
            await q.message.reply_text(
                "<b>Add Admin</b>\n\nSend the Telegram User ID of the new admin:",
                parse_mode="HTML", reply_markup=kb_cancel())

        elif action == "remove_admin":
            if not is_super_admin(uid):
                await q.answer("Super admin only.", show_alert=True); return
            admins = d.get("admin_ids", [])
            if not admins:
                await q.message.reply_text(
                    "👑 <b>Remove Admin</b>\n\nNo dynamically added admins to remove.",
                    parse_mode="HTML", reply_markup=kb_cancel())
                return
            current = "\n".join(f"  • <code>{a}</code>" for a in admins)
            set_state(d, uid, "remove_admin_id")
            await q.message.reply_text(
                f"🗑️ <b>Remove Admin</b>\n\n"
                f"Current admins:\n{current}\n\n"
                f"Send the Telegram User ID to <b>remove</b>:",
                parse_mode="HTML", reply_markup=kb_cancel())

        elif action == "grant_key_view":
            if not is_super_admin(uid):
                await q.answer("Super admin only.", show_alert=True); return
            kva = d.get("key_view_admins", [])
            current = "\n".join(f"  • <code>{i}</code>" for i in kva) if kva else "  None"
            set_state(d, uid, "grant_key_view")
            await q.message.reply_text(
                f"{CE_KEY_LBL} <b>Grant Key-View Access</b>\n\n"
                f"Admins who can currently view raw keys:\n{current}\n\n"
                f"Send the Telegram User ID to <b>grant</b> key-view access\n"
                f"(must already be an admin):",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫  Revoke from someone", callback_data="adm|revoke_key_view")],
                    [InlineKeyboardButton("❌  Cancel", callback_data="adm|cancel")],
                ])
            )

        elif action == "revoke_key_view":
            if not is_super_admin(uid):
                await q.answer("Super admin only.", show_alert=True); return
            kva = d.get("key_view_admins", [])
            current = "\n".join(f"  • <code>{i}</code>" for i in kva) if kva else "  None"
            set_state(d, uid, "revoke_key_view")
            await q.message.reply_text(
                f"🚫 <b>Revoke Key-View Access</b>\n\n"
                f"Admins with key-view access:\n{current}\n\n"
                f"Send the Telegram User ID to <b>revoke</b>:",
                parse_mode="HTML", reply_markup=kb_cancel()
            )

        elif action == "broadcast":
            set_state(d, uid, "broadcast")
            await q.message.reply_text(
                "📢 <b>Broadcast</b>\n\nType your message (HTML supported):",
                parse_mode="HTML", reply_markup=kb_cancel())

        elif action == "clear_pending":
            count = len(d.get("pending_orders", {}))
            d["pending_orders"] = {}
            save(d)
            await q.message.reply_text(
                f"✅ <b>Cleared {count} pending order(s).</b>",
                parse_mode="HTML"
            )

        elif action == "reseller_mgmt":
            resellers = d.get("resellers", {})
            if resellers:
                lines = [f"{CE_RESELLER} <b>Resellers</b>\n"]
                for rname, rdata in resellers.items():
                    bal = rdata.get("balance", 0.0)
                    lines.append(f"• <b>{esc(rname)}</b> — Balance: ${bal:.2f}")
                summary = "\n".join(lines)
            else:
                summary = f"{CE_RESELLER} <b>No resellers yet.</b>"
            await q.message.reply_text(
                summary + "\n\nManage resellers:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕  Add Reseller",         callback_data="adm|res_add")],
                    [InlineKeyboardButton("💰  Add Reseller Bal",     callback_data="adm|res_add_bal")],
                    [InlineKeyboardButton("🗑️  Remove Reseller",      callback_data="adm|res_del")],
                    [InlineKeyboardButton("🔑  Add Reseller Keys",    callback_data="adm|res_add_keys")],
                    [InlineKeyboardButton("⬅️  Back",                 callback_data="adm|back")],
                ])
            )

        elif action == "res_add":
            set_state(d, uid, "adm_res_add")
            await q.message.reply_text(
                f"{CE_RESELLER} <b>Add Reseller</b>\n\n"
                f"Send: <code>USERNAME PASSWORD</code>\n\n"
                f"<i>Example: john mypassword123</i>",
                parse_mode="HTML", reply_markup=kb_cancel())

        elif action == "res_add_bal":
            set_state(d, uid, "adm_res_bal")
            await q.message.reply_text(
                f"💰 <b>Add Reseller Balance</b>\n\nSend: <code>USERNAME AMOUNT</code>",
                parse_mode="HTML", reply_markup=kb_cancel())

        elif action == "res_del":
            set_state(d, uid, "adm_res_del")
            await q.message.reply_text(
                f"🗑️ <b>Remove Reseller</b>\n\nSend the reseller username:",
                parse_mode="HTML", reply_markup=kb_cancel())

        elif action == "res_add_keys":
            clear_state(d, uid)
            await q.message.reply_text(
                f"{CE_ADDKEYS} <b>Add Reseller Keys</b>\n\nSelect a product:",
                parse_mode="HTML", reply_markup=kb_res_add_keys_prods()
            )

        elif action == "clear":
            await q.message.reply_text(
                "⚠️ <b>Clear ALL shop keys?</b> This cannot be undone.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Yes, clear all", callback_data="adm|confirm_clear"),
                    InlineKeyboardButton("Cancel",         callback_data="adm|cancel"),
                ]]))

        elif action == "confirm_clear":
            d["keys"] = {}; save(d)
            try: await q.edit_message_text("✅ All shop keys cleared.")
            except Exception: await q.message.reply_text("✅ All shop keys cleared.")

        elif action == "cancel":
            clear_state(d, uid)
            try: await q.edit_message_text("Cancelled.")
            except Exception: await q.message.reply_text("Cancelled.")

        return


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER: cancel previous pending order for a user (cleanup orphans)
# ═══════════════════════════════════════════════════════════════════════════════
def _cancel_user_pending(uid: int, d: dict):
    """Remove any existing pending order for this user to avoid orphans."""
    pending = d.get("pending_orders", {})
    to_remove = [oid for oid, o in pending.items() if o.get("user_id") == uid]
    for oid in to_remove:
        pending.pop(oid, None)
    if to_remove:
        save(d)


# ═══════════════════════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ═══════════════════════════════════════════════════════════════════════════════
async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    err = ctx.error
    if isinstance(err, (Conflict, NetworkError, TimedOut)):
        logger.warning(f"Transient: {err}"); return
    logger.error(f"Unhandled error: {err}", exc_info=err)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    # Kill any other instances
    try:
        result = subprocess.run(
            ["pgrep", "-f", "bot.py"],
            capture_output=True, text=True
        )
        for pid_str in result.stdout.strip().splitlines():
            pid = int(pid_str.strip())
            if pid != os.getpid():
                try: os.kill(pid, signal.SIGTERM)
                except Exception: pass
    except Exception:
        pass

    for _f in [DATA_FILE, DATA_FILE + ".tmp", "bot_persistence"]:
        if Path(_f).exists():
            try: os.chmod(_f, 0o666)
            except Exception: pass

    # Clean up stale _state on startup
    try:
        d = load()
        d["_state"] = {}
        save(d)
        logger.info("Cleared all user states on startup.")
    except Exception:
        pass

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(handle_cb))
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.Document.ALL) & filters.ChatType.PRIVATE, handle_media))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_text))
    app.add_error_handler(on_error)

    logger.info(f"Starting {DEFAULT_SHOP_NAME}...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
