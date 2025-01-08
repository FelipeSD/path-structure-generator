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
        
        self.treeview = ttk.Treeview(self.tree_frame, columns=("Name"), selectmode="extended")
        self.treeview.heading("#0", text="Name")
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
        self.selected_items = set()
        self.path_to_id = {}  # New dictionary to store path-to-id mappings

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
        self.path_to_id.clear()  # Clear the path mapping
        
        # Insert root directory first
        root_name = os.path.basename(self.selected_directory)
        root_id = self.treeview.insert("", "end", text=root_name, open=True)
        self.path_to_id[self.selected_directory] = root_id

        # Walk through directory structure
        for root, dirs, files in os.walk(self.selected_directory):
            # Skip the root directory as we've already added it
            if root == self.selected_directory:
                continue
                
            # Get parent path and ID
            parent_path = os.path.dirname(root)
            parent_id = self.path_to_id.get(parent_path)
            
            if parent_id is not None:
                # Insert directory
                dir_name = os.path.basename(root)
                dir_id = self.treeview.insert(parent_id, "end", text=dir_name, open=True)
                self.path_to_id[root] = dir_id
                
                # Insert files in current directory
                for file in files:
                    self.treeview.insert(dir_id, "end", text=file)

    def create_nested_dict(self, path_parts):
        """Creates a nested dictionary from a list of path parts."""
        current = {}
        temp = current
        for part in path_parts[:-1]:
            temp[part] = {}
            temp = temp[part]
        temp[path_parts[-1]] = None
        return current

    def merge_dicts(self, dict1, dict2):
        """Recursively merges two nested dictionaries."""
        for key in dict2:
            if key in dict1:
                if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                    self.merge_dicts(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
        return dict1

    def generate_structure(self):
        """Generates the formatted directory structure."""
        self.selected_items = set(self.treeview.selection())
        if not self.selected_items:
            messagebox.showwarning("Warning", "No items were selected.")
            return
        
        directory_tree = {}
        for item in self.selected_items:
            path = self.get_full_path(item)
            parts = [p for p in path.split(os.sep) if p]  # Remove empty strings
            nested_dict = self.create_nested_dict(parts)
            directory_tree = self.merge_dicts(directory_tree, nested_dict)
        
        self.structure_text = self.format_structure(directory_tree)
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, self.structure_text)
        self.text_area.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)

    def get_full_path(self, item):
        """Returns the full path of the selected item in the Treeview."""
        path = []
        while item:
            path.append(self.treeview.item(item, "text"))
            item = self.treeview.parent(item)
        return os.path.join(*reversed(path))

    def format_structure(self, tree, indent="", last=False):
        """Converts the directory tree to text in the requested format."""
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
        """Saves the generated structure to a text file."""
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
