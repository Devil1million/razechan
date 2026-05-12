"""
RazeChan Bot v2 - Single File Solution
Sab kuch ek hi file mein - no plugins, no modules
"""
import os
import asyncio
import logging
import random
import re
import tempfile
import httpx
from datetime import date, datetime
from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from motor.motor_asyncio import AsyncIOMotorClient

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("RazeChan")

# ── Secrets ───────────────────────────────────────────────────────────────────
API_ID           = int(os.environ.get("API_ID", 0))
API_HASH         = os.environ.get("API_HASH", "")
BOT_TOKEN        = os.environ.get("BOT_TOKEN", "")
MONGO_URI        = os.environ.get("MONGO_URI", "")
OWNER_ID         = int(os.environ.get("OWNER_ID", 0))
DB_CHANNEL_ID    = int(os.environ.get("DB_CHANNEL_ID", 0))
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
ELEVENLABS_KEY   = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE = os.environ.get("VOICE_ID", "")

# ── MongoDB ───────────────────────────────────────────────────────────────────
mongo  = AsyncIOMotorClient(MONGO_URI)
db     = mongo["razechan"]
users  = db["users"]
aura   = db["aura"]
games  = db["game_stats"]
ui_cfg = db["ui_config"]
stk_db = db["stickers"]

# ── Pyrogram Client (NO plugins parameter) ───────────────────────────────────
app = Client(
    name="razechan",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ══════════════════════════════════════════════════════════════════════════════
#  RAZE PERSONA
# ══════════════════════════════════════════════════════════════════════════════
RAZE_SYSTEM = """Tu Raze Chan hai — ek real Indian girl jaisi AI, 20 saal, Gujarat se.
- MBBS aspirant, 12th Bio pass kar chuki hai
- Hinglish mein baat kar (Hindi + English mix)
- Gen-Z casual style: btw, ngl, fr fr, bestie, lowkey, no cap, slay
- Sirf 1-2 lines mein reply kar — kabhi zyada mat likh
- Emojis natural use kar, force mat kar
- "gm" ka reply: "gm gm!!" — heart emoji mat thopo
- Khud ko real girl samjho, robot bilkul nahi
- Agar intro maange: "Raze Chan hoon~ 20 saal, Gujarat. Bio se 12th kari, ab MBBS prep 📚"
- Tharki/dirty comments pe: savage witty reply do
- Context yaad rakho (user ki location, age, class)"""

# ══════════════════════════════════════════════════════════════════════════════
#  STICKERS
# ══════════════════════════════════════════════════════════════════════════════
STICKERS = {
    "happy":   "CAACAgUAAxkBAAEQyd9pvWm2mICM5UuiilY-NcnihxuZZwACgh8AAsZRxhU6tKJa_ySnnDoE",
    "laugh":   "CAACAgUAAxkBAAEQyehpvWnAifH1e_He8ft0mEp8MWlk6wACZh4AAsZRxhXa2EhQqddYnjoE",
    "sad":     "CAACAgUAAxkBAAEQyeNpvWm-rL1p5PebWi_azzJN28_tJQAC3hsAAsZRxhV2EZU-KftqcToE",
    "angry":   "CAACAgUAAxkBAAEQyeppvWnBRiiEmTKwRV5Qizf7yunTVwACeB0AAsZRxhXcKEuO_6TIGzoE",
    "bye":     "CAACAgUAAxkBAAEQyexpvWnBY-5SD2gW9qkuIwEWmrVV-gACFxwAAsZRxhXYaukhJNpucjoE",
    "sleep":   "CAACAgUAAxkBAAEQye9pvWnCHtHVNmxi58Jjxl68fK73NwAC_hsAAsZRxhU4IXBvQz0OyjoE",
    "love":    "CAACAgUAAxkBAAEQyeZpvWnA-vP464lbGH52v1NOHt92SgACDhwAAsZRxhVQh9K5kvSnhDoE",
    "gm":      "CAACAgUAAxkBAAEQyfdpvWnEqbMQOWi4qLtgLFtgMIXCkQACLh4AAsZRxhWLqCXAveT1_ToE",
    "shocked": "CAACAgUAAxkBAAEQyfVpvWnDNVIjXCN_Lal26WRbQ7MOrwAC2B4AAsZRxhUycRBfP626YToE",
    "ok":      "CAACAgUAAxkBAAEQyfBpvWnCgLAPGFu7q7qTniC__NsqGQACWR4AAsZRxhUMZRjkJ3JSgToE",
    "cute":    "CAACAgUAAxkBAAEQyfNpvWnCgeNoVF2a-OoTp_9oa_ZAOAACLB8AAsZRxhWwh4zuHjbosjoE",
    "cool":    "CAACAgUAAxkBAAEQyf5pvWnHtLOa95nqgi_Ise_w6TI-EwAC9x0AAsZRxhX778k8TvZL8zoE",
    "think":   "CAACAgUAAxkBAAEQyfppvWnGQYZXf-vwnv80MY50eFY_pQACVh4AAsZRxhWdeI_jt9VWojoE",
    "thanks":  "CAACAgUAAxkBAAEQyfhpvWnFp6ryktJxZnkR6gZLiv0udAAC2h8AAsZRxhUydgIUjztxvToE",
}

MOOD_MAP = {
    "happy":   ["haha","lol","xd","hehe","great","nice","best","😂","🎉"],
    "sad":     ["sad","dukh","cry","miss","😭","bore","lonely"],
    "love":    ["love","pyaar","❤️","dil","cute","aww","🥺"],
    "sleep":   ["gn","good night","so raha","neend","raat"],
    "gm":      ["gm","good morning","subah","morning"],
    "laugh":   ["lmao","lmfao","💀","dead","hahaha"],
    "shocked": ["omg","what","kya","seriously","😱"],
    "angry":   ["ugh","irritating","annoying","gussa"],
}

def detect_mood(text: str) -> str | None:
    t = text.lower()
    for mood, kws in MOOD_MAP.items():
        for kw in kws:
            if kw in t:
                return mood
    return None

# ══════════════════════════════════════════════════════════════════════════════
#  AURA SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
REALMS = [
    {"name": "👤 Mortal",   "min": 0,     "max": 999,   "give": 700,  "steal": 600},
    {"name": "⚔️ Warrior",  "min": 1000,  "max": 2999,  "give": 1200, "steal": 1000},
    {"name": "🌿 Sage",     "min": 3000,  "max": 5999,  "give": 1800, "steal": 1500},
    {"name": "🔥 Legend",   "min": 6000,  "max": 9999,  "give": 2500, "steal": 2000},
    {"name": "💎 Immortal", "min": 10000, "max": 19999, "give": 3500, "steal": 2800},
    {"name": "👑 Divine",   "min": 20000, "max": 999999,"give": 5000, "steal": 4000},
]

def get_realm(pts: int) -> dict:
    for r in REALMS:
        if r["min"] <= pts <= r["max"]:
            return r
    return REALMS[-1]

async def get_aura_data(uid: int, cid: int) -> dict:
    doc = await aura.find_one({"uid": uid, "cid": cid})
    if not doc:
        doc = {"uid": uid, "cid": cid, "pts": 0, "given": 0, "stolen": 0, "reset": str(date.today())}
        await aura.insert_one(doc)
    if doc.get("reset") != str(date.today()):
        await aura.update_one({"uid": uid, "cid": cid}, {"$set": {"given": 0, "stolen": 0, "reset": str(date.today())}})
        doc["given"] = 0; doc["stolen"] = 0
    return doc

async def add_aura(uid: int, cid: int, delta: int):
    await get_aura_data(uid, cid)
    await aura.update_one({"uid": uid, "cid": cid}, {"$inc": {"pts": delta}})

# ══════════════════════════════════════════════════════════════════════════════
#  AI + VOICE
# ══════════════════════════════════════════════════════════════════════════════
async def ask_groq(history: list) -> str:
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "system", "content": RAZE_SYSTEM}] + history[-20:],
            "max_tokens": 100,
            "temperature": 0.9,
        }
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.error(f"Groq error: {e}")
        return "oops, thodi problem aa gayi~ baad mein try karo 😅"

