FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY discord_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY discord_bot/bot.py .

# Run bot
CMD ["python", "-u", "bot.py"]
