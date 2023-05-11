import logging
import time
import os
import sys
import requests

import telegram
from dotenv import load_dotenv
from exceptions import GetStatusException, ParseStatusException


load_dotenv()
# настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """функция проверки наличия необходимых переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if not TELEGRAM_CHAT_ID:
            logger.critical('TOKEN not found')
            return False
    return True


def send_message(bot, message):
    """функция отправки сообщения в Telegram."""
    try:
        logger.debug(f'Отправлено сообщение: {message}')
        response = bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        return response
    except telegram.error.TelegramError as error:
        logger.error(f'сообщение - {message} не отправленно, ошибка - {error}')


def get_api_answer(timestamp):
    """функция получения ответа от API."""
    params = {'from_date': timestamp}
    try:
        homework_status = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params,
        )
    except requests.exceptions.RequestException as error:
        raise GetStatusException(f'Ошибка запроса API: {error}')

    if homework_status.status_code != requests.codes.ok:
        raise GetStatusException(
            f'Ошибка, код ответа API: {homework_status.status_code} '
        )
    return homework_status.json()


def check_response(response):
    """функция проверки ответа API."""
    if not isinstance(response, dict):
        raise TypeError('неправильный ответ')

    if 'homeworks' not in response:
        raise KeyError('Invalid server response')

    if not isinstance(response['homeworks'], list):
        raise TypeError('неверный формат')

    return response['homeworks']


def parse_status(homework):
    """функция извлечения статуса работы."""
    if 'homework_name' not in homework:
        raise KeyError('нет домашки')
    if 'status' not in homework:
        raise KeyError('нет статуса')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    message = '''
    f'неизвестный статус {homework_status}'
    '''
    raise ParseStatusException(message)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    send_message(bot, 'этот бот работает')
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            timestamp = response.get('current_date', timestamp)
            if homework:
                last_homework = homework[0]
                message = parse_status(last_homework)
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        timestamp = response.get('current_date', timestamp)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
