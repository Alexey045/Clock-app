import os
import random
import shutil
import sys
import time
from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu, qApp, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QTimer
from lib import *
from lib2 import *
import sqlite3
import threading


class ReadOnlyDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return


class MySettingsAlarmDialog(QtWidgets.QWidget, MySettingsAlarmDialog_Form):
    qss = """
        QWidget {
            background-color: #202020;
            color: #BBBBBB;
            border-color: #BBBBBB;
        }
        QPushButton {
            background-color: rgb(22, 22, 22);
            color: #FFFFFF;
        }
        QPushButton::pressed {
            background-color: rgb(45, 45, 45);
            color: #FFFFFF;
        }
        QListWidget {
            border: 0px;
        }
        """
    signal = pyqtSignal()

    def __init__(self, mainwindow, id, con, cur):
        self.con, self.cur = con, cur
        self.id = id
        self.md = None
        super().__init__()
        self.backwidget = QtWidgets.QWidget(self)
        self.backwidget.setGeometry(QtCore.QRect(0, 0, 3000, 3000))
        self.setStyleSheet(self.qss)
        self.setupUi(self)
        self.mainwindow = mainwindow
        self.state = 0
        self.pushButton.clicked.connect(self.MelodyDialog)
        self.buttonBox.accepted.connect(self.ok_pressed)
        self.buttonBox.rejected.connect(self.cancel_pressed)
        self.set_values()

    def set_values(self):
        res = self.cur.execute(f"SELECT * FROM Alarm WHERE AlarmId = {self.id}").fetchone()
        # Показ состояния чекбоксов
        self.c = {0: self.checkBox, 1: self.checkBox_2, 2: self.checkBox_3,
                  3: self.checkBox_4, 4: self.checkBox_5, 5: self.checkBox_6,
                  6: self.checkBox_7}
        if res[4]:
            days = str(res[4])
            days = "0" * (7 - len(days)) + days
            for index, i in enumerate(days):
                if i == "1":
                    self.c[index].setChecked(True)
        # Показ названия
        if res[3]:
            self.lineEdit.setText(str(res[3]))
        # Показ мелодии
        if res[2]:
            melody = self.cur.execute(
                f"SELECT Title FROM Ringtone WHERE RingId = {res[2]}").fetchone()
            self.label_6.setText(melody[0])
        # Показ времени
        if res[1]:
            h, m = res[1].split(":")
            self.spinBox.setValue(int(h))
            self.spinBox_2.setValue(int(m))
        # Инициализация громкости
        if res[6]:
            self.volume = res[6]
        else:
            self.volume = 100

    def ok_pressed(self):
        h, m, days, title, melody = self.spinBox.value(), self.spinBox_2.value(), \
                                    "".join(
                                        ["1" if i.isChecked() else "0" for i in self.c.values()]), \
                                    self.lineEdit.text(), \
                                    self.cur.execute(
                                        f"""SELECT RingId FROM Ringtone
WHERE Title = '{self.label_6.text()}'""").fetchone()[0]
        self.cur.execute(
            f"""UPDATE Alarm SET AlarmTime = '{h}:{'0' if len(str(
                m)) == 1 else ''}{m}' WHERE AlarmId = {self.id}""")
        self.cur.execute(f"UPDATE Alarm SET Title = '{title}' WHERE AlarmId = {self.id}")
        self.cur.execute(f"UPDATE Alarm SET Days = '{days}' WHERE AlarmId = {self.id}")
        if self.md:
            self.cur.execute(f"UPDATE Alarm SET RingId = '{melody}' WHERE AlarmId = {self.id}")
            self.cur.execute(f"UPDATE Alarm SET Volume = '{self.volume}' WHERE AlarmId = {self.id}")
        self.con.commit()
        self.mainwindow.alarm_update()
        self.signal.emit()

    def cancel_pressed(self):
        self.signal.emit()

    def MelodyDialog(self):
        melody_dialog = MyMelodyDialog(self, id=self.id, alarm_or_timer=True)
        self.melody = MainDialog(melody_dialog, melody_dialog.signal, "Выбор мелодии")._widget
        self.md = self.melody.rs
        self.volume = self.melody.value_sound
        if self.md:
            self.label_6.setText(self.md)


