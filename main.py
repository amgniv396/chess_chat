import tkinter as tk
import homecreen_graphics as home

def main():
    window = tk.Tk()
    window.title("Chess App")
    window.attributes('-fullscreen', True)

    home.show_home_screen(window)

    window.mainloop()

if __name__ == "__main__":
    main()
