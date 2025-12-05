# Juno Cash Telegram Bot - Deployment Guide

## Deploy to Railway (Free & Easy)

1. **Create GitHub Repository**
   - Go to https://github.com/new
   - Name it `junocash-telegram-bot`
   - Make it public or private
   - Don't initialize with README

2. **Push Code to GitHub**
   ```bash
   cd "C:\Users\albar\Desktop\zcash\juno cash\bot juno"
   git init
   git add .
   git commit -m "Initial commit - Juno Cash Telegram Bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/junocash-telegram-bot.git
   git push -u origin main
   ```

3. **Deploy to Railway**
   - Go to https://railway.app
   - Sign up with GitHub
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `junocash-telegram-bot` repository
   - Railway will auto-detect Python and deploy!

4. **Done!** 
   - Bot runs 24/7 for free (500 hours/month free tier)
   - Auto-restarts if it crashes
   - Logs available in Railway dashboard

## Alternative: Render.com

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New" → "Background Worker"
4. Connect your GitHub repo
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `python bot.py`
7. Deploy!

## Important Notes

- Database file (`juno_bot.db`) will persist on Railway
- Bot token is hardcoded (already in bot.py)
- Free tier limits: 500 hours/month Railway, unlimited on Render
- Both platforms auto-deploy on git push

## Testing Locally

```bash
python bot.py
```

## Commands

- `/start` - Welcome with interactive buttons
- `/setup <host> [user] [pass]` - Connect to node
- `/balance` - Check JUNO balance
- `/shield all` - Shield transparent to private
- `/send <address> <amount>` - Send JUNO privately
- `/confirm` - Confirm transaction

## Support

Join Juno Cash Telegram community for help!
