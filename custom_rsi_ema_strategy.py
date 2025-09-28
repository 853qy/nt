#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义 Binance RSI + EMA 策略示例

这是一个结合RSI和EMA指标的自定义交易策略。
策略逻辑：
- 当价格在EMA之上且RSI超卖时，买入
- 当价格在EMA之下且RSI超买时，卖出
- 包含风险控制和止损机制

使用方法：
1. 设置环境变量 BINANCE_API_KEY 和 BINANCE_API_SECRET
2. 运行脚本: python custom_rsi_ema_strategy.py

注意：
- 这是一个测试策略，没有alpha优势
- 请勿用于实盘交易真实资金
- 建议先在测试网测试
"""

from decimal import Decimal
import os
import sys
from typing import Optional

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nautilus_trader.adapters.binance import BINANCE
from nautilus_trader.adapters.binance import BinanceAccountType
from nautilus_trader.adapters.binance import BinanceDataClientConfig
from nautilus_trader.adapters.binance import BinanceExecClientConfig
from nautilus_trader.adapters.binance import BinanceLiveDataClientFactory
from nautilus_trader.adapters.binance import BinanceLiveExecClientFactory
from nautilus_trader.cache.config import CacheConfig
from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveExecEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import StrategyConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.core.data import Data
from nautilus_trader.core.message import Event
from nautilus_trader.indicators import ExponentialMovingAverage
from nautilus_trader.indicators import RelativeStrengthIndex
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import OrderBook
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import LimitOrder
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.model.orders import StopMarketOrder
from nautilus_trader.trading.strategy import Strategy


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


class CustomRSIEMAConfig(StrategyConfig, frozen=True):
    """自定义RSI+EMA策略配置"""
    
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    ema_period: int = 20
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    stop_loss_pct: float = 0.02  # 2%止损
    take_profit_pct: float = 0.04  # 4%止盈
    max_position_size: Decimal = Decimal("1.0")  # 最大持仓
    min_balance: Decimal = Decimal("100.0")  # 最小余额
    subscribe_quote_ticks: bool = True
    subscribe_trade_ticks: bool = True
    request_bars: bool = True
    unsubscribe_data_on_stop: bool = True
    close_positions_on_stop: bool = True
    reduce_only_on_stop: bool = True


class CustomRSIEMAStrategy(Strategy):
    """自定义RSI+EMA交易策略"""
    
    def __init__(self, config: CustomRSIEMAConfig) -> None:
        PyCondition.is_true(
            config.rsi_period > 0,
            f"RSI周期必须大于0，当前值: {config.rsi_period}",
        )
        PyCondition.is_true(
            config.ema_period > 0,
            f"EMA周期必须大于0，当前值: {config.ema_period}",
        )
        PyCondition.is_true(
            0 < config.rsi_oversold < config.rsi_overbought < 100,
            f"RSI参数无效: oversold={config.rsi_oversold}, overbought={config.rsi_overbought}",
        )
        
        super().__init__(config)
        
        self.instrument: Optional[Instrument] = None
        
        # 创建技术指标
        self.ema = ExponentialMovingAverage(config.ema_period)
        self.rsi = RelativeStrengthIndex(config.rsi_period)
        
        # 策略状态
        self.last_signal = None
        self.entry_price = None
        self.stop_loss_order = None
        self.take_profit_order = None
        
    def on_start(self) -> None:
        """策略启动时的操作"""
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"无法找到交易对: {self.config.instrument_id}")
            self.stop()
            return
            
        # 注册指标
        self.register_indicator_for_bars(self.config.bar_type, self.ema)
        self.register_indicator_for_bars(self.config.bar_type, self.rsi)
        
        # 订阅数据
        self.subscribe_bars(self.config.bar_type)
        if self.config.subscribe_quote_ticks:
            self.subscribe_quote_ticks(self.config.instrument_id)
        if self.config.subscribe_trade_ticks:
            self.subscribe_trade_ticks(self.config.instrument_id)
            
        self.log.info(f"自定义RSI+EMA策略启动: {self.config.instrument_id}")
        self.log.info(f"EMA周期: {self.config.ema_period}")
        self.log.info(f"RSI周期: {self.config.rsi_period}")
        self.log.info(f"RSI超买线: {self.config.rsi_overbought}")
        self.log.info(f"RSI超卖线: {self.config.rsi_oversold}")
        
    def on_bar(self, bar: Bar) -> None:
        """处理K线数据"""
        # 等待指标初始化
        if not self.indicators_initialized():
            self.log.info(
                f"等待指标初始化... EMA: {self.ema.initialized}, RSI: {self.rsi.initialized}",
                color=LogColor.BLUE,
            )
            return
            
        # 检查是否为单价格K线
        if bar.is_single_price():
            self.log.warning("K线为单价格，跳过处理")
            return
            
        # 获取当前价格
        current_price = bar.close
        
        # 计算交易信号
        signal = self._calculate_signal(current_price)
        
        # 执行交易逻辑
        if signal == "BUY" and self.last_signal != "BUY":
            self._execute_buy_signal(current_price)
            self.last_signal = "BUY"
        elif signal == "SELL" and self.last_signal != "SELL":
            self._execute_sell_signal(current_price)
            self.last_signal = "SELL"
            
        # 更新止损止盈
        self._update_stop_loss_take_profit(current_price)
        
    def _calculate_signal(self, price: float) -> str:
        """计算交易信号"""
        # 价格在EMA之上且RSI超卖 -> 买入信号
        if price > self.ema.value and self.rsi.value < self.config.rsi_oversold:
            return "BUY"
        # 价格在EMA之下且RSI超买 -> 卖出信号
        elif price < self.ema.value and self.rsi.value > self.config.rsi_overbought:
            return "SELL"
        else:
            return "HOLD"
            
    def _execute_buy_signal(self, price: float) -> None:
        """执行买入信号"""
        if not self._check_risk_limits():
            return
            
        # 如果已有空头持仓，先平仓
        if self.portfolio.is_net_short(self.config.instrument_id):
            self.log.info("检测到空头持仓，先平仓")
            self.close_all_positions(self.config.instrument_id)
            return
            
        # 如果已有多头持仓，跳过
        if self.portfolio.is_net_long(self.config.instrument_id):
            self.log.info("已有多头持仓，跳过买入")
            return
            
        # 下买单
        order = self.order_factory.limit(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.config.trade_size),
            price=self.instrument.make_price(price * 0.999),  # 略低于市价
            time_in_force=TimeInForce.GTC,
        )
        
        self.submit_order(order)
        self.entry_price = price
        self.log.info(f"下买单: {order}", color=LogColor.GREEN)
        
    def _execute_sell_signal(self, price: float) -> None:
        """执行卖出信号"""
        if not self._check_risk_limits():
            return
            
        # 如果已有多头持仓，先平仓
        if self.portfolio.is_net_long(self.config.instrument_id):
            self.log.info("检测到多头持仓，先平仓")
            self.close_all_positions(self.config.instrument_id)
            return
            
        # 如果有空头持仓，跳过
        if self.portfolio.is_net_short(self.config.instrument_id):
            self.log.info("已有空头持仓，跳过卖出")
            return
            
        # 下卖单
        order = self.order_factory.limit(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.config.trade_size),
            price=self.instrument.make_price(price * 1.001),  # 略高于市价
            time_in_force=TimeInForce.GTC,
        )
        
        self.submit_order(order)
        self.entry_price = price
        self.log.info(f"下卖单: {order}", color=LogColor.RED)
        
    def _check_risk_limits(self) -> bool:
        """检查风险限制"""
        # 检查最大持仓
        position = self.portfolio.net_position(self.config.instrument_id)
        if abs(position.quantity) >= self.config.max_position_size:
            self.log.warning(f"超过最大持仓限制: {position.quantity}")
            return False
            
        # 检查账户余额
        balance = self.portfolio.account_balance()
        if balance.free < self.config.min_balance:
            self.log.warning(f"账户余额不足: {balance.free}")
            return False
            
        return True
        
    def _update_stop_loss_take_profit(self, current_price: float) -> None:
        """更新止损止盈"""
        if self.entry_price is None:
            return
            
        position = self.portfolio.net_position(self.config.instrument_id)
        if position.is_flat():
            return
            
        # 计算止损止盈价格
        if position.is_net_long():
            # 多头持仓
            stop_loss_price = self.entry_price * (1 - self.config.stop_loss_pct)
            take_profit_price = self.entry_price * (1 + self.config.take_profit_pct)
        else:
            # 空头持仓
            stop_loss_price = self.entry_price * (1 + self.config.stop_loss_pct)
            take_profit_price = self.entry_price * (1 - self.config.take_profit_pct)
            
        # 更新止损单
        if self.stop_loss_order is None:
            self.stop_loss_order = self.order_factory.stop_market(
                instrument_id=self.config.instrument_id,
                order_side=OrderSide.SELL if position.is_net_long() else OrderSide.BUY,
                quantity=abs(position.quantity),
                trigger_price=self.instrument.make_price(stop_loss_price),
            )
            self.submit_order(self.stop_loss_order)
            self.log.info(f"设置止损: {stop_loss_price}")
            
        # 更新止盈单
        if self.take_profit_order is None:
            self.take_profit_order = self.order_factory.limit(
                instrument_id=self.config.instrument_id,
                order_side=OrderSide.SELL if position.is_net_long() else OrderSide.BUY,
                quantity=abs(position.quantity),
                price=self.instrument.make_price(take_profit_price),
                time_in_force=TimeInForce.GTC,
            )
            self.submit_order(self.take_profit_order)
            self.log.info(f"设置止盈: {take_profit_price}")
            
    def on_quote_tick(self, tick: QuoteTick) -> None:
        """处理报价数据"""
        # 可以在这里实现基于tick的交易逻辑
        pass
        
    def on_trade_tick(self, tick: TradeTick) -> None:
        """处理成交数据"""
        # 可以在这里实现基于成交的交易逻辑
        pass
        
    def on_order_book(self, order_book: OrderBook) -> None:
        """处理订单簿数据"""
        # 可以在这里实现基于订单簿的交易逻辑
        pass
        
    def on_order_book_deltas(self, deltas: OrderBookDeltas) -> None:
        """处理订单簿变化"""
        # 可以在这里实现基于订单簿变化的交易逻辑
        pass
        
    def on_data(self, data: Data) -> None:
        """处理其他数据"""
        pass
        
    def on_event(self, event: Event) -> None:
        """处理事件"""
        pass
        
    def on_stop(self) -> None:
        """策略停止时的清理操作"""
        self.cancel_all_orders(self.config.instrument_id)
        if self.config.close_positions_on_stop:
            self.close_all_positions(
                instrument_id=self.config.instrument_id,
                reduce_only=self.config.reduce_only_on_stop,
            )
        self.log.info("自定义RSI+EMA策略已停止")
        
    def on_reset(self) -> None:
        """策略重置"""
        # 重置指标
        self.ema.reset()
        self.rsi.reset()
        
        # 重置状态
        self.last_signal = None
        self.entry_price = None
        self.stop_loss_order = None
        self.take_profit_order = None
        
    def on_save(self) -> dict[str, bytes]:
        """保存策略状态"""
        return {}
        
    def on_load(self, state: dict[str, bytes]) -> None:
        """加载策略状态"""
        pass
        
    def on_dispose(self) -> None:
        """策略销毁"""
        pass


def create_trading_node_config():
    """创建交易节点配置"""
    return TradingNodeConfig(
        trader_id=TraderId("CUSTOM-RSI-EMA-001"),
        logging=LoggingConfig(
            log_level="INFO",
            log_to_file=True,
            log_file_path="custom_rsi_ema_trading.log",
        ),
        exec_engine=LiveExecEngineConfig(
            reconciliation=True,
            reconciliation_lookback_mins=1440,
        ),
        cache=CacheConfig(
            timestamps_as_iso8601=True,
            flush_on_start=False,
        ),
        data_clients={
            BINANCE: BinanceDataClientConfig(
                api_key=None,  # 从环境变量读取
                api_secret=None,  # 从环境变量读取
                account_type=BinanceAccountType.SPOT,
                testnet=True,  # 使用测试网
                instrument_provider=InstrumentProviderConfig(
                    load_all=True,
                    log_warnings=False,
                ),
            ),
        },
        exec_clients={
            BINANCE: BinanceExecClientConfig(
                api_key=None,  # 从环境变量读取
                api_secret=None,  # 从环境变量读取
                account_type=BinanceAccountType.SPOT,
                testnet=True,  # 使用测试网
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
    return CustomRSIEMAConfig(
        instrument_id=InstrumentId.from_str("BTCUSDT.BINANCE"),
        bar_type=BarType.from_str("BTCUSDT.BINANCE-1-MINUTE-LAST-EXTERNAL"),
        trade_size=Decimal("0.001"),  # 交易数量
        ema_period=20,  # EMA周期
        rsi_period=14,  # RSI周期
        rsi_overbought=70.0,  # RSI超买线
        rsi_oversold=30.0,  # RSI超卖线
        stop_loss_pct=0.02,  # 2%止损
        take_profit_pct=0.04,  # 4%止盈
        max_position_size=Decimal("1.0"),  # 最大持仓
        min_balance=Decimal("100.0"),  # 最小余额
        subscribe_quote_ticks=True,
        subscribe_trade_ticks=True,
        request_bars=True,
        unsubscribe_data_on_stop=True,
        close_positions_on_stop=True,
        reduce_only_on_stop=True,
    )


def main():
    """主函数"""
    print("🚀 启动自定义 RSI + EMA 策略")
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
        print("📈 创建自定义RSI+EMA策略...")
        strategy = CustomRSIEMAStrategy(config=strat_config)
        
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
        print(f"   - EMA周期: {strat_config.ema_period}")
        print(f"   - RSI周期: {strat_config.rsi_period}")
        print(f"   - RSI超买线: {strat_config.rsi_overbought}")
        print(f"   - RSI超卖线: {strat_config.rsi_oversold}")
        print(f"   - 止损比例: {strat_config.stop_loss_pct * 100}%")
        print(f"   - 止盈比例: {strat_config.take_profit_pct * 100}%")
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
