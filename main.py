import socket
import threading

# --- Налаштування мережі ---
# Локальна адреса (для запуску на одному комп'ютері) та порт для підключення
HOST = "127.0.0.1"
PORT = 8080

# Список для зберігання об'єктів підключення всіх активних клієнтів
clients = []


def broadcast(message, sender_socket):
    """Розсилає отримане повідомлення всім підключеним клієнтам,

    крім того, хто його відправив (щоб він не бачив своє повідомлення двічі).
    """
    for client in clients:
        if client != sender_socket:
            try:
                # Відправляємо байти клієнту
                client.sendall(message)
            except:
                # Якщо клієнт раптово відключився — закриваємо його сокет і видаляємо зі списку
                client.close()
                if client in clients:
                    clients.remove(client)


def handle_client(client_socket):
    """Функція для фонового потоку.

    Обслуговує конкретного підключеного клієнта: читає від нього дані та
    пересилає іншим.
    """
    buf = ""
    while True:
        try:
            # Отримуємо дані від клієнта (до 4096 байт)
            data = client_socket.recv(4096)
            if not data:
                break  # Якщо дані порожні — клієнт розірвав з'єднання

            # Декодуємо байти у рядок та додаємо до буфера
            buf += data.decode(errors="ignore")

            # Обробляємо повідомлення по рядках, оскільки вони розділені символом '\n'
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                print(f"[Отримано від клієнта]: {line}")

                # Пересилаємо рядок усім іншим учасникам чату (повертаючи символ '\n' в кінці)
                broadcast((line + "\n").encode(), client_socket)
        except:
            # У разі будь-якої помилки мережі виходимо з циклу
            break

    # Коли цикл завершився (клієнт вийшов), видаляємо його з активного списку
    if client_socket in clients:
        clients.remove(client_socket)
    client_socket.close()
    print("[-] Клієнт відключився від сервера.")


def start_server():
    """Головна функція запуску сервера"""
    # Створюємо TCP-сокет (AF_INET — IPv4, SOCK_STREAM — TCP)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Дозволяємо повторно використовувати порт одразу після зупинки програми
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Прив'язуємо сокет до IP-адреси та порту
    server.bind((HOST, PORT))

    # Переводимо сервер у режим прослуховування вхідних з'єднань
    server.listen()
    print(f"[*] Сервер запущено на {HOST}:{PORT}. Очікування підключень...")

    while True:
        # Чекаємо на підключення нового клієнта (метод accept блокує потік до появи клієнта)
        client_socket, addr = server.accept()
        print(f"[+] Нове підключення з IP: {addr}")

        # Додаємо нового клієнта до загального списку
        clients.append(client_socket)

        # Створюємо та запускаємо окремий потік для цього клієнта,
        # щоб сервер міг одночасно працювати з багатьма людьми (багатопотоковість)
        threading.Thread(
            target=handle_client, args=(client_socket,), daemon=True
        ).start()


# Запуск сервера при виконанні цього файлу
if __name__ == "__main__":
    start_server()