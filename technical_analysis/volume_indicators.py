"""
Volume-based technical indicators
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from .base_indicator import BaseIndicator

class VolumeIndicators(BaseIndicator):
    """Collection of volume indicators"""
    
    def __init__(self):
        super().__init__("VolumeIndicators")
        self.required_periods = 20
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all volume indicators"""
        if not self.validate_data(data):
            return {}
        
        # Skip volume indicators if no volume data
        if 'volume' not in data.columns or data['volume'].sum() == 0:
            return {}
        
        results = {}
        close = data['close']
        high = data['high']
        low = data['low']
        volume = data['volume']
        
        try:
            # On-Balance Volume
            results['obv'] = self.obv(close, volume)
            
            # Accumulation/Distribution Line
            results['ad_line'] = self.accumulation_distribution_line(high, low, close, volume)
            
            # Chaikin Money Flow
            results['cmf'] = self.chaikin_money_flow(high, low, close, volume)
            
            # Volume Oscillator
            results['volume_oscillator'] = self.volume_oscillator(volume)
            
            # Volume Weighted Average Price
            results['vwap'] = self.vwap(high, low, close, volume)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error calculating volume indicators: {str(e)}")
            return {}
    
    def obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        price_change = close.diff()
        obv_values = []
        obv_current = 0
        
        for i, (price_diff, vol) in enumerate(zip(price_change, volume)):
            if i == 0:  # First value
                obv_values.append(vol)
                obv_current = vol
            elif price_diff > 0:
                obv_current += vol
                obv_values.append(obv_current)
            elif price_diff < 0:
                obv_current -= vol
                obv_values.append(obv_current)
            else:
                obv_values.append(obv_current)
        
        return pd.Series(obv_values, index=close.index)
    
    def accumulation_distribution_line(self, high: pd.Series, low: pd.Series, 
                                     close: pd.Series, volume: pd.Series) -> pd.Series:
        """Accumulation/Distribution Line"""
        money_flow_multiplier = self.safe_divide(
            (close - low) - (high - close), 
            high - low, 
            0
        )
        money_flow_volume = money_flow_multiplier * volume
        ad_line = money_flow_volume.cumsum()
        
        return ad_line
    
    def chaikin_money_flow(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                          volume: pd.Series, period: int = 20) -> pd.Series:
        """Chaikin Money Flow"""
        money_flow_multiplier = self.safe_divide(
            (close - low) - (high - close), 
            high - low, 
            0
        )
        money_flow_volume = money_flow_multiplier * volume
        
        cmf = self.safe_divide(
            money_flow_volume.rolling(window=period).sum(),
            volume.rolling(window=period).sum()
        )
        
        return cmf
    
    def volume_oscillator(self, volume: pd.Series, short_period: int = 5, long_period: int = 10) -> pd.Series:
        """Volume Oscillator"""
        short_ma = volume.rolling(window=short_period).mean()
        long_ma = volume.rolling(window=long_period).mean()
        
        volume_osc = self.safe_divide(short_ma - long_ma, long_ma) * 100
        return volume_osc
    
    def vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        vwap_values = []
        cumulative_volume = 0
        cumulative_pv = 0
        
        for tp, vol in zip(typical_price, volume):
            cumulative_pv += tp * vol
            cumulative_volume += vol
            
            if cumulative_volume > 0:
                vwap_values.append(cumulative_pv / cumulative_volume)
            else:
                vwap_values.append(tp)
        
        return pd.Series(vwap_values, index=close.index)
