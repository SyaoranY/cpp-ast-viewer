from PySide6.QtWidgets import (
  QWidget,
  QVBoxLayout,
  QLabel
) 

class AstView(QWidget):
  def __init__(self):
    super().__init__()
    layout = QVBoxLayout(self)
    layout.addWidget(QLabel("AstView"))