import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import ctypes
import psycopg2
from time import sleep
import threading

# Ustawienie zmiennych
credentials = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "xxx"
}
current_word_index = 0

# Funkcja do uzyskiwania rozmiaru ekranu
def get_screen_size():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# Funkcja do ustawiania rozmiaru i położenia okna
def set_window_position(window, width, height):
    screen_width, screen_height = get_screen_size()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

# Funkcja do łączenia się z bazą danych postgres
def connect_to_database(credentials):
    conn = psycopg2.connect(**credentials)
    return conn

# Funkcja do logowania
def login(conn, username, password):
    cursor = conn.cursor()
    query = "SELECT * FROM wordsgame WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()
    cursor.close()
    return user

# Funkcja do dodawania nowego użytkownika
def register(conn, username, password):
    cursor = conn.cursor()
    query = "INSERT INTO wordsgame (username, password) VALUES (%s, %s)"
    cursor.execute(query, (username, password))
    conn.commit()
    cursor.close()

# Funkcja do pobierania słów użytkownika
def get_user_words(conn, user_id):
    cursor = conn.cursor()
    query = "SELECT id, word, meaning, pinyin FROM wordsgame WHERE username = %s AND word is not null"
    cursor.execute(query, (user_id,))
    words = cursor.fetchall()
    cursor.close()
    return words

# Funkcja do aktualizowania słowa użytkownika w bazie danych
def update_user_word(conn, word_id, word, meaning, pinyin):
    cursor = conn.cursor()
    query = "UPDATE wordsgame SET word = %s, meaning = %s, pinyin = %s WHERE id = %s"
    cursor.execute(query, (word, meaning, pinyin, word_id))
    conn.commit()
    cursor.close()

# Funkcja do obsługi przycisku "Lista słów"
def show_word_list_screen():
    frame_menu.pack_forget()
    frame_main.pack_forget()  # Ukryj główny ekran
    frame_add_word.pack_forget()  # Ukryj ekran dodawania słów
    frame_word_list.pack()  # Wyświetl ekran listy słów
    refresh_word_list()  # Odśwież listę słów

# Funkcja do aktualizowania wszystkich słów w bazie danych
def update_all_words(updated_words):
    for word_data in updated_words:
        word_id, entry_word, entry_meaning, entry_pinyin = word_data
        update_word(word_id, entry_word.get(), entry_meaning.get(), entry_pinyin.get())
    back_to_menu()

# Funkcja do aktualizowania słowa w bazie danych
def update_word(word_id, word, meaning, pinyin):
    update_user_word(conn, word_id, word, meaning, pinyin)

def refresh_word_list():
    for widget in frame_word_list.winfo_children():
        widget.destroy()

    # Pobierz słowa za pomocą polecenia SELECT
    cursor = conn.cursor()
    query = "SELECT id, word, meaning, pinyin FROM wordsgame where word is not null"
    cursor.execute(query)
    words = cursor.fetchall()
    cursor.close()

    # Przechowaj aktualizowane dane w liście
    updated_words = []

    # Dodaj słowa do listy words
    for word in words:
        word_id, word_text, meaning, pinyin = word
        entry_word = tk.Entry(frame_word_list, width=int(window_width/5))
        entry_word.insert(0, word_text)
        entry_word.grid(row=words.index(word), column=0, padx=5, pady=5)
        entry_meaning = tk.Entry(frame_word_list, width=int(window_width/5))
        entry_meaning.insert(0, meaning)
        entry_meaning.grid(row=words.index(word), column=1, padx=5, pady=5)
        entry_pinyin = tk.Entry(frame_word_list, width=int(window_width/5))
        entry_pinyin.insert(0, pinyin)
        entry_pinyin.grid(row=words.index(word), column=2, padx=5, pady=5)

        # Dodaj dane do listy aktualizowanych słów
        updated_words.append((word_id, entry_word, entry_meaning, entry_pinyin))

    # Stwórz tylko jeden przycisk zapisywania, który zaktualizuje wszystkie słowa na raz
    button_save = tk.Button(frame_word_list, text="Zapisz wszystkie", width=int(window_width/5),
                            command=lambda: update_all_words(updated_words))
    button_save.grid(row=len(words), column=0, columnspan=3, padx=5, pady=5)


