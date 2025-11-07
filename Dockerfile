FROM python:3.12.6-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /backend

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/backend

# Create a startup script
RUN echo '#!/bin/bash\nset -e\necho "Starting application..."\nexec python -m make run' > /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]