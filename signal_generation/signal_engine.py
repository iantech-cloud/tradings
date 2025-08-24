"""
Main signal generation engine
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading

from app import db
from models import TradingSignals, MarketData
from technical_analysis.indicators_engine import IndicatorsEngine
from .signal_analyzer import SignalAnalyzer
from .signal_formatter import SignalFormatter
from config import Config

logger = logging.getLogger(__name__)

class SignalEngine:
    """Main signal generation engine"""
    
    def __init__(self, config: Config):
        self.config = config
        self.indicators_engine = IndicatorsEngine()
        self.signal_analyzer = SignalAnalyzer(config)
        self.signal_formatter = SignalFormatter()
        
        # Thread lock for database operations
        self.db_lock = threading.Lock()
        
        # Signal generation settings
        self.min_time_between_signals = 300  # 5 minutes minimum between signals for same symbol
    
    def generate_signal(self, symbol: str, force_analysis: bool = False) -> Optional[Dict[str, Any]]:
        """Generate trading signal for a symbol"""
        try:
            # Check if we should generate a new signal
            if not force_analysis and not self._should_generate_signal(symbol):
                logger.debug(f"Skipping signal generation for {symbol} - too recent")
                return None
            
            # Get latest indicators
            indicators = self.indicators_engine.get_latest_indicators(symbol)
            if not indicators:
                logger.warning(f"No indicators available for {symbol}")
                return None
            
            # Analyze signal
            signal_result = self.signal_analyzer.analyze_signal(symbol, indicators)
            
            # Only generate signals with sufficient confidence
            if signal_result.get('confidence', 0) < 60 and signal_result.get('signal') != 'HOLD':
                logger.info(f"Low confidence signal for {symbol}, converting to HOLD")
                signal_result['signal'] = 'HOLD'
                signal_result['reasoning'] = "Insufficient confluence for directional bias. " + signal_result.get('reasoning', '')
            
            # Format signal for storage and notification
            formatted_signal = self.signal_formatter.format_signal(signal_result)
            
            # Store signal in database
            stored_signal = self._store_signal(formatted_signal)
            
            if stored_signal:
                logger.info(f"Generated {signal_result['signal']} signal for {symbol} with {signal_result['confidence']:.1f}% confidence")
                return formatted_signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {str(e)}")
            return None
    
    def generate_signals_for_all_symbols(self) -> Dict[str, Any]:
        """Generate signals for all configured symbols"""
        results = {}
        
        for symbol in self.config.SUPPORTED_PAIRS:
            try:
                signal = self.generate_signal(symbol)
                results[symbol] = {
                    'success': signal is not None,
                    'signal': signal.get('signal') if signal else None,
                    'confidence': signal.get('confidence') if signal else None
                }
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {str(e)}")
                results[symbol] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def get_active_signals(self, symbol: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get active trading signals"""
        try:
            query = TradingSignals.query.filter(
                TradingSignals.status == 'active'
            )
            
            if symbol:
                query = query.filter(TradingSignals.symbol == symbol)
            
            signals = query.order_by(TradingSignals.timestamp.desc()).limit(limit).all()
            
            return [self._format_signal_for_api(signal) for signal in signals]
            
        except Exception as e:
            logger.error(f"Error getting active signals: {str(e)}")
            return []
    
    def update_signal_outcome(self, signal_id: int, outcome: str, pnl: float = 0.0) -> bool:
        """Update signal outcome when trade is closed"""
        try:
            with self.db_lock:
                signal = TradingSignals.query.get(signal_id)
                if not signal:
                    logger.error(f"Signal {signal_id} not found")
                    return False
                
                signal.status = f'hit_{outcome.lower()}' if outcome in ['TP', 'SL'] else 'closed_manual'
                signal.outcome = 'profit' if pnl > 0 else 'loss' if pnl < 0 else 'breakeven'
                signal.pnl = pnl
                
                db.session.commit()
                logger.info(f"Updated signal {signal_id} outcome: {outcome}, P&L: {pnl}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating signal outcome: {str(e)}")
            db.session.rollback()
            return False
    
    def _should_generate_signal(self, symbol: str) -> bool:
        """Check if enough time has passed since last signal"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.min_time_between_signals)
            
            recent_signal = TradingSignals.query.filter(
                TradingSignals.symbol == symbol,
                TradingSignals.timestamp >= cutoff_time
            ).first()
            
            return recent_signal is None
            
        except Exception as e:
            logger.error(f"Error checking signal timing: {str(e)}")
            return True  # Default to allowing signal generation
    
    def _store_signal(self, signal_data: Dict[str, Any]) -> Optional[TradingSignals]:
        """Store signal in database"""
        try:
            with self.db_lock:
                trading_signal = TradingSignals(
                    symbol=signal_data['symbol'],
                    signal_type=signal_data['signal'],
                    entry_price=signal_data['entry_price'],
                    stop_loss=signal_data.get('stop_loss'),
                    take_profit=signal_data.get('take_profit'),
                    risk_reward_ratio=signal_data.get('risk_reward'),
                    reasoning=signal_data['reasoning'],
                    confidence_score=signal_data['confidence'],
                    rsi_value=signal_data.get('rsi_value'),
                    macd_value=signal_data.get('macd_value'),
                    trend_direction=signal_data.get('trend_direction'),
                    smc_confluence=signal_data.get('smc_confluence'),
                    status='active'
                )
                
                db.session.add(trading_signal)
                db.session.commit()
                
                return trading_signal
                
        except Exception as e:
            logger.error(f"Error storing signal: {str(e)}")
            db.session.rollback()
            return None
    
    def _format_signal_for_api(self, signal: TradingSignals) -> Dict[str, Any]:
        """Format database signal for API response"""
        return {
            'id': signal.id,
            'symbol': signal.symbol,
            'timestamp': signal.timestamp.isoformat(),
            'signal': signal.signal_type,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'risk_reward_ratio': signal.risk_reward_ratio,
            'reasoning': signal.reasoning,
            'confidence': signal.confidence_score,
            'status': signal.status,
            'outcome': signal.outcome,
            'pnl': signal.pnl
        }
    
    def get_signal_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary of generated signals"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            signals = TradingSignals.query.filter(
                TradingSignals.timestamp >= cutoff_date
            ).all()
            
            if not signals:
                return {
                    'total_signals': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'average_confidence': 0
                }
            
            total_signals = len(signals)
            winning_signals = len([s for s in signals if s.outcome == 'profit'])
            total_pnl = sum(s.pnl or 0 for s in signals)
            average_confidence = sum(s.confidence_score or 0 for s in signals) / total_signals
            
            # Signal type breakdown
            buy_signals = len([s for s in signals if s.signal_type == 'BUY'])
            sell_signals = len([s for s in signals if s.signal_type == 'SELL'])
            hold_signals = len([s for s in signals if s.signal_type == 'HOLD'])
            
            return {
                'total_signals': total_signals,
                'win_rate': (winning_signals / total_signals * 100) if total_signals > 0 else 0,
                'total_pnl': round(total_pnl, 2),
                'average_confidence': round(average_confidence, 1),
                'signal_breakdown': {
                    'buy': buy_signals,
                    'sell': sell_signals,
                    'hold': hold_signals
                },
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting signal performance: {str(e)}")
            return {}
