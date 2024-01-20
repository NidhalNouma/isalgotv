# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /usr/src/app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "etradingview.wsgi:application"]
