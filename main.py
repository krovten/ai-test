#!/usr/bin/env python3
from config import validate_environment
from core.factory import load_modules
from core.runner import run_job
from utils.logger import logger
from utils.reporting import save_csv_report

def main():
    logger.info("Инициализация системы и динамическая загрузка модулей...")
    load_modules()

    # Pre-flight валидация
    devices = validate_environment("devices.csv")

    # Запуск параллельной обработки
    results = run_job(devices, max_workers=10)

    # Генерация CSV-отчета
    save_csv_report(results, "change_password_report.csv")
    logger.info("Работа завершена. Результаты сохранены в change_password_report.csv и app.log")

if __name__ == "__main__":
    main()
