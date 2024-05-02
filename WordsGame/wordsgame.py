import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import ctypes
import psycopg2
from time import sleep
import threading
import customtkinter as ctk

# Connection to Postgres DB
credentials = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "xxxx"
}
current_word_index = 0


class TreeviewEdit(ttk.Treeview):
    def __init__(self,master,**kw):
        super().__init__(master,**kw)

        self.bind("<Double-1>",self.on_double_click)
        self.bind("<Delete>",self.on_delete)

    def on_double_click(self,event):
        region_clicked=self.identify_region(event.x,event.y)
        if region_clicked not in ("cell"):
            return
        
        column=self.identify_column(event.x)

        column_index=int(column[1:])-1
        selected_iid=self.focus()
        selected_values=self.item(selected_iid)
        selected_text=selected_values.get("values")[column_index]
        
        column_box=self.bbox(selected_iid,column)

        entry_edit=ttk.Entry(frame_word_list,width=column_box[2])
        entry_edit.editing_column_index=column_index
        entry_edit.editing_column_iid=selected_iid
        entry_edit.insert(0,selected_text)
        entry_edit.select_range(0,tk.END)
        entry_edit.focus()
        entry_edit.bind("<FocusOut>",self.on_focus_out)
        entry_edit.bind("<Return>",self.on_enter)


        entry_edit.place(x=column_box[0],
                         y=column_box[1],
                         w=column_box[2],
                         h=column_box[3])
        
    def on_focus_out(self,event):
        event.widget.destroy()
        refresh_word_list()
    def on_enter (self,event):
        new_text=event.widget.get()
        selected_iid=event.widget.editing_column_iid
        column_index=event.widget.editing_column_index

        current_values=self.item(selected_iid).get("values")
        
        current_values[column_index]=new_text
        update_db(current_values)
        self.item(selected_iid,values=current_values)


        event.widget.destroy()

    def on_delete(self,event):
        column=self.identify_column(event.x)
        column_index=int(column[1:])-1
        selected_iid=self.focus()
        selected_values=self.item(selected_iid)
        selected_text=selected_values.get("values")[column_index]
        current_values=self.item(selected_iid).get("values")
        delete_db (current_values)  
        refresh_word_list()
        

def delete_db(current_values):
    record_id=current_values[3]
    conn=connect_to_database(credentials)
    cursor = conn.cursor()
    try:
        query = f"delete from wordsgame where id={record_id}"
        cursor.execute(query)
        conn.commit()
        cursor.close()
    except:
        pass

def update_db(current_values):
    word=current_values[0]
    meaning=current_values[1]
    pinyin=current_values[2]
    record_id=current_values[3]
    conn=connect_to_database(credentials)
    cursor = conn.cursor()
    query = "Update wordsgame set word=%s,meaning=%s ,pinyin=%s where id=%s"
    cursor.execute(query, (word,meaning,pinyin,record_id))
    conn.commit()
    cursor.close()

def get_screen_size():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def set_window_position(window, width, height):
    screen_width, screen_height = get_screen_size()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def connect_to_database(credentials):
    conn = psycopg2.connect(**credentials)
    return conn


def login(conn, username, password):
    cursor = conn.cursor()
    query = "SELECT * FROM wordsgame WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()
    cursor.close()
    return user


def register(conn, username, password):
    cursor = conn.cursor()
    query = "INSERT INTO wordsgame (username, password) VALUES (%s, %s)"
    cursor.execute(query, (username, password))
    conn.commit()
    cursor.close()


def get_user_words(conn, user_id):
    cursor = conn.cursor()
    query = "SELECT id, word, meaning, pinyin FROM wordsgame WHERE username = %s AND word is not null"
    cursor.execute(query, (user_id,))
    words = cursor.fetchall()
    cursor.close()
    return words


def update_user_word(conn, word_id, word, meaning, pinyin):
    cursor = conn.cursor()
    query = "UPDATE wordsgame SET word = %s, meaning = %s, pinyin = %s WHERE id = %s"
    cursor.execute(query, (word, meaning, pinyin, word_id))
    conn.commit()
    cursor.close()


