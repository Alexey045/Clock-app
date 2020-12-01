from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QEnterEvent, QPainter, QColor, QPen
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem,\
    QSizePolicy, QPushButton
from PyQt5 import QtCore, QtGui, QtWidgets
from enum import Enum, auto
from main import *
import win32api


class TitleBar(QWidget):
    qss = """
    /* Панель заголовка */
    TitleBar {
        background-color: #232323;
    }
    /* Минимизировать кнопку `Максимальное выключение` Общий фон по умолчанию */
    #buttonMinimum, #buttonMaximum, #buttonClose {
        border: none;
        background-color: #232323;
        color: white;
    }
    /* Зависание */
    #buttonMinimum:hover,#buttonMaximum:hover {
        background-color: #191919;
    }
    #buttonClose:hover {
        color: white;
        background-color: rgb(232, 17, 35);
    }
    /* Мышь удерживать */
    #buttonMinimum:pressed,#buttonMaximum:pressed {
        background-color: #333333;
    }
    #buttonClose:pressed {
        color: white;
        background-color: rgb(241, 112, 122);
    }
    """
    # Сигнал минимизации окна
    windowMinimumed = pyqtSignal()

    # увеличить максимальный сигнал окна
    windowMaximumed = pyqtSignal()

    # сигнал восстановления окна
    windowNormaled = pyqtSignal()

    # сигнал закрытия окна
    windowClosed = pyqtSignal()

    # Окно мобильных
    windowMoved = pyqtSignal(QPoint)

    # Сигнал отжатия мыши
    mouseRelease = pyqtSignal()

    # Сигнал движения мышки
    mouseMove = pyqtSignal(QtGui.QMouseEvent)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet(self.qss)
        # Поддержка настройки фона qss
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._old_pos = None

        # Размер значка по умолчанию
        self.iconSize = 20

        # Установите цвет фона по умолчанию, иначе он будет прозрачным из-за влияния родительского окна
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(palette.Window, QColor(240, 240, 240))
        self.setPalette(palette)

        # значок окна
        self.iconLabel = QLabel()
        # self.iconLabel.setScaledContents(True)

        # название окна
        self.titleLabel = QLabel()
        self.titleLabel.setMargin(2)

        # Использовать шрифты Webdings для отображения значков
        font = self.font() or QFont()
        font.setFamily('Webdings')

        self.buttonMinimum = QPushButton('0', clicked=self.windowMinimumed.emit, font=font, objectName='buttonMinimum')
        self.buttonMaximum = QPushButton('1', clicked=self.showMaximized, font=font, objectName='buttonMaximum')
        self.buttonClose = QPushButton('r', clicked=self.windowClosed.emit, font=font, objectName='buttonClose')

        # макет
        layout = QHBoxLayout(spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.iconLabel)
        layout.addWidget(self.titleLabel)

        # Средний телескопический бар
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.layout_custom_widget = QHBoxLayout()
        self.layout_custom_widget.setContentsMargins(0, 0, 0, 0)

        layout.addLayout(self.layout_custom_widget)
        layout.addWidget(self.buttonMinimum)
        layout.addWidget(self.buttonMaximum)
        layout.addWidget(self.buttonClose)

        self.setLayout(layout)

        # начальная высота
        self.setHeight()

    def addWidget(self, widget, width=35, height=35):
        self.layout_custom_widget.addWidget(widget)

        widget.setMinimumSize(width, height)
        widget.setMaximumSize(width, height)

    def showMaximized(self):
        if self.buttonMaximum.text() == '1':
            # Максимизировать
            self.buttonMaximum.setText('2')
            self.windowMaximumed.emit()
        else:  # Восстановить
            self.buttonMaximum.setText('1')
            self.windowNormaled.emit()

    def setHeight(self, height=35):
        """ Установка высоты строки заголовка """
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
        # Задайте размер правой кнопки  ?
        self.buttonMinimum.setMinimumSize(height, height)
        self.buttonMinimum.setMaximumSize(height, height)
        self.buttonMaximum.setMinimumSize(height, height)
        self.buttonMaximum.setMaximumSize(height, height)
        self.buttonClose.setMinimumSize(height, height)
        self.buttonClose.setMaximumSize(height, height)

    def setTitle(self, title):
        """ Установить заголовок """
        self.titleLabel.setText(title)

    def setIcon(self, icon):
        """ настройки значокa """
        self.iconLabel.setPixmap(icon.pixmap(self.iconSize, self.iconSize))

    def setIconSize(self, size):
        """ Установить размер значка """
        self.iconSize = size

    def enterEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().enterEvent(event)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        self.showMaximized()

    def mousePressEvent(self, event):
        """ Событие клика мыши """
        if event.button() == Qt.LeftButton:
            self._old_pos = event.pos()
        event.accept()

    def mouseReleaseEvent(self, event):
        """ Событие отказов мыши """
        self._old_pos = None
        self.mouseRelease.emit()
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._old_pos:
            self.windowMoved.emit(self.mapToGlobal(event.pos() - self._old_pos))
        self.mouseMove.emit(event)
        event.accept()