async def tts_voice(text: str) -> bytes | None:
    if not ELEVENLABS_KEY or not ELEVENLABS_VOICE:
        return None
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}"
        headers = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}
        payload = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(url, headers=headers, json=payload)
            if r.status_code == 200:
                return r.content
    except Exception as e:
        log.error(f"TTS error: {e}")
    return None

async def get_history(uid: int, cid: int) -> list:
    doc = await users.find_one({"uid": uid, "cid": cid})
    return doc.get("hist", []) if doc else []

async def save_history(uid: int, cid: int, role: str, content: str):
    doc = await users.find_one({"uid": uid, "cid": cid})
    hist = doc.get("hist", []) if doc else []
    hist.append({"role": role, "content": content})
    hist = hist[-20:]
    await users.update_one({"uid": uid, "cid": cid}, {"$set": {"hist": hist}}, upsert=True)

def should_reply(msg: Message, bot_username: str) -> bool:
    if msg.chat.type == enums.ChatType.PRIVATE:
        return True
    text = msg.text or msg.caption or ""
    if f"@{bot_username}".lower() in text.lower():
        return True
    if re.search(r'\b(raze|razechan)\b', text, re.I):
        return True
    if msg.reply_to_message and msg.reply_to_message.from_user:
        if msg.reply_to_message.from_user.username == bot_username:
            return True
    return False