def show_word_list_screen():
    frame_menu.pack_forget()
    frame_word_list_menu.pack_forget()
    frame_main.pack_forget() 
    frame_add_word.pack_forget() 
    frame_word_list.pack(expand=True, fill='both')
    frame_word_list_menu.pack(expand=True, fill='both')
    refresh_word_list() 

#Update records in DB
def update_all_words(updated_words):
    for word_data in updated_words:
        word_id, entry_word, entry_meaning, entry_pinyin = word_data
        update_word(word_id, entry_word.get(), entry_meaning.get(), entry_pinyin.get())
    back_to_menu()

#Update selected word in DB
def update_word(word_id, word, meaning, pinyin):
    update_user_word(conn, word_id, word, meaning, pinyin)


#Refresh table words_list
def refresh_word_list():    
    for child in frame_word_list.get_children():
        frame_word_list.delete(child)

    cursor = conn.cursor()
    query = "SELECT id, word, meaning, pinyin FROM wordsgame where word is not null"
    cursor.execute(query)
    words = cursor.fetchall()
    cursor.close()
    for record in words:
        id, word,meaning, pinyin = record
        frame_word_list.insert(parent="",
                        index=tk.END,
                        values=(f"{word}",f"{meaning}",f"{pinyin}",f"{id}"))


def start_learning():
    global words
    global current_word_index
    words = get_user_words(conn, username)
    current_word_index = 0
    frame_menu.pack_forget()
    frame_main.pack(expand=True, fill='both')
    display_random_word()

#Add word button
def show_add_word_screen():
    frame_menu.pack_forget()
    frame_add_word.pack(expand=True, fill='both')

def add_word_to_database():
    han = entry_han.get()
    if han == '':
         messagebox.showerror("Error", "Enter word")
         return 
    pinyin = entry_pinyin.get()
    znaczenie = entry_znaczenie.get()
    add_word(conn, username, han, znaczenie, pinyin)
    messagebox.showinfo("Sucess", "Word added!")
    frame_add_word.pack_forget()
    frame_menu.pack(expand=True, fill='both')

def add_word(conn, user_id, han, znaczenie, pinyin):
    cursor = conn.cursor()
    query = "INSERT INTO wordsgame (username, word, meaning, pinyin) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user_id, han, znaczenie, pinyin))
    conn.commit()
    cursor.close()

def back_to_menu():
    frame_add_word.pack_forget()
    frame_word_list.pack_forget()
    frame_word_list_menu.pack_forget()
    frame_main.pack_forget()
    frame_menu.pack(expand=True, fill='both')


def handle_login():
    global username
    username = entry_username.get()
    password = entry_password.get()
    user = login(conn, username, password)
    if user:
        frame_login.pack_forget()
        frame_menu.pack(expand=True, fill='both')
    else:
        messagebox.showerror("Login Error", "Wrong login credentials")


def handle_registration():
    username = entry_username.get()
    password = entry_password.get()
    if username =="" or password=="":
        messagebox.showerror("Error", "You need to write username and password ,then click register")
    else:
        register(conn, username, password)
        messagebox.showinfo("Success", "Your account has been created. Now you can log in")


def display_meaning():
    if current_word_index > 0:
        _, han, znaczenie, _ = words[current_word_index - 1]
        label_znaczenie.config(text=znaczenie)


pinyin_lock = threading.Lock()


def display_random_word():
    global current_word_index
    label_pinyin.config(text='')
    if current_word_index < len(words):
        _, han, znaczenie, pinyin = words[current_word_index]
        label_han.config(text=han)
        label_znaczenie.config(text="")
        current_word_index += 1
        with pinyin_lock:
            if hasattr(display_random_word, 'pinyin_thread'):
                display_random_word.pinyin_thread.cancel()
            display_random_word.pinyin_thread = threading.Timer(4,show_pinyin_after_delay, args=(pinyin,))
            display_random_word.pinyin_thread.start()
    else:
        messagebox.showinfo("Thats all", "There are no more words to learn!")
        frame_main.pack_forget()
        frame_menu.pack(expand=True, fill='both')

