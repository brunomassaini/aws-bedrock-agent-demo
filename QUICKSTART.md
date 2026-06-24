# Quick Start Guide

Get your Discord bot running in under 10 minutes!

## Prerequisites Check

✅ Docker installed: `docker --version`  
✅ AWS CLI configured: `aws sts get-caller-identity`  
✅ Bedrock Agent created in AWS (you have the Agent ID)

## Step 1: Get Discord Bot Token (2 minutes)

1. Go to https://discord.com/developers/applications
2. Click **"New Application"** → Name it → Click **"Create"**
3. Go to **"Bot"** tab → Click **"Reset Token"** → Copy the token
4. Enable **"Message Content Intent"** toggle
5. Go to **OAuth2 → URL Generator**:
   - Check `bot` scope
   - Check `Send Messages` and `Read Messages/View Channels` permissions
   - Copy the URL and open it to invite bot

## Step 2: Get Your Discord User ID (30 seconds)

1. Open Discord → Settings → Advanced → Enable **Developer Mode**
2. Right-click your profile → **Copy User ID**

## Step 3: Configure Environment (1 minute)

```bash
cd /home/sagemaker-user/aws-bedrock-agent-demo

# Copy template
cp .env.template .env

# Edit .env
vim .env
```

Fill in these 4 required values:
```bash
DISCORD_BOT_TOKEN=<paste from Step 1>
AUTHORIZED_USER_ID=<paste from Step 2>
LAMBDA_FUNCTION_NAME=BedrockDiscordStack-MessageProcessor9DB0E972-CYQ8zNPojKog
AWS_REGION=us-west-2
```

For AWS credentials, choose one:

**Option A**: Use your existing AWS credentials (easiest)
```bash
# The docker-compose.yml already mounts ~/.aws
# Just make sure: aws sts get-caller-identity works
```

**Option B**: Set explicit credentials in .env
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

## Step 4: Run the Bot (1 minute)

```bash
# Start bot
docker-compose up -d

# Check logs
docker-compose logs -f discord-bot
```

You should see:
```
Bot logged in as YourBotName (ID: ...)
Bot is ready and listening for messages!
```

## Step 5: Test It! (30 seconds)

1. Open Discord
2. Send a DM to your bot: "Hello!"
3. Bot should respond with a message from the Bedrock Agent

### Try these commands:
- `/status` - Check bot status
- `/ping` - Test latency
- `/help` - Show commands

## Troubleshooting

### Bot doesn't come online in Discord
```bash
# Check logs
docker-compose logs discord-bot

# Look for errors like "LoginFailure" (bad token) or "Unauthorized" (need Message Content Intent)
```

### Bot online but doesn't respond
```bash
# Verify user ID
echo $AUTHORIZED_USER_ID

# Check it matches your Discord user ID
# Right-click your profile in Discord → Copy User ID → Compare
```

### "Internal server error" from bot
```bash
# Test Lambda directly
aws lambda invoke \
  --function-name BedrockDiscordStack-MessageProcessor9DB0E972-CYQ8zNPojKog \
  --cli-binary-format raw-in-base64-out \
  --payload '{"user_id": "123", "message": "test"}' \
  --region us-west-2 \
  response.json

cat response.json
```

### AWS credential errors
```bash
# Test AWS credentials
aws sts get-caller-identity

# If this works, credentials are fine
# Make sure Lambda function exists in us-west-2:
aws lambda list-functions --region us-west-2 | grep MessageProcessor
```

## Next Steps

✅ Bot is running!

Now you can:
- Talk to your bot and test conversation context (10-minute sessions)
- Monitor costs: AWS Console → Billing Dashboard
- Check logs: `docker-compose logs -f discord-bot`
- Stop bot: `docker-compose down`
- Restart bot: `docker-compose restart discord-bot`

## Production Deployment

Want the bot to run 24/7 without your computer being on?

### Option 1: AWS ECS Fargate (~$5/month)
1. Push Docker image to ECR
2. Create ECS task definition
3. Create Fargate service with restart policy

### Option 2: EC2 / VPS
1. Deploy to EC2 instance or any VPS
2. Run `docker-compose up -d`
3. Bot auto-restarts on server reboot

### Option 3: Keep it local
Just leave it running on your computer!

## Full Documentation

- **[README.md](README.md)** - Project overview and architecture
- **[DISCORD_BOT_README.md](DISCORD_BOT_README.md)** - Detailed setup guide
- **[PRD.md](PRD.md)** - Product requirements and design decisions

## Support

**Logs**:
- Bot: `docker-compose logs -f discord-bot`
- Lambda: `aws logs tail /aws/lambda/BedrockDiscordStack-MessageProcessor --follow --region us-west-2`

**Common Issues**:
- Bot token invalid → Regenerate in Discord Developer Portal
- User not authorized → Double-check AUTHORIZED_USER_ID
- Lambda not found → Verify function name and region
- AWS access denied → Check IAM permissions for lambda:InvokeFunction

Happy chatting! 🤖💬
