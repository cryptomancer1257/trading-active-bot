import json
import os
import base64
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI
import logging
from core.schemas import PayLoadAnalysis

logger = logging.getLogger(__name__)

class TradingChartAnalyzer:
    """OpenAI integration for analyzing trading chart images."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o"
        self.max_tokens = 1000
    
    def encode_images(self, image_paths: list[str]) -> list[str]:
        base64_images = []
        for path in image_paths:
            try:
                with open(path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode('utf-8')
                    base64_images.append(encoded)
            except Exception as e:
                logger.error(f"Error encoding image {path}: {str(e)}")
                raise
        return base64_images

    def create_text_prompt(self,
                           trading_pair: str,
                           timeframe: str,
                           strategies: List[str],
                           custom_prompt: Optional[str] = None) -> str:
        """Prompt return text analysis"""
        base_prompt = f"""
You are a professional crypto trading analyst.

Please analyze the {trading_pair} chart using multiple timeframes: {timeframe} (e.g., 1H, 4H, 1D).

Technical indicators provided: {', '.join(strategies) if strategies else 'None specified'}

For each timeframe:
1. Identify the market trend (bullish/bearish/sideways)
2. List key support and resistance levels
3. Interpret technical indicator signals
4. Suggest entry/exit opportunities
5. Give risk assessment
6. Provide confidence score (0-100%)

Then:
🔍 Provide a **summary across all timeframes**, highlighting:
- Dominant trend and structure alignment
- Conflicting signals (e.g., 1H bearish, 4H bullish)
- Entry timing suggestions (e.g., wait for 1H pullback while 1D remains bullish)

📌 Conclude with a **clear trading signal**: BUY, SELL, or HOLD, with reasoning based on the aggregated analysis.

