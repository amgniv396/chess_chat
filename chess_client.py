#!/usr/bin/env python3
"""Script for Tkinter GUI chat client."""
import tkinter
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

import chess_graphics


def receive():
    """Handles receiving of messages."""
    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            msg_list.insert(tkinter.END, msg)
        except OSError:  # Possibly client has left the chat.
            break


def send(commend="", event=""):  # event is passed by binders.
    #TODO:commend is for moves or quit
    """Handles sending of messages."""
    print("txt:", commend)
    if commend == "":
        commend = my_msg.get()#TODO: change this to intake form chat
        my_msg.set("")  # Clears input field.
        client_socket.send(bytes(commend, "utf8"))
    else:
        client_socket.send(bytes(commend, "utf8"))

    if commend == "{quit}":
        client_socket.close()
        top.quit()



def on_closing():
    #TODO:use send function like a normal human
    """This function is to be called when the window is closed."""
    my_msg.set("{quit}")
    send()

#----Now comes the sockets part----
HOST = '127.0.0.1'
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)

'''g = chess_graphics.start_game()

my_msg = '''

receive_thread = Thread(target=receive)
receive_thread.start()
tkinter.mainloop()  # Starts GUI execution.