import os
import time
import threading
from queue import Queue
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, 
    QProgressBar, QTextEdit, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QTimer

class DirectoryStructureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Directory Structure Generator")
        self.resize(800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)
        
        # Top frame
        top_frame = QWidget()
        top_layout = QHBoxLayout(top_frame)
        self.dir_label = QLabel("No directory selected.")
        self.dir_label.setWordWrap(True)
        self.select_button = QPushButton("Select Directory")
        self.select_button.clicked.connect(self.select_directory)
        top_layout.addWidget(self.dir_label)
        top_layout.addWidget(self.select_button)
        self.main_layout.addWidget(top_frame)
        
        # Status frame
        self.status_frame = QFrame()
        status_layout = QVBoxLayout(self.status_frame)
        self.progress_bar = QProgressBar()
        self.status_label = QLabel()
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.status_label)
        self.main_layout.addWidget(self.status_frame)
        self.status_frame.hide()
        
        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", ""])
        self.tree.header().setStretchLastSection(False)
        self.tree.clicked.connect(self.toggle_check)
        self.main_layout.addWidget(self.tree)
        
        # Bottom frame
        bottom_frame = QWidget()
        bottom_layout = QVBoxLayout(bottom_frame)
        self.generate_button = QPushButton("Generate Structure")
        self.generate_button.clicked.connect(self.generate_structure)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.save_button = QPushButton("Save Structure")
        self.save_button.clicked.connect(self.save_structure)
        self.save_button.setEnabled(False)
        
        bottom_layout.addWidget(self.generate_button)
        bottom_layout.addWidget(self.text_area)
        bottom_layout.addWidget(self.save_button)
        self.main_layout.addWidget(bottom_frame)
        
        # Initialize variables
        self.selected_directory = None
        self.structure_text = None
        self.path_to_item = {}
        self.item_to_path = {}
        self.total_items = 0
        self.processed_items = 0
        self.queue = Queue()
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_queue)

    def update_progress(self, value, status_text=""):
        self.progress_bar.setValue(int(value))
        if status_text:
            self.status_label.setText(status_text)

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
        root_item = QTreeWidgetItem([root_name, "☐"])
        self.tree.addTopLevelItem(root_item)
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.selected_directory)  # Store path in item

        for root, dirs, files in os.walk(self.selected_directory):
            parent_path = root
            parent_item = self.path_to_item.get(parent_path)

            if parent_item is not None:
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    dir_item = QTreeWidgetItem([dir_name, "☐"])
                    parent_item.addChild(dir_item)
                    dir_item.setData(0, Qt.ItemDataRole.UserRole, dir_path)  # Store path in item
                    self.path_to_item[dir_path] = dir_item

                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    file_item = QTreeWidgetItem([file_name, "☐"])
                    parent_item.addChild(file_item)
                    file_item.setData(0, Qt.ItemDataRole.UserRole, file_path)  # Store path in item

                self.processed_items += len(dirs) + len(files)
                progress = (self.processed_items / self.total_items) * 100
                self.queue.put(('progress', progress))
                self.queue.put(('status', f"Processed {self.processed_items} of {self.total_items} items"))
                time.sleep(0.001)

        self.queue.put(('done', None))

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                
                if msg_type == 'progress':
                    self.update_progress(data)
                elif msg_type == 'status':
                    self.status_label.setText(data)
                elif msg_type == 'done':
                    self.status_frame.hide()
                    self.timer.stop()
                    return
                
        except Exception:
            pass

    def select_directory(self):
        self.selected_directory = QFileDialog.getExistingDirectory(self)
        if self.selected_directory:
            self.dir_label.setText(f"Selected Directory: {self.selected_directory}")
            
            self.tree.clear()
            self.path_to_item.clear()
            self.item_to_path.clear()
            
            self.status_frame.show()
            self.update_progress(0, "Initializing...")
            
            threading.Thread(target=self.process_directory, daemon=True).start()
            self.timer.start(100)
        else:
            QMessageBox.warning(self, "Warning", "No directory was selected.")

    def toggle_check(self, index):
        item = self.tree.currentItem()
        if item and index.column() == 1:
            current_state = item.text(1)
            new_state = "☐" if current_state == "☑" else "☑"
            item.setText(1, new_state)
            self.toggle_children(item, new_state)
            self.update_parent_state(item.parent())

    def toggle_children(self, item, state):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setText(1, state)
            self.toggle_children(child, state)

    def update_parent_state(self, parent):
        if parent:
            child_states = [parent.child(i).text(1) for i in range(parent.childCount())]
            if all(state == "☑" for state in child_states):
                parent.setText(1, "☑")
            elif all(state == "☐" for state in child_states):
                parent.setText(1, "☐")
            else:
                parent.setText(1, "☑")
            self.update_parent_state(parent.parent())

    def get_checked_items(self):
        checked_items = []
        def collect_checked(item):
            if item.text(1) == "☑":
                path = item.data(0, Qt.ItemDataRole.UserRole)  # Retrieve path from item
                if path:
                    checked_items.append(path)
            for i in range(item.childCount()):
                collect_checked(item.child(i))
        
        root = self.tree.topLevelItem(0)
        if root:
            collect_checked(root)
        return checked_items

    def generate_structure(self):
        checked_paths = self.get_checked_items()
        if not checked_paths:
            QMessageBox.warning(self, "Warning", "No items were selected.")
            return
        
        root_name = os.path.basename(self.selected_directory)
        directory_tree = {root_name: {}}
        
        for path in checked_paths:
            rel_path = os.path.relpath(path, self.selected_directory)
            parts = rel_path.split(os.sep)
            
            current = directory_tree[root_name]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    if part not in current:
                        current[part] = {}
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        self.structure_text = self.format_structure(directory_tree)
        self.text_area.setPlainText(self.structure_text)
        self.save_button.setEnabled(True)

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
            QMessageBox.critical(self, "Error", "No structure generated to save.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Structure", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.structure_text)
            QMessageBox.information(self, "Success", f"Structure saved to: {file_path}")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = DirectoryStructureApp()
    window.show()
    sys.exit(app.exec())