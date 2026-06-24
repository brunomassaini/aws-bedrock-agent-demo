# Discord Bedrock Agent Bot

A personal assistant Discord bot powered by AWS Bedrock Agent using Amazon Nova Lite. The bot maintains conversation context and responds to DMs from an authorized user.

## Architecture

- **Discord Bot**: Python app using discord.py that connects to Discord Gateway
- **AWS Lambda**: Processes messages and invokes Bedrock Agent
- **Bedrock Agent**: Amazon Nova Lite agent with session management and memory
- **Docker**: Containerized bot for easy deployment

## Project Structure

```
.
├── app.py                          # CDK app entry point
├── infrastructure/
│   └── bedrock_discord_stack.py    # CDK stack definition
├── lambda/
│   ├── message_processor.py        # Lambda handler
│   └── requirements.txt            # Lambda dependencies
├── discord_bot/
│   ├── bot.py                      # Discord bot implementation
│   └── requirements.txt            # Bot dependencies
├── Dockerfile                      # Docker image for bot
├── docker-compose.yml              # Docker Compose configuration
├── .env.template                   # Environment variables template
├── cdk.json                        # CDK configuration
├── requirements.txt                # CDK dependencies
├── README.md                       # This file
├── DISCORD_BOT_README.md          # Detailed bot setup guide
└── PRD.md                          # Product requirements document
```

## Quick Start

### Prerequisites
- AWS account with Bedrock access
- Docker and Docker Compose installed
- Discord Developer account
- Python 3.12+ (for CDK deployment)

### Step 1: Deploy Infrastructure (One-time setup)

```bash
# Install CDK dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap aws://YOUR_ACCOUNT/us-west-2

# Deploy Lambda and infrastructure
cdk deploy
```

**Save the Lambda function name from the output** (you'll need it for the bot).

### Step 2: Run Discord Bot

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your values:
# - Discord bot token
# - Your Discord user ID
# - Lambda function name from Step 1
# - AWS credentials
vim .env

# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f discord-bot
```

📖 **See [DISCORD_BOT_README.md](DISCORD_BOT_README.md) for detailed setup instructions**

## How It Works

### Architecture Flow

1. **User sends DM** to the Discord bot
2. **Discord bot** receives message via WebSocket
3. Bot validates user is authorized
4. Bot calls **AWS Lambda** function with user ID and message
5. **Lambda** invokes **Bedrock Agent** with session ID
6. **Bedrock** maintains 10-minute conversation context
7. Agent response flows back: Lambda → Bot → Discord user

### Key Features

- ✅ **Session Management**: 10-minute conversation context (automatic via Bedrock)
- ✅ **Single-user Authorization**: Only responds to configured Discord user
- ✅ **Docker Deployment**: Easy local or cloud deployment
- ✅ **Error Handling**: Graceful error messages and retry logic
- ✅ **Logging**: Comprehensive logs for debugging
- ✅ **Slash Commands**: `/status`, `/ping`, `/help`

## Components

### 1. Discord Bot (`discord_bot/bot.py`)
- Maintains WebSocket connection to Discord
- Validates authorized user
- Shows typing indicator while processing
- Splits long messages (Discord 2000 char limit)
- Implements slash commands

### 2. Lambda Function (`lambda/message_processor.py`)
- Serverless message processor
- Invokes Bedrock Agent with session management
- Parses streaming responses
- 60-second timeout, 512MB memory

### 3. Bedrock Agent
- Model: Amazon Nova Lite
- Session TTL: 10 minutes
- Automatic memory management
- Region: us-west-2

## Development Commands

### CDK (Infrastructure)

```bash
# Deploy infrastructure
cdk deploy

# Show CloudFormation template
cdk synth

# Compare deployed vs current
cdk diff

# Destroy infrastructure
cdk destroy

# View Lambda logs
aws logs tail /aws/lambda/BedrockDiscordStack-MessageProcessor --follow --region us-west-2
```

### Docker (Bot)

```bash
# Start bot
docker-compose up -d

# View logs
docker-compose logs -f discord-bot

# Restart bot
docker-compose restart discord-bot

# Stop bot
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Testing

```bash
# Test Lambda directly
aws lambda invoke \
  --function-name BedrockDiscordStack-MessageProcessor9DB0E972-CYQ8zNPojKog \
  --cli-binary-format raw-in-base64-out \
  --payload '{"user_id": "123456789", "message": "Hello!"}' \
  --region us-west-2 \
  response.json

cat response.json
```

## Configuration

### Infrastructure
Edit `infrastructure/bedrock_discord_stack.py` to change:
- `agent_id`: Your Bedrock Agent ID
- `agent_alias_id`: Agent alias (TSTALIASID for testing)
- Lambda timeout, memory, etc.

### Bot
Edit `.env` to configure:
- Discord bot token
- Authorized user ID
- Lambda function name
- AWS credentials

## Costs

**Estimated Monthly Costs** (with moderate usage):
- Lambda: ~$1
- Bedrock Nova Lite: ~$5-15
  - Input: $0.00006 per 1K tokens
  - Output: $0.00024 per 1K tokens
- CloudWatch: ~$0.50
- **Total: ~$7-17/month**

Running the Discord bot:
- Local: Free
- EC2/ECS Fargate: +$5-10/month

## Deployment Options

### Option 1: Local Development (Current Setup)
- Bot runs on your machine
- Free (except AWS costs)
- Bot offline when computer is off

### Option 2: AWS ECS Fargate
- Always online
- Auto-scaling and managed
- +$5-10/month

### Option 3: EC2 / VPS
- Full control
- Run on any cloud provider
- Variable cost based on instance
