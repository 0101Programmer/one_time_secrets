import logging

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Настройка логгера с выводом только в консоль.
    :param name: Имя логгера (обычно __name__).
    :param level: Уровень логирования (по умолчанию INFO).
    :return: Экземпляр Logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Формат логов
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Логирование в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger