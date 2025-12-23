import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import date

class WeightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("体重管理器")
        self.root.geometry("400x450")
        
        self.init_db()
        
        # --- UI 布局 ---
        # 1. 输入区
        input_frame = tk.LabelFrame(root, text="录入信息", padx=10, pady=10)
        input_frame.pack(padx=10, pady=10, fill="x")
        
        tk.Label(input_frame, text="体重 (kg):").grid(row=0, column=0, padx=5)
        self.weight_entry = tk.Entry(input_frame, width=10)
        self.weight_entry.grid(row=0, column=1, padx=5)
        
        tk.Button(input_frame, text="保存今日", command=self.save_record, bg="#DDDDDD").grid(row=0, column=2, padx=10)
        
        # 2. 列表展示区
        list_frame = tk.LabelFrame(root, text="历史记录 (最近15条)", padx=10, pady=10)
        list_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # 定义表格列
        columns = ('date', 'weight', 'bmi')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        self.tree.heading('date', text='日期')
        self.tree.heading('weight', text='体重(kg)')
        self.tree.heading('bmi', text='备注') # 这里简单用作备注或简单BMI展示
        
        self.tree.column('date', width=100, anchor='center')
        self.tree.column('weight', width=80, anchor='center')
        self.tree.column('bmi', width=120, anchor='center')
        
        self.tree.pack(fill="both", expand=True)
        
        # 3. 统计区
        self.stats_label = tk.Label(root, text="加载中...", font=("Arial", 10, "bold"))
        self.stats_label.pack(pady=10)
        
        self.load_data()

    def init_db(self):
        self.conn = sqlite3.connect('weight_simple.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS records 
                        (date TEXT PRIMARY KEY, weight REAL)''')
        self.conn.commit()

    def save_record(self):
        try:
            w = float(self.weight_entry.get())
            d = date.today().strftime("%Y-%m-%d")
            
            # 插入或更新
            self.c.execute("INSERT OR REPLACE INTO records (date, weight) VALUES (?, ?)", (d, w))
            self.conn.commit()
            
            messagebox.showinfo("成功", f"已记录 {d} 体重: {w}kg")
            self.weight_entry.delete(0, tk.END)
            self.load_data()
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")

    def load_data(self):
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 读取数据
        self.c.execute("SELECT date, weight FROM records ORDER BY date DESC LIMIT 15")
        rows = self.c.fetchall()
        
        if rows:
            latest = rows[0][1]
            first = rows[-1][1]
            diff = latest - first
            self.stats_label.config(text=f"最新: {latest}kg | 相比最早: {diff:+.1f}kg")
        else:
            self.stats_label.config(text="暂无数据")

        for row in rows:
            # 简单展示
            self.tree.insert('', tk.END, values=(row[0], row[1], "-"))

if __name__ == "__main__":
    root = tk.Tk()
    app = WeightApp(root)
    root.mainloop()