import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QVBoxLayout, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QDate, QPoint
from PyQt5.QtGui import QColor, QBrush, QFont, QIcon
from PyQt5.sip import delete
import datetime
from PyQt5.QtWidgets import QComboBox, QDateEdit

STYLE_SHEET = """
QWidget {
    background-color: #f5f5f5;
    color: #444444;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 14px;
}

QLineEdit, QComboBox, QDateEdit, QTextEdit {
    padding: 10px;
    border: 1px solid #bbbbbb;
    border-radius: 5px;
    background-color: #ffffff;
    selection-background-color: #a0c4ff;
    color: #333333;
}

QPushButton {
    background-color: #5dade2;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2e86c1;
}

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #bbbbbb;
    border-radius: 5px;
    gridline-color: #dddddd;
}

QTableWidget::item {
    padding: 8px;
    color: #333333;
}

QHeaderView::section {
    background-color: #d0e9ff;
    padding: 10px;
    border: 1px solid #bbbbbb;
    font-weight: bold;
    color: #333333;
}

QLabel {
    padding: 8px;
    color: #444444;
}

.daily {
    color: #e67e22;
}

.incomplete {
    color: #e74c3c;
}

.completed {
    color: #2ecc71;
}
"""

# 定义一个函数来获取正确的文件路径，打包后将文件保存到用户数据目录
def get_file_path(filename):
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件，使用用户数据目录
        app_data_dir = os.getenv('APPDATA')
        app_dir = os.path.join(app_data_dir, 'TaskManager')
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        return os.path.join(app_dir, filename)
    else:
        # 如果是开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, filename)

class taskwindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet(STYLE_SHEET)
        self.setWindowTitle("任务管理")
        self.setWindowIcon(QIcon("task_icon.png"))
        self.open_windows = []
        self.drag_position = QPoint()
        self.sort_mode = "status"  # 初始化排序模式为按完成状态排序
        self.sort_reverse = False  # 初始化排序顺序为正序
        self.initUI()
        self.load_tasks()
        self.sort_tasks()

    def initUI(self):
        width = 600
        height = 700
        self.setGeometry(100, 100, width, height)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("任务管理", self)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        input_layout = QVBoxLayout()
        input_layout.setSpacing(10)

        self.input_label = QLineEdit(self)
        self.input_label.setPlaceholderText("请输入任务简称")
        input_layout.addWidget(self.input_label)

        self.input_content = QLineEdit(self)
        self.input_content.setPlaceholderText("请输入任务内容")
        input_layout.addWidget(self.input_content)

        choice_layout = QHBoxLayout()
        choice_layout.setSpacing(10)

        self.repeat_choice = QComboBox(self)
        self.repeat_choice.addItems(["仅此一次", "日常"])
        choice_layout.addWidget(self.repeat_choice)

        self.deadline_picker = QDateEdit(self)
        self.deadline_picker.setDate(QDate.currentDate())
        self.deadline_picker.setCalendarPopup(True)
        choice_layout.addWidget(self.deadline_picker)

        input_layout.addLayout(choice_layout)
        main_layout.addLayout(input_layout)

        # 添加排序选择下拉框
        sort_layout = QHBoxLayout()
        self.sort_choice = QComboBox(self)
        self.sort_choice.addItems(["按完成状态排序", "按创建时间排序", "按截止时间排序"])
        self.sort_choice.currentIndexChanged.connect(self.change_sort_mode)
        sort_layout.addWidget(self.sort_choice)

        self.order_choice = QComboBox(self)
        self.order_choice.addItems(["正序", "逆序"])
        self.order_choice.currentIndexChanged.connect(self.change_sort_order)
        sort_layout.addWidget(self.order_choice)

        main_layout.addLayout(sort_layout)

        self.add_button = QPushButton("添加任务", self)
        self.add_button.clicked.connect(self.add_task)
        main_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("删除选中任务", self)
        self.delete_button.clicked.connect(self.delete_task)
        main_layout.addWidget(self.delete_button)

        self.task_list = QTableWidget(self)
        self.task_list.setColumnCount(5)
        self.task_list.setHorizontalHeaderLabels(["完成情况", "任务简称", "创建时间", "截止日期", "任务内容"])
        self.task_list.setColumnWidth(0, 100)
        self.task_list.setColumnWidth(1, 120)
        self.task_list.setColumnWidth(2, 120)
        self.task_list.setColumnWidth(3, 120)
        self.task_list.setColumnWidth(4, 200)
        header = self.task_list.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        for col in range(1, self.task_list.columnCount()):
            self.task_list.setColumnHidden(col, False)
            item = QTableWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.task_list.itemClicked.connect(self.change_task)
        main_layout.addWidget(self.task_list)

        # 添加关闭程序的按钮
        self.close_button = QPushButton("关闭程序", self)
        self.close_button.clicked.connect(self.close_application)
        main_layout.addWidget(self.close_button)

        self.setLayout(main_layout)
        self.show()

    def close_application(self):
        """关闭整个应用程序"""
        self.close()
        QApplication.quit()

    def change_sort_mode(self, index):
        if index == 0:
            self.sort_mode = "status"
        elif index == 1:
            self.sort_mode = "create_time"
        elif index == 2:
            self.sort_mode = "deadline"
        self.sort_tasks()

    def change_sort_order(self, index):
        self.sort_reverse = index == 1
        self.sort_tasks()

    def add_task(self):
        task_label = self.input_label.text()
        task_content = self.input_content.text()
        task_repeat = "未完成" if self.repeat_choice.currentText() == "仅此一次" else "日常"
        task_ddl = self.deadline_picker.date().toString("yyyy-MM-dd")
        task_current = datetime.datetime.now().strftime("%Y-%m-%d")

        if not task_label or not task_content:
            return

        row_position = self.task_list.rowCount()
        self.task_list.insertRow(row_position)

        type_item = QTableWidgetItem(task_repeat)
        if task_repeat == "日常":
            type_item.setForeground(QBrush(QColor("#e67e22")))
            type_item.setData(Qt.UserRole, "daily")
        elif task_repeat == "未完成":
            type_item.setForeground(QBrush(QColor("#e74c3c")))
            type_item.setData(Qt.UserRole, "incomplete")
        else:
            type_item.setForeground(QBrush(QColor("#2ecc71")))
            type_item.setData(Qt.UserRole, "completed")
        self.task_list.setItem(row_position, 0, type_item)

        task_item = QTableWidgetItem(task_label)
        task_item.setForeground(QBrush(QColor(0, 0, 0)))
        task_item.setFlags(task_item.flags() & ~Qt.ItemIsEditable)
        self.task_list.setItem(row_position, 1, task_item)

        deadline_item = QTableWidgetItem(task_current)
        deadline_item.setForeground(QBrush(QColor(0, 0, 0)))
        deadline_item.setFlags(deadline_item.flags() & ~Qt.ItemIsEditable)
        self.task_list.setItem(row_position, 2, deadline_item)

        time_item = QTableWidgetItem(task_ddl)
        time_item.setForeground(QBrush(QColor(0, 0, 0)))
        time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
        self.task_list.setItem(row_position, 3, time_item)

        content_item = QTableWidgetItem(task_content)
        content_item.setForeground(QBrush(QColor(0, 0, 0)))
        content_item.setFlags(content_item.flags() & ~Qt.ItemIsEditable)
        self.task_list.setItem(row_position, 4, content_item)

        self.input_label.setText("")
        self.input_content.setText("")
        self.repeat_choice.setCurrentIndex(0)
        self.deadline_picker.setDate(QDate.currentDate())

        self.save_tasks()
        self.sort_tasks()

    def change_task(self, item):
        if item.column() == 0:
            current_row = self.task_list.currentRow()
            if current_row != -1:
                type_item = self.task_list.item(current_row, 0)
                if type_item:
                    current_status = type_item.text()
                    if current_status != "日常":
                        if current_status == "未完成":
                            type_item.setText("完成")
                            type_item.setForeground(QBrush(QColor("#2ecc71")))
                            type_item.setData(Qt.UserRole, "completed")
                        elif current_status == "完成":
                            type_item.setText("未完成")
                            type_item.setForeground(QBrush(QColor("#e74c3c")))
                            type_item.setData(Qt.UserRole, "incomplete")

            self.save_tasks()
            self.sort_tasks()
        else:
            self.open_task()

    def open_task(self):
        current_row = self.task_list.currentRow()
        if current_row != -1:
            task_label = self.task_list.item(current_row, 1).text() if self.task_list.item(current_row, 1) else ""
            task_content = self.task_list.item(current_row, 4).text() if self.task_list.item(current_row, 4) else ""
            task_repeat = self.task_list.item(current_row, 0).text() if self.task_list.item(current_row, 0) else ""
            task_ddl = self.task_list.item(current_row, 3).text() if self.task_list.item(current_row, 3) else ""
            task_current = self.task_list.item(current_row, 2).text() if self.task_list.item(current_row, 2) else ""
            window = open_task_window(task_label, task_content, task_repeat, task_ddl, task_current)
            self.open_windows.append(window)
            window.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.add_task()
        elif event.key() == Qt.Key_Escape:
            self.close()

    def save_tasks(self):
        file_path = get_file_path('mytask.txt')  # 使用自定义函数获取文件路径
        with open(file_path, 'w', encoding='utf-8') as file:
            for row in range(self.task_list.rowCount()):
                task_data = []
                for col in range(self.task_list.columnCount()):
                    item = self.task_list.item(row, col)
                    if item:
                        task_data.append(item.text())
                    else:
                        task_data.append('')
                file.write('\t'.join(task_data) + '\n')

    def load_tasks(self):
        file_path = get_file_path('mytask.txt')  # 使用自定义函数获取文件路径
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    task_data = line.strip().split('\t')
                    if len(task_data) == 5:
                        row_position = self.task_list.rowCount()
                        self.task_list.insertRow(row_position)
                        type_item = QTableWidgetItem(task_data[0])
                        status = task_data[0]
                        if status == "日常":
                            type_item.setForeground(QBrush(QColor("#e67e22")))
                            type_item.setData(Qt.UserRole, "daily")
                        elif status == "未完成":
                            type_item.setForeground(QBrush(QColor("#e74c3c")))
                            type_item.setData(Qt.UserRole, "incomplete")
                        else:
                            type_item.setForeground(QBrush(QColor("#2ecc71")))
                            type_item.setData(Qt.UserRole, "completed")
                        self.task_list.setItem(row_position, 0, type_item)
                        for col in range(1, 5):
                            item = QTableWidgetItem(task_data[col])
                            item.setForeground(QBrush(QColor(0, 0, 0)))
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            self.task_list.setItem(row_position, col, item)
        except FileNotFoundError:
            pass

    def sort_tasks(self):
        tasks = []
        for row in range(self.task_list.rowCount()):
            task_data = []
            for col in range(self.task_list.columnCount()):
                item = self.task_list.item(row, col)
                if item:
                    task_data.append(item.text())
                else:
                    task_data.append('')
            tasks.append(task_data)

        def sort_key(task):
            if self.sort_mode == "status":
                status = task[0]
                if status == "日常":
                    return 0
                elif status == "未完成":
                    return 1
                elif status == "完成":
                    return 2
                else:
                    return 3
            elif self.sort_mode == "create_time":
                return task[2]
            elif self.sort_mode == "deadline":
                return task[3]

        tasks.sort(key=sort_key, reverse=self.sort_reverse)

        self.task_list.setRowCount(0)
        for task in tasks:
            row_position = self.task_list.rowCount()
            self.task_list.insertRow(row_position)
            type_item = QTableWidgetItem(task[0])
            status = task[0]
            if status == "日常":
                type_item.setForeground(QBrush(QColor("#e67e22")))
                type_item.setData(Qt.UserRole, "daily")
            elif status == "未完成":
                type_item.setForeground(QBrush(QColor("#e74c3c")))
                type_item.setData(Qt.UserRole, "incomplete")
            else:
                type_item.setForeground(QBrush(QColor("#2ecc71")))
                type_item.setData(Qt.UserRole, "completed")
            self.task_list.setItem(row_position, 0, type_item)
            for col in range(1, 5):
                item = QTableWidgetItem(task[col])
                item.setForeground(QBrush(QColor(0, 0, 0)))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.task_list.setItem(row_position, col, item)

    def delete_task(self):
        selected_rows = set()
        for item in self.task_list.selectedItems():
            selected_rows.add(item.row())

        for row in sorted(selected_rows, reverse=True):
            self.task_list.removeRow(row)

        self.save_tasks()
        self.sort_tasks()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

