import os
import logging
import json
import boto3
import discord
from discord.ext import commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
DISCORD_BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']
AUTHORIZED_USER_ID = os.environ['AUTHORIZED_USER_ID']
LAMBDA_FUNCTION_NAME = os.environ['LAMBDA_FUNCTION_NAME']
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')

# Initialize AWS Lambda client
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

# Configure Discord bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

# Create bot instance
bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f'Bot logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Authorized user ID: {AUTHORIZED_USER_ID}')
    logger.info(f'Lambda function: {LAMBDA_FUNCTION_NAME}')
    logger.info('Bot is ready and listening for messages!')


@bot.event
async def on_message(message):
    """Handle incoming messages."""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Only respond to DMs from authorized user
    if not isinstance(message.channel, discord.DMChannel):
        logger.debug(f'Ignoring message from non-DM channel')
        return

    if str(message.author.id) != AUTHORIZED_USER_ID:
        logger.warning(f'Unauthorized user {message.author.id} tried to message the bot')
        await message.channel.send("Sorry, you are not authorized to use this bot.")
        return

    # Process commands first
    await bot.process_commands(message)

    # If message starts with /, it's a command - don't process as regular message
    if message.content.startswith('/'):
        return

    # Show typing indicator
    async with message.channel.typing():
        try:
            # Call Lambda function
            logger.info(f'Processing message from user {message.author.id}: {message.content[:50]}...')

            payload = {
                'user_id': str(message.author.id),
                'message': message.content
            }

            response = lambda_client.invoke(
                FunctionName=LAMBDA_FUNCTION_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            # Parse Lambda response
            response_payload = json.loads(response['Payload'].read())
            logger.debug(f'Lambda response: {response_payload}')

            if response_payload.get('statusCode') == 200:
                body = json.loads(response_payload['body'])
                agent_response = body.get('response', 'No response from agent')

                # Split long messages if needed (Discord has 2000 char limit)
                if len(agent_response) <= 2000:
                    await message.channel.send(agent_response)
                else:
                    # Split into chunks
                    chunks = [agent_response[i:i+2000] for i in range(0, len(agent_response), 2000)]
                    for chunk in chunks:
                        await message.channel.send(chunk)

                logger.info('Message processed successfully')
            else:
                error_body = json.loads(response_payload.get('body', '{}'))
                error_message = error_body.get('error', 'Unknown error')
                logger.error(f'Lambda error: {error_message}')
                await message.channel.send(f"Sorry, I encountered an error: {error_message}")

        except Exception as e:
            logger.error(f'Error processing message: {str(e)}', exc_info=True)
            await message.channel.send("Sorry, I encountered an unexpected error. Please try again later.")


@bot.command(name='status')
async def status_command(ctx):
    """Show bot status and session info."""
    if str(ctx.author.id) != AUTHORIZED_USER_ID:
        await ctx.send("You are not authorized to use this command.")
        return

    status_msg = f"""
**Bot Status**
🟢 Online and running
**User ID**: {ctx.author.id}
**Session ID**: discord_user_{ctx.author.id}
**Lambda**: {LAMBDA_FUNCTION_NAME}
**Region**: {AWS_REGION}

Your conversation context is maintained for 10 minutes after your last message.
    """
    await ctx.send(status_msg.strip())


@bot.command(name='ping')
async def ping_command(ctx):
    """Check if the bot is responsive."""
    if str(ctx.author.id) != AUTHORIZED_USER_ID:
        await ctx.send("You are not authorized to use this command.")
        return

    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latency: {latency}ms')


@bot.command(name='help')
async def help_command(ctx):
    """Show help message."""
    if str(ctx.author.id) != AUTHORIZED_USER_ID:
        await ctx.send("You are not authorized to use this command.")
        return

    help_msg = """
**Available Commands**
`/status` - Show bot status and session info
`/ping` - Check bot responsiveness
`/help` - Show this help message

**Usage**
Just send me a message and I'll respond using the Bedrock Agent!
Your conversation context is maintained for 10 minutes.
    """
    await ctx.send(help_msg.strip())


def main():
    """Main entry point."""
    logger.info('Starting Discord bot...')

    # Validate environment variables
    required_vars = ['DISCORD_BOT_TOKEN', 'AUTHORIZED_USER_ID', 'LAMBDA_FUNCTION_NAME']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error(f'Missing required environment variables: {", ".join(missing_vars)}')
        raise ValueError(f'Missing required environment variables: {", ".join(missing_vars)}')

    # Start bot
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logger.error('Failed to login. Check your DISCORD_BOT_TOKEN.')
        raise
    except Exception as e:
        logger.error(f'Bot crashed: {str(e)}', exc_info=True)
        raise


if __name__ == '__main__':
    main()