class Direction(Enum):
    LEFT = auto()
    TOP = auto()
    RIGHT = auto()
    BOTTOM = auto()

    LEFT_TOP = auto()
    RIGHT_TOP = auto()
    LEFT_BOTTOM = auto()
    RIGHT_BOTTOM = auto()


class MainWindow(QWidget):
    MARGINS = 7

    def __init__(self):
        super().__init__()
        self.setStyleSheet(MyMainWindow.qss)
        self.setupUi()
        self.setWindowTitle("Будильники и часы")
        self.setWindowIcon(QtGui.QIcon("TrayIcon.png"))

        self._old_pos = None
        self._direction = None
        self._widget = None

    def setupUi(self):
        self.resize(425, 600)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        layout = QVBoxLayout(spacing=0)
        layout.setContentsMargins(self.MARGINS, self.MARGINS, self.MARGINS, self.MARGINS)
        self.titleBar = TitleBar()
        layout.addWidget(self.titleBar)
        self.setLayout(layout)

        self.titleBar.windowMinimumed.connect(self.showMinimized)
        self.titleBar.windowMaximumed.connect(self.showMaximized)
        self.titleBar.windowNormaled.connect(self.showNormal)
        self.titleBar.windowClosed.connect(self.close)
        self.titleBar.windowMoved.connect(self.move)
        self.titleBar.mouseRelease.connect(self.myMouseReleaseEvent)
        self.titleBar.mouseMove.connect(self.myMouseMoveEvent)
        self.windowTitleChanged.connect(self.titleBar.setTitle)
        self.windowIconChanged.connect(self.titleBar.setIcon)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon("TrayIcon.png"))
        self.show_action = QAction("Показать", self)
        self.quit_action = QAction("Закрыть", self)
        self.hide_action = QAction("Спрятать", self)
        self.show_action.triggered.connect(self.show)
        self.hide_action.triggered.connect(self.hide)
        self.quit_action.triggered.connect(qApp.quit)
        self.tray_menu = QMenu()
        self.tray_menu.addAction(self.hide_action)
        self.tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def settrayFunctions(self):
        self.tray_menu.addAction(self.quit_action)

    def trayEvent(self, a):
        if a:
            self.tray_menu.clear()
            self.tray_menu.addAction(self.show_action)
        else:
            self.tray_menu.clear()
            self.tray_menu.addAction(self.hide_action)
        self.settrayFunctions()

    def hideEvent(self, a0: QtGui.QHideEvent) -> None:
        self.trayEvent(True)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        self.trayEvent(False)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def setTitleBarHeight(self, height=35):
        """ Установка высоты строки заголовка """
        self.titleBar.setHeight(height)

    def setIconSize(self, size):
        """ Установка размера значка """
        self.titleBar.setIconSize(size)

    def setWidget(self, widget):
        """ Настройте свои собственные элементы управления """

        self._widget = widget

        # Установите цвет фона по умолчанию, иначе он будет прозрачным из-за влияния родительского окна
        self._widget.setAutoFillBackground(True)
        palette = self._widget.palette()
        palette.setColor(palette.Window, QColor(240, 240, 240))
        self._widget.setPalette(palette)
        self._widget.installEventFilter(self)
        self.layout().addWidget(self._widget)

    def move(self, pos):
        if self.windowState() == Qt.WindowMaximized or self.windowState() == Qt.WindowFullScreen:
            # Максимизировать или полноэкранный режим не допускается
            return

        super().move(pos)

    def showMaximized(self):
        """ Чтобы максимизировать, удалите верхнюю, нижнюю, левую и правую границы.
            Если вы не удалите его, в пограничной области будут пробелы. """

        super().showMaximized()

        self.layout().setContentsMargins(0, 0, 0, 0)

    def showNormal(self):
        """ Восстановить, сохранить верхнюю и нижнюю левую и правую границы,
            иначе нет границы, которую нельзя отрегулировать """
        super().showNormal()

        self.layout().setContentsMargins(self.MARGINS, self.MARGINS, self.MARGINS, self.MARGINS)

    def eventFilter(self, obj, event):
        """ Фильтр событий, используемый для решения мыши в других элементах
            управления и восстановления стандартного стиля мыши """
        if isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)

        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        """ Поскольку это полностью прозрачное фоновое окно, жесткая для поиска
            граница с прозрачностью 1 рисуется в событии перерисовывания, чтобы отрегулировать размер окна. """
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 255, 1), 2 * self.MARGINS))
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        """ Событие клика мыши """
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._old_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """ Событие отказов мыши """
        super().mouseReleaseEvent(event)

        self._old_pos = None
        self._direction = None

    def myMouseReleaseEvent(self):
        if self.pos().y() <= -7:
            self.titleBar.showMaximized()

    def myMouseMoveEvent(self, event):
        if self.isFullScreen() or self.isMaximized():
            self.titleBar.showMaximized()
            self.move(event.pos())

    def mouseMoveEvent(self, event):
        """ Событие перемещения мыши """
        super().mouseMoveEvent(event)

        pos = event.pos()
        xPos, yPos = pos.x(), pos.y()
        wm, hm = self.width() - self.MARGINS, self.height() - self.MARGINS

        if self.isMaximized() or self.isFullScreen():
            self._direction = None
            self.setCursor(Qt.ArrowCursor)
            return

        if event.buttons() == Qt.LeftButton and self._old_pos:
            self._resizeWidget(pos)
            return

        if xPos <= self.MARGINS and yPos <= self.MARGINS:
            # Верхний левый угол
            self._direction = Direction.LEFT_TOP
            self.setCursor(Qt.SizeFDiagCursor)

        elif wm <= xPos <= self.width() and hm <= yPos <= self.height():
            # Нижний правый угол
            self._direction = Direction.RIGHT_BOTTOM
            self.setCursor(Qt.SizeFDiagCursor)

        elif wm <= xPos and yPos <= self.MARGINS:
            # верхний правый угол
            self._direction = Direction.RIGHT_TOP
            self.setCursor(Qt.SizeBDiagCursor)

        elif xPos <= self.MARGINS and hm <= yPos:
            # Нижний левый угол
            self._direction = Direction.LEFT_BOTTOM
            self.setCursor(Qt.SizeBDiagCursor)

        elif 0 <= xPos <= self.MARGINS and self.MARGINS <= yPos <= hm:
            # Влево
            self._direction = Direction.LEFT
            self.setCursor(Qt.SizeHorCursor)

        elif wm <= xPos <= self.width() and self.MARGINS <= yPos <= hm:
            # Право
            self._direction = Direction.RIGHT
            self.setCursor(Qt.SizeHorCursor)

        elif self.MARGINS <= xPos <= wm and 0 <= yPos <= self.MARGINS:
            # выше
            self._direction = Direction.TOP
            self.setCursor(Qt.SizeVerCursor)

        elif self.MARGINS <= xPos <= wm and hm <= yPos <= self.height():
            # ниже
            self._direction = Direction.BOTTOM
            self.setCursor(Qt.SizeVerCursor)

        else:
            # Курсор по умолчанию
            self.setCursor(Qt.ArrowCursor)

    def _resizeWidget(self, pos):
        """ Отрегулируйте размер окна """
        if self._direction is None:
            return

        mpos = pos - self._old_pos
        xPos, yPos = mpos.x(), mpos.y()
        geometry = self.geometry()
        x, y, w, h = geometry.x(), geometry.y(), geometry.width(), geometry.height()

        if self._direction == Direction.LEFT_TOP:          # Верхний левый угол
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos

            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos

        elif self._direction == Direction.RIGHT_BOTTOM:    # Нижний правый угол
            if w + xPos > self.minimumWidth():
                w += xPos
                self._old_pos = pos

            if h + yPos > self.minimumHeight():
                h += yPos
                self._old_pos = pos

        elif self._direction == Direction.RIGHT_TOP:       # верхний правый угол
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos

            if w + xPos > self.minimumWidth():
                w += xPos
                self._old_pos.setX(pos.x())

        elif self._direction == Direction.LEFT_BOTTOM:     # Нижний левый угол
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos

            if h + yPos > self.minimumHeight():
                h += yPos
                self._old_pos.setY(pos.y())

        elif self._direction == Direction.LEFT:            # Влево
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            else:
                return

        elif self._direction == Direction.RIGHT:           # Право
            if w + xPos > self.minimumWidth():
                w += xPos
                self._old_pos = pos
            else:
                return

        elif self._direction == Direction.TOP:             # выше
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            else:
                return

        elif self._direction == Direction.BOTTOM:          # ниже
            if h + yPos > self.minimumHeight():
                h += yPos
                self._old_pos = pos
            else:
                return

        self.setGeometry(x, y, w, h)


