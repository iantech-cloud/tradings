"""
Performance tracking and metrics calculation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import numpy as np

from app import db
from models import TradingSignals, SystemPerformance

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Tracks and calculates performance metrics"""
    
    def __init__(self):
        self.db_lock = threading.Lock()
    
    def update_performance_metrics(self, signal: 'TradingSignals') -> bool:
        """Update performance metrics when a signal is closed"""
        try:
            with self.db_lock:
                # Get or create performance record for today
                today = datetime.utcnow().date()
                performance = SystemPerformance.query.filter(
                    SystemPerformance.date == today,
                    SystemPerformance.symbol == signal.symbol
                ).first()
                
                if not performance:
                    performance = SystemPerformance(
                        date=today,
                        symbol=signal.symbol,
                        total_signals=0,
                        winning_signals=0,
                        losing_signals=0,
                        win_rate=0.0,
                        total_pnl=0.0,
                        average_win=0.0,
                        average_loss=0.0,
                        profit_factor=0.0,
                        max_drawdown=0.0,
                        sharpe_ratio=0.0
                    )
                    db.session.add(performance)
                
                # Update metrics based on signal outcome
                if signal.outcome == 'profit':
                    performance.winning_signals += 1
                    performance.total_pnl += signal.pnl or 0
                elif signal.outcome == 'loss':
                    performance.losing_signals += 1
                    performance.total_pnl += signal.pnl or 0  # pnl should be negative for losses
                
                performance.total_signals += 1
                
                # Recalculate derived metrics
                self._recalculate_daily_metrics(performance, signal.symbol, today)
                
                db.session.commit()
                
                # Update longer-term metrics
                self._update_monthly_metrics(signal.symbol)
                
                logger.debug(f"Updated performance metrics for {signal.symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
            db.session.rollback()
            return False
    
    def calculate_system_metrics(self, symbol: str = None, days: int = 30) -> Dict[str, Any]:
        """Calculate comprehensive system performance metrics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get signals for analysis
            query = TradingSignals.query.filter(
                TradingSignals.timestamp >= cutoff_date,
                TradingSignals.outcome.isnot(None)  # Only closed signals
            )
            
            if symbol:
                query = query.filter(TradingSignals.symbol == symbol)
            
            signals = query.all()
            
            if not signals:
                return {}
            
            # Basic metrics
            total_signals = len(signals)
            winning_signals = len([s for s in signals if s.outcome == 'profit'])
            losing_signals = len([s for s in signals if s.outcome == 'loss'])
            
            win_rate = (winning_signals / total_signals * 100) if total_signals > 0 else 0
            
            # P&L metrics
            pnl_values = [s.pnl or 0 for s in signals]
            total_pnl = sum(pnl_values)
            
            winning_trades = [s.pnl for s in signals if s.outcome == 'profit' and s.pnl]
            losing_trades = [s.pnl for s in signals if s.outcome == 'loss' and s.pnl]
            
            avg_win = np.mean(winning_trades) if winning_trades else 0
            avg_loss = np.mean(losing_trades) if losing_trades else 0
            
            # Risk metrics
            profit_factor = abs(sum(winning_trades) / sum(losing_trades)) if losing_trades else float('inf')
            
            # Drawdown calculation
            cumulative_pnl = np.cumsum(pnl_values)
            running_max = np.maximum.accumulate(cumulative_pnl)
            drawdown = running_max - cumulative_pnl
            max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
            
            # Sharpe ratio (simplified)
            returns = np.array(pnl_values)
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
            
            # Confidence analysis
            confidence_scores = [s.confidence_score for s in signals if s.confidence_score]
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            
            # Signal type analysis
            signal_type_performance = self._analyze_signal_type_performance(signals)
            
            # Time-based analysis
            hourly_performance = self._analyze_hourly_performance(signals)
            
            return {
                'period_days': days,
                'symbol': symbol or 'ALL',
                'basic_metrics': {
                    'total_signals': total_signals,
                    'winning_signals': winning_signals,
                    'losing_signals': losing_signals,
                    'win_rate': round(win_rate, 2),
                    'average_confidence': round(avg_confidence, 1)
                },
                'pnl_metrics': {
                    'total_pnl': round(total_pnl, 2),
                    'average_win': round(avg_win, 2),
                    'average_loss': round(avg_loss, 2),
                    'profit_factor': round(profit_factor, 2),
                    'best_trade': round(max(pnl_values), 2) if pnl_values else 0,
                    'worst_trade': round(min(pnl_values), 2) if pnl_values else 0
                },
                'risk_metrics': {
                    'max_drawdown': round(max_drawdown, 2),
                    'sharpe_ratio': round(sharpe_ratio, 2),
                    'volatility': round(np.std(pnl_values), 2) if pnl_values else 0
                },
                'signal_type_performance': signal_type_performance,
                'hourly_performance': hourly_performance,
                'equity_curve': cumulative_pnl.tolist() if len(cumulative_pnl) > 0 else []
            }
            
        except Exception as e:
            logger.error(f"Error calculating system metrics: {str(e)}")
            return {}
    
    def get_trade_analysis(self, signal_id: int) -> Dict[str, Any]:
        """Get detailed analysis of a specific trade"""
        try:
            signal = TradingSignals.query.get(signal_id)
            if not signal:
                return {}
            
            analysis = {
                'signal_details': {
                    'id': signal.id,
                    'symbol': signal.symbol,
                    'timestamp': signal.timestamp.isoformat(),
                    'signal_type': signal.signal_type,
                    'entry_price': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'risk_reward_ratio': signal.risk_reward_ratio
                },
                'outcome': {
                    'status': signal.status,
                    'outcome': signal.outcome,
                    'pnl': signal.pnl,
                    'duration_hours': self._calculate_trade_duration(signal)
                },
                'market_context': {
                    'rsi': signal.rsi_value,
                    'macd': signal.macd_value,
                    'trend_direction': signal.trend_direction,
                    'confidence_score': signal.confidence_score
                },
                'reasoning': signal.reasoning,
                'smc_analysis': signal.smc_confluence
            }
            
            # Add performance comparison
            analysis['performance_comparison'] = self._compare_to_average_performance(signal)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting trade analysis: {str(e)}")
            return {}
    
    def _recalculate_daily_metrics(self, performance: SystemPerformance, symbol: str, date):
        """Recalculate daily performance metrics"""
        try:
            # Get all signals for this symbol and date
            signals = TradingSignals.query.filter(
                TradingSignals.symbol == symbol,
                TradingSignals.timestamp >= date,
                TradingSignals.timestamp < date + timedelta(days=1),
                TradingSignals.outcome.isnot(None)
            ).all()
            
            if not signals:
                return
            
            # Recalculate metrics
            total_signals = len(signals)
            winning_signals = len([s for s in signals if s.outcome == 'profit'])
            losing_signals = len([s for s in signals if s.outcome == 'loss'])
            
            performance.total_signals = total_signals
            performance.winning_signals = winning_signals
            performance.losing_signals = losing_signals
            performance.win_rate = (winning_signals / total_signals * 100) if total_signals > 0 else 0
            
            # P&L calculations
            total_pnl = sum(s.pnl or 0 for s in signals)
            winning_trades = [s.pnl for s in signals if s.outcome == 'profit' and s.pnl]
            losing_trades = [s.pnl for s in signals if s.outcome == 'loss' and s.pnl]
            
            performance.total_pnl = total_pnl
            performance.average_win = np.mean(winning_trades) if winning_trades else 0
            performance.average_loss = np.mean(losing_trades) if losing_trades else 0
            
            # Profit factor
            if losing_trades and sum(losing_trades) != 0:
                performance.profit_factor = abs(sum(winning_trades) / sum(losing_trades))
            else:
                performance.profit_factor = float('inf') if winning_trades else 0
            
            # Simplified Sharpe ratio for daily data
            pnl_values = [s.pnl or 0 for s in signals]
            if len(pnl_values) > 1:
                performance.sharpe_ratio = np.mean(pnl_values) / np.std(pnl_values) if np.std(pnl_values) > 0 else 0
            
        except Exception as e:
            logger.error(f"Error recalculating daily metrics: {str(e)}")
    
    def _update_monthly_metrics(self, symbol: str):
        """Update monthly performance metrics"""
        try:
            # This could be expanded to calculate monthly summaries
            # For now, we'll just log that monthly update was triggered
            logger.debug(f"Monthly metrics update triggered for {symbol}")
            
        except Exception as e:
            logger.error(f"Error updating monthly metrics: {str(e)}")
    
    def _analyze_signal_type_performance(self, signals: List['TradingSignals']) -> Dict[str, Any]:
        """Analyze performance by signal type"""
        signal_types = ['BUY', 'SELL', 'HOLD']
        performance = {}
        
        for signal_type in signal_types:
            type_signals = [s for s in signals if s.signal_type == signal_type]
            
            if not type_signals:
                performance[signal_type] = {
                    'count': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'avg_pnl': 0
                }
                continue
            
            winning = len([s for s in type_signals if s.outcome == 'profit'])
            total_pnl = sum(s.pnl or 0 for s in type_signals)
            
            performance[signal_type] = {
                'count': len(type_signals),
                'win_rate': round((winning / len(type_signals) * 100), 2),
                'total_pnl': round(total_pnl, 2),
                'avg_pnl': round(total_pnl / len(type_signals), 2)
            }
        
        return performance
    
    def _analyze_hourly_performance(self, signals: List['TradingSignals']) -> Dict[str, Any]:
        """Analyze performance by hour of day"""
        hourly_performance = {}
        
        for hour in range(24):
            hour_signals = [s for s in signals if s.timestamp.hour == hour]
            
            if not hour_signals:
                hourly_performance[str(hour)] = {
                    'count': 0,
                    'win_rate': 0,
                    'avg_pnl': 0
                }
                continue
            
            winning = len([s for s in hour_signals if s.outcome == 'profit'])
            total_pnl = sum(s.pnl or 0 for s in hour_signals)
            
            hourly_performance[str(hour)] = {
                'count': len(hour_signals),
                'win_rate': round((winning / len(hour_signals) * 100), 2),
                'avg_pnl': round(total_pnl / len(hour_signals), 2)
            }
        
        return hourly_performance
    
    def _calculate_trade_duration(self, signal: 'TradingSignals') -> Optional[float]:
        """Calculate trade duration in hours"""
        try:
            if signal.status == 'active':
                return (datetime.utcnow() - signal.timestamp).total_seconds() / 3600
            
            # For closed signals, we'd need close timestamp
            # This is simplified - in production, you'd store close timestamp
            return None
            
        except Exception as e:
            logger.error(f"Error calculating trade duration: {str(e)}")
            return None
    
    def _compare_to_average_performance(self, signal: 'TradingSignals') -> Dict[str, Any]:
        """Compare signal performance to system average"""
        try:
            # Get average performance for this symbol
            avg_metrics = self.calculate_system_metrics(signal.symbol, 30)
            
            if not avg_metrics:
                return {}
            
            signal_pnl = signal.pnl or 0
            avg_pnl = avg_metrics.get('pnl_metrics', {}).get('total_pnl', 0) / max(avg_metrics.get('basic_metrics', {}).get('total_signals', 1), 1)
            
            return {
                'signal_pnl': signal_pnl,
                'average_pnl': round(avg_pnl, 2),
                'performance_vs_average': 'above' if signal_pnl > avg_pnl else 'below' if signal_pnl < avg_pnl else 'equal',
                'confidence_vs_average': 'above' if (signal.confidence_score or 0) > avg_metrics.get('basic_metrics', {}).get('average_confidence', 0) else 'below'
            }
            
        except Exception as e:
            logger.error(f"Error comparing to average performance: {str(e)}")
            return {}
