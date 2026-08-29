import logging

from PySide6.QtWidgets import (
  QWidget,
  QPlainTextEdit
) 

from PySide6.QtCore import QObject, Signal

class LogEmitter(QObject):
  message = Signal(str)

class QtLogHandler(logging.Handler):
  def __init__(self):
    super().__init__()
    self.emitter = LogEmitter()

  def emit(self, record):
    message = self.format(record)
    self.emitter.message.emit(message)

class LogView(QPlainTextEdit):
  def __init__(self):
    super().__init__()
    self.setReadOnly(True)

  def log(self, message : str):
    self.appendPlainText(message)
