import tkinter as tk
from tkinter import messagebox, filedialog
from fractions import Fraction
import random


class MathGeneratorGUI:  # 初始化与界面组件
    def __init__(self, master):
        self.master = master
        master.title("四则运算题目生成器") # 设置窗口标题
        master.geometry("300x250+700+200")
        self.frac_var = tk.BooleanVar()   # 初始化真分数复选框变量
        self.create_widgets()  # 调用创建界面组件方法

    def create_widgets(self): # 创建界面组件
        # 创建输入组件
        tk.Label(self.master, text="题目数量 (n):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.n_entry = tk.Entry(self.master)
        self.n_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.master, text="数值范围 (r):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.r_entry = tk.Entry(self.master)
        self.r_entry.grid(row=1, column=1, padx=10, pady=5)

        # 真分数复选框
        self.frac_check = tk.Checkbutton(
            self.master,
            text="包含真分数",
            variable=self.frac_var
        )
        self.frac_check.grid(row=2, column=0, columnspan=2, pady=5)

        # 创建生成按钮
        self.generate_btn = tk.Button(
            self.master,
            text="生成题目",
            command=self.generate,
            bg="#4CAF50",
            fg="white"
        )
        self.generate_btn.grid(row=3, column=0, columnspan=3, pady=20)

        # 创建批改按钮
        self.grade_btn = tk.Button(
            self.master,
            text="批改答案",
            command=self.grade_answers,
            bg="#2196F3",
            fg="white"
        )
        self.grade_btn.grid(row=5, column=0, columnspan=3, pady=10)

        # 创建状态标签
        self.status_label = tk.Label(self.master, text="")
        self.status_label.grid(row=4, column=0, columnspan=2)

    def generate_expression(self, remaining_ops, range_limit, allow_fraction, generated):
        MAX_RETRIES = 100
        for _ in range(MAX_RETRIES):
            try:
                if remaining_ops == 0:
                    # 生成原子表达式（单个数字）
                    # 递归终止条件（最低一层，都是数字）
                    num = self.generate_number(range_limit, allow_fraction)
                    expr = str(num)
                    if expr in generated:
                        continue
                    generated.add(expr)
                    return expr, num

                op = random.choice(['+', '-', '×', '÷'])
                left_ops = random.randint(0, remaining_ops - 1)
                right_ops = remaining_ops - 1 - left_ops

                left_exp, left_val = self.generate_expression(left_ops, range_limit, allow_fraction, generated)
                right_exp, right_val = self.generate_expression(right_ops, range_limit, allow_fraction, generated)

                # 生成左右子树立即规范化
                left_exp = self.normalize_expression(left_exp)
                right_exp = self.normalize_expression(right_exp)

                if op == '-' and left_val < right_val:
                    left_exp, right_exp = right_exp, left_exp
                    left_val, right_val = right_val, left_val

                if op == '÷':
                    for _ in range(MAX_RETRIES):
                        if right_val != 0 and not (allow_fraction and (left_val / right_val).denominator == 1):
                            break
                        right_exp, right_val = self.generate_expression(right_ops, range_limit, allow_fraction,
                                                                        generated)
                    else:
                        continue

                # 按数值排序操作数
                if op in ['+', '×']:
                    if left_val > right_val:
                        left_exp, right_exp = right_exp, left_exp
                        left_val, right_val = right_val, left_val
                    expr = f"{left_exp} {op} {right_exp}"
                else:
                    expr = f"{left_exp} {op} {right_exp}"

                if remaining_ops > 1:
                    expr = f"({expr})"

                # 直接返回规范化后的表达式
                if expr in generated:
                    continue
                generated.add(expr)

                value = self.calculate(op, left_val, right_val)
                return expr, value

            except (ValueError, ZeroDivisionError):
                continue
        raise RuntimeError(f"无法生成合法表达式，建议扩大数值范围（当前r={range_limit}）")

    def normalize_expression(self, expr): #让所有表达式规范化，便于查重
        # 移除所有括号
        expr = expr.replace('(', '').replace(')', '')

        def sort_sub_expressions(e):
            # 递归拆分表达式并排序
            if '×' in e or '÷' in e:
                # 处理乘除优先
                parts = []
                current = []
                ops = []
                for c in e:
                    if c in ['×', '÷']:
                        parts.append(''.join(current).strip())
                        ops.append(c)
                        current = []
                    else:
                        current.append(c)
                parts.append(''.join(current).strip())

                # 对乘法项排序（数值从小到大）
                for i in range(len(parts)):
                    if i < len(ops) and ops[i] == '×':
                        parts[i] = self.normalize_expression(parts[i])
                        parts[i + 1] = self.normalize_expression(parts[i + 1])
                        # 按数值排序
                        left = self._parse_number(parts[i])
                        right = self._parse_number(parts[i + 1])
                        if left > right:
                            parts[i], parts[i + 1] = parts[i + 1], parts[i]
                # 重组表达式
                sorted_expr = parts[0]
                for i in range(len(ops)):
                    sorted_expr += f' {ops[i]} {parts[i + 1]}'
                return sorted_expr
            else:
                # 处理加法
                add_parts = e.split('+')
                # 转换为数值排序
                add_nums = [self._parse_number(p) for p in add_parts]
                sorted_parts = sorted(zip(add_nums, add_parts), key=lambda x: x[0])
                return '+'.join([p[1] for p in sorted_parts])

        return sort_sub_expressions(expr)

    def _parse_number(self, expr):
        # 将表达式解析为数值（仅处理简单数字）
        if '×' in expr or '+' in expr:
            return 0  # 复杂表达式不参与排序（递归已处理）
        if '/' in expr:
            return float(Fraction(expr))
        else:
            return int(expr)


    def generate_number(self, range_limit, allow_fraction):
        # 生成自然数或真分数（概率各50%）
        if allow_fraction and random.random() < 0.5:
            denominator = random.randint(2, range_limit)
            numerator = random.randint(1, denominator - 1)
            return Fraction(numerator, denominator)
        else:
            return Fraction(random.randint(0, range_limit - 1), 1)

    def calculate(self, op, a, b):
        return {
            '+': a + b,
            '-': a - b,
            '×': a * b,
            '÷': a / b
        }[op]

    def _format_answer(self, value):
        # 答案格式化
        if value.denominator == 1:
            return str(value.numerator)
        whole = value.numerator // value.denominator
        numerator = value.numerator % value.denominator
        return f"{whole}'{numerator}/{value.denominator}" if whole else f"{numerator}/{value.denominator}"


    def validate_input(self):
        # 输入验证
        try:
            n = int(self.n_entry.get())
            r = int(self.r_entry.get())
            if n <= 0 or r <= 3:  # 扩大最小范围限制
                raise ValueError
            return n, r
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效参数：\nn必须>0且为整数\nr必须≥4且为整数")
            return None

    def generate(self):
        # 生成式子
        params = self.validate_input()
        if not params: return

        n, r = params
        generated = set()  # 使用集合存储规范化后的表达式
        try:
            with open("Exercises.txt", "w", encoding="utf-8") as ex_file, open("Answers.txt", "w") as ans_file:

                count = 0
                while count < n:
                    try:
                        # 生成并写入题目
                        expr, value = self.generate_expression(3, r, self.frac_var.get(), generated)
                        ex_file.write(f"[{count + 1}] {expr} =\n")
                        ans_file.write(f"[{count + 1}] {self._format_answer(value)}\n")
                        count += 1
                    except RuntimeError as e:
                        if "建议扩大数值范围" in str(e):
                            messagebox.showerror("参数错误", str(e))
                            break
                        continue

            # 更新状态
            self.status_label.config(text=f"成功生成{count}/{n}题",
                                     fg="green" if count == n else "orange")
            if count == n:
                messagebox.showinfo("完成", "题目和答案已保存到当前目录")

        except Exception as e:
            messagebox.showerror("系统错误", f"生成失败：{str(e)}")
            self.status_label.config(text="生成失败", fg="red")

    def grade_answers(self):
        # 批改功能
        try:
            # 读取正确答案
            correct_answers = self._read_answer_file("Answers.txt")
            # 选择用户答案文件
            user_file = filedialog.askopenfilename(title="选择学生答案文件")
            if not user_file: return
            user_answers = self._read_answer_file(user_file)

            # 比对答案
            correct, wrong = [], []
            # 处理用户答案
            for num in user_answers:
                if num in correct_answers:
                    if user_answers[num] == correct_answers[num]:
                        correct.append(num)
                    else:
                        wrong.append(num)
                else:
                    wrong.append(num)
            # 处理未作答题目
            for num in correct_answers:
                if num not in user_answers:
                    wrong.append(num)

            # 写入结果
            with open("Grade.txt", "w", encoding="utf-8") as f:
                with open("Grade.txt", "w", encoding="utf-8") as f:
                    f.write(f"Correct: {len(correct)} ({', '.join(map(str, sorted(correct)))})\n")
                    f.write(f"Wrong: {len(wrong)} ({', '.join(map(str, sorted(wrong)))})\n")
                messagebox.showinfo("批改完成", "结果已保存到Grade.txt")

        except Exception as e:
            messagebox.showerror("批改错误", f"文件处理失败：{str(e)}")

    def _read_answer_file(self, filename):
        # 读取答案文件
        answers = {}
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    if line.startswith("[") and "]" in line:
                        bracket_end = line.index("]")
                        num = int(line[1:bracket_end])
                        ans_str = line[bracket_end + 1:].split("=")[0].strip()
                        answers[num] = self._parse_answer(ans_str)
        except FileNotFoundError:
            raise ValueError(f"文件不存在: {filename}")
        return answers

    def _parse_answer(self, ans_str):
        # 解析答案
        ans_str = ans_str.strip()
        try:
            if "'" in ans_str:
                whole, fraction = ans_str.split("'", 1)
                numerator, denominator = map(int, fraction.split('/'))
                return Fraction(int(whole) * denominator + numerator, denominator)
            elif '/' in ans_str:
                return Fraction(*map(int, ans_str.split('/')))
            else:
                return Fraction(int(ans_str), 1)
        except ValueError:
            raise ValueError(f"无效答案格式: {ans_str}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MathGeneratorGUI(root)
    root.mainloop()