import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageOps, ImageDraw
import math


def piece_king():
    pass


def piece_queen():
    pass


def piece_rook():
    pass


def piece_bishop():
    pass


def piece_knight():
    pass


def piece_pawn():
    pass


def start_game():
    print("Game starting...")


def open_settings():
    print("Opening settings...")


class HexagonButton(ttk.Frame):
    def __init__(self, parent, image_path=None, command=None, size=80, filled=False, **kwargs):
        super().__init__(parent, **kwargs)

        self.size = size
        self.filled = filled

        # Canvas to draw the hexagon
        self.canvas = ttk.Canvas(self, width=size, height=size, highlightthickness=0)
        self.canvas.pack()

        # Draw hexagon with background
        self.draw_hexagon(image_path)

        # Add click event
        self.canvas.bind("<Button-1>", lambda e: command() if command else None)

        # Add hover effect
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)

    def draw_hexagon(self, image_path=None):
        """Draw a hexagon with background and optional image"""
        size = self.size

        # Calculate hexagon coordinates - pointy-top orientation
        w, h = size, size
        radius = min(w, h) / 2
        center_x, center_y = w / 2, h / 2

        # Calculate the six points of the hexagon
        hexagon = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.pi / 180 * angle_deg
            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)
            hexagon.append((x, y))

        # Choose background color based on filled status
        bg_color = 'red' if self.filled else "#DDDDDD"

        # Draw hexagon background
        self.hex_id = self.canvas.create_polygon(
            hexagon,
            fill=bg_color,
            outline="#222222",
            width=2
        )

        # Add image if provided
        if image_path:
            # Create hexagonal mask for the image
            img = Image.open(image_path).resize((size, size))
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            #TODO a fill will be cool
            draw.polygon(hexagon, fill=255)

            # Apply mask to image
            result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            result.paste(img, (0, 0), mask)

            # Store as instance variable to prevent garbage collection
            self.hex_image = ImageTk.PhotoImage(result)

            # Draw the image on top of background
            self.image_id = self.canvas.create_image(size / 2, size / 2, image=self.hex_image)

    def on_enter(self, event):
        """Hover effect - highlight"""
        if self.filled:
            self.canvas.itemconfig(self.hex_id, fill="#444444")
        else:
            self.canvas.itemconfig(self.hex_id, fill="#EEEEEE")

    def on_leave(self, event):
        """Remove highlight"""
        if self.filled:
            self.canvas.itemconfig(self.hex_id, fill='red')
        else:
            self.canvas.itemconfig(self.hex_id, fill="#DDDDDD")


def create_chess_app():
    window = ttk.Window(themename="darkly")
    window.title("Chess App")
    window.attributes('-fullscreen', True)

    main_frame = ttk.Frame(window)
    main_frame.pack(fill=BOTH, expand=True)

    bg_image = Image.open("assets/utils/chessBackground.jpg")
    bg_image = bg_image.resize((window.winfo_screenwidth(), window.winfo_screenheight()))
    bg_photo = ImageTk.PhotoImage(bg_image)

    bg_label = ttk.Label(main_frame, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)

    # Create honeycomb layout for pieces on the left side
    honeycomb_frame = ttk.Frame(main_frame)
    honeycomb_frame.place(relx=0.2, rely=0.5, anchor=CENTER)

    pieces = [
        ("black king", piece_king),
        ("black queen", piece_queen),
        ("black rook", piece_rook),
        ("black bishop", piece_bishop),
        ("black knight", piece_knight),
        ("black pawn", piece_pawn)
    ]

    # Hexagon dimensions
    hex_size = 150  # Increased size for better visibility

    # For perfect tangency:
    # Horizontal distance between centers of adjacent hexagons in same row
    hex_horizontal_distance = hex_size * 0.866  # sqrt(3)/2 * width

    # Vertical distance between centers of adjacent rows
    hex_vertical_distance = hex_size * 0.75

    # Define positions in (col, row) format
    # These coordinates are scaled by hex_horizontal_distance and hex_vertical_distance
    hex_coords = [
        (1, 0),  # Top center
        (0, 1),  # Middle left
        (1, 2),  # Middle right
        (2, 2),  # Middle center
        (0, 3),  # Bottom left
        (2, 0)  # Bottom right
    ]

    # Store references to the hexagon buttons
    hex_buttons = []

    # Create exactly 6 hexagons in a tangent pattern
    for i, (col, row) in enumerate(hex_coords):
        # Calculate position for tangent hexagons
        x = col * hex_horizontal_distance
        y = row * hex_vertical_distance

        # Offset odd rows for tangent hexagons
        if row % 2 == 1:
            x += hex_horizontal_distance / 2

        # Create frame for precise positioning
        pos_frame = ttk.Frame(honeycomb_frame)
        pos_frame.place(x=x, y=y)


        # Create the hexagon button
        hex_button = HexagonButton(
            pos_frame,
            image_path=f"assets/pieces/{pieces[i][0]}.png",
            command=pieces[i][1],
            size=hex_size,
            filled=True
        )
        hex_button.pack()
        hex_buttons.append(hex_button)

    # Ensure the honeycomb frame is sized appropriately
    honeycomb_frame.update()
    honeycomb_width = 4 * hex_horizontal_distance
    honeycomb_height = 4 * hex_vertical_distance
    honeycomb_frame.config(width=honeycomb_width, height=honeycomb_height)

    # Main content in center of screen
    content_frame = ttk.Frame(main_frame)
    content_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

    logo = Image.open("assets/utils/chessLogo.png").resize((200, 200))
    logo_with_border = ImageOps.expand(logo, border=10, fill=(12, 12, 12))
    logo_img = ImageTk.PhotoImage(logo_with_border)

    logo_label = ttk.Label(content_frame, image=logo_img)
    logo_label.pack(pady=20)

    title_label = ttk.Label(content_frame, text="CHESS MASTER", font=("Helvetica", 32, "bold"), style='primary')
    title_label.pack()

    subtitle_label = ttk.Label(content_frame, text="Challenge your mind, master the game", font=("Helvetica", 14),
                               style='secondary')
    subtitle_label.pack(pady=5)

    button_frame = ttk.Frame(content_frame)
    button_frame.pack(pady=30)

    play_button = ttk.Button(button_frame, text="Start New Game", command=start_game, style='primary.Outline.TButton',
                             width=15, padding=20)
    play_button.pack(pady=15)

    quit_button = ttk.Button(button_frame, text="Exit Game", command=window.quit, style='danger.Outline.TButton',
                             width=15, padding=20)
    quit_button.pack(pady=15)

    # Store references to prevent garbage collection
    window.logo_img = logo_img
    window.bg_photo = bg_photo
    window.hex_buttons = hex_buttons

    return window


if __name__ == "__main__":
    app = create_chess_app()
    app.mainloop()