class MySettingsTimerDialog(QtWidgets.QWidget, MySettingsTimerDialog_Form):
    qss = """
        QWidget {
            background-color: #202020;
            color: #BBBBBB;
            border-color: #BBBBBB;
        }
        QPushButton {
            background-color: rgb(22, 22, 22);
            color: #FFFFFF;
        }
        QPushButton::pressed {
            background-color: rgb(45, 45, 45);
            color: #FFFFFF;
        }
        QListWidget {
            border: 0px;
        }
        """
    signal = pyqtSignal()

    def __init__(self, mainwindow, id, con, cur):
        self.con, self.cur = con, cur
        self.id = id
        self.md = None
        super().__init__()
        self.backwidget = QtWidgets.QWidget(self)
        self.backwidget.setGeometry(QtCore.QRect(0, 0, 3000, 3000))
        self.setStyleSheet(self.qss)
        self.setupUi(self)
        self.mainwindow = mainwindow
        self.state = 0
        self.pushButton.clicked.connect(self.MelodyDialog)
        self.buttonBox.accepted.connect(self.ok_pressed)
        self.buttonBox.rejected.connect(self.cancel_pressed)
        self.set_values()

    def set_values(self):
        res = self.cur.execute(f"SELECT * FROM Timer WHERE TimerId = {self.id}").fetchone()
        # Показ названия
        if res[3]:
            self.lineEdit.setText(str(res[3]))
        # Показ мелодии
        if res[2]:
            melody = self.cur.execute(
                f"SELECT Title FROM Ringtone WHERE RingId = {res[2]}").fetchone()
            self.label_6.setText(melody[0])
        # Показ времени
        if res[1]:
            h, m, s = res[1].split(":")
            self.spinBox.setValue(int(h))
            self.spinBox_2.setValue(int(m))
            self.spinBox_3.setValue(int(s))
        # Инициализация громкости
        if res[5]:
            self.volume = res[5]
        else:
            self.volume = 100

    def ok_pressed(self):
        h, m, s, title, melody = self.spinBox.value(), self.spinBox_2.value(), \
                                 self.spinBox_3.value(), \
                                 self.lineEdit.text(), \
                                 self.cur.execute(
                                     f"""SELECT RingId FROM Ringtone
WHERE Title = '{self.label_6.text()}'""").fetchone()[0]
        self.cur.execute(
            f"""UPDATE Timer SET Time = '{'0' if len(str(h)) == 1 else ''}{h}:{'0' if len(str(
        m)) == 1 else ''}{m}:{'0' if len(str(s)) == 1 else ''}{s}' WHERE TimerId = {self.id}""")
        self.cur.execute(f"UPDATE Timer SET Title = '{title}' WHERE TimerId = {self.id}")
        if self.md:
            self.cur.execute(f"UPDATE Timer SET Volume = '{self.volume}' WHERE TimerId = {self.id}")
            self.cur.execute(f"UPDATE Timer SET RingId = '{melody}' WHERE TimerId = {self.id}")
        self.con.commit()
        self.mainwindow.timer_update()
        self.signal.emit()

    def cancel_pressed(self):
        self.signal.emit()

    def MelodyDialog(self):
        melody_dialog = MyMelodyDialog(self, id=self.id, alarm_or_timer=False)
        self.melody = MainDialog(melody_dialog, melody_dialog.signal, "Выбор мелодии")._widget

        self.md = self.melody.rs
        self.volume = self.melody.value_sound
        if self.md:
            self.label_6.setText(self.md)


