# HSR Flat-Hunt Bot

Watches Facebook groups, Reddit, and Twitter every 30 min for flat/PG/flatmate posts near HSR Layout (Bangalore). DMs matching posts to Telegram.

**Match rules:**
- Must mention HSR or a nearby area (Koramangala, BTM, Bommanahalli, Sarjapur Road, Iblur, Agara, Bellandur)
- Must mention men / male / boy / guys / bachelor
- Drops broker posts and female-only posts

---

## One-time setup

### 1. Local Python env

```bash
cd /Users/shubhamsingla/STAGE/hsr-flat-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Create a Telegram bot

1. Open Telegram, message **@BotFather**, send `/newbot`.
2. Pick a name (e.g. `HSR Flat Bot`) and username (e.g. `shubham_hsr_flat_bot`).
3. BotFather replies with a token like `123456:ABC-DEF...`. Save it.
4. Message your new bot anything (so it can DM you).
5. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser. Find `"chat":{"id":<NUMBER>}`. Save that chat id.

### 3. `.env`

```bash
cp .env.example .env
```

Fill in:
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from step 2.
- `FB_GROUP_URLS` — comma-separated full URLs of FB groups your **burner account** has joined. Example: `https://www.facebook.com/groups/bangaloreflatmates,https://www.facebook.com/groups/hsrflatmates`

### 4. Save FB session cookies (burner account)

```bash
python setup_fb.py
```

A Chrome window opens. Log into the **burner FB account**, wait for the home feed, switch back to the terminal, press Enter. `data/cookies.json` will be saved.

### 5. Test locally

```bash
python main.py
```

First run will only DM posts from the last 6 hours. You should get one or more messages on Telegram within ~30 seconds.

---

## Deploy to Render (free, every 30 min)

### 1. Push to a **private** GitHub repo

Use the **`shubhamsingla807`** account (not `shubhamsingla-netizen`).

```bash
cd /Users/shubhamsingla/STAGE/hsr-flat-bot
git init
git add .
git commit -m "init"
# Create a PRIVATE repo on github.com under shubhamsingla807, then:
git remote add origin https://github.com/shubhamsingla807/hsr-flat-bot.git
git branch -M main
git push -u origin main
```

> ⚠️ `cookies.json` is in `.gitignore` — it stays local. You'll upload it to Render as a secret file (step 3).

### 2. Create a GitHub fine-grained PAT

`github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token`

- **Repository access:** only `hsr-flat-bot`
- **Permissions:** Contents → Read and write
- Copy the `github_pat_...` token.

### 3. Render cron service

1. Go to render.com → New → Blueprint.
2. Point it at your GitHub repo. Render reads `render.yaml`.
3. Add env vars in the dashboard (these are `sync: false` in the yaml):
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `FB_GROUP_URLS`
   - `GIT_REPO_URL` = `https://github.com/shubhamsingla807/hsr-flat-bot.git`
   - `GIT_TOKEN` = the PAT from step 2
4. Upload `data/cookies.json` as a **Secret File** at path `data/cookies.json`.
5. Deploy.

The cron runs every 30 min: pulls latest repo → fetches sources → DMs matches → commits updated `seen.json` back to the repo.

---

## Maintenance

- **FB session expires** (FB sometimes invalidates cookies even on burner): re-run `setup_fb.py` locally, re-upload `cookies.json` to Render.
- **Tweak filters:** edit `filters.py`, push to GitHub, Render redeploys automatically.
- **Add a FB group:** add its URL to `FB_GROUP_URLS` env var in Render dashboard.
- **Pause the bot:** in Render, suspend the cron service.

## When you're done flat-hunting

Suspend the Render cron and (optionally) delete the GitHub repo. Bot is disposable.
