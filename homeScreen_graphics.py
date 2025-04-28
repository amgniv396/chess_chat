import tkinter as tk
import ttkbootstrap as tb
from PIL import Image, ImageTk
import math
import chess_graphics

# Initialize main window
window = tk.Tk()
window.title("Chess App")
window.attributes('-fullscreen', True)

# Configure ttkbootstrap style
tb.Style().configure("TButton", font=("Microsoft Yahei UI", 14))

# ----------------- Utility functions -----------------

def exit_game():
    window.quit()

def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """Draw a rounded rectangle on the canvas"""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)

def create_hexagon_image_button(canvas, x, y, size, image_path, command, color="#3498db"):
    """Create one hexagon button with an image inside."""
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.pi / 180 * angle_deg
        points.append(x + size * math.cos(angle_rad))
        points.append(y + size * math.sin(angle_rad))

    hexagon = canvas.create_polygon(points, outline="black", fill=color, width=2)

    # Load and resize the image
    image_size = int(size * 1.2)
    pil_image = Image.open(image_path).resize((image_size, image_size))
    tk_image = ImageTk.PhotoImage(pil_image)

    if not hasattr(canvas, 'images'):
        canvas.images = []
    canvas.images.append(tk_image)

    image_id = canvas.create_image(x, y, image=tk_image)

    # Hover effect
    lighter_color = "#333333"

    def on_enter(event):
        canvas.itemconfig(hexagon, fill=lighter_color)

    def on_leave(event):
        canvas.itemconfig(hexagon, fill=color)

    canvas.tag_bind(hexagon, "<Enter>", on_enter)
    canvas.tag_bind(hexagon, "<Leave>", on_leave)
    canvas.tag_bind(image_id, "<Enter>", on_enter)
    canvas.tag_bind(image_id, "<Leave>", on_leave)

    # Click event
    def on_click(event):
        command(image_path.split('/')[-1].split('.')[0])

    canvas.tag_bind(hexagon, "<Button-1>", on_click)
    canvas.tag_bind(image_id, "<Button-1>", on_click)

    return hexagon, image_id, {"x": x, "y": y}

def create_hexagon_grid(canvas, center_x, center_y, hex_size):
    """Create a group of hexagons for the home screen."""
    pieces_config = [
        {"piece": "black knight", "position": (1, 0), "color": "#222222"},
        {"piece": "black king", "position": (0.5, 1.5), "color": "#222222"},
        {"piece": "black queen", "position": (1, 3), "color": "#222222"},
        {"piece": "black bishop", "position": (0.5, -1.5), "color": "#222222"},
        {"piece": "black rook", "position": (0, 3), "color": "#222222"},
        {"piece": "black pawn", "position": (2, 0), "color": "#222222"}
    ]

    def handle_piece_click(piece_name):
        print(f"{piece_name} was clicked!")

    hexagons = {}

    horizontal_distance = hex_size * math.sqrt(3)
    vertical_distance = hex_size

    for config in pieces_config:
        rel_x, rel_y = config["position"]
        abs_x = center_x + rel_x * horizontal_distance
        abs_y = center_y + rel_y * vertical_distance

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
        hexagons[config["piece"]] = {"hex_id": hex_obj, "img_id": img_id, "position": pos}

    return hexagons

# ----------------- Home Screen functions -----------------

def create_home_screen():
    global bg_frame, canvas, bg_image, logo_image, logo_label, title_label
    global start_button, exit_button, settings_image, settings_button

    # Create background frame and canvas
    bg_frame = tk.Frame(window)
    bg_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(bg_frame, width=500, height=500)
    canvas.pack(fill="both", expand=True)

    # Load images
    bg_image = ImageTk.PhotoImage(
        Image.open("assets/utils/chessBackground.jpg").resize(
            (window.winfo_screenwidth(), window.winfo_screenheight()))
    )
    logo_image = ImageTk.PhotoImage(Image.open("assets/utils/chessLogo.png").resize((200, 200)))

    canvas.create_image(0, 0, image=bg_image, anchor=tk.NW)

    # Rounded rectangle background
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    center_x = screen_width / 2
    center_y = screen_height * 0.46
    rect_width = 320
    rect_height = 525

    create_rounded_rectangle(
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

    # Logo and title
    logo_label = tk.Label(window, image=logo_image, bg="#111111")
    logo_label.place(relx=0.5, rely=0.3, anchor=tk.CENTER)

    title_label = tb.Label(window, text="Chess Master", font=("Arial", 30), background="#111111", foreground="#ffffff")
    title_label.place(relx=0.5, rely=0.47, anchor=tk.CENTER)

    # Start and Exit buttons
    start_button = tb.Button(
        window, text="Start Game",
        command=lambda: chess_graphics.start_game(window, return_to_homescreen),
        bootstyle="success", padding=15, width=15
    )
    start_button.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

    exit_button = tb.Button(
        window, text="Exit Game",
        command=exit_game,
        bootstyle="danger", padding=15, width=15
    )
    exit_button.place(relx=0.5, rely=0.7, anchor=tk.CENTER)

    settings_image = ImageTk.PhotoImage(Image.open("assets/utils/settingsIcon.png").resize((50, 50)))
    settings_button = tb.Button(
        window, image=settings_image,
        command=lambda: print("Settings"),
        bootstyle="secondary"
    )
    settings_button.place(relx=0.955)

    # Hexagon grid
    hex_x = screen_width * 0.15
    hex_y = screen_height * 0.45
    create_hexagon_grid(canvas, hex_x, hex_y, 60)

def return_to_homescreen():
    # Destroy all current widgets
    for widget in window.winfo_children():
        widget.destroy()

    # Recreate home screen
    create_home_screen()

# ----------------- Start app -----------------

create_home_screen()

window.mainloop()
