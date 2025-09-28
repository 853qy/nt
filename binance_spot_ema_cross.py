#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binance 现货 EMA 交叉策略示例

这是一个简单的双均线交叉策略，仅用于学习目的。
策略逻辑：
- 当快速EMA上穿慢速EMA时，买入
- 当快速EMA下穿慢速EMA时，卖出

使用方法：
1. 设置环境变量 BINANCE_API_KEY 和 BINANCE_API_SECRET
2. 运行脚本: python binance_spot_ema_cross.py

注意：
- 这是一个测试策略，没有alpha优势
- 请勿用于实盘交易真实资金
- 建议先在测试网测试
"""

from decimal import Decimal
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nautilus_trader.adapters.binance import BINANCE
from nautilus_trader.adapters.binance import BinanceAccountType
from nautilus_trader.adapters.binance import BinanceDataClientConfig
from nautilus_trader.adapters.binance import BinanceExecClientConfig
from nautilus_trader.adapters.binance import BinanceLiveDataClientFactory
from nautilus_trader.adapters.binance import BinanceLiveExecClientFactory
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveExecEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.examples.strategies.ema_cross import EMACross
from nautilus_trader.examples.strategies.ema_cross import EMACrossConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TraderId


def check_environment():
    """检查环境变量设置"""
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ 错误: 请设置环境变量 BINANCE_API_KEY 和 BINANCE_API_SECRET")
        print("设置方法:")
        print("export BINANCE_API_KEY='your_api_key_here'")
        print("export BINANCE_API_SECRET='your_api_secret_here'")
        return False
    
    print("✅ 环境变量检查通过")
    return True


def create_trading_node_config():
    """创建交易节点配置"""
    return TradingNodeConfig(
        trader_id=TraderId("BINANCE-SPOT-EMA-001"),
        logging=LoggingConfig(
            log_level="INFO",
            log_to_file=True,
            log_file_path="binance_spot_trading.log",
        ),
        exec_engine=LiveExecEngineConfig(
            reconciliation=True,  # 启用对账
            reconciliation_lookback_mins=1440,  # 对账回看时间（分钟）
            # snapshot_orders=True,  # 可选：快照订单
            # snapshot_positions=True,  # 可选：快照持仓
        ),
        data_clients={
            BINANCE: BinanceDataClientConfig(
                api_key=None,  # 从环境变量读取
                api_secret=None,  # 从环境变量读取
                account_type=BinanceAccountType.SPOT,
                base_url_http=None,  # 使用默认URL
                base_url_ws=None,  # 使用默认URL
                us=False,  # 非Binance US
                testnet=False,  # 设置为True使用测试网
                instrument_provider=InstrumentProviderConfig(
                    load_all=True,
                    log_warnings=False,  # 减少警告日志
                ),
            ),
        },
        exec_clients={
            BINANCE: BinanceExecClientConfig(
                api_key=None,  # 从环境变量读取
                api_secret=None,  # 从环境变量读取
                account_type=BinanceAccountType.SPOT,
                base_url_http=None,  # 使用默认URL
                base_url_ws=None,  # 使用默认URL
                us=False,  # 非Binance US
                testnet=False,  # 设置为True使用测试网
                instrument_provider=InstrumentProviderConfig(
                    load_all=True,
                    log_warnings=False,
                ),
                max_retries=3,
                retry_delay_initial_ms=1_000,
                retry_delay_max_ms=10_000,
            ),
        },
        timeout_connection=30.0,
        timeout_reconciliation=10.0,
        timeout_portfolio=10.0,
        timeout_disconnection=10.0,
        timeout_post_stop=5.0,
    )


def create_strategy_config():
    """创建策略配置"""
    return EMACrossConfig(
        instrument_id=InstrumentId.from_str("BTCUSDT.BINANCE"),
        external_order_claims=[InstrumentId.from_str("BTCUSDT.BINANCE")],
        bar_type=BarType.from_str("BTCUSDT.BINANCE-1-MINUTE-LAST-EXTERNAL"),
        fast_ema_period=10,  # 快速EMA周期
        slow_ema_period=20,  # 慢速EMA周期
        trade_size=Decimal("0.001"),  # 交易数量（BTC）
        order_id_tag="EMA001",
        subscribe_quote_ticks=True,  # 订阅报价数据
        subscribe_trade_ticks=True,   # 订阅成交数据
        request_bars=True,           # 请求历史K线
        unsubscribe_data_on_stop=True,  # 停止时取消订阅
        close_positions_on_stop=True,   # 停止时平仓
        reduce_only_on_stop=True,       # 平仓时使用reduce_only
    )


def main():
    """主函数"""
    print("🚀 启动 Binance 现货 EMA 交叉策略")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        return
    
    try:
        # 创建配置
        print("📋 创建交易节点配置...")
        config_node = create_trading_node_config()
        
        print("📋 创建策略配置...")
        strat_config = create_strategy_config()
        
        # 实例化交易节点
        print("🏗️  构建交易节点...")
        node = TradingNode(config=config_node)
        
        # 实例化策略
        print("📈 创建EMA交叉策略...")
        strategy = EMACross(config=strat_config)
        
        # 添加策略到交易节点
        node.trader.add_strategy(strategy)
        
        # 注册客户端工厂
        print("🔌 注册客户端工厂...")
        node.add_data_client_factory(BINANCE, BinanceLiveDataClientFactory)
        node.add_exec_client_factory(BINANCE, BinanceLiveExecClientFactory)
        
        # 构建节点
        print("⚙️  构建交易节点...")
        node.build()
        
        print("✅ 交易节点构建完成")
        print("📊 策略配置:")
        print(f"   - 交易对: {strat_config.instrument_id}")
        print(f"   - K线周期: {strat_config.bar_type}")
        print(f"   - 快速EMA: {strat_config.fast_ema_period}")
        print(f"   - 慢速EMA: {strat_config.slow_ema_period}")
        print(f"   - 交易数量: {strat_config.trade_size}")
        print("=" * 50)
        print("🎯 开始运行策略...")
        print("按 Ctrl+C 停止策略")
        print("=" * 50)
        
        # 运行交易节点
        node.run()
        
    except KeyboardInterrupt:
        print("\n⏹️  收到停止信号，正在关闭策略...")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🧹 清理资源...")
        try:
            node.dispose()
        except:
            pass
        print("✅ 策略已停止")


if __name__ == "__main__":
    main()
