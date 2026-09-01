import logging
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import QObject, Signal


class LogEmitter(QObject):
  message = Signal(str)

class LogHandler(logging.Handler):
  def __init__(self, fmt, datefmt, log_level, slot):
    super().__init__()
    self.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    self.emitter = LogEmitter()
    self.emitter.message.connect(slot)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(self)

  def emit(self, record):
    self.emitter.message.emit(self.format(record))

class LogView(QPlainTextEdit):
  def __init__(self):
    super().__init__()
    self.setReadOnly(True)

    self.log_handler = LogHandler(
        fmt = "%(asctime)s [%(levelname)s] %(message)s",
        datefmt = "%H:%M:%S",
        log_level = logging.DEBUG,
        slot = self._log
    )

  def _log(self, message : str):
    self.appendPlainText(message)
