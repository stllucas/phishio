# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/runtime

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Recursos nltk
RUN python -m nltk.downloader stopwords punkt

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 8000 and run the FastAPI application using Uvicorn
CMD ["uvicorn", "runtime.main:app", "--host", "0.0.0.0", "--port", "8000"]
