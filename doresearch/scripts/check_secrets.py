#!/usr/bin/env python3
"""
安全检查脚本
检查代码中的API密钥泄露和其他安全问题
"""
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Pattern
from dataclasses import dataclass


@dataclass
class SecretPattern:
    """密钥模式定义"""
    name: str
    pattern: Pattern[str]
    description: str
    confidence: str  # high, medium, low


class SecretChecker:
    """密钥检查器"""
    
    def __init__(self):
        self.patterns = [
            SecretPattern(
                name="API Key",
                pattern=re.compile(r'(?i)(?:api[_-]?key|apikey)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']'),
                description="Potential API key in assignment",
                confidence="high"
            ),
            SecretPattern(
                name="DeepSeek API Key",
                pattern=re.compile(r'sk-[a-zA-Z0-9]{32}'),
                description="DeepSeek API key format",
                confidence="high"
            ),
            SecretPattern(
                name="Generic Secret",
                pattern=re.compile(r'(?i)(?:secret|password|token|key)\s*[:=]\s*["\']([a-zA-Z0-9_\-!@#$%^&*()]{8,})["\']'),
                description="Potential secret in assignment",
                confidence="medium"
            ),
            SecretPattern(
                name="AWS Access Key",
                pattern=re.compile(r'AKIA[0-9A-Z]{16}'),
                description="AWS Access Key ID",
                confidence="high"
            ),
            SecretPattern(
                name="Database URL",
                pattern=re.compile(r'(?i)(?:database|db)_?url\s*[:=]\s*["\']([^"\']+://[^"\']+)["\']'),
                description="Database connection string",
                confidence="medium"
            ),
            SecretPattern(
                name="JWT Token",
                pattern=re.compile(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*'),
                description="JWT token",
                confidence="high"
            ),
            SecretPattern(
                name="Private Key",
                pattern=re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----'),
                description="Private key header",
                confidence="high"
            ),
            SecretPattern(
                name="Hash",
                pattern=re.compile(r'(?i)(?:md5|sha1|sha256|sha512)\s*[:=]\s*["\']([a-fA-F0-9]{32,})["\']'),
                description="Potential hash value",
                confidence="low"
            ),
        ]
        
        # 白名单模式 - 这些是可以忽略的
        self.whitelist_patterns = [
            re.compile(r'your-secret-key-here'),  # 占位符
            re.compile(r'dev-secret-key'),        # 开发环境占位符
            re.compile(r'test-api-key'),          # 测试占位符
            re.compile(r'example\.com'),          # 示例域名
            re.compile(r'localhost'),             # 本地地址
            re.compile(r'127\.0\.0\.1'),          # 本地地址
        ]
        
        # 文件类型白名单
        self.allowed_extensions = {'.py', '.yaml', '.yml', '.json', '.toml', '.cfg', '.ini'}
        
        # 目录黑名单
        self.excluded_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.pytest_cache'}
    
    def is_whitelisted(self, match: str) -> bool:
        """检查是否在白名单中"""
        return any(pattern.search(match) for pattern in self.whitelist_patterns)
    
    def check_file(self, filepath: Path) -> List[Tuple[str, int, str, str, str]]:
        """检查单个文件"""
        if filepath.suffix not in self.allowed_extensions:
            return []
        
        if any(excluded in filepath.parts for excluded in self.excluded_dirs):
            return []
        
        findings = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_no, line in enumerate(lines, 1):
                for pattern in self.patterns:
                    matches = pattern.pattern.finditer(line)
                    for match in matches:
                        matched_text = match.group(0)
                        
                        # 跳过白名单项
                        if self.is_whitelisted(matched_text):
                            continue
                        
                        # 跳过注释中的示例
                        stripped_line = line.strip()
                        if stripped_line.startswith('#') and ('example' in stripped_line.lower() or 'todo' in stripped_line.lower()):
                            continue
                        
                        findings.append((
                            pattern.name,
                            line_no,
                            matched_text,
                            pattern.description,
                            pattern.confidence
                        ))
        
        except (UnicodeDecodeError, PermissionError):
            # 跳过二进制文件或无权限文件
            pass
        except Exception as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)
        
        return findings
    
    def check_directory(self, directory: Path) -> Dict[str, List[Tuple[str, int, str, str, str]]]:
        """检查目录中的所有文件"""
        results = {}
        
        for filepath in directory.rglob('*'):
            if filepath.is_file():
                findings = self.check_file(filepath)
                if findings:
                    results[str(filepath)] = findings
        
        return results


def format_findings(results: Dict[str, List[Tuple[str, int, str, str, str]]]) -> None:
    """格式化输出结果"""
    total_findings = sum(len(findings) for findings in results.values())
    
    if total_findings == 0:
        print("✅ No secrets or sensitive information found!")
        return
    
    print(f"🔍 Found {total_findings} potential security issues:")
    print("=" * 60)
    
    # 按置信度分组
    by_confidence = {'high': [], 'medium': [], 'low': []}
    
    for filepath, findings in results.items():
        for finding in findings:
            pattern_name, line_no, matched_text, description, confidence = finding
            by_confidence[confidence].append((filepath, pattern_name, line_no, matched_text, description))
    
    # 输出高置信度问题
    if by_confidence['high']:
        print("\n🚨 HIGH CONFIDENCE ISSUES (require immediate attention):")
        for filepath, pattern_name, line_no, matched_text, description in by_confidence['high']:
            print(f"  {filepath}:{line_no}")
            print(f"    Type: {pattern_name}")
            print(f"    Description: {description}")
            print(f"    Found: {matched_text[:50]}{'...' if len(matched_text) > 50 else ''}")
            print()
    
    # 输出中等置信度问题
    if by_confidence['medium']:
        print("\n⚠️  MEDIUM CONFIDENCE ISSUES (review recommended):")
        for filepath, pattern_name, line_no, matched_text, description in by_confidence['medium']:
            print(f"  {filepath}:{line_no} - {pattern_name}: {description}")
    
    # 输出低置信度问题
    if by_confidence['low']:
        print("\n📝 LOW CONFIDENCE ISSUES (informational):")
        for filepath, pattern_name, line_no, matched_text, description in by_confidence['low']:
            print(f"  {filepath}:{line_no} - {pattern_name}")


def main():
    """主函数"""
    checker = SecretChecker()
    
    if len(sys.argv) > 1:
        # 检查指定文件
        results = {}
        for filepath_str in sys.argv[1:]:
            filepath = Path(filepath_str)
            if filepath.is_file():
                findings = checker.check_file(filepath)
                if findings:
                    results[str(filepath)] = findings
            elif filepath.is_dir():
                dir_results = checker.check_directory(filepath)
                results.update(dir_results)
    else:
        # 检查当前目录
        results = checker.check_directory(Path.cwd())
    
    format_findings(results)
    
    # 如果有高置信度问题，返回错误码
    high_confidence_count = sum(
        len([f for f in findings if f[4] == 'high'])
        for findings in results.values()
    )
    
    if high_confidence_count > 0:
        print(f"\n❌ Found {high_confidence_count} high-confidence security issues!")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()