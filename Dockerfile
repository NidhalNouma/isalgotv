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

ENV LAMBDA_TASK_ROOT /usr/src/app/

# Set work directory
WORKDIR ${LAMBDA_TASK_ROOT} 

# Install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT} 

RUN chmod +r requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . ${LAMBDA_TASK_ROOT} 

COPY lambda_handler.py ${LAMBDA_TASK_ROOT}  

ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "lambda_handler.handler" ]