def start_learning():
    global words
    global current_word_index
    words = get_user_words(conn, username)
    current_word_index = 1
    frame_menu.pack_forget()
    frame_main.pack()
    display_random_word()

# Funkcja do obsługi przycisku "Dodaj słowa"
def show_add_word_screen():
    frame_menu.pack_forget()
    frame_add_word.pack()

# Funkcja do obsługi przycisku "Dodaj"
def add_word_to_database():
    han = entry_han.get()
    pinyin = entry_pinyin.get()
    znaczenie = entry_znaczenie.get()
    add_word(conn, username, han, znaczenie, pinyin)
    messagebox.showinfo("Sukces", "Słowo zostało dodane!")
    frame_add_word.pack_forget()
    frame_menu.pack()

# Funkcja do powrotu do menu
def back_to_menu():
    frame_add_word.pack_forget()
    frame_word_list.pack_forget()
    frame_menu.pack()

# Funkcja do obsługi logowania
def handle_login():
    global username
    username = entry_username.get()
    password = entry_password.get()
    user = login(conn, username, password)
    if user:
        frame_login.pack_forget()
        frame_menu.pack()
    else:
        messagebox.showerror("Błąd logowania", "Nieprawidłowe dane logowania")

# Funkcja do dodawania nowego słowa
def add_word(conn, user_id, han, znaczenie, pinyin):
    cursor = conn.cursor()
    query = "INSERT INTO wordsgame (username, word, meaning, pinyin) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user_id, han, znaczenie, pinyin))
    conn.commit()
    cursor.close()

# Funkcja do obsługi rejestracji
def handle_registration():
    username = entry_username.get()
    password = entry_password.get()
    register(conn, username, password)
    messagebox.showinfo("Sukces", "Konto zostało utworzone! Możesz się teraz zalogować.")

# Funkcja do wyświetlania znaczenia słowa
def display_meaning():
    if current_word_index > 0:
        _, han, znaczenie, _ = words[current_word_index - 1]
        label_znaczenie.config(text=znaczenie)
# Blokada dla wątku wyświetlania pinyin
pinyin_lock = threading.Lock()

# Funkcja do wyświetlania losowego słowa
def display_random_word():
    global current_word_index
    if current_word_index < len(words):
        _, han, znaczenie, pinyin = words[current_word_index]
        label_han.config(text=han)
        label_znaczenie.config(text="")
        current_word_index += 1
        # Wyłącz aktualnie działający wątek, jeśli istnieje
        with pinyin_lock:
            if hasattr(display_random_word, 'pinyin_thread'):
                display_random_word.pinyin_thread.cancel()
            # Uruchomienie nowego wątku, który wyświetli pinyin po 6 sekundach
            display_random_word.pinyin_thread = threading.Timer(4,show_pinyin_after_delay, args=(pinyin,))
            display_random_word.pinyin_thread.start()
    else:
        messagebox.showinfo("Koniec słów", "Nie ma więcej słów do nauki!")
        frame_main.pack_forget()
        frame_menu.pack()

# Funkcja do wyświetlania pinyin po opóźnieniu
def show_pinyin_after_delay(pinyin):
    label_pinyin.config(text=pinyin)

# Funkcja do aktualizacji szerokości elementów przy zmianie rozmiaru okna
def update_width(event):
    global window_width
    window_width = event.width
    root.after(100, update_elements)

# Funkcja do aktualizacji szerokości elementów
def update_elements():
    entry_username.config(width=int(window_width/16))
    entry_password.config(width=int(window_width/16))


# Ustawienie połączenia
conn = connect_to_database(credentials)


# Inicjalizacja głównego okna Tkinter
root = tk.Tk()
root.title("Aplikacja do nauki słówek")
s=ttk.Style(root)
s.theme_use("clam")
# Ustawienie rozmiaru i położenia głównego okna
window_width = 600
window_height = 600
set_window_position(root, window_width, window_height)

