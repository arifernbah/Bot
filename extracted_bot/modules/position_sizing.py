#!/usr/bin/env python3
"""
Position Sizing Module - Kelly Criterion & Risk Management
Professional grade position sizing untuk optimal capital allocation
"""

import numpy as np
from modules import FEE_RATE
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class KellyCriterionCalculator:
    """Kelly Criterion untuk optimal position sizing"""
    
    def __init__(self):
        self.default_win_rate = 0.6
        self.default_avg_win = 0.015
        self.default_avg_loss = 0.01
        
    def calculate_kelly_percentage(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Kelly Criterion: f* = (bp - q) / b
        where:
        - f* = fraction of capital to wager
        - b = odds received on the wager (avg_win / avg_loss)
        - p = probability of winning
        - q = probability of losing (1 - p)
        """
        try:
            if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
                return 0.01  # Conservative fallback
            
            p = win_rate
            q = 1 - p
            b = avg_win / abs(avg_loss)
            
            kelly_f = (b * p - q) / b
            
            # Safety caps
            kelly_f = max(0, min(kelly_f, 0.25))  # Cap at 25%
            
            # For small accounts, use fractional Kelly (more conservative)
            if kelly_f > 0.05:
                kelly_f = kelly_f * 0.4  # Use 40% of Kelly for safety
            
            return kelly_f
            
        except Exception as e:
            logger.error(f"Error calculating Kelly percentage: {e}")
            return 0.02  # Conservative fallback
    
    def update_performance_data(self, trades: List[Dict]) -> Dict[str, float]:
        """Update performance metrics dari trading history"""
        try:
            if len(trades) < 5:
                # Use default values for insufficient data
                return {
                    "win_rate": self.default_win_rate,
                    "avg_win": self.default_avg_win,
                    "avg_loss": self.default_avg_loss,
                    "kelly_percentage": self.calculate_kelly_percentage(
                        self.default_win_rate, 
                        self.default_avg_win, 
                        self.default_avg_loss
                    ),
                    "total_trades": len(trades)
                }
            
            # Separate wins and losses
            wins = [t["profit_pct"] for t in trades if t.get("profit_pct", 0) > 0]
            losses = [abs(t["profit_pct"]) for t in trades if t.get("profit_pct", 0) < 0]
            
            # Calculate metrics
            win_rate = len(wins) / len(trades) if trades else 0
            avg_win = np.mean(wins) if wins else self.default_avg_win
            avg_loss = np.mean(losses) if losses else self.default_avg_loss
            
            kelly_pct = self.calculate_kelly_percentage(win_rate, avg_win, avg_loss)
            
            return {
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "kelly_percentage": kelly_pct,
                "total_trades": len(trades),
                "winning_trades": len(wins),
                "losing_trades": len(losses)
            }
            
        except Exception as e:
            logger.error(f"Error updating performance data: {e}")
            return {
                "win_rate": self.default_win_rate,
                "avg_win": self.default_avg_win,
                "avg_loss": self.default_avg_loss,
                "kelly_percentage": 0.02,
                "total_trades": 0
            }
    
    def calculate_position_size(self, balance: float, kelly_pct: float, confidence_score: float) -> Dict[str, float]:
        """
        Calculate optimal position size berdasarkan:
        - Kelly Criterion percentage
        - Current confidence score (0-100)
        - Account balance
        """
        try:
            # Base Kelly percentage
            base_kelly = kelly_pct
            
            # Adjust based on confidence score
            confidence_multiplier = confidence_score / 100
            
            # Conservative adjustment untuk small accounts
            adjusted_kelly = base_kelly * confidence_multiplier
            
            # Safety limits untuk $5 accounts
            min_risk = 0.005  # 0.5% minimum
            max_risk = 0.05   # 5% maximum (very conservative)
            
            final_risk_pct = max(min_risk, min(adjusted_kelly, max_risk))
            
            # Calculate actual position size
            risk_amount = balance * final_risk_pct
            # Adjust risk to account for total fees so that risk+fee <= risk_amount
            fee_buffer = balance * FEE_RATE
            risk_amount = max(risk_amount - fee_buffer, 0)
            
            return {
                "risk_percentage": final_risk_pct,
                "risk_amount": risk_amount,
                "kelly_suggested": base_kelly,
                "confidence_multiplier": confidence_multiplier,
                "max_leverage": min(3, 1 + confidence_multiplier * 2)  # 1x to 3x
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {
                "risk_percentage": 0.02,
                "risk_amount": balance * 0.02,
                "kelly_suggested": 0.02,
                "confidence_multiplier": 0.6,
                "max_leverage": 2
            }
    
    def get_portfolio_heat(self, active_positions: List[Dict]) -> Dict[str, float]:
        """Calculate portfolio heat (total risk across positions)"""
        try:
            if not active_positions:
                return {
                    "total_heat": 0.0,
                    "position_count": 0,
                    "max_heat_reached": False
                }
            
            total_risk = 0.0
            for position in active_positions:
                position_risk = abs(float(position.get('positionAmt', 0))) * float(position.get('markPrice', 0))
                total_risk += position_risk
            
            # Portfolio heat thresholds
            max_heat = 0.10  # 10% max total portfolio risk
            current_heat_pct = total_risk / 100  # Simplified calculation
            
            return {
                "total_heat": current_heat_pct,
                "position_count": len(active_positions),
                "max_heat_reached": current_heat_pct > max_heat
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio heat: {e}")
            return {
                "total_heat": 0.0,
                "position_count": 0,
                "max_heat_reached": False
            }