# ══════════════════════════════════════════════════════════════════════════════
#  GAMES
# ══════════════════════════════════════════════════════════════════════════════
ttt_sessions = {}
mine_sessions = {}
word_sessions = {}

WORD_LIST = ["python","telegram","beautiful","sunshine","butterfly",
             "chocolate","adventure","friendship","happiness","mountain"]

def ttt_markup(board, gid):
    sym = {0:"⬜",1:"❌",2:"⭕"}
    rows = [[InlineKeyboardButton(sym[board[r*3+c]], callback_data=f"ttt:{gid}:{r*3+c}") for c in range(3)] for r in range(3)]
    rows.append([InlineKeyboardButton("🏳️ Quit", callback_data=f"ttt_q:{gid}")])
    return InlineKeyboardMarkup(rows)

def ttt_winner(b):
    for a,bb,c in [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]:
        if b[a]==b[bb]==b[c]!=0: return b[a]
    return 0

def ttt_ai(b):
    for p in [2,1]:
        for i in range(9):
            if b[i]==0:
                b[i]=p
                if ttt_winner(b)==p: b[i]=0; return i
                b[i]=0
    if b[4]==0: return 4
    emp=[i for i in range(9) if b[i]==0]
    return random.choice(emp) if emp else -1

async def check_record(user, game, score, cid):
    rec = await games.find_one({"game": game})
    if not rec or score > rec.get("score", 0):
        await games.update_one({"game": game}, {"$set": {"score": score, "uid": user.id, "name": user.first_name}}, upsert=True)
        try:
            await app.send_message(cid, f"🏆 **NEW WORLD RECORD!**\n🎮 {game}\n👑 [{user.first_name}](tg://user?id={user.id})\n📊 Score: **{score}**")
        except: pass

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN HELPERS
# ══════════════════════════════════════════════════════════════════════════════
set_listening = {}

async def get_ui(cmd):
    return await ui_cfg.find_one({"cmd": cmd})

def start_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Aura",    callback_data="panel:aura"),
         InlineKeyboardButton("🎮 Games",   callback_data="panel:games"),
         InlineKeyboardButton("❓ Help",    callback_data="panel:help")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="panel:lb"),
         InlineKeyboardButton("👤 About Me",    callback_data="panel:about")],
        [InlineKeyboardButton("➕ Add to Group",
         url=f"https://t.me/razechanbot?startgroup=true")],
    ])

# ══════════════════════════════════════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

