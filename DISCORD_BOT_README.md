# Discord Bot Setup Guide

This guide will help you set up and run the Discord bot locally using Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- Discord Developer account
- AWS account with deployed Lambda function (from CDK deployment)
- AWS credentials with permissions to invoke Lambda

## Step 1: Create Discord Bot Application

1. Go to https://discord.com/developers/applications
2. Click **"New Application"**
3. Give it a name (e.g., "Personal Assistant")
4. Go to the **"Bot"** section in the left sidebar
5. Click **"Add Bot"**
6. Under **"Privileged Gateway Intents"**, enable:
   - ✅ **Message Content Intent** (required to read DM content)
7. Click **"Reset Token"** and copy the bot token (you'll need this for `.env`)
8. Go to **OAuth2 → URL Generator**:
   - **Scopes**: Select `bot`
   - **Bot Permissions**: Select:
     - `Send Messages`
     - `Read Messages/View Channels`
     - `Read Message History`
9. Copy the generated URL and open it in your browser to invite the bot to your account

## Step 2: Get Your Discord User ID

1. Open Discord
2. Go to **User Settings → Advanced**
3. Enable **Developer Mode**
4. Right-click on your profile picture
5. Click **"Copy User ID"**
6. Save this ID - you'll need it for `.env`

## Step 3: Configure Environment Variables

1. Copy the template file:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and fill in the values:

   ```bash
   # Discord Configuration
   DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_FROM_STEP_1
   AUTHORIZED_USER_ID=YOUR_USER_ID_FROM_STEP_2
   
   # AWS Lambda Configuration
   LAMBDA_FUNCTION_NAME=BedrockDiscordStack-MessageProcessor9DB0E972-CYQ8zNPojKog
   AWS_REGION=us-west-2
   
   # AWS Credentials (choose one option below)
   
   # Option A: Use IAM user credentials
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   
   # Option B: If using AWS SSO or temporary credentials
   # AWS_SESSION_TOKEN=your_session_token
   ```

### Getting AWS Credentials

**Option A: IAM User Credentials (Recommended for local development)**

1. Go to AWS IAM Console
2. Create a new user or use existing
3. Attach policy: `AWSLambdaRole` or create custom policy:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "lambda:InvokeFunction",
         "Resource": "arn:aws:lambda:us-west-2:*:function:BedrockDiscordStack-MessageProcessor*"
       }
     ]
   }
   ```
4. Create access key and copy the credentials

**Option B: Use existing AWS credentials**

If you have AWS CLI configured (`~/.aws/credentials`), the Docker container will automatically mount and use those credentials. You can skip setting `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`.

## Step 4: Run the Bot

### Using Docker Compose (Recommended)

```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f discord-bot

# Stop the bot
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Manual Docker Build (Alternative)

```bash
# Build the image
docker build -t bedrock-discord-bot .

# Run the container
docker run -d \
  --name bedrock-discord-bot \
  --env-file .env \
  -v ~/.aws:/root/.aws:ro \
  bedrock-discord-bot

# View logs
docker logs -f bedrock-discord-bot

# Stop the container
docker stop bedrock-discord-bot
docker rm bedrock-discord-bot
```

## Step 5: Test the Bot

1. Open Discord and send a DM to your bot
2. Try these commands:
   - `/status` - Check bot status
   - `/ping` - Test responsiveness
   - `/help` - Show available commands
3. Send any regular message and the bot will respond using the Bedrock Agent

### Example Conversation

```
You: Hello! What can you help me with?
Bot: Hello there! I'm the joke-first assistant, here to sprinkle...

You: /status
Bot: 
**Bot Status**
🟢 Online and running
**User ID**: 123456789
**Session ID**: discord_user_123456789
...
```

## Troubleshooting

### Bot doesn't respond to DMs

- Check logs: `docker-compose logs -f discord-bot`
- Verify bot token is correct in `.env`
- Ensure **Message Content Intent** is enabled in Discord Developer Portal
- Confirm you're DMing the bot, not messaging in a server

