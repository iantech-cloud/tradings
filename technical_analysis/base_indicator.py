"""
Base class for all technical indicators
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseIndicator(ABC):
    """Base class for all technical indicators"""
    
    def __init__(self, name: str):
        self.name = name
        self.required_periods = 1
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data"""
        if data is None or data.empty:
            logger.error(f"{self.name}: No data provided")
            return False
        
        if len(data) < self.required_periods:
            logger.error(f"{self.name}: Insufficient data. Need {self.required_periods}, got {len(data)}")
            return False
        
        required_columns = ['open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            logger.error(f"{self.name}: Missing required columns: {missing_columns}")
            return False
        
        return True
    
    def prepare_data(self, ohlcv_data: List[Dict]) -> pd.DataFrame:
        """Convert OHLCV data to pandas DataFrame"""
        try:
            df = pd.DataFrame(ohlcv_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            df = df.reset_index(drop=True)
            
            # Ensure numeric columns
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"{self.name}: Error preparing data: {str(e)}")
            return pd.DataFrame()
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate the indicator"""
        pass
    
    def safe_divide(self, numerator, denominator, default=0):
        """Safe division to avoid division by zero"""
        return np.where(denominator != 0, numerator / denominator, default)
    
    def sma(self, data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period, min_periods=1).mean()
    
    def ema(self, data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    def rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = self.safe_divide(gain, loss, 0)
        return 100 - (100 / (1 + rs))
    
    def bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = self.sma(data, period)
        std = data.rolling(window=period).std()
        
        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }
