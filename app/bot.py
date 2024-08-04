import datetime
import logging
import os
import re

import paramiko
import psycopg2
from dotenv import load_dotenv
from telegram import Update
from telegram.error import Unauthorized
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

from psql import PsqlHelper

# Подключаем логирование
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Создание обработчика для вывода сообщений в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Конфигурация логирования
logging.basicConfig(
    handlers=[console_handler],  # Используем обработчик для консоли
    level=logging.DEBUG  # Уровень логирования
)

# Создание логгера
logger = logging.getLogger(__name__)
MAX_MESSAGE_LENGTH = 2000

db_client = PsqlHelper()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

commands_map = {
    "get_release": "cat /etc/os-release",
    "get_uname": "uname -a",
    "get_uptime": "uptime",
    "get_df": "df -h",
    "get_free": "free -h",
    "get_w": "w",
    "get_mpstat": "mpstat",
    "get_auths": "last -n 10",
    "get_critical": "journalctl -p crit -n 5",
    "get_ps": "ps aux",
    "get_ss": "ss -tuln",
    "get_services": "systemctl list-units --type=service --state=running",
    "get_repl_logs": "cat /var/log/postgresql/postgresql-15-main.log | grep 'replica_user'"
}


# функции обработчики:
def find_emails(update: Update, context):
    user_input = update.message.text

    email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    emails_list = email_regex.findall(user_input)

    if not emails_list:
        update.message.reply_text("Email'ы не найдены")
        return ConversationHandler.END

    emails_string = ""
    for i in range(len(emails_list)):
        emails_string += f'{i + 1}. {emails_list[i]}\n'  # Записываем очередной номер
    context.user_data['emails_list'] = emails_list
    update.message.reply_text(emails_string)
    update.message.reply_text("\nСохранить email'ы в базе данных? (да/нет): ")
    return 'add_emails'


def find_phone_numbers(update: Update, context: CallbackContext):
    user_input = update.message.text  # Получаем текст, содержащий (или нет) номера телефонов

    phone_num_regex = re.compile(
        r"(?:(?:8|\+7)[-\s]?)?(?:\(?\d{3}\)?[-\s]?)?\d{3}[-\s]?\d{2}[-\s]?\d{2}")

    phone_number_list = phone_num_regex.findall(user_input)  # Ищем номера телефонов

    if not phone_number_list:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END  # Завершаем выполнение функции

    phone_numbers = ''  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phone_number_list)):
        phone_numbers += f'{i + 1}. {phone_number_list[i]}\n'  # Записываем очередной номер
    context.user_data['phone_number_list'] = phone_number_list
    update.message.reply_text(phone_numbers)  # Отправляем сообщение пользователю
    update.message.reply_text("\nСохранить номера в базе данных? (да/нет): ")
    return 'add_phone_numbers'
    # return ConversationHandler.END  # Завершаем работу обработчика диалога

def add_phone_numbers(update: Update, context: CallbackContext):
    user_input = update.message.text
    phone_number_list = context.user_data.get('phone_number_list')
    if user_input == 'да':
        transformed_list = list(map(lambda num: {'phone_number': num}, phone_number_list))
        db_client.insert_many('phone_numbers', transformed_list)
        update.message.reply_text(f"Номера '{phone_number_list}' успешно сохранены в базе данных.")
    else:
        update.message.reply_text("Операция отменена. Номера не сохранены.")
    return ConversationHandler.END


def add_emails(update: Update, context):
    user_input = update.message.text
    emails_list = context.user_data.get('emails_list')
    if user_input == 'да':
        transformed_list = list(map(lambda num: {'email': num}, emails_list))
        db_client.insert_many('emails', transformed_list)
        update.message.reply_text(f"Email'ы '{emails_list}' успешно сохранены в базе данных.")
    else:
        update.message.reply_text("Операция отменена. Email'ы не сохранены.")
    return ConversationHandler.END


def verify_password(update: Update, context):
    user_input = update.message.text

    password_regex = re.compile(
        r"^(?=.*[A-Z])"
        r"(?=.*[a-z])"
        r"(?=.*\d)"
        r"(?=.*[!@#$%^&*()])"
        r".{8,}$"
    )

    if not password_regex.match(user_input):
        message = 'Пароль простой'
    else:
        message = 'Пароль сложный'

    update.message.reply_text(message)
    return ConversationHandler.END


def common_handler(update: Update, context):
    command = update.message.text.split()[0][1:]
    args = ""
    if len(update.message.text.split()) > 1:
        args = update.message.text.split(' ', 1)[1]
    if command in commands_map:
        logger.debug("executing command: {} with args {}".format(command, args))
        system_command = commands_map[command]
        result = execute_command_on_server(system_command, args)
        logger.debug("result of command: {}".format(result))
        if len(result) > MAX_MESSAGE_LENGTH:
            send_separate_message(result, update)
        else:
            update.message.reply_text(result)
    else:
        update.message.reply_text(f"Неизвестная команда {command}")