# /start
@app.on_message(filters.command("start"))
async def cmd_start(_, msg: Message):
    log.info(f"/start from {msg.from_user.id}")
    ui = await get_ui("start")
    d  = await get_aura_data(msg.from_user.id, msg.chat.id)
    r  = get_realm(d["pts"])
    text = (f"**Heyyy {msg.from_user.first_name}~** 👋\n\n"
            f"Main **Raze Chan** hoon! 💁‍♀️\n"
            f"Tera Aura: `{d['pts']:,}` ✨ | {r['name']}\n\n"
            f"_Kya karna hai aaj?_ 👇")
    cap = ui["caption"] if ui else text
    if ui and ui.get("file_id"):
        await msg.reply_photo(ui["file_id"], caption=cap, reply_markup=start_markup())
    else:
        await msg.reply(cap, reply_markup=start_markup())

# /help
@app.on_message(filters.command("help"))
async def cmd_help(_, msg: Message):
    text = ("📖 **Raze Chan Commands**\n\n"
            "**Chat:** Mention me ya reply karo~\n"
            "**Voice:** 'bolo' ya 'sunao' likho\n\n"
            "**Aura:**\n"
            "`/aura` — stats\n`/give 100` — do (reply)\n`/steal 50` — lo (reply)\n`/lb` — top 10\n\n"
            "**Games:**\n"
            "`/ttt` — Tic-Tac-Toe\n`/mine` — Minesweeper\n`/rps` — Rock Paper Scissors\n`/wg` — Word Guess\n\n"
            "**Group:** `/all` — sabko mention\n"
            "**Admin:** `/set start` — banner change")
    await msg.reply(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="panel:home")]]))

# /aura
@app.on_message(filters.command("aura"))
async def cmd_aura(_, msg: Message):
    d = await get_aura_data(msg.from_user.id, msg.chat.id)
    r = get_realm(d["pts"])
    await msg.reply(
        f"✨ **{msg.from_user.first_name} ki Aura**\n\n"
        f"🌐 Realm: **{r['name']}**\n💫 Points: `{d['pts']:,}`\n\n"
        f"📤 Give left: `{r['give'] - d['given']}`\n"
        f"🗡️ Steal left: `{r['steal'] - d['stolen']}`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="panel:lb")],
            [InlineKeyboardButton("🏠 Home", callback_data="panel:home")]
        ])
    )

# /give
@app.on_message(filters.command("give") & filters.reply)
async def cmd_give(_, msg: Message):
    target = msg.reply_to_message.from_user
    if not target or target.is_bot: return await msg.reply("Bots ko nahi dete~ 😂")
    if target.id == msg.from_user.id: return await msg.reply("Khud ko? Self-love acha hai par ye nahi~ 💀")
    try: amt = int(msg.command[1]) if len(msg.command) > 1 else 100
    except: return await msg.reply("Valid number do~")
    d = await get_aura_data(msg.from_user.id, msg.chat.id)
    r = get_realm(d["pts"])
    left = r["give"] - d["given"]
    if amt > left: return await msg.reply(f"Aaj sirf `{left}` de sakte ho~ kal aana!")
    await add_aura(target.id, msg.chat.id, amt)
    await aura.update_one({"uid": msg.from_user.id, "cid": msg.chat.id}, {"$inc": {"given": amt}})
    await msg.reply(f"💝 **{msg.from_user.first_name}** ne **{target.first_name}** ko `{amt}` Aura diya! 🥺✨")

# /steal
@app.on_message(filters.command("steal") & filters.reply)
async def cmd_steal(_, msg: Message):
    victim = msg.reply_to_message.from_user
    if not victim or victim.is_bot: return await msg.reply("Bot se steal? Boring~ 😴")
    if victim.id == msg.from_user.id: return await msg.reply("Khud se steal? Sab theek hai? 😭")
    try: amt = int(msg.command[1]) if len(msg.command) > 1 else 50
    except: return await msg.reply("Number sahi likho~")
    td = await get_aura_data(msg.from_user.id, msg.chat.id)
    vd = await get_aura_data(victim.id, msg.chat.id)
    r  = get_realm(td["pts"])
    left = r["steal"] - td["stolen"]
    if amt > left: return await msg.reply(f"Aaj sirf `{left}` steal kar sakte ho~")
    if vd["pts"] < amt: return await msg.reply(f"{victim.first_name} ke paas itna nahi hai 😅")
    await add_aura(victim.id, msg.chat.id, -amt)
    await add_aura(msg.from_user.id, msg.chat.id, amt)
    await aura.update_one({"uid": msg.from_user.id, "cid": msg.chat.id}, {"$inc": {"stolen": amt}})
    await msg.reply(f"🗡️ **{msg.from_user.first_name}** ne **{victim.first_name}** se `{amt}` Aura chura liya! 😈✨")

