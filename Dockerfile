# Use an official Python runtime as a parent image
FROM python:3.9

# At the top of your Dockerfile
ARG SECRET_KEY

# Set environment variables
ENV DJANGO_SETTINGS_MODULE etradingview.settings.dev
ENV SECRET_KEY ${SECRET_KEY}

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /usr/src/app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "etradingview.wsgi:application"]
