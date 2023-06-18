import sys
import os

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import IntVar
from ttkthemes import ThemedTk

class Application(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("2011Scape - Drop Table Maker by Pixel [Version 1.0]")

        # Get the path of the directory containing the executable or the script
        if getattr(sys, 'frozen', False):
            # Executable path in PyInstaller
            base_path = sys._MEIPASS
        else:
            # Script path
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Construct the absolute file path
        file_path = os.path.join(base_path, "Item_list.txt")

        # Load item names from file
        try:
            with open(file_path, 'r') as f:
                self.item_names = [line.strip() for line in f]
        except FileNotFoundError:
            print("File not found:", file_path)

        # Create a canvas within the root window
        self.canvas = tk.Canvas(root, width=727, height=474, bg='#999999', highlightthickness=0)
        self.canvas.grid(row=0, column=0)

        # Create a vertical scrollbar and associate it with the canvas
        self.scrollbar = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame within the canvas to hold the other widgets
        self.inner_frame = ttk.Frame(self.canvas, borderwidth=2, relief="solid", width=690)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')

        # Configure the canvas to update the scroll region as the size of the inner_frame changes
        self.inner_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.grid(sticky="nsew")
        self.create_widgets()
        self.items = []
        for _ in range(1):  # Add items by default
            self.add_item_row()

    def create_widgets(self):
            ttk.Label(self, text="Total slots").grid(row=0, column=0)

            self.total_slots = ttk.Combobox(self, values=["256", "1", "8", "32", "128", "256", "512", "1024", "2048", "4096", "10240"])
            self.total_slots.set("256")  # default value
            self.total_slots.grid(row=0, column=1)

            self.add_item = ttk.Button(self, text="Add Item", command=self.add_item_row)
            self.add_item.grid(row=0, column=2)

            self.generate = ttk.Button(self, text="Generate", command=self.generate_code)
            self.generate.grid(row=0, column=3)

    def add_item_row(self):
        row_num = len(self.items) + 1
        frame = ttk.Frame(self.inner_frame)  
        frame.grid(row=row_num, columnspan=4)

        ttk.Label(frame, text="Item Name").grid(row=row_num, column=0) 

        name_entry = ttk.Combobox(frame, values=self.item_names)
        name_entry.set("BONES")  # Set the default value
        name_entry.grid(row=row_num, column=1)

        # Add functionality to filter items as the user types
        def update_combobox(event):
            # Get the current text in the combobox
            current_text = name_entry.get()

            # Filter the list of item names
            filtered_items = [item for item in self.item_names if current_text.lower() in item.lower()]

            # Update the values in the combobox
            name_entry['values'] = filtered_items

        name_entry.bind('<KeyRelease>', update_combobox)

        ttk.Label(frame, text="Quantity").grid(row=row_num, column=2) 
        quantity_entry = ttk.Entry(frame)
        quantity_entry.insert(0, "1")  # Set the default value
        quantity_entry.grid(row=row_num, column=3)

        # Set style for combobox
        style = ttk.Style()
        style.map('TCombobox', fieldbackground=[('readonly', '#333333')])  # set the dropdown color
        style.map('TCombobox', selectbackground=[('readonly', 'white')])  # set the selected item background color
        style.map('TCombobox', selectforeground=[('readonly', 'black')])  # set the selected item text color

        probability_entry = ttk.Combobox(frame, values=["1/8", "1/32", "1/128", "1/256", "1/512", "1/5000", "1/10000"], style='TCombobox')
        probability_entry.set("1/28")  # Set the default value
        guaranteed = IntVar()
        chk = ttk.Checkbutton(frame, variable=guaranteed)
        ttk.Label(frame, text="Guaranteed Drop").grid(row=row_num, column=6)
        chk.grid(row=row_num, column=7)

        if not guaranteed.get():
            ttk.Label(frame, text="Probability").grid(row=row_num, column=4)
            probability_entry.grid(row=row_num, column=5)

        remove_button = ttk.Button(frame, text=" x ", width=2, command=lambda: self.remove_item((name_entry, quantity_entry, probability_entry, guaranteed, frame)))
        remove_button.grid(row=row_num, column=8)

        self.items.append((name_entry, quantity_entry, probability_entry, guaranteed, frame))

    def remove_item(self, item):
        self.items.remove(item)
        item[-1].destroy()  # Remove the frame of the item

    def calculate_slots(self, probability):
        total = int(self.total_slots.get())
        if '/' in probability:  # If probability is entered as a fraction
            numerator, denominator = map(int, probability.split('/'))
            probability = numerator / denominator
        else:
            probability = float(probability)
        return int(total * probability)

    def generate_code(self):
        total_slots = self.total_slots.get()
        guaranteed_code = f'    guaranteed {{\n'
        main_code = f'    main {{\n'
        main_code += f'        total({total_slots})\n'  # total slots function


        for item in self.items:
            name = item[0].get() if item[0].get() != "" else "BONES"
            quantity = item[1].get() if item[1].get() != "" else "1"
            probability = item[2].get() if item[2].get() != "" else "1/28"

            if item[3].get():  # if it is a guaranteed drop
                guaranteed_code += f'        obj(Items.{name.upper()}, quantity = {quantity})\n'
            else:
                probability = item[2].get()
                slots = self.calculate_slots(probability)
                main_code += f'        obj(Items.{name.upper()}, quantity = {quantity}, slots = {slots})\n'
        
        guaranteed_code += '    }\n'
        main_code += '    }\n'

        code = f'import gg.rsmod.plugins.content.drops.DropTableFactory\n\n'
        code += 'val ids = intArrayOf(Npcs.YOUR_NPC_ID)\n\n'
        code += 'val table = DropTableFactory.build {\n'
        code += guaranteed_code
        code += main_code
        code += '}\n\n'
        self.save_code(code)

    def save_code(self, code):
        f = filedialog.asksaveasfile(mode='w', defaultextension=".plugin.kts", filetypes=(("Kotlin Script", "*.plugin.kts"), ("All files", "*.*")))
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
        f.write(code)
        f.close()

root = ThemedTk(theme="elegant") 
root.geometry("745x500")  # Set the window size
root.resizable(False, False)  # Prevent resizing of the window
root.attributes('-fullscreen', False)  # Prevent fullscreen
root.configure(bg="#999999")

app = Application(master=root)
app.mainloop()