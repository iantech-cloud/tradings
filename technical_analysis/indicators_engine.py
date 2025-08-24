"""
Main technical indicators engine that coordinates all analysis
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from app import db
from models import TechnicalIndicators, SmartMoneyAnalysis, MarketData
from .trend_indicators import TrendIndicators
from .momentum_indicators import MomentumIndicators
from .volatility_indicators import VolatilityIndicators
from .volume_indicators import VolumeIndicators
from .smart_money_concepts import SmartMoneyConcepts

logger = logging.getLogger(__name__)

class IndicatorsEngine:
    """Main engine for calculating all technical indicators"""
    
    def __init__(self):
        self.trend_indicators = TrendIndicators()
        self.momentum_indicators = MomentumIndicators()
        self.volatility_indicators = VolatilityIndicators()
        self.volume_indicators = VolumeIndicators()
        self.smc_analyzer = SmartMoneyConcepts()
    
    def calculate_all_indicators(self, symbol: str, limit: int = 200) -> Dict[str, Any]:
        """Calculate all indicators for a symbol"""
        try:
            # Get market data
            market_data = self._get_market_data(symbol, limit)
            if market_data.empty:
                logger.error(f"No market data available for {symbol}")
                return {}
            
            # Calculate indicators concurrently
            results = {}
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit calculation tasks
                futures = {
                    executor.submit(self.trend_indicators.calculate, market_data): 'trend',
                    executor.submit(self.momentum_indicators.calculate, market_data): 'momentum',
                    executor.submit(self.volatility_indicators.calculate, market_data): 'volatility',
                    executor.submit(self.volume_indicators.calculate, market_data): 'volume',
                    executor.submit(self.smc_analyzer.calculate, market_data): 'smc'
                }
                
                # Collect results
                for future in as_completed(futures):
                    indicator_type = futures[future]
                    try:
                        indicator_results = future.result()
                        results[indicator_type] = indicator_results
                        logger.debug(f"Calculated {indicator_type} indicators for {symbol}")
                    except Exception as e:
                        logger.error(f"Error calculating {indicator_type} indicators: {str(e)}")
                        results[indicator_type] = {}
            
            # Store results in database
            self._store_indicators(symbol, results, market_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {str(e)}")
            return {}
    
    def get_latest_indicators(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the latest calculated indicators from database"""
        try:
            # Get the most recent market data point
            latest_market_data = MarketData.query.filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.desc()).first()
            
            if not latest_market_data:
                return None
            
            # Get corresponding technical indicators
            latest_indicators = TechnicalIndicators.query.filter(
                TechnicalIndicators.market_data_id == latest_market_data.id
            ).first()
            
            # Get SMC analysis
            latest_smc = SmartMoneyAnalysis.query.filter(
                SmartMoneyAnalysis.market_data_id == latest_market_data.id
            ).first()
            
            if not latest_indicators:
                return None
            
            # Format results
            results = {
                'timestamp': latest_indicators.timestamp,
                'market_data': {
                    'open': latest_market_data.open_price,
                    'high': latest_market_data.high_price,
                    'low': latest_market_data.low_price,
                    'close': latest_market_data.close_price,
                    'volume': latest_market_data.volume
                },
                'trend': {
                    'sma_20': latest_indicators.sma_20,
                    'sma_50': latest_indicators.sma_50,
                    'ema_12': latest_indicators.ema_12,
                    'ema_26': latest_indicators.ema_26,
                    'macd': latest_indicators.macd,
                    'macd_signal': latest_indicators.macd_signal,
                    'macd_histogram': latest_indicators.macd_histogram
                },
                'momentum': {
                    'rsi': latest_indicators.rsi,
                    'stochastic_k': latest_indicators.stochastic_k,
                    'stochastic_d': latest_indicators.stochastic_d,
                    'cci': latest_indicators.cci,
                    'williams_r': latest_indicators.williams_r
                },
                'volatility': {
                    'bollinger_upper': latest_indicators.bollinger_upper,
                    'bollinger_middle': latest_indicators.bollinger_middle,
                    'bollinger_lower': latest_indicators.bollinger_lower,
                    'atr': latest_indicators.atr
                },
                'volume': {
                    'obv': latest_indicators.obv,
                    'ad_line': latest_indicators.ad_line
                }
            }
            
            # Add SMC data if available
            if latest_smc:
                results['smc'] = {
                    'market_structure': latest_smc.market_structure,
                    'bos_detected': latest_smc.bos_detected,
                    'choch_detected': latest_smc.choch_detected,
                    'liquidity_sweep': latest_smc.liquidity_sweep,
                    'order_block_type': latest_smc.order_block_type,
                    'order_block_price': latest_smc.order_block_price,
                    'fvg_detected': latest_smc.fvg_detected,
                    'fvg_high': latest_smc.fvg_high,
                    'fvg_low': latest_smc.fvg_low
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting latest indicators for {symbol}: {str(e)}")
            return None
    
    def _get_market_data(self, symbol: str, limit: int) -> pd.DataFrame:
        """Get market data from database"""
        try:
            market_data = MarketData.query.filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.desc()).limit(limit).all()
            
            if not market_data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for md in reversed(market_data):  # Reverse to get chronological order
                data.append({
                    'timestamp': md.timestamp,
                    'open': md.open_price,
                    'high': md.high_price,
                    'low': md.low_price,
                    'close': md.close_price,
                    'volume': md.volume
                })
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _store_indicators(self, symbol: str, results: Dict[str, Any], market_data: pd.DataFrame):
        """Store calculated indicators in database"""
        try:
            # Get the latest market data record
            latest_market_data = MarketData.query.filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.desc()).first()
            
            if not latest_market_data:
                return
            
            # Extract latest indicator values
            trend_data = results.get('trend', {})
            momentum_data = results.get('momentum', {})
            volatility_data = results.get('volatility', {})
            volume_data = results.get('volume', {})
            smc_data = results.get('smc', {})
            
            # Store technical indicators
            indicators = TechnicalIndicators(
                market_data_id=latest_market_data.id,
                sma_20=self._get_latest_value(trend_data.get('sma_20')),
                sma_50=self._get_latest_value(trend_data.get('sma_50')),
                ema_12=self._get_latest_value(trend_data.get('ema_12')),
                ema_26=self._get_latest_value(trend_data.get('ema_26')),
                macd=self._get_latest_value(trend_data.get('macd')),
                macd_signal=self._get_latest_value(trend_data.get('macd_signal')),
                macd_histogram=self._get_latest_value(trend_data.get('macd_histogram')),
                rsi=self._get_latest_value(momentum_data.get('rsi')),
                stochastic_k=self._get_latest_value(momentum_data.get('stochastic_k')),
                stochastic_d=self._get_latest_value(momentum_data.get('stochastic_d')),
                cci=self._get_latest_value(momentum_data.get('cci')),
                williams_r=self._get_latest_value(momentum_data.get('williams_r')),
                bollinger_upper=self._get_latest_value(volatility_data.get('bollinger_upper')),
                bollinger_middle=self._get_latest_value(volatility_data.get('bollinger_middle')),
                bollinger_lower=self._get_latest_value(volatility_data.get('bollinger_lower')),
                atr=self._get_latest_value(volatility_data.get('atr')),
                obv=self._get_latest_value(volume_data.get('obv')),
                ad_line=self._get_latest_value(volume_data.get('ad_line'))
            )
            
            db.session.add(indicators)
            
            # Store SMC analysis
            if smc_data:
                smc_analysis = SmartMoneyAnalysis(
                    market_data_id=latest_market_data.id,
                    market_structure=smc_data.get('market_structure'),
                    bos_detected=len(smc_data.get('bos_points', [])) > 0,
                    choch_detected=len(smc_data.get('choch_points', [])) > 0,
                    liquidity_sweep=len(smc_data.get('liquidity_zones', [])) > 0,
                    order_block_type=self._get_latest_order_block_type(smc_data.get('order_blocks', [])),
                    order_block_price=self._get_latest_order_block_price(smc_data.get('order_blocks', [])),
                    fvg_detected=len(smc_data.get('fair_value_gaps', [])) > 0,
                    fvg_high=self._get_latest_fvg_high(smc_data.get('fair_value_gaps', [])),
                    fvg_low=self._get_latest_fvg_low(smc_data.get('fair_value_gaps', []))
                )
                
                db.session.add(smc_analysis)
            
            db.session.commit()
            logger.info(f"Stored indicators for {symbol}")
            
        except Exception as e:
            logger.error(f"Error storing indicators: {str(e)}")
            db.session.rollback()
    
    def _get_latest_value(self, series) -> Optional[float]:
        """Get the latest value from a pandas Series"""
        if series is None or len(series) == 0:
            return None
        
        if hasattr(series, 'iloc'):
            latest_val = series.iloc[-1]
            return float(latest_val) if not pd.isna(latest_val) else None
        
        return None
    
    def _get_latest_order_block_type(self, order_blocks: List[Dict]) -> Optional[str]:
        """Get the type of the most recent order block"""
        if not order_blocks:
            return None
        
        latest_ob = max(order_blocks, key=lambda x: x['index'])
        return latest_ob.get('type')
    
    def _get_latest_order_block_price(self, order_blocks: List[Dict]) -> Optional[float]:
        """Get the price of the most recent order block"""
        if not order_blocks:
            return None
        
        latest_ob = max(order_blocks, key=lambda x: x['index'])
        return (latest_ob.get('high', 0) + latest_ob.get('low', 0)) / 2
    
    def _get_latest_fvg_high(self, fvgs: List[Dict]) -> Optional[float]:
        """Get the high of the most recent FVG"""
        if not fvgs:
            return None
        
        latest_fvg = max(fvgs, key=lambda x: x['index'])
        return latest_fvg.get('high')
    
    def _get_latest_fvg_low(self, fvgs: List[Dict]) -> Optional[float]:
        """Get the low of the most recent FVG"""
        if not fvgs:
            return None
        
        latest_fvg = max(fvgs, key=lambda x: x['index'])
        return latest_fvg.get('low')