def connect_to_server(update: Update, context):
    try:
        hostname = os.getenv('RM_HOST')
        username = os.getenv('RM_USER')
        password = os.getenv('RM_PASSWORD')
        port = int(os.getenv('RM_HOST'))

        client.connect(hostname=hostname, username=username, password=password, port=port)
    except Exception as e:
        logger.error(f"Connection error: {e}")
        update.message.reply_text("Ошибка при соединении с сервером {}".format(hostname))
        exit(1)
    logger.info("Connection to server {} established".format(hostname))
    update.message.reply_text("Соединение с сервером {} установлено".format(hostname))
    return ConversationHandler.END


def get_apt_list(update: Update, context):
    result = ''
    if update.message.text == 'all':
        result = execute_command_on_server("apt list --installed")
    else:
        result = execute_command_on_server("apt show {}".format(update.message.text))

    if len(result) > MAX_MESSAGE_LENGTH:
        send_separate_message(result, update)
    else:
        update.message.reply_text(result)
    return ConversationHandler.END


def get_emails(update: Update, context):
    emails_list = db_client.select('emails', 'email')
    result = ""
    for email in emails_list:
        result += str(email[0]) + "\n"
    update.message.reply_text(result)
    return ConversationHandler.END


def get_phone_numbers(update: Update, context):
    phone_numbers = db_client.select('phone_numbers', 'phone_number')
    result = ""
    for phone_number in phone_numbers:
        result += str(phone_number[0]) + "\n"
    update.message.reply_text(result)
    return ConversationHandler.END

# вспомогательные функции:

def get_apt_list_command(update: Update, context):
    update.message.reply_text("Введите интересующий вас пакет или напечатайте all для получения всех пакетов: ")
    return 'get_apt_list'
def find_emails_command(update: Update, context):
    update.message.reply_text("Введите текст для поиска email'ов: ")

    return 'find_emails'



def find_phone_numbers_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_numbers'


def verify_password_command(update: Update, context):
    update.message.reply_text("Введите пароль для оценки: ")

    return 'verify_password'


def execute_command_on_server(command, args=''):
    try:
        command_string = " ".join([command, args])
        stdin, stdout, stderr = client.exec_command(command_string)

        stdout_data = stdout.read().decode('utf-8')
        stderr_data = stderr.read().decode('utf-8')

        result = stdout_data + stderr_data
        return result.replace('\\n', '\n').replace('\\t', '\t')

    except Exception as e:
        return str(e)


def send_separate_message(message, update: Update):
    chunks = []
    while len(message) > MAX_MESSAGE_LENGTH:
        last_newline_index = message.rfind('\n', 0, MAX_MESSAGE_LENGTH)
        if last_newline_index == -1:
            chunks.append(message[:MAX_MESSAGE_LENGTH])
            message = message[MAX_MESSAGE_LENGTH:]
        else:
            chunks.append(message[:last_newline_index])
            message = message[last_newline_index + 1:]
    if message:
        chunks.append(message)

    for chunk in chunks:
        update.message.reply_text(chunk)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')

def main():
    logger.info("Reading config....")
    load_dotenv()
    logger.info("OK")
    if os.getenv("MESSAGE_SYMBOL_LIMIT"):
        MAX_MESSAGE_LENGTH = int(os.getenv('MESSAGE_SYMBOL_LIMIT'))
    token = os.getenv('TOKEN')
    if not token:
        logger.error("Can't get token from env")
        exit(1)

    logger.info("Bind telegram bot by token")
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    logger.info("OK")

    dp.add_handler(CommandHandler("connect_to_server", connect_to_server))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))

    # get_phone_numbers
    # add_emails
    # add_phone_numbers
    for command in commands_map.keys():
        dp.add_handler(CommandHandler(command, common_handler))


    # Обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('find_phone_numbers', find_phone_numbers_command),
                      CommandHandler('find_emails', find_emails_command),
                      CommandHandler('verify_password', verify_password_command),
                      CommandHandler('get_apt_list', get_apt_list_command)],

        states={
            'find_phone_numbers': [MessageHandler(Filters.text & ~Filters.command, find_phone_numbers)],
            'add_phone_numbers': [MessageHandler(Filters.text & ~Filters.command, add_phone_numbers)],
            'find_emails': [MessageHandler(Filters.text & ~Filters.command, find_emails)],
            'add_emails': [MessageHandler(Filters.text & ~Filters.command, add_emails)],
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
            'add_emails': [MessageHandler(Filters.text & ~Filters.command, add_emails)],
        },
        fallbacks=[]
    )
    dp.add_handler(conv_handler)

    # Запускаем бота
    logger.info("Start polling...")
    try:
        updater.start_polling()
    except Unauthorized:
        logger.error("Wrong token")
        exit(1)

    logger.info("OK")
    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
