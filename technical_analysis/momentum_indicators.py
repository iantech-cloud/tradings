"""
Momentum-based technical indicators
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from .base_indicator import BaseIndicator

class MomentumIndicators(BaseIndicator):
    """Collection of momentum indicators"""
    
    def __init__(self):
        super().__init__("MomentumIndicators")
        self.required_periods = 20
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all momentum indicators"""
        if not self.validate_data(data):
            return {}
        
        results = {}
        close = data['close']
        high = data['high']
        low = data['low']
        
        try:
            # RSI
            results['rsi'] = self.rsi(close, 14)
            
            # Stochastic Oscillator
            stoch_data = self.stochastic_oscillator(high, low, close)
            results.update(stoch_data)
            
            # Commodity Channel Index
            results['cci'] = self.cci(high, low, close)
            
            # Momentum Indicator
            results['momentum'] = self.momentum_indicator(close)
            
            # Williams %R
            results['williams_r'] = self.williams_r(high, low, close)
            
            # Rate of Change
            results['roc'] = self.rate_of_change(close)
            
            # Money Flow Index
            if 'volume' in data.columns:
                results['mfi'] = self.money_flow_index(high, low, close, data['volume'])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error calculating momentum indicators: {str(e)}")
            return {}
    
    def stochastic_oscillator(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                            k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * self.safe_divide(close - lowest_low, highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'stochastic_k': k_percent,
            'stochastic_d': d_percent
        }
    
    def cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Commodity Channel Index"""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        
        # Mean Absolute Deviation
        mad = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - np.mean(x))), raw=True
        )
        
        cci = self.safe_divide(typical_price - sma_tp, 0.015 * mad)
        return cci
    
    def momentum_indicator(self, close: pd.Series, period: int = 10) -> pd.Series:
        """Momentum Indicator"""
        return close / close.shift(period) * 100
    
    def williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        williams_r = -100 * self.safe_divide(highest_high - close, highest_high - lowest_low)
        return williams_r
    
    def rate_of_change(self, close: pd.Series, period: int = 12) -> pd.Series:
        """Rate of Change"""
        return ((close - close.shift(period)) / close.shift(period)) * 100
    
    def money_flow_index(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                        volume: pd.Series, period: int = 14) -> pd.Series:
        """Money Flow Index"""
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        
        # Positive and negative money flow
        positive_flow = np.where(typical_price > typical_price.shift(1), money_flow, 0)
        negative_flow = np.where(typical_price < typical_price.shift(1), money_flow, 0)
        
        positive_flow = pd.Series(positive_flow, index=close.index)
        negative_flow = pd.Series(negative_flow, index=close.index)
        
        # Money Flow Ratio
        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()
        
        mfr = self.safe_divide(positive_mf, negative_mf, 1)
        mfi = 100 - (100 / (1 + mfr))
        
        return mfi