# Function to display pinyin after delay
def show_pinyin_after_delay(pinyin):
    try:
        label_pinyin.config(text=pinyin)
    except:
        pass



conn = connect_to_database(credentials)


def set_window_position(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")


if __name__ == "__main__":
    ctk.set_appearance_mode('system')
    ctk.set_default_color_theme('dark-blue')
    root = tk.Tk()
    root.title("Flashcards APP")
    root.minsize(300, 200)
    window_width = 600
    window_height = 600
    set_window_position(root, window_width, window_height)

    # Login screen frame
    frame_login = tk.Frame(root)
    frame_login.pack(expand=True, fill='both')

    frame_login.columnconfigure((0, 3), weight=2)
    frame_login.columnconfigure((1, 2), weight=1)
    frame_login.rowconfigure((0, 5), weight=10)
    frame_login.rowconfigure((1, 2, 3, 4), weight=1)

    username_label = ctk.CTkLabel(frame_login, text='Username', font=('Arial', 18))
    username_label.grid(row=1, column=1)
    entry_username = ctk.CTkEntry(frame_login)
    entry_username.grid(row=1, column=2, sticky='ew', padx=10, pady=20)

    password_label = ctk.CTkLabel(frame_login, text='Password', font=('Arial', 18))
    password_label.grid(row=2, column=1)
    entry_password = ctk.CTkEntry(frame_login, show='*')
    entry_password.grid(row=2, column=2, sticky='ew', padx=10, pady=10)

    login_button = tk.Button(frame_login, text='Login', font=('Arial', 18), command=handle_login)
    login_button.grid(row=3, column=1, columnspan=2, sticky='ew', padx=10, pady=10)

    register_button =  tk.Button(frame_login, text='Register', font=('Arial', 18), command=handle_registration)
    register_button.grid(row=4, column=1, columnspan=2, sticky='ew', padx=10, pady=10)

    #Main Manu Frame
    frame_menu = tk.Frame(root)

    frame_menu.columnconfigure((0, 3), weight=2)
    frame_menu.columnconfigure((1, 2), weight=1)
    frame_menu.rowconfigure((0, 5), weight=10)
    frame_menu.rowconfigure((1, 2, 3, 4), weight=1)

    button_learn = tk.Button(frame_menu, text="Learn", font=('Arial', 18), command=start_learning)
    button_learn.grid(row=1, column=1,columnspan=2, sticky='ew', padx=10, pady=10)
    button_add_words = tk.Button(frame_menu, text="Add words", font=('Arial', 18), command=show_add_word_screen)
    button_add_words.grid(row=2, column=1,columnspan=2, sticky='ew', padx=10, pady=10)
    button_word_list = tk.Button(frame_menu, text="Word list", font=('Arial', 18), command=show_word_list_screen)
    button_word_list.grid(row=3, column=1,columnspan=2, sticky='ew', padx=10, pady=10)

    #Add words Frame
    frame_add_word = tk.Frame(root)
    frame_add_word.columnconfigure((0, 3), weight=2)
    frame_add_word.columnconfigure((1, 2), weight=1)
    frame_add_word.rowconfigure((0, 5), weight=10)
    frame_add_word.rowconfigure((1, 2, 3, 4), weight=1)

    label_han = tk.Label(frame_add_word, text="Word:", font=('Arial', 18))
    label_han.grid(row=1, column=1, padx=5, pady=5)
    entry_han = tk.Entry(frame_add_word, font=('Arial', 18))
    entry_han.grid(row=1, column=2, padx=5, pady=5)
    label_pinyin = tk.Label(frame_add_word, text="Pinyin:", font=('Arial', 18))
    label_pinyin.grid(row=2, column=1, padx=5, pady=5)
    entry_pinyin = tk.Entry(frame_add_word, font=('Arial', 18))
    entry_pinyin.grid(row=2, column=2, padx=5, pady=5)
    label_znaczenie = tk.Label(frame_add_word, text="Meaning:", font=('Arial', 18))
    label_znaczenie.grid(row=3, column=1, padx=5, pady=5)
    entry_znaczenie = tk.Entry(frame_add_word, font=('Arial', 18))
    entry_znaczenie.grid(row=3, column=2, padx=5, pady=5)
    button_add = tk.Button(frame_add_word, text="Add Word", font=('Arial', 18),  command=add_word_to_database)
    button_add.grid(row=4, column=1, columnspan=2, padx=5, pady=10)
    button_back = tk.Button(frame_add_word, text="Back to menu", font=('Arial', 18), command=back_to_menu)
    button_back.grid(row=5, column=1, columnspan=2, padx=5, pady=5)

    #Learn Frame
    frame_main = tk.Frame(root)

    frame_main.columnconfigure((0, 3), weight=2)
    frame_main.columnconfigure((1, 2), weight=1)
    frame_main.rowconfigure((0), weight=6)
    frame_main.rowconfigure((1,2,3), weight=2)
    frame_main.rowconfigure(( 4,5,6,7), weight=1)

    label_han = tk.Label(frame_main, font=("Helvetica", 36))
    label_han.grid(row=1, column=1,columnspan=2)
    label_pinyin = tk.Label(frame_main, font=("Helvetica", 36))
    label_pinyin.grid(row=2, column=1,columnspan=2)
    label_znaczenie = tk.Label(frame_main, font=("Helvetica", 36))
    label_znaczenie.grid(row=3, column=1,columnspan=2)


    button_meaning = tk.Button(frame_main, text="Meaning", font=('Arial', 18), command=display_meaning)
    button_meaning.grid(row=5, column=1,columnspan=2,pady=20,sticky="ew")
    button_next = tk.Button(frame_main, text="Next",  font=('Arial', 18), command=display_random_word)
    button_next.grid(row=6, column=1,columnspan=2,pady=20,sticky="ew")
 
    button_back = tk.Button(frame_main, text="Back to menu", font=('Arial', 18), command=back_to_menu)
    button_back.grid(row=7, column=1,columnspan=2,pady=20)


    #Words List Frame
    column_names=("word","meaning","pinyin","id")
    frame_word_list=TreeviewEdit(root,columns=column_names)
    frame_word_list.heading('#0',text="Word")
    frame_word_list.heading('word',text="Word")
    frame_word_list.heading('meaning',text="Meaning")
    frame_word_list.heading("pinyin",text="Pinyin")
    frame_word_list.heading('id',text="ID")
    # Hide default column '#0'
    frame_word_list.column("id", width=0, stretch=False)
    frame_word_list.column("#0", width=0, stretch=False)
    frame_word_list.column("word", anchor=tk.CENTER)    
    frame_word_list.column("meaning", anchor=tk.CENTER)  
    frame_word_list.column("pinyin", anchor=tk.CENTER) 

    frame_word_list_menu=tk.Frame(root)
    frame_word_list_menu = tk.Frame(root)
    frame_word_list_menu.columnconfigure(0,weight=1)
    frame_word_list_menu.columnconfigure(1,weight=1)
    frame_word_list_menu.rowconfigure(0,weight=1)
    frame_word_list_menu.rowconfigure(1,weight=1)
    frame_word_list_menu.rowconfigure(2,weight=1)
    frame_word_list_menu.rowconfigure(3,weight=1)
    

    button_register = tk.Button(frame_word_list_menu, text="Back to menu",font=('Arial', 18), command=back_to_menu)
    button_register.grid(row=3, column=0, columnspan=2, padx=5, pady=10)
    frame_login.pack(padx=10, pady=10)
    style = ttk.Style()
    style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold')) 

    #Mainloop start
    root.mainloop()
