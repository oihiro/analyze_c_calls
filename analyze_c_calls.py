#!/usr/bin/env python3
"""
C言語ソースファイルから関数あるいはマクロ呼び出し行を出力するプログラム
"""

import re
import sys
import subprocess
import os
from typing import Set, Tuple, List, Optional

# C言語の予約語
C_RESERVED_WORDS = {
    'if', 'else', 'while', 'for', 'do', 'switch', 'case', 'default',
    'return', 'break', 'continue', 'goto', 'sizeof', 'typedef', 'struct',
    'union', 'enum', 'const', 'volatile', 'static', 'extern', 'auto',
    'register', 'inline', 'restrict', 'signed', 'unsigned', 'int', 'char',
    'short', 'long', 'float', 'double', 'void', 'printf', 'scanf',
    'malloc', 'free', 'memcpy', 'strcpy', 'strlen', 'strcmp', 'strcat',
    'fopen', 'fclose', 'fread', 'fwrite', 'fprintf', 'fscanf', 'assert'
}

def extract_function_calls(file_path: str, start_line_num: int) -> Tuple[Set[str], Set[str]]:
    """
    ファイルから関数/マクロ呼び出しを抽出
    
    Args:
        file_path: ファイルパス
        start_line_num: 検索開始行番号（この次の行から検索）
        
    Returns:
        (関数呼び出し集合, マクロ呼び出し集合)
    """
    functions = set()
    macros = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return functions, macros
    
    # 関数パターン: (\w+)\s*\(
    func_pattern = re.compile(r'(\w+)\s*\(')
    # マクロパターン: [A-Z_\d]+（最初は大文字またはアンダースコア）
    macro_pattern = re.compile(r'([A-Z_][A-Z_\d]*)')
    
    # start_line_numの次の行から開始（start_line_numは0-indexed）
    for i in range(start_line_num + 1, len(lines)):
        line = lines[i]
        
        # 関数本体終了判定: 行の先頭に"}"
        if line.lstrip().startswith('}'):
            break
        
        # コメント行をスキップ（簡易版）
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('/*'):
            continue
        
        # 関数呼び出しを抽出
        for match in func_pattern.finditer(line):
            func_name = match.group(1)
            if func_name not in C_RESERVED_WORDS:
                functions.add(func_name)
        
        # マクロ呼び出しを抽出（マクロ定義行は除外）
        if not stripped.startswith('#define'):
            for match in macro_pattern.finditer(line):
                macro_name = match.group(1)
                # 全て大文字とアンダースコア、数字で構成
                if all(c.isupper() or c == '_' or c.isdigit() for c in macro_name):
                    if len(macro_name) > 1 and macro_name not in C_RESERVED_WORDS:
                        macros.add(macro_name)
    
    return functions, macros


def find_definition(name: str, is_macro: bool = False) -> List[str]:
    """
    grepコマンドで関数/マクロの定義を検索
    
    Args:
        name: 検索する名前
        is_macro: マクロか関数か
        
    Returns:
        grep結果のリスト
    """
    try:
        if is_macro:
            # マクロ定義: #define \w+ で、\w+ の部分が検索名と一致
            pattern = r'#define\s+' + re.escape(name) + r'(\s|$)'
            grep_cmd = ['grep', '-rn', '--include=*.c', '--include=*.cpp', '--include=*.h',
                       '-E', pattern, '.']
        else:
            # 関数定義: (\w+)\s*\([^\(]*\)\s*$ で、(\w+)の部分が検索名と一致
            pattern = re.escape(name) + r'\s*\([^\(]*\)\s*$'
            grep_cmd = ['grep', '-rn', '--include=*.c', '--include=*.cpp', '--include=*.h',
                       '-E', pattern, '.']
        
        result = subprocess.run(
            grep_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        return [line for line in lines if line]
    except Exception as e:
        print(f"Error running grep: {e}", file=sys.stderr)
        return []


def parse_grep_output(grep_line: str) -> Optional[Tuple[str, int]]:
    """
    grep出力をパースしてファイルパスと行番号を抽出
    
    Args:
        grep_line: grepの出力行
        
    Returns:
        (ファイルパス, 行番号) またはNone
    """
    # フォーマット: ファイルパス:行番号:内容
    match = re.match(r'^([^:]+):(\d+):', grep_line)
    if match:
        return (match.group(1), int(match.group(2)) - 1)  # 0-indexedに変換
    return None


def analyze_calls(func_name: str, file_path: str, line_num: int, depth: int = 0, visited: Optional[Set[Tuple[str, str, int]]] = None) -> None:
    """
    関数呼び出しを再帰的に分析
    
    Args:
        func_name: 関数名
        file_path: ファイルパス
        line_num: 関数定義行の行番号（0-indexed）
        depth: 再帰の深さ
        visited: 既に処理した(関数名, ファイル, 行番号)の集合
    """
    if visited is None:
        visited = set()
    
    # 無限ループ防止
    key = (func_name, file_path, line_num)
    if key in visited:
        return
    visited.add(key)
    
    # 呼び出しを抽出（line_numは関数定義行）
    functions, macros = extract_function_calls(file_path, line_num)
    
    # 重複を排除した呼び出し先
    all_calls = functions | macros
    
    # 自分自身の呼び出しを除外
    all_calls.discard(func_name)
    
    # 出力済みの呼び出しを追跡（同じ関数で複数回出力しない）
    if not hasattr(analyze_calls, 'output_cache'):
        analyze_calls.output_cache = {}
    
    cache_key = (func_name, file_path, line_num)
    if cache_key not in analyze_calls.output_cache:
        analyze_calls.output_cache[cache_key] = set()
    
    # マクロ呼び出しの処理（再帰なし、表示のみ）
    for macro_name in sorted(macros):
        if macro_name not in analyze_calls.output_cache[cache_key]:
            print(f"{func_name} {macro_name}")
            analyze_calls.output_cache[cache_key].add(macro_name)
    
    # 関数呼び出しの処理（再帰的に分析）
    for func_call_name in sorted(functions):
        if func_call_name not in analyze_calls.output_cache[cache_key]:
            # 出力：呼び出し元と呼び出し先をスペース区切り
            print(f"{func_name} {func_call_name}")
            analyze_calls.output_cache[cache_key].add(func_call_name)
        
        # 関数の場合のみ再帰的に処理
        grep_results = find_definition(func_call_name, is_macro=False)
        
        if not grep_results:
            pass  # 定義が見つからない場合はスキップ
        elif len(grep_results) == 1:
            # 定義が1つ見つかった
            parsed = parse_grep_output(grep_results[0])
            if parsed:
                new_file_path, new_line_num = parsed
                analyze_calls(func_call_name, new_file_path, new_line_num, depth + 1, visited)
        else:
            # 定義が2個以上見つかった
            for grep_line in grep_results:
                print(f"{grep_line}")


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 analyze_c_calls.py <function_name> <file_path> <line_number>", file=sys.stderr)
        sys.exit(1)
    
    func_name = sys.argv[1]
    file_path = sys.argv[2]
    try:
        line_num = int(sys.argv[3]) - 1  # 1-indexedから0-indexedに変換
    except ValueError:
        print("Error: line_number must be an integer", file=sys.stderr)
        sys.exit(1)
    
    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found", file=sys.stderr)
        sys.exit(1)
    
    analyze_calls(func_name, file_path, line_num)


if __name__ == '__main__':
    main()
