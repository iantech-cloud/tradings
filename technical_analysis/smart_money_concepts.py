"""
Smart Money Concepts (SMC) analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from .base_indicator import BaseIndicator

class SmartMoneyConcepts(BaseIndicator):
    """Smart Money Concepts analysis"""
    
    def __init__(self):
        super().__init__("SmartMoneyConcepts")
        self.required_periods = 50
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Smart Money Concepts analysis"""
        if not self.validate_data(data):
            return {}
        
        results = {}
        
        try:
            # Market Structure Analysis
            structure_data = self.analyze_market_structure(data)
            results.update(structure_data)
            
            # Order Blocks
            order_blocks = self.identify_order_blocks(data)
            results['order_blocks'] = order_blocks
            
            # Fair Value Gaps
            fvgs = self.identify_fair_value_gaps(data)
            results['fair_value_gaps'] = fvgs
            
            # Liquidity Zones
            liquidity_zones = self.identify_liquidity_zones(data)
            results['liquidity_zones'] = liquidity_zones
            
            # Imbalances
            imbalances = self.identify_imbalances(data)
            results['imbalances'] = imbalances
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error calculating SMC analysis: {str(e)}")
            return {}
    
    def analyze_market_structure(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market structure for BOS and CHoCH"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        # Find swing highs and lows
        swing_highs = self.find_swing_points(high, 'high')
        swing_lows = self.find_swing_points(low, 'low')
        
        # Determine market structure
        structure = self.determine_market_structure(swing_highs, swing_lows, close)
        
        # Detect Break of Structure (BOS) and Change of Character (CHoCH)
        bos_points = self.detect_bos(swing_highs, swing_lows, close)
        choch_points = self.detect_choch(swing_highs, swing_lows, close)
        
        return {
            'market_structure': structure,
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'bos_points': bos_points,
            'choch_points': choch_points
        }
    
    def find_swing_points(self, data: pd.Series, point_type: str, lookback: int = 5) -> List[Dict]:
        """Find swing highs or lows"""
        swing_points = []
        
        for i in range(lookback, len(data) - lookback):
            if point_type == 'high':
                # Check if current point is higher than surrounding points
                is_swing = all(data.iloc[i] > data.iloc[j] for j in range(i - lookback, i + lookback + 1) if j != i)
            else:  # low
                # Check if current point is lower than surrounding points
                is_swing = all(data.iloc[i] < data.iloc[j] for j in range(i - lookback, i + lookback + 1) if j != i)
            
            if is_swing:
                swing_points.append({
                    'index': i,
                    'timestamp': data.index[i],
                    'price': data.iloc[i],
                    'type': point_type
                })
        
        return swing_points
    
    def determine_market_structure(self, swing_highs: List[Dict], swing_lows: List[Dict], close: pd.Series) -> str:
        """Determine overall market structure"""
        if not swing_highs or not swing_lows:
            return 'ranging'
        
        # Get recent swing points
        recent_highs = swing_highs[-3:] if len(swing_highs) >= 3 else swing_highs
        recent_lows = swing_lows[-3:] if len(swing_lows) >= 3 else swing_lows
        
        # Check for higher highs and higher lows (bullish structure)
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            hh = recent_highs[-1]['price'] > recent_highs[-2]['price']
            hl = recent_lows[-1]['price'] > recent_lows[-2]['price']
            
            if hh and hl:
                return 'bullish'
        
        # Check for lower highs and lower lows (bearish structure)
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            lh = recent_highs[-1]['price'] < recent_highs[-2]['price']
            ll = recent_lows[-1]['price'] < recent_lows[-2]['price']
            
            if lh and ll:
                return 'bearish'
        
        return 'ranging'
    
    def detect_bos(self, swing_highs: List[Dict], swing_lows: List[Dict], close: pd.Series) -> List[Dict]:
        """Detect Break of Structure points"""
        bos_points = []
        
        # Bullish BOS: Price breaks above previous swing high
        for i, swing_high in enumerate(swing_highs[:-1]):
            next_high_index = swing_highs[i + 1]['index']
            high_price = swing_high['price']
            
            # Check if price broke above this swing high
            for j in range(swing_high['index'], min(next_high_index, len(close))):
                if close.iloc[j] > high_price:
                    bos_points.append({
                        'index': j,
                        'timestamp': close.index[j],
                        'price': close.iloc[j],
                        'type': 'bullish_bos',
                        'broken_level': high_price
                    })
                    break
        
        # Bearish BOS: Price breaks below previous swing low
        for i, swing_low in enumerate(swing_lows[:-1]):
            next_low_index = swing_lows[i + 1]['index']
            low_price = swing_low['price']
            
            # Check if price broke below this swing low
            for j in range(swing_low['index'], min(next_low_index, len(close))):
                if close.iloc[j] < low_price:
                    bos_points.append({
                        'index': j,
                        'timestamp': close.index[j],
                        'price': close.iloc[j],
                        'type': 'bearish_bos',
                        'broken_level': low_price
                    })
                    break
        
        return bos_points
    
    def detect_choch(self, swing_highs: List[Dict], swing_lows: List[Dict], close: pd.Series) -> List[Dict]:
        """Detect Change of Character points"""
        choch_points = []
        
        # CHoCH occurs when market structure changes from bullish to bearish or vice versa
        # This is a simplified implementation
        
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Check for bullish to bearish CHoCH
            recent_high = swing_highs[-1]
            previous_low = None
            
            for swing_low in reversed(swing_lows):
                if swing_low['index'] < recent_high['index']:
                    previous_low = swing_low
                    break
            
            if previous_low:
                # Check if price breaks below the previous low after making a higher high
                for i in range(recent_high['index'], len(close)):
                    if close.iloc[i] < previous_low['price']:
                        choch_points.append({
                            'index': i,
                            'timestamp': close.index[i],
                            'price': close.iloc[i],
                            'type': 'bearish_choch',
                            'broken_level': previous_low['price']
                        })
                        break
        
        return choch_points
    
    def identify_order_blocks(self, data: pd.DataFrame, min_size: float = 0.001) -> List[Dict]:
        """Identify institutional order blocks"""
        order_blocks = []
        high = data['high']
        low = data['low']
        close = data['close']
        open_price = data['open']
        
        # Look for strong moves followed by consolidation
        for i in range(10, len(data) - 5):
            # Check for strong bullish move
            if close.iloc[i] > open_price.iloc[i] and (close.iloc[i] - open_price.iloc[i]) / open_price.iloc[i] > min_size:
                # Look for the last bearish candle before the move
                for j in range(i - 1, max(0, i - 10), -1):
                    if close.iloc[j] < open_price.iloc[j]:
                        order_blocks.append({
                            'index': j,
                            'timestamp': data.index[j],
                            'high': high.iloc[j],
                            'low': low.iloc[j],
                            'type': 'bullish_ob',
                            'strength': (close.iloc[i] - open_price.iloc[i]) / open_price.iloc[i]
                        })
                        break
            
            # Check for strong bearish move
            elif close.iloc[i] < open_price.iloc[i] and (open_price.iloc[i] - close.iloc[i]) / open_price.iloc[i] > min_size:
                # Look for the last bullish candle before the move
                for j in range(i - 1, max(0, i - 10), -1):
                    if close.iloc[j] > open_price.iloc[j]:
                        order_blocks.append({
                            'index': j,
                            'timestamp': data.index[j],
                            'high': high.iloc[j],
                            'low': low.iloc[j],
                            'type': 'bearish_ob',
                            'strength': (open_price.iloc[i] - close.iloc[i]) / open_price.iloc[i]
                        })
                        break
        
        return order_blocks
    
    def identify_fair_value_gaps(self, data: pd.DataFrame) -> List[Dict]:
        """Identify Fair Value Gaps (FVGs)"""
        fvgs = []
        high = data['high']
        low = data['low']
        
        # Look for 3-candle patterns where middle candle creates a gap
        for i in range(1, len(data) - 1):
            # Bullish FVG: Gap between candle 1 high and candle 3 low
            if low.iloc[i + 1] > high.iloc[i - 1]:
                fvgs.append({
                    'index': i,
                    'timestamp': data.index[i],
                    'high': low.iloc[i + 1],
                    'low': high.iloc[i - 1],
                    'type': 'bullish_fvg',
                    'size': low.iloc[i + 1] - high.iloc[i - 1]
                })
            
            # Bearish FVG: Gap between candle 1 low and candle 3 high
            elif high.iloc[i + 1] < low.iloc[i - 1]:
                fvgs.append({
                    'index': i,
                    'timestamp': data.index[i],
                    'high': low.iloc[i - 1],
                    'low': high.iloc[i + 1],
                    'type': 'bearish_fvg',
                    'size': low.iloc[i - 1] - high.iloc[i + 1]
                })
        
        return fvgs
    
    def identify_liquidity_zones(self, data: pd.DataFrame, lookback: int = 20) -> List[Dict]:
        """Identify liquidity zones (areas of stop hunts)"""
        liquidity_zones = []
        high = data['high']
        low = data['low']
        
        # Find areas where price repeatedly tests the same level
        for i in range(lookback, len(data)):
            window_high = high.iloc[i - lookback:i]
            window_low = low.iloc[i - lookback:i]
            
            # Check for resistance levels (multiple touches of highs)
            max_high = window_high.max()
            high_touches = sum(1 for h in window_high if abs(h - max_high) / max_high < 0.001)
            
            if high_touches >= 3:
                liquidity_zones.append({
                    'index': i,
                    'timestamp': data.index[i],
                    'price': max_high,
                    'type': 'resistance',
                    'touches': high_touches
                })
            
            # Check for support levels (multiple touches of lows)
            min_low = window_low.min()
            low_touches = sum(1 for l in window_low if abs(l - min_low) / min_low < 0.001)
            
            if low_touches >= 3:
                liquidity_zones.append({
                    'index': i,
                    'timestamp': data.index[i],
                    'price': min_low,
                    'type': 'support',
                    'touches': low_touches
                })
        
        return liquidity_zones
    
    def identify_imbalances(self, data: pd.DataFrame) -> List[Dict]:
        """Identify price imbalances"""
        imbalances = []
        high = data['high']
        low = data['low']
        close = data['close']
        open_price = data['open']
        
        # Look for large candles that create imbalances
        for i in range(len(data)):
            candle_size = abs(close.iloc[i] - open_price.iloc[i])
            candle_range = high.iloc[i] - low.iloc[i]
            
            # Strong directional move with little wicks
            if candle_size / candle_range > 0.7 and candle_size / close.iloc[i] > 0.01:
                imbalance_type = 'bullish' if close.iloc[i] > open_price.iloc[i] else 'bearish'
                
                imbalances.append({
                    'index': i,
                    'timestamp': data.index[i],
                    'high': high.iloc[i],
                    'low': low.iloc[i],
                    'type': f'{imbalance_type}_imbalance',
                    'strength': candle_size / close.iloc[i]
                })
        
        return imbalances
