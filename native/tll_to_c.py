#!/usr/bin/env python3
"""
TLL → C Minimal Transpiler (PoC)
Native Execution Backend Reality Assessment - Minimal PoC

目标：TLL source → C source → native executable → return 42
仅支持最小子集：fn main() -> int { return <expr>; }
支持：整数常量、基本算术(+ - * /)、局部变量(let)、return
"""

import sys
import re

class TLLToCTranspiler:
    def __init__(self):
        self.output = []
        self.indent = 0

    def emit(self, line):
        self.output.append("    " * self.indent + line)

    def transpile(self, source):
        # 预处理：移除注释
        source = self.remove_comments(source)

        # 解析函数
        functions = self.parse_functions(source)

        # 生成 C 代码
        self.emit("#include <stdio.h>")
        self.emit("#include <stdlib.h>")
        self.emit("")

        for fn in functions:
            self.generate_function(fn)

        return "\n".join(self.output) + "\n"

    def remove_comments(self, source):
        # 移除 // 单行注释
        lines = source.split("\n")
        result = []
        for line in lines:
            # 简单处理：移除 // 后面的内容（不处理字符串中的 //）
            idx = line.find("//")
            if idx >= 0:
                line = line[:idx]
            result.append(line)
        return "\n".join(result)

    def parse_functions(self, source):
        functions = []
        # 匹配 fn name(params) -> return_type { ... }
        pattern = r'fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\w+))?\s*\{(.*?)\}'
        matches = re.finditer(pattern, source, re.DOTALL)
        for m in matches:
            fn = {
                'name': m.group(1),
                'params': m.group(2).strip(),
                'return_type': m.group(3) if m.group(3) else 'void',
                'body': m.group(4).strip()
            }
            functions.append(fn)
        return functions

    def generate_function(self, fn):
        # 转换返回类型
        c_return_type = self.convert_type(fn['return_type'])

        # 转换参数
        c_params = self.convert_params(fn['params'])

        self.emit(f"{c_return_type} {fn['name']}({c_params}) {{")
        self.indent += 1

        # 解析函数体语句
        statements = self.parse_statements(fn['body'])
        for stmt in statements:
            self.generate_statement(stmt)

        self.indent -= 1
        self.emit("}")
        self.emit("")

    def convert_type(self, tll_type):
        type_map = {
            'int': 'int',
            'float': 'double',
            'bool': 'int',
            'string': 'const char*',
            'void': 'void',
        }
        return type_map.get(tll_type, 'int')

    def convert_params(self, params):
        if not params:
            return 'void'
        # 简单处理：name: type → type name
        result = []
        for p in params.split(','):
            p = p.strip()
            if ':' in p:
                name, typ = p.split(':', 1)
                name = name.strip()
                typ = self.convert_type(typ.strip())
                result.append(f"{typ} {name}")
            else:
                result.append(f"int {p}")
        return ', '.join(result)

    def parse_statements(self, body):
        statements = []
        lines = body.split('\n')
        current = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            current += line + " "
            if line.endswith(';') or line.endswith('{') or line.endswith('}'):
                statements.append(current.strip())
                current = ""
        if current.strip():
            statements.append(current.strip())
        return statements

    def generate_statement(self, stmt):
        # let x = expr;
        if stmt.startswith('let ') or stmt.startswith('const '):
            self.generate_let(stmt)
        # return expr;
        elif stmt.startswith('return '):
            self.generate_return(stmt)
        # if (cond) { ... }
        elif stmt.startswith('if '):
            self.generate_if(stmt)
        else:
            # 表达式语句
            self.emit(self.convert_expression(stmt.rstrip(';')) + ";")

    def generate_let(self, stmt):
        # let x = expr;
        m = re.match(r'(?:let|const)\s+(\w+)\s*(?::\s*(\w+))?\s*=\s*(.+);', stmt)
        if m:
            name = m.group(1)
            typ = self.convert_type(m.group(2)) if m.group(2) else 'int'
            expr = self.convert_expression(m.group(3))
            self.emit(f"{typ} {name} = {expr};")
        else:
            # let x; (无初始化)
            m = re.match(r'(?:let|const)\s+(\w+)\s*(?::\s*(\w+))?\s*;', stmt)
            if m:
                name = m.group(1)
                typ = self.convert_type(m.group(2)) if m.group(2) else 'int'
                self.emit(f"{typ} {name};")

    def generate_return(self, stmt):
        # return expr;
        expr = stmt[len('return '):].rstrip(';').strip()
        if expr:
            self.emit(f"return {self.convert_expression(expr)};")
        else:
            self.emit("return;")

    def generate_if(self, stmt):
        # 简单处理 if (cond) { ... }
        m = re.match(r'if\s*\((.+)\)\s*\{(.*)\}', stmt, re.DOTALL)
        if m:
            cond = self.convert_expression(m.group(1))
            self.emit(f"if ({cond}) {{")
            self.indent += 1
            body = m.group(2).strip()
            if body:
                for s in self.parse_statements(body):
                    self.generate_statement(s)
            self.indent -= 1
            self.emit("}")

    def convert_expression(self, expr):
        expr = expr.strip()
        # 模块函数调用 io.println(...)
        if re.match(r'\w+\.\w+\s*\(', expr):
            return self.convert_function_call(expr)
        # 普通函数调用
        if re.match(r'\w+\s*\(', expr):
            return self.convert_function_call(expr)
        # 字符串字面量
        if expr.startswith('"') and expr.endswith('"'):
            return expr
        # 整数/浮点数
        if re.match(r'^-?\d+\.\d+$', expr):
            return expr
        if re.match(r'^-?\d+$', expr):
            return expr
        # true/false
        if expr == 'true':
            return '1'
        if expr == 'false':
            return '0'
        # 算术表达式（简单处理，直接透传，因为 C 语法兼容）
        # 处理 TLL 特定运算符
        expr = expr.replace('**', '/* POW */')  # 临时处理
        # 变量名直接透传
        return expr

    def convert_function_call(self, expr):
        # io.println("...") → printf("...\n")
        m = re.match(r'(\w+)\.(\w+)\s*\((.*)\)', expr)
        if m:
            module = m.group(1)
            func = m.group(2)
            args = m.group(3)
            if module == 'io' and func == 'println':
                if args:
                    # 简单处理：如果是字符串字面量，直接 printf
                    if args.startswith('"') and args.endswith('"'):
                        return f'printf({args[:-1]}\\n")'
                    else:
                        return f'printf("%d\\n", {args})'
                else:
                    return 'printf("\\n")'
            if module == 'io' and func == 'print':
                return f'printf({args})'
        # 普通函数调用
        m = re.match(r'(\w+)\s*\((.*)\)', expr)
        if m:
            return expr  # C 语法兼容
        return expr


def main():
    if len(sys.argv) < 2:
        print("Usage: python tll_to_c.py <input.tll> [output.c]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.tll', '.c')

    with open(input_file, 'r', encoding='utf-8') as f:
        source = f.read()

    transpiler = TLLToCTranspiler()
    c_source = transpiler.transpile(source)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(c_source)

    print(f"Transpiled: {input_file} → {output_file}")


if __name__ == '__main__':
    main()
