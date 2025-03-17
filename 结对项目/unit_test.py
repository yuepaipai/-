import unittest
from unittest import mock
from tkinter import Tk
from fractions import Fraction
import random
import tempfile
import os

# 导入待测试的类，假设代码保存在math_generator.py中
from main import MathGeneratorGUI


class TestMathGeneratorGUI(unittest.TestCase):
    def setUp(self):
        self.root = Tk()
        self.app = MathGeneratorGUI(self.root)
        # 设置固定随机种子以保证测试可重复
        random.seed(42)

    def tearDown(self):
        self.root.destroy()

    # 测试输入验证逻辑
    def test_validate_input(self):
        test_cases = [
            (('5', '10'), (5, 10)),  # 有效输入
            (('0', '10'), None),  # n太小
            (('-3', '10'), None),  # 负n值
            (('5', '3'), None),  # r太小
            (('abc', '10'), None),  # 无效n格式
            (('5', 'xyz'), None)  # 无效r格式
        ]

        for inputs, expected in test_cases:
            with self.subTest(inputs=inputs):
                self.app.n_entry.delete(0, 'end')
                self.app.r_entry.delete(0, 'end')
                self.app.n_entry.insert(0, inputs[0])
                self.app.r_entry.insert(0, inputs[1])
                self.assertEqual(self.app.validate_input(), expected)

    # 测试数值生成逻辑
    def test_generate_number(self):
        # 测试整数生成
        num = self.app.generate_number(10, False)
        self.assertEqual(num.denominator, 1)
        self.assertTrue(0 <= num.numerator < 10)

        # 测试真分数生成
        has_fraction = False
        for _ in range(100):
            num = self.app.generate_number(10, True)
            if num.denominator != 1 and 0 < num.numerator < num.denominator:
                has_fraction = True
                break
        self.assertTrue(has_fraction)

    # 测试运算逻辑
    def test_calculate(self):
        test_cases = [
            ('+', Fraction(1, 2), Fraction(1, 2), Fraction(1)),
            ('-', Fraction(3, 2), Fraction(1, 2), Fraction(1)),
            ('×', Fraction(2, 3), Fraction(3, 4), Fraction(1, 2)),
            ('÷', Fraction(3, 4), Fraction(1, 2), Fraction(3, 2))
        ]

        for op, a, b, expected in test_cases:
            with self.subTest(op=op):
                self.assertEqual(self.app.calculate(op, a, b), expected)

    # 测试答案格式化
    def test_format_answer(self):
        test_cases = [
            (Fraction(5, 1), "5"),
            (Fraction(3, 4), "3/4"),
            (Fraction(5, 2), "2'1/2"),
            (Fraction(7, 3), "2'1/3")
        ]

        for value, expected in test_cases:
            with self.subTest(value=value):
                self.assertEqual(self.app._format_answer(value), expected)

    # 测试答案解析
    def test_parse_answer(self):
        test_cases = [
            ("5", Fraction(5, 1)),
            ("3/4", Fraction(3, 4)),
            ("2'1/2", Fraction(5, 2)),
            ("1'3/4", Fraction(7, 4))
        ]

        for ans_str, expected in test_cases:
            with self.subTest(ans_str=ans_str):
                self.assertEqual(self.app._parse_answer(ans_str), expected)

    # 测试表达式规范化
    def test_normalize_expression(self):
        test_cases = [
            ("3+2", "2+3"),
            ("2×3", "3×2"),
            ("(3+5)×2", "2×(5+3)"),
            ("4+1+3", "1+3+4"),
            ("(2+3)×(5+1)", "(2+3)×(1+5)")
        ]

        for expr, expected in test_cases:
            with self.subTest(expr=expr):
                self.assertEqual(
                    self.app.normalize_expression(expr),
                    self.app.normalize_expression(expected)
                )

    # 测试文件生成功能
    def test_file_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # 重定向文件生成路径
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                self.app.n_entry.insert(0, '3')
                self.app.r_entry.insert(0, '40')
                self.app.frac_var.set(True)
                self.app.generate()

                # 验证文件生成
                self.assertTrue(os.path.exists("Exercises.txt"))
                self.assertTrue(os.path.exists("Answers.txt"))

                # 验证题目数量
                with open("Exercises.txt", "r", encoding="utf-8") as f:
                    self.assertEqual(len(f.readlines()), 3)

            finally:
                os.chdir(original_cwd)

    # 测试批改功能
    def test_grading_logic(self):
        # 准备测试文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("[1] 3/4\n[2] 5\n[3] 2'1/2\n")
            user_file = f.name

        try:
            # 生成正确答案
            correct_answers = {
                1: Fraction(3, 4),
                2: Fraction(5, 1),
                3: Fraction(5, 2)
            }

            # 执行批改逻辑
            with mock.patch.object(self.app, '_read_answer_file',
                                   side_effect=[correct_answers, {
                                       1: Fraction(3, 4),
                                       2: Fraction(4, 1),  # 错误答案
                                       3: Fraction(5, 2)
                                   }]):
                self.app.grade_answers()

                # 验证结果文件
                self.assertTrue(os.path.exists("Grade.txt"))
                with open("Grade.txt", "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertIn("Correct: 2", content)
                    self.assertIn("Wrong: 1", content)

        finally:
            os.unlink(user_file)
            if os.path.exists("Grade.txt"):
                os.unlink("Grade.txt")


if __name__ == "__main__":
    unittest.main()