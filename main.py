import tkinter.filedialog
import tkinter.messagebox
import pywinstyles
import sys
import tkinter
from tkinter import ttk
import sv_ttk
from PIL import Image, ImageTk
from math import sqrt
import json


# class Item:
#     def __init__(self, item_id, points, item_type):
#         self.item_id: str = item_id
#         self.points: list[float] = points
#         self.item_type: str = item_type

#     def __repr__(self):
#         return f"item: {self.item_id} type: {self.item_type}, {len(self.points)} points"

def resize_image(file_path, width, height):
    image = Image.open(file_path)
    image = image.resize((width, height), Image.ANTIALIAS)
    return ImageTk.PhotoImage(image)

class WhiteboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whiteboard - Untitled")
        

        self.open_directory = None
        self.unsaved_changes = False


        self.last_x, self.last_y = None, None
        self.pan_start = (0,0)
        self.camera_offset = (0,0)
        self.zoom_offset = 1
        

        self.point_resolution = 7
        self.line_simplification = 0 # Minimum distance of x between each point in cache

        self.pen_color = "white"
        self.pen_width = 2

        self.hotkey_down = False

        self.hotkey = "space"

        self.colors = {
            "white": "white",  # Keeping white as is
            "red": "#FF4C4C",   # Bright but slightly muted red
            "green": "#32D74B", # Vivid yet soft green
            "blue": "#4C9AFF",  # Clean, modern blue

            # Additional minimalistic colors
            "orange": "#FF9F1C",  # Warm, modern orange
            "yellow": "#FFD700",  # Deep gold-like yellow
            "purple": "#9B5DE5",  # Elegant, slightly muted purple
            "cyan": "#00C4CC",    # Soft yet striking cyan
            "pink": "#FF5370",    # Modern neon pink
            "gray": "#A0A0A0"     # Neutral gray for softer accents
        }

        self.tool = "pen"

        self.line_cache = []
        self.line_coord_cache = []
        

        self.objects = []

        # Create a Canvas widget
        self.canvas = tkinter.Canvas(self.root, bg="#141414", width=800, 
                                     height=600, highlightthickness=0)
        self.canvas.pack(fill=tkinter.BOTH, expand=True)

        ## Load images
        self.icon_pen = resize_image("icons/pencil.png", 16, 16)
        self.icon_eraser = resize_image("icons/eraser.png", 16, 16)
        self.icon_color = resize_image("icons/color.png", 16, 16)
        self.icon_lines = resize_image("icons/lines.png", 16, 16)
        self.bending_arrow = resize_image("icons/bending_arrow.png", 16, 16)
        self.icon_clear = resize_image("icons/clear.png", 16, 16)
        self.icon_more = resize_image("icons/more.png", 16, 16)



        self.context_menu = tkinter.Menu(root, tearoff=0, borderwidth = 0)

        self._add_to_context(self.context_menu, "Pen         1", lambda: self.set_tool("pen"), "#141414", icon=self.icon_pen)
        self._add_to_context(self.context_menu, "Eraser      2", lambda: self.set_tool("eraser"), "#141414", icon=self.icon_eraser)
        
        self.context_menu.add_separator()

        # Add sub menus
        self.color_context_m = tkinter.Menu(self.context_menu, tearoff=0, borderwidth = 0)
        
        self._add_to_context(self.color_context_m, "white", lambda: self.set_color("white"), "#141414", 
                              icon=self.bending_arrow)
        
        for name, color in self.colors.items():
            if name == "white": continue
            print(f"{name} - {color}")
            self._add_to_context(self.color_context_m, name, 
                                 lambda color=color, name=name: self.set_color(color, name), 
                                 color, 
                                 icon=self.bending_arrow)
        # self._add_to_context(self.color_context_m, "Red    R", lambda: self.set_color("red"), "red", 
        #                      icon=self.bending_arrow, activebackground = "red")
        # self._add_to_context(self.color_context_m, "Green  G", lambda: self.set_color("green"), "green", 
        #                      icon=self.bending_arrow, activebackground = "green")
        # self._add_to_context(self.color_context_m, "Blue   B", lambda: self.set_color("blue"), "blue", 
        #                      icon=self.bending_arrow, activebackground = "blue")
        
        self.context_menu.add_cascade(label="Colors", menu=self.color_context_m,
                                      foreground="#141414",
                                      activeforeground="white",
                                      activebackground="#141414", 
                                      image=self.icon_color,
                                      compound="left")

        self.context_menu_open = False

        self.line_width_context_m = tkinter.Menu(self.context_menu, tearoff=0, borderwidth = 0)
        self._add_to_context(self.line_width_context_m, "1 px", lambda: self.set_ln_width(1), "#141414", 
                             icon=self.bending_arrow)
        self._add_to_context(self.line_width_context_m, "2 px", lambda: self.set_ln_width(2), "#141414", 
                             icon=self.bending_arrow)
        self._add_to_context(self.line_width_context_m, "4 px", lambda: self.set_ln_width(4), "#141414", 
                             icon=self.bending_arrow)
        self._add_to_context(self.line_width_context_m, "8 px", lambda: self.set_ln_width(8), "#141414", 
                             icon=self.bending_arrow)
        self.context_menu.add_cascade(label="Line Width", menu=self.line_width_context_m,
                                      foreground="#141414",
                                      activeforeground="white",
                                      activebackground="#141414", 
                                      image=self.icon_lines,
                                      compound="left")


        self.more_context_m = tkinter.Menu(self.context_menu, tearoff=0, borderwidth = 0)
        self._add_to_context(self.more_context_m, "Simple Lines", lambda: self.set_color("white"), "#141414", 
                             icon=self.bending_arrow)
        self._add_to_context(self.more_context_m, "Dots", lambda: self.set_color("white"), "#141414", 
                             icon=self.bending_arrow)
        self.context_menu.add_cascade(label="More", menu=self.more_context_m,
                                      foreground="#141414",
                                      activeforeground="white",
                                      activebackground="#141414", 
                                      image=self.icon_more,
                                      compound="left")

        self.context_menu.add_separator()

        self._add_to_context(self.context_menu, "Clear", self.clear_button, "#141414", icon=self.icon_clear)


        self.label = tkinter.Label(self.root, text="pen - white ", fg="#2a2a2a", bg="#141414", 
                                   font=("Helvetica", 12, "bold italic"), bd=0)
        self.label.place(relx=1.0, rely=1.0, anchor="se", x=-3, y=-3)  # Positioning in bottom-right corner


        # Bind mouse events to the canvas
        self.canvas.bind("<B1-Motion>", self.mouse_move)  # Draw when the left mouse button is held down
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up)

        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)

        self.canvas.bind("<Button-3>", self.show_context_menu)

        self.canvas.bind("<Button-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)

        self.canvas.bind("<MouseWheel>", self.zoom)

        self.canvas.bind_all("<Control-z>", self.undo)

        self.canvas.bind_all("<Control-s>", self.save)
        self.canvas.bind_all("<Control-o>", self.open)
        self.canvas.bind_all("<Control-n>", self.new)


        # Apply theme and title bar style
        sv_ttk.set_theme("dark")
        self.apply_theme_to_titlebar()

        # Apply icon after the theme!
        self.root.iconbitmap("icons/app_icon.ico")

    def clear_button(self) -> None:
        if tkinter.messagebox.askokcancel("Confirm", "Clear canvas?"):
            self.clear_canvas()

    def clear_canvas(self) -> None:
        self.title_changes_made()
        for obj in self.objects:
            self.canvas.delete(obj["id"])

        self.objects = []

    def undo(self, event) -> None:
        self.title_changes_made()
        self.canvas.delete(self.objects[-1]["id"])
        del self.objects[-1]

    def open(self, event) -> None:
        self.open_directory = tkinter.filedialog.askopenfilename(
                                                title="Save File", 
                                                defaultextension=".json", 
                                                filetypes=[("Json files", "*.json"), 
                                                        ("All files", "*.*")]
        )

        content = None
        with open(self.open_directory, "r") as file:
            content = json.load(file)

        for item in content:
            if item["type"] == "oval":
                ref = self.canvas.create_oval(item["points"],
                                    fill=item["color"])
                self.objects.append({"id":ref, "type":"oval", "points":item["points"], 
                                     "color":item["color"]})
                
            if item["type"] == "line":
                ref = self.canvas.create_line(item["points"], 
                                        fill=item["color"], 
                                        width=item["width"],
                                        smooth=1)
                self.objects.append({"id":ref, "type":"line", "points":item["points"], 
                                     "color":item["color"], "width":item["width"]})
                
        self.update_title()
    
    def save(self, event) -> None:
        if not self.open_directory:
            self.open_directory = tkinter.filedialog.asksaveasfilename(
                                                    title="Save File", 
                                                    defaultextension=".json", 
                                                    filetypes=[("Json files", "*.json"), 
                                                               ("All files", "*.*")]
            )

        with open(self.open_directory, "w") as file:
            file.write( json.dumps(self.objects, indent=4) )

        self.update_title()
        self.unsaved_changes = False

    def new(self, event) -> None:
        if self.unsaved_changes and not tkinter.messagebox.askokcancel(
                "Confirmation",
                "You have unsaved changes, are you sure you want to create a new file?"):
            return
        
        self.open_directory = None
        self.update_title()
        self.clear_canvas()

        self.update_title()

    def _add_to_context(self, context, lbl, command, clr, icon = None, 
                        activeforeground="white",
                        activebackground="#141414") -> None:
        context.add_command(label=lbl, foreground=clr,
                                      activeforeground=activeforeground,
                                      activebackground=activebackground,
                         command=command,
                         image=icon,
                         compound="left")

    def apply_theme_to_titlebar(self):
        version = sys.getwindowsversion()
        if version.major == 10 and version.build >= 22000:
            pywinstyles.change_header_color(self.root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
        elif version.major == 10:
            pywinstyles.apply_style(self.root, "dark" if sv_ttk.get_theme() == "dark" else "normal")
            self.root.wm_attributes("-alpha", 0.99)
            self.root.wm_attributes("-alpha", 1)

    def update_lbl(self, text):
        clr = self.pen_color if self.tool == "pen" else "#2a2a2a"
        self.label.config(text=text+" ", foreground=clr)

    def update_title(self, additional: str = "") -> None:
        d = self.open_directory if self.open_directory else "Untitled"
        self.root.title("Whiteboard - "+d+additional)

    def title_changes_made(self) -> None:
        self.update_title(" *")
        self.unsaved_changes =True

    def start_pan(self, event) -> None:
        print("Start pan")
        self.pan_start = (event.x, event.y)

    def pan(self, event) -> None:
        x_change = event.x - self.pan_start[0]
        y_change = event.y - self.pan_start[1]

        for obj in self.objects:
            self.canvas.move(obj["id"], x_change, y_change)

        self.camera_offset = (self.camera_offset[0]-x_change,
                              self.camera_offset[1]-y_change)

        self.pan_start = (event.x, event.y)

    def get_color_name(self, color) -> str | None:
        for name, clr in self.colors.items():
            if color == clr:
                return name
        return None

    def set_tool(self, tool):
        self.tool = tool
        if tool == "pen":
            self.update_lbl(f"{tool} - {self.get_color_name(self.pen_color)}")
        else:
            self.update_lbl(tool)

    def set_color(self, color, name: str = None) -> None:
        if not name: name = color

        self.pen_color = color
        if self.tool == "pen":
            self.update_lbl(f"{self.tool} - {name}")

    def set_ln_width(self, width) -> None:
        self.pen_width = width

    def show_context_menu(self, event):
        if not self.context_menu_open:
            self.context_menu.post(event.x_root, event.y_root)
        else:
            self.context_menu.unpost()
        self.context_menu_open = not self.context_menu_open

    # :TODO Move to utils.py
    def _dist_between_coords(self, a, b) -> float:
        return sqrt( abs(a[0] - b[0]) ** 2 
                    +
                     abs(a[1] - b[1]) ** 2 )

    def erase(self, event):
        self.title_changes_made()
        overlapping_items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        for item in overlapping_items:
            self.canvas.delete(item)

            for i, obj in enumerate(self.objects):
                if obj["id"] == item:
                    del self.objects[i]

    def draw(self, event):
        self.title_changes_made()
        x, y = event.x, event.y
        if self.last_x and self.last_y:
            if self._dist_between_coords((x,y), (self.last_x, self.last_y)) < self.point_resolution:
                return

            segment = self.canvas.create_line(x, y, self.last_x, self.last_y, 
                                    fill=self.pen_color, width=self.pen_width,
                                    smooth=1)
            
            self.line_cache.append(segment)

        self.last_x, self.last_y = x, y
        self.line_coord_cache += [x, y]

    def mouse_move(self, event):
        match self.tool:
            case "pen":
                self.draw(event)
            case "eraser":
                self.erase(event)

    def simplify_line(self, coords=None) -> list[float]:
        if not coords:
            coords = self.line_coord_cache
        
        index = 0

        simple_coords = []
        last_coords = []

        while index + 2 <= len(coords):
            x = coords[index]
            y = coords[index+1]

            if not last_coords:
                last_coords = [x,y]
                simple_coords += [x,y]
                index += 2
                continue

            if (self._dist_between_coords( (x,y), 
                                         (last_coords[0], last_coords[1]) )
                                         >= self.line_simplification
                                         ):
                simple_coords += [x,y]

                last_coords = [x,y]

            index += 2

        return simple_coords

    def apply_offset(self, coords, scale=True):
        new_coords = []

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        canvas_center_x = canvas_width / 2
        canvas_center_y = canvas_height / 2

        for i, coord in enumerate(coords):
            # Apply camera offset (panning) first
            world_space = coord + (self.camera_offset[0] if i % 2 == 0 else self.camera_offset[1])

            if scale:
                # Calculate the distance from the center of the canvas
                center_dist = world_space - (canvas_center_x if i % 2 == 0 else canvas_center_y)

                # Apply scaling based on zoom offset
                scaled_coord = world_space + center_dist * (self.zoom_offset - 1)
                new_coords.append(scaled_coord)
            else:
                # If no scaling, just apply the panning offset
                new_coords.append(world_space)

        return new_coords


    # def apply_offset(self, coords, scale=True):
    #     new_coords = []

    #     for i, coord in enumerate(coords):
    #         # Get the world space coordinates by adding the camera offset
    #         world_space = coord + self.camera_offset[0] if i % 2 == 0 else coord + self.camera_offset[1]

    #         if scale:
    #             # Calculate the center distance from the center of the canvas
    #             center_dist = world_space - (self.canvas.winfo_width() / 2 if i % 2 == 0 else self.canvas.winfo_height() / 2)
                
    #             # Apply scaling based on zoom (if scale=True)
    #             new_coords.append(world_space + center_dist * (self.zoom_offset - 1))
    #         else:
    #             # If scale=False, no scaling is applied, only account for panning
    #             new_coords.append(world_space)

    #     return new_coords


    def mouse_up(self, event):
        if not self.tool == "pen": return

        self.title_changes_made()

        # Resent coords
        self.last_x, self.last_y = None, None


        # Create new line
        if len(self.line_coord_cache) <= 2:
            points = event.x - self.pen_width, event.y - self.pen_width, event.x + self.pen_width, event.y + self.pen_width
            offset_points = self.apply_offset(points)
            ref = self.canvas.create_oval(points,
                                    fill=self.pen_color)
            self.objects.append({"id":ref, "type":"oval", "points":offset_points, "color":self.pen_color})
        else:
            coords = self.simplify_line()
            offset_coords = self.apply_offset(coords)
            try:
                ref = self.canvas.create_line(coords, 
                                        fill=self.pen_color, width=self.pen_width,
                                        smooth=1)
                
                self.objects.append({"id":ref, "type":"line", "points":offset_coords, 
                                     "color":self.pen_color, "width":self.pen_width})

                print(f"Created line with {len(coords)/2} segments, {len(self.line_coord_cache)/2} before simplification")
            except:
                print(f"ERROR: Line segments: {len(coords)}")

        # Delete temporary lines
        for ln in self.line_cache:
            self.canvas.delete(ln)

        self.line_cache = []
        self.line_coord_cache = []

    def zoom_in(self, event):
        canvas_center_x = self.canvas.winfo_width() / 2
        canvas_center_y = self.canvas.winfo_height() / 2
        self.canvas.scale("all", canvas_center_x, canvas_center_y, 1.1, 1.1)
        self.zoom_offset *= 0.9

    def zoom_out(self, event):
        canvas_center_x = self.canvas.winfo_width() / 2
        canvas_center_y = self.canvas.winfo_height() / 2
        self.canvas.scale("all", canvas_center_x, canvas_center_y, 0.9, 0.9)
        self.zoom_offset *= 1.1
        #print(self.zoom_offset)

    def zoom(self, event):
        if event.delta > 0:
            self.zoom_in(event)
        else:
            self.zoom_out(event)

    def key_down(self, event):
        print(event.keysym, self.hotkey_down)
        if self.hotkey_down:
            key: str = event.keysym
            print(f"{self.hotkey} + {key}")
            if (key.isnumeric() and 
                int(key) > 0 and 
                int(key) <= 10 and 
                int(key) < len(list(self.colors.keys()))):
                self.pen_color = list(
                    self.colors.values())[int(key)-1]
                self.update_lbl(f"{self.tool} - {self.get_color_name(self.pen_color)}")
        else:
            match event.keysym:
                case "1":
                    self.set_tool("pen")
                case "2":
                    self.set_tool("eraser")

        if event.keysym == self.hotkey:
            self.hotkey_down = True

    def key_up(self, event):
        if event.keysym == self.hotkey:
            self.hotkey_down = False


if __name__ == "__main__":
    root = tkinter.Tk()
    app = WhiteboardApp(root)
    root.mainloop()