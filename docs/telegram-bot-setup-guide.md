# Telegram Bot Setup Guide

This guide covers setting up the NotesApp Telegram bot for reminders and backup functionality.

## Developer Setup

### 1. Create Bot via BotFather

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow prompts to set bot name and username
4. Copy the **bot token** (format: `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`)

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. Set Up Webhook (Production)

For production, configure webhook to receive updates:

```bash
# Set webhook URL
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-api-domain.com/api/telegram/webhook"}'

# Verify webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

### 4. Webhook Endpoint

The backend exposes `POST /api/telegram/webhook` which handles:
- `/start <link_code>` - Link Telegram account
- `/todo <title>` - Create a todo
- `/list` - List active todos
- `/done <n>` - Mark todo as complete
- `/search <query>` - Search notes

## End-User Guide

### Linking Your Account

1. Go to **Settings** → **Telegram** in NotesApp
2. Click **"Tạo mã liên kết"** (Generate link code)
3. Open the bot: [@NotesAppX](https://t.me/notesappx_bot)
4. Send the command shown (e.g., `/start abc123`)
5. Bot confirms link success
6. Click **"Đã link xong → Refresh"** in Settings

### Using Reminders

Once linked, you'll receive Telegram notifications for:
- Todo reminders (set reminder time when creating todos)
- Upcoming deadlines

### Backup & Restore

#### Manual Backup
1. Go to **Settings** → **Telegram** → **Backup Settings**
2. Toggle **"Encrypt backup"** for E2E encryption (recommended)
3. Click **"Backup Now"**
4. Backup file is sent to your Telegram chat

#### Auto Backup
1. Enable **"Enable auto backup"**
2. Select schedule: **Daily** (3:00 UTC) or **Weekly** (Sunday 3:00 UTC)
3. Set retention: 3, 5, or 10 versions

#### Restore
1. Find your backup in the **Backups** list
2. Click **"Restore"**
3. For encrypted backups:
   - **Passkey (PRF)**: Uses your device passkey
   - **Password**: Enter the password used during backup
4. Data is merged (existing data preserved)

### Encryption Options

| Method | Security | Portability |
|--------|----------|-------------|
| **Passkey (PRF)** | Highest - tied to device | Same device only |
| **Password** | High - AES-256-GCM | Any device with password |
| **None** | Readable by anyone with access | Any device |

## Troubleshooting

### Bot Not Responding

1. Verify `TELEGRAM_BOT_TOKEN` is set correctly
2. Check webhook is configured (production)
3. Review backend logs for errors

### Link Code Expired

Link codes expire after 10 minutes. Generate a new one from Settings.

### Backup Failed

- **Rate limit**: Only 1 backup per hour allowed
- **Size limit**: Backup must be under 50 MB (Telegram limit)
- **Not linked**: Ensure Telegram is linked first

### Restore Failed

- **Wrong password**: For password-encrypted backups, ensure correct password
- **PRF mismatch**: PRF-encrypted backups require the same device/passkey used for backup
- **Rate limit**: Only 1 restore per hour

### Unlinking Account

1. Go to **Settings** → **Telegram**
2. Click **"Unlink"**
3. Confirm - you'll stop receiving reminders

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/telegram/link` | POST | Generate link code |
| `/api/telegram/unlink` | POST | Unlink account |
| `/api/telegram/status` | GET | Check link status |
| `/api/telegram/webhook` | POST | Receive bot updates |
| `/api/backup/trigger` | POST | Manual backup |
| `/api/backup/trigger/encrypted` | POST | Encrypted backup |
| `/api/backup/list` | GET | List backups |
| `/api/backup/settings` | GET/PUT | Backup settings |
| `/api/backup/{id}/restore` | POST | Restore backup |
| `/api/backup/{id}/download` | GET | Download for client decrypt |
| `/api/backup/import` | POST | Import decrypted data |