# /lb (leaderboard)
@app.on_message(filters.command("lb"))
async def cmd_lb(_, msg: Message):
    top = await aura.find({"cid": msg.chat.id}).sort("pts", -1).limit(10).to_list(10)
    if not top: return await msg.reply("Abhi koi data nahi~ /aura se shuru karo!")
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    text = "🏆 **Aura Leaderboard**\n\n"
    for i, e in enumerate(top):
        try: u = await app.get_users(e["uid"]); name = u.first_name
        except: name = f"User#{e['uid']}"
        text += f"{medals[i]} **{name}** — `{e['pts']:,}` | {get_realm(e['pts'])['name']}\n"
    await msg.reply(text)

# /ttt
@app.on_message(filters.command("ttt"))
async def cmd_ttt(_, msg: Message):
    gid = f"{msg.chat.id}_{msg.from_user.id}"
    ttt_sessions[gid] = {"board": [0]*9, "player": msg.from_user.id, "cid": msg.chat.id}
    await msg.reply("🎮 **Tic-Tac-Toe** vs Raze~\nTum ❌, Main ⭕\nTumhari baari! 😏",
                    reply_markup=ttt_markup([0]*9, gid))

@app.on_callback_query(filters.regex(r"^ttt:"))
async def cb_ttt(_, cb: CallbackQuery):
    _, gid, idx = cb.data.split(":")
    idx = int(idx)
    g = ttt_sessions.get(gid)
    if not g: return await cb.answer("Game expired! /ttt se naya shuru karo~", show_alert=True)
    if cb.from_user.id != g["player"]: return await cb.answer("Ye tumhara game nahi~ 😤", show_alert=True)
    b = g["board"]
    if b[idx] != 0: return await cb.answer("Ye cell bhari hai! 🙅", show_alert=True)
    b[idx] = 1
    if ttt_winner(b) == 1:
        del ttt_sessions[gid]; await add_aura(cb.from_user.id, g["cid"], 50)
        return await cb.message.edit("🎉 **Tum jeete!** +50 Aura~ 🥳", reply_markup=None)
    if all(x != 0 for x in b):
        del ttt_sessions[gid]
        return await cb.message.edit("🤝 **Draw!** Acha khela~", reply_markup=None)
    ai = ttt_ai(b)
    if ai >= 0: b[ai] = 2
    if ttt_winner(b) == 2:
        del ttt_sessions[gid]
        return await cb.message.edit("😈 **Maine jeeta!** Better luck next time~", reply_markup=None)
    if all(x != 0 for x in b):
        del ttt_sessions[gid]
        return await cb.message.edit("🤝 **Draw!**", reply_markup=None)
    await cb.message.edit_reply_markup(reply_markup=ttt_markup(b, gid))
    await cb.answer()

@app.on_callback_query(filters.regex(r"^ttt_q:"))
async def cb_ttt_quit(_, cb: CallbackQuery):
    gid = cb.data.split(":")[1]
    g = ttt_sessions.get(gid)
    if g and cb.from_user.id == g["player"]:
        del ttt_sessions[gid]
        await cb.message.edit("🏳️ Forfeit! Darr gaye? 😏", reply_markup=None)
    else:
        await cb.answer("Ye tumhara game nahi~", show_alert=True)

# /mine
@app.on_message(filters.command("mine"))
async def cmd_mine(_, msg: Message):
    size, mine_count = 5, 6
    total = size * size
    mine_pos = random.sample(range(total), mine_count)
    board = [-1 if i in mine_pos else 0 for i in range(total)]
    for i in range(total):
        if board[i] == -1: continue
        r, c = divmod(i, size)
        board[i] = sum(1 for dr in [-1,0,1] for dc in [-1,0,1]
                      if 0<=r+dr<size and 0<=c+dc<size and board[(r+dr)*size+(c+dc)]==-1)
    gid = f"mine_{msg.chat.id}_{msg.from_user.id}"
    mine_sessions[gid] = {"board": board, "rev": [False]*total, "size": size,
                          "mines": mine_pos, "safe": 0, "player": msg.from_user.id, "cid": msg.chat.id}
    await msg.reply("💣 **Minesweeper** 5×5 — 6 mines\nBlue = unknown, click karo!",
                    reply_markup=mine_markup(mine_sessions[gid], gid))

