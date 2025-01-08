import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.scrolledtext as scrolledtext
from queue import Queue

class DirectoryStructureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Directory Structure Generator")
        self.root.geometry("800x600")
        
        # Container principal
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Frame superior
        self.top_frame = tk.Frame(self.main_container)
        self.top_frame.pack(fill=tk.X)
        
        self.dir_label = tk.Label(self.top_frame, text="No directory selected.", wraplength=700)
        self.dir_label.pack(side=tk.LEFT, pady=5)
        
        self.select_button = tk.Button(self.top_frame, text="Select Directory", command=self.select_directory)
        self.select_button.pack(side=tk.RIGHT, pady=5)
        
        # Status frame com barra de progresso e label
        self.status_frame = tk.Frame(self.main_container)
        self.status_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(self.status_frame, text="")
        self.status_label.pack(fill=tk.X)
        
        # Ocultar frame de status inicialmente
        self.status_frame.pack_forget()
        
        # Frame da árvore
        self.tree_frame = tk.Frame(self.main_container)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.treeview = ttk.Treeview(self.tree_frame, columns=("Checked"), selectmode="none")
        self.treeview.heading("#0", text="Name")
        self.treeview.heading("Checked", text="")
        self.treeview.column("Checked", width=50, anchor="center")
        self.treeview.column("#0", stretch=tk.YES)
        
        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.treeview.yview)
        self.treeview.configure(yscroll=self.tree_scroll.set)
        
        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame inferior
        self.bottom_frame = tk.Frame(self.main_container)
        self.bottom_frame.pack(fill=tk.X, pady=5)
        
        self.generate_button = tk.Button(self.bottom_frame, text="Generate Structure", 
                                       command=self.generate_structure, state=tk.NORMAL)
        self.generate_button.pack(pady=5)
        
        self.text_area = tk.Text(self.bottom_frame, wrap=tk.WORD, state=tk.DISABLED, height=15)
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.save_button = tk.Button(self.bottom_frame, text="Save Structure", 
                                   command=self.save_structure, state=tk.DISABLED)
        self.save_button.pack(pady=5)
        
        self.selected_directory = None
        self.structure_text = None
        self.path_to_id = {}
        self.id_to_path = {}
        self.total_items = 0
        self.processed_items = 0
        
        self.treeview.tag_configure('checked', image='')
        self.treeview.tag_configure('unchecked', image='')
        self.treeview.bind('<Button-1>', self.toggle_check)
        
        self.queue = Queue()

    def update_progress(self, value, status_text=""):
        self.progress_var.set(value)
        if status_text:
            self.status_label.config(text=status_text)
        self.root.update_idletasks()

    def count_items(self, directory):
        total = 0
        for _, dirs, files in os.walk(directory):
            total += len(dirs) + len(files)
        return total

    def process_directory(self):
        self.total_items = self.count_items(self.selected_directory)
        self.processed_items = 0
        self.queue.put(('status', f"Found {self.total_items} items to process"))
        
        root_name = os.path.basename(self.selected_directory)
        root_id = self.treeview.insert("", "end", text=root_name, open=False, values=("☐",))
        self.path_to_id[self.selected_directory] = root_id
        self.id_to_path[root_id] = self.selected_directory

        for root, dirs, files in os.walk(self.selected_directory):
            if root == self.selected_directory:
                continue
                
            parent_path = os.path.dirname(root)
            parent_id = self.path_to_id.get(parent_path)
            
            if parent_id is not None:
                dir_name = os.path.basename(root)
                dir_id = self.treeview.insert(parent_id, "end", text=dir_name, open=False, values=("☐",))
                self.path_to_id[root] = dir_id
                self.id_to_path[dir_id] = root
                
                for file in files:
                    file_id = self.treeview.insert(dir_id, "end", text=file, values=("☐",))
                    file_path = os.path.join(root, file)
                    self.id_to_path[file_id] = file_path
                    
                self.processed_items += len(files) + 1  # +1 for the directory
                progress = (self.processed_items / self.total_items) * 100
                self.queue.put(('progress', progress))
                self.queue.put(('status', f"Processed {self.processed_items} of {self.total_items} items"))
                time.sleep(0.001)

        self.queue.put(('done', None))

    def process_queue(self):
        try:
            while True:  # Process all available messages
                msg_type, data = self.queue.get_nowait()
                
                if msg_type == 'progress':
                    self.update_progress(data)
                elif msg_type == 'status':
                    self.status_label.config(text=data)
                elif msg_type == 'done':
                    self.status_frame.pack_forget()
                    return
                
        except Exception:
            self.root.after(100, self.process_queue)

    def select_directory(self):
        self.selected_directory = filedialog.askdirectory()
        if self.selected_directory:
            self.dir_label.config(text=f"Selected Directory: {self.selected_directory}")
            
            # Reset
            self.treeview.delete(*self.treeview.get_children())
            self.path_to_id.clear()
            self.id_to_path.clear()
            
            # Show progress frame
            self.status_frame.pack(after=self.top_frame, fill=tk.X, pady=5)
            self.update_progress(0, "Initializing...")
            
            # Start processing
            threading.Thread(target=self.process_directory, daemon=True).start()
            self.root.after(100, self.process_queue)
        else:
            messagebox.showwarning("Warning", "No directory was selected.")

    def toggle_check(self, event):
        """Handles the checkbox toggle when clicking on an item"""
        region = self.treeview.identify_region(event.x, event.y)
        if region == "cell":
            column = self.treeview.identify_column(event.x)
            if column == "#1":  # Checkbox column
                item = self.treeview.identify_row(event.y)
                current_state = self.treeview.set(item, "Checked")
                new_state = "☐" if current_state == "☑" else "☑"
                self.treeview.set(item, "Checked", new_state)
                
                # Toggle all children
                self.toggle_children(item, new_state)
                # Update parent state
                self.update_parent_state(self.treeview.parent(item))

    def toggle_children(self, item, state):
        """Recursively toggles all children of an item"""
        children = self.treeview.get_children(item)
        for child in children:
            self.treeview.set(child, "Checked", state)
            self.toggle_children(child, state)

    def update_parent_state(self, parent):
        """Updates parent checkbox based on children states"""
        if parent:
            children = self.treeview.get_children(parent)
            child_states = [self.treeview.set(child, "Checked") for child in children]
            
            if all(state == "☑" for state in child_states):
                self.treeview.set(parent, "Checked", "☑")
            elif all(state == "☐" for state in child_states):
                self.treeview.set(parent, "Checked", "☐")
            else:
                self.treeview.set(parent, "Checked", "☑")
            
            # Recursively update parent's parent
            self.update_parent_state(self.treeview.parent(parent))

    def populate_treeview(self):
        """Populates the Treeview with the directory and file structure."""
        self.treeview.delete(*self.treeview.get_children())
        self.path_to_id.clear()
        self.id_to_path.clear()
        
        # Insert root directory first
        root_name = os.path.basename(self.selected_directory)
        root_id = self.treeview.insert("", "end", text=root_name, open=True, values=("☐",))
        self.path_to_id[self.selected_directory] = root_id
        self.id_to_path[root_id] = self.selected_directory

        # Walk through directory structure
        for root, dirs, files in os.walk(self.selected_directory):
            if root == self.selected_directory:
                continue
                
            parent_path = os.path.dirname(root)
            parent_id = self.path_to_id.get(parent_path)
            
            if parent_id is not None:
                dir_name = os.path.basename(root)
                dir_id = self.treeview.insert(parent_id, "end", text=dir_name, open=True, values=("☐",))
                self.path_to_id[root] = dir_id
                self.id_to_path[dir_id] = root
                
                for file in files:
                    file_id = self.treeview.insert(dir_id, "end", text=file, values=("☐",))
                    file_path = os.path.join(root, file)
                    self.id_to_path[file_id] = file_path

    def get_checked_items(self):
        """Returns a list of checked items with their full paths"""
        checked_items = []
        def collect_checked(item):
            if self.treeview.set(item, "Checked") == "☑":
                full_path = self.id_to_path.get(item)
                if full_path:
                    checked_items.append(full_path)
            for child in self.treeview.get_children(item):
                collect_checked(child)
        
        for item in self.treeview.get_children():
            collect_checked(item)
        return checked_items

    def generate_structure(self):
        """Generates the formatted directory structure."""
        checked_paths = self.get_checked_items()
        if not checked_paths:
            messagebox.showwarning("Warning", "No items were selected.")
            return
        
        # Criar a estrutura inicial com o diretório raiz
        root_name = os.path.basename(self.selected_directory)
        directory_tree = {root_name: {}}
        
        for path in checked_paths:
            # Get the relative path from the selected directory
            rel_path = os.path.relpath(path, self.selected_directory)
            parts = rel_path.split(os.sep)
            
            # Create nested dictionary for this path, starting from the root
            current = directory_tree[root_name]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # Se for o último item
                    if part not in current:
                        current[part] = {}
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        self.structure_text = self.format_structure(directory_tree)
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, self.structure_text)
        self.text_area.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)

    def format_structure(self, tree, indent=""):
        result = ""
        keys = list(tree.keys())
        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            branch = "└── " if is_last else "├── "
            spacer = "    " if is_last else "│   "
            result += f"{indent}{branch}{key}\n"
            if isinstance(tree[key], dict):
                result += self.format_structure(tree[key], indent + spacer)
        return result

    def save_structure(self):
        if not self.structure_text:
            messagebox.showerror("Error", "No structure generated to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.structure_text)
            messagebox.showinfo("Success", f"Structure saved to: {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DirectoryStructureApp(root)
    root.mainloop()