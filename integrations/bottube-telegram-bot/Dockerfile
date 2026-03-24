FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bottube_bot.py .

# Set environment variables
ENV BOT_TOKEN=""
ENV BOTUBE_API_BASE="https://50.28.86.153:8097"

# Run the bot
CMD ["python", "bottube_bot.py"]