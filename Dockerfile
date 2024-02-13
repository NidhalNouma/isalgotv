# Use an official Python runtime as a parent image
FROM public.ecr.aws/lambda/python:3.9

# Set arguments
ARG SECRET_KEY

ARG EMAIL_HOST_USER
ARG EMAIL_HOST_PASSWORD

ARG STRIPE_API_KEY
ARG STRIPE_API_PUBLIC_KEY

ARG STRIPE_PRICE_MN_ID
ARG STRIPE_PRICE_3MN_ID
ARG STRIPE_PRICE_Y_ID
ARG STRIPE_PRICE_LT_ID

ARG STRIPE_PRICE_MN_PRICE
ARG STRIPE_PRICE_3MN_PRICE
ARG STRIPE_PRICE_Y_PRICE
ARG STRIPE_PRICE_LT_PRICE

ARG DATABASE_HOST
ARG DATABASE_NAME
ARG DATABASE_USER

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_STORAGE_BUCKET_NAME

ARG TV_SESSION_ID

# Set environment variables
ENV DJANGO_SETTINGS_MODULE etradingview.settings.prod
ENV SECRET_KEY ${SECRET_KEY}

ENV EMAIL_HOST_USER ${EMAIL_HOST_USER}
ENV EMAIL_HOST_PASSWORD ${EMAIL_HOST_PASSWORD}

ENV STRIPE_API_KEY ${STRIPE_API_KEY}
ENV STRIPE_API_PUBLIC_KEY ${STRIPE_API_PUBLIC_KEY}

ENV STRIPE_PRICE_MN_ID ${STRIPE_PRICE_MN_ID}
ENV STRIPE_PRICE_3MN_ID ${STRIPE_PRICE_3MN_ID}
ENV STRIPE_PRICE_Y_ID ${STRIPE_PRICE_Y_ID}
ENV STRIPE_PRICE_LT_ID ${STRIPE_PRICE_LT_ID}

ENV STRIPE_PRICE_MN_PRICE ${STRIPE_PRICE_MN_PRICE}
ENV STRIPE_PRICE_3MN_PRICE ${STRIPE_PRICE_3MN_PRICE}
ENV STRIPE_PRICE_Y_PRICE ${STRIPE_PRICE_Y_PRICE}
ENV STRIPE_PRICE_LT_PRICE ${STRIPE_PRICE_LT_PRICE}

ENV DATABASE_HOST ${DATABASE_HOST}
ENV DATABASE_NAME ${DATABASE_NAME}
ENV DATABASE_USER ${DATABASE_USER}

ENV AWS_ACCESS_KEY_ID ${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY ${AWS_SECRET_ACCESS_KEY}
ENV AWS_STORAGE_BUCKET_NAME ${AWS_STORAGE_BUCKET_NAME}

ENV TV_SESSION_ID ${TV_SESSION_ID}

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt /usr/src/app/

RUN pip3 install --user --no-cache-dir -r requirements.txt

# Copy project
COPY . /usr/src/app/

# Collect static files
# RUN python manage.py collectstatic --noinput --clear

# Compress for tailwindcss build
# RUN python manage.py compress

# Run migrate
RUN python3 manage.py migrate --noinput

# Expose port 8000
EXPOSE 8000

# Command to run the application
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "etradingview.wsgi:application", "--access-logfile", "-", "--error-logfile", "-"]


# FOR deploy on AWS LAMBDA

# Adjust CMD to use aws-lambda-wsgi
# Specify the handler file as the command to run
# CMD ["python", "lambda_handler.py"]
# CMD ["python", "-m", "awslambdaric", "lambda_handler.handler"]
ENTRYPOINT [ "python3", "-m", "awslambdaric" ]
CMD [ "lambda_handler.handler" ]

