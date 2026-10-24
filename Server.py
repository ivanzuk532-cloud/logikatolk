#Server

import threading
from socket import *
from customtkinter import *


class LogiTalk(CTk):

    def __init__(self):
        # Ініціалізація головного вікна CustomTkinter
        super().__init__()

        # --- Налаштування параметрів головного вікна ---
        self.title("LogiTalk")
        self.geometry("400x300")
        self.minsize(400, 300)

        # Ім'я користувача за замовчуванням
        self.username = "Клієнт"

        # Налаштування сітки (Grid):
        # Колонці 1 (чат) даємо маштабування (weight=1), щоб вона розширювалася
        # Рядку 0 (основний контент) також даємо розширення
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Ліва бічна панель (Профіль та налаштування) ---
        self.frame = CTkFrame(self, width=200)
        self.frame.grid(row=0, column=0, rowspan=2, sticky="ns")
        # Забороняємо фрейму стискатися під розмір внутрішніх елементів
        self.frame.grid_propagate(False)

        # Елементи профілю: Текст вітання, поле для введення ніка та кнопка зміни
        self.label = CTkLabel(self.frame, text=f"Привіт, {self.username}")
        self.label.pack(pady=30)

        self.entry = CTkEntry(self.frame)
        self.entry.pack()

        CTkButton(
            self.frame, text="Прийняти", command=self.set_username
        ).pack(pady=30)

        # Перемикач теми (Світла / Темна) внизу бічної панелі
        CTkOptionMenu(
            self.frame,
            values=["Світла", "Темна"],
            command=self.change_theme,
        ).pack(side="bottom", pady=20)

        # --- Права частина: Область повідомлень чату ---
        # Використовуємо CTkScrollableFrame для автоматичної прокрутки повідомлень
        self.chat_text = CTkScrollableFrame(self)
        self.chat_text.grid(row=0, column=1, sticky="nsew")

        # --- Нижня панель: Поле введення та кнопка відправки ---
        bottom = CTkFrame(self)
        bottom.grid(row=1, column=1, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self.message_input = CTkEntry(
            bottom, placeholder_text="Ваше повідомлення"
        )
        self.message_input.grid(row=0, column=0, sticky="ew", padx=(5, 0), pady=5)

        self.send_button = CTkButton(
            bottom, text="▶️", width=40, command=self.send_message
        )
        self.send_button.grid(row=0, column=1, padx=5, pady=5)

        # --- Мережеве підключення (Socket) ---
        try:
            # Створення TCP-сокета та підключення до сервера
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(("127.0.0.1", 8080))

            # Формування та відправка системного повідомлення про вхід
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднується до чату!\n"
            self.sock.send(hello.encode())

            # Запуск окремого фонового потоку для безперервного прийому повідомлень
            # daemon=True означає, що потік закриється разом із закриттям програми
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            # Якщо сервер недоступний — виводимо помилку в чат
            self.add_message(f"Не вдалось підключитись: {e}")

    def set_username(self):
        """Змінює ім'я користувача на введене в текстовому полі"""
        self.username = self.entry.get()
        self.label.configure(text=f"Привіт, {self.username}")
        self.entry.delete(0, END)

    def add_message(self, message, img=None, own_message=False):
        """Додає нове повідомлення в графічний інтерфейс чату.

        own_message=True відповідає за вирівнювання (свої — праворуч, чужі —
        ліворуч).
        """
        # Колір фону хмарки повідомлення (свої — світліші, чужі — темніші)
        bg = "#4a4a4a" if own_message else "#2d2d2d"

        # Створення контейнера (хмарки) для повідомлення
        f = CTkFrame(self.chat_text, fg_color=bg)
        # Притискаємо праворуч ("e"), якщо це наше повідомлення, і ліворуч ("w"), якщо чуже
        f.pack(anchor="e" if own_message else "w", pady=5, padx=5)

        # Текст повідомлення з переносом довгих слів (wraplength=260)
        CTkLabel(f, text=message, wraplength=260, justify="left").pack(
            padx=10, pady=5
        )

    def send_message(self):
        """Зчитує текст із поля введення, показує в чаті та відправляє на сервер"""
        msg = self.message_input.get()
        if not msg:
            return  # Якщо текст порожній — нічого не робимо

        # Відображаємо власний текст у чаті
        self.add_message(f"{self.username}: {msg}", own_message=True)

        try:
            # Відправляємо протокольне повідомлення на сервер (формат: TEXT@user@message)
            self.sock.sendall(f"TEXT@{self.username}@{msg}\n".encode())
        except:
            pass

        # Очищаємо поле введення після відправки
        self.message_input.delete(0, END)

    def recv_message(self):
        """Функція для роботи у фоновому потоці.

        Слухає сокет та обробляє вхідні дані.
        """
        buf = ""
        while True:
            try:
                # Отримуємо дані з сокета пакетами до 4096 байт
                data = self.sock.recv(4096)
                if not data:
                    break

                # Декодуємо байти у рядок
                buf += data.decode(errors="ignore")

                # Обробляємо буфер по рядках (розділювач '\n')
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    self.handle_line(line)
            except:
                break

    def handle_line(self, line):
        """Розбирає отриманий рядок за протоколом та додає його в чат"""
        # Розбиваємо рядок за символом '@' (не більше 3 частин)
        parts = line.split("@", 3)

        # Перевірка типу повідомлення (TEXT) та кількості елементів
        if parts[0] == "TEXT" and len(parts) == 3:
            # parts[1] — відправник, parts[2] — текст повідомлення
            self.add_message(f"{parts[1]}: {parts[2]}")

    def change_theme(self, value):
        """Змінює колірну тему додатка (Темна / Світла)"""
        set_appearance_mode("dark" if value == "Темна" else "light")


# --- Запуск додатка ---
if __name__ == "__main__":
    LogiTalk().mainloop()