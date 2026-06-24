# Setup Checklist

Use this checklist to get your Discord bot running!

## ✅ Prerequisites (Already Done)

- [x] AWS Account configured
- [x] Bedrock Agent created (ID: JLD5FDHXV6)
- [x] Lambda function deployed to us-west-2
- [x] Infrastructure tested and working
- [x] Docker installed on your machine

## 📋 Setup Steps (Your Turn!)

### Step 1: Create Discord Bot (5 minutes)

- [ ] Go to https://discord.com/developers/applications
- [ ] Click "New Application" and give it a name
- [ ] Go to "Bot" tab
- [ ] Click "Reset Token" and **copy the token** (save it somewhere)
- [ ] Enable "Message Content Intent" toggle
- [ ] Go to OAuth2 → URL Generator:
  - [ ] Check `bot` scope
  - [ ] Check `Send Messages` and `Read Messages/View Channels` permissions
  - [ ] Copy the generated URL
  - [ ] Open URL in browser to invite bot

### Step 2: Get Your Discord User ID (1 minute)

- [ ] Open Discord
- [ ] Go to Settings → Advanced
- [ ] Enable "Developer Mode"
- [ ] Close settings
- [ ] Right-click your profile picture
- [ ] Click "Copy User ID"
- [ ] **Save this ID** (it's a long number like 123456789012345678)

### Step 3: Configure Environment (2 minutes)

```bash
cd /home/sagemaker-user/aws-bedrock-agent-demo
```

- [ ] Copy template: `cp .env.template .env`
- [ ] Edit .env: `vim .env` or `nano .env`
- [ ] Fill in these values:

```bash
DISCORD_BOT_TOKEN=<paste token from Step 1>
AUTHORIZED_USER_ID=<paste user ID from Step 2>
LAMBDA_FUNCTION_NAME=BedrockDiscordStack-MessageProcessor9DB0E972-CYQ8zNPojKog
AWS_REGION=us-west-2
```

- [ ] Save the file (in vim: press `Esc`, type `:wq`, press Enter)

**Note**: AWS credentials should already work (using ~/.aws/credentials mounted in Docker)

### Step 4: Start the Bot (1 minute)

```bash
# Make sure Docker is running
docker --version

# Start the bot
docker-compose up -d

# Check logs
docker-compose logs -f discord-bot
```

- [ ] Run `docker-compose up -d`
- [ ] Check logs show: "Bot is ready and listening for messages!"
- [ ] No error messages in logs

### Step 5: Test the Bot (2 minutes)

- [ ] Open Discord
- [ ] Find your bot in the DM list (it should show as online/green)
- [ ] Send a DM: "Hello!"
- [ ] Bot responds with a message from Bedrock Agent
- [ ] Try: `/status` command
- [ ] Try: `/ping` command
- [ ] Try: `/help` command

## 🎉 Success Criteria

Your bot is working correctly if:

- ✅ Bot shows as online (green) in Discord
- ✅ Bot responds to your DMs
- ✅ `/status` command shows session info
- ✅ No error messages in logs
- ✅ Conversation context maintained (ask follow-up questions)

## 🔧 Troubleshooting

### Bot doesn't come online
```bash
# Check logs for errors
docker-compose logs discord-bot

# Common issues:
# - "LoginFailure" → Bot token is wrong, regenerate in Discord portal
# - "Unauthorized" → Enable "Message Content Intent" in Discord portal
```

### Bot online but doesn't respond
```bash
# Verify your user ID
echo $AUTHORIZED_USER_ID

# Compare with your actual Discord user ID
# Right-click profile → Copy ID → should match
```

### "You are not authorized" message
- Your AUTHORIZED_USER_ID doesn't match your actual Discord user ID
- Copy ID again: Settings → Advanced → Developer Mode → Right-click profile → Copy ID
- Update .env and restart: `docker-compose restart discord-bot`

### AWS/Lambda errors
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

### View detailed logs
```bash
# Bot logs
docker-compose logs -f discord-bot

# Lambda logs
aws logs tail /aws/lambda/BedrockDiscordStack-MessageProcessor --follow --region us-west-2

# Stop bot
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## 📚 Next Steps After Setup

Once your bot is working:

1. **Test Conversation Context**
   - Send multiple messages
   - Ask follow-up questions
   - Verify the agent remembers context

2. **Monitor Costs**
   - Check AWS Billing Dashboard
   - Set up a billing alarm

3. **Explore Features**
   - Try different questions
   - Test slash commands
   - See how long the 10-minute context window works

4. **Optional: Deploy 24/7**
   - See DISCORD_BOT_README.md for production deployment options
   - Deploy to ECS Fargate for always-on availability

## 🆘 Need Help?

1. Check the logs: `docker-compose logs -f discord-bot`
2. Read DISCORD_BOT_README.md for detailed troubleshooting
3. Read QUICKSTART.md for common issues
4. Verify all environment variables in .env are correct
5. Test Lambda function directly (command above)

## 📊 Monitoring

### Check Bot Status
```bash
# View logs
docker-compose logs -f discord-bot

# Check if bot is running
docker-compose ps

# Restart bot
docker-compose restart discord-bot
```

### Check AWS Usage
```bash
# Lambda invocations today
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=BedrockDiscordStack-MessageProcessor9DB0E972-CYQ8zNPojKog \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum \
  --region us-west-2
```

## ✨ You're All Set!

Once you complete this checklist, you'll have a fully functional Discord bot powered by AWS Bedrock!

**Estimated setup time**: 10-15 minutes  
**Monthly cost**: ~$7-17 (depending on usage)  
**Fun factor**: 🚀🚀🚀

Happy chatting with your AI assistant! 🤖💬
