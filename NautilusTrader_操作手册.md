# NautilusTrader 详细操作手册

## 目录
1. [项目概述](#项目概述)
2. [安装与配置](#安装与配置)
3. [核心模块详解](#核心模块详解)
4. [Binance适配器](#binance适配器)
5. [策略开发指南](#策略开发指南)
6. [实战示例](#实战示例)
7. [故障排除](#故障排除)

## 项目概述

NautilusTrader 是一个开源的高性能量化交易平台，专为专业量化交易者设计。

### 核心特性
- **高性能**: Rust核心 + Python接口
- **可靠性**: 类型安全和线程安全
- **跨平台**: Linux/macOS/Windows支持
- **模块化**: 支持多种交易所适配器
- **一致性**: 回测与实盘代码统一

### 架构组件
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TradingNode   │    │    Strategy     │    │   DataClient    │
│   (交易节点)     │◄──►│   (交易策略)    │◄──►│   (数据客户端)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ExecClient    │    │     Cache       │    │   MessageBus    │
│   (执行客户端)   │    │   (缓存系统)    │    │   (消息总线)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 安装与配置

### 系统要求
- **操作系统**: Linux (Ubuntu 22.04+), macOS 15.0+, Windows Server 2022+
- **Python版本**: 3.11-3.13
- **架构**: 64位 (x86_64 或 ARM64)

### 安装方式

#### 方式一: PyPI安装 (推荐)
```bash
# 基础安装
pip install -U nautilus_trader

# 包含Binance支持
pip install -U "nautilus_trader[binance]"

# 包含所有适配器
pip install -U "nautilus_trader[all]"
```

#### 方式二: 源码安装
```bash
# 1. 安装Rust工具链
curl https://sh.rustup.rs -sSf | sh
source $HOME/.cargo/env

# 2. 安装clang
sudo apt-get install clang  # Linux
# Windows: 安装Visual Studio Build Tools 2022

# 3. 安装uv包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 4. 克隆并安装
git clone --branch develop --depth 1 https://github.com/nautechsystems/nautilus_trader
cd nautilus_trader
uv sync --all-extras
```

### 验证安装
```python
import nautilus_trader
print(f"NautilusTrader版本: {nautilus_trader.__version__}")

# 测试导入
from nautilus_trader.adapters.binance import BINANCE
print("Binance适配器导入成功")
```

## 核心模块详解

### 1. TradingNode (交易节点)

TradingNode是NautilusTrader的核心组件，负责管理整个交易系统。

#### 主要功能
- 协调各个组件
- 管理策略生命周期
- 处理数据流和执行流
- 提供统一的配置接口

#### 配置示例
```python
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.identifiers import TraderId

config = TradingNodeConfig(
    trader_id=TraderId("MY-TRADER-001"),
    logging=LoggingConfig(log_level="INFO"),
    timeout_connection=30.0,
    timeout_reconciliation=10.0,
    timeout_portfolio=10.0,
    timeout_disconnection=10.0,
    timeout_post_stop=5.0,
)
```

#### 关键参数说明
- `trader_id`: 交易者唯一标识
- `logging`: 日志配置
- `timeout_*`: 各种超时设置
- `data_clients`: 数据客户端配置
- `exec_clients`: 执行客户端配置

### 2. Strategy (交易策略)

Strategy是交易逻辑的核心实现。

#### 策略生命周期
```python
class MyStrategy(Strategy):
    def on_start(self) -> None:
        """策略启动时调用"""
        pass
        
    def on_stop(self) -> None:
        """策略停止时调用"""
        pass
        
    def on_reset(self) -> None:
        """策略重置时调用"""
        pass
        
    def on_save(self) -> dict[str, bytes]:
        """保存策略状态"""
        return {}
        
    def on_load(self, state: dict[str, bytes]) -> None:
        """加载策略状态"""
        pass
```

#### 数据事件处理
```python
def on_bar(self, bar: Bar) -> None:
    """处理K线数据"""
    pass
    
def on_quote_tick(self, tick: QuoteTick) -> None:
    """处理报价数据"""
    pass
    
def on_trade_tick(self, tick: TradeTick) -> None:
    """处理成交数据"""
    pass
    
def on_order_book(self, order_book: OrderBook) -> None:
    """处理订单簿数据"""
    pass
```

#### 订单管理
```python
def submit_order(self, order: Order) -> None:
    """提交订单"""
    pass
    
def cancel_order(self, order: Order) -> None:
    """取消订单"""
    pass
    
def cancel_all_orders(self, instrument_id: InstrumentId) -> None:
    """取消所有订单"""
    pass
```

### 3. DataClient (数据客户端)

DataClient负责接收和处理市场数据。

#### 主要功能
- 连接数据源
- 订阅市场数据
- 数据格式转换
- 错误处理和重连

#### 配置示例
```python
from nautilus_trader.adapters.binance import BinanceDataClientConfig
from nautilus_trader.adapters.binance import BinanceAccountType

data_config = BinanceDataClientConfig(
    api_key="your_api_key",
    api_secret="your_api_secret",
    account_type=BinanceAccountType.SPOT,
    testnet=False,
    instrument_provider=InstrumentProviderConfig(load_all=True),
)
```

### 4. ExecClient (执行客户端)

ExecClient负责订单执行和账户管理。

#### 主要功能
- 订单提交
- 订单状态跟踪
- 账户余额查询
- 持仓管理

#### 配置示例
```python
from nautilus_trader.adapters.binance import BinanceExecClientConfig

exec_config = BinanceExecClientConfig(
    api_key="your_api_key",
    api_secret="your_api_secret",
    account_type=BinanceAccountType.SPOT,
    testnet=False,
    max_retries=3,
    retry_delay_initial_ms=1_000,
    retry_delay_max_ms=10_000,
)
```

### 5. Cache (缓存系统)

Cache提供高效的数据存储和检索。

#### 主要功能
- 市场数据缓存
- 订单状态缓存
- 持仓信息缓存
- 历史数据存储

#### 配置示例
```python
from nautilus_trader.cache.config import CacheConfig

cache_config = CacheConfig(
    timestamps_as_iso8601=True,
    flush_on_start=False,
)
```

### 6. Portfolio (投资组合)

Portfolio管理账户状态和风险。

#### 主要功能
- 余额跟踪
- 持仓管理
- 盈亏计算
- 风险监控

#### 使用示例
```python
# 检查账户状态
if self.portfolio.is_flat(instrument_id):
    # 空仓状态
    pass
elif self.portfolio.is_net_long(instrument_id):
    # 多头持仓
    pass
elif self.portfolio.is_net_short(instrument_id):
    # 空头持仓
    pass

# 获取持仓信息
position = self.portfolio.net_position(instrument_id)
balance = self.portfolio.account_balance()
```

## Binance适配器

### 支持的账户类型
| 账户类型 | 支持状态 | 说明 |
|---------|---------|------|
| Spot现货 | ✅ | 完全支持 |
| USDT永续合约 | ✅ | 完全支持 |
| Coin永续合约 | ✅ | 完全支持 |
| 保证金交易 | ❌ | 暂不支持 |

### 订单类型支持
| 订单类型 | Spot | Futures | 说明 |
|---------|------|---------|------|
| MARKET | ✅ | ✅ | 市价单 |
| LIMIT | ✅ | ✅ | 限价单 |
| STOP_MARKET | ❌ | ✅ | 止损市价单 |
| STOP_LIMIT | ✅ | ✅ | 止损限价单 |
| TRAILING_STOP_MARKET | ❌ | ✅ | 跟踪止损市价单 |

### 配置参数详解

#### BinanceDataClientConfig
```python
class BinanceDataClientConfig:
    api_key: str | None = None
    api_secret: str | None = None
    account_type: BinanceAccountType
    base_url_http: str | None = None
    base_url_ws: str | None = None
    us: bool = False  # Binance US
    testnet: bool = False
    instrument_provider: InstrumentProviderConfig
    use_agg_trade_ticks: bool = False
```

#### BinanceExecClientConfig
```python
class BinanceExecClientConfig:
    api_key: str | None = None
    api_secret: str | None = None
    account_type: BinanceAccountType
    base_url_http: str | None = None
    base_url_ws: str | None = None
    us: bool = False
    testnet: bool = False
    instrument_provider: InstrumentProviderConfig
    use_gtd: bool = True
    use_reduce_only: bool = True
    use_position_ids: bool = True
    treat_expired_as_canceled: bool = False
    futures_leverages: dict[str, int] | None = None
    futures_margin_types: dict[str, str] | None = None
```

### 特殊功能

#### 价格匹配模式 (Futures)
```python
order = strategy.order_factory.limit(
    instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    order_side=OrderSide.BUY,
    quantity=Quantity.from_int(1),
    price=Price.from_str("65000"),
)

strategy.submit_order(
    order,
    params={"price_match": "QUEUE"},  # 价格匹配模式
)
```

#### 跟踪止损
```python
order = strategy.order_factory.trailing_stop_market(
    instrument_id=instrument_id,
    order_side=OrderSide.SELL,
    quantity=quantity,
    trailing_offset=Decimal("0.01"),  # 1%回调
    activation_price=Price.from_str("60000"),  # 激活价格
)
```

## 策略开发指南

### 1. 策略配置
```python
from nautilus_trader.config import StrategyConfig

class MyStrategyConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    # 其他参数...
```

### 2. 指标使用
```python
from nautilus_trader.indicators import ExponentialMovingAverage
from nautilus_trader.indicators import RelativeStrengthIndex

class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig):
        super().__init__(config)
        
        # 创建指标
        self.ema = ExponentialMovingAverage(20)
        self.rsi = RelativeStrengthIndex(14)
        
    def on_start(self):
        # 注册指标
        self.register_indicator_for_bars(self.config.bar_type, self.ema)
        self.register_indicator_for_bars(self.config.bar_type, self.rsi)
```

### 3. 订单工厂
```python
# 市价单
market_order = self.order_factory.market(
    instrument_id=instrument_id,
    order_side=OrderSide.BUY,
    quantity=quantity,
    time_in_force=TimeInForce.GTC,
)

# 限价单
limit_order = self.order_factory.limit(
    instrument_id=instrument_id,
    order_side=OrderSide.BUY,
    quantity=quantity,
    price=price,
    time_in_force=TimeInForce.GTC,
)

# 止损单
stop_order = self.order_factory.stop_market(
    instrument_id=instrument_id,
    order_side=OrderSide.SELL,
    quantity=quantity,
    trigger_price=trigger_price,
)
```

### 4. 风险控制
```python
def check_risk_limits(self) -> bool:
    """检查风险限制"""
    # 检查最大持仓
    position = self.portfolio.net_position(self.config.instrument_id)
    if abs(position.quantity) > self.max_position_size:
        self.log.warning("超过最大持仓限制")
        return False
        
    # 检查账户余额
    balance = self.portfolio.account_balance()
    if balance.free < self.min_balance:
        self.log.warning("账户余额不足")
        return False
        
    return True
```

## 实战示例

### 示例1: 简单EMA交叉策略
```python
# 见 binance_spot_ema_cross.py
```

### 示例2: 期货对冲策略
```python
# 见 binance_futures_hedge.py
```

### 示例3: 自定义RSI策略
```python
# 见 custom_rsi_strategy.py
```

## 故障排除

### 常见问题

#### 1. 连接问题
**问题**: 无法连接到Binance API
**解决方案**:
- 检查网络连接
- 验证API密钥和密钥
- 确认API权限设置
- 检查防火墙设置

#### 2. 订单问题
**问题**: 订单被拒绝
**解决方案**:
- 检查订单参数
- 验证账户余额
- 确认交易对状态
- 检查最小交易量

#### 3. 数据问题
**问题**: 接收不到市场数据
**解决方案**:
- 检查数据订阅
- 验证网络连接
- 确认交易对存在
- 检查API限制

#### 4. 权限问题
**问题**: API权限不足
**解决方案**:
- 检查API密钥权限
- 确认交易权限
- 验证IP白名单
- 检查API限制

### 调试技巧

#### 1. 日志配置
```python
logging_config = LoggingConfig(
    log_level="DEBUG",  # 详细日志
    log_to_file=True,   # 保存到文件
    log_file_path="trading.log",
)
```

#### 2. 测试模式
```python
# 使用测试网
testnet=True

# 小资金测试
trade_size=Decimal("0.001")
```

#### 3. 错误处理
```python
try:
    # 交易逻辑
    self.submit_order(order)
except Exception as e:
    self.log.error(f"订单提交失败: {e}")
    # 错误处理逻辑
```

## 最佳实践

### 1. 开发流程
1. **回测验证**: 历史数据测试
2. **模拟交易**: 测试网验证
3. **小资金实盘**: 真实环境测试
4. **逐步放大**: 确认稳定后增加资金

### 2. 代码规范
- 使用类型提示
- 添加详细注释
- 遵循PEP8规范
- 编写单元测试

### 3. 风险控制
- 设置止损
- 限制仓位大小
- 监控回撤
- 定期检查

### 4. 监控告警
- 策略状态监控
- 异常情况告警
- 性能指标跟踪
- 日志分析

---

**免责声明**: 本手册仅供学习参考，不构成投资建议。量化交易存在风险，请谨慎操作。