class MyMelodyDialog(QtWidgets.QWidget, MyMelodyDialog_Form):
    qss = """
    QWidget {
        background-color: #202020;
        color: #BBBBBB;
        border-color: #BBBBBB;
    }
    QPushButton {
        background-color: rgb(22, 22, 22);
        color: #FFFFFF;
    }
    QPushButton::pressed {
        background-color: rgb(45, 45, 45);
        color: #FFFFFF;
    }
    QListWidget {
        border: 0px;
    }
    """
    rs = None
    value_sound = None
    signal = pyqtSignal()

    def __init__(self, mainwindow, melody="", id=None, alarm_or_timer=True):
        super().__init__()
        self.rs = melody
        self.signal.connect(self.closeEvent)
        self.backwidget = QtWidgets.QWidget(self)
        self.backwidget.setGeometry(QtCore.QRect(0, 0, 3000, 3000))
        self.setStyleSheet(self.qss)
        self.setupUi(self)
        self.mainwindow = mainwindow
        self.buttonBox.accepted.connect(self.ok_pressed)
        self.buttonBox.rejected.connect(self.cancel_pressed)
        self.pushButton_2.clicked.connect(self.plus)
        self.pushButton_3.clicked.connect(self.delete)
        self.con = sqlite3.connect("clock.sqlite")
        self.cur = self.con.cursor()
        res = self.cur.execute("select Title, Link from Ringtone").fetchall()
        self.res = {k: v for k, v in res}
        self.listWidget.addItems(self.res.keys())
        self.pushButton.clicked.connect(self.play)
        self.sound = QtMultimedia.QSoundEffect()
        self.horizontalSlider.setRange(0, 100)
        if id:
            if alarm_or_timer:
                volume = self.cur.execute(
                    f"SELECT Volume FROM Alarm WHERE AlarmId = {id}").fetchone()[0]
                if volume:
                    self.horizontalSlider.setValue(volume)
                else:
                    self.horizontalSlider.setValue(100)
            else:
                volume = self.cur.execute(
                    f"SELECT Volume FROM Timer WHERE TimerId = {id}").fetchone()[0]
                if volume:
                    self.horizontalSlider.setValue(volume)
                else:
                    self.horizontalSlider.setValue(100)
        else:
            self.horizontalSlider.setValue(100)
        self.horizontalSlider.valueChanged.connect(self.volumeChangeEvent)
        self.state = 0
        self.pushButton.setIcon(QtGui.QIcon("play.png"))
        self.pushButton_2.setIcon(QtGui.QIcon("plus.png"))
        self.pushButton_3.setIcon(QtGui.QIcon("minus.png"))

    def play(self):
        if not self.state:
            self.pushButton.setIcon(QtGui.QIcon("pause.png"))
            self.state = 2
            if not self.listWidget.currentItem():
                QMessageBox.critical(self, "Ошибка!", "Выберите рингтон.",
                                     QMessageBox.Ok)
                self.pushButton.click()
                return
            item = self.listWidget.currentItem().text()
            self.sound.setSource(QtCore.QUrl.fromLocalFile(self.res[item]))
            self.sound.setLoopCount(QtMultimedia.QSoundEffect.Infinite)
            self.sound.play()
        else:
            self.pushButton.setIcon(QtGui.QIcon("play.png"))
            self.state = 0
            self.sound.stop()

    def volumeChangeEvent(self):
        self.sound.setVolume(self.horizontalSlider.value() / 100)

    def ok_pressed(self):
        if not self.listWidget.currentItem():
            QMessageBox.critical(self, "Ошибка!", "Выберите рингтон.",
                                 QMessageBox.Ok)
            return
        self.rs = self.listWidget.currentItem().text()
        self.value_sound = self.horizontalSlider.value()
        self.pushButton.click()
        self.signal.emit()

    def cancel_pressed(self):
        self.signal.emit()

    def closeEvent(self, a0=None) -> None:
        self.sound.stop()

    def plus(self):
        flag = False
        filter = "Wav File (*.wav)"
        fname = QFileDialog.getOpenFileName(self, 'Choose file', '/', filter)[0]
        if os.path.exists(fname):
            self.con = sqlite3.connect("clock.sqlite")
            self.cur = self.con.cursor()
            check = self.cur.execute(f"""select * from ringtone where title = '{os.path.basename(
                fname).rstrip('.wav')}'""").fetchall()
            if len(check) == 0:
                shutil.move(fname, 'ringtones')
            else:
                QMessageBox.critical(self, "Ошибка!", "Элемент с таким названием существует!",
                                     QMessageBox.Ok)
                flag = True
        if fname == '':
            pass
        else:
            if flag:
                pass
            else:
                self.con = sqlite3.connect("clock.sqlite")
                self.cur = self.con.cursor()
                self.cur.execute(f"""insert into Ringtone(title, link) values (?, ?)""", (
                    os.path.basename(fname).rstrip('.wav'),
                       f'ringtones\{os.path.basename(fname)}'))
                self.con.commit()
                res = self.cur.execute("select Title, Link from Ringtone").fetchall()
                self.res = {k: v for k, v in res}
                self.cur.close()
                self.con.close()
                self.listWidget.clear()
                self.listWidget.addItems(self.res.keys())

    def delete(self):
        if not self.listWidget.currentItem():
            QMessageBox.critical(self, "Ошибка!", "Выберите элемент, который хотите удалить.",
                                 QMessageBox.Ok)
        else:
            self.con = sqlite3.connect("clock.sqlite")
            self.cur = self.con.cursor()
            standard_ringid = [i for i in range(1, 23)]
            if self.cur.execute(f"""select RingId from Ringtone where title = '{
                self.listWidget.currentItem().text()}'""").fetchone()[0] in standard_ringid:
                QMessageBox.critical(self, "Ошибка!", "Нельзя удалять стандартные рингтоны.",
                                     QMessageBox.Ok)
            else:
                self.cur.execute(f"""update Alarm set RingId = {random.choice(
                    standard_ringid)} where RingId = (select RingId from Ringtone where title = '{
                    self.listWidget.currentItem().text()}')""")
                self.cur.execute(f"""update Timer set RingId = {random.choice(
                    standard_ringid)} where RingId = (select RingId from Ringtone where title = '{
                    self.listWidget.currentItem().text()}')""")
                link = self.cur.execute(f"""select Link from Ringtone where title = '{
                    self.listWidget.currentItem().text()}'""").fetchone()[0]
                os.remove(f'{link}')
                self.cur.execute(
                    f"""delete from Ringtone where title = '{
                    self.listWidget.currentItem().text()}'""")
                self.con.commit()
                res = self.cur.execute("select Title, Link from Ringtone").fetchall()
                self.res = {k: v for k, v in res}
            self.cur.close()
            self.con.close()
            self.listWidget.clear()
            self.listWidget.addItems(self.res.keys())


