# Use a minimal 'slim' base image for Python
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements from parent directory and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the test client code
COPY cmd/testclient/testclient.py .

# The command to run when the container starts
# -u flag ensures Python output is unbuffered (good for logs)
ENTRYPOINT ["python3", "-u", "testclient.py"]
CMD ["-i", "-url", "http://localhost:8080/mcp"]
