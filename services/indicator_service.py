"""
Advanced Trading Indicators Suite
Complete technical analysis toolkit for crypto futures trading

Author: Trading System
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TrendStrength(Enum):
    """Enum for trend strength classification"""
    RANGING = "ranging"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class IndicatorResult:
    """Standardized indicator result container"""
    name: str
    value: float
    signal: str  # bullish, bearish, neutral
    strength: float  # 0-100
    metadata: Dict[str, Any]


class AdvancedIndicators:
    """
    Comprehensive technical indicators calculator
    Includes all major indicators for crypto futures trading
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # ============= TREND INDICATORS =============
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=period, min_periods=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Exponential Moving Average
        More responsive to recent price changes than SMA
        """
        return prices.ewm(span=period, adjust=False, min_periods=period).mean()
    
    def calculate_wma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Weighted Moving Average
        Recent prices have more weight
        """
        weights = np.arange(1, period + 1)
        
        def wma_calc(x):
            return np.dot(x, weights) / weights.sum()
        
        return prices.rolling(window=period, min_periods=period).apply(wma_calc, raw=True)
    
    def calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                      volume: pd.Series, reset_period: Optional[int] = None) -> pd.Series:
        """
        Volume Weighted Average Price
        Shows the average price weighted by volume
        
        Args:
            reset_period: If provided, resets VWAP every N periods (for intraday)
        """
        typical_price = (high + low + close) / 3
        
        if reset_period is None:
            # Standard cumulative VWAP
            vwap = (typical_price * volume).cumsum() / volume.cumsum()
        else:
            # Reset VWAP periodically
            vwap = pd.Series(index=close.index, dtype=float)
            for i in range(0, len(close), reset_period):
                end = min(i + reset_period, len(close))
                segment_tp = typical_price.iloc[i:end]
                segment_vol = volume.iloc[i:end]
                vwap.iloc[i:end] = (segment_tp * segment_vol).cumsum() / segment_vol.cumsum()
        
        return vwap
    
    def calculate_supertrend(self, high: pd.Series, low: pd.Series, close: pd.Series,
                            period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
        """
        Supertrend Indicator
        ATR-based trend follower
        
        Returns:
            supertrend: Supertrend line values
            direction: 1 for bullish, -1 for bearish
        """
        # Calculate ATR
        atr = self.calculate_atr(high, low, close, period)
        hl_avg = (high + low) / 2
        
        # Basic bands
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        # Initialize
        final_upper = upper_band.copy()
        final_lower = lower_band.copy()
        supertrend = pd.Series(index=close.index, dtype=float)
        direction = pd.Series(index=close.index, dtype=int)
        
        # Calculate
        for i in range(period, len(close)):
            # Final upper band
            if upper_band.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1]:
                final_upper.iloc[i] = upper_band.iloc[i]
            else:
                final_upper.iloc[i] = final_upper.iloc[i-1]
            
            # Final lower band
            if lower_band.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1]:
                final_lower.iloc[i] = lower_band.iloc[i]
            else:
                final_lower.iloc[i] = final_lower.iloc[i-1]
            
            # Supertrend
            if i == period:
                supertrend.iloc[i] = final_upper.iloc[i]
                direction.iloc[i] = -1
            else:
                if supertrend.iloc[i-1] == final_upper.iloc[i-1] and close.iloc[i] <= final_upper.iloc[i]:
                    supertrend.iloc[i] = final_upper.iloc[i]
                    direction.iloc[i] = -1
                elif supertrend.iloc[i-1] == final_upper.iloc[i-1] and close.iloc[i] > final_upper.iloc[i]:
                    supertrend.iloc[i] = final_lower.iloc[i]
                    direction.iloc[i] = 1
                elif supertrend.iloc[i-1] == final_lower.iloc[i-1] and close.iloc[i] >= final_lower.iloc[i]:
                    supertrend.iloc[i] = final_lower.iloc[i]
                    direction.iloc[i] = 1
                elif supertrend.iloc[i-1] == final_lower.iloc[i-1] and close.iloc[i] < final_lower.iloc[i]:
                    supertrend.iloc[i] = final_upper.iloc[i]
                    direction.iloc[i] = -1
        
        return supertrend, direction
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                     period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Average Directional Index (ADX)
        Measures trend strength (not direction)
        
        Returns:
            adx: Trend strength (0-100)
            plus_di: Positive directional indicator
            minus_di: Negative directional indicator
        """
        # Calculate True Range
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Convert to Series
        plus_dm = pd.Series(plus_dm, index=high.index)
        minus_dm = pd.Series(minus_dm, index=low.index)
        
        # Smooth with Wilder's method
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    def calculate_ichimoku(self, high: pd.Series, low: pd.Series, close: pd.Series,
                          tenkan_period: int = 9, kijun_period: int = 26,
                          senkou_b_period: int = 52) -> Dict[str, pd.Series]:
        """
        Ichimoku Cloud
        Complete trading system showing trend, momentum, support/resistance
        
        Returns dict with:
            - tenkan_sen: Conversion line
            - kijun_sen: Base line
            - senkou_span_a: Leading span A (cloud edge 1)
            - senkou_span_b: Leading span B (cloud edge 2)
            - chikou_span: Lagging span
        """
        # Tenkan-sen (Conversion Line)
        tenkan_high = high.rolling(tenkan_period).max()
        tenkan_low = low.rolling(tenkan_period).min()
        tenkan = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Base Line)
        kijun_high = high.rolling(kijun_period).max()
        kijun_low = low.rolling(kijun_period).min()
        kijun = (kijun_high + kijun_low) / 2
        
        # Senkou Span A (Leading Span A)
        senkou_a = ((tenkan + kijun) / 2).shift(kijun_period)
        
        # Senkou Span B (Leading Span B)
        senkou_b_high = high.rolling(senkou_b_period).max()
        senkou_b_low = low.rolling(senkou_b_period).min()
        senkou_b = ((senkou_b_high + senkou_b_low) / 2).shift(kijun_period)
        
        # Chikou Span (Lagging Span)
        chikou = close.shift(-kijun_period)
        
        return {
            'tenkan_sen': tenkan,
            'kijun_sen': kijun,
            'senkou_span_a': senkou_a,
            'senkou_span_b': senkou_b,
            'chikou_span': chikou,
            'cloud_top': pd.concat([senkou_a, senkou_b], axis=1).max(axis=1),
            'cloud_bottom': pd.concat([senkou_a, senkou_b], axis=1).min(axis=1)
        }
    
    # ============= MOMENTUM INDICATORS =============
    
    def calculate_rsi_wilder(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI using Wilder's smoothing method (correct calculation)
        """
        delta = prices.diff()
        
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        # First values: simple average
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        
        # Subsequent values: Wilder's smoothing
        for i in range(period, len(gain)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series,
                            k_period: int = 14, d_period: int = 3, 
                            smooth_k: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator
        Shows momentum and overbought/oversold conditions
        
        Returns:
            k_line: Fast stochastic (%K)
            d_line: Slow stochastic (%D) - signal line
        """
        # Lowest low and highest high
        lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
        highest_high = high.rolling(window=k_period, min_periods=k_period).max()
        
        # Fast %K
        fast_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        # Smooth %K
        k_line = fast_k.rolling(window=smooth_k, min_periods=smooth_k).mean()
        
        # %D (signal line)
        d_line = k_line.rolling(window=d_period, min_periods=d_period).mean()
        
        return k_line, d_line
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, 
                      signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence
        
        Returns:
            macd_line: MACD line
            signal_line: Signal line
            histogram: MACD histogram
        """
        ema_fast = prices.ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = prices.ewm(span=slow, adjust=False, min_periods=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series,
                            period: int = 14) -> pd.Series:
        """
        Williams %R
        Momentum indicator similar to stochastic but inverted
        Range: -100 to 0 (oversold > -20, overbought < -80)
        """
        highest_high = high.rolling(window=period, min_periods=period).max()
        lowest_low = low.rolling(window=period, min_periods=period).min()
        
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        
        return williams_r
    
    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series,
                     period: int = 20) -> pd.Series:
        """
        Commodity Channel Index
        Measures deviation from average price
        Range: typically -100 to +100 (overbought > +100, oversold < -100)
        """
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period, min_periods=period).mean()
        mean_deviation = typical_price.rolling(window=period, min_periods=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )
        
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        
        return cci
    
    def calculate_roc(self, prices: pd.Series, period: int = 12) -> pd.Series:
        """
        Rate of Change
        Momentum indicator showing percentage change
        """
        roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
        return roc
    
    # ============= VOLATILITY INDICATORS =============
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                     period: int = 14) -> pd.Series:
        """Average True Range - volatility measure"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period, min_periods=period).mean()
        
        return atr
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, 
                                 std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        Volatility bands around moving average
        
        Returns:
            upper_band, middle_band, lower_band
        """
        middle_band = prices.rolling(window=period, min_periods=period).mean()
        std = prices.rolling(window=period, min_periods=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    def calculate_keltner_channels(self, high: pd.Series, low: pd.Series, close: pd.Series,
                                   period: int = 20, multiplier: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Keltner Channels
        Similar to Bollinger Bands but uses ATR instead of standard deviation
        
        Returns:
            upper_channel, middle_line, lower_channel
        """
        middle_line = close.ewm(span=period, adjust=False, min_periods=period).mean()
        atr = self.calculate_atr(high, low, close, period)
        
        upper_channel = middle_line + (multiplier * atr)
        lower_channel = middle_line - (multiplier * atr)
        
        return upper_channel, middle_line, lower_channel
    
    def calculate_donchian_channels(self, high: pd.Series, low: pd.Series,
                                    period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Donchian Channels
        Shows highest high and lowest low over period
        """
        upper_channel = high.rolling(window=period, min_periods=period).max()
        lower_channel = low.rolling(window=period, min_periods=period).min()
        middle_channel = (upper_channel + lower_channel) / 2
        
        return upper_channel, middle_channel, lower_channel
    
    # ============= VOLUME INDICATORS =============
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume
        Cumulative volume indicator based on price direction
        """
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def calculate_cmf(self, high: pd.Series, low: pd.Series, close: pd.Series,
                     volume: pd.Series, period: int = 20) -> pd.Series:
        """
        Chaikin Money Flow
        Measures buying/selling pressure
        Range: -1 to +1 (> 0.05 bullish, < -0.05 bearish)
        """
        mf_multiplier = ((close - low) - (high - close)) / (high - low)
        mf_multiplier = mf_multiplier.fillna(0)  # Handle division by zero
        mf_volume = mf_multiplier * volume
        
        cmf = mf_volume.rolling(window=period, min_periods=period).sum() / \
              volume.rolling(window=period, min_periods=period).sum()
        
        return cmf
    
    def calculate_mfi(self, high: pd.Series, low: pd.Series, close: pd.Series,
                     volume: pd.Series, period: int = 14) -> pd.Series:
        """
        Money Flow Index
        Volume-weighted RSI
        Range: 0-100 (oversold < 20, overbought > 80)
        """
        typical_price = (high + low + close) / 3
        raw_money_flow = typical_price * volume
        
        # Positive and negative money flow
        positive_flow = pd.Series(0.0, index=close.index)
        negative_flow = pd.Series(0.0, index=close.index)
        
        for i in range(1, len(typical_price)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                positive_flow.iloc[i] = raw_money_flow.iloc[i]
            elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                negative_flow.iloc[i] = raw_money_flow.iloc[i]
        
        positive_mf = positive_flow.rolling(window=period, min_periods=period).sum()
        negative_mf = negative_flow.rolling(window=period, min_periods=period).sum()
        
        mfi = 100 - (100 / (1 + positive_mf / negative_mf))
        
        return mfi
    
    def calculate_vwma(self, close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """
        Volume Weighted Moving Average
        Moving average weighted by volume
        """
        vwma = (close * volume).rolling(window=period, min_periods=period).sum() / \
               volume.rolling(window=period, min_periods=period).sum()
        
        return vwma
    
    # ============= SUPPORT/RESISTANCE INDICATORS =============
    
    def calculate_pivot_points(self, high: float, low: float, close: float,
                              pivot_type: str = 'standard') -> Dict[str, float]:
        """
        Pivot Points
        Support and resistance levels for day trading
        
        Args:
            pivot_type: 'standard', 'fibonacci', or 'camarilla'
        """
        pivot = (high + low + close) / 3
        
        if pivot_type == 'standard':
            r1 = 2 * pivot - low
            r2 = pivot + (high - low)
            r3 = high + 2 * (pivot - low)
            s1 = 2 * pivot - high
            s2 = pivot - (high - low)
            s3 = low - 2 * (high - pivot)
            
        elif pivot_type == 'fibonacci':
            r1 = pivot + 0.382 * (high - low)
            r2 = pivot + 0.618 * (high - low)
            r3 = pivot + 1.000 * (high - low)
            s1 = pivot - 0.382 * (high - low)
            s2 = pivot - 0.618 * (high - low)
            s3 = pivot - 1.000 * (high - low)
            
        elif pivot_type == 'camarilla':
            r1 = close + (high - low) * 1.1 / 12
            r2 = close + (high - low) * 1.1 / 6
            r3 = close + (high - low) * 1.1 / 4
            r4 = close + (high - low) * 1.1 / 2
            s1 = close - (high - low) * 1.1 / 12
            s2 = close - (high - low) * 1.1 / 6
            s3 = close - (high - low) * 1.1 / 4
            s4 = close - (high - low) * 1.1 / 2
            
            return {
                'pivot': pivot,
                'r4': r4, 'r3': r3, 'r2': r2, 'r1': r1,
                's1': s1, 's2': s2, 's3': s3, 's4': s4
            }
        
        return {
            'pivot': pivot,
            'r3': r3, 'r2': r2, 'r1': r1,
            's1': s1, 's2': s2, 's3': s3
        }
    
    def calculate_fibonacci_retracement(self, high: float, low: float, 
                                       is_uptrend: bool = True) -> Dict[str, float]:
        """
        Fibonacci Retracement Levels
        Key support/resistance levels
        """
        diff = high - low
        
        if is_uptrend:
            # For uptrend, levels below high
            return {
                '0.0': high,
                '23.6': high - 0.236 * diff,
                '38.2': high - 0.382 * diff,
                '50.0': high - 0.500 * diff,
                '61.8': high - 0.618 * diff,
                '78.6': high - 0.786 * diff,
                '100.0': low
            }
        else:
            # For downtrend, levels above low
            return {
                '0.0': low,
                '23.6': low + 0.236 * diff,
                '38.2': low + 0.382 * diff,
                '50.0': low + 0.500 * diff,
                '61.8': low + 0.618 * diff,
                '78.6': low + 0.786 * diff,
                '100.0': high
            }
    
    def calculate_parabolic_sar(self, high: pd.Series, low: pd.Series, close: pd.Series,
                               af: float = 0.02, max_af: float = 0.2) -> pd.Series:
        """
        Parabolic SAR
        Trailing stop and trend indicator
        """
        sar = pd.Series(index=close.index, dtype=float)
        ep = pd.Series(index=close.index, dtype=float)  # Extreme point
        af_series = pd.Series(index=close.index, dtype=float)
        trend = pd.Series(index=close.index, dtype=int)  # 1 for up, -1 for down
        
        # Initialize
        sar.iloc[0] = low.iloc[0]
        ep.iloc[0] = high.iloc[0]
        af_series.iloc[0] = af
        trend.iloc[0] = 1
        
        for i in range(1, len(close)):
            # Update SAR
            sar.iloc[i] = sar.iloc[i-1] + af_series.iloc[i-1] * (ep.iloc[i-1] - sar.iloc[i-1])
            
            # Check for trend reversal
            if trend.iloc[i-1] == 1:  # Uptrend
                if low.iloc[i] < sar.iloc[i]:
                    # Reversal to downtrend
                    trend.iloc[i] = -1
                    sar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = low.iloc[i]
                    af_series.iloc[i] = af
                else:
                    # Continue uptrend
                    trend.iloc[i] = 1
                    if high.iloc[i] > ep.iloc[i-1]:
                        ep.iloc[i] = high.iloc[i]
                        af_series.iloc[i] = min(af_series.iloc[i-1] + af, max_af)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af_series.iloc[i] = af_series.iloc[i-1]
            else:  # Downtrend
                if high.iloc[i] > sar.iloc[i]:
                    # Reversal to uptrend
                    trend.iloc[i] = 1
                    sar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = high.iloc[i]
                    af_series.iloc[i] = af
                else:
                    # Continue downtrend
                    trend.iloc[i] = -1
                    if low.iloc[i] < ep.iloc[i-1]:
                        ep.iloc[i] = low.iloc[i]
                        af_series.iloc[i] = min(af_series.iloc[i-1] + af, max_af)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af_series.iloc[i] = af_series.iloc[i-1]
        
        return sar
    
    # ============= ADVANCED ANALYSIS =============
    
    def detect_divergence(self, prices: pd.Series, indicator: pd.Series,
                         lookback: int = 10) -> Dict[str, bool]:
        """
        Detect bullish/bearish divergence between price and indicator
        Works with RSI, MACD, Stochastic, etc.
        """
        if len(prices) < lookback + 1:
            return {'bullish_divergence': False, 'bearish_divergence': False}
        
        recent_prices = prices.iloc[-lookback:]
        recent_indicator = indicator.iloc[-lookback:]
        
        # Bullish divergence: Price lower low, Indicator higher low
        price_makes_lower_low = recent_prices.iloc[-1] < recent_prices.iloc[:-1].min()
        indicator_makes_higher_low = recent_indicator.iloc[-1] > recent_indicator.iloc[:-1].min()
        bullish_div = price_makes_lower_low and indicator_makes_higher_low
        
        # Bearish divergence: Price higher high, Indicator lower high
        price_makes_higher_high = recent_prices.iloc[-1] > recent_prices.iloc[:-1].max()
        indicator_makes_lower_high = recent_indicator.iloc[-1] < recent_indicator.iloc[:-1].max()
        bearish_div = price_makes_higher_high and indicator_makes_lower_high
        
        return {
            'bullish_divergence': bullish_div,
            'bearish_divergence': bearish_div
        }
    
    def calculate_trend_strength(self, adx: pd.Series) -> TrendStrength:
        """
        Classify trend strength based on ADX value
        """
        adx_value = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0
        
        if adx_value < 20:
            return TrendStrength.RANGING
        elif adx_value < 25:
            return TrendStrength.WEAK
        elif adx_value < 40:
            return TrendStrength.MODERATE
        elif adx_value < 50:
            return TrendStrength.STRONG
        else:
            return TrendStrength.VERY_STRONG
    
    def calculate_volume_profile(self, close: pd.Series, volume: pd.Series,
                                 num_bins: int = 20) -> Dict[str, Any]:
        """
        Volume Profile Analysis
        Shows volume distribution at different price levels
        """
        price_min = close.min()
        price_max = close.max()
        price_range = price_max - price_min
        bin_size = price_range / num_bins
        
        # Create price bins
        bins = [price_min + i * bin_size for i in range(num_bins + 1)]
        volume_at_price = {f"{bins[i]:.2f}-{bins[i+1]:.2f}": 0 for i in range(num_bins)}
        
        # Accumulate volume in each bin
        for i in range(len(close)):
            price = close.iloc[i]
            vol = volume.iloc[i]
            
            for j in range(num_bins):
                if bins[j] <= price < bins[j+1]:
                    key = f"{bins[j]:.2f}-{bins[j+1]:.2f}"
                    volume_at_price[key] += vol
                    break
        
        # Find POC (Point of Control) - price level with highest volume
        poc_bin = max(volume_at_price, key=volume_at_price.get)
        poc_price = (float(poc_bin.split('-')[0]) + float(poc_bin.split('-')[1])) / 2
        
        # Find Value Area (70% of volume)
        sorted_bins = sorted(volume_at_price.items(), key=lambda x: x[1], reverse=True)
        total_volume = sum(volume_at_price.values())
        value_area_volume = 0
        value_area_bins = []
        
        for bin_name, bin_vol in sorted_bins:
            value_area_bins.append(bin_name)
            value_area_volume += bin_vol
            if value_area_volume >= total_volume * 0.7:
                break
        
        # Extract value area high and low
        value_area_prices = []
        for bin_name in value_area_bins:
            low, high = bin_name.split('-')
            value_area_prices.extend([float(low), float(high)])
        
        vah = max(value_area_prices)  # Value Area High
        val = min(value_area_prices)  # Value Area Low
        
        return {
            'poc': poc_price,
            'vah': vah,
            'val': val,
            'volume_distribution': volume_at_price
        }
    
    # ============= COMPREHENSIVE ANALYSIS =============
    
    def calculate_all_indicators(self, data: pd.DataFrame,
                                 include_advanced: bool = True) -> Dict[str, Any]:
        """
        Calculate ALL indicators at once
        
        Args:
            data: DataFrame with OHLCV columns
            include_advanced: Include computationally expensive indicators
            
        Returns:
            Dictionary with all calculated indicators
        """
        try:
            # Validate data
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_cols):
                raise ValueError(f"Data must contain: {required_cols}")
            
            if len(data) < 52:  # Need at least 52 for Ichimoku
                self.logger.warning("Insufficient data for all indicators (need 52+)")
            
            result = {
                'metadata': {
                    'timestamp': pd.Timestamp.now().isoformat(),
                    'candles_count': len(data),
                    'price_range': {
                        'high': float(data['high'].max()),
                        'low': float(data['low'].min()),
                        'current': float(data['close'].iloc[-1])
                    }
                }
            }
            
            # ===== TREND INDICATORS =====
            result['trend'] = {}
            
            # Moving Averages
            for period in [5, 10, 20, 50, 100, 200]:
                if len(data) >= period:
                    result['trend'][f'sma_{period}'] = float(self.calculate_sma(data['close'], period).iloc[-1])
                    result['trend'][f'ema_{period}'] = float(self.calculate_ema(data['close'], period).iloc[-1])
            
            # VWAP
            if len(data) >= 20:
                vwap = self.calculate_vwap(data['high'], data['low'], data['close'], data['volume'])
                result['trend']['vwap'] = float(vwap.iloc[-1])
            
            # Supertrend
            if len(data) >= 10:
                supertrend, direction = self.calculate_supertrend(
                    data['high'], data['low'], data['close']
                )
                result['trend']['supertrend'] = {
                    'value': float(supertrend.iloc[-1]) if not pd.isna(supertrend.iloc[-1]) else None,
                    'direction': int(direction.iloc[-1]) if not pd.isna(direction.iloc[-1]) else 0,
                    'signal': 'bullish' if direction.iloc[-1] == 1 else 'bearish'
                }
            
            # ADX
            if len(data) >= 14:
                adx, plus_di, minus_di = self.calculate_adx(
                    data['high'], data['low'], data['close']
                )
                adx_val = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0
                result['trend']['adx'] = {
                    'value': adx_val,
                    'plus_di': float(plus_di.iloc[-1]) if not pd.isna(plus_di.iloc[-1]) else 0,
                    'minus_di': float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else 0,
                    'strength': self.calculate_trend_strength(adx).value,
                    'direction': 'bullish' if plus_di.iloc[-1] > minus_di.iloc[-1] else 'bearish'
                }
            
            # Ichimoku (if advanced)
            if include_advanced and len(data) >= 52:
                ichimoku = self.calculate_ichimoku(data['high'], data['low'], data['close'])
                current_price = data['close'].iloc[-1]
                cloud_top = ichimoku['cloud_top'].iloc[-1]
                cloud_bottom = ichimoku['cloud_bottom'].iloc[-1]
                
                result['trend']['ichimoku'] = {
                    'tenkan_sen': float(ichimoku['tenkan_sen'].iloc[-1]),
                    'kijun_sen': float(ichimoku['kijun_sen'].iloc[-1]),
                    'senkou_span_a': float(cloud_top),
                    'senkou_span_b': float(cloud_bottom),
                    'cloud_color': 'green' if cloud_top > cloud_bottom else 'red',
                    'price_vs_cloud': 'above' if current_price > cloud_top else 'below' if current_price < cloud_bottom else 'inside'
                }
            
            # ===== MOMENTUM INDICATORS =====
            result['momentum'] = {}
            
            # RSI
            if len(data) >= 14:
                rsi = self.calculate_rsi_wilder(data['close'], 14)
                rsi_val = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
                rsi_prev = float(rsi.iloc[-2]) if not pd.isna(rsi.iloc[-2]) else 50
                
                result['momentum']['rsi'] = {
                    'value': rsi_val,
                    'previous': rsi_prev,
                    'slope': rsi_val - rsi_prev,
                    'oversold': rsi_val < 30,
                    'overbought': rsi_val > 70,
                    'signal': 'oversold' if rsi_val < 30 else 'overbought' if rsi_val > 70 else 'neutral'
                }
                
                # RSI Divergence
                divergence = self.detect_divergence(data['close'], rsi, lookback=10)
                result['momentum']['rsi']['divergence'] = divergence
            
            # Stochastic
            if len(data) >= 14:
                k_line, d_line = self.calculate_stochastic(
                    data['high'], data['low'], data['close']
                )
                k_val = float(k_line.iloc[-1]) if not pd.isna(k_line.iloc[-1]) else 50
                d_val = float(d_line.iloc[-1]) if not pd.isna(d_line.iloc[-1]) else 50
                
                result['momentum']['stochastic'] = {
                    'k': k_val,
                    'd': d_val,
                    'oversold': k_val < 20 and d_val < 20,
                    'overbought': k_val > 80 and d_val > 80,
                    'bullish_cross': k_val > d_val,
                    'signal': 'oversold' if k_val < 20 else 'overbought' if k_val > 80 else 'neutral'
                }
            
            # MACD
            if len(data) >= 26:
                macd, signal, hist = self.calculate_macd(data['close'])
                macd_val = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0
                signal_val = float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else 0
                hist_val = float(hist.iloc[-1]) if not pd.isna(hist.iloc[-1]) else 0
                
                macd_prev = float(macd.iloc[-2]) if not pd.isna(macd.iloc[-2]) else 0
                signal_prev = float(signal.iloc[-2]) if not pd.isna(signal.iloc[-2]) else 0
                
                result['momentum']['macd'] = {
                    'macd': macd_val,
                    'signal': signal_val,
                    'histogram': hist_val,
                    'bullish': macd_val > signal_val,
                    'cross_up': (macd_val > signal_val) and (macd_prev <= signal_prev),
                    'cross_down': (macd_val < signal_val) and (macd_prev >= signal_prev)
                }
            
            # Williams %R
            if len(data) >= 14:
                williams = self.calculate_williams_r(data['high'], data['low'], data['close'])
                w_val = float(williams.iloc[-1]) if not pd.isna(williams.iloc[-1]) else -50
                
                result['momentum']['williams_r'] = {
                    'value': w_val,
                    'oversold': w_val > -20,
                    'overbought': w_val < -80,
                    'signal': 'oversold' if w_val > -20 else 'overbought' if w_val < -80 else 'neutral'
                }
            
            # CCI
            if len(data) >= 20:
                cci = self.calculate_cci(data['high'], data['low'], data['close'])
                cci_val = float(cci.iloc[-1]) if not pd.isna(cci.iloc[-1]) else 0
                
                result['momentum']['cci'] = {
                    'value': cci_val,
                    'oversold': cci_val < -100,
                    'overbought': cci_val > 100,
                    'signal': 'oversold' if cci_val < -100 else 'overbought' if cci_val > 100 else 'neutral'
                }
            
            # ROC
            if len(data) >= 12:
                roc = self.calculate_roc(data['close'], 12)
                roc_val = float(roc.iloc[-1]) if not pd.isna(roc.iloc[-1]) else 0
                
                result['momentum']['roc'] = {
                    'value': roc_val,
                    'signal': 'bullish' if roc_val > 0 else 'bearish'
                }
            
            # ===== VOLATILITY INDICATORS =====
            result['volatility'] = {}
            
            # ATR
            if len(data) >= 14:
                atr = self.calculate_atr(data['high'], data['low'], data['close'])
                atr_val = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0
                atr_percent = (atr_val / data['close'].iloc[-1]) * 100
                
                result['volatility']['atr'] = {
                    'value': atr_val,
                    'percent': atr_percent,
                    'level': 'high' if atr_percent > 5 else 'low' if atr_percent < 2 else 'medium'
                }
            
            # Bollinger Bands
            if len(data) >= 20:
                bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(data['close'])
                current_price = data['close'].iloc[-1]
                bb_width = ((bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_middle.iloc[-1]) * 100
                bb_position = ((current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])) * 100
                
                result['volatility']['bollinger_bands'] = {
                    'upper': float(bb_upper.iloc[-1]),
                    'middle': float(bb_middle.iloc[-1]),
                    'lower': float(bb_lower.iloc[-1]),
                    'width_percent': float(bb_width),
                    'position_percent': float(bb_position),
                    'squeeze': bb_width < 2,
                    'signal': 'touch_upper' if bb_position > 95 else 'touch_lower' if bb_position < 5 else 'neutral'
                }
            
            # Keltner Channels
            if len(data) >= 20:
                kc_upper, kc_middle, kc_lower = self.calculate_keltner_channels(
                    data['high'], data['low'], data['close']
                )
                
                result['volatility']['keltner_channels'] = {
                    'upper': float(kc_upper.iloc[-1]),
                    'middle': float(kc_middle.iloc[-1]),
                    'lower': float(kc_lower.iloc[-1])
                }
            
            # Donchian Channels
            if len(data) >= 20:
                dc_upper, dc_middle, dc_lower = self.calculate_donchian_channels(
                    data['high'], data['low']
                )
                
                result['volatility']['donchian_channels'] = {
                    'upper': float(dc_upper.iloc[-1]),
                    'middle': float(dc_middle.iloc[-1]),
                    'lower': float(dc_lower.iloc[-1])
                }
            
            # ===== VOLUME INDICATORS =====
            result['volume'] = {}
            
            # Basic volume metrics
            current_vol = data['volume'].iloc[-1]
            avg_vol_20 = data['volume'].rolling(20).mean().iloc[-1]
            vol_ratio = current_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
            
            result['volume']['basic'] = {
                'current': float(current_vol),
                'average_20': float(avg_vol_20),
                'ratio': float(vol_ratio),
                'signal': 'high' if vol_ratio > 1.5 else 'low' if vol_ratio < 0.5 else 'normal'
            }
            
            # OBV
            if len(data) >= 2:
                obv = self.calculate_obv(data['close'], data['volume'])
                obv_val = float(obv.iloc[-1]) if not pd.isna(obv.iloc[-1]) else 0
                obv_ma = obv.rolling(20).mean().iloc[-1]
                
                result['volume']['obv'] = {
                    'value': obv_val,
                    'trend': 'rising' if obv_val > obv_ma else 'falling'
                }
                
                # OBV Divergence
                obv_divergence = self.detect_divergence(data['close'], obv, lookback=10)
                result['volume']['obv']['divergence'] = obv_divergence
            
            # CMF
            if len(data) >= 20:
                cmf = self.calculate_cmf(data['high'], data['low'], data['close'], data['volume'])
                cmf_val = float(cmf.iloc[-1]) if not pd.isna(cmf.iloc[-1]) else 0
                
                result['volume']['cmf'] = {
                    'value': cmf_val,
                    'buying_pressure': cmf_val > 0.05,
                    'selling_pressure': cmf_val < -0.05,
                    'signal': 'bullish' if cmf_val > 0.05 else 'bearish' if cmf_val < -0.05 else 'neutral'
                }
            
            # MFI
            if len(data) >= 14:
                mfi = self.calculate_mfi(data['high'], data['low'], data['close'], data['volume'])
                mfi_val = float(mfi.iloc[-1]) if not pd.isna(mfi.iloc[-1]) else 50
                
                result['volume']['mfi'] = {
                    'value': mfi_val,
                    'oversold': mfi_val < 20,
                    'overbought': mfi_val > 80,
                    'signal': 'oversold' if mfi_val < 20 else 'overbought' if mfi_val > 80 else 'neutral'
                }
            
            # VWMA
            if len(data) >= 20:
                vwma = self.calculate_vwma(data['close'], data['volume'], 20)
                result['volume']['vwma_20'] = float(vwma.iloc[-1])
            
            # Volume Profile (if advanced)
            if include_advanced and len(data) >= 20:
                vol_profile = self.calculate_volume_profile(data['close'], data['volume'])
                result['volume']['profile'] = vol_profile
            
            # ===== SUPPORT/RESISTANCE =====
            result['levels'] = {}
            
            # Basic levels
            swing_high = float(data['high'].iloc[-20:].max())
            swing_low = float(data['low'].iloc[-20:].min())
            current_price = float(data['close'].iloc[-1])
            
            result['levels']['swing'] = {
                'high': swing_high,
                'low': swing_low,
                'range': swing_high - swing_low,
                'position_percent': ((current_price - swing_low) / (swing_high - swing_low)) * 100
            }
            
            # Pivot Points
            last_high = float(data['high'].iloc[-1])
            last_low = float(data['low'].iloc[-1])
            last_close = float(data['close'].iloc[-1])
            
            for pivot_type in ['standard', 'fibonacci', 'camarilla']:
                pivots = self.calculate_pivot_points(last_high, last_low, last_close, pivot_type)
                result['levels'][f'pivot_{pivot_type}'] = pivots
            
            # Fibonacci Retracement
            is_uptrend = data['close'].iloc[-1] > data['close'].iloc[-20]
            fib_levels = self.calculate_fibonacci_retracement(swing_high, swing_low, is_uptrend)
            result['levels']['fibonacci'] = fib_levels
            
            # Parabolic SAR
            if len(data) >= 5:
                sar = self.calculate_parabolic_sar(data['high'], data['low'], data['close'])
                sar_val = float(sar.iloc[-1]) if not pd.isna(sar.iloc[-1]) else current_price
                
                result['levels']['parabolic_sar'] = {
                    'value': sar_val,
                    'signal': 'bullish' if sar_val < current_price else 'bearish'
                }
            
            # ===== COMPOSITE SIGNALS =====
            result['signals'] = self._generate_composite_signals(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _generate_composite_signals(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate composite trading signals from all indicators
        """
        signals = {
            'overall': 'neutral',
            'strength': 0,
            'confidence': 0,
            'details': []
        }
        
        bullish_count = 0
        bearish_count = 0
        total_signals = 0
        
        try:
            # Trend signals
            if 'trend' in indicators and 'adx' in indicators['trend']:
                adx_data = indicators['trend']['adx']
                if adx_data['value'] > 25:
                    total_signals += 1
                    if adx_data['direction'] == 'bullish':
                        bullish_count += 1
                        signals['details'].append('ADX shows strong uptrend')
                    else:
                        bearish_count += 1
                        signals['details'].append('ADX shows strong downtrend')
            
            # Supertrend signal
            if 'trend' in indicators and 'supertrend' in indicators['trend']:
                st_data = indicators['trend']['supertrend']
                total_signals += 1
                if st_data['signal'] == 'bullish':
                    bullish_count += 1
                    signals['details'].append('Supertrend bullish')
                else:
                    bearish_count += 1
                    signals['details'].append('Supertrend bearish')
            
            # RSI signal
            if 'momentum' in indicators and 'rsi' in indicators['momentum']:
                rsi_data = indicators['momentum']['rsi']
                total_signals += 1
                if rsi_data['oversold']:
                    bullish_count += 1
                    signals['details'].append('RSI oversold - bounce potential')
                elif rsi_data['overbought']:
                    bearish_count += 1
                    signals['details'].append('RSI overbought - rejection potential')
                elif rsi_data['value'] > 50:
                    bullish_count += 0.5
                else:
                    bearish_count += 0.5
            
            # Stochastic signal
            if 'momentum' in indicators and 'stochastic' in indicators['momentum']:
                stoch_data = indicators['momentum']['stochastic']
                total_signals += 1
                if stoch_data['oversold']:
                    bullish_count += 1
                    signals['details'].append('Stochastic oversold')
                elif stoch_data['overbought']:
                    bearish_count += 1
                    signals['details'].append('Stochastic overbought')
                elif stoch_data['bullish_cross']:
                    bullish_count += 0.5
                else:
                    bearish_count += 0.5
            
            # MACD signal
            if 'momentum' in indicators and 'macd' in indicators['momentum']:
                macd_data = indicators['momentum']['macd']
                total_signals += 1
                if macd_data['cross_up']:
                    bullish_count += 2  # Strong signal
                    signals['details'].append('MACD bullish crossover')
                elif macd_data['cross_down']:
                    bearish_count += 2  # Strong signal
                    signals['details'].append('MACD bearish crossover')
                elif macd_data['bullish']:
                    bullish_count += 0.5
                else:
                    bearish_count += 0.5
            
            # Volume signal
            if 'volume' in indicators:
                if 'cmf' in indicators['volume']:
                    cmf_data = indicators['volume']['cmf']
                    total_signals += 1
                    if cmf_data['buying_pressure']:
                        bullish_count += 1
                        signals['details'].append('Strong buying pressure (CMF)')
                    elif cmf_data['selling_pressure']:
                        bearish_count += 1
                        signals['details'].append('Strong selling pressure (CMF)')
            
            # Calculate overall signal
            if total_signals > 0:
                bullish_percent = (bullish_count / total_signals) * 100
                bearish_percent = (bearish_count / total_signals) * 100
                
                if bullish_percent > 60:
                    signals['overall'] = 'bullish'
                    signals['strength'] = bullish_percent
                elif bearish_percent > 60:
                    signals['overall'] = 'bearish'
                    signals['strength'] = bearish_percent
                else:
                    signals['overall'] = 'neutral'
                    signals['strength'] = 50
                
                signals['confidence'] = max(bullish_percent, bearish_percent)
                signals['bullish_signals'] = int(bullish_count)
                signals['bearish_signals'] = int(bearish_count)
                signals['total_signals'] = int(total_signals)
        
        except Exception as e:
            self.logger.error(f"Error generating composite signals: {e}")
        
        return signals
    
    def calculate_selected_indicators(self, data: pd.DataFrame, 
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate only selected indicators based on config
        
        Args:
            data: DataFrame with OHLCV columns
            config: Indicator configuration dict with enabled_categories and enabled_indicators
            
        Returns:
            Dictionary with only enabled indicators
        """
        try:
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_cols):
                raise ValueError(f"Data must contain: {required_cols}")
            
            enabled_categories = config.get('enabled_categories', {})
            enabled_indicators = config.get('enabled_indicators', {})
            indicator_periods = config.get('indicator_periods', {})
            
            result = {
                'metadata': {
                    'timestamp': pd.Timestamp.now().isoformat(),
                    'candles_count': len(data),
                    'price_range': {
                        'high': float(data['high'].max()),
                        'low': float(data['low'].min()),
                        'current': float(data['close'].iloc[-1])
                    }
                }
            }
            
            # ===== TREND INDICATORS =====
            if enabled_categories.get('trend', True):
                result['trend'] = {}
                
                # SMA
                if 'sma' in enabled_indicators and enabled_indicators['sma']:
                    sma_periods = enabled_indicators['sma'] if isinstance(enabled_indicators['sma'], list) else []
                    for period in sma_periods:
                        if len(data) >= period:
                            sma = self.calculate_sma(data['close'], period)
                            result['trend'][f'sma_{period}'] = float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None
                
                # EMA
                if 'ema' in enabled_indicators and enabled_indicators['ema']:
                    ema_periods = enabled_indicators['ema'] if isinstance(enabled_indicators['ema'], list) else []
                    for period in ema_periods:
                        if len(data) >= period:
                            ema = self.calculate_ema(data['close'], period)
                            result['trend'][f'ema_{period}'] = float(ema.iloc[-1]) if not pd.isna(ema.iloc[-1]) else None
                
                # ADX
                if enabled_indicators.get('adx', False):
                    if len(data) >= 14:
                        adx, plus_di, minus_di = self.calculate_adx(data['high'], data['low'], data['close'])
                        adx_val = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0
                        result['trend']['adx'] = {
                            'value': adx_val,
                            'plus_di': float(plus_di.iloc[-1]) if not pd.isna(plus_di.iloc[-1]) else 0,
                            'minus_di': float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else 0,
                            'strength': self.calculate_trend_strength(adx).value,
                            'direction': 'bullish' if plus_di.iloc[-1] > minus_di.iloc[-1] else 'bearish'
                        }
                
                # Supertrend
                if enabled_indicators.get('supertrend', False):
                    if len(data) >= 10:
                        supertrend, direction = self.calculate_supertrend(data['high'], data['low'], data['close'])
                        result['trend']['supertrend'] = {
                            'value': float(supertrend.iloc[-1]) if not pd.isna(supertrend.iloc[-1]) else None,
                            'direction': int(direction.iloc[-1]) if not pd.isna(direction.iloc[-1]) else 0,
                            'signal': 'bullish' if direction.iloc[-1] == 1 else 'bearish'
                        }
            
            # ===== MOMENTUM INDICATORS =====
            if enabled_categories.get('momentum', True):
                result['momentum'] = {}
                
                # RSI
                if enabled_indicators.get('rsi', False):
                    rsi_period = indicator_periods.get('rsi_period', 14)
                    if len(data) >= rsi_period:
                        rsi = self.calculate_rsi_wilder(data['close'], rsi_period)
                        rsi_val = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
                        
                        result['momentum']['rsi'] = {
                            'value': rsi_val,
                            'oversold': rsi_val < 30,
                            'overbought': rsi_val > 70,
                            'signal': 'oversold' if rsi_val < 30 else 'overbought' if rsi_val > 70 else 'neutral'
                        }
                
                # MACD
                if enabled_indicators.get('macd', False):
                    macd_fast = indicator_periods.get('macd_fast', 12)
                    macd_slow = indicator_periods.get('macd_slow', 26)
                    macd_signal_period = indicator_periods.get('macd_signal', 9)
                    
                    if len(data) >= macd_slow:
                        macd, signal, hist = self.calculate_macd(data['close'], fast=macd_fast, slow=macd_slow, signal=macd_signal_period)
                        macd_val = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0
                        signal_val = float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else 0
                        
                        result['momentum']['macd'] = {
                            'macd': macd_val,
                            'signal': signal_val,
                            'histogram': float(hist.iloc[-1]) if not pd.isna(hist.iloc[-1]) else 0,
                            'bullish': macd_val > signal_val
                        }
            
            # ===== VOLATILITY INDICATORS =====
            if enabled_categories.get('volatility', True):
                result['volatility'] = {}
                
                # ATR
                if enabled_indicators.get('atr', False):
                    atr_period = indicator_periods.get('atr_period', 14)
                    if len(data) >= atr_period:
                        atr = self.calculate_atr(data['high'], data['low'], data['close'], atr_period)
                        atr_val = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0
                        atr_percent = (atr_val / data['close'].iloc[-1]) * 100
                        
                        result['volatility']['atr'] = {
                            'value': atr_val,
                            'percent': atr_percent,
                            'level': 'high' if atr_percent > 5 else 'low' if atr_percent < 2 else 'medium'
                        }
                
                # Bollinger Bands
                if enabled_indicators.get('bollinger_bands', False):
                    bb_period = indicator_periods.get('bollinger_period', 20)
                    bb_std = indicator_periods.get('bollinger_std', 2.0)
                    
                    if len(data) >= bb_period:
                        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(data['close'], period=bb_period, std_dev=bb_std)
                        current_price = data['close'].iloc[-1]
                        
                        result['volatility']['bollinger_bands'] = {
                            'upper': float(bb_upper.iloc[-1]),
                            'middle': float(bb_middle.iloc[-1]),
                            'lower': float(bb_lower.iloc[-1]),
                        }
            
            # ===== VOLUME INDICATORS =====
            if enabled_categories.get('volume', True):
                result['volume'] = {}
                
                # Basic volume metrics
                current_vol = data['volume'].iloc[-1]
                avg_vol_20 = data['volume'].rolling(20).mean().iloc[-1] if len(data) >= 20 else current_vol
                vol_ratio = current_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
                
                result['volume']['basic'] = {
                    'current': float(current_vol),
                    'average_20': float(avg_vol_20),
                    'ratio': float(vol_ratio)
                }
                
                # OBV
                if enabled_indicators.get('obv', False):
                    if len(data) >= 2:
                        obv = self.calculate_obv(data['close'], data['volume'])
                        result['volume']['obv'] = {
                            'value': float(obv.iloc[-1]) if not pd.isna(obv.iloc[-1]) else 0
                        }
                
                # CMF
                if enabled_indicators.get('cmf', False):
                    if len(data) >= 20:
                        cmf = self.calculate_cmf(data['high'], data['low'], data['close'], data['volume'])
                        cmf_val = float(cmf.iloc[-1]) if not pd.isna(cmf.iloc[-1]) else 0
                        
                        result['volume']['cmf'] = {
                            'value': cmf_val,
                            'signal': 'bullish' if cmf_val > 0.05 else 'bearish' if cmf_val < -0.05 else 'neutral'
                        }
                
                # MFI
                if enabled_indicators.get('mfi', False):
                    if len(data) >= 14:
                        mfi = self.calculate_mfi(data['high'], data['low'], data['close'], data['volume'])
                        mfi_val = float(mfi.iloc[-1]) if not pd.isna(mfi.iloc[-1]) else 50
                        
                        result['volume']['mfi'] = {
                            'value': mfi_val,
                            'signal': 'oversold' if mfi_val < 20 else 'overbought' if mfi_val > 80 else 'neutral'
                        }
            
            # Generate composite signals from enabled indicators
            if result.get('trend') or result.get('momentum') or result.get('volume'):
                result['signals'] = self._generate_composite_signals(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating selected indicators: {e}", exc_info=True)
            return {'error': str(e)}


# ============= USAGE EXAMPLE =============

def example_comprehensive_analysis():
    """
    Example: Calculate all indicators for BTC/USDT
    """
    import ccxt
    
    # Fetch data
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=200)
    
    # Convert to DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Initialize calculator
    calculator = AdvancedIndicators()
    
    # Calculate all indicators
    print("Calculating all indicators...")
    indicators = calculator.calculate_all_indicators(df, include_advanced=True)
    
    # Print results
    import json
    print(json.dumps(indicators, indent=2, default=str))
    
    return indicators


if __name__ == "__main__":
    result = example_comprehensive_analysis()
    result = example_comprehensive_analysis()