from flask import jsonify, request, render_template
from app import app, db
from models import MarketData, TradingSignals, SystemPerformance
from datetime import datetime, timedelta
import json

@app.route('/api/signals')
def get_signals():
    """Get recent trading signals"""
    try:
        # Get query parameters
        symbol = request.args.get('symbol', 'all')
        limit = int(request.args.get('limit', 50))
        
        # Build query
        query = TradingSignals.query
        if symbol != 'all':
            query = query.filter(TradingSignals.symbol == symbol)
        
        signals = query.order_by(TradingSignals.timestamp.desc()).limit(limit).all()
        
        # Format response
        signals_data = []
        for signal in signals:
            signals_data.append({
                'id': signal.id,
                'symbol': signal.symbol,
                'timestamp': signal.timestamp.isoformat(),
                'signal_type': signal.signal_type,
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'risk_reward_ratio': signal.risk_reward_ratio,
                'reasoning': signal.reasoning,
                'confidence_score': signal.confidence_score,
                'status': signal.status,
                'pnl': signal.pnl
            })
        
        return jsonify({
            'success': True,
            'data': signals_data,
            'count': len(signals_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/performance')
def get_performance():
    """Get system performance metrics"""
    try:
        # Get query parameters
        symbol = request.args.get('symbol', 'all')
        days = int(request.args.get('days', 30))
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = SystemPerformance.query.filter(
            SystemPerformance.date >= start_date,
            SystemPerformance.date <= end_date
        )
        
        if symbol != 'all':
            query = query.filter(SystemPerformance.symbol == symbol)
        
        performance_data = query.all()
        
        # Calculate aggregate metrics
        total_signals = sum(p.total_signals for p in performance_data)
        total_wins = sum(p.winning_signals for p in performance_data)
        total_losses = sum(p.losing_signals for p in performance_data)
        total_pnl = sum(p.total_pnl for p in performance_data)
        
        win_rate = (total_wins / total_signals * 100) if total_signals > 0 else 0
        
        # Format daily performance
        daily_performance = []
        for p in performance_data:
            daily_performance.append({
                'date': p.date.isoformat(),
                'symbol': p.symbol,
                'total_signals': p.total_signals,
                'win_rate': p.win_rate,
                'total_pnl': p.total_pnl,
                'profit_factor': p.profit_factor
            })
        
        return jsonify({
            'success': True,
            'summary': {
                'total_signals': total_signals,
                'winning_signals': total_wins,
                'losing_signals': total_losses,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'period_days': days
            },
            'daily_performance': daily_performance
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market-data')
def get_market_data():
    """Get recent market data for a symbol"""
    try:
        symbol = request.args.get('symbol', 'EUR/USD')
        limit = int(request.args.get('limit', 100))
        
        market_data = MarketData.query.filter(
            MarketData.symbol == symbol
        ).order_by(MarketData.timestamp.desc()).limit(limit).all()
        
        # Format OHLCV data
        ohlcv_data = []
        for data in reversed(market_data):  # Reverse to get chronological order
            ohlcv_data.append({
                'timestamp': data.timestamp.isoformat(),
                'open': data.open_price,
                'high': data.high_price,
                'low': data.low_price,
                'close': data.close_price,
                'volume': data.volume
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'data': ohlcv_data,
            'count': len(ohlcv_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/signals')
def signals_page():
    """Signals history page"""
    return render_template('signals.html')

@app.route('/performance')
def performance_page():
    """Performance analytics page"""
    return render_template('performance.html')

@app.route('/settings')
def settings_page():
    """System settings page"""
    return render_template('settings.html')