### "You are not authorized" message

- Verify `AUTHORIZED_USER_ID` in `.env` matches your Discord user ID
- Make sure you copied the ID correctly (should be a long number like `123456789012345678`)

### AWS/Lambda errors

- Check AWS credentials are valid: `aws sts get-caller-identity`
- Verify Lambda function name matches deployment output
- Ensure AWS region is correct (us-west-2)
- Check IAM permissions allow `lambda:InvokeFunction`

### Bot logs show "LoginFailure"

- Bot token is incorrect or invalid
- Bot token may have been regenerated - get new one from Discord Developer Portal

### "Command not found" errors in Docker

- Ensure Docker and Docker Compose are installed
- Try `docker compose` (without hyphen) if `docker-compose` doesn't work

## Running in Production

### Option 1: Run on EC2 / VPS

Deploy the Docker Compose setup to an EC2 instance or VPS:

```bash
# Install Docker and Docker Compose on your server
# Clone your repository
git clone <your-repo>
cd aws-bedrock-agent-demo

# Set up .env file
cp .env.template .env
vim .env  # Edit with your values

# Run with restart policy
docker-compose up -d
```

The bot will auto-restart on crashes and server reboots.

### Option 2: Run on AWS ECS Fargate

1. Push Docker image to ECR
2. Create ECS task definition with environment variables
3. Create ECS Fargate service
4. Estimated cost: ~$5-10/month

### Option 3: Keep it local

Run on your personal computer. The bot will be online whenever your computer is on.

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | Yes | Bot token from Discord Developer Portal | `MTIzNDU2Nzg5MDEyMzQ1Njc4.GhIjKl.MnOpQrStUvWxYz...` |
| `AUTHORIZED_USER_ID` | Yes | Your Discord user ID (numbers only) | `123456789012345678` |
| `LAMBDA_FUNCTION_NAME` | Yes | Lambda function name from CDK output | `BedrockDiscordStack-MessageProcessor9DB0E972-CYQ8zNPojKog` |
| `AWS_REGION` | No | AWS region (defaults to us-west-2) | `us-west-2` |
| `AWS_ACCESS_KEY_ID` | Yes* | AWS access key ID | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Yes* | AWS secret access key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_SESSION_TOKEN` | No | For temporary credentials | `FwoGZXIvYXdz...` |

*Not required if using mounted `~/.aws/credentials`

## Bot Features

- ✅ Responds to DMs from authorized user only
- ✅ Maintains conversation context (10-minute sessions via Bedrock)
- ✅ Handles long messages (auto-splits >2000 characters)
- ✅ Typing indicator while processing
- ✅ Error handling and logging
- ✅ Slash commands for status and help
- ✅ Auto-reconnect on connection loss
- ✅ Docker containerized for easy deployment

## Next Steps

After getting the bot running:

1. **Test conversation continuity**: Send multiple messages and verify the agent remembers context
2. **Monitor costs**: Check AWS billing to track Lambda and Bedrock usage
3. **Add custom commands**: Extend `bot.py` with more slash commands
4. **Enable memory features**: Configure Bedrock Agent memory if not already enabled
5. **Set up monitoring**: Add CloudWatch alarms for errors and costs

## Support

For issues or questions:
- Check logs: `docker-compose logs -f discord-bot`
- Review Lambda logs: `aws logs tail /aws/lambda/BedrockDiscordStack-MessageProcessor --follow --region us-west-2`
- Check Discord Developer Portal for bot status
- Verify AWS Lambda function is deployed and accessible

## Security Notes

- ⚠️ Never commit `.env` file to Git (already in `.gitignore`)
- ⚠️ Keep bot token secret - regenerate if exposed
- ⚠️ Rotate AWS credentials periodically
- ⚠️ Use IAM roles with minimal permissions
- ⚠️ Only authorize trusted users (currently single-user by design)
