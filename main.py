import sys
import random
import os
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit,
    QLabel, QTextEdit, QInputDialog, QMessageBox, QCheckBox, QScrollArea, QGridLayout, QHBoxLayout, QListWidget
)
from PyQt5.QtCore import QThread, pyqtSignal


class LoadParticipantsThread(QThread):
    participants_loaded = pyqtSignal(list)

    def __init__(self, participants_file, parent=None):
        super().__init__(parent)  # Передаем parent
        self.participants_file = participants_file

    def run(self):
        participants = []
        if os.path.exists(self.participants_file):
            with open(self.participants_file, "r", encoding="utf-8") as file:
                for line in file:
                    participant = line.strip()
                    if participant:
                        participants.append(participant)
        self.participants_loaded.emit(participants)


class LoadRequirementsThread(QThread):
    requirements_loaded = pyqtSignal(list)  # Сигнал для передачи списка требований

    def __init__(self, requirements_file, parent=None):
        super().__init__(parent)
        self.requirements_file = requirements_file

    def run(self):
        requirements = []
        if os.path.exists(self.requirements_file):
            try:
                with open(self.requirements_file, "r", encoding="utf-8") as file:
                    for line in file:
                        requirement = line.strip()
                        if requirement:
                            requirements.append(requirement)
            except Exception as e:
                print(f"Ошибка при загрузке требований: {e}")
        self.requirements_loaded.emit(requirements)  # Передаем данные через сигнал


class TournamentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Турнирная схема")
        self.resize(1000, 600)

        self.participants = []
        self.current_round = []
        self.next_round = []
        self.participants_file = "participants.txt"
        self.requirements_file = "tournament_req.txt"
        self.tournaments_folder = "tournaments"
        self.current_tournament_file = "current_tournament.json"
        self.checkboxes = []

        if not os.path.exists(self.tournaments_folder):
            os.makedirs(self.tournaments_folder)

        self.initUI()
        self.load_participants_async()
        self.load_last_tournament()
        self.load_requirements_async()

    def initUI(self):
        main_layout = QHBoxLayout()

        # Левая панель: список участников с флажками
        left_panel = QVBoxLayout()

        self.add_participant_label = QLabel("Добавить нового участника:")
        left_panel.addWidget(self.add_participant_label)

        self.add_participant_input = QLineEdit()
        left_panel.addWidget(self.add_participant_input)

        self.add_participant_button = QPushButton("Добавить участника")
        self.add_participant_button.clicked.connect(self.add_participant)
        left_panel.addWidget(self.add_participant_button)

        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_area_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_widget)
        left_panel.addWidget(self.scroll_area)

        # Кнопка для открытия файла участников
        self.open_participants_button = QPushButton("Открыть файл участников")
        self.open_participants_button.clicked.connect(self.open_participants_file)
        left_panel.addWidget(self.open_participants_button)

        # Кнопка для обновления списка участников
        self.refresh_participants_button = QPushButton("Обновить список участников")
        self.refresh_participants_button.clicked.connect(self.refresh_participants)
        left_panel.addWidget(self.refresh_participants_button)

        main_layout.addLayout(left_panel)

        # Центральная панель: основное окно турнира
        center_panel = QVBoxLayout()

        self.start_button = QPushButton("Начать турнир")
        self.start_button.clicked.connect(self.start_tournament)
        center_panel.addWidget(self.start_button)

        self.round_display = QTextEdit()
        self.round_display.setReadOnly(True)
        center_panel.addWidget(self.round_display)

        self.next_round_button = QPushButton("Следующий этап")
        self.next_round_button.clicked.connect(self.next_round_selection)
        self.next_round_button.setEnabled(False)
        center_panel.addWidget(self.next_round_button)

        self.view_reports_button = QPushButton("Просмотр отчетов")
        self.view_reports_button.clicked.connect(self.view_reports)
        center_panel.addWidget(self.view_reports_button)

        main_layout.addLayout(center_panel)

        # Правая панель: список требований
        right_panel = QVBoxLayout()

        self.add_requirement_label = QLabel("Добавить новое требование:")
        right_panel.addWidget(self.add_requirement_label)

        self.add_requirement_input = QLineEdit()
        right_panel.addWidget(self.add_requirement_input)

        self.add_requirement_button = QPushButton("Добавить требование")
        self.add_requirement_button.clicked.connect(self.add_requirement)
        right_panel.addWidget(self.add_requirement_button)

        self.requirements_scroll_area = QScrollArea()
        self.requirements_scroll_area_widget = QWidget()
        self.requirements_scroll_layout = QVBoxLayout()
        self.requirements_scroll_area_widget.setLayout(self.requirements_scroll_layout)
        self.requirements_scroll_area.setWidgetResizable(True)
        self.requirements_scroll_area.setWidget(self.requirements_scroll_area_widget)
        right_panel.addWidget(self.requirements_scroll_area)

        # Кнопка для открытия файла требований
        self.open_requirements_button = QPushButton("Открыть файл требований")
        self.open_requirements_button.clicked.connect(self.open_requirements_file)
        right_panel.addWidget(self.open_requirements_button)

        # Кнопка для обновления списка требований
        self.refresh_requirements_button = QPushButton("Обновить список требований")
        self.refresh_requirements_button.clicked.connect(self.refresh_requirements)
        right_panel.addWidget(self.refresh_requirements_button)

        main_layout.addLayout(right_panel)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_participants_async(self):
        try:
            self.load_thread = LoadParticipantsThread(self.participants_file)
            self.load_thread.participants_loaded.connect(self.populate_participants)
            self.load_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке участников: {e}")

    def load_requirements_async(self):
        try:
            self.load_requirements_thread = LoadRequirementsThread(self.requirements_file)
            self.load_requirements_thread.requirements_loaded.connect(self.populate_requirements)
            self.load_requirements_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке требований: {e}")

    def populate_participants(self, participants):
        for participant in participants:
            self.add_participant_checkbox(participant)

    def populate_requirements(self, requirements):
        for requirement in requirements:
            self.add_requirement_checkbox(requirement)

    def save_requirement(self, requirement):
        """Сохранение нового требования в файл."""
        try:
            # Если файл не существует, создаём его
            if not os.path.exists(self.requirements_file):
                with open(self.requirements_file, "w", encoding="utf-8") as file:
                    pass  # Просто создаём пустой файл

            # Сохраняем требование в файл
            with open(self.requirements_file, "a", encoding="utf-8") as file:
                file.write(requirement + "\n")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить требование: {e}")

    def add_participant(self):
        participant = self.add_participant_input.text().strip()
        if not participant:
            QMessageBox.warning(self, "Ошибка", "Введите имя участника!")
            return

        # Проверка на уникальность
        if participant in [cb.text() for cb in self.checkboxes]:
            QMessageBox.warning(self, "Ошибка", "Участник с таким именем уже существует!")
            self.add_participant_input.clear()
            return

        # Добавляем участника, если он уникален
        self.add_participant_checkbox(participant)
        self.save_participant(participant)
        self.add_participant_input.clear()

    def add_participant_checkbox(self, participant):
        checkbox = QCheckBox(participant)
        self.scroll_layout.addWidget(checkbox)
        self.checkboxes.append(checkbox)

    def add_requirement_checkbox(self, requirement):
        """Добавляет чекбокс с требованием в правую панель."""
        try:
            checkbox = QCheckBox(requirement)  # Создаём новый чекбокс
            self.requirements_scroll_layout.addWidget(checkbox)  # Добавляем его в правую панель
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при добавлении чекбокса требования: {e}")

    def add_requirement(self):
        """Добавление нового требования в список и сохранение его в файл с обработкой ошибок."""
        try:
            requirement = self.add_requirement_input.text().strip()
            if not requirement:
                QMessageBox.warning(self, "Ошибка", "Введите название требования!")
                return

            # Проверка на уникальность
            existing_requirements = [
                cb.text() for cb in self.requirements_scroll_layout.children() if isinstance(cb, QCheckBox)
            ]
            if requirement in existing_requirements:
                QMessageBox.warning(self, "Ошибка", "Требование с таким названием уже существует!")
                self.add_requirement_input.clear()
                return

            # Добавляем требование в интерфейс
            self.add_requirement_checkbox(requirement)

            # Сохраняем требование в файл
            self.save_requirement(requirement)

            # Очищаем поле ввода
            self.add_requirement_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при добавлении требования: {e}")

    def open_participants_file(self):
        """Открыть файл участников в текстовом редакторе."""
        try:
            if not os.path.exists(self.participants_file):
                with open(self.participants_file, "w", encoding="utf-8") as file:
                    pass  # Создаём пустой файл, если его нет
            subprocess.Popen(["notepad", self.participants_file])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл участников: {e}")

    def open_requirements_file(self):
        """Открыть файл требований в текстовом редакторе."""
        try:
            if not os.path.exists(self.requirements_file):
                with open(self.requirements_file, "w", encoding="utf-8") as file:
                    pass  # Создаём пустой файл, если его нет
            subprocess.Popen(["notepad", self.requirements_file])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл требований: {e}")

    def refresh_participants(self):
        """Обновляет список участников из файла."""
        try:
            # Очищаем текущий список участников
            for i in reversed(range(self.scroll_layout.count())):
                widget = self.scroll_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # Перечитываем участников из файла
            self.load_participants_async()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить список участников: {e}")

    def refresh_requirements(self):
        """Обновляет список требований из файла."""
        try:
            # Очищаем текущий список требований
            for i in reversed(range(self.requirements_scroll_layout.count())):
                widget = self.requirements_scroll_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # Перечитываем требования из файла
            self.load_requirements_async()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить список требований: {e}")

    def save_tournament_state(self):
        state = {
            "participants": self.participants,
            "current_round": self.current_round,
            "next_round": self.next_round,
            "round_display": self.round_display.toPlainText(),
            "current_round_number": self.calculate_total_rounds(len(self.participants)) - self.calculate_total_rounds(
                len(self.current_round)) + 1  # Номер текущего раунда
        }
        with open(os.path.join(self.tournaments_folder, self.current_tournament_file), "w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=4)

    def load_last_tournament(self):
        tournament_path = os.path.join(self.tournaments_folder, self.current_tournament_file)
        if os.path.exists(tournament_path):
            try:
                with open(tournament_path, "r", encoding="utf-8") as file:
                    state = json.load(file)
                    self.participants = state.get("participants", [])
                    self.current_round = state.get("current_round", [])
                    self.next_round = state.get("next_round", [])
                    self.round_display.setText(state.get("round_display", ""))
                    self.current_round_number = state.get("current_round_number", 0)  # Загружаем номер текущего раунда

                    # Проверка на основе current_round_number
                    if self.current_round_number > 0:
                        self.next_round_button.setEnabled(True)
                    else:
                        self.next_round_button.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить состояние турнира: {e}")

    def start_tournament(self):
        try:
            self.participants = [cb.text() for cb in self.checkboxes if cb.isChecked()]
            if len(self.participants) < 2:
                QMessageBox.warning(self, "Ошибка", "Необходимо выбрать минимум 2 участников!")
                return

            # Подсчёт уникальных требований
            total_requirements = self.calculate_requirements(len(self.participants))
            self.round_display.clear()
            self.round_display.append(
                f"Для проведения турнира потребуется {total_requirements} уникальных требований.\n")

            random.shuffle(self.participants)
            self.next_round_button.setEnabled(True)
            self.current_round = self.participants
            self.current_round_number = 1  # Устанавливаем первый раунд

            self.display_round()
            self.save_tournament_state()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при старте турнира: {e}")

    def get_checked_requirements(self):
        """Возвращает список выбранных требований."""
        requirements = [
            cb.text() for cb in self.requirements_scroll_area_widget.findChildren(QCheckBox) if cb.isChecked()
        ]
        print("Выбранные требования:", requirements)
        return requirements

    def calculate_requirements(self, num_participants):
        """Вычисляет количество уникальных требований для турнира."""
        requirements = 0
        while num_participants > 1:
            group_size = 3 if num_participants % 2 != 0 else 2
            groups_in_round = num_participants // group_size + (1 if num_participants % group_size else 0)
            requirements += groups_in_round
            num_participants = groups_in_round  # Уменьшаем количество участников для следующего этапа
        return requirements

    def display_round(self):
        total_rounds = self.calculate_total_rounds(len(self.participants))
        current_round_number = self.calculate_total_rounds(len(self.current_round))
        round_index = total_rounds - current_round_number + 1

        self.round_display.append(f"Раунд {round_index} ({len(self.current_round)} участников):\n")
        self.next_round = []

        # Получаем список доступных требований
        requirements = self.get_checked_requirements()
        if len(requirements) < len(self.current_round) // 2:
            print(len(self.current_round))
            print(len(requirements))
            QMessageBox.warning(self, "Ошибка", "Недостаточно требований для всех пар!")
            return

        random.shuffle(requirements)

        while len(self.current_round) > 3:
            group_size = 3 if len(self.current_round) % 2 != 0 else 2
            group = self.current_round[:group_size]
            self.current_round = self.current_round[group_size:]
            requirement = requirements.pop(0)
            self.round_display.append(f"  Группа: {', '.join(group)} -> Требование: {requirement}")
            self.next_round.append(group)

        if self.current_round:
            requirement = requirements.pop(0) if requirements else "Без требования"
            self.round_display.append(f"  Группа: {', '.join(self.current_round)} -> Требование: {requirement}")
            self.next_round.append(self.current_round)
            self.current_round = []

        self.save_tournament_state()

    def calculate_total_rounds(self, num_participants):
        rounds = 0
        while num_participants > 1:
            num_participants = (num_participants + 1) // 2
            rounds += 1
        return rounds

    def next_round_selection(self):
        try:
            winners = []
            for group in self.next_round:
                winner, ok = QInputDialog.getItem(
                    self, "Выбор победителя",
                    f"Выберите победителя из группы: {', '.join(group)}", group, 0, False
                )
                if ok and winner:
                    winners.append(winner)

            self.current_round = winners
            self.round_display.append("\nПобедители текущего этапа:")
            self.round_display.append(", ".join(winners) + "\n")

            if len(winners) == 1:
                self.round_display.append(f"Победитель: {winners[0]}\n")
                self.next_round_button.setEnabled(False)

                # Сохраняем завершённый турнир в отчётах
                tournament_number = len(
                    [f for f in os.listdir(self.tournaments_folder) if f.startswith("tournament_")]) + 1
                report_path = os.path.join(self.tournaments_folder, f"tournament_{tournament_number}.json")
                with open(report_path, "w", encoding="utf-8") as file:
                    json.dump({
                        "participants": self.participants,
                        "winner": winners[0],
                        "log": self.round_display.toPlainText()
                    }, file, ensure_ascii=False, indent=4)

                os.remove(os.path.join(self.tournaments_folder, self.current_tournament_file))
            elif len(winners) < 2:
                QMessageBox.warning(self, "Ошибка", "В следующем этапе должно быть минимум 2 участника!")
            else:
                self.display_round()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выборе победителей: {e}")

    def view_reports(self):
        reports = [f for f in os.listdir(self.tournaments_folder) if f.startswith("tournament_")]
        if reports:
            dialog = QMainWindow(self)
            dialog.setWindowTitle("Выберите отчет")

            list_widget = QListWidget()
            for report_file in reports:
                list_widget.addItem(report_file)

            list_widget.itemDoubleClicked.connect(lambda item: self.show_report(item.text(), dialog))

            layout = QVBoxLayout()
            layout.addWidget(list_widget)

            container = QWidget()
            container.setLayout(layout)
            dialog.setCentralWidget(container)
            dialog.resize(400, 300)
            dialog.show()
        else:
            QMessageBox.information(self, "Отчёты о турнирах", "Нет завершённых турниров.")

    def show_report(self, report_file, dialog):
        dialog.close()

        report_path = os.path.join(self.tournaments_folder, report_file)
        with open(report_path, "r", encoding="utf-8") as file:
            report_data = json.load(file)

        report_dialog = QMainWindow(self)
        report_dialog.setWindowTitle(f"Отчет: {report_file}")

        report_display = QTextEdit()
        report_display.setReadOnly(True)
        report_display.setText(report_data["log"])

        layout = QVBoxLayout()
        layout.addWidget(report_display)

        container = QWidget()
        container.setLayout(layout)
        report_dialog.setCentralWidget(container)
        report_dialog.resize(600, 400)
        report_dialog.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TournamentApp()
    window.show()
    sys.exit(app.exec_())
