FROM python:3

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]



# docker build --tag isalgo .
# docker run --publish 3000:8000 isalgo