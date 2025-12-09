FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (if needed for web server)
EXPOSE 8080

# Command to run the bot
CMD ["python", "bot.py"]
