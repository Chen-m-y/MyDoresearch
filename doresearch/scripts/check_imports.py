#!/usr/bin/env python3
"""
导入检查脚本
检查未使用的导入和导入顺序问题
"""
import ast
import sys
import os
from pathlib import Path
from typing import List, Set, Dict, Tuple
from collections import defaultdict


class ImportChecker(ast.NodeVisitor):
    """导入检查器"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.imports: Dict[str, List[int]] = defaultdict(list)  # 导入名称 -> 行号列表
        self.used_names: Set[str] = set()  # 使用的名称
        self.from_imports: Dict[str, List[Tuple[str, int]]] = defaultdict(list)  # 模块 -> [(名称, 行号)]
        self.errors: List[str] = []
    
    def visit_Import(self, node: ast.Import):
        """访问 import 语句"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name].append(node.lineno)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """访问 from ... import 语句"""
        module = node.module or ""
        for alias in node.names:
            if alias.name == "*":
                # 通配符导入，跳过检查
                return
            name = alias.asname if alias.asname else alias.name
            self.from_imports[module].append((name, node.lineno))
            self.imports[name].append(node.lineno)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """访问名称节点"""
        self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """访问属性节点"""
        # 对于 module.function 形式，记录 module 的使用
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)
    
    def check_unused_imports(self):
        """检查未使用的导入"""
        for name, lines in self.imports.items():
            if name not in self.used_names:
                for line in lines:
                    self.errors.append(f"Line {line}: Unused import '{name}'")
    
    def check_import_order(self, content: str):
        """检查导入顺序"""
        lines = content.split('\n')
        import_lines = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                if not stripped.startswith('#'):
                    import_lines.append((i, line))
        
        # 简单的顺序检查：标准库 -> 第三方 -> 本地
        standard_libs = {
            'os', 'sys', 'json', 'datetime', 'time', 'logging', 'threading',
            'sqlite3', 'pathlib', 'typing', 'dataclasses', 'enum', 'abc',
            'contextlib', 'collections', 'functools', 'itertools'
        }
        
        prev_category = 0  # 0: 标准库, 1: 第三方, 2: 本地
        
        for line_no, line in import_lines:
            category = self._get_import_category(line, standard_libs)
            
            if category < prev_category:
                self.errors.append(
                    f"Line {line_no}: Import order violation - "
                    f"should group standard library, third-party, then local imports"
                )
            
            prev_category = max(prev_category, category)
    
    def _get_import_category(self, line: str, standard_libs: Set[str]) -> int:
        """获取导入类别"""
        line = line.strip()
        
        if line.startswith('from '):
            module = line.split()[1].split('.')[0]
        elif line.startswith('import '):
            module = line.split()[1].split('.')[0]
        else:
            return 2
        
        if module in standard_libs:
            return 0  # 标准库
        elif module.startswith('.') or module in ['common', 'services', 'models']:
            return 2  # 本地模块
        else:
            return 1  # 第三方库


def check_file(filepath: Path) -> List[str]:
    """检查单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(filepath))
        checker = ImportChecker(str(filepath))
        checker.visit(tree)
        checker.check_unused_imports()
        checker.check_import_order(content)
        
        return checker.errors
    
    except SyntaxError as e:
        return [f"Syntax error in {filepath}: {e}"]
    except Exception as e:
        return [f"Error processing {filepath}: {e}"]


def main():
    """主函数"""
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:] if f.endswith('.py')]
    else:
        # 默认检查整个项目
        project_root = Path.cwd()
        files = list(project_root.glob('**/*.py'))
        # 排除一些目录
        exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist'}
        files = [f for f in files if not any(part in exclude_dirs for part in f.parts)]
    
    total_errors = 0
    
    for filepath in files:
        errors = check_file(filepath)
        if errors:
            print(f"\n{filepath}:")
            for error in errors:
                print(f"  {error}")
            total_errors += len(errors)
    
    if total_errors == 0:
        print("✅ No import issues found!")
        sys.exit(0)
    else:
        print(f"\n❌ Found {total_errors} import issues")
        sys.exit(1)


if __name__ == "__main__":
    main()