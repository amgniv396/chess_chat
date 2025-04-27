import tkinter as tk
import chess_graphics as chess

def show_home_screen(window):
    # Clear window
    for widget in window.winfo_children():
        widget.destroy()

    # Home screen frame
    bg_frame = tk.Frame(window, bg="black")
    bg_frame.pack(fill="both", expand=True)

    # Title
    title_label = tk.Label(bg_frame, text="Chess Master", font=("Arial", 40), fg="white", bg="black")
    title_label.pack(pady=50)

    # Start Game Button
    start_button = tk.Button(bg_frame, text="Start Game", font=("Arial", 20),
                             command=lambda: chess.start_game(window, show_home_screen))
    start_button.pack(pady=20)

    # Exit Button
    exit_button = tk.Button(bg_frame, text="Exit Game", font=("Arial", 20), command=window.quit)
    exit_button.pack(pady=20)
