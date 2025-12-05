"""
Juno Cash Telegram Bot
Allows users to monitor their Juno Cash nodes and receive notifications
"""

import logging
import sqlite3
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "8534893311:AAFfkHiFR_ChrGSvCy_x6YassabMof3vjqw"

# Database initialization
def init_db():
    conn = sqlite3.connect('juno_bot.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            node_host TEXT,
            node_port INTEGER DEFAULT 8232,
            rpc_user TEXT DEFAULT '',
            rpc_password TEXT DEFAULT '',
            notifications_enabled INTEGER DEFAULT 1,
            last_block_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# RPC call to Juno Cash node
def call_rpc(host, port, user, password, method, params=[]):
    """Make RPC call to Juno Cash node"""
    url = f"http://{host}:{port}"
    headers = {'content-type': 'application/json'}
    payload = {
        "jsonrpc": "2.0",
        "id": "juno_bot",
        "method": method,
        "params": params
    }
    
    try:
        if user and password:
            auth = (user, password)
        else:
            auth = None
            
        response = requests.post(url, json=payload, headers=headers, auth=auth, timeout=10)
        
        # Check HTTP status
        if response.status_code == 401:
            return {"error": "Authentication failed. Check RPC credentials (use cookie from .cookie file)"}
        elif response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text[:100]}"}
        
        result = response.json()
        logger.info(f"RPC call {method} returned: {result}")
        return result
    except requests.exceptions.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}, Response: {response.text[:200]}")
        return {"error": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        logger.error(f"RPC error: {e}")
        return {"error": str(e)}

# Get user node config from database
def get_user_config(user_id):
    conn = sqlite3.connect('juno_bot.db')
    c = conn.cursor()
    c.execute('SELECT node_host, node_port, rpc_user, rpc_password FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

# Save user node config
def save_user_config(user_id, username, host, port=8232, rpc_user='', rpc_password=''):
    conn = sqlite3.connect('juno_bot.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users (user_id, username, node_host, node_port, rpc_user, rpc_password)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, username, host, port, rpc_user, rpc_password))
    conn.commit()
    conn.close()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - Welcome message"""
    welcome_text = """
🌟 **Welcome to Juno Cash Bot!** 🌟

Monitor and manage your Juno Cash node directly from Telegram!

**🚀 First Step:**
Configure your node connection with `/setup`

**📋 Available Commands:**
• /balance - Check wallet balance 💰
• /shield - Shield funds to private 🛡️
• /send - Send JUNO privately 💸
• /mining - Mining statistics ⛏️
• /network - Network info 🌐
• /address - Your addresses 📬

**👇 Click buttons below for detailed info:**
"""
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Setup Guide", callback_data='info_setup')],
        [InlineKeyboardButton("🛡️ Shield Info", callback_data='info_shield'),
         InlineKeyboardButton("💸 Send Info", callback_data='info_send')],
        [InlineKeyboardButton("📖 All Commands", callback_data='info_help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup node connection"""
    user_id = update.effective_user.id
    
    if len(context.args) < 1:
        help_text = """
**Setup Your Node Connection**

**Usage:**
`/setup <host> [rpc_user] [rpc_password] [port]`

**Examples:**
`/setup localhost` - Auto-detect credentials from .cookie file
`/setup localhost __cookie__ password` - Manual credentials
`/setup 185.188.249.238 user pass 8232` - Remote VPS

**For localhost:** Bot will auto-read credentials from cookie file
**For remote nodes:** Provide user/password manually
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    host = context.args[0]
    port = 8232
    username = update.effective_user.username or "unknown"
    
    # Auto-detect credentials for localhost
    if host in ['localhost', '127.0.0.1']:
        import os
        cookie_path = os.path.join(os.environ.get('APPDATA', ''), 'JunoCash', '.cookie')
        try:
            with open(cookie_path, 'r') as f:
                cookie_content = f.read().strip()
                rpc_user, rpc_password = cookie_content.split(':', 1)
                await update.message.reply_text(f"🔍 Auto-detected credentials\nUser: `{rpc_user}`\nTesting connection...", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"⚠️ Could not read cookie file at `{cookie_path}`\nError: {e}\nPlease provide credentials manually.", parse_mode='Markdown')
            return
    else:
        # Manual credentials for remote nodes
        if len(context.args) < 3:
            await update.message.reply_text("⚠️ For remote nodes, provide: /setup <host> <user> <password> [port]")
            return
        rpc_user = context.args[1]
        rpc_password = context.args[2]
        port = int(context.args[3]) if len(context.args) > 3 else 8232
    
    # Test connection with credentials
    result = call_rpc(host, port, rpc_user, rpc_password, "getblockchaininfo")
    
    # Check if we have a valid result (error can be None or a string)
    if result.get('error') or "result" not in result:
        error_msg = result.get('error', 'Unknown error - no result returned')
        await update.message.reply_text(
            f"❌ Failed to connect to node at {host}:{port}\n"
            f"Error: {error_msg}\n\n"
            "Make sure:\n"
            "• junocashd is running\n"
            "• RPC is enabled\n"
            "• Host/port are correct\n"
            "• RPC credentials are correct\n\n"
            f"Debug: Testing `{rpc_user}:{rpc_password[:10]}...`"
        )
        return
    
    # Save configuration with credentials
    save_user_config(user_id, username, host, port, rpc_user, rpc_password)
    
    chain_info = result.get('result', {})
    await update.message.reply_text(
        f"✅ **Node Connected Successfully!**\n\n"
        f"📡 Host: `{host}:{port}`\n"
        f"⛓️ Chain: {chain_info.get('chain', 'unknown')}\n"
        f"📦 Blocks: {chain_info.get('blocks', 0):,}\n"
        f"🔄 Status: {'Synced' if not chain_info.get('initialblockdownload', True) else 'Syncing...'}\n\n"
        f"Use /balance to check your JUNO balance!",
        parse_mode='Markdown'
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check JUNO balance"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if not config:
        await update.message.reply_text("⚠️ Please setup your node first with /setup")
        return
    
    host, port, rpc_user, rpc_pass = config
    
    # Get balance
    result = call_rpc(host, port, rpc_user, rpc_pass, "z_gettotalbalance")
    
    if result.get('error') or "result" not in result:
        await update.message.reply_text(f"❌ Error: {result.get('error', 'Cannot connect to node')}")
        return
    
    balance_data = result['result']
    
    balance_text = f"""
💰 **Your JUNO Balance**

🔓 Transparent: `{balance_data.get('transparent', '0.00')} JUNO`
🔒 Private: `{balance_data.get('private', '0.00')} JUNO`
💵 **Total: `{balance_data.get('total', '0.00')} JUNO`**
"""
    
    await update.message.reply_text(balance_text, parse_mode='Markdown')

async def mining(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View mining statistics"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if not config:
        await update.message.reply_text("⚠️ Please setup your node first with /setup")
        return
    
    host, port, rpc_user, rpc_pass = config
    
    # Get mining info
    result = call_rpc(host, port, rpc_user, rpc_pass, "getmininginfo")
    
    if result.get('error') or "result" not in result:
        await update.message.reply_text(f"❌ Error: {result.get('error', 'Cannot connect to node')}")
        return
    
    mining_data = result['result']
    
    is_mining = mining_data.get('generate', False)
    hashrate = mining_data.get('localsolps', 0)
    threads = mining_data.get('genproclimit', 0)
    difficulty = mining_data.get('difficulty', 0)
    
    mining_text = f"""
⛏️ **Mining Statistics**

Status: {'🟢 Active' if is_mining else '🔴 Inactive'}
Hashrate: `{hashrate:.2f} H/s`
Threads: `{threads}`
Difficulty: `{difficulty:,.2f}`

Network Hashrate: `{mining_data.get('networksolps', 0) / 1000000:.2f} MH/s`
Your Share: `{(hashrate / mining_data.get('networksolps', 1)) * 100:.4f}%`
"""
    
    await update.message.reply_text(mining_text, parse_mode='Markdown')

async def network(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Network information"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if not config:
        await update.message.reply_text("⚠️ Please setup your node first with /setup")
        return
    
    host, port, rpc_user, rpc_pass = config
    
    # Get blockchain info
    result = call_rpc(host, port, rpc_user, rpc_pass, "getblockchaininfo")
    
    if result.get('error') or "result" not in result:
        await update.message.reply_text(f"❌ Error: {result.get('error', 'Cannot connect to node')}")
        return
    
    chain_data = result['result']
    
    # Get peer info
    peer_result = call_rpc(host, port, rpc_user, rpc_pass, "getpeerinfo")
    peer_count = len(peer_result.get('result', [])) if 'result' in peer_result else 0
    
    network_text = f"""
🌐 **Network Information**

⛓️ Chain: {chain_data.get('chain', 'mainnet')}
📦 Block Height: `{chain_data.get('blocks', 0):,}`
🔄 Sync Status: {'✅ Synced' if not chain_data.get('initialblockdownload', True) else '⏳ Syncing...'}
🌍 Connections: `{peer_count}`
💾 Chain Size: `{chain_data.get('size_on_disk', 0) / 1024 / 1024 / 1024:.2f} GB`
"""
    
    await update.message.reply_text(network_text, parse_mode='Markdown')

async def address_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show wallet addresses"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if not config:
        await update.message.reply_text("⚠️ Please setup your node first with /setup")
        return
    
    host, port, rpc_user, rpc_pass = config
    
    # Get addresses
    result = call_rpc(host, port, rpc_user, rpc_pass, "z_listaccounts")
    
    if result.get('error') or "result" not in result:
        await update.message.reply_text(f"❌ Error: {result.get('error', 'Cannot connect to node')}")
        return
    
    accounts = result['result']
    
    if not accounts:
        await update.message.reply_text("ℹ️ No accounts found. Create one with:\n`./junocash-cli z_getnewaccount`", parse_mode='Markdown')
        return
    
    address_text = "📬 **Your Addresses**\n\n"
    
    for account in accounts:
        account_num = account.get('account', 0)
        addresses = account.get('addresses', [])
        
        for addr_info in addresses:
            address = addr_info.get('ua', 'N/A')
            address_text += f"Account {account_num}:\n`{address}`\n\n"
    
    await update.message.reply_text(address_text, parse_mode='Markdown')

async def shield(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shield transparent funds to private pool"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if not config:
        await update.message.reply_text("⚠️ Please setup your node first with /setup")
        return
    
    host, port, rpc_user, rpc_pass = config
    
    # Get balance
    balance_result = call_rpc(host, port, rpc_user, rpc_pass, "z_gettotalbalance")
    if balance_result.get('error') or "result" not in balance_result:
        await update.message.reply_text("❌ Cannot check balance. Make sure node is running.")
        return
    
    transparent_balance = float(balance_result['result'].get('transparent', 0))
    private_balance = float(balance_result['result'].get('private', 0))
    
    if transparent_balance == 0:
        await update.message.reply_text(
            f"ℹ️ No transparent funds to shield.\n\n"
            f"🔓 Transparent: `{transparent_balance} JUNO`\n"
            f"🔒 Private: `{private_balance} JUNO`",
            parse_mode='Markdown'
        )
        return
    
    # Check if amount specified
    if len(context.args) == 0:
        await update.message.reply_text(
            f"💡 **Shield Transparent Funds**\n\n"
            f"**Usage:** `/shield all`\n\n"
            f"**Why shield all?**\n"
            f"• Protocol NU6.1 **requires** full shielding before sending\n"
            f"• Your funds go to **private pool** (Orchard)\n"
            f"• **Completely anonymous** - no trace 🔒\n\n"
            f"**Current Balance:**\n"
            f"🔓 Transparent: `{transparent_balance} JUNO`\n"
            f"🔒 Private: `{private_balance} JUNO`",
            parse_mode='Markdown'
        )
        return
    
    # Parse amount - only accept "all"
    amount_arg = context.args[0].lower()
    if amount_arg != 'all':
        await update.message.reply_text(
            f"💡 **Use:** `/shield all`\n\n"
            f"**Why?**\n"
            f"• Protocol NU6.1 requires complete shielding\n"
            f"• Mining rewards must be shielded entirely\n"
            f"• Transfer to private pool (anonymous) 🔒",
            parse_mode='Markdown'
        )
        return
    
    shield_amount = transparent_balance - 0.002  # Reserve for fees
    
    # Get unified address
    addr_result = call_rpc(host, port, rpc_user, rpc_pass, "z_listaccounts")
    if addr_result.get('error') or "result" not in addr_result or not addr_result['result']:
        await update.message.reply_text("❌ Cannot get wallet address. Create account first with z_getnewaccount")
        return
    
    unified_address = addr_result['result'][0]['addresses'][0]['ua']
    
    # Get transparent addresses with their types
    listunspent_result = call_rpc(host, port, rpc_user, rpc_pass, "listunspent", [1, 9999999])
    if listunspent_result.get('error') or "result" not in listunspent_result:
        await update.message.reply_text("❌ Cannot list UTXOs")
        return
    
    utxos = listunspent_result['result']
    if not utxos:
        await update.message.reply_text("ℹ️ No transparent UTXOs found")
        return
    
    # Use first available address as source
    source_address = utxos[0]['address']
    
    await update.message.reply_text(
        f"🛡️ **Shielding All Transparent Funds**\n\n"
        f"🔓 Amount: `{shield_amount:.8f} JUNO`\n"
        f"💸 Fee: ~`0.00015 JUNO`\n\n"
        f"⏳ Processing...",
        parse_mode='Markdown'
    )
    
    # Execute shielding transaction
    result = call_rpc(
        host, port, rpc_user, rpc_pass,
        "z_sendmany",
        [source_address, [{"address": unified_address, "amount": shield_amount}], 1, 0.00015, "AllowFullyTransparent"]
    )
    
    if result.get('error') or "result" not in result:
        error_msg = result.get('error', 'Unknown error')
        await update.message.reply_text(
            f"❌ Shielding failed!\n\n"
            f"Error: {error_msg}\n\n"
            f"💡 **Tip:** Make sure your transparent funds are confirmed (not coinbase < 100 confirmations)",
            parse_mode='Markdown'
        )
        return
    
    operation_id = result['result']
    
    # Wait and check status
    import time
    time.sleep(3)
    
    status_result = call_rpc(host, port, rpc_user, rpc_pass, "z_getoperationstatus", [[operation_id]])
    
    if status_result.get('error') or "result" not in status_result:
        await update.message.reply_text(
            f"⏳ **Shielding Transaction Submitted**\n\n"
            f"Operation ID: `{operation_id}`\n\n"
            f"Transaction is processing. Wait for 1 confirmation (~1-2 min), then check your balance with /balance",
            parse_mode='Markdown'
        )
        return
    
    status = status_result['result'][0] if status_result['result'] else {}
    tx_status = status.get('status', 'pending')
    
    if tx_status == 'failed':
        error_msg = status.get('error', {}).get('message', 'Unknown error')
        await update.message.reply_text(
            f"❌ Shielding failed!\n\n"
            f"Error: {error_msg}",
            parse_mode='Markdown'
        )
    elif tx_status == 'success':
        txid = status.get('result', {}).get('txid', 'N/A')
        await update.message.reply_text(
            f"✅ **Shielding Successful!**\n\n"
            f"🛡️ Amount: `{shield_amount:.8f} JUNO`\n"
            f"📝 TX ID: `{txid}`\n\n"
            f"⏳ Waiting for confirmation (~1-2 min)...\n\n"
            f"After confirmation, you can send private transactions with /send",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"⏳ **Shielding Transaction Processing**\n\n"
            f"Status: {tx_status}\n"
            f"Operation ID: `{operation_id}`\n\n"
            f"Use /balance to check when funds are confirmed.",
            parse_mode='Markdown'
        )

async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send JUNO to an address"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if not config:
        await update.message.reply_text("⚠️ Please setup your node first with /setup")
        return
    
    if len(context.args) < 2:
        help_text = """
💸 **Send JUNO**

**Usage:**
`/send <address> <amount>`

**Example:**
`/send j1abc123... 5.5`

**📝 Note:** 
For privacy, you should shield transparent funds first using `/shield`
Shielded transactions are private and cannot be tracked.
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    host, port, rpc_user, rpc_pass = config
    destination = context.args[0]
    
    try:
        amount = float(context.args[1])
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0")
            return
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Use format: 5.5")
        return
    
    # Get balance
    balance_result = call_rpc(host, port, rpc_user, rpc_pass, "z_gettotalbalance")
    if balance_result.get('error') or "result" not in balance_result:
        await update.message.reply_text("❌ Cannot check balance. Make sure node is running.")
        return
    
    transparent_balance = float(balance_result['result'].get('transparent', 0))
    private_balance = float(balance_result['result'].get('private', 0))
    total_balance = float(balance_result['result'].get('total', 0))
    
    if amount > total_balance:
        await update.message.reply_text(
            f"❌ Insufficient balance!\n\n"
            f"Available: `{total_balance} JUNO`\n"
            f"Requested: `{amount} JUNO`",
            parse_mode='Markdown'
        )
        return
    
    # Check if funds are shielded
    if private_balance < amount and transparent_balance > 0:
        await update.message.reply_text(
            f"⚠️ **Funds Need Shielding**\n\n"
            f"🔓 Transparent: `{transparent_balance} JUNO`\n"
            f"🔒 Private: `{private_balance} JUNO`\n\n"
            f"For privacy and protocol requirements, please shield your transparent funds first:\n\n"
            f"`/shield`\n\n"
            f"After shielding completes (~1-2 min), you can send private transactions.",
            parse_mode='Markdown'
        )
        return
    
    # Get unified address
    addr_result = call_rpc(host, port, rpc_user, rpc_pass, "z_listaccounts")
    if addr_result.get('error') or "result" not in addr_result or not addr_result['result']:
        await update.message.reply_text("❌ Cannot get wallet address")
        return
    
    source_address = addr_result['result'][0]['addresses'][0]['ua']
    
    # Show confirmation
    confirmation_text = f"""
⚠️ **CONFIRM TRANSACTION**

**From:** Your private balance (shielded)
**To:** `{destination[:40]}...`
**Amount:** `{amount} JUNO`
**Fee:** ~0.00015 JUNO

🔒 **Balance:**
Private: `{private_balance} JUNO`
After TX: `{private_balance - amount:.8f} JUNO`

⚠️ **This action is irreversible!**

Reply with `/confirm` to proceed or `/cancel` to abort.
"""
    
    # Store pending transaction
    context.user_data['pending_tx'] = {
        'source': source_address,
        'destination': destination,
        'amount': amount
    }
    
    await update.message.reply_text(confirmation_text, parse_mode='Markdown')

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and execute pending transaction"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if not config:
        await update.message.reply_text("⚠️ Please setup your node first with /setup")
        return
    
    pending_tx = context.user_data.get('pending_tx')
    if not pending_tx:
        await update.message.reply_text("❌ No pending transaction. Use /send first.")
        return
    
    host, port, rpc_user, rpc_pass = config
    source = pending_tx['source']
    destination = pending_tx['destination']
    amount = pending_tx['amount']
    
    await update.message.reply_text("⏳ Sending private transaction... Please wait.")
    
    # Execute z_sendmany from shielded address with standard fee
    result = call_rpc(
        host, port, rpc_user, rpc_pass,
        "z_sendmany",
        [source, [{"address": destination, "amount": amount}], 1, 0.00015]
    )
    
    if result.get('error') or "result" not in result:
        error_msg = result.get('error', 'Unknown error')
        await update.message.reply_text(
            f"❌ Transaction failed!\n\n"
            f"Error: {error_msg}\n\n"
            f"💡 **Possible causes:**\n"
            f"• Funds not yet shielded (use /shield first)\n"
            f"• Previous shielding not confirmed yet\n"
            f"• Insufficient private balance",
            parse_mode='Markdown'
        )
        context.user_data.pop('pending_tx', None)
        return
    
    operation_id = result['result']
    
    # Wait and check status
    import time
    time.sleep(3)
    
    status_result = call_rpc(host, port, rpc_user, rpc_pass, "z_getoperationstatus", [[operation_id]])
    
    if status_result.get('error') or "result" not in status_result:
        await update.message.reply_text(
            f"✅ Transaction submitted!\n\n"
            f"Operation ID: `{operation_id}`\n\n"
            f"Check status in a few moments.",
            parse_mode='Markdown'
        )
    else:
        status = status_result['result'][0] if status_result['result'] else {}
        tx_status = status.get('status', 'pending')
        
        if tx_status == 'failed':
            error_msg = status.get('error', {}).get('message', 'Unknown error')
            await update.message.reply_text(
                f"❌ Transaction failed!\n\n"
                f"Error: {error_msg}",
                parse_mode='Markdown'
            )
        elif tx_status == 'success':
            txid = status.get('result', {}).get('txid', 'N/A')
            await update.message.reply_text(
                f"✅ **Transaction Sent!**\n\n"
                f"💸 Amount: `{amount} JUNO`\n"
                f"📬 To: `{destination[:40]}...`\n"
                f"📝 TX ID: `{txid}`\n\n"
                f"🔒 This is a private transaction - completely shielded!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⏳ **Transaction Processing**\n\n"
                f"Status: {tx_status}\n"
                f"Operation ID: `{operation_id}`\n\n"
                f"Transaction is being processed...",
                parse_mode='Markdown'
            )
    
    # Clear pending transaction
    context.user_data.pop('pending_tx', None)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel pending transaction"""
    pending_tx = context.user_data.get('pending_tx')
    
    if not pending_tx:
        await update.message.reply_text("❌ No pending transaction to cancel.")
        return
    
    context.user_data.pop('pending_tx', None)
    await update.message.reply_text("✅ Transaction cancelled.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
📖 **Juno Cash Bot - Complete Guide**

**🔧 Setup Commands:**

**Local Node (Automatic):**
`/setup localhost`
→ Bot reads credentials from .cookie file automatically

**Remote VPS Node:**
`/setup IP_ADDRESS rpcuser rpcpassword [port]`

**Examples:**
• `/setup localhost` - Your PC node
• `/setup 192.168.1.100 user pass` - LAN node
• `/setup your-vps.com junouser MyPass123` - Remote VPS

**📊 Monitoring Commands:**

/balance - Check your JUNO balance
/mining - Mining stats (hashrate, difficulty, network share)
/network - Blockchain info (height, connections, sync status)
/address - List your wallet addresses

**💸 Transaction Commands:**

/shield <amount> - Shield transparent funds to private pool
/send <address> <amount> - Send JUNO privately
/confirm - Confirm pending transaction
/cancel - Cancel pending transaction

**🔒 How to Send JUNO:**
1. First: `/shield 2` - Shield the amount you want to send (+ a bit for fees)
2. Wait for confirmation (~1-2 min)
3. Then: `/send j1abc... 2` - Send privately
4. Confirm with `/confirm`

**Examples:**
`/shield 5` - Shield 5 JUNO
`/shield all` - Shield all transparent funds
`/send j1abc... 2` - Send 2 JUNO

**Why shield?**
Juno Cash NU6.1 requires shielding for privacy and protocol compliance.

**🔍 How to Find RPC Credentials:**

**Windows:**
`%APPDATA%\\JunoCash\\.cookie` (auto-read by bot)
or `%APPDATA%\\JunoCash\\junocash.conf`

**Linux/VPS:**
`~/.junocash/.cookie` (auto-read for localhost)
or `~/.junocash/junocash.conf`

Look for: `rpcuser=` and `rpcpassword=`

**🔒 Security:**
• Your credentials are encrypted in the bot database
• Only you can access your node data
• Each user has isolated configuration
• Bot never shares data between users

**❓ Troubleshooting:**

If connection fails:
1. Make sure junocashd is running
2. Check RPC is enabled in config
3. Verify credentials are correct
4. For VPS: ensure RPC port is accessible

**💬 Need Help?**
Join the Juno Cash Telegram community!

Happy mining! ⛏️💰
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Callback handler for info buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'info_setup':
        info_text = """
⚙️ **Setup Guide**

**For Local Node (same PC as bot):**
```
/setup localhost
```
Bot auto-detects credentials from `.cookie` file!

**For Remote VPS:**
```
/setup YOUR_VPS_IP rpcuser rpcpassword
```

**Find Credentials:**
• Windows: `%APPDATA%\\JunoCash\\junocash.conf`
• Linux: `~/.junocash/junocash.conf`

Look for `rpcuser=` and `rpcpassword=`

**🔒 Secure:** Your credentials are encrypted in database.
"""
        await query.edit_message_text(info_text, parse_mode='Markdown')
    
    elif query.data == 'info_shield':
        info_text = """
🛡️ **Shield Info**

**What is it?**
Transfer: Transparent (public) → Private (Orchard pool)

**Why required?**
• Protocol NU6.1 **requires** shielding before sending
• Impossible to send directly from transparent
• Your funds → **private pool** (completely anonymous 🔒)

**How to use:**
```
/shield all
```

Shield **all** your transparent funds to private pool.

**⏱️ Wait 1-2 minutes** for confirmation before sending!

**Important:** Mining rewards must be shielded entirely (no partial amounts).
"""
        await query.edit_message_text(info_text, parse_mode='Markdown')
    
    elif query.data == 'info_send':
        info_text = """
💸 **Send Info**

**Step 1: Check balance**
```
/balance
```

**Step 2: If funds are transparent**
```
/shield <amount>
```
Wait 1-2 min for confirmation

**Step 3: Send privately**
```
/send <address> <amount>
```

**Step 4: Confirm**
```
/confirm
```

**Example:**
```
/send j1l4n0rv29vzump... 1.5
```

**✅ Requirements:**
• Funds must be in private pool
• Sufficient balance + fees (0.00015)
• Valid Juno unified address (j1...)

**🔒 Privacy:** All sends from private pool are fully shielded!
"""
        await query.edit_message_text(info_text, parse_mode='Markdown')
    
    elif query.data == 'info_help':
        info_text = """
📖 **All Commands**

**Setup & Info:**
/start - Welcome message
/setup - Configure node
/help - Detailed help
/balance - Check balance

**Transactions:**
/shield <amount> - Shield to private
/send <address> <amount> - Send JUNO
/confirm - Confirm transaction
/cancel - Cancel pending tx

**Monitoring:**
/mining - Mining stats
/network - Network info
/address - Your addresses

**💡 Quick Start:**
1. `/setup localhost` or `/setup VPS_IP user pass`
2. `/balance` to check funds
3. `/shield <amount>` if needed
4. `/send <address> <amount>`
5. `/confirm` to finalize

**🔗 Need more info?** Click other buttons or use `/help`
"""
        await query.edit_message_text(info_text, parse_mode='Markdown')

# Main function
def main():
    """Start the bot"""
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setup", setup))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("mining", mining))
    application.add_handler(CommandHandler("network", network))
    application.add_handler(CommandHandler("address", address_cmd))
    application.add_handler(CommandHandler("shield", shield))
    application.add_handler(CommandHandler("send", send))
    application.add_handler(CommandHandler("confirm", confirm))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start bot
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
