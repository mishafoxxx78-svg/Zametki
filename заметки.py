import customtkinter as ctk
import json
import os
from datetime import datetime
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DATA_FILE = "notes_data.json"

class NotesApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("📝 Мои заметки")
        self.window.geometry("850x550")
        self.window.minsize(700, 450)
        
        self.notes = self.load_notes()
        self.current_note_index = None
        self.filtered_indices = list(range(len(self.notes)))
        self.search_query = ""
        
        self.build_ui()
        self.refresh_notes_list()
        self.window.mainloop()
    
    def load_notes(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    
    def save_notes(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)
    
    def build_ui(self):
        # Левая панель
        left_panel = ctk.CTkFrame(self.window, width=230, corner_radius=0)
        left_panel.pack(side="left", fill="y")
        left_panel.pack_propagate(False)
        
        ctk.CTkLabel(
            left_panel, text="📝 Мои заметки",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 10))
        
        # Поиск
        self.search_entry = ctk.CTkEntry(left_panel, placeholder_text="🔍 Поиск...", width=200)
        self.search_entry.pack(pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        # Список заметок
        self.notes_list_frame = ctk.CTkScrollableFrame(left_panel, width=210, height=350)
        self.notes_list_frame.pack(pady=5, fill="both", expand=True)
        
        ctk.CTkButton(
            left_panel, text="+ Новая заметка", width=200,
            command=self.new_note
        ).pack(pady=15)
        
        # Правая панель
        right_panel = ctk.CTkFrame(self.window, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True, padx=20, pady=15)
        
        # Заголовок
        ctk.CTkLabel(right_panel, text="Заголовок:", anchor="w").pack(fill="x")
        self.title_entry = ctk.CTkEntry(
            right_panel, font=ctk.CTkFont(size=18, weight="bold"), height=40
        )
        self.title_entry.pack(fill="x", pady=(0, 10))
        self.title_entry.bind("<KeyRelease>", self.on_edit)
        
        # Теги
        ctk.CTkLabel(right_panel, text="Теги (через запятую):", anchor="w").pack(fill="x")
        self.tags_entry = ctk.CTkEntry(right_panel, height=30)
        self.tags_entry.pack(fill="x", pady=(0, 10))
        self.tags_entry.bind("<KeyRelease>", self.on_edit)
        
        # Текст заметки
        ctk.CTkLabel(right_panel, text="Содержание:", anchor="w").pack(fill="x")
        self.text_box = ctk.CTkTextbox(right_panel, font=ctk.CTkFont(size=13))
        self.text_box.pack(fill="both", expand=True, pady=(0, 10))
        self.text_box.bind("<KeyRelease>", self.on_edit)
        
        # Нижняя панель с кнопками и датой
        bottom_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        bottom_frame.pack(fill="x")
        
        self.date_label = ctk.CTkLabel(
            bottom_frame, text="", text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        self.date_label.pack(side="left")
        
        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(
            btn_frame, text="💾 Сохранить", width=100,
            command=self.save_current_note
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame, text="📌", width=40,
            fg_color="#555555", hover_color="#777777",
            command=self.toggle_pin
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame, text="🗑️", width=40,
            fg_color="#8B0000", hover_color="#A00000",
            command=self.delete_note
        ).pack(side="left", padx=3)
    
    def clear_right_panel(self):
        self.title_entry.delete(0, "end")
        self.tags_entry.delete(0, "end")
        self.text_box.delete("1.0", "end")
        self.date_label.configure(text="")
    
    def load_note_to_panel(self, index):
        if index is None or index >= len(self.notes):
            self.clear_right_panel()
            return
        note = self.notes[index]
        self.current_note_index = index
        
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, note.get("title", ""))
        
        self.tags_entry.delete(0, "end")
        self.tags_entry.insert(0, ", ".join(note.get("tags", [])))
        
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", note.get("content", ""))
        
        created = note.get("created", "")
        edited = note.get("edited", "")
        date_str = f"Создано: {created}"
        if edited:
            date_str += f" | Изменено: {edited}"
        self.date_label.configure(text=date_str)
    
    def refresh_notes_list(self):
        for widget in self.notes_list_frame.winfo_children():
            widget.destroy()
        
        self.filtered_indices = []
        query = self.search_query.lower()
        
        # Сортировка: закреплённые сверху
        pinned = [i for i, n in enumerate(self.notes) if n.get("pinned")]
        unpinned = [i for i, n in enumerate(self.notes) if not n.get("pinned")]
        
        for idx in pinned + unpinned:
            note = self.notes[idx]
            title = note.get("title", "Без названия")
            tags = " ".join(note.get("tags", []))
            content = note.get("content", "")
            
            if query and query not in title.lower() and query not in tags.lower() and query not in content.lower():
                continue
            
            self.filtered_indices.append(idx)
            
            # Рамка заметки
            note_frame = ctk.CTkFrame(
                self.notes_list_frame, fg_color="#2B2B2B",
                corner_radius=8
            )
            note_frame.pack(pady=2, padx=5, fill="x")
            
            # Заголовок
            pin_icon = "📌 " if note.get("pinned") else ""
            display_title = f"{pin_icon}{title[:30]}{'...' if len(title) > 30 else ''}"
            title_btn = ctk.CTkButton(
                note_frame, text=display_title, anchor="w",
                fg_color="transparent", hover_color="#3B3B3B",
                font=ctk.CTkFont(size=12),
                command=lambda i=idx: self.load_note_to_panel(i)
            )
            title_btn.pack(fill="x")
            
            # Теги
            if note.get("tags"):
                tags_str = " ".join([f"#{t}" for t in note["tags"][:3]])
                ctk.CTkLabel(
                    note_frame, text=tags_str,
                    font=ctk.CTkFont(size=10), text_color="#4A9EFF"
                ).pack(anchor="w", padx=10)
            
            # Дата
            created = note.get("created", "")
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    date_str = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    date_str = created[:16]
                ctk.CTkLabel(
                    note_frame, text=date_str,
                    font=ctk.CTkFont(size=9), text_color="gray"
                ).pack(anchor="w", padx=10, pady=(0, 5))
    
    def on_search(self, event=None):
        self.search_query = self.search_entry.get()
        self.refresh_notes_list()
    
    def on_edit(self, event=None):
        if self.current_note_index is not None:
            self.save_current_note(silent=True)
    
    def new_note(self):
        note = {
            "title": "Новая заметка",
            "tags": [],
            "content": "",
            "created": datetime.now().isoformat(),
            "edited": "",
            "pinned": False
        }
        self.notes.append(note)
        self.save_notes()
        self.current_note_index = len(self.notes) - 1
        self.load_note_to_panel(self.current_note_index)
        self.refresh_notes_list()
        self.title_entry.focus_set()
    
    def save_current_note(self, silent=False):
        if self.current_note_index is None or self.current_note_index >= len(self.notes):
            return
        note = self.notes[self.current_note_index]
        note["title"] = self.title_entry.get()
        tags_raw = self.tags_entry.get()
        note["tags"] = [t.strip().strip("#") for t in tags_raw.split(",") if t.strip()]
        note["content"] = self.text_box.get("1.0", "end-1c")
        note["edited"] = datetime.now().isoformat()
        self.save_notes()
        self.refresh_notes_list()
        if not silent:
            self.date_label.configure(
                text=f"Изменено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
    
    def toggle_pin(self):
        if self.current_note_index is None:
            return
        self.notes[self.current_note_index]["pinned"] = \
            not self.notes[self.current_note_index].get("pinned", False)
        self.save_notes()
        self.refresh_notes_list()
    
    def delete_note(self):
        if self.current_note_index is None:
            return
        title = self.notes[self.current_note_index].get("title", "")
        if messagebox.askyesno("Удаление", f"Удалить заметку «{title}»?"):
            del self.notes[self.current_note_index]
            self.save_notes()
            self.current_note_index = None
            self.clear_right_panel()
            self.refresh_notes_list()

if __name__ == "__main__":
    NotesApp()