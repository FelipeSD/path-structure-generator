import os
import time
import json
import mimetypes
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.scrolledtext as scrolledtext
from queue import Queue

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("400x600")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Create main frame with scrollbar
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        self.main_frame = ttk.Frame(canvas)
        self.main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollable elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Settings sections
        self.create_ignored_folders_section(settings.get('ignored_folders', []))
        self.create_file_content_section(settings.get('file_content_settings', {}))
        
        # Save button
        ttk.Button(self.main_frame, text="Save", command=self.save_settings).pack(pady=10)
        
        self.result = None
        
    def create_ignored_folders_section(self, ignored_folders):
        # Ignored folders section
        ttk.Label(self.main_frame, text="Ignored Folders:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=(10,5))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=6)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate listbox
        for folder in ignored_folders:
            self.listbox.insert(tk.END, folder)
        
        # Input frame
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.folder_entry = ttk.Entry(input_frame)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(input_frame, text="Add", command=self.add_folder).pack(side=tk.LEFT)
        ttk.Button(input_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=5)

    def create_file_content_section(self, content_settings):
        # File content settings section
        ttk.Label(self.main_frame, text="File Content Settings:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=(10,5))
        
        # Include file contents checkbox
        self.include_contents = tk.BooleanVar(value=content_settings.get('include_contents', False))
        ttk.Checkbutton(self.main_frame, text="Include file contents", variable=self.include_contents).pack(anchor=tk.W)
        
        # Max file size frame
        size_frame = ttk.Frame(self.main_frame)
        size_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(size_frame, text="Max file size (KB):").pack(side=tk.LEFT)
        self.max_size = tk.StringVar(value=str(content_settings.get('max_file_size_kb', 100)))
        ttk.Entry(size_frame, textvariable=self.max_size, width=10).pack(side=tk.LEFT, padx=5)
        
        # Allowed extensions
        ttk.Label(self.main_frame, text="Allowed Extensions:").pack(anchor=tk.W, pady=(10,5))
        
        extensions_frame = ttk.Frame(self.main_frame)
        extensions_frame.pack(fill=tk.BOTH, expand=True)
        
        self.extensions_text = tk.Text(extensions_frame, height=4, width=40)
        extensions_scroll = ttk.Scrollbar(extensions_frame, command=self.extensions_text.yview)
        self.extensions_text.configure(yscrollcommand=extensions_scroll.set)
        
        self.extensions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        extensions_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Set default extensions
        default_extensions = content_settings.get('allowed_extensions', ['.txt', '.py', '.js', '.html', '.css', '.md', '.json', '.xml', '.yaml', '.yml'])
        self.extensions_text.insert('1.0', '\n'.join(default_extensions))

    def add_folder(self):
        folder = self.folder_entry.get().strip()
        if folder:
            self.listbox.insert(tk.END, folder)
            self.folder_entry.delete(0, tk.END)
            
    def remove_selected(self):
        selection = self.listbox.curselection()
        if selection:
            self.listbox.delete(selection)
            
    def save_settings(self):
        try:
            max_size = int(self.max_size.get())
            if max_size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Max file size must be a positive number")
            return
            
        extensions = [ext.strip() for ext in self.extensions_text.get('1.0', tk.END).split('\n') if ext.strip()]
        
        self.result = {
            'ignored_folders': list(self.listbox.get(0, tk.END)),
            'file_content_settings': {
                'include_contents': self.include_contents.get(),
                'max_file_size_kb': max_size,
                'allowed_extensions': extensions
            }
        }
        self.destroy()


class DirectoryStructureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Directory Structure Generator")
        self.root.geometry("800x650")
        
        # Load settings
        self.settings_file = "directory_settings.json"
        self.settings = self.load_settings()
        self.ignored_folders = self.settings.get('ignored_folders', [])
        
        # Container principal
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Top frame with directory selection and settings
        self.top_frame = tk.Frame(self.main_container)
        self.top_frame.pack(fill=tk.X, pady=5)
        
        self.dir_label = tk.Label(self.top_frame, text="No directory selected.", wraplength=700)
        self.dir_label.pack(side=tk.LEFT)
        
        self.settings_button = tk.Button(self.top_frame, text="Settings", command=self.show_settings)
        self.settings_button.pack(side=tk.RIGHT, padx=5)
        
        self.select_button = tk.Button(self.top_frame, text="Select Directory", command=self.select_directory)
        self.select_button.pack(side=tk.RIGHT, padx=5)
        
        # Status frame with progress bar
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
        
        self.text_area = scrolledtext.ScrolledText(self.bottom_frame, wrap=tk.WORD, state=tk.DISABLED, height=15)
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.save_button = tk.Button(self.bottom_frame, text="Save Structure", 
                                   command=self.save_structure, state=tk.DISABLED)
        self.save_button.pack(side=tk.RIGHT, padx=5)

        self.copy_button = tk.Button(self.bottom_frame, text="Copy", 
                                   command=lambda: self.copy_text(self.text_area), state=tk.DISABLED)
        self.copy_button.pack(pady=5)
        self.copy_button.pack(side=tk.RIGHT, padx=5)
        
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

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'ignored_folders': [],
                'file_content_settings': {
                    'include_contents': False,
                    'max_file_size_kb': 100,
                    'allowed_extensions': ['.txt', '.py', '.js', '.html', '.css', '.md', '.json', '.xml', '.yaml', '.yml']
                }
            }

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)
            
    def show_settings(self):
        dialog = SettingsDialog(self.root, self.settings)
        self.root.wait_window(dialog)
        if dialog.result is not None:
            self.settings = dialog.result
            self.ignored_folders = self.settings['ignored_folders']
            self.save_settings()
            
            # If directory is already loaded, refresh the view
            if self.selected_directory:
                self.populate_treeview()
                
    def should_ignore_folder(self, folder_name):
        return folder_name in self.ignored_folders
    
    def should_include_file_content(self, filepath):
        """Check if file content should be included based on settings"""
        if not self.settings['file_content_settings']['include_contents']:
            return False
            
        # Check file size
        try:
            size_kb = os.path.getsize(filepath) / 1024
            if size_kb > self.settings['file_content_settings']['max_file_size_kb']:
                return False
        except OSError:
            return False
            
        # Check extension
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in self.settings['file_content_settings']['allowed_extensions']:
            return False
            
        # Try to detect if it's a text file
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type and not mime_type.startswith('text/'):
            return False
            
        return True

    def read_file_content(self, filepath):
        """Safely read file content"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def update_progress(self, value, status_text=""):
        self.progress_var.set(value)
        if status_text:
            self.status_label.config(text=status_text)
        self.root.update_idletasks()

    def count_items(self, directory):
        total = 0
        for _, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not self.should_ignore_folder(d)]
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
            # Remove ignored folders from dirs list (modifies dirs in place)
            dirs[:] = [d for d in dirs if not self.should_ignore_folder(d)]
            
            if root == self.selected_directory:
                continue
                
            parent_path = os.path.dirname(root)
            parent_id = self.path_to_id.get(parent_path)
            
            if parent_id is not None:
                dir_name = os.path.basename(root)
                if not self.should_ignore_folder(dir_name):
                    dir_id = self.treeview.insert(parent_id, "end", text=dir_name, open=False, values=("☐",))
                    self.path_to_id[root] = dir_id
                    self.id_to_path[dir_id] = root
                    
                    for file in files:
                        file_id = self.treeview.insert(dir_id, "end", text=file, values=("☐",))
                        file_path = os.path.join(root, file)
                        self.id_to_path[file_id] = file_path
                        
                    self.processed_items += len(files) + 1
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
        """Generates the formatted directory structure with file contents after."""
        checked_paths = self.get_checked_items()
        if not checked_paths:
            messagebox.showwarning("Warning", "No items were selected.")
            return
        
        # Create initial structure with root directory
        root_name = os.path.basename(self.selected_directory)
        directory_tree = {root_name: {}}
        
        # Build the tree structure
        for path in checked_paths:
            rel_path = os.path.relpath(path, self.selected_directory)
            parts = rel_path.split(os.sep)
            
            current = directory_tree[root_name]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    if os.path.isfile(path) and self.should_include_file_content(path):
                        # Store tuple of (rel_path, content) instead of just content
                        current[part] = (rel_path, self.read_file_content(path))
                    else:
                        current[part] = {}
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        # Generate structure and content separately
        structure, content = self.format_structure(directory_tree)
        
        # Combine structure and content with separators
        full_text = structure
        if content.strip():
            full_text += "\n\n# File Contents\n\n"
            full_text += content
        
        self.structure_text = full_text
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, self.structure_text)
        self.text_area.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)
        self.copy_button.config(state=tk.NORMAL)

    def format_structure(self, tree, indent="", include_content=True):
        """Formats the directory structure and returns tuple of (structure, content)"""
        structure = ""
        content = ""
        files_content = []
        
        keys = list(tree.keys())
        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            branch = "└── " if is_last else "├── "
            spacer = "    " if is_last else "│   "
            
            # Add item to structure
            structure += f"{indent}{branch}{key}\n"
            
            if isinstance(tree[key], dict):
                # Recurse for directories
                sub_structure, sub_content = self.format_structure(
                    tree[key], 
                    indent + spacer, 
                    include_content
                )
                structure += sub_structure
                if sub_content:
                    files_content.append(sub_content)
            elif isinstance(tree[key], tuple):
                # It's a file with content (rel_path, content)
                rel_path, file_content = tree[key]
                if file_content.strip():
                    files_content.append(f"# {rel_path}\n{file_content}\n")
        
        content = "\n".join(files_content)
        return structure, content

    def save_structure(self):
        if not self.structure_text:
            messagebox.showerror("Error", "No structure generated to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.structure_text)
            messagebox.showinfo("Success", f"Structure saved to: {file_path}")

    def copy_text(self, text_widget):
        """Copy the content of a text widget to clipboard"""
        self.clipboard_clear()
        text = text_widget.get("1.0", tk.END).strip()
        if text:
            self.clipboard_append(text)
            messagebox.showinfo("Success", "Text copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "No text to copy!")

if __name__ == "__main__":
    root = tk.Tk()
    app = DirectoryStructureApp(root)
    root.mainloop()