class MainDialog(QtWidgets.QDialog):
    MARGINS = 7

    def __init__(self, widget, signal, title):
        super().__init__()
        self.setStyleSheet(MyMainWindow.qss)
        self.setupUi()
        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon("TrayIcon.png"))

        self._old_pos = None
        self._direction = None
        self._widget = None
        self.setWidget(widget)
        signal.connect(self.close)
        self.sig = signal
        self.exec_()

    def setupUi(self):
        self.resize(425, 600)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        layout = QVBoxLayout(spacing=0)
        layout.setContentsMargins(self.MARGINS, self.MARGINS, self.MARGINS, self.MARGINS)
        self.titleBar = TitleBar()
        layout.addWidget(self.titleBar)
        self.setLayout(layout)

        self.titleBar.windowMinimumed.connect(self.showMinimized)
        self.titleBar.windowMaximumed.connect(self.showMaximized)
        self.titleBar.windowNormaled.connect(self.showNormal)
        self.titleBar.windowClosed.connect(self.close)
        self.titleBar.windowMoved.connect(self.move)
        self.titleBar.mouseRelease.connect(self.myMouseReleaseEvent)
        self.titleBar.mouseMove.connect(self.myMouseMoveEvent)
        self.windowTitleChanged.connect(self.titleBar.setTitle)
        self.windowIconChanged.connect(self.titleBar.setIcon)

    def closeEvent(self, event):
        self.sig.emit()
        super().closeEvent(event)

    def setTitleBarHeight(self, height=35):
        """ Установка высоты строки заголовка """
        self.titleBar.setHeight(height)

    def setIconSize(self, size):
        """ Установка размера значка """
        self.titleBar.setIconSize(size)

    def setWidget(self, widget):
        """ Настройте свои собственные элементы управления """

        self._widget = widget

        # Установите цвет фона по умолчанию, иначе он будет прозрачным из-за влияния родительского окна
        self._widget.setAutoFillBackground(True)
        palette = self._widget.palette()
        palette.setColor(palette.Window, QColor(240, 240, 240))
        self._widget.setPalette(palette)
        self._widget.installEventFilter(self)
        self.layout().addWidget(self._widget)

    def move(self, pos):
        if self.windowState() == Qt.WindowMaximized or self.windowState() == Qt.WindowFullScreen:
            # Максимизировать или полноэкранный режим не допускается
            return

        super().move(pos)

    def showMaximized(self):
        """ Чтобы максимизировать, удалите верхнюю, нижнюю, левую и правую границы.
            Если вы не удалите его, в пограничной области будут пробелы. """

        super().showMaximized()

        self.layout().setContentsMargins(0, 0, 0, 0)

    def showNormal(self):
        """ Восстановить, сохранить верхнюю и нижнюю левую и правую границы,
            иначе нет границы, которую нельзя отрегулировать """
        super().showNormal()

        self.layout().setContentsMargins(self.MARGINS, self.MARGINS, self.MARGINS, self.MARGINS)

    def eventFilter(self, obj, event):
        """ Фильтр событий, используемый для решения мыши в других элементах
            управления и восстановления стандартного стиля мыши """
        if isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)

        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        """ Поскольку это полностью прозрачное фоновое окно, жесткая для поиска
            граница с прозрачностью 1 рисуется в событии перерисовывания, чтобы отрегулировать размер окна. """
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 255, 1), 2 * self.MARGINS))
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        """ Событие клика мыши """
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._old_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """ Событие отказов мыши """
        super().mouseReleaseEvent(event)

        self._old_pos = None
        self._direction = None

    def myMouseReleaseEvent(self):
        if self.pos().y() <= -7:
            self.titleBar.showMaximized()

    def myMouseMoveEvent(self, event):
        if self.isFullScreen() or self.isMaximized():
            self.titleBar.showMaximized()
            self.move(event.pos())

    def mouseMoveEvent(self, event):
        """ Событие перемещения мыши """
        super().mouseMoveEvent(event)

        pos = event.pos()
        xPos, yPos = pos.x(), pos.y()
        wm, hm = self.width() - self.MARGINS, self.height() - self.MARGINS

        if self.isMaximized() or self.isFullScreen():
            self._direction = None
            self.setCursor(Qt.ArrowCursor)
            return

        if event.buttons() == Qt.LeftButton and self._old_pos:
            self._resizeWidget(pos)
            return

        if xPos <= self.MARGINS and yPos <= self.MARGINS:
            # Верхний левый угол
            self._direction = Direction.LEFT_TOP
            self.setCursor(Qt.SizeFDiagCursor)

        elif wm <= xPos <= self.width() and hm <= yPos <= self.height():
            # Нижний правый угол
            self._direction = Direction.RIGHT_BOTTOM
            self.setCursor(Qt.SizeFDiagCursor)

        elif wm <= xPos and yPos <= self.MARGINS:
            # верхний правый угол
            self._direction = Direction.RIGHT_TOP
            self.setCursor(Qt.SizeBDiagCursor)

        elif xPos <= self.MARGINS and hm <= yPos:
            # Нижний левый угол
            self._direction = Direction.LEFT_BOTTOM
            self.setCursor(Qt.SizeBDiagCursor)

        elif 0 <= xPos <= self.MARGINS and self.MARGINS <= yPos <= hm:
            # Влево
            self._direction = Direction.LEFT
            self.setCursor(Qt.SizeHorCursor)

        elif wm <= xPos <= self.width() and self.MARGINS <= yPos <= hm:
            # Право
            self._direction = Direction.RIGHT
            self.setCursor(Qt.SizeHorCursor)

        elif self.MARGINS <= xPos <= wm and 0 <= yPos <= self.MARGINS:
            # выше
            self._direction = Direction.TOP
            self.setCursor(Qt.SizeVerCursor)

        elif self.MARGINS <= xPos <= wm and hm <= yPos <= self.height():
            # ниже
            self._direction = Direction.BOTTOM
            self.setCursor(Qt.SizeVerCursor)

        else:
            # Курсор по умолчанию
            self.setCursor(Qt.ArrowCursor)

    def _resizeWidget(self, pos):
        """ Отрегулируйте размер окна """
        if self._direction is None:
            return

        mpos = pos - self._old_pos
        xPos, yPos = mpos.x(), mpos.y()
        geometry = self.geometry()
        x, y, w, h = geometry.x(), geometry.y(), geometry.width(), geometry.height()

        if self._direction == Direction.LEFT_TOP:          # Верхний левый угол
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos

            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos

        elif self._direction == Direction.RIGHT_BOTTOM:    # Нижний правый угол
            if w + xPos > self.minimumWidth():
                w += xPos
                self._old_pos = pos

            if h + yPos > self.minimumHeight():
                h += yPos
                self._old_pos = pos

        elif self._direction == Direction.RIGHT_TOP:       # верхний правый угол
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos

            if w + xPos > self.minimumWidth():
                w += xPos
                self._old_pos.setX(pos.x())

        elif self._direction == Direction.LEFT_BOTTOM:     # Нижний левый угол
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos

            if h + yPos > self.minimumHeight():
                h += yPos
                self._old_pos.setY(pos.y())

        elif self._direction == Direction.LEFT:            # Влево
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            else:
                return

        elif self._direction == Direction.RIGHT:           # Право
            if w + xPos > self.minimumWidth():
                w += xPos
                self._old_pos = pos
            else:
                return

        elif self._direction == Direction.TOP:             # выше
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            else:
                return

        elif self._direction == Direction.BOTTOM:          # ниже
            if h + yPos > self.minimumHeight():
                h += yPos
                self._old_pos = pos
            else:
                return

        self.setGeometry(x, y, w, h)
