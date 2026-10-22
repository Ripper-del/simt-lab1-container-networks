FROM python:3.12-alpine
WORKDIR /srv/app
# спочатку залежності, щоб кешувався шар
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
# запуск через gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
