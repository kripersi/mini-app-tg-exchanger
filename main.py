from threading import Thread
import subprocess
import sys
import os


def run_script(script_name):
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    if not os.path.isfile(script_path):
        print(f"Файл не найден: {script_path}")
        return
    subprocess.run([sys.executable, script_path], cwd=os.path.dirname(__file__))


if __name__ == "__main__":
    # Запускаем каждый скрипт в отдельном потоке
    threads = [
        Thread(target=run_script, args=("tg_bot.py",)),
        Thread(target=run_script, args=("update_exchange_rates.py",)),
        Thread(target=run_script, args=("app.py",))
    ]

    # Запускаем потоки
    for thread in threads:
        thread.start()

    # Ждём завершения всех потоков (опционально)
    for thread in threads:
        thread.join()
