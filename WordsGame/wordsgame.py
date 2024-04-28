import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import ctypes
import psycopg2
from time import sleep
import threading




# Connection to Postgres DB
credentials = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "password"
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
        
        #Który item klikamy
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
        print(current_values)
        update_db(current_values)
        self.item(selected_iid,values=current_values)


        event.widget.destroy()

    def on_delete(self,event):
         #Który item klikamy
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
        print(query)
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
    frame_word_list.pack()
    frame_word_list_menu.pack()  
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


#Refresh table with words list
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
        print(f"{word},{meaning},{pinyin}")
        frame_word_list.insert(parent="",
                        index=tk.END,
                        values=(f"{word}",f"{meaning}",f"{pinyin}",f"{id}"))

    




def start_learning():
    global words
    global current_word_index
    words = get_user_words(conn, username)
    current_word_index = 0
    frame_menu.pack_forget()
    frame_main.pack()
    display_random_word()

#Add word button
def show_add_word_screen():
    frame_menu.pack_forget()
    frame_add_word.pack()

def add_word_to_database():
    han = entry_han.get()
    if han == '':
         messagebox.showerror("Błąd", "Muszisz dodać słowo")
         return 
    pinyin = entry_pinyin.get()
    znaczenie = entry_znaczenie.get()
    add_word(conn, username, han, znaczenie, pinyin)
    messagebox.showinfo("Sukces", "Słowo zostało dodane!")
    frame_add_word.pack_forget()
    frame_menu.pack()

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
    frame_menu.pack()


def handle_login():
    global username
    username = entry_username.get()
    password = entry_password.get()
    user = login(conn, username, password)
    if user:
        frame_login.pack_forget()
        frame_menu.pack()
    else:
        messagebox.showerror("Login Error", "Wrong login credentials")


def handle_registration():
    username = entry_username.get()
    password = entry_password.get()
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
        frame_menu.pack()

# Function to display pinyin after delay
def show_pinyin_after_delay(pinyin):
    label_pinyin.config(text=pinyin)


def update_width(event):
    global window_width
    window_width = event.width
    root.after(100, update_elements)


def update_elements():
    entry_username.config(width=int(window_width/8))
    entry_password.config(width=int(window_width/8))



conn = connect_to_database(credentials)




if __name__=="__main__":

    root = tk.Tk()
    root.title("Flashcards APP")
    s=ttk.Style(root)
    s.theme_use("clam")
    window_width = 600
    window_height = 600
    set_window_position(root, window_width, window_height)



    #Login screen frame
    frame_login = tk.Frame(root)
    frame_login.columnconfigure(0,weight=1)
    frame_login.columnconfigure(1,weight=1)
    frame_login.rowconfigure(0,weight=1)
    frame_login.rowconfigure(1,weight=1)
    frame_login.rowconfigure(2,weight=1)
    frame_login.rowconfigure(3,weight=1)
    
    label_username = tk.Label(frame_login, text="User:")
    label_username.grid(row=0, column=0)
    entry_username = tk.Entry(frame_login,width=int(window_width/8),)
    entry_username.grid(row=0, column=1)
    label_password = tk.Label(frame_login, text="Password:")
    label_password.grid(row=1, column=0, padx=5, pady=20)
    entry_password = tk.Entry(frame_login, show="*", width=int(window_width/8),)
    entry_password.grid(row=1, column=1, padx=10, pady=20)
    button_login = tk.Button(frame_login, text="Login", width=int(window_width/8), command=handle_login)
    button_login.grid(row=2, column=0, columnspan=2, padx=5, pady=10)
    button_register = tk.Button(frame_login, text="Register", width=int(window_width/8), command=handle_registration)
    button_register.grid(row=3, column=0, columnspan=2, padx=5, pady=10)
    frame_login.pack(padx=10, pady=10)




    #Added window resizing event
    root.bind("<Configure>", update_width)


    #Main Manu Frame
    frame_menu = tk.Frame(root)
    button_learn = tk.Button(frame_menu, text="Learn", width=int(window_width/16), command=start_learning)
    button_learn.pack(pady=10)
    button_add_words = tk.Button(frame_menu, text="Add words", width=int(window_width/16), command=show_add_word_screen)
    button_add_words.pack(pady=10)
    button_word_list = tk.Button(frame_menu, text="Word list", width=int(window_width/16), command=show_word_list_screen)
    button_word_list.pack(pady=10)

    #Add words Frame
    frame_add_word = tk.Frame(root)
    label_han = tk.Label(frame_add_word, text="Word:", width=int(window_width/16))
    label_han.grid(row=0, column=0, padx=5, pady=5)
    entry_han = tk.Entry(frame_add_word, width=int(window_width/16))
    entry_han.grid(row=0, column=1, padx=5, pady=5)
    label_pinyin = tk.Label(frame_add_word, text="Pinyin:", width=int(window_width/16))
    label_pinyin.grid(row=1, column=0, padx=5, pady=5)
    entry_pinyin = tk.Entry(frame_add_word, width=int(window_width/16))
    entry_pinyin.grid(row=1, column=1, padx=5, pady=5)
    label_znaczenie = tk.Label(frame_add_word, text="Meaning:", width=int(window_width/16))
    label_znaczenie.grid(row=2, column=0, padx=5, pady=5)
    entry_znaczenie = tk.Entry(frame_add_word, width=int(window_width/16))
    entry_znaczenie.grid(row=2, column=1, padx=5, pady=5)
    button_add = tk.Button(frame_add_word, text="Add Word", width=int(window_width/16), command=add_word_to_database)
    button_add.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
    button_back = tk.Button(frame_add_word, text="Back to menu", width=int(window_width/16), command=back_to_menu)
    button_back.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

    #Learn Frame
    frame_main = tk.Frame(root)
    label_han = tk.Label(frame_main, font=("Helvetica", 24))
    label_han.pack(pady=20)
    label_pinyin = tk.Label(frame_main, font=("Helvetica", 16))
    label_pinyin.pack(pady=10)
    label_znaczenie = tk.Label(frame_main, font=("Helvetica", 16))
    label_znaczenie.pack(pady=10)

    frame_buttons = tk.Frame(frame_main)
    button_meaning = tk.Button(frame_buttons, text="Meaning", width=int(window_width/16), command=display_meaning)
    button_meaning.pack(side=tk.LEFT, padx=10)
    button_next = tk.Button(frame_buttons, text="Next", width=int(window_width/16), command=display_random_word)
    button_next.pack(side=tk.LEFT, padx=10)
    frame_buttons.pack()

    button_back = tk.Button(frame_main, text="Back to menu", width=30, command=back_to_menu)
    button_back.pack(pady=20)







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

    frame_word_list_menu=tk.Frame(root)
    frame_word_list_menu = tk.Frame(root)
    frame_word_list_menu.columnconfigure(0,weight=1)
    frame_word_list_menu.columnconfigure(1,weight=1)
    frame_word_list_menu.rowconfigure(0,weight=1)
    frame_word_list_menu.rowconfigure(1,weight=1)
    frame_word_list_menu.rowconfigure(2,weight=1)
    frame_word_list_menu.rowconfigure(3,weight=1)
    

    button_register = tk.Button(frame_word_list_menu, text="Back to menu", width=30, command=back_to_menu)
    button_register.grid(row=3, column=1, columnspan=1, padx=5, pady=10)
    frame_login.pack(padx=10, pady=10)


    #Mainloop start
    root.mainloop()
