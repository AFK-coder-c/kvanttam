import pyglet
from pyglet.window import mouse
import time
import os
import random
import math
import json
from datetime import datetime


# ==================== НАСТРОЙКА ЛОГИРОВАНИЯ ====================
class Logger:
    def __init__(self):
        # создаем папку debug если её нет
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.debug_folder = os.path.join(script_dir, "debug")
        self.log_file = os.path.join(self.debug_folder, "debug.txt")

        # создаем папку debug
        if not os.path.exists(self.debug_folder):
            os.makedirs(self.debug_folder)
            # это единственный print который оставляем для создания папки
            original_print = __builtins__.print
            original_print(f"📁 Создана папка: {self.debug_folder}")

        # очищаем файл при новом запуске
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Запуск Тамагочи {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write("=" * 50 + "\n\n")

    def log(self, message):
        """Записывает сообщение в лог-файл с временной меткой"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")


# создаем глобальный логгер
logger = Logger()


# переопределяем print чтобы ничего не выводил в консоль
def print(*args, **kwargs):
    # делаем заглушку - ничего не выводим
    pass


# ==================== КОНЕЦ НАСТРОЙКИ ЛОГИРОВАНИЯ ====================


# ==================== КЛАСС ДЛЯ СОХРАНЕНИЯ НАСТРОЕК ====================
class SettingsStorage:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(script_dir, "settings.json")
        self.settings = self.load_settings()

    def load_settings(self):
        """Загружает настройки из файла"""
        default_settings = {
            "questions_path": "",
            "music_volume": 0.3
        }

        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    logger.log(f"⚙️ Загружены настройки из {self.settings_file}")
                    return settings
            else:
                logger.log("⚙️ Файл настроек не найден, используются значения по умолчанию")
                return default_settings
        except Exception as e:
            logger.log(f"❌ Ошибка загрузки настроек: {e}")
            return default_settings

    def save_settings(self, questions_path, music_volume):
        """Сохраняет настройки в файл"""
        try:
            settings = {
                "questions_path": questions_path,
                "music_volume": music_volume
            }

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            logger.log(f"💾 Настройки сохранены: путь={questions_path}, громкость={music_volume}")
            return True
        except Exception as e:
            logger.log(f"❌ Ошибка сохранения настроек: {e}")
            return False


class BackgroundMusic:
    def __init__(self, initial_volume=0.3):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        music_path = os.path.join(script_dir, "resource", "ElectroDynamix.mp3")

        self.player = None
        self.is_playing = False
        self.volume = initial_volume

        try:
            if os.path.exists(music_path):
                # Загружаем музыку
                music = pyglet.media.load(music_path)
                logger.log(f"🎵 Музыка загружена, длительность: {music.duration} сек")

                # Простой способ зацикливания - ставим музыку и используем eos_action
                self.player = pyglet.media.Player()
                self.player.queue(music)
                self.player.eos_action = pyglet.media.SourceGroup.loop  # зацикливаем
                self.player.volume = self.volume

                logger.log("🎵 Музыка загружена и будет играть вечно!")
            else:
                logger.log(f"❌ Файл не найден: {music_path}")
        except Exception as e:
            logger.log(f"❌ Ошибка загрузки музыки: {e}")

    def start(self):
        """Запускает музыку"""
        if self.player and not self.is_playing:
            self.player.play()
            self.is_playing = True
            logger.log("🎵 ElectroDynamix заиграла!")
            # Проверяем что музыка действительно играет
            if self.player.playing:
                logger.log("✅ Плеер работает, музыка играет")
            else:
                logger.log("❌ Плеер не играет")

    def stop(self):
        """Останавливает музыку"""
        if self.player and self.is_playing:
            self.player.pause()
            self.is_playing = False
            logger.log("🔇 Музыка остановлена")

    def set_volume(self, volume):
        """Меняет громкость (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if self.player:
            self.player.volume = self.volume
        logger.log(f"🔊 Громкость: {int(self.volume * 100)}%")


# ==================== КЛАСС ДЛЯ ЗАГРУЗКИ ВОПРОСОВ ====================
class QuestionLoader:
    def __init__(self, questions_path=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Если путь не указан, используем путь по умолчанию
        if questions_path and os.path.exists(questions_path):
            self.questions_file = questions_path
        else:
            self.questions_file = os.path.join(script_dir, "resource", "questions.json")

        self.questions = []
        self.last_error = None
        self.load_questions()

    def load_questions(self):
        """Загружает вопросы из JSON файла"""
        try:
            if os.path.exists(self.questions_file):
                with open(self.questions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.questions = data.get('questions', [])
                logger.log(f"📚 Загружено {len(self.questions)} вопросов из {self.questions_file}")
                self.last_error = None
                return True
            else:
                # Создаем пример файла с вопросами, если его нет
                self.create_sample_questions()
                logger.log(f"📝 Создан файл с примерами вопросов: {self.questions_file}")
                self.last_error = None
                return True
        except Exception as e:
            self.last_error = str(e)
            logger.log(f"❌ Ошибка загрузки вопросов: {e}")
            self.questions = []
            return False

    def create_sample_questions(self):
        """Создает пример файла с вопросами"""
        sample_data = {
            "questions": [
                {
                    "question": "Сколько будет 2 + 2?",
                    "options": ["3", "4", "5", "6"],
                    "correct": "4"
                },
                {
                    "question": "Столица Франции?",
                    "options": ["Лондон", "Берлин", "Париж", "Мадрид"],
                    "correct": "Париж"
                },
                {
                    "question": "Сколько дней в неделе?",
                    "options": ["5", "6", "7", "8"],
                    "correct": "7"
                },
                {
                    "question": "Какого цвета трава?",
                    "options": ["Красного", "Синего", "Зеленого", "Желтого"],
                    "correct": "Зеленого"
                },
                {
                    "question": "Сколько месяцев в году?",
                    "options": ["10", "11", "12", "13"],
                    "correct": "12"
                }
            ]
        }

        # Создаем папку resource если её нет
        os.makedirs(os.path.dirname(self.questions_file), exist_ok=True)

        with open(self.questions_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)

    def set_questions_path(self, new_path):
        """Устанавливает новый путь к файлу с вопросами и перезагружает их"""
        self.questions_file = new_path
        success = self.load_questions()
        if success:
            logger.log(f"✅ Путь к вопросам изменен на: {new_path}")
        else:
            logger.log(f"❌ Не удалось загрузить вопросы из: {new_path}")
        return success

    def get_random_question(self):
        """Возвращает случайный вопрос с перемешанными вариантами ответов"""
        if not self.questions:
            return None

        # Выбираем случайный вопрос
        question_data = random.choice(self.questions)

        # Создаем копию вариантов ответов и перемешиваем их
        shuffled_options = question_data['options'].copy()
        random.shuffle(shuffled_options)

        return {
            'question': question_data['question'],
            'options': shuffled_options,
            'correct': question_data['correct']
        }


# ==================== КЛАСС ДЛЯ ВОПРОСОВ ====================
class QuestionWindow(pyglet.window.Window):
    def __init__(self, pet, action_type, question_loader):
        super().__init__(500, 400, "Вопрос")
        self.pet = pet
        self.action_type = action_type  # 'feed' или 'play'
        self.is_active = True
        self.question_loader = question_loader

        # Приостанавливаем основную игру
        global game_paused
        game_paused = True
        pyglet.clock.unschedule(update)

        logger.log(f"❓ Открыто окно вопроса для действия: {action_type}")

        # Получаем случайный вопрос
        question_data = self.question_loader.get_random_question()
        if question_data:
            self.question_text = question_data['question']
            self.options = question_data['options']
            self.correct_answer = question_data['correct']
            logger.log(f"❓ Загружен вопрос: {self.question_text}")
            logger.log(f"📋 Варианты: {self.options}")
            logger.log(f"✅ Правильный ответ: {self.correct_answer}")
        else:
            # Заглушка на случай если вопросы не загрузились
            self.question_text = "Ошибка загрузки вопросов"
            self.options = ["ОК"]
            self.correct_answer = "ОК"
            logger.log("⚠️ Используется заглушка вопроса")

        # Создаем текст вопроса
        self.question_label = pyglet.text.Label(
            self.question_text,
            x=250, y=300,
            anchor_x='center', anchor_y='center',
            font_size=14,
            width=450,
            multiline=True,
            align='center',
            color=(0, 0, 0, 255)
        )

        # Создаем кнопки ответов
        self.option_buttons = []
        button_width = 200
        button_height = 50
        start_x = 50
        y_pos = 200

        for i, option in enumerate(self.options):
            btn_x = start_x + (i % 2) * 220
            btn_y = y_pos - (i // 2) * 70

            button = {
                'rect': pyglet.shapes.Rectangle(btn_x, btn_y, button_width, button_height, color=BLUE),
                'label': pyglet.text.Label(option, x=btn_x + button_width // 2, y=btn_y + button_height // 2,
                                           anchor_x='center', anchor_y='center',
                                           color=(255, 255, 255, 255),
                                           font_size=12,
                                           width=button_width - 10,
                                           multiline=True,
                                           align='center'),
                'value': option,
                'x': btn_x, 'y': btn_y,
                'width': button_width, 'height': button_height
            }
            self.option_buttons.append(button)

        logger.log("📋 Создано окно вопросов")

    def on_draw(self):
        self.clear()
        # Белый фон
        pyglet.shapes.Rectangle(0, 0, 500, 400, color=(255, 255, 255)).draw()

        # Рисуем вопрос
        self.question_label.draw()

        # Рисуем кнопки ответов
        for btn in self.option_buttons:
            btn['rect'].draw()
            btn['label'].draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            # Проверяем клик по кнопкам ответов
            for btn in self.option_buttons:
                if (btn['x'] <= x <= btn['x'] + btn['width'] and
                        btn['y'] <= y <= btn['y'] + btn['height']):
                    self.check_answer(btn['value'])
                    break

    def check_answer(self, answer):
        """Проверяет ответ и применяет эффекты"""
        if answer == self.correct_answer:
            logger.log(f"✅ Правильный ответ: {answer}")
            # Правильный ответ - пополняем характеристики
            if self.action_type == 'feed':
                self.pet.hunger = min(100, self.pet.hunger + 30)
                logger.log(f"🍖 +30 к голоду! Текущий голод: {self.pet.hunger}%")
            else:  # play
                self.pet.happiness = min(100, self.pet.happiness + 30)
                logger.log(f"🎮 +30 к счастью! Текущее счастье: {self.pet.happiness}%")
        else:
            logger.log(f"❌ Неправильный ответ: {answer}, правильный: {self.correct_answer}")
            # Неправильный ответ - ускоренный расход на 10 секунд
            self.pet.speed_boost_active = True
            self.pet.speed_boost_end_time = time.time() + 10
            self.pet.speed_multiplier = 1.5
            logger.log("⚡ Ускоренный расход характеристик на 10 секунд (x1.5)")

        # Закрываем окно и возобновляем игру
        self.close_and_resume()

    def close_and_resume(self):
        """Закрывает окно и возобновляет игру"""
        global game_paused, question_window
        self.is_active = False
        question_window = None
        game_paused = False
        pyglet.clock.schedule_interval(update, 1 / 60.0)
        logger.log("❓ Окно вопроса закрыто, игра возобновлена")
        self.close()

    def on_close(self):
        """При закрытии окна крестиком тоже возобновляем игру"""
        self.close_and_resume()


# Окно настроек
# Окно настроек
class SettingsWindow(pyglet.window.Window):
    def __init__(self, music_player, question_loader, settings_storage):
        super().__init__(500, 450, "Настройки")
        self.music_player = music_player
        self.question_loader = question_loader
        self.settings_storage = settings_storage

        # ползунок громкости
        self.slider_x = 150
        self.slider_y = 320
        self.slider_width = 200
        self.slider_height = 20
        self.slider_pos = music_player.volume * self.slider_width

        # поле ввода пути к файлу вопросов
        self.path_input_x = 50
        self.path_input_y = 220
        self.path_input_width = 400
        self.path_input_height = 30
        self.path_text = self.question_loader.questions_file
        self.path_input_active = False
        self.cursor_position = len(self.path_text)

        # создаем текст для отображения пути
        self.update_display_text()

        # кнопка "Вставить"
        self.paste_button_x = 150
        self.paste_button_y = 180
        self.paste_button_width = 80
        self.paste_button_height = 25
        self.mouse_over_paste = False

        # кнопка "Загрузить"
        self.load_button_x = 250
        self.load_button_y = 180
        self.load_button_width = 100
        self.load_button_height = 30
        self.mouse_over_load = False

        # текст статуса загрузки
        self.update_status_text()

        # текст
        self.volume_text = pyglet.text.Label("Громкость:", x=250, y=360, anchor_x='center', color=(0, 0, 0, 255))
        self.volume_value = pyglet.text.Label(f"{int(music_player.volume * 100)}%", x=250, y=290, anchor_x='center',
                                              color=(0, 0, 0, 255))

        self.path_label = pyglet.text.Label("Путь к файлу с вопросами:", x=250, y=260, anchor_x='center',
                                            color=(0, 0, 0, 255))

        # для перетаскивания ползунка
        self.dragging = False

        # крестик закрытия
        self.mouse_over_close = False

        # мигающий курсор
        self.cursor_visible = True
        self.cursor_timer = 0
        pyglet.clock.schedule_interval(self.update_cursor, 0.5)

        logger.log("📊 Окно настроек открыто")

    def update_display_text(self):
        """Обновляет отображаемый текст с путем"""
        self.display_text = pyglet.text.Label(
            self.path_text,
            x=self.path_input_x + 5, y=self.path_input_y + self.path_input_height // 2,
            anchor_y='center',
            color=(0, 0, 0, 255),
            font_size=10,
            width=self.path_input_width - 10,
            multiline=False
        )

    def update_status_text(self):
        """Обновляет текст статуса"""
        if self.question_loader.last_error:
            self.status_text = pyglet.text.Label(
                f"Ошибка: {self.question_loader.last_error}",
                x=250, y=100,
                anchor_x='center',
                color=RED,
                font_size=10
            )
        else:
            self.status_text = pyglet.text.Label(
                f"Загружено {len(self.question_loader.questions)} вопросов",
                x=250, y=100,
                anchor_x='center',
                color=GREEN,
                font_size=10
            )

    def update_cursor(self, dt):
        """Обновляет состояние мигающего курсора"""
        if self.path_input_active:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0

    def on_draw(self):
        self.clear()
        # Белый фон
        pyglet.shapes.Rectangle(0, 0, 500, 450, color=(255, 255, 255)).draw()

        # рисуем ползунок
        # фон ползунка
        slider_bg = pyglet.shapes.Rectangle(self.slider_x, self.slider_y,
                                            self.slider_width, self.slider_height,
                                            color=GRAY)
        slider_bg.draw()

        # заполненная часть (громкость)
        slider_fill = pyglet.shapes.Rectangle(self.slider_x, self.slider_y,
                                              self.slider_pos, self.slider_height,
                                              color=BLUE)
        slider_fill.draw()

        # кружок-ползунок
        knob_x = self.slider_x + self.slider_pos
        knob = pyglet.shapes.Circle(knob_x, self.slider_y + self.slider_height / 2,
                                    10, color=WHITE)
        knob.draw()

        # поле ввода пути
        path_bg_color = LIGHT_BLUE if self.path_input_active else WHITE
        path_bg = pyglet.shapes.Rectangle(
            self.path_input_x, self.path_input_y,
            self.path_input_width, self.path_input_height,
            color=path_bg_color
        )
        path_bg.draw()
        path_border = pyglet.shapes.Rectangle(
            self.path_input_x, self.path_input_y,
            self.path_input_width, self.path_input_height,
            color=BLACK
        )
        path_border.opacity = 100
        path_border.draw()

        # текст пути
        self.update_display_text()
        self.display_text.draw()

        # рисуем курсор если поле активно
        if self.path_input_active and self.cursor_visible:
            # вычисляем позицию курсора
            cursor_x = self.path_input_x + 5 + self.display_text.content_width
            if cursor_x < self.path_input_x + self.path_input_width - 5:
                cursor = pyglet.shapes.Rectangle(
                    cursor_x, self.path_input_y + 5,
                    2, self.path_input_height - 10,
                    color=BLACK
                )
                cursor.draw()

        # кнопка вставки
        paste_color = LIGHT_GREEN if self.mouse_over_paste else GRAY
        paste_btn = pyglet.shapes.Rectangle(
            self.paste_button_x, self.paste_button_y,
            self.paste_button_width, self.paste_button_height,
            color=paste_color
        )
        paste_btn.draw()
        paste_label = pyglet.text.Label(
            "Вставить",
            x=self.paste_button_x + self.paste_button_width // 2,
            y=self.paste_button_y + self.paste_button_height // 2,
            anchor_x='center', anchor_y='center',
            color=(0, 0, 0, 255),
            font_size=9
        )
        paste_label.draw()

        # кнопка загрузки
        load_color = LIGHT_GREEN if self.mouse_over_load else GRAY
        load_btn = pyglet.shapes.Rectangle(
            self.load_button_x, self.load_button_y,
            self.load_button_width, self.load_button_height,
            color=load_color
        )
        load_btn.draw()
        load_label = pyglet.text.Label(
            "Загрузить",
            x=self.load_button_x + self.load_button_width // 2,
            y=self.load_button_y + self.load_button_height // 2,
            anchor_x='center', anchor_y='center',
            color=(0, 0, 0, 255)
        )
        load_label.draw()

        # статус
        self.update_status_text()
        self.status_text.draw()

        # рисуем текст
        self.volume_text.draw()
        self.volume_value.text = f"{int(self.music_player.volume * 100)}%"
        self.volume_value.draw()

        self.path_label.draw()

        # крестик закрытия
        close_color = RED if self.mouse_over_close else GRAY
        close_btn = pyglet.shapes.Rectangle(470, 420, 20, 20, color=close_color)
        close_btn.draw()
        close_text = pyglet.text.Label("X", x=480, y=425, anchor_x='center', color=(0, 0, 0, 255))
        close_text.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            # проверяем клик по ползунку
            knob_x = self.slider_x + self.slider_pos
            if (knob_x - 15 <= x <= knob_x + 15 and
                    self.slider_y <= y <= self.slider_y + self.slider_height):
                self.dragging = True
                logger.log("🎚️ Начали перетаскивать ползунок")

            # проверяем клик по полю ввода
            if (self.path_input_x <= x <= self.path_input_x + self.path_input_width and
                    self.path_input_y <= y <= self.path_input_y + self.path_input_height):
                self.path_input_active = True
                self.cursor_position = len(self.path_text)
                self.cursor_visible = True
                self.cursor_timer = 0
                logger.log("📝 Активировано поле ввода пути")
            else:
                self.path_input_active = False

            # проверяем клик по кнопке вставки
            if (self.paste_button_x <= x <= self.paste_button_x + self.paste_button_width and
                    self.paste_button_y <= y <= self.paste_button_y + self.paste_button_height):
                self.paste_from_clipboard()

            # проверяем клик по кнопке загрузки
            if (self.load_button_x <= x <= self.load_button_x + self.load_button_width and
                    self.load_button_y <= y <= self.load_button_y + self.load_button_height):
                self.load_questions()

            # проверяем клик по крестику
            if 470 <= x <= 490 and 420 <= y <= 440:
                logger.log("❌ Окно настроек закрыто")
                # Сохраняем настройки перед закрытием
                self.save_settings()
                # Возобновляем игру
                self.resume_game()
                pyglet.clock.unschedule(self.update_cursor)
                self.close()

    def on_mouse_release(self, x, y, button, modifiers):
        if self.dragging:
            self.dragging = False
            logger.log(f"🎚️ Громкость установлена на {int(self.music_player.volume * 100)}%")
            # Сохраняем настройки при изменении громкости
            self.save_settings()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.dragging:
            # ограничиваем позицию ползунка
            self.slider_pos = max(0, min(self.slider_width, x - self.slider_x))
            # меняем громкость (0-1)
            volume = self.slider_pos / self.slider_width
            self.music_player.set_volume(volume)

    def on_mouse_motion(self, x, y, dx, dy):
        # проверяем наведение на крестик
        self.mouse_over_close = (470 <= x <= 490 and 420 <= y <= 440)
        # проверяем наведение на кнопку вставки
        self.mouse_over_paste = (self.paste_button_x <= x <= self.paste_button_x + self.paste_button_width and
                                 self.paste_button_y <= y <= self.paste_button_y + self.paste_button_height)
        # проверяем наведение на кнопку загрузки
        self.mouse_over_load = (self.load_button_x <= x <= self.load_button_x + self.load_button_width and
                                self.load_button_y <= y <= self.load_button_y + self.load_button_height)

    def on_text(self, text):
        """Обработка ввода текста"""
        if self.path_input_active:
            # вставляем текст в позицию курсора
            self.path_text = self.path_text[:self.cursor_position] + text + self.path_text[self.cursor_position:]
            self.cursor_position += len(text)
            logger.log(f"📝 Ввод: {text}")

    def on_text_motion(self, motion):
        """Обработка специальных клавиш"""
        if self.path_input_active:
            if motion == pyglet.window.key.MOTION_BACKSPACE:
                if self.cursor_position > 0:
                    self.path_text = self.path_text[:self.cursor_position - 1] + self.path_text[self.cursor_position:]
                    self.cursor_position -= 1
                    logger.log("📝 Backspace")
            elif motion == pyglet.window.key.MOTION_DELETE:
                if self.cursor_position < len(self.path_text):
                    self.path_text = self.path_text[:self.cursor_position] + self.path_text[self.cursor_position + 1:]
                    logger.log("📝 Delete")
            elif motion == pyglet.window.key.MOTION_LEFT:
                if self.cursor_position > 0:
                    self.cursor_position -= 1
                    logger.log("📝 Курсор влево")
            elif motion == pyglet.window.key.MOTION_RIGHT:
                if self.cursor_position < len(self.path_text):
                    self.cursor_position += 1
                    logger.log("📝 Курсор вправо")
            elif motion == pyglet.window.key.MOTION_BEGINNING_OF_LINE:
                self.cursor_position = 0
                logger.log("📝 Курсор в начало")
            elif motion == pyglet.window.key.MOTION_END_OF_LINE:
                self.cursor_position = len(self.path_text)
                logger.log("📝 Курсор в конец")

    def paste_from_clipboard(self):
        """Вставляет текст из буфера обмена"""
        try:
            # Пытаемся получить текст из буфера обмена разными способами
            clipboard_text = None

            # Способ 1: через pyglet (может не работать на некоторых системах)
            try:
                clipboard_text = pyglet.app.platform.get_default().get_clipboard_text()
            except:
                pass

            # Способ 2: через Tkinter (более надежный)
            if not clipboard_text:
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()  # скрываем окно
                    clipboard_text = root.clipboard_get()
                    root.destroy()
                except:
                    pass

            # Способ 3: через PyQt5 если установлен
            if not clipboard_text:
                try:
                    from PyQt5.QtWidgets import QApplication
                    import sys
                    app = QApplication.instance()
                    if not app:
                        app = QApplication(sys.argv)
                    clipboard_text = app.clipboard().text()
                except:
                    pass

            if clipboard_text:
                # Вставляем текст в текущую позицию курсора
                self.path_text = self.path_text[:self.cursor_position] + clipboard_text + self.path_text[
                    self.cursor_position:]
                self.cursor_position += len(clipboard_text)
                logger.log(f"📋 Вставлено из буфера: {clipboard_text}")
            else:
                logger.log("📋 Буфер обмена пуст или не удалось получить данные")
        except Exception as e:
            logger.log(f"❌ Ошибка вставки из буфера: {e}")

    def load_questions(self):
        """Загружает вопросы по указанному пути"""
        logger.log(f"📚 Попытка загрузки вопросов из: {self.path_text}")
        success = self.question_loader.set_questions_path(self.path_text)

        if success:
            logger.log("✅ Вопросы успешно загружены")
        else:
            logger.log(f"❌ Ошибка загрузки вопросов: {self.question_loader.last_error}")

        # Сохраняем настройки после загрузки
        self.save_settings()

    def save_settings(self):
        """Сохраняет текущие настройки"""
        self.settings_storage.save_settings(
            self.path_text,
            self.music_player.volume
        )

    def resume_game(self):
        """Возобновляет игру после закрытия настроек"""
        global game_paused, settings_window
        game_paused = False
        settings_window = None
        pyglet.clock.schedule_interval(update, 1 / 60.0)
        logger.log("▶️ Игра возобновлена после настроек")

    def on_close(self):
        """Обработчик закрытия окна (крестик, Alt+F4 и т.д.)"""
        logger.log("❌ Окно настроек закрыто (on_close)")
        # Сохраняем настройки
        self.save_settings()
        # Возобновляем игру
        self.resume_game()
        pyglet.clock.unschedule(self.update_cursor)
        super().on_close()  # вызываем родительский метод


# Создаем окошко
window = pyglet.window.Window(800, 600, "Тамагочи")

# Цветики
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)
YELLOW = (255, 255, 0)
LIGHT_GREEN = (144, 238, 144)
DARK_GRAY = (64, 64, 64)


class AnimatedBackground:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0

        # облачка
        self.clouds = []
        self.create_clouds(3)

        # звездочки
        self.stars = []
        self.create_stars(20)

        # время суток
        self.hour = 12

        logger.log("🌅 Анимированный фон создан")

    def create_clouds(self, count):
        for i in range(count):
            cloud = {
                'x': random.randint(0, self.width),
                'y': random.randint(400, 550),
                'speed': random.uniform(0.2, 0.5),
                'size': random.randint(40, 70)
            }
            self.clouds.append(cloud)
        logger.log(f"☁️ Создано {count} облачка")

    def create_stars(self, count):
        for i in range(count):
            star = {
                'x': random.randint(0, self.width),
                'y': random.randint(300, 580),
                'twinkle_speed': random.uniform(0.5, 2),
                'phase': random.uniform(0, 3.14)
            }
            self.stars.append(star)
        logger.log(f"⭐ Создано {count} звездочек")

    def update(self, dt):
        self.time += dt
        self.hour = (self.hour + dt * 0.5) % 24

        for cloud in self.clouds:
            cloud['x'] += cloud['speed']
            if cloud['x'] > self.width + 100:
                cloud['x'] = -100
                cloud['y'] = random.randint(400, 550)

    def draw(self):
        # небо
        if self.hour < 6 or self.hour > 20:
            sky_color = (10, 10, 30)
            sun_visible = False
        elif self.hour < 8 or self.hour > 18:
            sky_color = (255, 140, 90)
            sun_visible = True
        else:
            sky_color = LIGHT_BLUE
            sun_visible = True

        sky = pyglet.shapes.Rectangle(0, 0, self.width, self.height, color=sky_color)
        sky.draw()

        # солнце/луна
        if sun_visible:
            sun_x = int((self.hour / 24) * self.width)
            sun_y = 500 - abs(self.hour - 12) * 30
            sun = pyglet.shapes.Circle(sun_x, sun_y, 40, color=YELLOW)
            sun.draw()
        else:
            moon_x = int((self.hour / 24) * self.width)
            moon_y = 500 - abs(self.hour - 12) * 30
            moon = pyglet.shapes.Circle(moon_x, moon_y, 30, color=GRAY)
            moon.draw()

            for star in self.stars:
                brightness = 0.5 + 0.5 * (self.time * star['twinkle_speed'] + star['phase']) % 1
                color = int(255 * brightness)
                star_shape = pyglet.shapes.Circle(star['x'], star['y'], 2, color=(color, color, color))
                star_shape.draw()

        # облака
        for cloud in self.clouds:
            cloud_color = (255, 255, 255)
            c1 = pyglet.shapes.Circle(cloud['x'], cloud['y'], cloud['size'] // 2, color=cloud_color)
            c2 = pyglet.shapes.Circle(cloud['x'] + 30, cloud['y'] + 10, cloud['size'] // 3, color=cloud_color)
            c3 = pyglet.shapes.Circle(cloud['x'] - 20, cloud['y'] + 5, cloud['size'] // 3, color=cloud_color)
            c1.draw()
            c2.draw()
            c3.draw()

        # травка
        for i in range(0, self.width, 20):
            grass_height = 20 + 10 * ((self.time * 2 + i) % 1)
            grass = pyglet.shapes.Rectangle(i, 0, 10, grass_height, color=LIGHT_GREEN)
            grass.draw()


class Tamagochi:
    def __init__(self):
        self.x = 300
        self.y = 250
        self.hunger = 100
        self.happiness = 100
        self.last_update = time.time()

        # анимация
        self.animation_time = 0
        self.bounce_offset = 0
        self.bounce_direction = 1
        self.wiggle = 0
        self.original_scale = 1

        # макс размер спрайта
        self.max_sprite_width = 200
        self.max_sprite_height = 200

        # ускоренный расход (для неправильных ответов)
        self.speed_boost_active = False
        self.speed_boost_end_time = 0
        self.speed_multiplier = 1.0

        # грузим капибару
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sprite_path = os.path.join(script_dir, "resource", "kapybara.png")

        try:
            if os.path.exists(sprite_path):
                self.image = pyglet.image.load(sprite_path)

                if self.image.width > self.max_sprite_width or self.image.height > self.max_sprite_height:
                    scale_x = self.max_sprite_width / self.image.width
                    scale_y = self.max_sprite_height / self.image.height
                    scale = min(scale_x, scale_y)
                    self.original_scale = scale

                    self.sprite = pyglet.sprite.Sprite(self.image, x=self.x, y=self.y)
                    self.sprite.scale = scale
                    logger.log(f"🦫 Уменьшили капибару с {self.image.width}x{self.image.height} "
                               f"до {int(self.image.width * scale)}x{int(self.image.height * scale)}")
                else:
                    self.sprite = pyglet.sprite.Sprite(self.image, x=self.x, y=self.y)
                    self.original_scale = 1

                self.has_texture = True
                logger.log("🦫 Капибара загрузилась!")
            else:
                self.has_texture = False
                logger.log(f"❌ Капибара не найдена в {sprite_path}")
        except Exception as e:
            self.has_texture = False
            logger.log(f"❌ Текстура не найдена: {e}")

    def update(self, dt):
        self.animation_time += dt

        # прыжки
        self.bounce_offset += dt * 3 * self.bounce_direction
        if abs(self.bounce_offset) > 10:
            self.bounce_direction *= -1

        # покачивание
        self.wiggle = 5 * ((self.animation_time * 2) % 1 - 0.5)

        if self.happiness < 30:
            self.bounce_offset *= 0.5
        if self.hunger < 30:
            self.wiggle *= 2

        if self.has_texture:
            self.sprite.x = self.x + self.wiggle
            self.sprite.y = self.y + self.bounce_offset

            if self.happiness > 70:
                pulse = 1 + 0.05 * ((self.animation_time * 5) % 1)
                self.sprite.scale = self.original_scale * pulse
            else:
                self.sprite.scale = self.original_scale

        # Проверка ускоренного расхода
        current_time = time.time()
        if self.speed_boost_active and current_time > self.speed_boost_end_time:
            self.speed_boost_active = False
            self.speed_multiplier = 1.0
            logger.log("⚡ Ускоренный расход закончился")

        # обновление голода/счастья
        if current_time - self.last_update > 1:
            old_hunger = self.hunger
            old_happiness = self.happiness

            # Применяем множитель скорости если активен
            hunger_decrease = 2 * self.speed_multiplier
            happiness_decrease = 1 * self.speed_multiplier

            self.hunger = max(0, self.hunger - hunger_decrease)
            self.happiness = max(0, self.happiness - happiness_decrease)
            self.last_update = current_time

            # логируем изменения состояния раз в 10 секунд (чтобы не засорять лог)
            if int(self.animation_time) % 10 == 0:
                boost_info = " (УСКОРЕННО!)" if self.speed_boost_active else ""
                logger.log(f"📊 Голод: {self.hunger}%, Счастье: {self.happiness}%{boost_info}")

    def feed(self, question_loader):
        # Вместо прямого кормления открываем окно вопроса
        logger.log("🍖 Попытка кормления - открывается окно вопроса")
        return QuestionWindow(self, 'feed', question_loader)

    def play(self, question_loader):
        # Вместо прямой игры открываем окно вопроса
        logger.log("🎮 Попытка игры - открывается окно вопроса")
        return QuestionWindow(self, 'play', question_loader)

    def draw(self):
        if self.has_texture:
            self.sprite.draw()
            if self.hunger < 20:
                tear = pyglet.shapes.Circle(self.x + 70, self.y + 130, 5, color=LIGHT_BLUE)
                tear.draw()
            if self.happiness < 20:
                tear = pyglet.shapes.Circle(self.x + 130, self.y + 130, 5, color=GRAY)
                tear.draw()
            # Индикатор ускоренного расхода
            if self.speed_boost_active:
                # Рисуем красный контур вокруг питомца
                glow = pyglet.shapes.Circle(self.x + 100, self.y + 100, 110, color=RED)
                glow.opacity = 100
                glow.draw()
        else:
            circle = pyglet.shapes.Circle(self.x + 100, self.y + 100, 100, color=GREEN)
            circle.draw()
            eye1 = pyglet.shapes.Circle(self.x + 70, self.y + 130, 15, color=BLACK)
            eye2 = pyglet.shapes.Circle(self.x + 130, self.y + 130, 15, color=BLACK)
            eye1.draw()
            eye2.draw()


# создаем хранилище настроек
settings_storage = SettingsStorage()

# создаем питомца, фон, загрузчик вопросов и музыку с сохраненными настройками
logger.log("🚀 Запуск Тамагочи...")
pet = Tamagochi()
background = AnimatedBackground(800, 600)

# Загружаем сохраненный путь к вопросам или используем по умолчанию
saved_path = settings_storage.settings.get("questions_path", "")
if saved_path and os.path.exists(saved_path):
    question_loader = QuestionLoader(saved_path)
else:
    question_loader = QuestionLoader()  # Создаем загрузчик вопросов по умолчанию

# Создаем музыку с сохраненной громкостью
saved_volume = settings_storage.settings.get("music_volume", 0.3)
background_music = BackgroundMusic(saved_volume)
background_music.start()

# окно настроек
settings_window = None
# текущее окно вопроса (если открыто)
question_window = None
# флаг паузы игры
game_paused = False


# кнопка-шестеренка (без подсветки)
class GearButton:
    def __init__(self, x, y, size=40):
        self.x = x
        self.y = y
        self.size = size
        self.rotation = 0
        logger.log(f"⚙️ Шестеренка создана на позиции ({x}, {y})")

    def update(self, dt):
        # шестеренка медленно крутится
        self.rotation += dt * 30  # 30 градусов в секунду

    def draw(self):
        # всегда серый цвет
        color = GRAY

        # основной круг
        center = pyglet.shapes.Circle(self.x, self.y, self.size // 2, color=color)
        center.draw()

        # зубчики (8 штук)
        for i in range(8):
            angle = self.rotation + i * 45
            tooth_x = self.x + math.cos(math.radians(angle)) * (self.size // 2 + 5)
            tooth_y = self.y + math.sin(math.radians(angle)) * (self.size // 2 + 5)
            tooth = pyglet.shapes.Circle(tooth_x, tooth_y, 5, color=color)
            tooth.draw()

        # дырочка в центре
        hole = pyglet.shapes.Circle(self.x, self.y, 8, color=BLACK)
        hole.draw()

    def check_click(self, x, y):
        distance = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        return distance < self.size


# создаем кнопку-шестеренку ПО ЦЕНТРУ СВЕРХУ (x=400)
gear = GearButton(400, 550)


@window.event
def on_draw():
    window.clear()

    background.draw()
    pet.draw()

    # полоски здоровья
    hunger_bg = pyglet.shapes.Rectangle(50, 500, 200, 30, color=GRAY)
    hunger_fill = pyglet.shapes.Rectangle(50, 500, pet.hunger * 2, 30, color=RED)
    happiness_bg = pyglet.shapes.Rectangle(50, 550, 200, 30, color=GRAY)
    happiness_fill = pyglet.shapes.Rectangle(50, 550, pet.happiness * 2, 30, color=BLUE)

    hunger_bg.draw()
    hunger_fill.draw()
    happiness_bg.draw()
    happiness_fill.draw()

    hunger_text = pyglet.text.Label(f"Голод: {int(pet.hunger)}", x=260, y=510, color=(0, 0, 0, 255))
    happy_text = pyglet.text.Label(f"Счастье: {int(pet.happiness)}", x=260, y=560, color=(0, 0, 0, 255))
    hunger_text.draw()
    happy_text.draw()

    # кнопки
    feed_btn = pyglet.shapes.Rectangle(500, 500, 100, 50, color=GREEN)
    play_btn = pyglet.shapes.Rectangle(620, 500, 100, 50, color=BLUE)
    feed_btn.draw()
    play_btn.draw()

    feed_label = pyglet.text.Label("Кормить", x=525, y=520, color=(0, 0, 0, 255))
    play_label = pyglet.text.Label("Играть", x=645, y=520, color=(0, 0, 0, 255))
    feed_label.draw()
    play_label.draw()

    # шестеренка
    gear.draw()

    # Индикатор ускоренного расхода на интерфейсе
    if pet.speed_boost_active:
        boost_text = pyglet.text.Label("⚡ УСКОРЕННЫЙ РАСХОД!",
                                       x=400, y=450,
                                       anchor_x='center', color=RED)
        boost_text.draw()

        # Таймер ускоренного расхода
        remaining = int(pet.speed_boost_end_time - time.time())
        timer_text = pyglet.text.Label(f"Осталось: {remaining} сек",
                                       x=400, y=420,
                                       anchor_x='center', color=RED)
        timer_text.draw()

    # Если игра на паузе - показываем сообщение
    if game_paused:
        pause_text = pyglet.text.Label("⏸ ИГРА НА ПАУЗЕ",
                                       x=400, y=400,
                                       anchor_x='center', font_size=24, color=RED)
        pause_text.draw()

    if pet.hunger <= 0 or pet.happiness <= 0:
        background_music.stop()
        logger.log("💀 Питомец умер!")
        pyglet.app.exit()


def update(dt):
    global question_window, game_paused

    # Если игра на паузе - ничего не обновляем
    if game_paused:
        return

    pet.update(dt)
    background.update(dt)
    gear.update(dt)

    # Проверяем не закрыто ли окно вопроса
    if question_window and not question_window.is_active:
        question_window = None
        game_paused = False


@window.event
def on_mouse_press(x, y, button, modifiers):
    global settings_window, question_window, game_paused

    if button == mouse.LEFT:
        # Если игра на паузе или открыто окно вопроса - не обрабатываем клики в основном окне
        if game_paused or question_window is not None:
            return

        if 500 <= x <= 600 and 500 <= y <= 550:
            # Кормление - открываем окно вопроса и ставим игру на паузу
            game_paused = True
            question_window = pet.feed(question_loader)
        elif 620 <= x <= 720 and 500 <= y <= 550:
            # Игра - открываем окно вопроса и ставим игру на паузу
            game_paused = True
            question_window = pet.play(question_loader)
        elif gear.check_click(x, y):
            if settings_window is None or not settings_window.visible:
                logger.log("⚙️ Открытие окна настроек")
                # Ставим игру на паузу при открытии настроек
                game_paused = True
                pyglet.clock.unschedule(update)
                settings_window = SettingsWindow(background_music, question_loader, settings_storage)
            else:
                logger.log("⚙️ Закрытие окна настроек")
                settings_window.close()
                settings_window = None


# запускаем анимацию
pyglet.clock.schedule_interval(update, 1 / 60.0)

logger.log("🎮 Игра запущена!")
# запускаем приложение
pyglet.app.run()
logger.log("👋 Игра завершена")