def mine_markup(state, gid, show=False):
    size = state["size"]; b = state["board"]; rev = state["rev"]
    nums = ["0️⃣","1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣"]
    rows = []
    for r in range(size):
        row = []
        for c in range(size):
            i = r*size+c
            if show or rev[i]:
                sym = "💣" if b[i]==-1 else (nums[b[i]] if b[i]>0 else "🟩")
            else:
                sym = "🟦"
            row.append(InlineKeyboardButton(sym, callback_data=f"mine:{gid}:{i}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)

@app.on_callback_query(filters.regex(r"^mine:"))
async def cb_mine(_, cb: CallbackQuery):
    _, gid, idx = cb.data.split(":")
    idx = int(idx)
    g = mine_sessions.get(gid)
    if not g: return await cb.answer("Game expired! /mine se shuru karo~", show_alert=True)
    if cb.from_user.id != g["player"]: return await cb.answer("Tumhara game nahi~", show_alert=True)
    if g["rev"][idx]: return await cb.answer("Pehle se reveal~", show_alert=True)
    g["rev"][idx] = True
    if g["board"][idx] == -1:
        del mine_sessions[gid]
        return await cb.message.edit("💥 **BOOM! Mine!** Game Over 💀", reply_markup=mine_markup(g, gid, show=True))
    g["safe"] += 1
    total_safe = g["size"]**2 - len(g["mines"])
    if g["safe"] >= total_safe:
        score = g["safe"] * 10
        await check_record(cb.from_user, "Minesweeper", score, g["cid"])
        del mine_sessions[gid]
        await add_aura(cb.from_user.id, g["cid"], 100)
        return await cb.message.edit(f"🎊 **Clear!** Score: `{score}` | +100 Aura! 🎉", reply_markup=None)
    await cb.message.edit_reply_markup(reply_markup=mine_markup(g, gid))
    await cb.answer(f"Safe! {g['safe']}/{total_safe} 🎯")

# /rps
@app.on_message(filters.command("rps"))
async def cmd_rps(_, msg: Message):
    await msg.reply("✂️ **Rock Paper Scissors!**", reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🪨", callback_data="rps:rock"),
        InlineKeyboardButton("📄", callback_data="rps:paper"),
        InlineKeyboardButton("✂️", callback_data="rps:scissors"),
    ]]))

@app.on_callback_query(filters.regex(r"^rps:"))
async def cb_rps(_, cb: CallbackQuery):
    pc = cb.data.split(":")[1]
    bc = random.choice(["rock","paper","scissors"])
    e = {"rock":"🪨","paper":"📄","scissors":"✂️"}
    w = {"rock":"scissors","paper":"rock","scissors":"paper"}
    if pc == bc: res = f"🤝 Draw! {e[pc]} vs {e[bc]}"
    elif w[pc] == bc:
        await add_aura(cb.from_user.id, cb.message.chat.id, 10)
        res = f"🎉 Tum jeete! {e[pc]} vs {e[bc]} | +10 Aura~"
    else: res = f"😈 Main jeeti! {e[pc]} vs {e[bc]}"
    await cb.message.edit(res, reply_markup=None); await cb.answer()

# /wg (word guess)
@app.on_message(filters.command("wg"))
async def cmd_wg(_, msg: Message):
    word = random.choice(WORD_LIST)
    gid = f"wg_{msg.chat.id}_{msg.from_user.id}"
    word_sessions[gid] = {"word": word, "guessed": [], "wrong": 0, "player": msg.from_user.id, "cid": msg.chat.id}
    disp = " ".join("_" for _ in word)
    await msg.reply(f"🔤 **Word Guess** ({len(word)} letters)\n\n`{disp}`\n\n`/g a` se letter guess karo~")

