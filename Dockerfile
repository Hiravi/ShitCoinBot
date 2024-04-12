# Base image
FROM python:3.11.9

# Working directory
WORKDIR /app

# Copy your Python file
COPY main.py /app
COPY requirements.txt /app
COPY utils.py /app
COPY languages.py /app
COPY db.py /app
COPY config.py /app
COPY logging_config.py /app
COPY .env /app
COPY webp_images /app/webp_images

# Install dependencies (if needed)
RUN pip install -r requirements.txt

# Command to run
CMD ["python", "main.py"]