class open_task_window(QWidget):
    def __init__(self, task_label, task_content, task_repeat, task_ddl, task_current):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet(STYLE_SHEET)
        self.drag_position = QPoint()
        self.initUI(task_label, task_content, task_repeat, task_ddl, task_current)

    def initUI(self, task_label, task_content, task_repeat, task_ddl, task_current):
        width = 500
        height = 700
        self.setGeometry(701, 100, width, height)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel("任务详情", self)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        status_label = QLabel(f"状态: {task_repeat}", self)
        status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if task_repeat == "日常":
            status_label.setStyleSheet("color: #e67e22;")
        elif task_repeat == "未完成":
            status_label.setStyleSheet("color: #e74c3c;")
        else:
            status_label.setStyleSheet("color: #2ecc71;")
        layout.addWidget(status_label)

        label_label = QLabel(f"简称: {task_label}", self)
        label_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(label_label)

        content_label = QTextEdit(task_content, self)
        content_label.setReadOnly(True)
        content_label.setLineWrapMode(QTextEdit.WidgetWidth)
        content_label.setMinimumHeight(300)
        layout.addWidget(content_label)

        ddl_label = QLabel(f"截止日期: {task_ddl}", self)
        ddl_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(ddl_label)

        current_label = QLabel(f"创建时间: {task_current}", self)
        current_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(current_label)

        close_button = QPushButton("关闭", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = taskwindow()
    sys.exit(app.exec_())

# pyinstaller --windowed --onefile --icon=myico.ico --add-data "mytask.txt;."   WaliTask.py
