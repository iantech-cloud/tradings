"""
Advanced analytics and insights generation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from app import db
from models import TradingSignals, SystemPerformance, MarketData

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """Advanced analytics and insights generation"""
    
    def generate_insights(self, symbol: str = None, days: int = 30) -> Dict[str, Any]:
        """Generate actionable insights from trading data"""
        try:
            insights = {
                'performance_insights': self._analyze_performance_patterns(symbol, days),
                'market_insights': self._analyze_market_conditions(symbol, days),
                'timing_insights': self._analyze_timing_patterns(symbol, days),
                'confidence_insights': self._analyze_confidence_patterns(symbol, days),
                'recommendations': []
            }
            
            # Generate recommendations based on insights
            insights['recommendations'] = self._generate_recommendations(insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {}
    
    def analyze_strategy_effectiveness(self, days: int = 30) -> Dict[str, Any]:
        """Analyze effectiveness of different trading strategies"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            signals = TradingSignals.query.filter(
                TradingSignals.timestamp >= cutoff_date,
                TradingSignals.outcome.isnot(None)
            ).all()
            
            if not signals:
                return {}
            
            # Analyze by trend direction
            trend_analysis = self._analyze_by_trend_direction(signals)
            
            # Analyze by confidence levels
            confidence_analysis = self._analyze_by_confidence_levels(signals)
            
            # Analyze by market conditions
            market_conditions_analysis = self._analyze_by_market_conditions(signals)
            
            # Analyze by signal type
            signal_type_analysis = self._analyze_by_signal_type(signals)
            
            return {
                'period_days': days,
                'total_signals_analyzed': len(signals),
                'trend_direction_analysis': trend_analysis,
                'confidence_level_analysis': confidence_analysis,
                'market_conditions_analysis': market_conditions_analysis,
                'signal_type_analysis': signal_type_analysis,
                'strategy_recommendations': self._generate_strategy_recommendations(
                    trend_analysis, confidence_analysis, market_conditions_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing strategy effectiveness: {str(e)}")
            return {}
    
    def get_risk_analysis(self, symbol: str = None, days: int = 30) -> Dict[str, Any]:
        """Comprehensive risk analysis"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = TradingSignals.query.filter(
                TradingSignals.timestamp >= cutoff_date,
                TradingSignals.outcome.isnot(None)
            )
            
            if symbol:
                query = query.filter(TradingSignals.symbol == symbol)
            
            signals = query.all()
            
            if not signals:
                return {}
            
            pnl_values = [s.pnl or 0 for s in signals]
            
            # Risk metrics
            var_95 = np.percentile(pnl_values, 5) if pnl_values else 0  # Value at Risk (95%)
            cvar_95 = np.mean([pnl for pnl in pnl_values if pnl <= var_95]) if pnl_values else 0  # Conditional VaR
            
            # Consecutive losses analysis
            consecutive_losses = self._analyze_consecutive_losses(signals)
            
            # Risk-reward analysis
            risk_reward_analysis = self._analyze_risk_reward_ratios(signals)
            
            # Volatility analysis
            volatility = np.std(pnl_values) if len(pnl_values) > 1 else 0
            
            return {
                'period_days': days,
                'symbol': symbol or 'ALL',
                'risk_metrics': {
                    'value_at_risk_95': round(var_95, 2),
                    'conditional_var_95': round(cvar_95, 2),
                    'volatility': round(volatility, 2),
                    'max_loss': round(min(pnl_values), 2) if pnl_values else 0,
                    'max_gain': round(max(pnl_values), 2) if pnl_values else 0
                },
                'consecutive_losses': consecutive_losses,
                'risk_reward_analysis': risk_reward_analysis,
                'risk_recommendations': self._generate_risk_recommendations(var_95, consecutive_losses, volatility)
            }
            
        except Exception as e:
            logger.error(f"Error in risk analysis: {str(e)}")
            return {}
    
    def _analyze_performance_patterns(self, symbol: str, days: int) -> Dict[str, Any]:
        """Analyze performance patterns"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = TradingSignals.query.filter(
            TradingSignals.timestamp >= cutoff_date,
            TradingSignals.outcome.isnot(None)
        )
        
        if symbol:
            query = query.filter(TradingSignals.symbol == symbol)
        
        signals = query.all()
        
        if not signals:
            return {}
        
        wins = [s for s in signals if (s.pnl or 0) > 0]
        losses = [s for s in signals if (s.pnl or 0) < 0]
        
        return {
            'win_rate': round(len(wins) / len(signals) * 100, 2),
            'avg_win': round(np.mean([s.pnl for s in wins]), 2) if wins else 0,
            'avg_loss': round(np.mean([s.pnl for s in losses]), 2) if losses else 0,
            'profit_factor': round(sum([s.pnl for s in wins]) / abs(sum([s.pnl for s in losses])), 2) if losses else float('inf'),
            'best_performing_hours': self._get_best_performing_hours(signals),
            'best_performing_days': self._get_best_performing_days(signals)
        }
    
    def _analyze_market_conditions(self, symbol: str, days: int) -> Dict[str, Any]:
        """Analyze market condition patterns"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = TradingSignals.query.filter(
            TradingSignals.timestamp >= cutoff_date,
            TradingSignals.outcome.isnot(None)
        )
        
        if symbol:
            query = query.filter(TradingSignals.symbol == symbol)
        
        signals = query.all()
        
        if not signals:
            return {}
        
        # Group by market condition
        trending_signals = [s for s in signals if 'trending' in (s.reasoning or '').lower()]
        ranging_signals = [s for s in signals if 'ranging' in (s.reasoning or '').lower()]
        volatile_signals = [s for s in signals if 'volatile' in (s.reasoning or '').lower()]
        
        return {
            'trending_performance': self._calculate_condition_performance(trending_signals),
            'ranging_performance': self._calculate_condition_performance(ranging_signals),
            'volatile_performance': self._calculate_condition_performance(volatile_signals)
        }
    
    def _analyze_timing_patterns(self, symbol: str, days: int) -> Dict[str, Any]:
        """Analyze timing patterns"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = TradingSignals.query.filter(
            TradingSignals.timestamp >= cutoff_date,
            TradingSignals.outcome.isnot(None)
        )
        
        if symbol:
            query = query.filter(TradingSignals.symbol == symbol)
        
        signals = query.all()
        
        if not signals:
            return {}
        
        # Analyze by hour of day
        hourly_performance = {}
        for hour in range(24):
            hour_signals = [s for s in signals if s.timestamp.hour == hour]
            if hour_signals:
                hourly_performance[hour] = self._calculate_condition_performance(hour_signals)
        
        # Analyze by day of week
        daily_performance = {}
        for day in range(7):  # 0 = Monday, 6 = Sunday
            day_signals = [s for s in signals if s.timestamp.weekday() == day]
            if day_signals:
                daily_performance[day] = self._calculate_condition_performance(day_signals)
        
        return {
            'hourly_performance': hourly_performance,
            'daily_performance': daily_performance,
            'best_trading_hours': sorted(hourly_performance.items(), key=lambda x: x[1]['win_rate'], reverse=True)[:3],
            'best_trading_days': sorted(daily_performance.items(), key=lambda x: x[1]['win_rate'], reverse=True)[:3]
        }
    
    def _analyze_confidence_patterns(self, symbol: str, days: int) -> Dict[str, Any]:
        """Analyze confidence level patterns"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = TradingSignals.query.filter(
            TradingSignals.timestamp >= cutoff_date,
            TradingSignals.outcome.isnot(None)
        )
        
        if symbol:
            query = query.filter(TradingSignals.symbol == symbol)
        
        signals = query.all()
        
        if not signals:
            return {}
        
        # Group by confidence levels
        high_confidence = [s for s in signals if (s.confidence or 0) >= 80]
        medium_confidence = [s for s in signals if 60 <= (s.confidence or 0) < 80]
        low_confidence = [s for s in signals if (s.confidence or 0) < 60]
        
        return {
            'high_confidence_performance': self._calculate_condition_performance(high_confidence),
            'medium_confidence_performance': self._calculate_condition_performance(medium_confidence),
            'low_confidence_performance': self._calculate_condition_performance(low_confidence),
            'confidence_correlation': self._calculate_confidence_correlation(signals)
        }
    
    def _calculate_condition_performance(self, signals: List) -> Dict[str, Any]:
        """Calculate performance metrics for a condition"""
        if not signals:
            return {'count': 0, 'win_rate': 0, 'avg_pnl': 0}
        
        wins = [s for s in signals if (s.pnl or 0) > 0]
        total_pnl = sum([s.pnl or 0 for s in signals])
        
        return {
            'count': len(signals),
            'win_rate': round(len(wins) / len(signals) * 100, 2),
            'avg_pnl': round(total_pnl / len(signals), 2),
            'total_pnl': round(total_pnl, 2)
        }
    
    def _get_best_performing_hours(self, signals: List) -> List[int]:
        """Get best performing hours"""
        hourly_pnl = {}
        for signal in signals:
            hour = signal.timestamp.hour
            if hour not in hourly_pnl:
                hourly_pnl[hour] = []
            hourly_pnl[hour].append(signal.pnl or 0)
        
        hourly_avg = {hour: np.mean(pnls) for hour, pnls in hourly_pnl.items()}
        return sorted(hourly_avg.keys(), key=lambda x: hourly_avg[x], reverse=True)[:3]
    
    def _get_best_performing_days(self, signals: List) -> List[int]:
        """Get best performing days of week"""
        daily_pnl = {}
        for signal in signals:
            day = signal.timestamp.weekday()
            if day not in daily_pnl:
                daily_pnl[day] = []
            daily_pnl[day].append(signal.pnl or 0)
        
        daily_avg = {day: np.mean(pnls) for day, pnls in daily_pnl.items()}
        return sorted(daily_avg.keys(), key=lambda x: daily_avg[x], reverse=True)[:3]
    
    def _analyze_consecutive_losses(self, signals: List) -> Dict[str, Any]:
        """Analyze consecutive losses patterns"""
        sorted_signals = sorted(signals, key=lambda x: x.timestamp)
        
        current_streak = 0
        max_streak = 0
        streaks = []
        
        for signal in sorted_signals:
            if (signal.pnl or 0) < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                if current_streak > 0:
                    streaks.append(current_streak)
                current_streak = 0
        
        if current_streak > 0:
            streaks.append(current_streak)
        
        return {
            'max_consecutive_losses': max_streak,
            'avg_consecutive_losses': round(np.mean(streaks), 2) if streaks else 0,
            'total_loss_streaks': len(streaks)
        }
    
    def _analyze_risk_reward_ratios(self, signals: List) -> Dict[str, Any]:
        """Analyze risk-reward ratios"""
        ratios = []
        for signal in signals:
            if signal.stop_loss and signal.take_profit and signal.entry_price:
                risk = abs(signal.entry_price - signal.stop_loss)
                reward = abs(signal.take_profit - signal.entry_price)
                if risk > 0:
                    ratios.append(reward / risk)
        
        if not ratios:
            return {}
        
        return {
            'avg_risk_reward_ratio': round(np.mean(ratios), 2),
            'median_risk_reward_ratio': round(np.median(ratios), 2),
            'min_risk_reward_ratio': round(min(ratios), 2),
            'max_risk_reward_ratio': round(max(ratios), 2)
        }
    
    def _calculate_confidence_correlation(self, signals: List) -> float:
        """Calculate correlation between confidence and performance"""
        if len(signals) < 2:
            return 0
        
        confidences = [s.confidence or 0 for s in signals]
        pnls = [s.pnl or 0 for s in signals]
        
        return round(np.corrcoef(confidences, pnls)[0, 1], 3) if len(set(confidences)) > 1 else 0
    
    def _generate_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Performance-based recommendations
        perf = insights.get('performance_insights', {})
        if perf.get('win_rate', 0) < 50:
            recommendations.append("Consider tightening entry criteria - current win rate is below 50%")
        
        # Timing-based recommendations
        timing = insights.get('timing_insights', {})
        if timing.get('best_trading_hours'):
            best_hours = [str(h[0]) for h in timing['best_trading_hours']]
            recommendations.append(f"Focus trading during hours: {', '.join(best_hours)} for better performance")
        
        # Confidence-based recommendations
        confidence = insights.get('confidence_insights', {})
        if confidence.get('confidence_correlation', 0) > 0.3:
            recommendations.append("Higher confidence signals show better performance - consider filtering low confidence signals")
        
        return recommendations
    
    def _generate_risk_recommendations(self, var_95: float, consecutive_losses: Dict, volatility: float) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if var_95 < -100:  # Significant potential loss
            recommendations.append("Consider reducing position sizes - high Value at Risk detected")
        
        if consecutive_losses.get('max_consecutive_losses', 0) > 5:
            recommendations.append("Implement circuit breaker after 3-4 consecutive losses")
        
        if volatility > 50:
            recommendations.append("High volatility detected - consider wider stop losses or smaller positions")
        
        return recommendations
    
    def _analyze_by_trend_direction(self, signals: List) -> Dict[str, Any]:
        """Placeholder for trend direction analysis"""
        return {}
    
    def _analyze_by_confidence_levels(self, signals: List) -> Dict[str, Any]:
        """Placeholder for confidence levels analysis"""
        return {}
    
    def _analyze_by_market_conditions(self, signals: List) -> Dict[str, Any]:
        """Placeholder for market conditions analysis"""
        return {}
    
    def _analyze_by_signal_type(self, signals: List) -> Dict[str, Any]:
        """Placeholder for signal type analysis"""
        return {}
    
    def _generate_strategy_recommendations(self, trend_analysis: Dict, confidence_analysis: Dict, market_conditions_analysis: Dict) -> List[str]:
        """Placeholder for strategy recommendations generation"""
        return []
