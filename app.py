import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class DirectoryStructureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Directory Structure Generator")
        self.root.geometry("800x600")

        # Main widgets
        self.dir_label = tk.Label(self.root, text="No directory selected.", wraplength=700)
        self.dir_label.pack(pady=10)

        self.select_button = tk.Button(self.root, text="Select Directory", command=self.select_directory)
        self.select_button.pack(pady=5)

        self.tree_frame = tk.Frame(self.root)
        self.tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Modified Treeview to include a checkbox column
        self.treeview = ttk.Treeview(self.tree_frame, columns=("Checked"), selectmode="none")
        self.treeview.heading("#0", text="Name")
        self.treeview.heading("Checked", text="")
        self.treeview.column("Checked", width=10, anchor="center")
        self.treeview.column("#0", stretch=tk.YES)
        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.treeview.yview)
        self.treeview.configure(yscroll=self.tree_scroll.set)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.generate_button = tk.Button(self.root, text="Generate Structure", command=self.generate_structure, state=tk.DISABLED)
        self.generate_button.pack(pady=5)

        self.text_area = tk.Text(self.root, wrap=tk.WORD, state=tk.DISABLED, height=15, width=70)
        self.text_area.pack(pady=10)

        self.save_button = tk.Button(self.root, text="Save Structure", command=self.save_structure, state=tk.DISABLED)
        self.save_button.pack(pady=5)

        self.selected_directory = None
        self.structure_text = None
        self.path_to_id = {}  # Dictionary to store path-to-id mappings
        self.id_to_path = {}  # New dictionary to store id-to-path mappings
        
        # Bind click event to handle checkboxes
        self.treeview.tag_configure('checked', image='')
        self.treeview.tag_configure('unchecked', image='')
        self.treeview.bind('<Button-1>', self.toggle_check)

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

    def select_directory(self):
        """Allows the user to select a directory."""
        self.selected_directory = filedialog.askdirectory()
        if self.selected_directory:
            self.dir_label.config(text=f"Selected Directory: {self.selected_directory}")
            self.populate_treeview()
            self.generate_button.config(state=tk.NORMAL)
        else:
            messagebox.showwarning("Warning", "No directory was selected.")

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

    def format_structure(self, tree, indent="", last=False):
        result = ""
        keys = list(tree.keys())
        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            branch = "└── " if is_last else "├── "
            spacer = "    " if is_last else "│   "
            result += f"{indent}{branch}{key}\n"
            if isinstance(tree[key], dict):
                result += self.format_structure(tree[key], indent + spacer, last=is_last)
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