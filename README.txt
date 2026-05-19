diyzu Bot — Fixed Version
==========================

SETUP
-----
1. Install dependencies:
   pip install -r requirements.txt

2. Set your bot token:
   - Edit bot.py line: BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
   OR set environment variable: export BOT_TOKEN=your_token

3. Run the bot:
   python bot.py

FIXES APPLIED
-------------
1. CRITICAL BUG: res_add_keys_item state parser was split("|",3) checking len==4
   but state only has 3 parts — admin could NEVER add reseller keys. FIXED.

2. Binance Pay now shows a clickable "Open Binance App" deep-link button
   (https://app.binance.com/qr/orf/pay?userId=YOUR_ID) so buyers can tap to pay
   directly from Telegram — no manual app-switching needed.

3. Users stuck in "awaiting screenshot" state who send a text message now get a
   clear reminder: "Please send your Binance/UPI screenshot as a photo."
   Previously the bot was silently ignoring their text.

4. /start now clears any stuck state automatically. If a user is stuck just tell
   them to type /start.

5. Bot startup clears ALL stale _state entries from the data file so nobody is
   stuck on restart.

6. Old/orphaned pending orders are cancelled when the same user starts a new
   payment — no more piling up of ghost orders.

7. When wallet balance is low but Binance/UPI are available, the message now
   says "Balance low — pay via Binance/UPI below" instead of just "Insufficient
   balance" with no explanation.

8. New "Clear Pending Orders" button in Admin Panel to wipe all pending orders
   at any time.

9. All dur (duration) values are now encoded/decoded safely (spaces → ~) in
   callback_data for consistency.

ADMIN COMMANDS
--------------
- /start  — Main menu (also clears your stuck state)
- Admin Panel → Clear Pending Orders — wipe all ghost pending orders
- Admin Panel → Settings → Set Binance ID — update Binance Pay UID

ENVIRONMENT
-----------
- BOT_TOKEN  — set in bot.py or as env variable
- bot_data.json — auto-created/saved next to bot.py

NOTE: bot_data.json included in this zip has all stale pending orders cleared
and all user states reset so you start clean.
