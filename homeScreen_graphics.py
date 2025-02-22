import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk


def start_game():
   print("Game starting...")  # Replace with actual game logic


def open_settings():
   print("Opening settings...")  # Replace with settings window logic


def create_chess_app():
   window = ttk.Window(themename="darkly")
   window.title("Chess App")
   window.attributes('-fullscreen', True)

   # Create main container with background
   main_frame = ttk.Frame(window)
   main_frame.pack(fill=BOTH, expand=True)

   # Create a decorative header
   header_frame = ttk.Frame(main_frame, bootstyle=PRIMARY)
   header_frame.pack(fill=X, pady=(0, 20))

   # Settings button in top right
   settings_frame = ttk.Frame(header_frame)
   settings_frame.pack(side=RIGHT, padx=20)

   # Load gear icon
   # TODO put a gear image
   gear_icon = Image.open(f"assets/pieces/white rook.png")
   gear_icon = gear_icon.resize((30, 30))
   gear_photo = ImageTk.PhotoImage(gear_icon)

   settings_button = ttk.Button(
       settings_frame,
       image=gear_photo,
       command=open_settings,
       bootstyle=SECONDARY
   )
   settings_button.pack()

   # Add chess pieces as decorative elements to header
   pieces = ['white king', 'white queen', 'white rook', 'white bishop', 'white knight', 'white pawn']
   piece_frames = []
   piece_images = []

   for piece in pieces:
       piece_img = Image.open(f"assets/pieces/{piece}.png")
       piece_img = piece_img.resize((40, 40))
       photo = ImageTk.PhotoImage(piece_img)
       piece_images.append(photo)

       piece_label = ttk.Label(header_frame, image=photo)
       piece_label.pack(side=LEFT, padx=10, pady=5)
       piece_frames.append(piece_label)

   # Create central content frame
   content_frame = ttk.Frame(main_frame)
   content_frame.pack(expand=True)

   # Load and display main logo
   logo = Image.open(f"assets/pieces/white rook.png")
   logo = logo.resize((150, 150))
   logo_img = ImageTk.PhotoImage(logo)

   logo_label = ttk.Label(content_frame, image=logo_img)
   logo_label.pack(pady=20)

   # Title with styled label
   title_frame = ttk.Frame(content_frame)
   title_frame.pack(pady=20)

   title_label = ttk.Label(
       title_frame,
       text="CHESS MASTER",
       font=("Helvetica", 32, "bold"),
       bootstyle=PRIMARY
   )
   title_label.pack()

   subtitle_label = ttk.Label(
       title_frame,
       text="Challenge your mind, master the game",
       font=("Helvetica", 14),
       bootstyle=SECONDARY
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
       #bootstyle=(PRIMARY, OUTLINE),
       style='primary.Outline.TButton',
       width=15,
       padding=20  # Added padding to make button bigger
   )
   play_button.pack(pady=15)  # Increased spacing

   exit_button_style = ttk.Style()
   exit_button_style.configure('danger.Outline.TButton', font=('Helvetica', 15))
   quit_button = ttk.Button(
       button_frame,
       text="Exit Game",
       command=window.quit,
       style='danger.Outline.TButton',
       width=15,
       padding=20  # Added padding to make button bigger
   )
   quit_button.pack(pady=15)  # Increased spacing

   # Footer with version info
   footer_frame = ttk.Frame(main_frame)
   footer_frame.pack(side=BOTTOM, pady=20)

   version_label = ttk.Label(
       footer_frame,
       text="Chess Master v1.0",
       bootstyle=SECONDARY
   )
   version_label.pack()

   # Store references to prevent garbage collection
   window.logo_img = logo_img
   window.piece_images = piece_images
   window.gear_photo = gear_photo

   return window


if __name__ == "__main__":
   app = create_chess_app()
   app.mainloop()