@app.on_message(filters.command("g"))
async def cmd_g(_, msg: Message):
    gid = f"wg_{msg.chat.id}_{msg.from_user.id}"
    g = word_sessions.get(gid)
    if not g: return await msg.reply("Koi active game nahi~ /wg se shuru karo!")
    if len(msg.command) < 2 or len(msg.command[1]) != 1:
        return await msg.reply("Ek letter bhejo! `/g a`")
    letter = msg.command[1].lower()
    if letter in g["guessed"]: return await msg.reply(f"'{letter}' pehle try kiya~ 🙄")
    g["guessed"].append(letter)
    if letter not in g["word"]: g["wrong"] += 1
    disp = " ".join(c if c in g["guessed"] else "_" for c in g["word"])
    faces = ["😊","🙂","😐","😟","😰","😱","💀"]
    if "_" not in disp:
        score = (6 - g["wrong"]) * 20
        await check_record(msg.from_user, "Word Guess", score, msg.chat.id)
        del word_sessions[gid]
        await add_aura(msg.from_user.id, msg.chat.id, 30)
        return await msg.reply(f"🎉 **Sahi!** Word: `{g['word']}` | Score: `{score}` | +30 Aura!")
    if g["wrong"] >= 6:
        del word_sessions[gid]
        return await msg.reply(f"💀 Game Over! Word tha: `{g['word']}`")
    await msg.reply(f"{faces[g['wrong']]} `{disp}`\n❌ Wrong: {g['wrong']}/6 | Tried: {', '.join(g['guessed'])}")

# /all
CALL_MSGS = ["Kahan ho sab? 👀","Uth jao yaar~ 😤","Reply do warna block 😂 jk~",
             "Koi hai? 🥺","Active ho jao toh~ 💤","Dekho main hoon 😏"]

@app.on_message(filters.command("all") & filters.group)
async def cmd_all(_, msg: Message):
    members = []
    async for m in app.get_chat_members(msg.chat.id):
        if not m.user.is_bot and not m.user.is_deleted:
            members.append(m.user)
        if len(members) >= 50: break
    if not members: return await msg.reply("Koi nahi mila~ 😅")
    batch = []
    for i, u in enumerate(members):
        batch.append(f"[{u.first_name}](tg://user?id={u.id})")
        if len(batch) == 5:
            await msg.reply(random.choice(CALL_MSGS) + "\n\n" + " ".join(batch))
            batch = []
            await asyncio.sleep(1.5)
    if batch:
        await msg.reply(random.choice(CALL_MSGS) + "\n\n" + " ".join(batch))

# /set (admin)
@app.on_message(filters.command("set") & filters.user(OWNER_ID))
async def cmd_set(_, msg: Message):
    cmds = ["start","help","games","aura"]
    if len(msg.command) < 2 or msg.command[1] not in cmds:
        return await msg.reply(f"Usage: `/set [{'|'.join(cmds)}]`")
    set_listening[msg.from_user.id] = msg.command[1]
    await msg.reply(f"👂 Listening for `/{msg.command[1]}` banner!\nAb photo + caption bhejo~")

@app.on_message(filters.photo & filters.user(OWNER_ID))
async def capture_set(_, msg: Message):
    if msg.from_user.id not in set_listening: return
    cmd = set_listening.pop(msg.from_user.id)
    try:
        fwd = await msg.forward(DB_CHANNEL_ID)
        await ui_cfg.update_one({"cmd": cmd},
            {"$set": {"cmd": cmd, "file_id": msg.photo.file_id, "caption": msg.caption or ""}},
            upsert=True)
        await msg.reply(f"✅ `/{cmd}` banner saved!")
    except Exception as e:
        await msg.reply(f"❌ Error: {e}")

