"""
Core signal analysis logic
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class SignalAnalyzer:
    """Analyzes technical indicators and SMC data to determine signals"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Signal thresholds
        self.rsi_oversold = config.RSI_OVERSOLD
        self.rsi_overbought = config.RSI_OVERBOUGHT
        self.macd_threshold = config.MACD_SIGNAL_THRESHOLD
        
        # Confluence requirements
        self.min_confluence_score = 3  # Minimum confluences for signal
        self.strong_signal_score = 5   # Score for strong signals
    
    def analyze_signal(self, symbol: str, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Main signal analysis function"""
        try:
            # Extract indicator data
            trend_data = indicators.get('trend', {})
            momentum_data = indicators.get('momentum', {})
            volatility_data = indicators.get('volatility', {})
            volume_data = indicators.get('volume', {})
            smc_data = indicators.get('smc', {})
            market_data = indicators.get('market_data', {})
            
            # Analyze each category
            trend_analysis = self._analyze_trend(trend_data, market_data)
            momentum_analysis = self._analyze_momentum(momentum_data)
            volatility_analysis = self._analyze_volatility(volatility_data, market_data)
            volume_analysis = self._analyze_volume(volume_data)
            smc_analysis = self._analyze_smc(smc_data)
            
            # Determine overall signal
            signal_result = self._determine_signal(
                trend_analysis, momentum_analysis, volatility_analysis,
                volume_analysis, smc_analysis, market_data
            )
            
            return {
                'symbol': symbol,
                'timestamp': datetime.utcnow(),
                'signal': signal_result['signal'],
                'confidence': signal_result['confidence'],
                'reasoning': signal_result['reasoning'],
                'confluences': signal_result['confluences'],
                'risk_reward': signal_result.get('risk_reward'),
                'entry_price': market_data.get('close'),
                'stop_loss': signal_result.get('stop_loss'),
                'take_profit': signal_result.get('take_profit'),
                'trend_analysis': trend_analysis,
                'momentum_analysis': momentum_analysis,
                'volatility_analysis': volatility_analysis,
                'volume_analysis': volume_analysis,
                'smc_analysis': smc_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing signal for {symbol}: {str(e)}")
            return self._create_error_result(symbol)
    
    def _analyze_trend(self, trend_data: Dict, market_data: Dict) -> Dict[str, Any]:
        """Analyze trend indicators"""
        analysis = {
            'direction': 'neutral',
            'strength': 0,
            'confluences': [],
            'details': {}
        }
        
        try:
            current_price = market_data.get('close', 0)
            sma_20 = trend_data.get('sma_20')
            sma_50 = trend_data.get('sma_50')
            ema_12 = trend_data.get('ema_12')
            ema_26 = trend_data.get('ema_26')
            macd = trend_data.get('macd')
            macd_signal = trend_data.get('macd_signal')
            macd_histogram = trend_data.get('macd_histogram')
            adx = trend_data.get('adx')
            
            bullish_signals = 0
            bearish_signals = 0
            
            # Moving Average Analysis
            if sma_20 and sma_50:
                if sma_20 > sma_50:
                    bullish_signals += 1
                    analysis['confluences'].append("SMA 20 > SMA 50 (bullish trend)")
                elif sma_20 < sma_50:
                    bearish_signals += 1
                    analysis['confluences'].append("SMA 20 < SMA 50 (bearish trend)")
            
            # Price vs Moving Averages
            if sma_20 and current_price > sma_20:
                bullish_signals += 1
                analysis['confluences'].append("Price above SMA 20")
            elif sma_20 and current_price < sma_20:
                bearish_signals += 1
                analysis['confluences'].append("Price below SMA 20")
            
            # EMA Analysis
            if ema_12 and ema_26:
                if ema_12 > ema_26:
                    bullish_signals += 1
                    analysis['confluences'].append("EMA 12 > EMA 26")
                elif ema_12 < ema_26:
                    bearish_signals += 1
                    analysis['confluences'].append("EMA 12 < EMA 26")
            
            # MACD Analysis
            if macd and macd_signal:
                if macd > macd_signal and abs(macd - macd_signal) > self.macd_threshold:
                    bullish_signals += 1
                    analysis['confluences'].append("MACD bullish crossover")
                elif macd < macd_signal and abs(macd - macd_signal) > self.macd_threshold:
                    bearish_signals += 1
                    analysis['confluences'].append("MACD bearish crossover")
            
            # MACD Histogram
            if macd_histogram:
                if macd_histogram > 0:
                    bullish_signals += 0.5
                    analysis['confluences'].append("MACD histogram positive")
                elif macd_histogram < 0:
                    bearish_signals += 0.5
                    analysis['confluences'].append("MACD histogram negative")
            
            # ADX Trend Strength
            if adx and adx > 25:
                analysis['confluences'].append(f"Strong trend (ADX: {adx:.1f})")
                analysis['strength'] = min(adx / 25, 2)  # Cap at 2x strength
            
            # Determine trend direction
            if bullish_signals > bearish_signals + 1:
                analysis['direction'] = 'bullish'
            elif bearish_signals > bullish_signals + 1:
                analysis['direction'] = 'bearish'
            
            analysis['details'] = {
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'macd': macd,
                'macd_signal': macd_signal,
                'adx': adx
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend: {str(e)}")
        
        return analysis
    
    def _analyze_momentum(self, momentum_data: Dict) -> Dict[str, Any]:
        """Analyze momentum indicators"""
        analysis = {
            'condition': 'neutral',
            'strength': 0,
            'confluences': [],
            'details': {}
        }
        
        try:
            rsi = momentum_data.get('rsi')
            stoch_k = momentum_data.get('stochastic_k')
            stoch_d = momentum_data.get('stochastic_d')
            cci = momentum_data.get('cci')
            williams_r = momentum_data.get('williams_r')
            
            bullish_signals = 0
            bearish_signals = 0
            
            # RSI Analysis
            if rsi:
                if rsi < self.rsi_oversold:
                    bullish_signals += 2  # Strong bullish signal
                    analysis['confluences'].append(f"RSI oversold ({rsi:.1f})")
                elif rsi > self.rsi_overbought:
                    bearish_signals += 2  # Strong bearish signal
                    analysis['confluences'].append(f"RSI overbought ({rsi:.1f})")
                elif rsi < 45:
                    bullish_signals += 0.5
                    analysis['confluences'].append(f"RSI below midpoint ({rsi:.1f})")
                elif rsi > 55:
                    bearish_signals += 0.5
                    analysis['confluences'].append(f"RSI above midpoint ({rsi:.1f})")
            
            # Stochastic Analysis
            if stoch_k and stoch_d:
                if stoch_k < 20 and stoch_d < 20:
                    bullish_signals += 1
                    analysis['confluences'].append("Stochastic oversold")
                elif stoch_k > 80 and stoch_d > 80:
                    bearish_signals += 1
                    analysis['confluences'].append("Stochastic overbought")
                
                # Stochastic crossover
                if stoch_k > stoch_d and stoch_k < 80:
                    bullish_signals += 0.5
                    analysis['confluences'].append("Stochastic bullish crossover")
                elif stoch_k < stoch_d and stoch_k > 20:
                    bearish_signals += 0.5
                    analysis['confluences'].append("Stochastic bearish crossover")
            
            # CCI Analysis
            if cci:
                if cci < -100:
                    bullish_signals += 1
                    analysis['confluences'].append(f"CCI oversold ({cci:.1f})")
                elif cci > 100:
                    bearish_signals += 1
                    analysis['confluences'].append(f"CCI overbought ({cci:.1f})")
            
            # Williams %R Analysis
            if williams_r:
                if williams_r < -80:
                    bullish_signals += 1
                    analysis['confluences'].append("Williams %R oversold")
                elif williams_r > -20:
                    bearish_signals += 1
                    analysis['confluences'].append("Williams %R overbought")
            
            # Determine momentum condition
            if bullish_signals > bearish_signals + 0.5:
                analysis['condition'] = 'bullish'
                analysis['strength'] = min(bullish_signals / 2, 2)
            elif bearish_signals > bullish_signals + 0.5:
                analysis['condition'] = 'bearish'
                analysis['strength'] = min(bearish_signals / 2, 2)
            
            analysis['details'] = {
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals,
                'rsi': rsi,
                'stochastic_k': stoch_k,
                'stochastic_d': stoch_d,
                'cci': cci,
                'williams_r': williams_r
            }
            
        except Exception as e:
            logger.error(f"Error analyzing momentum: {str(e)}")
        
        return analysis
    
    def _analyze_volatility(self, volatility_data: Dict, market_data: Dict) -> Dict[str, Any]:
        """Analyze volatility indicators"""
        analysis = {
            'condition': 'normal',
            'support_resistance': [],
            'confluences': [],
            'details': {}
        }
        
        try:
            current_price = market_data.get('close', 0)
            bb_upper = volatility_data.get('bollinger_upper')
            bb_middle = volatility_data.get('bollinger_middle')
            bb_lower = volatility_data.get('bollinger_lower')
            atr = volatility_data.get('atr')
            
            # Bollinger Bands Analysis
            if bb_upper and bb_lower and bb_middle and current_price:
                bb_position = self._calculate_bb_position(current_price, bb_upper, bb_lower)
                
                if bb_position < 0.2:  # Near lower band
                    analysis['confluences'].append("Price near Bollinger lower band (oversold)")
                    analysis['support_resistance'].append({
                        'type': 'support',
                        'price': bb_lower,
                        'strength': 'medium'
                    })
                elif bb_position > 0.8:  # Near upper band
                    analysis['confluences'].append("Price near Bollinger upper band (overbought)")
                    analysis['support_resistance'].append({
                        'type': 'resistance',
                        'price': bb_upper,
                        'strength': 'medium'
                    })
                
                # Bollinger Band squeeze detection
                bb_width = (bb_upper - bb_lower) / bb_middle
                if bb_width < 0.1:  # Tight bands indicate low volatility
                    analysis['condition'] = 'low_volatility'
                    analysis['confluences'].append("Bollinger Bands squeeze (breakout expected)")
                elif bb_width > 0.2:  # Wide bands indicate high volatility
                    analysis['condition'] = 'high_volatility'
                    analysis['confluences'].append("High volatility environment")
            
            # ATR Analysis
            if atr and current_price:
                atr_percentage = (atr / current_price) * 100
                if atr_percentage > 2:
                    analysis['condition'] = 'high_volatility'
                    analysis['confluences'].append(f"High ATR ({atr_percentage:.2f}%)")
                elif atr_percentage < 0.5:
                    analysis['condition'] = 'low_volatility'
                    analysis['confluences'].append(f"Low ATR ({atr_percentage:.2f}%)")
            
            analysis['details'] = {
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'atr': atr,
                'bb_position': bb_position if 'bb_position' in locals() else None
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volatility: {str(e)}")
        
        return analysis
    
    def _analyze_volume(self, volume_data: Dict) -> Dict[str, Any]:
        """Analyze volume indicators"""
        analysis = {
            'trend': 'neutral',
            'confluences': [],
            'details': {}
        }
        
        try:
            obv = volume_data.get('obv')
            ad_line = volume_data.get('ad_line')
            cmf = volume_data.get('cmf')
            
            bullish_signals = 0
            bearish_signals = 0
            
            # Note: Volume analysis is limited for forex pairs
            # These indicators are more relevant for stocks/crypto
            
            if cmf:
                if cmf > 0.1:
                    bullish_signals += 1
                    analysis['confluences'].append("Positive money flow")
                elif cmf < -0.1:
                    bearish_signals += 1
                    analysis['confluences'].append("Negative money flow")
            
            # Determine volume trend
            if bullish_signals > bearish_signals:
                analysis['trend'] = 'bullish'
            elif bearish_signals > bullish_signals:
                analysis['trend'] = 'bearish'
            
            analysis['details'] = {
                'obv': obv,
                'ad_line': ad_line,
                'cmf': cmf
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume: {str(e)}")
        
        return analysis
    
    def _analyze_smc(self, smc_data: Dict) -> Dict[str, Any]:
        """Analyze Smart Money Concepts"""
        analysis = {
            'market_structure': 'neutral',
            'key_levels': [],
            'confluences': [],
            'details': {}
        }
        
        try:
            market_structure = smc_data.get('market_structure', 'neutral')
            bos_points = smc_data.get('bos_points', [])
            choch_points = smc_data.get('choch_points', [])
            order_blocks = smc_data.get('order_blocks', [])
            fair_value_gaps = smc_data.get('fair_value_gaps', [])
            liquidity_zones = smc_data.get('liquidity_zones', [])
            
            analysis['market_structure'] = market_structure
            
            # Market Structure Analysis
            if market_structure == 'bullish':
                analysis['confluences'].append("Bullish market structure (HH, HL)")
            elif market_structure == 'bearish':
                analysis['confluences'].append("Bearish market structure (LH, LL)")
            
            # Break of Structure
            recent_bos = [bos for bos in bos_points if bos.get('index', 0) > len(bos_points) - 10]
            for bos in recent_bos:
                if bos.get('type') == 'bullish_bos':
                    analysis['confluences'].append("Recent bullish Break of Structure")
                elif bos.get('type') == 'bearish_bos':
                    analysis['confluences'].append("Recent bearish Break of Structure")
            
            # Change of Character
            recent_choch = [choch for choch in choch_points if choch.get('index', 0) > len(choch_points) - 10]
            for choch in recent_choch:
                analysis['confluences'].append("Change of Character detected")
            
            # Order Blocks
            recent_obs = sorted(order_blocks, key=lambda x: x.get('index', 0))[-3:]
            for ob in recent_obs:
                ob_type = ob.get('type', '')
                ob_price = (ob.get('high', 0) + ob.get('low', 0)) / 2
                strength = ob.get('strength', 0)
                
                analysis['key_levels'].append({
                    'type': 'order_block',
                    'direction': 'bullish' if 'bullish' in ob_type else 'bearish',
                    'price': ob_price,
                    'strength': strength
                })
                
                if strength > 0.02:  # Strong order block
                    analysis['confluences'].append(f"Strong {ob_type.replace('_', ' ')}")
            
            # Fair Value Gaps
            recent_fvgs = sorted(fair_value_gaps, key=lambda x: x.get('index', 0))[-3:]
            for fvg in recent_fvgs:
                fvg_type = fvg.get('type', '')
                fvg_high = fvg.get('high', 0)
                fvg_low = fvg.get('low', 0)
                
                analysis['key_levels'].append({
                    'type': 'fair_value_gap',
                    'direction': 'bullish' if 'bullish' in fvg_type else 'bearish',
                    'high': fvg_high,
                    'low': fvg_low
                })
                
                analysis['confluences'].append(f"Unfilled {fvg_type.replace('_', ' ')}")
            
            # Liquidity Zones
            recent_liq = sorted(liquidity_zones, key=lambda x: x.get('touches', 0))[-3:]
            for liq in recent_liq:
                liq_type = liq.get('type', '')
                liq_price = liq.get('price', 0)
                touches = liq.get('touches', 0)
                
                analysis['key_levels'].append({
                    'type': 'liquidity_zone',
                    'direction': liq_type,
                    'price': liq_price,
                    'strength': touches
                })
                
                if touches >= 3:
                    analysis['confluences'].append(f"Strong {liq_type} zone ({touches} touches)")
            
            analysis['details'] = {
                'bos_count': len(bos_points),
                'choch_count': len(choch_points),
                'order_blocks_count': len(order_blocks),
                'fvg_count': len(fair_value_gaps),
                'liquidity_zones_count': len(liquidity_zones)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing SMC: {str(e)}")
        
        return analysis
    
    def _determine_signal(self, trend_analysis: Dict, momentum_analysis: Dict, 
                         volatility_analysis: Dict, volume_analysis: Dict,
                         smc_analysis: Dict, market_data: Dict) -> Dict[str, Any]:
        """Determine final trading signal based on all analyses"""
        
        bullish_score = 0
        bearish_score = 0
        confluences = []
        
        # Trend Analysis Weight: 30%
        if trend_analysis['direction'] == 'bullish':
            bullish_score += 3 * trend_analysis.get('strength', 1)
            confluences.extend(trend_analysis['confluences'])
        elif trend_analysis['direction'] == 'bearish':
            bearish_score += 3 * trend_analysis.get('strength', 1)
            confluences.extend(trend_analysis['confluences'])
        
        # Momentum Analysis Weight: 25%
        if momentum_analysis['condition'] == 'bullish':
            bullish_score += 2.5 * momentum_analysis.get('strength', 1)
            confluences.extend(momentum_analysis['confluences'])
        elif momentum_analysis['condition'] == 'bearish':
            bearish_score += 2.5 * momentum_analysis.get('strength', 1)
            confluences.extend(momentum_analysis['confluences'])
        
        # SMC Analysis Weight: 25%
        if smc_analysis['market_structure'] == 'bullish':
            bullish_score += 2.5
            confluences.extend(smc_analysis['confluences'])
        elif smc_analysis['market_structure'] == 'bearish':
            bearish_score += 2.5
            confluences.extend(smc_analysis['confluences'])
        
        # Volume Analysis Weight: 10%
        if volume_analysis['trend'] == 'bullish':
            bullish_score += 1
            confluences.extend(volume_analysis['confluences'])
        elif volume_analysis['trend'] == 'bearish':
            bearish_score += 1
            confluences.extend(volume_analysis['confluences'])
        
        # Volatility considerations Weight: 10%
        volatility_confluences = volatility_analysis.get('confluences', [])
        confluences.extend(volatility_confluences)
        
        # Determine signal
        signal = 'HOLD'
        confidence = 0
        
        if bullish_score >= self.min_confluence_score and bullish_score > bearish_score + 1:
            signal = 'BUY'
            confidence = min(bullish_score / self.strong_signal_score * 100, 100)
        elif bearish_score >= self.min_confluence_score and bearish_score > bullish_score + 1:
            signal = 'SELL'
            confidence = min(bearish_score / self.strong_signal_score * 100, 100)
        else:
            confidence = 50  # Neutral confidence for HOLD
        
        # Calculate risk management levels
        current_price = market_data.get('close', 0)
        atr = volatility_analysis.get('details', {}).get('atr', 0)
        
        stop_loss, take_profit, risk_reward = self._calculate_risk_levels(
            signal, current_price, atr, smc_analysis, volatility_analysis
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            signal, confluences, trend_analysis, momentum_analysis,
            smc_analysis, current_price, stop_loss, take_profit, risk_reward
        )
        
        return {
            'signal': signal,
            'confidence': round(confidence, 1),
            'reasoning': reasoning,
            'confluences': confluences,
            'bullish_score': round(bullish_score, 2),
            'bearish_score': round(bearish_score, 2),
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': risk_reward
        }
    
    def _calculate_bb_position(self, price: float, bb_upper: float, bb_lower: float) -> float:
        """Calculate position within Bollinger Bands (0 = lower band, 1 = upper band)"""
        if bb_upper == bb_lower:
            return 0.5
        return (price - bb_lower) / (bb_upper - bb_lower)
    
    def _calculate_risk_levels(self, signal: str, current_price: float, atr: float,
                              smc_analysis: Dict, volatility_analysis: Dict) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate stop loss, take profit, and risk/reward ratio"""
        if signal == 'HOLD' or not current_price or not atr:
            return None, None, None
        
        # Base ATR multipliers
        stop_loss_atr_multiplier = 1.5
        take_profit_atr_multiplier = 3.0
        
        # Adjust based on volatility
        volatility_condition = volatility_analysis.get('condition', 'normal')
        if volatility_condition == 'high_volatility':
            stop_loss_atr_multiplier = 2.0
            take_profit_atr_multiplier = 4.0
        elif volatility_condition == 'low_volatility':
            stop_loss_atr_multiplier = 1.0
            take_profit_atr_multiplier = 2.0
        
        # Look for SMC levels for better stop loss placement
        key_levels = smc_analysis.get('key_levels', [])
        
        if signal == 'BUY':
            # Default stop loss
            stop_loss = current_price - (atr * stop_loss_atr_multiplier)
            
            # Check for nearby support levels
            support_levels = [level for level in key_levels 
                            if level.get('type') in ['order_block', 'liquidity_zone'] 
                            and level.get('direction') == 'bullish'
                            and level.get('price', 0) < current_price]
            
            if support_levels:
                nearest_support = max(support_levels, key=lambda x: x.get('price', 0))
                support_price = nearest_support.get('price', 0)
                if support_price > stop_loss and (current_price - support_price) < (atr * 2):
                    stop_loss = support_price - (atr * 0.2)  # Slightly below support
            
            take_profit = current_price + (atr * take_profit_atr_multiplier)
            
        else:  # SELL
            # Default stop loss
            stop_loss = current_price + (atr * stop_loss_atr_multiplier)
            
            # Check for nearby resistance levels
            resistance_levels = [level for level in key_levels 
                               if level.get('type') in ['order_block', 'liquidity_zone'] 
                               and level.get('direction') == 'bearish'
                               and level.get('price', 0) > current_price]
            
            if resistance_levels:
                nearest_resistance = min(resistance_levels, key=lambda x: x.get('price', 0))
                resistance_price = nearest_resistance.get('price', 0)
                if resistance_price < stop_loss and (resistance_price - current_price) < (atr * 2):
                    stop_loss = resistance_price + (atr * 0.2)  # Slightly above resistance
            
            take_profit = current_price - (atr * take_profit_atr_multiplier)
        
        # Calculate risk/reward ratio
        risk = abs(current_price - stop_loss)
        reward = abs(take_profit - current_price)
        risk_reward = round(reward / risk, 2) if risk > 0 else None
        
        return round(stop_loss, 5), round(take_profit, 5), risk_reward
    
    def _generate_reasoning(self, signal: str, confluences: List[str], trend_analysis: Dict,
                           momentum_analysis: Dict, smc_analysis: Dict, current_price: float,
                           stop_loss: Optional[float], take_profit: Optional[float], 
                           risk_reward: Optional[float]) -> str:
        """Generate detailed reasoning for the signal"""
        
        reasoning_parts = []
        
        # Signal decision
        if signal == 'BUY':
            reasoning_parts.append("BULLISH SIGNAL DETECTED")
        elif signal == 'SELL':
            reasoning_parts.append("BEARISH SIGNAL DETECTED")
        else:
            reasoning_parts.append("NO CLEAR DIRECTIONAL BIAS - HOLD POSITION")
        
        # Key confluences (limit to top 5 for readability)
        if confluences:
            reasoning_parts.append("\nKey Confluences:")
            for i, confluence in enumerate(confluences[:5]):
                reasoning_parts.append(f"• {confluence}")
            if len(confluences) > 5:
                reasoning_parts.append(f"• ... and {len(confluences) - 5} more confluences")
        
        # Trend context
        trend_dir = trend_analysis.get('direction', 'neutral')
        if trend_dir != 'neutral':
            reasoning_parts.append(f"\nTrend Analysis: {trend_dir.upper()} trend confirmed")
        
        # Momentum context
        momentum_cond = momentum_analysis.get('condition', 'neutral')
        if momentum_cond != 'neutral':
            rsi = momentum_analysis.get('details', {}).get('rsi')
            if rsi:
                reasoning_parts.append(f"Momentum: {momentum_cond.upper()} (RSI: {rsi:.1f})")
        
        # SMC context
        market_structure = smc_analysis.get('market_structure', 'neutral')
        if market_structure != 'neutral':
            reasoning_parts.append(f"Market Structure: {market_structure.upper()}")
        
        # Risk management
        if signal != 'HOLD' and stop_loss and take_profit and risk_reward:
            reasoning_parts.append(f"\nRisk Management:")
            reasoning_parts.append(f"Entry: {current_price:.5f}")
            reasoning_parts.append(f"Stop Loss: {stop_loss:.5f}")
            reasoning_parts.append(f"Take Profit: {take_profit:.5f}")
            reasoning_parts.append(f"Risk/Reward Ratio: 1:{risk_reward}")
        
        return "\n".join(reasoning_parts)
    
    def _create_error_result(self, symbol: str) -> Dict[str, Any]:
        """Create error result when analysis fails"""
        return {
            'symbol': symbol,
            'timestamp': datetime.utcnow(),
            'signal': 'HOLD',
            'confidence': 0,
            'reasoning': 'Error occurred during signal analysis. No position recommended.',
            'confluences': [],
            'error': True
        }
