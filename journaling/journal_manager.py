"""
Main journal manager for auto-logging trading activities
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading

from app import db
from models import TradingSignals, MarketData, SystemPerformance, TechnicalIndicators, SmartMoneyAnalysis
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class JournalManager:
    """Manages automatic journaling of all trading activities"""
    
    def __init__(self):
        self.performance_tracker = PerformanceTracker()
        self.db_lock = threading.Lock()
    
    def log_signal_generation(self, signal_data: Dict[str, Any], 
                            market_snapshot: Dict[str, Any],
                            indicators_snapshot: Dict[str, Any]) -> bool:
        """Log signal generation with complete market context"""
        try:
            with self.db_lock:
                # The signal itself is already stored by SignalEngine
                # Here we log additional context and market snapshot
                
                signal_id = signal_data.get('id')
                if not signal_id:
                    logger.error("No signal ID provided for journaling")
                    return False
                
                # Log market snapshot at signal generation time
                self._log_market_snapshot(signal_data['symbol'], market_snapshot)
                
                # Log technical indicators snapshot
                self._log_indicators_snapshot(signal_data['symbol'], indicators_snapshot)
                
                # Log SMC analysis if available
                if 'smc_analysis' in indicators_snapshot:
                    self._log_smc_snapshot(signal_data['symbol'], indicators_snapshot['smc_analysis'])
                
                logger.info(f"Logged signal generation for {signal_data['symbol']}: {signal_data['signal']}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging signal generation: {str(e)}")
            return False
    
    def log_signal_outcome(self, signal_id: int, outcome_data: Dict[str, Any]) -> bool:
        """Log signal outcome when trade is closed"""
        try:
            with self.db_lock:
                signal = TradingSignals.query.get(signal_id)
                if not signal:
                    logger.error(f"Signal {signal_id} not found for outcome logging")
                    return False
                
                # Update signal with outcome
                signal.status = outcome_data.get('status', 'closed_manual')
                signal.outcome = outcome_data.get('outcome', 'unknown')
                signal.pnl = outcome_data.get('pnl', 0.0)
                
                # Add outcome timestamp and additional details
                outcome_details = {
                    'close_timestamp': datetime.utcnow(),
                    'close_price': outcome_data.get('close_price'),
                    'close_reason': outcome_data.get('close_reason', 'manual'),
                    'duration_hours': self._calculate_signal_duration(signal),
                    'market_conditions_at_close': outcome_data.get('market_conditions')
                }
                
                # Store outcome details in reasoning field (append)
                if signal.reasoning:
                    signal.reasoning += f"\n\nOUTCOME: {outcome_details}"
                
                db.session.commit()
                
                # Update performance metrics
                self.performance_tracker.update_performance_metrics(signal)
                
                logger.info(f"Logged outcome for signal {signal_id}: {outcome_data.get('outcome')} (P&L: {outcome_data.get('pnl', 0)})")
                return True
                
        except Exception as e:
            logger.error(f"Error logging signal outcome: {str(e)}")
            db.session.rollback()
            return False
    
    def log_market_event(self, symbol: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Log significant market events"""
        try:
            with self.db_lock:
                # Create a special market event record
                event_record = MarketData(
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    open_price=event_data.get('price', 0),
                    high_price=event_data.get('price', 0),
                    low_price=event_data.get('price', 0),
                    close_price=event_data.get('price', 0),
                    volume=0,
                    source=f'market_event_{event_type}'
                )
                
                db.session.add(event_record)
                db.session.commit()
                
                logger.info(f"Logged market event for {symbol}: {event_type}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging market event: {str(e)}")
            db.session.rollback()
            return False
    
    def get_trading_journal(self, symbol: str = None, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive trading journal"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = TradingSignals.query.filter(
                TradingSignals.timestamp >= cutoff_date
            )
            
            if symbol:
                query = query.filter(TradingSignals.symbol == symbol)
            
            signals = query.order_by(TradingSignals.timestamp.desc()).all()
            
            # Format journal entries
            journal_entries = []
            for signal in signals:
                entry = {
                    'id': signal.id,
                    'timestamp': signal.timestamp.isoformat(),
                    'symbol': signal.symbol,
                    'signal_type': signal.signal_type,
                    'entry_price': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'risk_reward_ratio': signal.risk_reward_ratio,
                    'reasoning': signal.reasoning,
                    'confidence_score': signal.confidence_score,
                    'status': signal.status,
                    'outcome': signal.outcome,
                    'pnl': signal.pnl,
                    'duration': self._calculate_signal_duration(signal),
                    'market_context': {
                        'rsi': signal.rsi_value,
                        'macd': signal.macd_value,
                        'trend': signal.trend_direction,
                        'smc': signal.smc_confluence
                    }
                }
                journal_entries.append(entry)
            
            # Calculate summary statistics
            summary = self._calculate_journal_summary(signals)
            
            return {
                'period_days': days,
                'symbol': symbol or 'ALL',
                'total_entries': len(journal_entries),
                'summary': summary,
                'entries': journal_entries
            }
            
        except Exception as e:
            logger.error(f"Error getting trading journal: {str(e)}")
            return {}
    
    def get_performance_analytics(self, symbol: str = None, days: int = 30) -> Dict[str, Any]:
        """Get detailed performance analytics"""
        try:
            cutoff_date = datetime.utcnow().date() - timedelta(days=days)
            
            # Build query
            query = SystemPerformance.query.filter(
                SystemPerformance.date >= cutoff_date
            )
            
            if symbol:
                query = query.filter(SystemPerformance.symbol == symbol)
            
            performance_data = query.order_by(SystemPerformance.date.desc()).all()
            
            if not performance_data:
                return {}
            
            # Calculate aggregate metrics
            total_signals = sum(p.total_signals for p in performance_data)
            total_wins = sum(p.winning_signals for p in performance_data)
            total_losses = sum(p.losing_signals for p in performance_data)
            total_pnl = sum(p.total_pnl for p in performance_data)
            
            # Calculate advanced metrics
            win_rate = (total_wins / total_signals * 100) if total_signals > 0 else 0
            avg_win = sum(p.average_win for p in performance_data if p.average_win) / len([p for p in performance_data if p.average_win]) if any(p.average_win for p in performance_data) else 0
            avg_loss = sum(p.average_loss for p in performance_data if p.average_loss) / len([p for p in performance_data if p.average_loss]) if any(p.average_loss for p in performance_data) else 0
            
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            max_drawdown = max(p.max_drawdown for p in performance_data) if performance_data else 0
            avg_sharpe = sum(p.sharpe_ratio for p in performance_data) / len(performance_data) if performance_data else 0
            
            # Daily performance chart data
            daily_performance = []
            for p in reversed(performance_data):  # Chronological order
                daily_performance.append({
                    'date': p.date.isoformat(),
                    'pnl': p.total_pnl,
                    'signals': p.total_signals,
                    'win_rate': p.win_rate
                })
            
            return {
                'period_days': days,
                'symbol': symbol or 'ALL',
                'summary': {
                    'total_signals': total_signals,
                    'winning_signals': total_wins,
                    'losing_signals': total_losses,
                    'win_rate': round(win_rate, 2),
                    'total_pnl': round(total_pnl, 2),
                    'average_win': round(avg_win, 2),
                    'average_loss': round(avg_loss, 2),
                    'profit_factor': round(profit_factor, 2),
                    'max_drawdown': round(max_drawdown, 2),
                    'sharpe_ratio': round(avg_sharpe, 2)
                },
                'daily_performance': daily_performance,
                'performance_by_symbol': self._get_performance_by_symbol(performance_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance analytics: {str(e)}")
            return {}
    
    def _log_market_snapshot(self, symbol: str, market_snapshot: Dict[str, Any]):
        """Log market data snapshot"""
        try:
            # Market snapshot is already logged by DataManager
            # This could be extended for additional market context
            pass
        except Exception as e:
            logger.error(f"Error logging market snapshot: {str(e)}")
    
    def _log_indicators_snapshot(self, symbol: str, indicators_snapshot: Dict[str, Any]):
        """Log technical indicators snapshot"""
        try:
            # Indicators are already logged by IndicatorsEngine
            # This could be extended for additional indicator context
            pass
        except Exception as e:
            logger.error(f"Error logging indicators snapshot: {str(e)}")
    
    def _log_smc_snapshot(self, symbol: str, smc_analysis: Dict[str, Any]):
        """Log Smart Money Concepts analysis snapshot"""
        try:
            # SMC analysis is already logged by IndicatorsEngine
            # This could be extended for additional SMC context
            pass
        except Exception as e:
            logger.error(f"Error logging SMC snapshot: {str(e)}")
    
    def _calculate_signal_duration(self, signal: TradingSignals) -> Optional[float]:
        """Calculate signal duration in hours"""
        try:
            if signal.status == 'active':
                return (datetime.utcnow() - signal.timestamp).total_seconds() / 3600
            
            # For closed signals, we'd need close timestamp
            # This is simplified - in production, you'd store close timestamp
            return None
            
        except Exception as e:
            logger.error(f"Error calculating signal duration: {str(e)}")
            return None
    
    def _calculate_journal_summary(self, signals: List[TradingSignals]) -> Dict[str, Any]:
        """Calculate summary statistics for journal"""
        if not signals:
            return {}
        
        total_signals = len(signals)
        buy_signals = len([s for s in signals if s.signal_type == 'BUY'])
        sell_signals = len([s for s in signals if s.signal_type == 'SELL'])
        hold_signals = len([s for s in signals if s.signal_type == 'HOLD'])
        
        closed_signals = [s for s in signals if s.outcome is not None]
        winning_signals = len([s for s in closed_signals if s.outcome == 'profit'])
        losing_signals = len([s for s in closed_signals if s.outcome == 'loss'])
        
        total_pnl = sum(s.pnl or 0 for s in signals)
        avg_confidence = sum(s.confidence_score or 0 for s in signals) / total_signals
        
        win_rate = (winning_signals / len(closed_signals) * 100) if closed_signals else 0
        
        return {
            'total_signals': total_signals,
            'signal_breakdown': {
                'buy': buy_signals,
                'sell': sell_signals,
                'hold': hold_signals
            },
            'closed_signals': len(closed_signals),
            'winning_signals': winning_signals,
            'losing_signals': losing_signals,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'average_confidence': round(avg_confidence, 1)
        }
    
    def _get_performance_by_symbol(self, performance_data: List[SystemPerformance]) -> Dict[str, Any]:
        """Get performance breakdown by symbol"""
        symbol_performance = {}
        
        for p in performance_data:
            if p.symbol not in symbol_performance:
                symbol_performance[p.symbol] = {
                    'total_signals': 0,
                    'total_pnl': 0,
                    'win_rate': 0,
                    'days_tracked': 0
                }
            
            symbol_performance[p.symbol]['total_signals'] += p.total_signals
            symbol_performance[p.symbol]['total_pnl'] += p.total_pnl
            symbol_performance[p.symbol]['days_tracked'] += 1
        
        # Calculate averages
        for symbol in symbol_performance:
            days = symbol_performance[symbol]['days_tracked']
            if days > 0:
                symbol_performance[symbol]['avg_signals_per_day'] = round(
                    symbol_performance[symbol]['total_signals'] / days, 1
                )
                symbol_performance[symbol]['avg_pnl_per_day'] = round(
                    symbol_performance[symbol]['total_pnl'] / days, 2
                )
        
        return symbol_performance