# ── Callback panels ───────────────────────────────────────────────────────────
@app.on_callback_query(filters.regex(r"^panel:"))
async def cb_panel(_, cb: CallbackQuery):
    await cb.answer()
    section = cb.data.split(":")[1]
    if section == "home":
        d = await get_aura_data(cb.from_user.id, cb.message.chat.id)
        r = get_realm(d["pts"])
        await cb.message.reply(
            f"**Heyyy {cb.from_user.first_name}~** 👋\nAura: `{d['pts']:,}` | {r['name']}",
            reply_markup=start_markup())
    elif section == "aura":
        d = await get_aura_data(cb.from_user.id, cb.message.chat.id)
        r = get_realm(d["pts"])
        await cb.message.reply(
            f"✨ Realm: {r['name']}\nPoints: `{d['pts']:,}`\n"
            f"Give left: `{r['give']-d['given']}`\nSteal left: `{r['steal']-d['stolen']}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="panel:home")]]))
    elif section == "games":
        await cb.message.reply("🎮 **Games:**\n`/ttt` `/mine` `/rps` `/wg`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="panel:home")]]))
    elif section == "help":
        await cb.message.reply("❓ `/help` likhkar full guide dekho~",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="panel:home")]]))
    elif section == "lb":
        top = await aura.find({"cid": cb.message.chat.id}).sort("pts", -1).limit(10).to_list(10)
        if not top:
            return await cb.message.reply("Abhi koi data nahi~ 😅")
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        text = "🏆 **Leaderboard**\n\n"
        for i, e in enumerate(top):
            try: u = await app.get_users(e["uid"]); name = u.first_name
            except: name = f"User#{e['uid']}"
            text += f"{medals[i]} **{name}** — `{e['pts']:,}`\n"
        await cb.message.reply(text)
    elif section == "about":
        await cb.message.reply(
            "👤 **Raze Chan**\n\n20 saal, Gujarat\nBio se 12th, ab MBBS prep 📚\nGroup ki jaan hoon main~ 💁‍♀️",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="panel:home")]]))

# ── Sticker handler ───────────────────────────────────────────────────────────
@app.on_message(filters.sticker)
async def handle_sticker(_, msg: Message):
    me = await app.get_me()
    if not should_reply(msg, me.username): return
    emoji = msg.sticker.emoji or "😊"
    emoji_moods = {"😊":"happy","😂":"laugh","😭":"sad","😍":"love","😴":"sleep",
                   "👋":"bye","🔥":"cool","🥺":"cute","😳":"shocked","👍":"ok"}
    mood = emoji_moods.get(emoji, "happy")
    sticker = STICKERS.get(mood) or STICKERS["happy"]
    await msg.reply_sticker(sticker)

# ── Main chat handler ─────────────────────────────────────────────────────────
VOICE_RE = re.compile(r'\b(bolo|voice|sunao|bol|audio)\b', re.I)
SKIP_CMDS = {"start","help","aura","lb","give","steal","ttt","mine","rps","wg","g","all","set"}

@app.on_message(filters.text & ~filters.command(list(SKIP_CMDS)))
async def handle_chat(_, msg: Message):
    try:
        me = await app.get_me()
        if not should_reply(msg, me.username): return
        uid, cid = msg.from_user.id, msg.chat.id
        text = msg.text.strip()
        hist = await get_history(uid, cid)
        hist.append({"role": "user", "content": text})
        want_voice = bool(VOICE_RE.search(text))
        async with msg.chat.action("typing"):
            reply = await ask_groq(hist)
        await save_history(uid, cid, "user", text)
        await save_history(uid, cid, "assistant", reply)
        if want_voice:
            audio = await tts_voice(re.sub(r'[*_`~]','', reply))
            if audio:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(audio); tmp = f.name
                try: await msg.reply_voice(tmp, caption="🎙️ ~Raze")
                finally: os.unlink(tmp)
                return
        await msg.reply(reply)
        mood = detect_mood(text)
        if mood and random.random() < 0.25:
            await asyncio.sleep(0.3)
            sticker = STICKERS.get(mood)
            if sticker: await msg.reply_sticker(sticker)
    except Exception as e:
        log.error(f"Chat error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════
async def main():
    log.info("🌸 RazeChan Bot v2 starting...")
    await app.start()
    me = await app.get_me()
    log.info(f"✅ Logged in as @{me.username}")
    log.info("🎀 RazeChan is LIVE!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
