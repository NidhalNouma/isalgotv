FROM python:3

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
# RUN python3 manage.py collectstatic --no-input --clear --settings=etradingview.settings.prod
RUN python3 manage.py migrate --settings=etradingview.settings.prod

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000", "--settings=etradingview.settings.prod" ]



# docker build --progress=plain --no-cache --tag isalgo .
# docker run -d --name isalgo_run --publish 3000:8000 isalgo