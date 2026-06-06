#!/usr/bin/env bash
# Wrapper that runs the bot and persists seen.json back to git.
# Designed for Render cron. Locally, you can just `python main.py`.

set -euo pipefail

cd "$(dirname "$0")"

# Pull latest seen.json (in case a previous tick or manual edit changed it)
if [ -n "${GIT_REPO_URL:-}" ] && [ -n "${GIT_TOKEN:-}" ]; then
  git config --global user.email "bot@hsr-flat-bot.local"
  git config --global user.name "hsr-flat-bot"
  AUTH_URL="$(echo "$GIT_REPO_URL" | sed "s#https://#https://${GIT_TOKEN}@#")"

  if [ ! -d .git ]; then
    git clone "$AUTH_URL" tmp_repo
    cp -r tmp_repo/.git .
    rm -rf tmp_repo
  fi
  git remote set-url origin "$AUTH_URL"
  git pull --rebase --autostash origin main || echo "git pull failed, continuing with local seen.json"
fi

python main.py

# Commit + push seen.json + cookies update if anything changed.
if [ -n "${GIT_REPO_URL:-}" ] && [ -n "${GIT_TOKEN:-}" ]; then
  if ! git diff --quiet data/seen.json 2>/dev/null; then
    git add data/seen.json
    git commit -m "chore: update seen.json [skip ci]" || true
    git push origin main || echo "git push failed (non-fatal)"
  fi
fi
