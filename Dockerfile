FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy all files to the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the bot
CMD ["python", "bot.py"]