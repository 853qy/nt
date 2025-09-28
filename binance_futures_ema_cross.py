#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binance 期货合约 EMA 交叉策略示例

这是一个支持永续合约交易的EMA交叉策略，包含对冲模式支持。
策略逻辑：
- 当快速EMA上穿慢速EMA时，开多仓
- 当快速EMA下穿慢速EMA时，开空仓
- 支持对冲模式，可以同时持有多空仓位

使用方法：
1. 设置环境变量 BINANCE_API_KEY 和 BINANCE_API_SECRET
2. 运行脚本: python binance_futures_ema_cross.py

注意：
- 这是一个测试策略，没有alpha优势
- 期货交易风险更高，请谨慎操作
- 建议先在测试网测试
- 支持对冲模式，可以同时持有多空仓位
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
from nautilus_trader.cache.config import CacheConfig
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
        trader_id=TraderId("BINANCE-FUTURES-EMA-001"),
        logging=LoggingConfig(
            log_level="INFO",
            log_to_file=True,
            log_file_path="binance_futures_trading.log",
        ),
        exec_engine=LiveExecEngineConfig(
            reconciliation=True,  # 启用对账
            reconciliation_lookback_mins=1440,  # 对账回看时间（分钟）
            # snapshot_orders=True,  # 可选：快照订单
            # snapshot_positions=True,  # 可选：快照持仓
        ),
        cache=CacheConfig(
            timestamps_as_iso8601=True,
            flush_on_start=False,
        ),
        data_clients={
            BINANCE: BinanceDataClientConfig(
                api_key=None,  # 从环境变量读取
                api_secret=None,  # 从环境变量读取
                account_type=BinanceAccountType.USDT_FUTURES,
                base_url_http=None,  # 使用默认URL
                base_url_ws=None,  # 使用默认URL
                us=False,  # 非Binance US
                testnet=True,  # 使用测试网进行测试
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
                account_type=BinanceAccountType.USDT_FUTURES,
                base_url_http=None,  # 使用默认URL
                base_url_ws=None,  # 使用默认URL
                us=False,  # 非Binance US
                testnet=True,  # 使用测试网进行测试
                instrument_provider=InstrumentProviderConfig(
                    load_all=True,
                    log_warnings=False,
                ),
                use_position_ids=False,  # 禁用位置ID（用于对冲模式）
                use_reduce_only=False,   # 禁用reduce_only（用于对冲模式）
                max_retries=3,
                retry_delay_initial_ms=1_000,
                retry_delay_max_ms=10_000,
                # 设置杠杆和保证金类型
                futures_leverages={
                    "BTCUSDT-PERP": 10,  # BTC永续合约10倍杠杆
                },
                futures_margin_types={
                    "BTCUSDT-PERP": "ISOLATED",  # 逐仓模式
                },
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
        instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),  # 永续合约
        external_order_claims=[InstrumentId.from_str("BTCUSDT-PERP.BINANCE")],
        bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
        fast_ema_period=10,  # 快速EMA周期
        slow_ema_period=20,  # 慢速EMA周期
        trade_size=Decimal("0.010"),  # 交易数量
        order_id_tag="FUTURES001",
        oms_type="HEDGING",  # 对冲模式
        subscribe_quote_ticks=True,  # 订阅报价数据
        subscribe_trade_ticks=True,   # 订阅成交数据
        request_bars=True,           # 请求历史K线
        unsubscribe_data_on_stop=True,  # 停止时取消订阅
        close_positions_on_stop=True,   # 停止时平仓
        reduce_only_on_stop=False,      # 对冲模式下不使用reduce_only
    )


