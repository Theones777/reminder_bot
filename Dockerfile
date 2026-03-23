FROM python:3.11-bullseye

RUN pip install --upgrade setuptools pip

# Создаём пользователя
RUN useradd -m myuser
USER myuser

WORKDIR /app
COPY --chown=myuser:myuser . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
