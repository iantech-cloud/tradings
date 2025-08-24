"""
Trend-following technical indicators
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from .base_indicator import BaseIndicator

class TrendIndicators(BaseIndicator):
    """Collection of trend-following indicators"""
    
    def __init__(self):
        super().__init__("TrendIndicators")
        self.required_periods = 50  # For longer-term indicators like SMA50
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all trend indicators"""
        if not self.validate_data(data):
            return {}
        
        results = {}
        close = data['close']
        high = data['high']
        low = data['low']
        
        try:
            # Simple Moving Averages
            results['sma_10'] = self.sma(close, 10)
            results['sma_20'] = self.sma(close, 20)
            results['sma_50'] = self.sma(close, 50)
            results['sma_200'] = self.sma(close, 200)
            
            # Exponential Moving Averages
            results['ema_12'] = self.ema(close, 12)
            results['ema_26'] = self.ema(close, 26)
            results['ema_50'] = self.ema(close, 50)
            
            # Weighted Moving Average
            results['wma_20'] = self.wma(close, 20)
            
            # MACD
            macd_data = self.macd(close)
            results.update(macd_data)
            
            # Parabolic SAR
            results['parabolic_sar'] = self.parabolic_sar(high, low, close)
            
            # Average Directional Index (ADX)
            adx_data = self.adx(high, low, close)
            results.update(adx_data)
            
            # Ichimoku Cloud
            ichimoku_data = self.ichimoku_cloud(high, low, close)
            results.update(ichimoku_data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error calculating trend indicators: {str(e)}")
            return {}
    
    def wma(self, data: pd.Series, period: int) -> pd.Series:
        """Weighted Moving Average"""
        weights = np.arange(1, period + 1)
        
        def weighted_mean(x):
            if len(x) < period:
                return np.nan
            return np.dot(x[-period:], weights) / weights.sum()
        
        return data.rolling(window=period).apply(weighted_mean, raw=True)
    
    def macd(self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = self.ema(data, fast)
        ema_slow = self.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        }
    
    def parabolic_sar(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                     af_start: float = 0.02, af_increment: float = 0.02, af_max: float = 0.2) -> pd.Series:
        """Parabolic SAR"""
        length = len(close)
        psar = np.zeros(length)
        af = af_start
        ep = 0
        trend = 0
        
        # Initialize
        psar[0] = close.iloc[0]
        
        for i in range(1, length):
            if trend == 0:  # First bar, determine initial trend
                if close.iloc[i] > close.iloc[i-1]:
                    trend = 1  # Uptrend
                    ep = high.iloc[i]
                    psar[i] = low.iloc[i-1]
                else:
                    trend = -1  # Downtrend
                    ep = low.iloc[i]
                    psar[i] = high.iloc[i-1]
            else:
                # Calculate PSAR
                psar[i] = psar[i-1] + af * (ep - psar[i-1])
                
                if trend == 1:  # Uptrend
                    # Check for trend reversal
                    if low.iloc[i] <= psar[i]:
                        trend = -1
                        psar[i] = ep
                        ep = low.iloc[i]
                        af = af_start
                    else:
                        # Update extreme point and acceleration factor
                        if high.iloc[i] > ep:
                            ep = high.iloc[i]
                            af = min(af + af_increment, af_max)
                        
                        # Ensure PSAR doesn't exceed previous lows
                        psar[i] = min(psar[i], low.iloc[i-1], low.iloc[i-2] if i > 1 else low.iloc[i-1])
                
                else:  # Downtrend
                    # Check for trend reversal
                    if high.iloc[i] >= psar[i]:
                        trend = 1
                        psar[i] = ep
                        ep = high.iloc[i]
                        af = af_start
                    else:
                        # Update extreme point and acceleration factor
                        if low.iloc[i] < ep:
                            ep = low.iloc[i]
                            af = min(af + af_increment, af_max)
                        
                        # Ensure PSAR doesn't exceed previous highs
                        psar[i] = max(psar[i], high.iloc[i-1], high.iloc[i-2] if i > 1 else high.iloc[i-1])
        
        return pd.Series(psar, index=close.index)
    
    def adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """Average Directional Index"""
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        dm_plus = np.where((high - high.shift(1)) > (low.shift(1) - low), 
                          np.maximum(high - high.shift(1), 0), 0)
        dm_minus = np.where((low.shift(1) - low) > (high - high.shift(1)), 
                           np.maximum(low.shift(1) - low, 0), 0)
        
        dm_plus = pd.Series(dm_plus, index=high.index)
        dm_minus = pd.Series(dm_minus, index=high.index)
        
        # Smoothed values
        tr_smooth = tr.rolling(window=period).mean()
        dm_plus_smooth = dm_plus.rolling(window=period).mean()
        dm_minus_smooth = dm_minus.rolling(window=period).mean()
        
        # Directional Indicators
        di_plus = 100 * self.safe_divide(dm_plus_smooth, tr_smooth)
        di_minus = 100 * self.safe_divide(dm_minus_smooth, tr_smooth)
        
        # ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(window=period).mean()
        
        return {
            'adx': adx,
            'di_plus': di_plus,
            'di_minus': di_minus
        }
    
    def ichimoku_cloud(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Ichimoku Cloud"""
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
        tenkan_sen = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
        
        # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
        kijun_sen = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
        
        # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, shifted 26 periods ahead
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, shifted 26 periods ahead
        senkou_span_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
        
        # Chikou Span (Lagging Span): Close price shifted 26 periods back
        chikou_span = close.shift(-26)
        
        return {
            'ichimoku_tenkan': tenkan_sen,
            'ichimoku_kijun': kijun_sen,
            'ichimoku_senkou_a': senkou_span_a,
            'ichimoku_senkou_b': senkou_span_b,
            'ichimoku_chikou': chikou_span
        }
