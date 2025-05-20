import tkinter as tk
from tkinter import filedialog, messagebox
import re
import os

# Handle headless environments
try:
    from pyvirtualdisplay import Display
    if os.system('which Xvfb > /dev/null 2>&1') == 0:
        display = Display(visible=0, size=(1280, 720))
        display.start()
    else:
        print("Warning: Xvfb not found. Ensure a display server is available.")
except ImportError:
    print("Warning: pyvirtualdisplay not installed. Ensure a display server is available.")

class PythonToCConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Python to C Converter")
        self.root.geometry("1000x600")
        self.root.configure(bg="white")  # Changed root bg to white for consistency

        # Variables
        self.python_content = ""

        # Create UI with scrollbar
        self.setup_ui()

    def setup_ui(self):
        # Create a canvas with a scrollbar
        self.canvas = tk.Canvas(self.root, bg="white")  # Changed bg to white to remove blue line
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white", padx=20, pady=20)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Title
        title = tk.Label(self.scrollable_frame, text="Python to C Converter", font=("Arial", 20, "bold"), bg="white", fg="#1f2937")
        title.pack(pady=10)

        # File upload
        file_frame = tk.Frame(self.scrollable_frame, bg="white")
        file_frame.pack(fill="x", pady=10)
        tk.Label(file_frame, text="Upload Python File (.py)", font=("Arial", 12, "bold"), bg="white", fg="#374151").pack(side="left")
        upload_btn = tk.Button(file_frame, text="Browse", command=self.upload_file, bg="#2563eb", fg="white", font=("Arial", 10), padx=10, pady=5)
        upload_btn.pack(side="left", padx=10)

        # Text areas
        text_frame = tk.Frame(self.scrollable_frame, bg="white")
        text_frame.pack(fill="both", expand=True, pady=10)

        # Python code area
        python_label = tk.Label(text_frame, text="Python Code", font=("Arial", 12, "bold"), bg="white", fg="#374151")
        python_label.pack(anchor="w")
        self.python_text = tk.Text(text_frame, height=15, bg="#1f2937", fg="#e5e7eb", font=("Courier New", 10), insertbackground="white")
        self.python_text.pack(fill="x", pady=5)
        self.python_text.config(state="disabled")

        # C code area
        c_label = tk.Label(text_frame, text="C Code", font=("Arial", 12, "bold"), bg="white", fg="#374151")
        c_label.pack(anchor="w", pady=(10, 0))
        self.c_text = tk.Text(text_frame, height=15, bg="#1f2937", fg="#e5e7eb", font=("Courier New", 10), insertbackground="white")
        self.c_text.pack(fill="x", pady=5)
        self.c_text.config(state="disabled")

        # Buttons
        btn_frame = tk.Frame(self.scrollable_frame, bg="white")
        btn_frame.pack(pady=10)
        self.convert_btn = tk.Button(btn_frame, text="Convert to C", command=self.convert, bg="#2563eb", fg="white", font=("Arial", 12), padx=20, pady=10, state="disabled")
        self.convert_btn.pack(side="left", padx=10)
        self.save_btn = tk.Button(btn_frame, text="Save C File", command=self.save_file, bg="#16a34a", fg="white", font=("Arial", 12), padx=20, pady=10, state="disabled")
        self.save_btn.pack(side="left", padx=10)

        # Status label
        self.status = tk.Label(self.scrollable_frame, text="", font=("Arial", 10), bg="white", fg="#4b5563")
        self.status.pack(pady=5)

        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
        if file_path:
            if not file_path.endswith('.py'):
                self.status.config(text="Please upload a .py file.")
                return
            try:
                with open(file_path, 'r') as file:
                    self.python_content = file.read()
                self.python_text.config(state="normal")
                self.python_text.delete(1.0, tk.END)
                self.python_text.insert(tk.END, self.python_content)
                self.python_text.config(state="disabled")
                self.convert_btn.config(state="normal")
                self.status.config(text="File loaded. Ready to convert!")
            except Exception as e:
                self.status.config(text=f"Error loading file: {str(e)}")

    def python_to_c(self, python_code):
        c_code = '#include <stdio.h>\n#include <math.h>\n#include <string.h>\n\n'
        lines = python_code.split('\n')
        indent_level = 0
        in_function = False
        functions = []
        main_code = ['int main() {\n']
        main_indent_level = 1
        variables = {}  # Track variable types

        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()
            if not line:
                continue

            indent = '    ' * indent_level
            main_indent = '    ' * main_indent_level

            # Detect unsupported constructs
            if any(keyword in line for keyword in ['class ', 'import ', 'try:', 'except ', 'with ', 'lambda ']):
                raise ValueError(f"Unsupported construct at line {line_num}: {line.strip()}. Classes, imports, try-except, with, and lambdas are not supported.")

            # Handle function definitions
            if line.strip().startswith('def '):
                match = re.match(r'def (\w+)\((.*?)\):', line.strip())
                if match:
                    func_name, params = match.groups()
                    param_list = [p.strip() for p in params.split(',') if p.strip()]
                    c_params = ', '.join(f'int {p}' for p in param_list)  # Default to int for simplicity
                    c_code += f'int {func_name}({c_params}) {{\n'
                    in_function = True
                    indent_level += 1
                    functions.append(func_name)
                    continue

            # Handle return statements
            if in_function and line.strip().startswith('return '):
                return_val = line.strip()[7:].rstrip(';')
                # Check if returning a string literal
                if return_val.startswith('"') or return_val.startswith("'"):
                    c_code += f'{indent}return {return_val};\n'
                else:
                    c_code += f'{indent}return {return_val};\n'
                continue

            # Handle if statements
            if line.strip().startswith('if '):
                condition = re.match(r'if (.*):', line.strip())
                if condition:
                    if in_function:
                        c_code += f'{indent}if ({condition.group(1)}) {{\n'
                    else:
                        main_code.append(f'{main_indent}if ({condition.group(1)}) {{\n')
                    indent_level += 1 if in_function else 0
                    main_indent_level += 1 if not in_function else 0
                    continue

            # Handle elif statements
            if line.strip().startswith('elif '):
                condition = re.match(r'elif (.*):', line.strip())
                if condition:
                    if in_function:
                        c_code += f'{indent}}} else if ({condition.group(1)}) {{\n'
                    else:
                        main_code.append(f'{main_indent}}} else if ({condition.group(1)}) {{\n')
                    continue

            # Handle else statements
            if line.strip() == 'else:':
                if in_function:
                    c_code += f'{indent}}} else {{\n'
                else:
                    main_code.append(f'{main_indent}}} else {{\n')
                indent_level += 1 if in_function else 0
                main_indent_level += 1 if not in_function else 0
                continue

            # Handle while loops
            if line.strip().startswith('while '):
                condition = re.match(r'while (.*):', line.strip())
                if condition:
                    if in_function:
                        c_code += f'{indent}while ({condition.group(1)}) {{\n'
                    else:
                        main_code.append(f'{main_indent}while ({condition.group(1)}) {{\n')
                    indent_level += 1 if in_function else 0
                    main_indent_level += 1 if not in_function else 0
                    continue

            # Handle end of block
            if not line.strip() or (line.strip() and not line.strip().startswith(('if ', 'elif ', 'else:', 'while ', 'def ', 'return '))):
                if in_function and indent_level > 0:
                    indent_level -= 1
                    c_code += '    ' * indent_level + '}\n\n'
                    in_function = False
                elif not in_function and main_indent_level > 1:
                    main_indent_level -= 1
                    main_code.append('    ' * main_indent_level + '}\n')

            # Handle variable assignments with input
            if 'input(' in line:
                match = re.match(r'(\w+)\s*=\s*(?:int|float|str)?\(input\((.*?)\)\)', line.strip())
                if match:
                    var_name, prompt = match.groups()
                    prompt = prompt.strip('"\'')
                    if 'int(' in line:
                        variables[var_name] = 'int'
                        main_code.append(f'{main_indent}int {var_name};\n')
                        main_code.append(f'{main_indent}printf("{prompt}: ");\n')
                        main_code.append(f'{main_indent}scanf("%d", &{var_name});\n')
                    elif 'float(' in line:
                        variables[var_name] = 'float'
                        main_code.append(f'{main_indent}float {var_name};\n')
                        main_code.append(f'{main_indent}printf("{prompt}: ");\n')
                        main_code.append(f'{main_indent}scanf("%f", &{var_name});\n')
                    else:
                        variables[var_name] = 'char*'
                        main_code.append(f'{main_indent}char {var_name}[256];\n')
                        main_code.append(f'{main_indent}printf("{prompt}: ");\n')
                        main_code.append(f'{main_indent}scanf("%s", {var_name});\n')
                    continue

            # Handle regular variable assignments
            if '=' in line and not 'input(' in line:
                var_name, value = map(str.strip, line.split('='))
                if var_name in variables:
                    if in_function:
                        c_code += f'{indent}{var_name} = {value};\n'
                    else:
                        main_code.append(f'{main_indent}{var_name} = {value};\n')
                else:
                    if re.match(r'^\d+$', value):
                        variables[var_name] = 'int'
                        if in_function:
                            c_code += f'{indent}int {var_name} = {value};\n'
                        else:
                            main_code.append(f'{main_indent}int {var_name} = {value};\n')
                    elif re.match(r'^\d+\.\d+$', value):
                        variables[var_name] = 'float'
                        if in_function:
                            c_code += f'{indent}float {var_name} = {value};\n'
                        else:
                            main_code.append(f'{main_indent}float {var_name} = {value};\n')
                    elif value.startswith('"') or value.startswith("'"):
                        variables[var_name] = 'char*'
                        if in_function:
                            c_code += f'{indent}char* {var_name} = {value};\n'
                        else:
                            main_code.append(f'{main_indent}char* {var_name} = {value};\n')
                    else:
                        variables[var_name] = 'int'  # Default to int for expressions
                        if in_function:
                            c_code += f'{indent}int {var_name} = {value};\n'
                        else:
                            main_code.append(f'{main_indent}int {var_name} = {value};\n')
                continue

            # Handle list creation (basic integer lists)
            if '=' in line and '[' in line and ']' in line:
                var_name, value = map(str.strip, line.split('='))
                if re.match(r'\[\d+(,\s*\d+)*\]', value):
                    items = value.strip('[]').split(',')
                    items = [item.strip() for item in items]
                    variables[var_name] = 'int[]'
                    size = len(items)
                    if in_function:
                        c_code += f'{indent}int {var_name}[{size}] = {{{", ".join(items)}}};\n'
                    else:
                        main_code.append(f'{main_indent}int {var_name}[{size}] = {{{", ".join(items)}}};\n')
                    continue
                else:
                    raise ValueError(f"Unsupported list type at line {line_num}: {line.strip()}. Only integer lists are supported.")

            # Handle f-string print statements with indexing
            if line.strip().startswith('print(f"'):
                match = re.match(r'print\(f"(.*?)(?:\{(\w+)(?:\[(-?\d+)\])?\})?(.*?)(?:\{(\w+)(?:\[(-?\d+)\])?\})?(.*?)"\);', line.strip())
                if match:
                    parts = match.groups()
                    format_str = parts[0]
                    var1 = parts[1] if parts[1] else ''
                    index1 = parts[2] if parts[2] else ''
                    mid = parts[3]
                    var2 = parts[4] if parts[4] else ''
                    index2 = parts[5] if parts[5] else ''
                    end = parts[6]
                    format_str = f"{format_str}%s{mid}%s{end}\\n"
                    args = []
                    if var1:
                        if var1 in functions:
                            format_str = format_str.replace('%s', '%d', 1)
                            args.append(f'{var1}()')
                        elif index1:
                            if index1.startswith('-'):
                                idx = f'strlen({var1}) - {index1[1:]}'
                                format_str = format_str.replace('%s', '%c', 1)
                                args.append(f'{var1}[{idx}]')
                            else:
                                format_str = format_str.replace('%s', '%d' if variables.get(var1, 'int') == 'int[]' else '%c', 1)
                                args.append(f'{var1}[{index1}]')
                        else:
                            format_str = format_str.replace('%s', '%d' if variables.get(var1, 'int') == 'int' else '%f' if variables.get(var1) == 'float' else '%s', 1)
                            args.append(var1)
                    if var2:
                        if var2 in functions:
                            format_str = format_str.replace('%s', '%d', 1)
                            args.append(f'{var2}()')
                        elif index2:
                            if index2.startswith('-'):
                                idx = f'strlen({var2}) - {index2[1:]}'
                                format_str = format_str.replace('%s', '%c', 1)
                                args.append(f'{var2}[{idx}]')
                            else:
                                format_str = format_str.replace('%s', '%d' if variables.get(var2, 'int') == 'int[]' else '%c', 1)
                                args.append(f'{var2}[{index2}]')
                        else:
                            format_str = format_str.replace('%s', '%d' if variables.get(var2, 'int') == 'int' else '%f' if variables.get(var2) == 'float' else '%s', 1)
                            args.append(var2)
                    if in_function:
                        c_code += f'{indent}printf("{format_str}", {", ".join(args)});\n'
                    else:
                        main_code.append(f'{main_indent}printf("{format_str}", {", ".join(args)});\n')
                    continue

            # Handle regular print statements
            if line.strip().startswith('print('):
                match = re.match(r'print\((.*?)\)', line.strip())
                if match:
                    content = match.group(1).strip('"\'')
                    if content in functions:
                        if in_function:
                            c_code += f'{indent}printf("%d\\n", {content}());\n'
                        else:
                            main_code.append(f'{main_indent}printf("%d\\n", {content}());\n')
                    else:
                        if in_function:
                            c_code += f'{indent}printf("%s\\n", {content});\n'
                        else:
                            main_code.append(f'{main_indent}printf("%s\\n", {content});\n')
                    continue

        # Close main function
        while main_indent_level > 1:
            main_indent_level -= 1
            main_code.append('    ' * main_indent_level + '}\n')
        main_code.append('    return 0;\n}\n')
        c_code += ''.join(main_code)
        return c_code

    def convert(self):
        if not self.python_content:
            self.status.config(text="No Python code to convert.")
            return

        try:
            c_code = self.python_to_c(self.python_content)
            self.c_text.config(state="normal")
            self.c_text.delete(1.0, tk.END)
            self.c_text.insert(tk.END, c_code)
            self.c_text.config(state="disabled")
            self.save_btn.config(state="normal")
            self.status.config(text="Conversion successful!")
        except Exception as e:
            self.status.config(text=f"Error during conversion: {str(e)}")

    def save_file(self):
        c_code = self.c_text.get(1.0, tk.END).strip()
        if not c_code:
            self.status.config(text="No C code to save.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".c", filetypes=[("C files", "*.c")])
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(c_code)
                self.status.config(text="C file saved successfully!")
            except Exception as e:
                self.status.config(text=f"Error saving file: {str(e)}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = PythonToCConverter(root)
        root.mainloop()
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        try:
            display.stop()
        except NameError:
            pass

