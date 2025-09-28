#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NautilusTrader Binance 连接测试脚本

此脚本用于测试NautilusTrader与Binance的连接
包括API连接、权限验证、账户信息获取等

使用方法：
1. 设置环境变量 BINANCE_API_KEY 和 BINANCE_API_SECRET
2. 运行脚本: python test_binance_connection.py

注意：
- 请确保API密钥具有正确的权限
- 建议先在测试网测试
"""

import os
import sys
import asyncio
from typing import Optional

try:
    from nautilus_trader.adapters.binance import BINANCE
    from nautilus_trader.adapters.binance import BinanceAccountType
    from nautilus_trader.adapters.binance import BinanceHttpClient
    from nautilus_trader.common.clock import LiveClock
    from nautilus_trader.model.identifiers import InstrumentId
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请先安装NautilusTrader: pip install nautilus_trader[binance]")
    sys.exit(1)


class BinanceConnectionTester:
    """Binance连接测试器"""
    
    def __init__(self):
        self.clock = LiveClock()
        self.api_key: Optional[str] = None
        self.api_secret: Optional[str] = None
        
    def check_environment(self) -> bool:
        """检查环境变量"""
        print("🔍 检查环境变量...")
        
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            print("❌ 错误: 请设置环境变量 BINANCE_API_KEY 和 BINANCE_API_SECRET")
            print("设置方法:")
            print("export BINANCE_API_KEY='your_api_key_here'")
            print("export BINANCE_API_SECRET='your_api_secret_here'")
            return False
        
        print("✅ 环境变量检查通过")
        return True
    
    def create_client(self, account_type: BinanceAccountType, testnet: bool = False) -> BinanceHttpClient:
        """创建HTTP客户端"""
        if account_type == BinanceAccountType.SPOT:
            base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        elif account_type in [BinanceAccountType.USDT_FUTURES, BinanceAccountType.COIN_FUTURES]:
            base_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
        else:
            base_url = "https://api.binance.com"
            
        return BinanceHttpClient(
            clock=self.clock,
            api_key=self.api_key,
            api_secret=self.api_secret,
            base_url=base_url,
        )
    
    def test_spot_connection(self, testnet: bool = False) -> bool:
        """测试现货连接"""
        print(f"📡 测试现货API连接 ({'测试网' if testnet else '主网'})...")
        
        try:
            client = self.create_client(BinanceAccountType.SPOT, testnet)
            
            # 测试ping
            response = client._get("/api/v3/ping")
            if response:
                print("✅ Ping测试成功")
            else:
                print("❌ Ping测试失败")
                return False
            
            # 测试服务器时间
            response = client._get("/api/v3/time")
            if response:
                server_time = response.get("serverTime")
                print(f"✅ 服务器时间获取成功: {server_time}")
            else:
                print("❌ 服务器时间获取失败")
                return False
            
            # 测试账户信息
            response = client._get("/api/v3/account")
            if response:
                print("✅ 账户信息获取成功")
                print(f"   账户类型: {response.get('accountType', 'Unknown')}")
                print(f"   权限: {response.get('permissions', [])}")
                print(f"   余额数量: {len(response.get('balances', []))}")
            else:
                print("❌ 账户信息获取失败")
                return False
            
            # 测试交易对信息
            response = client._get("/api/v3/exchangeInfo")
            if response:
                symbols = response.get("symbols", [])
                print(f"✅ 交易对信息获取成功，共{len(symbols)}个交易对")
            else:
                print("❌ 交易对信息获取失败")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 现货连接测试失败: {e}")
            return False
    
    def test_futures_connection(self, testnet: bool = False) -> bool:
        """测试期货连接"""
        print(f"📡 测试期货API连接 ({'测试网' if testnet else '主网'})...")
        
        try:
            client = self.create_client(BinanceAccountType.USDT_FUTURES, testnet)
            
            # 测试ping
            response = client._get("/fapi/v1/ping")
            if response:
                print("✅ Ping测试成功")
            else:
                print("❌ Ping测试失败")
                return False
            
            # 测试服务器时间
            response = client._get("/fapi/v1/time")
            if response:
                server_time = response.get("serverTime")
                print(f"✅ 服务器时间获取成功: {server_time}")
            else:
                print("❌ 服务器时间获取失败")
                return False
            
            # 测试账户信息
            response = client._get("/fapi/v2/account")
            if response:
                print("✅ 账户信息获取成功")
                print(f"   账户类型: {response.get('accountType', 'Unknown')}")
                print(f"   总余额: {response.get('totalWalletBalance', 'Unknown')}")
                print(f"   可用余额: {response.get('availableBalance', 'Unknown')}")
            else:
                print("❌ 账户信息获取失败")
                return False
            
            # 测试交易对信息
            response = client._get("/fapi/v1/exchangeInfo")
            if response:
                symbols = response.get("symbols", [])
                print(f"✅ 交易对信息获取成功，共{len(symbols)}个交易对")
            else:
                print("❌ 交易对信息获取失败")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 期货连接测试失败: {e}")
            return False
    
    def test_instrument_provider(self) -> bool:
        """测试工具提供者"""
        print("🔧 测试工具提供者...")
        
        try:
            from nautilus_trader.adapters.binance.spot.providers import BinanceSpotInstrumentProvider
            from nautilus_trader.config import InstrumentProviderConfig
            
            client = self.create_client(BinanceAccountType.SPOT)
            
            provider = BinanceSpotInstrumentProvider(
                client=client,
                clock=self.clock,
                config=InstrumentProviderConfig(load_all=True),
                venue=BINANCE,
            )
            
            # 加载工具
            provider.load_all_async()
            
            # 获取BTCUSDT工具
            btcusdt = provider.find_with_venue_symbol("BTCUSDT")
            if btcusdt:
                print("✅ BTCUSDT工具加载成功")
                print(f"   基础资产: {btcusdt.base_currency}")
                print(f"   报价资产: {btcusdt.quote_currency}")
                print(f"   最小数量: {btcusdt.min_quantity}")
                print(f"   最小价格: {btcusdt.min_price}")
            else:
                print("❌ BTCUSDT工具加载失败")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 工具提供者测试失败: {e}")
            return False
    
    def test_websocket_connection(self) -> bool:
        """测试WebSocket连接"""
        print("🌐 测试WebSocket连接...")
        
        try:
            from nautilus_trader.adapters.binance.spot.data import BinanceSpotDataClient
            from nautilus_trader.adapters.binance import BinanceDataClientConfig
            from nautilus_trader.cache import Cache
            from nautilus_trader.common.component import TestClock
            from nautilus_trader.common.logging import Logger
            from nautilus_trader.core.message import MessageBus
            
            # 创建测试组件
            clock = TestClock()
            logger = Logger(clock)
            msgbus = MessageBus(clock, logger)
            cache = Cache(clock, logger)
            
            # 创建数据客户端配置
            config = BinanceDataClientConfig(
                api_key=self.api_key,
                api_secret=self.api_secret,
                account_type=BinanceAccountType.SPOT,
                testnet=True,  # 使用测试网
            )
            
            # 创建数据客户端
            client = BinanceSpotDataClient(
                loop=asyncio.get_event_loop(),
                client_id=BINANCE,
                config=config,
                msgbus=msgbus,
                cache=cache,
                clock=clock,
            )
            
            print("✅ WebSocket客户端创建成功")
            print("   注意: WebSocket连接测试需要实际运行才能验证")
            
            return True
            
        except Exception as e:
            print(f"❌ WebSocket连接测试失败: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始Binance连接测试")
        print("=" * 50)
        
        if not self.check_environment():
            return False
        
        success = True
        
        # 测试现货连接
        print("\n📊 测试现货连接...")
        if not self.test_spot_connection(testnet=False):
            success = False
        
        # 测试现货测试网连接
        print("\n📊 测试现货测试网连接...")
        if not self.test_spot_connection(testnet=True):
            success = False
        
        # 测试期货连接
        print("\n📊 测试期货连接...")
        if not self.test_futures_connection(testnet=False):
            success = False
        
        # 测试期货测试网连接
        print("\n📊 测试期货测试网连接...")
        if not self.test_futures_connection(testnet=True):
            success = False
        
        # 测试工具提供者
        print("\n📊 测试工具提供者...")
        if not self.test_instrument_provider():
            success = False
        
        # 测试WebSocket连接
        print("\n📊 测试WebSocket连接...")
        if not self.test_websocket_connection():
            success = False
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 所有测试通过！")
            print("✅ Binance连接正常，可以开始交易")
        else:
            print("❌ 部分测试失败，请检查配置")
            print("💡 建议:")
            print("   - 检查API密钥是否正确")
            print("   - 检查API权限设置")
            print("   - 检查网络连接")
            print("   - 检查IP白名单设置")
        
        return success


def main():
    """主函数"""
    tester = BinanceConnectionTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
