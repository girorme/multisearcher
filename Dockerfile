# Use a slim image for reduced size
FROM python:3.11-slim AS builder
WORKDIR /app

COPY requirements.txt .

# Install dependencies to a local user directory
RUN pip install --user --no-cache-dir -r requirements.txt

# Second stage
FROM python:3.11-slim
WORKDIR /code

# Copy only the dependencies from the builder stage
COPY --from=builder /root/.local /home/appuser/.local
COPY ./ .

# Create a non-root user and group
RUN adduser --disabled-password --gecos "" appuser

# Change ownership to the non-root user
RUN chown -R appuser:appuser /code /home/appuser/.local

# Switch to the non-root user
USER appuser

# Update PATH environment variable
ENV PATH=/home/appuser/.local/bin:$PATH

# Use ENTRYPOINT to allow passing additional arguments
ENTRYPOINT ["python", "multisearcher.py"]