# Ramka dla ekranu logowania
frame_login = tk.Frame(root)
label_username = tk.Label(frame_login, text="Użytkownik:")
label_username.grid(row=0, column=0, padx=5, pady=5)
entry_username = tk.Entry(frame_login, width=int(window_width/8))
entry_username.grid(row=0, column=1, padx=10, pady=10)
label_password = tk.Label(frame_login, text="Hasło:")
label_password.grid(row=1, column=0, padx=5, pady=5)
entry_password = tk.Entry(frame_login, show="*", width=int(window_width/8))
entry_password.grid(row=1, column=1, padx=10, pady=10)
button_login = tk.Button(frame_login, text="Zaloguj", width=int(window_width/16), command=handle_login)
button_login.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
button_register = tk.Button(frame_login, text="Zarejestruj", width=int(window_width/16), command=handle_registration)
button_register.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
frame_login.pack(padx=10, pady=10)

# Dodanie zdarzenia zmiany rozmiaru okna
root.bind("<Configure>", update_width)


# Ramka dla menu głównego
frame_menu = tk.Frame(root)
button_learn = tk.Button(frame_menu, text="Ucz się", width=int(window_width/16), command=start_learning)
button_learn.pack(pady=10)
button_add_words = tk.Button(frame_menu, text="Dodaj słowa", width=int(window_width/16), command=show_add_word_screen)
button_add_words.pack(pady=10)
button_word_list = tk.Button(frame_menu, text="Lista słów", width=int(window_width/16), command=show_word_list_screen)
button_word_list.pack(pady=10)

# Ramka dla dodawania słów
frame_add_word = tk.Frame(root)
label_han = tk.Label(frame_add_word, text="Słowo:", width=int(window_width/16))
label_han.grid(row=0, column=0, padx=5, pady=5)
entry_han = tk.Entry(frame_add_word, width=int(window_width/16))
entry_han.grid(row=0, column=1, padx=5, pady=5)
label_pinyin = tk.Label(frame_add_word, text="Pinyin:", width=int(window_width/16))
label_pinyin.grid(row=1, column=0, padx=5, pady=5)
entry_pinyin = tk.Entry(frame_add_word, width=int(window_width/16))
entry_pinyin.grid(row=1, column=1, padx=5, pady=5)
label_znaczenie = tk.Label(frame_add_word, text="Znaczenie:", width=int(window_width/16))
label_znaczenie.grid(row=2, column=0, padx=5, pady=5)
entry_znaczenie = tk.Entry(frame_add_word, width=int(window_width/16))
entry_znaczenie.grid(row=2, column=1, padx=5, pady=5)
button_add = tk.Button(frame_add_word, text="Dodaj", width=int(window_width/16), command=add_word_to_database)
button_add.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
button_back = tk.Button(frame_add_word, text="Cofnij", width=int(window_width/16), command=back_to_menu)
button_back.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

# Ramka dla głównej części aplikacji
frame_main = tk.Frame(root)
label_han = tk.Label(frame_main, font=("Helvetica", 24))
label_han.pack(pady=20)
label_pinyin = tk.Label(frame_main, font=("Helvetica", 16))
label_pinyin.pack(pady=10)
label_znaczenie = tk.Label(frame_main, font=("Helvetica", 16))
label_znaczenie.pack(pady=10)
button_meaning = tk.Button(frame_main, text="Znaczenie", width=int(window_width/16), command=display_meaning)
button_meaning.pack(side=tk.LEFT, padx=10)
button_next = tk.Button(frame_main, text="Dalej", width=int(window_width/16), command=display_random_word)
button_next.pack(side=tk.RIGHT, padx=10)

# Ramka dla listy słów
frame_word_list = tk.Frame(root)
tree=ttk.Treeview(frame_word_list)
tree["columns"]=("ID","Word","Meaning","Pinyin") 

tree.column("#0",width=0,stretch=tk.NO)
tree.column("ID",width=50,minwidth=50,anchor=tk.CENTER)
tree.column("Word",width=50,minwidth=50,anchor=tk.CENTER)
tree.column("Meaning",width=50,minwidth=50,anchor=tk.CENTER)
tree.column("Pinyin",width=50,minwidth=50,anchor=tk.CENTER)

tree.heading("#0",text="",anchor=tk.CENTER)
tree.heading("ID",text="ID",anchor=tk.CENTER)
tree.heading("Word",text="Word",anchor=tk.CENTER)
tree.heading("Meaning",text="Meaning",anchor=tk.CENTER)
tree.heading("Pinyin",text="Pinyin",anchor=tk.CENTER)

tree.pack()

# Uruchomienie głównej pętli Tkinter
root.mainloop()
