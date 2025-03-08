import tkinter as tk
import ttkbootstrap as tb
from PIL import Image, ImageTk
from ttkbootstrap.constants import *
import math


def exit_game():
    window.quit()


def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """Draw a rounded rectangle on the canvas"""
    points = [
        x1 + radius, y1,  # Top side
        x2 - radius, y1,
        x2, y1,  # Top right corner
        x2, y1 + radius,
        x2, y2 - radius,  # Right side
        x2, y2,
        x2 - radius, y2,  # Bottom right corner
        x1 + radius, y2,  # Bottom side
        x1, y2,  # Bottom left corner
        x1, y2 - radius,
        x1, y1 + radius,  # Left side
        x1, y1
    ]

    rect_id = canvas.create_polygon(points, **kwargs, smooth=True)
    return rect_id


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
    if not hasattr(canvas, 'images'):
        canvas.images = []
    canvas.images.append(tk_image)

    # Add image to the center of the hexagon
    image_id = canvas.create_image(x, y, image=tk_image)

    # Event handlers for hover effect
    lighter_color = "#333333"  # Lighter version of the default color

    def on_enter(event):
        canvas.itemconfig(hexagon, fill=lighter_color)

    def on_leave(event):
        canvas.itemconfig(hexagon, fill=color)

    # Bind events
    canvas.tag_bind(hexagon, "<Enter>", on_enter)
    canvas.tag_bind(hexagon, "<Leave>", on_leave)
    canvas.tag_bind(image_id, "<Enter>", on_enter)
    canvas.tag_bind(image_id, "<Leave>", on_leave)

    # Bind click event
    def on_click(event):
        command(image_path.split('/')[-1].split('.')[0])  # Pass piece name to command

    canvas.tag_bind(hexagon, "<Button-1>", on_click)
    canvas.tag_bind(image_id, "<Button-1>", on_click)

    return hexagon, image_id, {"x": x, "y": y}  # Return position for reference


def create_hexagon_grid(canvas, center_x, center_y, hex_size):
    # Dictionary to store all hex positions and references
    hexagons = {}

    # Calculate positioning constants
    horizontal_distance = hex_size * math.sqrt(3)  # Distance between centers horizontally
    vertical_distance = hex_size  # Distance between centers vertically

    # Piece configuration - piece name and relative position from center
    pieces_config = [
        {"piece": "black knight", "position": (1, 0), "color": "#222222"},  # Center
        {"piece": "black king", "position": (0.5, 1.5), "color": "#222222"},  # Right
        {"piece": "black queen", "position": (1, 3), "color": "#222222"},  # Top-right
        {"piece": "black bishop", "position": (0.5, -1.5), "color": "#222222"},  # Top-left
        {"piece": "black rook", "position": (0, 3), "color": "#222222"},  # Left
        {"piece": "black pawn", "position": (2, 0), "color": "#222222"}  # Bottom
    ]

    def handle_piece_click(piece_name):
        print(f"{piece_name} was clicked!")
        # You could implement piece selection logic here

    # Create each hexagon at its relative position
    for config in pieces_config:
        # Calculate absolute position based on relative position
        rel_x, rel_y = config["position"]
        abs_x = center_x + rel_x * horizontal_distance
        abs_y = center_y + rel_y * vertical_distance

        # Create the hexagon with the specified piece
        image_path = f"assets/pieces/{config['piece']}.png"
        hex_obj, img_id, pos = create_hexagon_image_button(
            canvas,
            abs_x,
            abs_y,
            hex_size,
            image_path,
            handle_piece_click,
            config["color"]
        )

        # Store the hexagon reference
        hexagons[config["piece"]] = {
            "hex_id": hex_obj,
            "img_id": img_id,
            "position": pos
        }

    return hexagons


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

# Calculate positions for a single rounded rectangle containing both logo and buttons
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
center_x = screen_width / 2
center_y = screen_height * 0.46  # Centered between logo and buttons

# Size of the rectangle to contain both logo and buttons
rect_width = 320
rect_height = 525

# Draw a single rounded rectangle behind both logo and buttons
main_rect = create_rounded_rectangle(
    canvas,
    center_x - rect_width / 2,
    center_y - rect_height / 2,
    center_x + rect_width / 2,
    center_y + rect_height / 2,
    radius=40,
    fill="#111111",
    outline="#333333",
    width=2
)

# Place logo on top of the rounded rectangle
logo_label = tk.Label(window, image=logo_image, bg="#111111")
logo_label.place(relx=0.5, rely=0.3, anchor=tk.CENTER)

title_label = tb.Label(window, text="Chess Master", font=("Arial", 30), background="#111111", foreground="#ffffff")
title_label.place(relx=0.5, rely=0.47, anchor=tk.CENTER)  # Position it between the logo and buttons


# Create buttons on top of the rounded rectangle
start_button = tb.Button(window, text="Start Game", command=lambda: print("Game Starting..."), bootstyle="success",
                         padding=15, width=15)
start_button.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

exit_button = tb.Button(window, text="Exit Game", command=exit_game, bootstyle="danger", padding=15, width=15)
exit_button.place(relx=0.5, rely=0.7, anchor=tk.CENTER)

# Create the hexagonal grid with all chess pieces
hex_x = window.winfo_screenwidth() * 0.15  # 15% position horizontally
hex_y = window.winfo_screenheight() * 0.45  # Middle of the screen vertically
hex_grid = create_hexagon_grid(canvas, hex_x, hex_y, 60)

# Start the main loop
window.mainloop()