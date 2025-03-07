import tkinter as tk
import ttkbootstrap as tb
from PIL import Image, ImageTk
from ttkbootstrap.constants import *
import math


def exit_game():
    window.quit()


def create_hexagon_image_button(canvas, x, y, size, image_path, command, color="#3498db"):
    # Calculate the points for a hexagon
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.pi / 180 * angle_deg
        points.append(x + size * math.cos(angle_rad))
        points.append(y + size * math.sin(angle_rad))

    # Create hexagon shape
    hexagon = canvas.create_polygon(points, outline="black", fill=color, width=2)

    # Load and resize the image to fit inside the hexagon
    image_size = int(size * 1.2)  # Make image slightly smaller than the hexagon
    pil_image = Image.open(image_path).resize((image_size, image_size))
    tk_image = ImageTk.PhotoImage(pil_image)

    # Store the image reference to prevent garbage collection
    canvas.image = tk_image

    # Add image to the center of the hexagon
    image_id = canvas.create_image(x, y, image=tk_image)

    # Bind click event
    def on_click(event):
        command()
        canvas.itemconfig(hexagon, fill="#2980b9")  # Darker color when clicked
        canvas.after(100, lambda: canvas.itemconfig(hexagon, fill=color))  # Return to original color

    canvas.tag_bind(hexagon, "<Button-1>", on_click)
    canvas.tag_bind(image_id, "<Button-1>", on_click)

    return hexagon, image_id, tk_image


# Initialize main window
window = tk.Tk()
window.title("Chess App")
window.attributes('-fullscreen', True)

# Configure style
tb.Style().configure("TButton", font=("Microsoft Yahei UI", 14))

# Create background frame and canvas
bg_frame = tk.Frame(window)
bg_frame.pack(fill="both", expand=True)

canvas = tk.Canvas(bg_frame, width=500, height=500)
canvas.pack(fill="both", expand=True)

# Load images
bg_image = ImageTk.PhotoImage(
    Image.open("assets/utils/chessBackground.jpg").resize((window.winfo_screenwidth(), window.winfo_screenheight())))
logo_image = ImageTk.PhotoImage(Image.open("assets/utils/chessLogo.png").resize((200, 200)))

# Place background image
canvas.create_image(0, 0, image=bg_image, anchor=tk.NW)

# Place logo
logo_label = tk.Label(window, image=logo_image, bg="black")
logo_label.place(relx=0.5, rely=0.3, anchor=tk.CENTER)

# Create buttons
start_button = tb.Button(window, text="Start Game", command=lambda: print("Game Starting..."), bootstyle="success",
                         padding=15)
start_button.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

exit_button = tb.Button(window, text="Exit Game", command=exit_game, bootstyle="danger", padding=15)
exit_button.place(relx=0.5, rely=0.7, anchor=tk.CENTER)

# Create the hexagonal button with knight image
hex_x = window.winfo_screenwidth() * 0.3  # This places it at the 30% position (padx=0.3)
hex_y = window.winfo_screenheight() * 0.5  # Middle of the screen vertically
knight_image_path = "assets/pieces/black knight.png"  # Path fixed with forward slashes
hex_button, hex_image, image_ref = create_hexagon_image_button(
    canvas,
    hex_x,
    hex_y,
    60,  # Size of the hexagon
    knight_image_path,
    lambda: print("Knight button clicked!"),
    "#222222"
)

# Start the main loop
window.mainloop()