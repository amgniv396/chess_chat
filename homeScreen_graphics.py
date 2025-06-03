import tkinter as tk
import ttkbootstrap as tb
from PIL import Image, ImageTk
import math
import chess_client_graphics
from SQLL_database import UserDatabase

player_name = "Player1"  # Default player name
player_rating = 0  # Default rating


def show_profile_overlay():
    global player_name, player_rating

    # Get current rating from database
    db = UserDatabase()
    _, current_rating = db.get_rating(player_name)

    # Update global player_rating if we got a valid rating
    if current_rating and str(current_rating).isdigit():
        player_rating = current_rating
    else:
        player_rating = 0

    # === Create an overlay frame ===
    overlay = tk.Frame(window, bg="", width=window.winfo_screenwidth(), height=window.winfo_screenheight())
    overlay.place(x=0, y=0)

    # Force overlay to the top
    overlay.lift()
    overlay.tkraise()

    # Semi-transparent dark background
    dark_bg = tk.Canvas(overlay, width=window.winfo_screenwidth(), height=window.winfo_screenheight(),
                        bg="#000000", highlightthickness=0)
    dark_bg.pack(fill="both", expand=True)
    dark_bg.create_rectangle(0, 0, window.winfo_screenwidth(), window.winfo_screenheight(),
                             fill="#000000", stipple="gray50", outline="")

    # Center panel
    center_x = window.winfo_screenwidth() // 2
    center_y = window.winfo_screenheight() // 2
    rect_width = 500
    rect_height = 400

    create_rounded_rectangle(
        dark_bg,
        center_x - rect_width / 2,
        center_y - rect_height / 2,
        center_x + rect_width / 2,
        center_y + rect_height / 2,
        radius=30,
        fill="#222222",
        outline="#444444",
        width=2
    )

    # === Profile title ===
    dark_bg.create_text(center_x, center_y - 140, text="Player Profile", font=("Arial", 24, "bold"), fill="white")

    # === Player Name ===
    dark_bg.create_text(center_x - 150, center_y - 88, text="Name:", font=("Arial", 14), fill="white")

    name_entry = tk.Entry(overlay, textvariable=tk.StringVar(value=player_name), font=("Arial", 14), width=15,
                          bg="#333333", fg="white")
    name_entry.place(x=center_x - 100, y=center_y - 100)

    # === Rating Display ===
    dark_bg.create_text(center_x - 150, center_y - 38, text="Rating:", font=("Arial", 14), fill="white")
    rating_label = tk.Label(overlay, text=str(player_rating), font=("Arial", 14), bg="#222222", fg="white")
    rating_label.place(x=center_x - 100, y=center_y - 50)

    # === Texture Options Title ===
    dark_bg.create_text(center_x - 141, center_y + 8, text="Themes:", font=("Arial", 14), fill="white")

    # === Texture Options ===
    textures = ["black bishop", "black king", "black knight"]
    selected_texture = tk.StringVar(value="black king")

    for i, tex in enumerate(textures):
        img = ImageTk.PhotoImage(Image.open(f"assets/pieces/{tex}.png").resize((80, 80)))

        texture_frame = tk.Frame(overlay, bg="#333333", relief="raised", bd=2)
        texture_frame.place(x=center_x - 151 + i * 110, y=center_y + 35, width=90, height=90)

        label = tk.Label(texture_frame, image=img, bg="#333333")
        label.image = img
        label.pack()

        def select_texture(t=tex):
            selected_texture.set(t)

        label.bind("<Button-1>", lambda e, t=tex: select_texture(t))

    # === Close Button ===
    close_btn = tk.Button(overlay, text="✕", command=overlay.destroy, font=("Arial", 14, "bold"),
                          bg="#ff4444", fg="white", width=3, height=1)
    close_btn.place(x=center_x + rect_width / 2 - 40, y=center_y - rect_height / 2 + 10)

    # === Save Button ===
    def save_profile():
        global player_name, player_rating
        new_name = name_entry.get()

        # Import the database class
        from SQLL_database import UserDatabase
        db = UserDatabase()

        # Update username in database
        success, message = db.update_username(player_name, new_name)

        if success:
            # Update the global player_name variable
            player_name = new_name

            # Get updated rating after name change
            _, updated_rating = db.get_rating(player_name)
            if updated_rating and str(updated_rating).isdigit():
                player_rating = updated_rating

            print(f"Name updated to: {new_name}")
            print(f"Rating: {player_rating}")
            print(f"Selected texture: {selected_texture.get()}")

            # Show success message
            import tkinter.messagebox as messagebox
            messagebox.showinfo("Success", "Profile updated successfully!")
            overlay.destroy()
        else:
            # Show error message
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", message)

    save_btn = tk.Button(overlay, text="Save", command=save_profile, font=("Arial", 12, "bold"),
                         bg="#00aa44", fg="white", width=8, height=1)
    save_btn.place(x=center_x - 40, y=center_y + 140)


# ----------------- Game mode functions -----------------

def start_game():
    chess_client_graphics.start_game(window, player_name, return_to_homescreen)


def play_with_stockfish():
    # Placeholder function for Stockfish gameplay
    print("Play with Stockfish clicked - functionality to be implemented")
    pass


