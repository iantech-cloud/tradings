"""
Volatility-based technical indicators
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from .base_indicator import BaseIndicator

class VolatilityIndicators(BaseIndicator):
    """Collection of volatility indicators"""
    
    def __init__(self):
        super().__init__("VolatilityIndicators")
        self.required_periods = 20
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all volatility indicators"""
        if not self.validate_data(data):
            return {}
        
        results = {}
        close = data['close']
        high = data['high']
        low = data['low']
        
        try:
            # Bollinger Bands
            bb_data = self.bollinger_bands(close, 20, 2)
            results.update({
                'bollinger_upper': bb_data['upper'],
                'bollinger_middle': bb_data['middle'],
                'bollinger_lower': bb_data['lower']
            })
            
            # Average True Range
            results['atr'] = self.atr(high, low, close)
            
            # Donchian Channels
            donchian_data = self.donchian_channels(high, low)
            results.update(donchian_data)
            
            # Keltner Channels
            keltner_data = self.keltner_channels(high, low, close)
            results.update(keltner_data)
            
            # Volatility Index
            results['volatility_index'] = self.volatility_index(close)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility indicators: {str(e)}")
            return {}
    
    def atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def donchian_channels(self, high: pd.Series, low: pd.Series, period: int = 20) -> Dict[str, pd.Series]:
        """Donchian Channels"""
        upper_channel = high.rolling(window=period).max()
        lower_channel = low.rolling(window=period).min()
        middle_channel = (upper_channel + lower_channel) / 2
        
        return {
            'donchian_upper': upper_channel,
            'donchian_middle': middle_channel,
            'donchian_lower': lower_channel
        }
    
    def keltner_channels(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                       period: int = 20, multiplier: float = 2.0) -> Dict[str, pd.Series]:
        """Keltner Channels"""
        middle_line = self.ema(close, period)
        atr_value = self.atr(high, low, close, period)
        
        upper_channel = middle_line + (multiplier * atr_value)
        lower_channel = middle_line - (multiplier * atr_value)
        
        return {
            'keltner_upper': upper_channel,
            'keltner_middle': middle_line,
            'keltner_lower': lower_channel
        }
    
    def volatility_index(self, close: pd.Series, period: int = 10) -> pd.Series:
        """Volatility Index (Standard Deviation)"""
        returns = close.pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(period)
        return volatility * 100  # Convert to percentage
