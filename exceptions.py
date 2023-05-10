class GetStatusException(Exception):
    '''Класс пользовательского исключения для обработки ошибок
    при запросе статуса домашней работы'''

    def __init__(self, message="Ошибка запроса API"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class MyTelegramError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ParseStatusException(Exception):
    def __init__(self, homework_name, status):
        self.homework_name = homework_name
        self.status = status

    def __str__(self):
        return (f'Ошибка при парсинге статуса работы "{self.homework_name}": '
                f'{self.status}')
