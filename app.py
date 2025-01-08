# app.py

import os
import tkinter as tk
from tkinter import filedialog, messagebox
import dpath

class DirectoryStructureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Estrutura de Diretórios")
        self.root.geometry("600x400")
        
        # Widgets principais
        self.dir_label = tk.Label(self.root, text="Nenhum diretório selecionado.", wraplength=500)
        self.dir_label.pack(pady=10)
        
        self.select_button = tk.Button(self.root, text="Selecionar Diretório", command=self.select_directory)
        self.select_button.pack(pady=5)
        
        self.generate_button = tk.Button(self.root, text="Gerar Estrutura", command=self.generate_structure, state=tk.DISABLED)
        self.generate_button.pack(pady=5)
        
        self.text_area = tk.Text(self.root, wrap=tk.WORD, state=tk.DISABLED, height=15, width=70)
        self.text_area.pack(pady=10)
        
        self.save_button = tk.Button(self.root, text="Salvar Estrutura", command=self.save_structure, state=tk.DISABLED)
        self.save_button.pack(pady=5)
        
        self.selected_directory = None
        self.structure_text = None

    def select_directory(self):
        """Permite ao usuário selecionar um diretório."""
        self.selected_directory = filedialog.askdirectory()
        if self.selected_directory:
            self.dir_label.config(text=f"Diretório Selecionado: {self.selected_directory}")
            self.generate_button.config(state=tk.NORMAL)
        else:
            messagebox.showwarning("Aviso", "Nenhum diretório foi selecionado.")
    
    def generate_structure(self):
        """Gera a estrutura de diretórios formatada no estilo solicitado."""
        if not self.selected_directory:
            messagebox.showerror("Erro", "Selecione um diretório primeiro.")
            return
        
        try:
            # Gerando a estrutura de diretórios
            directory_tree = {}
            for root, dirs, files in os.walk(self.selected_directory):
                relative_path = os.path.relpath(root, self.selected_directory)
                if relative_path == ".":
                    relative_path = ""
                for directory in dirs:
                    dpath.new(directory_tree, os.path.join(relative_path, directory), {})
                for file in files:
                    dpath.new(directory_tree, os.path.join(relative_path, file), None)
            
            # Convertendo para texto legível com estilo de estrutura solicitado
            self.structure_text = self.format_structure(directory_tree, prefix=self.selected_directory)
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, self.structure_text)
            self.text_area.config(state=tk.DISABLED)
            self.save_button.config(state=tk.NORMAL)
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar a estrutura: {str(e)}")
    
    def format_structure(self, tree, indent="", last=False, prefix=""):
        """Converte a árvore de diretórios em texto no formato solicitado."""
        result = f"{prefix}/\n" if indent == "" else ""
        keys = list(tree.keys())
        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            branch = "└── " if is_last else "├── "
            spacer = "    " if is_last else "│   "
            path = tree[key]
            result += f"{indent}{branch}{key}\n"
            if isinstance(path, dict):
                result += self.format_structure(path, indent + spacer, last=is_last)
        return result

    def save_structure(self):
        """Salva a estrutura gerada em um arquivo de texto."""
        if not self.structure_text:
            messagebox.showerror("Erro", "Nenhuma estrutura gerada para salvar.")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Arquivos de Texto", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.structure_text)
            messagebox.showinfo("Sucesso", f"Estrutura salva em: {file_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DirectoryStructureApp(root)
    root.mainloop()
