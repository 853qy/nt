#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NautilusTrader Binance 示例代码测试脚本

此脚本用于测试和调试NautilusTrader Binance示例代码
包括语法检查、导入测试、配置验证等

使用方法：
1. 运行脚本: python test_examples.py
2. 测试特定文件: python test_examples.py --file binance_spot_ema_cross.py

注意：
- 请确保已安装NautilusTrader
- 请确保已设置环境变量
"""

import os
import sys
import ast
import subprocess
import argparse
from typing import List, Dict, Any
from pathlib import Path


class ExampleTester:
    """示例代码测试器"""
    
    def __init__(self):
        self.test_results: Dict[str, bool] = {}
        self.example_files = [
            "binance_spot_ema_cross.py",
            "binance_futures_ema_cross.py", 
            "custom_rsi_ema_strategy.py",
            "test_binance_connection.py"
        ]
        
    def print_info(self, message: str):
        """打印信息"""
        print(f"🔍 [INFO] {message}")
        
    def print_success(self, message: str):
        """打印成功信息"""
        print(f"✅ [SUCCESS] {message}")
        
    def print_warning(self, message: str):
        """打印警告信息"""
        print(f"⚠️  [WARNING] {message}")
        
    def print_error(self, message: str):
        """打印错误信息"""
        print(f"❌ [ERROR] {message}")
        
    def check_file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        if not os.path.exists(filename):
            self.print_error(f"文件不存在: {filename}")
            return False
        return True
        
    def check_syntax(self, filename: str) -> bool:
        """检查Python语法"""
        self.print_info(f"检查语法: {filename}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # 解析AST
            ast.parse(source)
            self.print_success(f"语法检查通过: {filename}")
            return True
            
        except SyntaxError as e:
            self.print_error(f"语法错误: {filename} - {e}")
            return False
        except Exception as e:
            self.print_error(f"语法检查失败: {filename} - {e}")
            return False
            
    def check_imports(self, filename: str) -> bool:
        """检查导入模块"""
        self.print_info(f"检查导入: {filename}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # 解析AST
            tree = ast.parse(source)
            
            # 提取导入语句
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # 检查关键导入
            required_imports = [
                'nautilus_trader',
                'nautilus_trader.adapters.binance'
            ]
            
            missing_imports = []
            for req_import in required_imports:
                if not any(req_import in imp for imp in imports):
                    missing_imports.append(req_import)
            
            if missing_imports:
                self.print_warning(f"缺少导入: {filename} - {missing_imports}")
                return False
            else:
                self.print_success(f"导入检查通过: {filename}")
                return True
                
        except Exception as e:
            self.print_error(f"导入检查失败: {filename} - {e}")
            return False
            
    def check_environment_variables(self, filename: str) -> bool:
        """检查环境变量使用"""
        self.print_info(f"检查环境变量: {filename}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # 检查环境变量使用
            env_vars = ['BINANCE_API_KEY', 'BINANCE_API_SECRET']
            missing_vars = []
            
            for var in env_vars:
                if f'os.getenv("{var}")' not in source and f"os.getenv('{var}')" not in source:
                    missing_vars.append(var)
            
            if missing_vars:
                self.print_warning(f"缺少环境变量检查: {filename} - {missing_vars}")
                return False
            else:
                self.print_success(f"环境变量检查通过: {filename}")
                return True
                
        except Exception as e:
            self.print_error(f"环境变量检查失败: {filename} - {e}")
            return False
            
    def check_configuration(self, filename: str) -> bool:
        """检查配置"""
        self.print_info(f"检查配置: {filename}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # 检查关键配置
            config_checks = [
                'TradingNodeConfig',
                'BinanceDataClientConfig',
                'BinanceExecClientConfig'
            ]
            
            missing_configs = []
            for config in config_checks:
                if config not in source:
                    missing_configs.append(config)
            
            if missing_configs:
                self.print_warning(f"缺少配置: {filename} - {missing_configs}")
                return False
            else:
                self.print_success(f"配置检查通过: {filename}")
                return True
                
        except Exception as e:
            self.print_error(f"配置检查失败: {filename} - {e}")
            return False
            
    def check_strategy_structure(self, filename: str) -> bool:
        """检查策略结构"""
        self.print_info(f"检查策略结构: {filename}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # 检查策略类
            if 'class' in source and 'Strategy' in source:
                self.print_success(f"策略结构检查通过: {filename}")
                return True
            else:
                self.print_warning(f"缺少策略类: {filename}")
                return False
                
        except Exception as e:
            self.print_error(f"策略结构检查失败: {filename} - {e}")
            return False
            
    def check_error_handling(self, filename: str) -> bool:
        """检查错误处理"""
        self.print_info(f"检查错误处理: {filename}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # 检查错误处理
            error_handling = ['try:', 'except:', 'finally:', 'KeyboardInterrupt']
            missing_handling = []
            
            for handling in error_handling:
                if handling not in source:
                    missing_handling.append(handling)
            
            if len(missing_handling) > 2:  # 允许缺少一些
                self.print_warning(f"缺少错误处理: {filename} - {missing_handling}")
                return False
            else:
                self.print_success(f"错误处理检查通过: {filename}")
                return True
                
        except Exception as e:
            self.print_error(f"错误处理检查失败: {filename} - {e}")
            return False
            
    def run_python_check(self, filename: str) -> bool:
        """运行Python检查"""
        self.print_info(f"运行Python检查: {filename}")
        
        try:
            # 运行python -m py_compile
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', filename],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.print_success(f"Python检查通过: {filename}")
                return True
            else:
                self.print_error(f"Python检查失败: {filename} - {result.stderr}")
                return False
                
        except Exception as e:
            self.print_error(f"Python检查异常: {filename} - {e}")
            return False
            
    def test_file(self, filename: str) -> bool:
        """测试单个文件"""
        print(f"\n📁 测试文件: {filename}")
        print("=" * 50)
        
        if not self.check_file_exists(filename):
            return False
        
        tests = [
            self.check_syntax,
            self.check_imports,
            self.check_environment_variables,
            self.check_configuration,
            self.check_strategy_structure,
            self.check_error_handling,
            self.run_python_check
        ]
        
        results = []
        for test in tests:
            try:
                result = test(filename)
                results.append(result)
            except Exception as e:
                self.print_error(f"测试异常: {test.__name__} - {e}")
                results.append(False)
        
        # 计算通过率
        passed = sum(results)
        total = len(results)
        pass_rate = passed / total * 100
        
        print(f"\n📊 测试结果: {filename}")
        print(f"   通过: {passed}/{total} ({pass_rate:.1f}%)")
        
        if pass_rate >= 80:
            self.print_success(f"文件测试通过: {filename}")
            return True
        else:
            self.print_error(f"文件测试失败: {filename}")
            return False
            
    def test_all_files(self) -> bool:
        """测试所有文件"""
        print("🚀 开始测试所有示例文件")
        print("=" * 50)
        
        results = []
        for filename in self.example_files:
            if os.path.exists(filename):
                result = self.test_file(filename)
                results.append(result)
                self.test_results[filename] = result
            else:
                self.print_warning(f"文件不存在，跳过: {filename}")
                results.append(False)
                self.test_results[filename] = False
        
        # 计算总体结果
        passed = sum(results)
        total = len(results)
        pass_rate = passed / total * 100
        
        print(f"\n📊 总体测试结果")
        print("=" * 50)
        print(f"通过: {passed}/{total} ({pass_rate:.1f}%)")
        
        if pass_rate >= 80:
            self.print_success("所有测试通过！")
            return True
        else:
            self.print_error("部分测试失败")
            return False
            
    def show_summary(self):
        """显示测试摘要"""
        print(f"\n📋 测试摘要")
        print("=" * 50)
        
        for filename, result in self.test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{filename}: {status}")
            
    def show_recommendations(self):
        """显示建议"""
        print(f"\n💡 建议")
        print("=" * 50)
        
        print("1. 环境设置:")
        print("   - 确保已安装NautilusTrader: pip install nautilus_trader[binance]")
        print("   - 设置环境变量: export BINANCE_API_KEY='your_key'")
        print("   - 设置环境变量: export BINANCE_API_SECRET='your_secret'")
        
        print("\n2. 测试步骤:")
        print("   - 运行连接测试: python test_binance_connection.py")
        print("   - 运行策略测试: python binance_spot_ema_cross.py")
        print("   - 查看日志文件: tail -f *.log")
        
        print("\n3. 注意事项:")
        print("   - 建议先在测试网测试")
        print("   - 注意风险控制和资金管理")
        print("   - 定期检查策略运行状态")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='NautilusTrader Binance 示例代码测试')
    parser.add_argument('--file', '-f', help='测试特定文件')
    parser.add_argument('--all', '-a', action='store_true', help='测试所有文件')
    
    args = parser.parse_args()
    
    tester = ExampleTester()
    
    if args.file:
        # 测试特定文件
        success = tester.test_file(args.file)
    else:
        # 测试所有文件
        success = tester.test_all_files()
    
    # 显示摘要和建议
    tester.show_summary()
    tester.show_recommendations()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
