import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from telegram import Bot

from exceptions import (APIResponsError, NoKeyError, ParameterNotTypeError,
                        SendMessageError)

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
    except SendMessageError as e:
        raise (f'Ошибка в отправке сообщения: {e}')
    else:
        logging.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    """Функция get_api_answer делает запрос.
    к единственному эндпоинту API-сервиса.
    """
    requests_params = dict(url=ENDPOINT,
                           headers=HEADERS,
                           params={'from_date': current_timestamp})

    if not isinstance(requests_params, dict):
        raise ParameterNotTypeError(f'Ошибка типа данных в requests_params:'
                                    f'{type(requests_params)}')

    if (('url' not in requests_params)
            or ('headers' not in requests_params)
            or ('params' not in requests_params)):
        raise NoKeyError('Ошибка, в словаре requests_params '
                         'нет ключа')

    response = requests.get(**requests_params)

    logging.info('Функция get_api_answer')
    if response.status_code != HTTPStatus.OK:
        raise APIResponsError(f'Ошибка, возвращаемый статус не 200'
                              f'requests_params = {requests_params};'
                              f'http_code = {response.status_code};'
                              f'reason = {response.reason};'
                              f'content = {response.text}')
    return response.json()


def check_response(response):
    """Функция check_response проверяет ответ API на корректность."""
    logging.info('Функция check_response')
    if not isinstance(response, dict):
        raise TypeError(f'Ошибка типа данных в response:'
                        f'{type(response)}')

    if ('homeworks' not in response) or ('current_date' not in response):
        raise NoKeyError('Ошибка, в словаре response '
                         'нет ключа')

    return response.get('homeworks')[0]


def parse_status(homework):
    """Функция parse_status извлекает из информации о.
    конкретной домашней работе статус этой работы.
    """
    """По pytest здеcь почему-то обязателен KeyError"""
    if not isinstance(homework, dict):
        raise KeyError(f'Ошибка типа данных в response:'
                       f'{type(homework)}')

    if ('status' not in homework) or ('homework_name' not in homework):
        raise NoKeyError('Ошибка, в словаре homework '
                         'нет ключа')

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if ('status' not in homework) or ('homework_name' not in homework):
        raise NoKeyError('Ошибка, в словаре homework '
                         'нет ключа')

    if homework_status not in HOMEWORK_STATUSES.keys():
        logging.exception('Обнаружен недокументированный статус домашней '
                          'работы в ответе API.')
        raise NoKeyError('Обнаружен недокументированный статус домашней'
                         'работы в ответе API.')

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функция check_tokens роверяет доступность переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(tokens)


def main():
    """Функция main писывает основную логика работы программы.
    - Сделает запрос к API.
    - Проверяет ответ.
    - Если есть обновления — получить статус работы из обновления
    и отправить сообщение в Telegram.
    - Ждёт 10 мин и делает новый запрос.
    """
    if check_tokens() is False:
        logging.critical('НЕТ переменной окружения')
        sys.exit
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - PAYLOAD)
    previous_request = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            checked_response = check_response(response)
            parsed_status = parse_status(checked_response)
            if parsed_status != previous_request:
                send_message(bot, parsed_status)
                previous_request = parsed_status
        except SendMessageError:
            message_sendmessage = 'Ошибка в отправке сообщения.'
            send_message(bot, message_sendmessage)
            logging.error(message_sendmessage)
        except APIResponsError:
            message_apirespons = 'Ошибка,статус отличный от 200.'
            get_api_answer(bot, message_apirespons)
            logging.error(message_apirespons)
        except ParameterNotTypeError:
            message_parameternottype = ('Ошибка, '
                                        'не приведено к'
                                        'типу данных Python.')
            check_response(response)
            logging.error(message_parameternottype)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
