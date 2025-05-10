import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import csv
from collections import defaultdict
from copy import deepcopy

# Hàm CloSpan chính xác với kiểm tra đóng + bỏ mẫu rỗng
def run_clospan(sequences, minsup):
    def support(pattern, database):
        count = 0
        for seq in database:
            if is_subsequence(pattern, seq):
                count += 1
        return count

    def is_subsequence(pattern, sequence):
        i = 0
        for itemset in sequence:
            if i < len(pattern) and set(pattern[i]).issubset(set(itemset)):
                i += 1
        return i == len(pattern)

    def project_database(database, pattern):
        projected = []
        for seq in database:
            proj = []
            matched = False
            for idx, itemset in enumerate(seq):
                if not matched and set(pattern[-1]).issubset(set(itemset)):
                    matched = True
                    proj.extend(seq[idx + 1:])
                elif matched:
                    proj.append(itemset)
            if matched and proj:
                projected.append(proj)
        return projected

    def dfs(pattern, db, results):
        sup = support(pattern, sequences)
        if sup < minsup:
            return
        if pattern:
            results.append((deepcopy(pattern), sup))

        items = defaultdict(int)
        for seq in db:
            seen = set()
            for itemset in seq:
                for item in itemset:
                    if item not in seen:
                        items[item] += 1
                        seen.add(item)

        for item, item_sup in items.items():
            if item_sup >= minsup:
                new_pattern = deepcopy(pattern)
                new_pattern.append([item])
                new_db = project_database(db, new_pattern)
                dfs(new_pattern, new_db, results)

    results = []
    dfs([], sequences, results)

    # Lọc lại chỉ giữ các mẫu tuần tự đóng
    closed_results = []
    for i, (pattern_i, sup_i) in enumerate(results):
        is_closed = True
        for j, (pattern_j, sup_j) in enumerate(results):
            if i != j and sup_i == sup_j and is_subsequence(pattern_i, pattern_j) and not is_subsequence(pattern_j, pattern_i):
                is_closed = False
                break
        if is_closed:
            closed_results.append((pattern_i, sup_i))

    return closed_results
# Lưu ra file CSV định dạng SPMF
def save_result_csv(results):
    with open("result_clospan.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        for pattern, sup in results:
            flat = []
            for itemset in pattern:
                flat.extend(itemset)
                flat.append(-1)
            flat.append(-2)
            writer.writerow(flat + [f'sup={sup}'])

# GUI chính
class CloSpanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CloSpan Sequential Pattern Mining")
        self.root.geometry("850x600")
        self.root.configure(bg="#f2f2f2")
        self.filename = None

        tk.Label(root, text="Dữ liệu SPMF (-1: kết thúc itemset, -2: kết thúc sequence):", bg="#f2f2f2").pack(pady=5)
        self.text_input = scrolledtext.ScrolledText(root, height=10, width=105, font=("Consolas", 10))
        self.text_input.pack(padx=10, pady=5)

        frame = tk.Frame(root, bg="#f2f2f2")
        frame.pack(pady=5)

        tk.Button(frame, text="Chọn file CSV/TXT", command=self.load_file, bg="#87CEEB", width=18).grid(row=0, column=0, padx=5)
        tk.Label(frame, text="MinSup:", bg="#f2f2f2").grid(row=0, column=1, padx=5)
        self.entry_minsup = tk.Entry(frame, width=5)
        self.entry_minsup.insert(0, "2")
        self.entry_minsup.grid(row=0, column=2, padx=5)
        tk.Button(frame, text="Chạy CloSpan", command=self.run_clospan_display, bg="#32CD32", fg="white", width=15).grid(row=0, column=3, padx=10)

        tk.Label(root, text="Kết quả CloSpan:", bg="#f2f2f2").pack(pady=5)
        self.text_output = scrolledtext.ScrolledText(root, height=15, width=105, font=("Consolas", 10))
        self.text_output.pack(padx=10, pady=5)

    def load_file(self):
        self.filename = filedialog.askopenfilename(filetypes=[("CSV and TXT files", "*.csv *.txt")])
        if not self.filename:
            return
        try:
            with open(self.filename, 'r') as f:
                content = f.read().replace(",", " ")
                self.text_input.delete('1.0', tk.END)
                self.text_input.insert(tk.END, content)
            messagebox.showinfo("Thành công", "Đã tải dữ liệu vào ô nhập.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file: {e}")

    def run_clospan_display(self):
        try:
            minsup = int(self.entry_minsup.get())
        except ValueError:
            minsup = 2
            messagebox.showwarning("Cảnh báo", "MinSup không hợp lệ, mặc định là 2.")

        raw_data = self.text_input.get("1.0", tk.END).strip().splitlines()
        sequences = []
        for line in raw_data:
            parts = line.strip().split()
            seq = []
            itemset = []
            for p in parts:
                if p == '-1':
                    if itemset:
                        seq.append(itemset)
                        itemset = []
                elif p == '-2':
                    break
                else:
                    try:
                        itemset.append(int(p))
                    except ValueError:
                        pass
            if itemset:
                seq.append(itemset)
            if seq:
                sequences.append(seq)

        if not sequences:
            messagebox.showerror("Lỗi", "Không có dữ liệu đầu vào hợp lệ.")
            return

        results = run_clospan(sequences, minsup)
        self.text_output.delete("1.0", tk.END)

        if results:
            for pattern, sup in results:
                pattern_str = ' -> '.join(f'({ " ".join(map(str, itemset)) })' for itemset in pattern)
                self.text_output.insert(tk.END, f"{pattern_str}  sup={sup}\n")
            save_result_csv(results)
            messagebox.showinfo("Thành công", "Đã lưu kết quả vào result_clospan.csv")
        else:
            self.text_output.insert(tk.END, "Không có kết quả nào thỏa mãn MinSup.")
            messagebox.showinfo("Thông báo", "Không có kết quả nào thỏa mãn.")

# Chạy ứng dụng
if __name__ == "__main__":
    root = tk.Tk()
    app = CloSpanApp(root)
    root.mainloop()
