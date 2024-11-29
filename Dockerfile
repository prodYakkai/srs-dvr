# Use an official Python runtime as a parent image
FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required packages
RUN uv sync --frozen

# Expose the port the app runs on
EXPOSE 5000

# Run the command to start the Flask app
CMD ["uv","run", "gunicorn", "--bind", "0.0.0.0:5000", "app:app" , "--capture-output"]