def create_hedge_mode_strategy():
    """创建支持对冲模式的自定义策略"""
    from nautilus_trader.config import StrategyConfig
    from nautilus_trader.core.data import Data
    from nautilus_trader.core.message import Event
    from nautilus_trader.indicators import ExponentialMovingAverage
    from nautilus_trader.model.data import Bar
    from nautilus_trader.model.data import BarType
    from nautilus_trader.model.data import QuoteTick
    from nautilus_trader.model.data import TradeTick
    from nautilus_trader.model.enums import OrderSide
    from nautilus_trader.model.enums import TimeInForce
    from nautilus_trader.model.identifiers import InstrumentId
    from nautilus_trader.model.identifiers import PositionId
    from nautilus_trader.model.instruments import Instrument
    from nautilus_trader.model.objects import Quantity
    from nautilus_trader.model.orders import MarketOrder
    from nautilus_trader.trading.strategy import Strategy

    class HedgeModeEMACrossConfig(StrategyConfig, frozen=True):
        """对冲模式EMA交叉策略配置"""
        instrument_id: InstrumentId
        bar_type: BarType
        trade_size: Decimal
        fast_ema_period: int = 10
        slow_ema_period: int = 20
        subscribe_quote_ticks: bool = True
        subscribe_trade_ticks: bool = True
        request_bars: bool = True
        unsubscribe_data_on_stop: bool = True
        close_positions_on_stop: bool = True

    class HedgeModeEMACross(Strategy):
        """对冲模式EMA交叉策略"""
        
        def __init__(self, config: HedgeModeEMACrossConfig) -> None:
            super().__init__(config)
            
            self.instrument: Instrument = None
            
            # 创建指标
            self.fast_ema = ExponentialMovingAverage(config.fast_ema_period)
            self.slow_ema = ExponentialMovingAverage(config.slow_ema_period)
            
            # 策略状态
            self.last_signal = None
            
        def on_start(self) -> None:
            """策略启动"""
            self.instrument = self.cache.instrument(self.config.instrument_id)
            if self.instrument is None:
                self.log.error(f"无法找到交易对: {self.config.instrument_id}")
                self.stop()
                return
                
            # 注册指标
            self.register_indicator_for_bars(self.config.bar_type, self.fast_ema)
            self.register_indicator_for_bars(self.config.bar_type, self.slow_ema)
            
            # 订阅数据
            self.subscribe_bars(self.config.bar_type)
            if self.config.subscribe_quote_ticks:
                self.subscribe_quote_ticks(self.config.instrument_id)
            if self.config.subscribe_trade_ticks:
                self.subscribe_trade_ticks(self.config.instrument_id)
                
            self.log.info(f"对冲模式EMA交叉策略启动: {self.config.instrument_id}")
            
        def on_bar(self, bar: Bar) -> None:
            """处理K线数据"""
            # 等待指标初始化
            if not self.indicators_initialized():
                self.log.info("等待指标初始化...")
                return
                
            # 计算信号
            if self.fast_ema.value >= self.slow_ema.value:
                signal = "BUY"
            else:
                signal = "SELL"
                
            # 执行交易逻辑
            if signal != self.last_signal:
                if signal == "BUY":
                    self._open_long_position()
                elif signal == "SELL":
                    self._open_short_position()
                self.last_signal = signal
                
        def _open_long_position(self) -> None:
            """开多仓"""
            order = self.order_factory.market(
                instrument_id=self.config.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.instrument.make_qty(self.config.trade_size),
                time_in_force=TimeInForce.GTC,
            )
            
            # 使用LONG后缀标识多头仓位
            position_id = PositionId(f"{self.config.instrument_id}-LONG")
            self.submit_order(order, position_id)
            self.log.info(f"开多仓: {order}")
            
        def _open_short_position(self) -> None:
            """开空仓"""
            order = self.order_factory.market(
                instrument_id=self.config.instrument_id,
                order_side=OrderSide.SELL,
                quantity=self.instrument.make_qty(self.config.trade_size),
                time_in_force=TimeInForce.GTC,
            )
            
            # 使用SHORT后缀标识空头仓位
            position_id = PositionId(f"{self.config.instrument_id}-SHORT")
            self.submit_order(order, position_id)
            self.log.info(f"开空仓: {order}")
            
        def on_quote_tick(self, tick: QuoteTick) -> None:
            """处理报价数据"""
            pass
            
        def on_trade_tick(self, tick: TradeTick) -> None:
            """处理成交数据"""
            pass
            
        def on_stop(self) -> None:
            """策略停止"""
            self.cancel_all_orders(self.config.instrument_id)
            if self.config.close_positions_on_stop:
                self.close_all_positions(self.config.instrument_id)
            self.log.info("对冲模式策略已停止")
            
        def on_reset(self) -> None:
            """策略重置"""
            self.fast_ema.reset()
            self.slow_ema.reset()
            
        def on_save(self) -> dict[str, bytes]:
            """保存策略状态"""
            return {}
            
        def on_load(self, state: dict[str, bytes]) -> None:
            """加载策略状态"""
            pass
            
        def on_dispose(self) -> None:
            """策略销毁"""
            pass

    return HedgeModeEMACross, HedgeModeEMACrossConfig


def main():
    """主函数"""
    print("🚀 启动 Binance 期货 EMA 交叉策略")
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
        print(f"   - 对冲模式: {strat_config.oms_type}")
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
