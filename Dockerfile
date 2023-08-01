FROM python:3

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
# RUN python3 manage.py collectstatic --no-input --clear 
RUN python3 manage.py migrate

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]



# docker build --progress=plain --no-cache --tag isalgo .
# docker run -e "DJANGO_SETTINGS_MODULE=etradingview.settings.prod" -d --name isalgo_run --publish 3000:8000 isalgo