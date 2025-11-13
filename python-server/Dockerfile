# Use a minimal 'slim' base image for Python
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install the Python dependencies
RUN pip install -r requirements.txt

# Copy the Python server code into the container
COPY mcp_server.py .

# Expose the port the server runs on
EXPOSE 8080

# The command to run when the container starts
# -u flag ensures Python output is unbuffered (good for logs)
# Default: HTTP/SSE mode on 0.0.0.0:8080
CMD ["python3", "-u", "mcp_server.py", "--mode=http", "--host=0.0.0.0", "--port=8080"]

