# Use an official lightweight Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install all Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY . /app

# Expose the port that FastAPI runs on
EXPOSE 8000

# Set PYTHONPATH so absolute imports within src/ work
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python", "src/agent_backend.py"]