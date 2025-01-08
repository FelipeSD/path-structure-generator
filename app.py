import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class DirectoryStructureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Estrutura de Diretórios")
        self.root.geometry("800x600")

        # Widgets principais
        self.dir_label = tk.Label(self.root, text="Nenhum diretório selecionado.", wraplength=700)
        self.dir_label.pack(pady=10)

        self.select_button = tk.Button(self.root, text="Selecionar Diretório", command=self.select_directory)
        self.select_button.pack(pady=5)

        self.tree_frame = tk.Frame(self.root)
        self.tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.treeview = ttk.Treeview(self.tree_frame, columns=("Name"), selectmode="extended")
        self.treeview.heading("#0", text="Nome")
        self.treeview.column("#0", stretch=tk.YES)
        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.treeview.yview)
        self.treeview.configure(yscroll=self.tree_scroll.set)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.generate_button = tk.Button(self.root, text="Gerar Estrutura", command=self.generate_structure, state=tk.DISABLED)
        self.generate_button.pack(pady=5)

        self.text_area = tk.Text(self.root, wrap=tk.WORD, state=tk.DISABLED, height=15, width=70)
        self.text_area.pack(pady=10)

        self.save_button = tk.Button(self.root, text="Salvar Estrutura", command=self.save_structure, state=tk.DISABLED)
        self.save_button.pack(pady=5)

        self.selected_directory = None
        self.structure_text = None
        self.selected_items = set()
        self.path_to_id = {}  # New dictionary to store path-to-id mappings

    def select_directory(self):
        """Permite ao usuário selecionar um diretório."""
        self.selected_directory = filedialog.askdirectory()
        if self.selected_directory:
            self.dir_label.config(text=f"Diretório Selecionado: {self.selected_directory}")
            self.populate_treeview()
            self.generate_button.config(state=tk.NORMAL)
        else:
            messagebox.showwarning("Aviso", "Nenhum diretório foi selecionado.")

    def populate_treeview(self):
        """Popula a Treeview com a estrutura de diretórios e arquivos."""
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
        """Cria um dicionário aninhado a partir de uma lista de partes do caminho."""
        current = {}
        temp = current
        for part in path_parts[:-1]:
            temp[part] = {}
            temp = temp[part]
        temp[path_parts[-1]] = None
        return current

    def merge_dicts(self, dict1, dict2):
        """Mescla dois dicionários aninhados recursivamente."""
        for key in dict2:
            if key in dict1:
                if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                    self.merge_dicts(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
        return dict1

    def generate_structure(self):
        """Gera a estrutura de diretórios formatada no estilo solicitado."""
        self.selected_items = set(self.treeview.selection())
        if not self.selected_items:
            messagebox.showwarning("Aviso", "Nenhum item foi selecionado.")
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
        """Retorna o caminho completo do item selecionado na Treeview."""
        path = []
        while item:
            path.append(self.treeview.item(item, "text"))
            item = self.treeview.parent(item)
        return os.path.join(*reversed(path))

    def format_structure(self, tree, indent="", last=False):
        """Converte a árvore de diretórios em texto no formato solicitado."""
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
        """Salva a estrutura gerada em um arquivo de texto."""
        if not self.structure_text:
            messagebox.showerror("Erro", "Nenhuma estrutura gerada para salvar.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.structure_text)
            messagebox.showinfo("Sucesso", f"Estrutura salva em: {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DirectoryStructureApp(root)
    root.mainloop()