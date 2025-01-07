import tkinter as tk
from ttkbootstrap import Style

# Create main window with ttkbootstrap style
root = tk.Tk()
style = Style(theme="flatly")  # Choose your preferred theme

root.title("chess-chat")

# Function to create the chessboard
def create_chessboard():
    board = tk.Frame(root)
    board.grid(row=0, column=0, sticky="nsew")

    # RGB values for white and black squares
    white_rgb = "#FFFFFF"  # White square (RGB: 255, 255, 255)
    black_rgb = "#333333"  # Black square (RGB: 51, 51, 51)

    # Make the rows and columns of the board expandable when resizing
    for i in range(8):
        board.grid_columnconfigure(i, weight=1)
        board.grid_rowconfigure(i, weight=1)

    # Create the chessboard squares
    for row in range(8):
        for col in range(8):
            square = tk.Label(board, width=6, height=3, relief="solid")

            # Set the color of the squares (alternating black and white)
            if (row + col) % 2 == 0:
                square.configure(background=white_rgb)
            else:
                square.configure(background=black_rgb)

            square.grid(row=row, column=col, sticky="nsew")


# Ensure the window expands equally in both x and y directions
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Ensure the window is resizable equally in both directions
root.minsize(300, 300)  # Set a minimum window size to prevent it from becoming too small
root.maxsize(900, 900)  # Set a maximum window size to prevent it from becoming too large

# Call the function to create the chessboard
create_chessboard()

# Run the main loop
root.mainloop()