def play_with_bot():
    # Placeholder function for bot gameplay
    print("Play with Bot clicked - functionality to be implemented")
    pass


def exit_game():
    chess_client_graphics.stop_client()
    window.quit()


# ----------------- Utility functions -----------------

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
    global start_button, stockfish_button, bot_button, exit_button, profile_image, profile_button

    width = window.winfo_screenwidth()
    height = window.winfo_screenheight()

    # Create background frame and canvas
    bg_frame = tk.Frame(window)
    bg_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(bg_frame, width=500, height=500)
    canvas.pack(fill="both", expand=True)

    # Load images
    bg_image = ImageTk.PhotoImage(
        Image.open("assets/utils/chessBackground.jpg").resize(
            (width, height))
    )
    logo_image = ImageTk.PhotoImage(
        Image.open("assets/utils/chessLogo.png").resize((int(width // 7.7), int(width // 7.7))))

    canvas.create_image(0, 0, image=bg_image, anchor=tk.NW)

    # Rounded rectangle background (adjusted height for additional buttons)
    center_x = width / 2
    center_y = height * 0.5
    rect_width = 320
    rect_height = 625  # Increased height to accommodate new buttons

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

    # Start Game button (multiplayer)
    start_button = tb.Button(
        window, text="Multiplayer",
        command=start_game,
        bootstyle="success", padding=15, width=15
    )
    start_button.place(relx=0.5, rely=0.56, anchor=tk.CENTER)

    # Play with Stockfish button
    stockfish_button = tb.Button(
        window, text="Play vs Stockfish",
        command=play_with_stockfish,
        bootstyle="info", padding=15, width=15
    )
    stockfish_button.place(relx=0.5, rely=0.64, anchor=tk.CENTER)

    # Play with Bot button
    bot_button = tb.Button(
        window, text="Play vs Bot",
        command=play_with_bot,
        bootstyle="info", padding=15, width=15
    )
    bot_button.place(relx=0.5, rely=0.72, anchor=tk.CENTER)

    # Exit Game button
    exit_button = tb.Button(
        window, text="Exit Game",
        command=exit_game,
        bootstyle="danger", padding=15, width=15
    )
    exit_button.place(relx=0.5, rely=0.8, anchor=tk.CENTER)

    # Profile button (changed from settings)
    try:
        profile_image = ImageTk.PhotoImage(Image.open("assets/utils/profileIcon.png").resize((50, 50)))
    except:
        # Fallback if profile icon doesn't exist, use settings icon
        profile_image = ImageTk.PhotoImage(Image.open("assets/utils/settingsIcon.png").resize((50, 50)))

    profile_button = tb.Button(
        window, image=profile_image,
        command=lambda: show_profile_overlay(),
        bootstyle="secondary"
    )
    profile_button.place(relx=0.955)

    # Hexagon grid
    hex_x = width * 0.15
    hex_y = height * 0.45
    create_hexagon_grid(canvas, hex_x, hex_y, 60)


def return_to_homescreen():
    global player_name, player_rating
    db = UserDatabase()
    _, current_rating = db.get_rating(player_name)

    # Update player_rating with current value from database
    if current_rating and str(current_rating).isdigit():
        player_rating = current_rating
    else:
        player_rating = 0

    chess_client_graphics.send_message("{quit_game}")
    # Destroy all current widgets
    for widget in window.winfo_children():
        widget.destroy()

    # Recreate home screen
    create_home_screen()


# ----------------- Start app -----------------

def run_home_screen(parent_window=None, username="Player1"):
    """Run the home screen from an external module.
    If parent_window is provided, it will be used instead of creating a new window.
    If username is provided, it will update the player_name."""
    global window, player_name, player_rating

    # Update the player name with the provided username
    player_name = username
    db = UserDatabase()
    _, current_rating = db.get_rating(player_name)

    # Update player_rating with proper type checking
    if current_rating and str(current_rating).isdigit():
        player_rating = current_rating
    else:
        player_rating = 0

    if parent_window:
        # Use the existing window from sign_in_page.py
        window = parent_window

        # Clear all widgets from the window
        for widget in window.winfo_children():
            widget.destroy()

        # Configure window properties
        window.title("Chess App")

    else:
        '''# Create a new window if none is provided (when running directly)
        window = tk.Tk()
        window.title("Chess App")
        window.attributes('-fullscreen', True)
        tb.Style().configure("TButton", font=("Microsoft Yahei UI", 14))'''
        # TODO: check if needed
        pass

    tb.Style().configure("TButton", font=("Microsoft Yahei UI", 14))
    # Create the home screen UI
    create_home_screen()
    print((window.winfo_screenwidth(), window.winfo_screenheight()))
    # Only start mainloop if we're running this module directly
    if not parent_window:
        window.mainloop()


# Only run the app directly if this script is executed directly
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Chess App1")
    window.attributes('-fullscreen', True)
    tb.Style().configure("TButton", font=("Microsoft Yahei UI", 14))
    # Window is already created at the top of the file
    create_home_screen()
    print((window.winfo_screenwidth(), window.winfo_screenheight()))
    window.mainloop()