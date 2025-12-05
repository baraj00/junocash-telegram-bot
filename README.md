# 🤖 Juno Cash Telegram Bot

Monitor your Juno Cash nodes directly from Telegram!

## Features

- 💰 Check JUNO balance
- ⛏️ View mining statistics (hashrate, threads, blocks)
- 🌐 Network information
- 📬 View wallet addresses
- 🔔 Real-time notifications (coming soon)
- 👥 Multi-user support

## Installation

### 1. Install Dependencies

**Windows (PowerShell):**
```powershell
cd "C:\Users\albar\Desktop\zcash\juno cash\bot juno"
python -m pip install -r requirements.txt
```

**Linux/Mac:**
```bash
cd ~/juno-cash-bot
pip install -r requirements.txt
```

### 2. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the **Bot Token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 3. Configure Bot

Edit `bot.py` and replace:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
```

With your actual token:
```python
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
```

### 4. Run Bot

**Windows:**
```powershell
python bot.py
```

**Linux/Mac:**
```bash
python3 bot.py
```

## Usage

### Setup Your Node

Open your bot in Telegram and send:

```
/setup localhost
```

For remote nodes:
```
/setup 192.168.1.100
/setup your-vps-ip 8232
```

### Commands

- `/start` - Welcome message
- `/setup <host> [port]` - Configure node connection
- `/balance` - Check JUNO balance
- `/mining` - View mining stats
- `/network` - Network information
- `/address` - Show wallet addresses
- `/help` - Show help

## Examples

**Check Balance:**
```
/balance
```

**View Mining Stats:**
```
/mining
```

**Network Info:**
```
/network
```

## Configuration

### Enable RPC on Juno Cash Node

Make sure your `junocashd` is running with RPC enabled (default).

**Config file location:**
- Windows: `%APPDATA%\JunoCash\junocash.conf`
- Linux: `~/.junocash/junocash.conf`

**Example config:**
```conf
rpcuser=yourusername
rpcpassword=yourpassword
rpcallowip=127.0.0.1
rpcport=8232
```

### For Remote Access

If accessing a remote VPS, configure RPC to accept external connections:

```conf
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0
```

⚠️ **Security Warning:** Only do this if you have a firewall configured!

## Security

- Bot stores node credentials in local SQLite database
- Database file: `juno_bot.db`
- Only you can access your node through the bot
- Each user has separate configuration

## Troubleshooting

### "Failed to connect to node"

**Solutions:**
1. Check if `junocashd` is running
2. Verify host and port are correct
3. Check firewall settings
4. Ensure RPC is enabled

### "Cannot connect to node"

**Check connection:**
```bash
curl -X POST http://localhost:8232 -d '{"method":"getblockchaininfo"}' -H 'content-type:application/json'
```

### Bot doesn't respond

1. Check if bot is running
2. Verify Bot Token is correct
3. Check internet connection

## Running 24/7

### On VPS (Recommended)

**Using screen:**
```bash
screen -S junobot
python3 bot.py
# Press Ctrl+A then D to detach
```

**To reconnect:**
```bash
screen -r junobot
```

### As a Service (Linux)

Create `/etc/systemd/system/junobot.service`:

```ini
[Unit]
Description=Juno Cash Telegram Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 /path/to/bot/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable junobot
sudo systemctl start junobot
sudo systemctl status junobot
```

## Future Features

- 🔔 Push notifications when blocks are mined
- 💸 Send JUNO directly from Telegram
- 📊 Hashrate/balance charts
- 👥 Multi-node support per user
- 🔐 Encrypted credentials storage
- ⚡ Pool mining statistics
- 📈 Earnings calculator

## Support

- Telegram: Juno Cash Community
- GitHub: https://github.com/juno-cash/junocash
- Website: https://juno.cash

## License

MIT License - Free to use and modify

---

**Created by the Juno Cash Community** 💜
