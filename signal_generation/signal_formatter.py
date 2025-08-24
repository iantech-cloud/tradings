"""
Signal formatting for storage and notifications
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalFormatter:
    """Formats signals for different outputs"""
    
    def format_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format signal data for storage and notifications"""
        try:
            # Extract key indicator values for storage
            trend_analysis = signal_data.get('trend_analysis', {})
            momentum_analysis = signal_data.get('momentum_analysis', {})
            smc_analysis = signal_data.get('smc_analysis', {})
            
            # Get key indicator values
            trend_details = trend_analysis.get('details', {})
            momentum_details = momentum_analysis.get('details', {})
            
            formatted_signal = {
                'symbol': signal_data['symbol'],
                'timestamp': signal_data['timestamp'],
                'signal': signal_data['signal'],
                'confidence': signal_data['confidence'],
                'reasoning': signal_data['reasoning'],
                'entry_price': signal_data['entry_price'],
                'stop_loss': signal_data.get('stop_loss'),
                'take_profit': signal_data.get('take_profit'),
                'risk_reward': signal_data.get('risk_reward'),
                
                # Key indicator values for database storage
                'rsi_value': momentum_details.get('rsi'),
                'macd_value': trend_details.get('macd'),
                'trend_direction': trend_analysis.get('direction'),
                'smc_confluence': self._format_smc_confluence(smc_analysis),
                
                # Additional context
                'confluences': signal_data.get('confluences', []),
                'bullish_score': signal_data.get('bullish_score'),
                'bearish_score': signal_data.get('bearish_score')
            }
            
            return formatted_signal
            
        except Exception as e:
            logger.error(f"Error formatting signal: {str(e)}")
            return signal_data
    
    def format_for_telegram(self, signal_data: Dict[str, Any]) -> str:
        """Format signal for Telegram notification"""
        try:
            symbol = signal_data['symbol']
            signal = signal_data['signal']
            confidence = signal_data['confidence']
            entry_price = signal_data['entry_price']
            stop_loss = signal_data.get('stop_loss')
            take_profit = signal_data.get('take_profit')
            risk_reward = signal_data.get('risk_reward')
            reasoning = signal_data['reasoning']
            
            # Signal emoji
            signal_emoji = {
                'BUY': '🟢',
                'SELL': '🔴',
                'HOLD': '🟡'
            }.get(signal, '⚪')
            
            # Confidence emoji
            if confidence >= 80:
                confidence_emoji = '🔥'
            elif confidence >= 70:
                confidence_emoji = '💪'
            elif confidence >= 60:
                confidence_emoji = '👍'
            else:
                confidence_emoji = '🤔'
            
            message_parts = [
                f"{signal_emoji} **{signal} {symbol}** {confidence_emoji}",
                f"Confidence: {confidence:.1f}%",
                f"Entry: {entry_price:.5f}" if entry_price else ""
            ]
            
            if signal != 'HOLD' and stop_loss and take_profit and risk_reward:
                message_parts.extend([
                    f"SL: {stop_loss:.5f}",
                    f"TP: {take_profit:.5f}",
                    f"R:R = 1:{risk_reward}"
                ])
            
            message_parts.append("")  # Empty line
            message_parts.append("**Analysis:**")
            message_parts.append(reasoning)
            
            # Add timestamp
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            message_parts.append("")
            message_parts.append(f"⏰ {timestamp}")
            
            return "\n".join(filter(None, message_parts))
            
        except Exception as e:
            logger.error(f"Error formatting signal for Telegram: {str(e)}")
            return f"Error formatting signal for {signal_data.get('symbol', 'Unknown')}"
    
    def format_for_web_display(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format signal for web interface display"""
        try:
            return {
                'id': signal_data.get('id'),
                'symbol': signal_data['symbol'],
                'timestamp': signal_data['timestamp'].isoformat() if isinstance(signal_data['timestamp'], datetime) else signal_data['timestamp'],
                'signal': signal_data['signal'],
                'confidence': signal_data['confidence'],
                'entry_price': signal_data['entry_price'],
                'stop_loss': signal_data.get('stop_loss'),
                'take_profit': signal_data.get('take_profit'),
                'risk_reward': signal_data.get('risk_reward'),
                'reasoning': signal_data['reasoning'],
                'status': signal_data.get('status', 'active'),
                'confluences': signal_data.get('confluences', []),
                'trend_direction': signal_data.get('trend_direction'),
                'rsi_value': signal_data.get('rsi_value'),
                'macd_value': signal_data.get('macd_value')
            }
            
        except Exception as e:
            logger.error(f"Error formatting signal for web: {str(e)}")
            return signal_data
    
    def _format_smc_confluence(self, smc_analysis: Dict[str, Any]) -> str:
        """Format SMC analysis into a string for database storage"""
        try:
            confluences = smc_analysis.get('confluences', [])
            market_structure = smc_analysis.get('market_structure', 'neutral')
            
            smc_parts = [f"Market Structure: {market_structure}"]
            
            if confluences:
                smc_parts.append("SMC Confluences:")
                smc_parts.extend([f"• {conf}" for conf in confluences[:3]])  # Limit to top 3
            
            return " | ".join(smc_parts)
            
        except Exception as e:
            logger.error(f"Error formatting SMC confluence: {str(e)}")
            return "SMC analysis available"