class MyMainWindow(QtWidgets.QWidget):
    qss = '''
        QWidget {
            background-color: #232323;
            color: #BBBBBB;
            border-color: #BBBBBB;
        } 
        ::tab {
            background: rgb(0, 0, 0);
            color: white;
        } 
        ::tab:selected {
            background-color: rgb(50, 50, 50);
            color: #BBBBBB;
        } 
        QTabWidget::pane {
            border: 0px;
        }
        QTabWidget::tab-bar {
            color: red;
            background-color: red;
        }
        QHeaderView::section {
            background: rgb(23, 23, 23);
            color: white;
        }
        QTableWidget {
            border: 0px;
        }
        QPushButton {
            background-color: #232323;
            color: #ffffff;
        }
        QTableWidget QTableCornerButton::section {
            background: rgb(0, 0, 0);
            color: white;
        }
        '''
    qss_btn = '''
        QPushButton {
            background-color: #232323;
            color: #ffffff;
        }'''
    alarm_signal = pyqtSignal()
    timer_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.con = sqlite3.connect("clock.sqlite")
        self.cur = self.con.cursor()
        self.timer2_btns = []
        self.setupUi()
        self.alarm_signal.connect(self.alarm_check)
        self.timer_signal.connect(self.timer_check)

        self.past_local_s_alarm = time.localtime(time.time())[5]
        self.past_local_s_timer = time.localtime(time.time())[5]
        self.mythread = threading.Thread(target=self.time_tick)
        self.mythread.start()

    def setupUi(self):
        self.resize(411, 560)
        self.setStyleSheet(self.qss)
        self.setMinimumSize(232, 250)
        self.system_icon = QtGui.QIcon("TrayIcon.png")
        self.backwidget = QtWidgets.QWidget(self)
        self.backwidget.setGeometry(QtCore.QRect(0, 0, 3000, 3000))
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setIconSize(QtCore.QSize(30, 30))
        # 1ая вкладка
        self.tab = QtWidgets.QWidget()
        self.tabWidget.addTab(self.tab, QtGui.QIcon("b.png"), "Будильник")
        self.alarm_table_widget = QtWidgets.QTableWidget(self.tab)
        self.alarm_table_widget.resize(QtCore.QSize(411, 480))
        self.alarm_table_widget.setColumnCount(5)
        self.alarm_table_widget.setRowCount(0)
        self.alarm_table_widget.setHorizontalHeaderLabels(
            ["Название", "Время", "Мелодия", " ", "Состояние"])
        delegate_alarm = ReadOnlyDelegate(self.alarm_table_widget)
        self.alarm_table_widget.setItemDelegateForColumn(0, delegate_alarm)
        self.alarm_table_widget.setItemDelegateForColumn(1, delegate_alarm)
        self.alarm_table_widget.setItemDelegateForColumn(2, delegate_alarm)
        self.alarm_set()  # считывание базы данных и внос данных в таблицу

        self.btn_plus_alarm = QtWidgets.QPushButton(self.tab)
        self.btn_plus_alarm.resize(QtCore.QSize(44, 40))
        self.btn_plus_alarm.setIcon(QtGui.QIcon("plus.png"))
        self.btn_plus_alarm.clicked.connect(self.alarm_add)

        self.btn_minus_alarm = QtWidgets.QPushButton(self.tab)
        self.btn_minus_alarm.resize(QtCore.QSize(44, 40))
        self.btn_minus_alarm.setIcon(QtGui.QIcon("minus.png"))
        self.btn_minus_alarm.clicked.connect(self.alarm_delete)
        # 2ая вкладка
        self.tab_2 = QtWidgets.QWidget()
        self.tabWidget.addTab(self.tab_2, QtGui.QIcon("m.png"), "Часы")
        self.clocks_table_widget = QtWidgets.QTableWidget(self.tab_2)
        self.clocks_table_widget.resize(QtCore.QSize(411, 480))
        self.clocks_table_widget.setColumnCount(2)
        self.clocks_table_widget.setRowCount(0)
        self.clocks_table_widget.setHorizontalHeaderLabels(
            ["Название", "Время"])
        delegate_alarm = ReadOnlyDelegate(self.clocks_table_widget)
        self.clocks_table_widget.setItemDelegateForColumn(0, delegate_alarm)
        self.clocks_table_widget.setItemDelegateForColumn(1, delegate_alarm)

        self.btn_plus_clocks = QtWidgets.QPushButton(self.tab_2)
        self.btn_plus_clocks.resize(QtCore.QSize(44, 40))
        self.btn_plus_clocks.setIcon(QtGui.QIcon("plus.png"))
        self.btn_plus_clocks.clicked.connect(self.clock_add)

        self.btn_minus_clocks = QtWidgets.QPushButton(self.tab_2)
        self.btn_minus_clocks.resize(QtCore.QSize(44, 40))
        self.btn_minus_clocks.setIcon(QtGui.QIcon("minus.png"))
        self.btn_minus_clocks.clicked.connect(self.clock_delete)

        self.clock_combobox = QtWidgets.QComboBox(self.tab_2)
        self.clock_combobox.resize(QtCore.QSize(100, 40))
        res_clock = self.cur.execute("SELECT * FROM Clocks").fetchall()
        self.clock_dict = {b: a for a, b, c in res_clock}
        self.clock_combobox.addItems(self.clock_dict.keys())

        self.clocks_set()
        # 3яя вкладка
        self.tab_3 = QtWidgets.QWidget()
        self.tabWidget.addTab(self.tab_3, QtGui.QIcon("t.png"), "Таймер")
        self.timer_table_widget = QtWidgets.QTableWidget(self.tab_3)
        self.timer_table_widget.resize(QtCore.QSize(411, 480))
        self.timer_table_widget.setColumnCount(7)
        self.timer_table_widget.setRowCount(0)
        self.timer_table_widget.setHorizontalHeaderLabels(
            ["Название", "Время", "Ост. Время", "Мелодия", " ", " ", " "])
        delegate_timer = ReadOnlyDelegate(self.timer_table_widget)
        self.timer_table_widget.setItemDelegateForColumn(0, delegate_timer)
        self.timer_table_widget.setItemDelegateForColumn(1, delegate_timer)
        self.timer_table_widget.setItemDelegateForColumn(2, delegate_timer)
        self.timer_table_widget.setItemDelegateForColumn(3, delegate_timer)

        self.timer_set()

        self.btn_plus_timer = QtWidgets.QPushButton(self.tab_3)
        self.btn_plus_timer.resize(QtCore.QSize(44, 40))
        self.btn_plus_timer.setIcon(QtGui.QIcon("plus.png"))
        self.btn_plus_timer.clicked.connect(self.timer_add)

        self.btn_minus_timer = QtWidgets.QPushButton(self.tab_3)
        self.btn_minus_timer.resize(QtCore.QSize(44, 40))
        self.btn_minus_timer.setIcon(QtGui.QIcon("minus.png"))
        self.btn_minus_timer.clicked.connect(self.timer_delete)
        # 4ая вкладка
        self.tab_4 = QtWidgets.QWidget()
        self.sec_start_flag = True
        self.sec_count = 0
        self.sec_label = QtWidgets.QLabel(self.tab_4)
        self.sec_label.setText(f'')
        self.sec_label.setStyleSheet("border : 4px solid white;")
        self.sec_list_widget = QtWidgets.QListWidget(self.tab_4)
        self.sec_label.setText(str(self.sec_count))
        self.sec_start_btn = QtWidgets.QPushButton(self.tab_4)
        self.sec_cycle_btn = QtWidgets.QPushButton(self.tab_4)
        self.sec_reset_btn = QtWidgets.QPushButton(self.tab_4)
        self.sec_start_btn.setText('start')
        self.sec_cycle_btn.setText('cycle')
        self.sec_reset_btn.setText('reset')
        self.sec_start_btn.resize(QtCore.QSize(44, 40))
        self.sec_cycle_btn.resize(QtCore.QSize(44, 40))
        self.sec_reset_btn.resize(QtCore.QSize(44, 40))
        self.sec_start_btn.clicked.connect(self.sec_start)
        self.sec_cycle_btn.clicked.connect(self.sec_cycle)
        self.sec_reset_btn.clicked.connect(self.sec_reset)
        timer = QTimer(self)
        timer.timeout.connect(self.show_time)
        timer.start(100)
        self.tabWidget.addTab(self.tab_4, QtGui.QIcon("s.png"), "Секундомер")
        self.verticalLayout.addWidget(self.tabWidget)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        x, y = self.size().width(), self.size().height()  # считываем размеры окна
        if x < 411:
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), "")
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), "")
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), "")
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), "")
        elif x >= 411:
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), "Будильник")
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), "Часы")
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), "Таймер")
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), "Секундомер")
        self.alarm_table_widget.resize(x, self.alarm_table_widget.size().height())
        self.timer_table_widget.resize(x, self.timer_table_widget.size().height())
        self.clocks_table_widget.resize(x, self.clocks_table_widget.size().height())
        self.clock_combobox.resize(QtCore.QSize(x - 89, self.clock_combobox.size().height()))
        self.sec_label.resize(x, self.sec_label.size().height())
        self.sec_list_widget.resize(QtCore.QSize(x, y - 80 - self.sec_label.size().height()))
        self.sec_list_widget.move(0, self.sec_label.size().height())

        self.alarm_table_widget.resize(self.alarm_table_widget.size().width(), y - 80)
        self.timer_table_widget.resize(self.timer_table_widget.size().width(), y - 80)
        self.clocks_table_widget.resize(self.clocks_table_widget.size().width(), y - 80)

        self.alarm_table_widget.horizontalHeader(). \
            setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.alarm_table_widget.horizontalHeader(). \
            setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.alarm_table_widget.horizontalHeader(). \
            setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.alarm_table_widget.horizontalHeader(). \
            setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)

        self.clocks_table_widget.horizontalHeader(). \
            setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.clocks_table_widget.horizontalHeader(). \
            setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.btn_plus_clocks.move(x - 89, y - 80)
        self.btn_minus_clocks.move(x - 45, y - 80)
        self.clock_combobox.move(0, y - 80)

        self.timer_table_widget.horizontalHeader(). \
            setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.timer_table_widget.horizontalHeader(). \
            setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.timer_table_widget.horizontalHeader(). \
            setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.timer_table_widget.horizontalHeader(). \
            setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        self.timer_table_widget.horizontalHeader(). \
            setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        self.timer_table_widget.horizontalHeader(). \
            setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        self.btn_plus_timer.move(x - 89, y - 80)
        self.btn_minus_timer.move(x - 45, y - 80)

        self.btn_plus_alarm.move(x - 89, y - 80)
        self.btn_minus_alarm.move(x - 45, y - 80)
        self.sec_start_btn.move(x - 133, y - 80)
        self.sec_cycle_btn.move(x - 89, y - 80)
        self.sec_reset_btn.move(x - 45, y - 80)

    def button_check_alarm(self, sender=None):
        if not sender:
            sender = self.sender()
        if sender.state:
            sender.setIcon(QtGui.QIcon("onbtn.png"))
            self.cur.execute(f"UPDATE Alarm SET Status = 1 where AlarmId = {sender.id}")
        else:
            sender.setIcon(QtGui.QIcon("offbtn.png"))
            self.cur.execute(f"UPDATE Alarm SET Status = 0 where AlarmId = {sender.id}")
        self.con.commit()

    def button_check_timer(self, sender=None):
        if not sender:
            sender = self.sender()
        if sender.state:
            sender.setIcon(QtGui.QIcon("pause.png"))
            self.cur.execute(f"UPDATE Timer SET Status = 1 where TimerId = {sender.id}")
        else:
            sender.setIcon(QtGui.QIcon("play.png"))
            self.cur.execute(f"UPDATE Timer SET Status = 0 where TimerId = {sender.id}")
        self.con.commit()

    def change_button_value(self):
        sender = self.sender()
        if sender.state:
            sender.state = 0
        else:
            sender.state = 1
        sender.button_check()

    # Логика будильника
    def alarm_set(self):
        self.alarm_indexs = {}
        res = self.cur.execute("SELECT * FROM Alarm").fetchall()
        for i in res:
            self.alarm_add(i[0], i[1], i[2], i[3], i[4], i[5])

    def alarm_add(self, res=None, time=None, RingId=None, title=None, Days=None, Status=False):
        self.alarm_table_widget.setRowCount(self.alarm_table_widget.rowCount() + 1)
        self.btn = QtWidgets.QPushButton()
        self.btn.setIcon(QtGui.QIcon("offbtn.png"))
        self.btn.setIconSize(QtCore.QSize(75, 75))
        self.btn.state = 0
        self.btn.button_check = self.button_check_alarm
        self.btn.clicked.connect(self.change_button_value)
        self.alarm_table_widget.setCellWidget(self.alarm_table_widget.rowCount() - 1, 4, self.btn)
        self.btn_settings = QtWidgets.QPushButton()
        self.btn_settings.setIcon(QtGui.QIcon("st.png"))
        self.btn_settings.clicked.connect(self.alarm_set_settings)
        self.btn_settings.setMaximumSize(QtCore.QSize(40, 40))
        self.btn.setStyleSheet(self.qss_btn)
        self.btn_settings.setStyleSheet(self.qss_btn)
        self.alarm_table_widget.setCellWidget(self.alarm_table_widget.rowCount() - 1, 3,
                                              self.btn_settings)
        if not res:
            self.cur.execute("INSERT INTO Alarm (AlarmId) VALUES (NULL)")
            self.con.commit()
            res = max(self.cur.execute("SELECT AlarmId FROM Alarm").fetchall())[0]

        self.btn.id = res
        self.btn_settings.id = res
        if time:
            self.alarm_table_widget.setItem(self.alarm_table_widget.rowCount() - 1, 1,
                                            QtWidgets.QTableWidgetItem(str(time)))
        if RingId:
            id = self.cur.execute(
                f"SELECT Title FROM Ringtone WHERE RingId = {RingId}").fetchone()[0]
            self.alarm_table_widget.setItem(self.alarm_table_widget.rowCount() - 1, 2,
                                            QtWidgets.QTableWidgetItem(id))
        else:
            self.cur.execute(f"UPDATE Alarm SET RingId = 1")
            self.con.commit()
            id = self.cur.execute(f"SELECT Title FROM Ringtone WHERE RingId = 1").fetchone()[0]
            self.alarm_table_widget.setItem(self.alarm_table_widget.rowCount() - 1, 2,
                                            QtWidgets.QTableWidgetItem(id))

        if title:
            self.alarm_table_widget.setItem(self.alarm_table_widget.rowCount() - 1, 0,
                                            QtWidgets.QTableWidgetItem(str(title)))
        if Days:
            s = []
            c = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
            days = str(Days)
            days = "0" * (7 - len(days)) + days
            for index, i in enumerate(days):
                if i == "1":
                    s.append(c[index])
            a = self.alarm_table_widget.item(self.alarm_table_widget.rowCount() - 1, 1).text()
            self.alarm_table_widget.setItem(self.alarm_table_widget.rowCount() - 1, 1,
                                            QtWidgets.QTableWidgetItem(f"{a} {' '.join(s)}"))
        if Status:
            self.btn.state = 1
            self.btn.button_check(self.btn)
        self.alarm_indexs[res] = self.alarm_table_widget.rowCount() - 1

    def alarm_delete(self):
        if self.alarm_table_widget.currentRow() != -1:
            id = self.alarm_table_widget.cellWidget(self.alarm_table_widget.currentRow(), 4).id
        else:
            QMessageBox.critical(self, "Ошибка!", "Выберите элемент, который хотите удалить.",
                                 QMessageBox.Ok)
            return
        self.cur.execute(f"DELETE FROM Alarm WHERE AlarmId = {id}")
        self.con.commit()
        self.alarm_update()

    def alarm_update(self):
        self.alarm_table_widget.setRowCount(0)
        self.alarm_set()

    def alarm_set_settings(self):
        widget = MySettingsAlarmDialog(self, self.sender().id, self.con, self.cur)
        self.res = MainDialog(widget, widget.signal, "Настройки будильника")

    def alarm_check(self):
        t = time.localtime(time.time())
        local_h, local_m, local_s, local_day = t[3], t[4], t[5], t[6]
        if local_s == self.past_local_s_alarm:
            return
        self.past_local_s_alarm = local_s
        if local_s != 1:
            return
        data = self.cur.execute("SELECT * FROM Alarm").fetchall()
        for i in data:
            AlarmId, tm, RingId, title, days, status, volume = i[0], i[1], i[2], str(i[3]), \
                                                               i[4], i[5], i[6]
            if status and tm and RingId:
                RingPath = self.cur.execute(
                    f"SELECT Link FROM Ringtone WHERE RingId = {RingId}").fetchone()[0]
                if local_h == int(i[1].split(":")[0]) and local_m == int(i[1].split(":")[1]):
                    sound = QtMultimedia.QSoundEffect()
                    sound.setSource(QtCore.QUrl.fromLocalFile(str(RingPath)))
                    sound.setLoopCount(QtMultimedia.QSoundEffect.Infinite)
                    sound.setVolume(volume)
                    if days:
                        days = "0" * (7 - len(str(days))) + str(days)
                        days = [index for index, i in enumerate(days) if i == "1"]
                        if local_day in days:
                            sound.play()
                            QMessageBox.information(self, str(title), f"{tm}")
                            sound.stop()
                            self.alarm_update()
                    else:
                        sound.play()
                        QMessageBox.information(self, str(title), f"{tm}")
                        self.cur.execute(f"UPDATE Alarm SET Status = 0 WHERE AlarmId = {AlarmId}")
                        self.con.commit()
                        sound.stop()
                        self.alarm_update()

    # Логика Часов
    def clocks_set(self):
        res = self.cur.execute("SELECT * FROM Clocks WHERE Status = 1").fetchall()
        for i in res:
            self.clock_add(i[0], i[1], i[2])

    def clock_add(self, res=None, title=None, status=None):
        if status:
            self.clocks_table_widget.setRowCount(self.clocks_table_widget.rowCount() + 1)

            if title:
                self.clocks_table_widget.setItem(self.clocks_table_widget.rowCount() - 1, 0,
                                                 QtWidgets.QTableWidgetItem(str(title)))
            return
        res = self.clock_dict[self.clock_combobox.currentText()]
        self.cur.execute(f"UPDATE Clocks SET Status = 1 WHERE ClockId = {res}")
        self.con.commit()
        self.clock_update()

    def clock_delete(self):
        if self.clocks_table_widget.currentRow() != -1:
            title = self.clocks_table_widget.item(self.clocks_table_widget.currentRow(),
                                                  0).text()
            id = \
                self.cur.execute(f"SELECT ClockId FROM Clocks WHERE UTC = '{title}'").fetchone()[0]
        else:
            QMessageBox.critical(self, "Ошибка!", "Выберите элемент, который хотите удалить.",
                                 QMessageBox.Ok)
            return
        self.cur.execute(f"UPDATE Clocks SET Status = 0 WHERE ClockId = {id}")
        self.con.commit()
        self.clock_update()

    def clock_update(self):
        self.clocks_table_widget.setRowCount(0)
        self.clocks_set()
        self.clock_check()

    def clock_check(self):
        t = time.gmtime(time.time())
        gm_h, gm_m, gm_s = t[3], t[4], t[5]

    # Логика таймера
    def timer_set(self):
        self.timer_indexs = {}
        res = self.cur.execute("SELECT * FROM Timer").fetchall()
        for i in res:
            self.timer_add(i[0], i[1], i[2], i[3], i[4])

    def timer_add(self, res=None, tms=None, RingId=None, title=None, Status=False):
        self.timer_table_widget.setRowCount(self.timer_table_widget.rowCount() + 1)

        self.btn = QtWidgets.QPushButton()
        self.btn.setIcon(QtGui.QIcon("play.png"))
        self.btn.setIconSize(QtCore.QSize(30, 30))
        self.btn.state = 0
        self.btn.button_check = self.button_check_timer
        self.btn.clicked.connect(self.change_button_value)
        self.btn2 = QtWidgets.QPushButton()
        self.btn2.setIcon(QtGui.QIcon("c.png"))
        self.btn2.setIconSize(QtCore.QSize(30, 30))
        self.btn2.setMaximumSize(QtCore.QSize(40, 40))
        self.btn2.clicked.connect(self.timer_clear)
        self.btn.control_btn = self.btn2
        self.btn2.control_btn = self.btn

        self.btn_settings = QtWidgets.QPushButton()
        self.btn_settings.setIcon(QtGui.QIcon("st.png"))
        self.btn_settings.clicked.connect(self.timer_set_settings)
        self.btn_settings.setMaximumSize(QtCore.QSize(40, 40))
        self.btn.setStyleSheet(self.qss_btn)
        self.btn_settings.setStyleSheet(self.qss_btn)

        self.timer_table_widget.setCellWidget(self.timer_table_widget.rowCount() - 1, 6,
                                              self.btn2)
        self.timer_table_widget.setCellWidget(self.timer_table_widget.rowCount() - 1, 5,
                                              self.btn)
        self.timer_table_widget.setCellWidget(self.timer_table_widget.rowCount() - 1, 4,
                                              self.btn_settings)

        if not res:
            self.cur.execute("INSERT INTO Timer (TimerId) VALUES (NULL)")
            self.con.commit()
            res = max(self.cur.execute("SELECT TimerId FROM Timer").fetchall())[0]

        self.btn.id = res
        self.btn_settings.id = res
        if tms:
            self.timer_table_widget.setItem(self.timer_table_widget.rowCount() - 1, 1,
                                            QtWidgets.QTableWidgetItem(str(tms)))
            tms1 = int(tms.split(":")[0]) * 3600 + int(tms.split(":")[1]) * 60 + int(
                tms.split(":")[2])
            self.timer_table_widget.setItem(self.timer_table_widget.rowCount() - 1, 2,
                                            QtWidgets.QTableWidgetItem(
                                                str(time.strftime("%H:%M:%S",
                                                                  time.gmtime(tms1)))))
        if RingId:
            id = self.cur.execute(
                f"SELECT Title FROM Ringtone WHERE RingId = {RingId}").fetchone()[0]
            self.timer_table_widget.setItem(self.timer_table_widget.rowCount() - 1, 3,
                                            QtWidgets.QTableWidgetItem(id))
        else:
            self.cur.execute(f"UPDATE Timer SET RingId = 1")
            self.con.commit()
            id = self.cur.execute(f"SELECT Title FROM Ringtone WHERE RingId = 1").fetchone()[0]
            self.timer_table_widget.setItem(self.timer_table_widget.rowCount() - 1, 3,
                                            QtWidgets.QTableWidgetItem(id))
        if title:
            self.timer_table_widget.setItem(self.timer_table_widget.rowCount() - 1, 0,
                                            QtWidgets.QTableWidgetItem(str(title)))
        if Status:
            self.btn.state = 1
            self.btn.button_check(self.btn)
        self.timer_indexs[res] = self.timer_table_widget.rowCount() - 1
        self.timer2_btns.append(self.btn2)

    def timer_delete(self):
        if self.timer_table_widget.currentRow() != -1:
            id = self.timer_table_widget.cellWidget(self.timer_table_widget.currentRow(), 4).id
        else:
            QMessageBox.critical(self, "Ошибка!", "Выберите элемент, который хотите удалить.",
                                 QMessageBox.Ok)
            return
        self.cur.execute(f"DELETE FROM Timer WHERE TimerId = {id}")
        self.con.commit()
        self.timer_update()

    def timer_update(self):
        self.timer_table_widget.setRowCount(0)
        self.timer_set()

    def timer_set_settings(self):
        widget = MySettingsTimerDialog(self, self.sender().id, self.con, self.cur)
        self.res = MainDialog(widget, widget.signal, "Найстроки таймера")

    def timer_check(self):
        t = time.localtime(time.time())
        local_h, local_m, local_s = t[3], t[4], t[5]
        if local_s == self.past_local_s_timer:
            return
        self.past_local_s_timer = local_s

        data = self.cur.execute("SELECT * FROM Timer").fetchall()
        for i in data:
            TimerId, tms, RingId, title, status, volume, timer_out = i[0], i[1], i[2], str(i[3]), \
                                                                     i[4], i[5], i[6]
            if tms == "00:00:00":
                continue
            if timer_out:
                timer_out += 1
            else:
                timer_out = 1
            if status and tms and RingId:
                RingPath = self.cur.execute(
                    f"SELECT Link FROM Ringtone WHERE RingId = {RingId}").fetchone()[0]
                tms = int(tms.split(":")[0]) * 3600 + int(tms.split(":")[1]) * 60 + int(
                    tms.split(":")[2])
                tms_out = tms - timer_out
                self.cur.execute(f"UPDATE Timer SET TimeOut = {timer_out} WHERE TimerId = {TimerId}")
                self.con.commit()
                index = self.timer_indexs[TimerId]
                self.timer_table_widget.setItem(index, 2,
                                                QtWidgets.QTableWidgetItem(
                                                    str(time.strftime("%H:%M:%S",
                                                                      time.gmtime(
                                                                          tms - timer_out)))))
                if tms_out == 0:
                    sound = QtMultimedia.QSoundEffect()
                    sound.setSource(QtCore.QUrl.fromLocalFile(str(RingPath)))
                    sound.setLoopCount(QtMultimedia.QSoundEffect.Infinite)
                    sound.setVolume(volume)
                    sound.play()
                    self.timer_table_widget.cellWidget(self.timer_indexs[TimerId], 6).click()
                    QMessageBox.information(self, str(title), "Время вышло!")
                    sound.stop()
                    break

    def timer_clear(self):
        sender = self.sender()
        btn = sender.control_btn
        if btn.state:
            btn.click()
        self.cur.execute(f"UPDATE Timer SET TimeOut = 0 WHERE TimerId = {btn.id}")
        self.con.commit()
        index = self.timer_indexs[btn.id]
        tms = self.cur.execute(f"SELECT Time FROM Timer WHERE TimerId = {btn.id}").fetchone()[0]
        if tms:
            tms = int(tms.split(":")[0]) * 3600 + int(tms.split(":")[1]) * 60 + int(
                tms.split(":")[2])
            self.timer_table_widget.setItem(index, 2,
                                            QtWidgets.QTableWidgetItem(
                                                str(time.strftime("%H:%M:%S",
                                                                  time.gmtime(tms)))))

    def time_tick(self):
        while True:
            self.alarm_signal.emit()
            self.timer_signal.emit()
            time.sleep(0.9)

    def sec_start(self):
        if self.sec_start_flag:
            self.sec_start_flag = False
            self.sec_start_btn.setText('pause')
        else:
            self.sec_start_flag = True
            self.sec_start_btn.setText('start')

    def sec_cycle(self):
        self.sec_list_widget.addItem(f"{self.sec_list_widget.count() + 1}) {self.sec_label.text()}")

    def sec_reset(self):
        self.sec_start_flag = True
        self.sec_count = 0
        self.sec_label.setText(str(self.sec_count))
        self.sec_start_btn.setText('start')
        self.sec_list_widget.clear()

    def show_time(self):
        if not self.sec_start_flag:
            self.sec_count += 1
        if self.sec_count > 8640000:
            self.sec_count = 0
        seconds = (self.sec_count // 10) % 60
        minutes = (self.sec_count // (10 * 60)) % 60
        hours = (self.sec_count // (10 * 60 * 60)) % 24
        text = "%d:%d:%d" % (hours, minutes, seconds)
        self.sec_label.setText(text)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    myw = MyMainWindow()
    w.setWidget(myw)
    w.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
