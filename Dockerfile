# Use an official lightweight Python image
FROM python:3.10-slim

# Set environment variables
# Prevent Python from writing .pyc files and force stdout/stderr to be unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /workspace

# Install dependencies
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY app /workspace/app/

# Run the bot as a module to correctly resolve package imports (from app import ...)
CMD ["python", "-m", "app.main"]
