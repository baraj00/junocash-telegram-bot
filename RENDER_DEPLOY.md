# 🚀 Deploy on Render.com (100% FREE)

## Why Render?
✅ **Completely FREE** - No credit card needed
✅ 750 hours/month free (enough for 24/7)
✅ Auto-restart on crash
✅ Easy deployment from GitHub

## Step 1: Push to GitHub

```bash
cd "C:\Users\albar\Desktop\zcash\juno cash\bot juno"

# Initialize git
git init
git add .
git commit -m "Juno Cash Telegram Bot"

# Create repo on GitHub (https://github.com/new)
# Name it: junocash-telegram-bot

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/junocash-telegram-bot.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy on Render

1. Go to **https://render.com**
2. Sign up with GitHub (FREE, no credit card)
3. Click **"New +"** → **"Background Worker"**
4. Connect your GitHub account
5. Select **junocash-telegram-bot** repository
6. Fill in:
   - **Name**: `junocash-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: **FREE** ✅
7. Click **"Create Background Worker"**

## Step 3: Done! 🎉

Your bot is now live 24/7 for FREE!

## Monitor Your Bot

- **Logs**: Available in Render dashboard
- **Status**: Shows if bot is running
- **Auto-deploy**: Pushes to GitHub auto-update bot

## Alternative: Fly.io (Also Free)

If Render doesn't work:

1. Go to **https://fly.io**
2. Sign up (free tier: 3 VMs, no credit card)
3. Install flyctl: `powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"`
4. Deploy:
```bash
cd "C:\Users\albar\Desktop\zcash\juno cash\bot juno"
fly launch
fly deploy
```

## Comparison

| Platform | Free Tier | Credit Card | Best For |
|----------|-----------|-------------|----------|
| Render.com | 750h/month | ❌ No | **Easiest** |
| Fly.io | 3 VMs | ❌ No (optional) | Flexible |
| Railway | ❌ Paid now | ✅ Yes | Was good |
| Heroku | ❌ No free tier | ✅ Yes | Dead |

## Recommendation

**Use Render.com** - 100% free, no tricks, works perfectly for bots!
