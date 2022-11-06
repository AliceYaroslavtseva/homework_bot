import os
import telegram
import logging
import time
from http import HTTPStatus
from telegram import Bot
from dotenv import load_dotenv
import requests

load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
PAYLOAD = 30 * 24 * 60 * 60

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


def send_message(bot, message):
    """Функция send_message отправляет сообщение в Telegram чат."""
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение отправлено')
    except Exception as error:
        logging.error(f'Сообщение НЕ отправлено: {error}')


def get_api_answer(current_timestamp):
    """Функция get_api_answer делает запрос.
    к единственному эндпоинту API-сервиса.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    logging.info('Функция get_api_answer')
    if response.status_code != HTTPStatus.OK:
        logging.exception('Ошибка! API возвращает код, отличный от 200')
        raise TypeError(msg='Ошибка! API возвращает код, не 200.')
    return response.json()


def check_response(response):
    """Функция check_response проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        logging.info('Функция get_api_answer')
        raise TypeError('Ошибка! Параметр не приведен к типу данных Python')
    return response.get('homeworks')[0]


def parse_status(homework):
    """Функция parse_status извлекает из информации о.
    конкретной домашней работе статус этой работы.
    """
    if not isinstance(homework, dict):
        logging.exception('Ошибка! типа данных в homework')
        raise KeyError('Ошибка! типа данных в homework')

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES.keys():
        logging.exception('Обнаружен недокументированный статус домашней '
                          'работы в ответе API.')
        raise KeyError('Обнаружен недокументированный статус домашней работы '
                       'в ответе API.')

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функция check_tokens роверяет доступность переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    if all(tokens):
        return True
    else:
        return False


def main():
    """Функция main писывает основную логика работы программы.
    - Сделает запрос к API.
    - Проверяет ответ.
    - Если есть обновления — получить статус работы из обновления
    и отправить сообщение в Telegram.
    - Ждёт 10 мин и делает новый запрос.
    """
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - PAYLOAD)
    previous_request = ''
    while True:
        try:
            check_tokens()
            response = get_api_answer(current_timestamp)
            checked_response = check_response(response)
            parsed_status = parse_status(checked_response)
            if parsed_status != previous_request:
                send_message(bot, parsed_status)
                previous_request = parsed_status
        except Exception as error:
            message = f'Сбой в работе: {error}'
            send_message(bot, message)
            logging.exception('Ошибка!')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
