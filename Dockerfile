FROM python:3.11-slim

# Рабочая директория
WORKDIR /exchanger_tg_bot

# Копируем только requirements.txt
COPY __install__/requirements.txt /exchanger_tg_bot/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /exchanger_tg_bot

# Отключаем буферизацию вывода (логирование сразу)
ENV PYTHONUNBUFFERED=1

# Запуск приложения
CMD ["python", "main.py"]