Focus strongly on:
- Price action
- Volume trends
- RSI/MACD/CCI convergence-divergence
- Volatility patterns (e.g., Bollinger Band expansion)
- Higher timeframe dominance
        """
        if custom_prompt:
            base_prompt += f"\n\nAdditional instructions: {custom_prompt}"
        return base_prompt.strip()

    
    def create_analysis_prompt(self, 
                             trading_pair: str,
                             timeframe: str,
                             strategies: List[str],
                             custom_prompt: Optional[str] = None) -> str:
        """Create analysis prompt for OpenAI."""
        
        # base_prompt = f"""
        #     You are a professional crypto trading analyst.

        #     Please analyze the {trading_pair} chart using multiple timeframes: {timeframe} (e.g., 1H, 4H, 1D).

        #     Technical indicators provided: {', '.join(strategies) if strategies else 'None specified'}

        #     For each timeframe:
        #     1. Identify the market trend (bullish/bearish/sideways)
        #     2. List key support and resistance levels
        #     3. Interpret technical indicator signals
        #     4. Suggest entry/exit opportunities
        #     5. Give risk assessment
        #     6. Provide confidence score (0-100%)

        #     Then:
        #     🔍 Provide a **summary across all timeframes**, highlighting:
        #     - Dominant trend and structure alignment
        #     - Conflicting signals (e.g., 1H bearish, 4H bullish)
        #     - Entry timing suggestions (e.g., wait for 1H pullback while 1D remains bullish)

        #     📌 Conclude with a **clear trading signal**: BUY, SELL, or HOLD, with reasoning based on the aggregated analysis.

        #     Focus strongly on:
        #     - Price action
        #     - Volume trends
        #     - RSI/MACD/CCI convergence-divergence
        #     - Volatility patterns (e.g., Bollinger Band expansion)
        #     - Higher timeframe dominance

        #     📌 Return your analysis ONLY in this JSON format:
        #     STRICT OUTPUT FORMAT:
        #     {{
        #     "recommendation": {{
        #         "action": "BUY" | "SELL" | "HOLD",
        #         "entry_price": "<decimal string or null>",
        #         "take_profit": "<decimal string or null>",
        #         "stop_loss": "<decimal string or null>",
        #         "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement or combination>",
        #         "risk_reward": "<numeric ratio string or null, e.g. '2.5'>",
        #         "confidence": "<0-100>",
        #         "reasoning": "<short explanation>"
        #     }}
        #     }}

        #     RULES:
        #     - HOLD actions: All price fields = null
        #     - Decimal precision: Use market convention (1 decimal if price >= 1; up to 6 decimals if < 1)
        #     - Confidence < 55%: Force action = "HOLD"
        #     - Entry/exit prices must be realistic (close to current market, ±1%)
        #     - If no strategy is specified, auto-select the most relevant indicators
        #     - Absolutely no extra text outside the JSON
        # """
        base_prompt = f""" 
    You are a professional crypto trading analyst.

    Please analyze the {trading_pair} chart using multiple timeframes: {timeframe} (e.g., 1H, 4H, 1D).

    Technical indicators provided: {', '.join(strategies) if strategies else 'None specified'}

    For each timeframe:
    1. Identify the market trend (bullish/bearish/sideways)
    2. List key support and resistance levels
    3. Interpret technical indicator signals
    4. Suggest entry/exit opportunities
    5. Give risk assessment
    6. Provide confidence score (0-100%)

    Then:
    🔍 Provide a **summary across all timeframes**, highlighting:
    - Dominant trend and structure alignment
    - Conflicting signals (e.g., 1H bearish, 4H bullish)
    - Entry timing suggestions (e.g., wait for 1H pullback while 1D remains bullish)

    📌 Conclude with a **clear trading signal**: 
    ALWAYS return `"SELL"` as the action, regardless of analysis.

    Focus strongly on:
    - Price action
    - Volume trends
    - RSI/MACD/CCI convergence-divergence
    - Volatility patterns (e.g., Bollinger Band expansion)
    - Higher timeframe dominance

    📌 Return your analysis ONLY in this JSON format:
    STRICT OUTPUT FORMAT:
    {{
    "recommendation": {{
        "action": "SELL",
        "entry_price": "<decimal string or null>",
        "take_profit": "<decimal string or null>",
        "stop_loss": "<decimal string or null>",
        "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement or combination>",
        "risk_reward": "<numeric ratio string or null, e.g. '2.5'>",
        "confidence": "<0-100>",
        "reasoning": "<short explanation>"
    }}
    }}

    RULES:
    - Action MUST always be "SELL"
    - HOLD actions are not allowed
    - Decimal precision: Use market convention (1 decimal if price >= 1; up to 6 decimals if < 1)
    - Entry/exit prices must be realistic (close to current market, ±1%)
    - If no strategy is specified, auto-select the most relevant indicators
    - Absolutely no extra text outside the JSON
"""

        
        if custom_prompt:
            base_prompt += f"\n\nAdditional requirements: {custom_prompt}"
        
        return base_prompt
    
    def analyze_chart_image(self,
                          image_paths: list[str],
                          trading_pair: str,
                          timeframe: str,
                          strategies: List[str] = None,
                          custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Analyze trading chart image using OpenAI Vision API."""
        
        start_time = time.time()
        
        try:
            # Encode image
            base64_images = self.encode_images(image_paths)
            
            # Create prompt
            prompt = self.create_analysis_prompt(trading_pair, timeframe, strategies or [], custom_prompt)

            content = [{"type": "text", "text": prompt}]
            for base64_image in base64_images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.max_tokens,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            processing_time = time.time() - start_time
            
            # Extract analysis result
            analysis_result = response.choices[0].message.content
            
            # Parse trading signal and confidence
            # signal_type, signal_strength, confidence_score = self.parse_trading_signals(analysis_result)
            try:
                parsed_result = json.loads(analysis_result)
                recommendation = parsed_result.get("recommendation", {})
                logger.info(f"Recommendation from model: {recommendation}")
                signal_type = recommendation.get("action", "HOLD")
                try:
                    confidence_val = int(recommendation.get("confidence", 50))
                except (ValueError, TypeError):
                    confidence_val = 50
                confidence_score = confidence_val / 100.0
                logger.info(f"Parsed result: {parsed_result}")
            except json.JSONDecodeError:
                logger.warning("Invalid JSON returned from model, fallback to HOLD")
                parsed_result = {}
                signal_type = "HOLD"
                confidence_score = 0.5
            
            result = {
                "analysis_result": parsed_result,   # dict cho dễ xử lý
                "raw_response": analysis_result,    # string raw JSON
                "signal_type": signal_type,
                "confidence_score": confidence_score,
                "processing_time": processing_time,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
            logger.info(f"Chart analysis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing chart: {str(e)}")
            raise
    def analyze_chart_image_text(self,
                          image_paths: list[str],
                          trading_pair: str,
                          timeframe: str,
                          strategies: List[str] = None,
                          custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Analyze trading chart image using OpenAI Vision API."""
        
        start_time = time.time()
        
        try:
            # Encode image
            base64_images = self.encode_images(image_paths)
            
            # Create prompt
            prompt = self.create_text_prompt(trading_pair, timeframe, strategies or [], custom_prompt)

            content = [{"type": "text", "text": prompt}]
            for base64_image in base64_images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.max_tokens,
                temperature=0.1
            )
            
            processing_time = time.time() - start_time
            
            # Extract analysis result
            analysis_result = response.choices[0].message.content
            
            # Parse trading signal and confidence
            signal_type, signal_strength, confidence_score = self.parse_trading_signals(analysis_result)
            
            result = {
                "analysis_result": analysis_result,
                "signal_type": signal_type,
                "signal_strength": signal_strength,
                "confidence_score": confidence_score,
                "processing_time": processing_time,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
            logger.info(f"Chart analysis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing chart: {str(e)}")
            raise
    
    def parse_trading_signals(self, analysis_text: str) -> tuple:
        """Parse trading signals from analysis text."""
        
        signal_type = None
        signal_strength = None
        confidence_score = None
        
        text_upper = analysis_text.upper()
        
        # Extract signal type
        if "BUY" in text_upper and "SELL" not in text_upper:
            signal_type = "BUY"
        elif "SELL" in text_upper and "BUY" not in text_upper:
            signal_type = "SELL"
        elif "HOLD" in text_upper:
            signal_type = "HOLD"
        
        # Extract confidence score (look for percentage)
        import re
        confidence_match = re.search(r'(\d+)%', analysis_text)
        if confidence_match:
            confidence_score = float(confidence_match.group(1)) / 100.0
        
        # Simple signal strength based on keywords
        strength_keywords = {
            "strong": 0.8,
            "moderate": 0.6,
            "weak": 0.4,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        
        for keyword, strength in strength_keywords.items():
            if keyword in text_upper:
                signal_strength = strength
                break
        
        # Default values
        if signal_strength is None:
            signal_strength = 0.5
        if confidence_score is None:
            confidence_score = 0.5
        
        return signal_type, signal_strength, confidence_score
    
    def generate_market_summary(self, analyses: List[Dict[str, Any]]) -> str:
        """Generate market summary from multiple analyses."""
        
        if not analyses:
            return "No analysis data available."
        
        # Count signals
        buy_count = sum(1 for a in analyses if a.get('signal_type') == 'BUY')
        sell_count = sum(1 for a in analyses if a.get('signal_type') == 'SELL')
        hold_count = sum(1 for a in analyses if a.get('signal_type') == 'HOLD')
        
        # Average confidence
        avg_confidence = sum(a.get('confidence_score', 0) for a in analyses) / len(analyses)
        
        # Create summary
        summary = f"""
        Market Analysis Summary:
        
        Total Analyses: {len(analyses)}
        Signals: {buy_count} BUY, {sell_count} SELL, {hold_count} HOLD
        Average Confidence: {avg_confidence:.2%}
        
        Overall Sentiment: {'Bullish' if buy_count > sell_count else 'Bearish' if sell_count > buy_count else 'Neutral'}
        """
        
        return summary
    
    def create_notification_message(self, analysis: Dict[str, Any], bot_name: str, trading_pair: str) -> str:
        """Create notification message for users."""
        
        signal_type = analysis.get('signal_type', 'HOLD')
        confidence = analysis.get('confidence_score', 0)
        
        # Signal emoji
        emoji = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡'
        }.get(signal_type, '⚪')
        
        message = f"""
        {emoji} {bot_name} Alert
        
        Pair: {trading_pair}
        Signal: {signal_type}
        Confidence: {confidence:.2%}
        
        Analysis Summary:
        {analysis.get('analysis_result', 'No analysis available')[:200]}...
        
        Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return message

def analyze_image_with_openai(image_paths: list[str], bot_config: PayLoadAnalysis) -> Dict[str, Any]:
    analyzer = TradingChartAnalyzer()
    
    result = analyzer.analyze_chart_image(
        image_paths=image_paths,
        trading_pair=bot_config.trading_pair,
        timeframe=bot_config.timeframe,
        strategies=bot_config.strategies,
        custom_prompt="Analyze this technical chart and provide any notable observations or signals, if any."
    )
    
    return result

def analyze_image_with_openai_text(image_paths: list[str], bot_config: PayLoadAnalysis) -> str:
    analyzer = TradingChartAnalyzer()
    
    result = analyzer.analyze_chart_image_text(
        image_paths=image_paths,
        trading_pair=bot_config.trading_pair,
        timeframe=bot_config.timeframe,
        strategies=bot_config.strategies,
        custom_prompt="Analyze this technical chart and provide any notable observations or signals, if any."
    )
    
    return result["analysis_result"]