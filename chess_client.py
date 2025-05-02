#!/usr/bin/env python3
"""Script for Tkinter GUI chat client."""

from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter
from tkinter.constants import TOP, LEFT


def receive():
    """Handles receiving of messages."""
    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            msg_list.insert(tkinter.END, msg)
        except OSError:  # Possibly client has left the chat.
            break


def send(commend="", event=""):  # event is passed by binders.
    """Handles sending of messages."""
    #print("txt:", commend)
    if commend == "":
        commend = my_msg.get()
        my_msg.set("")  # Clears input field.
        client_socket.send(bytes(commend, "utf8"))
    else:
        client_socket.send(bytes(commend, "utf8"))

    if commend == "{quit}":
        client_socket.close()
        top.quit()



def on_closing():
    """This function is to be called when the window is closed."""
    my_msg.set("{quit}")
    send()

top = tkinter.Tk()
top.title("Chatter")

messages_frame = tkinter.Frame(top)
my_msg = tkinter.StringVar()  # For the messages to be sent.
my_msg.set("Type your messages here.")
scrollbar = tkinter.Scrollbar(messages_frame)  # To navigate through past messages.
# Following will contain the messages.
msg_list = tkinter.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
messages_frame.pack()

entry_field = tkinter.Entry(top, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.pack(expand=True,fill=tkinter.X,side=TOP)

send_button = tkinter.Button(top, text="send", command=lambda: send())
send_button.pack(side=LEFT,expand=True,fill=tkinter.X)

rand_button = tkinter.Button(top, text="rand", command=lambda: send("{rand}"))
rand_button.pack(side=LEFT,expand=True,fill=tkinter.X)

time_button = tkinter.Button(top, text="time", command=lambda: send("{time}"))
time_button.pack(side=LEFT,expand=True,fill=tkinter.X)

name_button = tkinter.Button(top, text="name", command=lambda: send("{name}"))
name_button.pack(side=LEFT,expand=True,fill=tkinter.X)

quit_button = tkinter.Button(top, text="quit", command=lambda: send("{quit}"))
quit_button.pack(side=LEFT,expand=True,fill=tkinter.X)

top.protocol("WM_DELETE_WINDOW", on_closing)

#----Now comes the sockets part----
HOST = '127.0.0.1'
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)

receive_thread = Thread(target=receive)
receive_thread.start()
tkinter.mainloop()  # Starts GUI execution.