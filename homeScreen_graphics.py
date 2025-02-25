import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageOps


def start_game():
    print("Game starting...")  # Replace with actual game logic


def open_settings():
    print("Opening settings...")  # Replace with settings window logic


def create_chess_app():
    window = ttk.Window(themename="darkly")
    window.title("Chess App")
    window.attributes('-fullscreen', True)

    # Create main container
    main_frame = ttk.Frame(window)
    main_frame.pack(fill=BOTH, expand=True)

    # Load background image
    bg_image = Image.open("assets\\utils\\chessBackground.jpg")
    bg_image = bg_image.resize((window.winfo_screenwidth(), window.winfo_screenheight()))
    bg_photo = ImageTk.PhotoImage(bg_image)

    # Create a label to hold the background image and place it inside the main frame
    bg_label = ttk.Label(main_frame, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)  # Fill the entire frame

    # Create a decorative header
    header_frame = ttk.Frame(main_frame, style='primary')
    header_frame.pack(fill=X, pady=(0, 20))

    # Settings button in top right
    settings_frame = ttk.Frame(header_frame)
    settings_frame.pack(side=RIGHT, padx=20)

    # Load gear icon
    gear_icon = Image.open("assets/pieces/white rook.png")
    gear_icon = gear_icon.resize((30, 30))
    gear_photo = ImageTk.PhotoImage(gear_icon)

    settings_button = ttk.Button(
        settings_frame,
        image=gear_photo,
        command=open_settings,
        style='secondary'
    )
    settings_button.pack()

    # Add chess pieces as decorative elements to header
    pieces = ['white king', 'white queen', 'white rook', 'white bishop', 'white knight', 'white pawn']
    piece_images = []

    for piece in pieces:
        piece_img = Image.open(f"assets/pieces/{piece}.png")
        piece_img = piece_img.resize((40, 40))
        photo = ImageTk.PhotoImage(piece_img)
        piece_images.append(photo)

        piece_label = ttk.Label(header_frame, image=photo)
        piece_label.pack(side=LEFT, padx=10, pady=5)

    # Create central content frame
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(expand=True)

    # Load and display main logo
    logo = Image.open("assets\\utils\\chessLogo.png")
    logo = logo.resize((200, 200))

    # Add a border (outline) around the image
    border_color = (12, 12, 12)
    border_width = 10
    logo_with_border = ImageOps.expand(logo, border=border_width, fill=border_color)

    # Convert the image to a format that can be used in Tkinter
    logo_img = ImageTk.PhotoImage(logo_with_border)

    # Display the logo with the border in the Tkinter label
    logo_label = ttk.Label(content_frame, image=logo_img)
    logo_label.pack(pady=20)

    # Keep a reference to avoid garbage collection
    logo_label.image = logo_img

    # Title with styled label
    title_frame = ttk.Frame(content_frame)
    title_frame.pack(pady=20)

    title_label = ttk.Label(
        title_frame,
        text="CHESS MASTER",
        font=("Helvetica", 32, "bold"),
        style='primary'
    )
    title_label.pack()

    subtitle_label = ttk.Label(
        title_frame,
        text="Challenge your mind, master the game",
        font=("Helvetica", 14),
        style='secondary'
    )
    subtitle_label.pack(pady=5)

    # Button container
    button_frame = ttk.Frame(content_frame)
    button_frame.pack(pady=30)

    play_button_style = ttk.Style()
    play_button_style.configure('primary.Outline.TButton', font=('Helvetica', 22))
    play_button = ttk.Button(
        button_frame,
        text="Start New Game",
        command=start_game,
        style='primary.Outline.TButton',
        width=15,
        padding=20
    )
    play_button.pack(pady=15)

    exit_button_style = ttk.Style()
    exit_button_style.configure('danger.Outline.TButton', font=('Helvetica', 15))
    quit_button = ttk.Button(
        button_frame,
        text="Exit Game",
        command=window.quit,
        style='danger.Outline.TButton',
        width=15,
        padding=20
    )
    quit_button.pack(pady=15)

    # Store references to prevent garbage collection
    window.logo_img = logo_img
    window.piece_images = piece_images
    window.gear_photo = gear_photo
    window.bg_photo = bg_photo  # Store background image reference

    return window


if __name__ == "__main__":
    app = create_chess_app()
    app.mainloop()
