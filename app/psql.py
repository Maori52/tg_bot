import logging
import os
import time

import psycopg2
from dotenv import load_dotenv
from psycopg2 import Error, OperationalError

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Создание обработчика для вывода сообщений в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Конфигурация логирования
logging.basicConfig(
    handlers=[console_handler],  # Используем обработчик для консоли
    level=logging.DEBUG  # Уровень логирования
)

class PsqlHelper():
    def __init__(self):

        load_dotenv()
        try:
            max_retries = 30
            delay = 1
            retries = 0

            while retries < max_retries:
                try:
                    logging.info("Подключаемся к базе данных...")
                    self.connection = psycopg2.connect(
                        user=os.getenv("DB_USER"),
                        password=os.getenv("DB_PASSWORD"),
                        host=os.getenv("DB_HOST"),
                        port=os.getenv("DB_PORT"),
                        database=os.getenv("DB_DATABASE")
                    )
                    logging.info("Подключение успешно!")
                    self.connection.autocommit = True
                    self.cursor = self.connection.cursor()
                    return
                except OperationalError as e:
                    retries += 1
                    logging.warning(f"Ошибка подключения: {e}. Повторная попытка через {delay} секунд...")
                    time.sleep(delay)

            logging.error("Не удалось подключиться к базе данных за 30 секунд.")
            raise Exception("Не удалось подключиться к базе данных.")

        except (Exception, Error) as error:
            logging.error("Ошибка при соединении с PostgreSQL: %s", error)


    def select(self, table, query, condition=None):
        try:
            select_query = f"SELECT {query} FROM {table}"
            if condition:
                select_query += f"WHERE {condition}"
            self.cursor.execute(select_query)
            records = self.cursor.fetchall()
            return records
        except (Exception, Error) as error:
            logging.info("Ошибка при выполнении SELECT операции", error)


    def insert_many(self, table, values):
        # Пример insert-запроса
        # insert_values = [{
        #     "column1": "value1",
        #     "column2": "value2"
        # }]
        try:
            columns = ', '.join(values[0].keys())
            placeholders = ', '.join(['%s'] * len(values[0]))
            insert_query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            insert_values = [tuple(d.values()) for d in values]

            self.cursor.executemany(insert_query, insert_values)
            logging.info(f"Запись в таблицу {table} успешно добавлена")
        except (Exception, Error) as error:
            logging.info("Ошибка при выполнении INSERT операции", error)