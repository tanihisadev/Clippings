# Notification Setup

Clippings supports three notification channels. Pick one and configure it below.

## Discord

Clippings uses a Discord **bot** (not a webhook) so it can react to your feedback on individual articles.

### Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** → name it "Clippings"
3. Go to **Bot** in the left sidebar
4. Click **Reset Token** → **Yes, do it!** → copy the token
5. Scroll down to **Privileged Gateway Intents** → toggle on:
   - **Message Content Intent**
   - **Server Members Intent**
6. Save Changes
7. Invite the bot to your server:
   ```
   https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=139586825280&scope=bot
   ```
   Find `YOUR_CLIENT_ID` on the **OAuth2 → General** page.

### Get Channel ID

1. In Discord → User Settings → Advanced → enable **Developer Mode**
2. Right-click the channel you want digests posted in
3. Click **Copy Channel ID**

### Configure

```yaml
notifier:
  type: discord
  discord_bot_token: "MTIz..."
  discord_channel_id: 123456789012345678
  discord_ping: "everyone"
```

`discord_ping` options:
- `"everyone"` — pings @everyone
- `"here"` — pings @here (online members only)
- `"<@USER_ID>"` — pings a specific user
- `"<@&ROLE_ID>"` — pings a role
- `""` — no ping

### Channel Permissions

If the bot can't post to a channel, check:
1. Channel settings → Permissions → find the bot's role
2. Ensure **View Channel**, **Send Messages**, **Add Reactions** are allowed

## ntfy.sh

The simplest option — no auth needed.

```yaml
notifier:
  type: ntfy
  ntfy_topic: "my-clippings"
```

Messages go to `https://ntfy.sh/my-clippings`. Use a unique topic name.

For a self-hosted ntfy instance:
```yaml
notifier:
  type: ntfy
  ntfy_url: "https://ntfy.yourdomain.com"
  ntfy_topic: "my-clippings"
```

## Telegram

```yaml
notifier:
  type: telegram
  telegram_bot_token: "123456:ABC-..."
  telegram_chat_id: "123456789"
```

### Setup

1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → follow prompts
2. Copy the bot token
3. Message [@userinfobot](https://t.me/userinfobot) → get your chat ID
4. Add the bot to a group or start a DM with it
