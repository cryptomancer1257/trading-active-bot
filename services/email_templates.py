"""
Email Templates for Bot Marketplace
Provides templates for different types of email notifications
"""

from typing import Dict, Any, Optional
from datetime import datetime

class EmailTemplates:
    """Email templates for bot notifications"""
    
    @staticmethod
    def get_hold_signal_template(
        trading_pair: str,
        current_price: float,
        action: str,
        reason: str,
        confidence: Any,
        timeframe: str,
        is_testnet: bool,
        balance_info: str = ""
    ) -> tuple[str, str]:
        """
        Get hold signal email template
        
        Returns:
            tuple: (subject, body)
        """
        subject = f"🟡 Bot Signal - {action} - {trading_pair}"
        
        body = f"""Your bot analysis complete:

📈 Signal Information:
   • Symbol: {trading_pair}
   • Action: {action}
   • Reason: {reason}
   • Confidence: {confidence or 'N/A'}
   • Timeframe: {timeframe}
   • Current Price: ${current_price:.2f}

📝 Signal Reason: {reason or 'Bot signal'}
🔄 Mode: {'🧪 TESTNET' if is_testnet else '🚀 LIVE TRADING'}
⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

        if balance_info:
            body += f"\n{balance_info}"
            
        return subject, body
    
    @staticmethod
    def get_successful_trade_template(
        bot_name: str,
        trading_pair: str,
        action: str,
        reason: str,
        confidence: Any,
        timeframe: str,
        is_testnet: bool,
        trade_details: Dict[str, Any],
        balance_info: str = ""
    ) -> tuple[str, str]:
        """
        Get successful trade execution email template
        
        Returns:
            tuple: (subject, body)
        """
        subject = f"✅ Bot Signal - Trade Executed - {bot_name}"
        
        # Determine allocation text based on action
        base_asset = trade_details.get('base_asset', '')
        if action == 'BUY':
            allocation_text = 'USDT balance'
        else:
            allocation_text = f'{base_asset} holdings'
        
        trade_info = f"""💰 Trade Details:
   • Order ID: {trade_details.get('order_id', 'N/A')}
   • Quantity: {trade_details.get('quantity', 'N/A')} {base_asset}
   • Price: ${trade_details.get('current_price', 0):.2f} per {base_asset}
   • Total Value: ${trade_details.get('usdt_value', 0):.2f} USDT
   • Allocation: {trade_details.get('percentage_used', 0):.1f}% of {allocation_text}"""
        
        body = f"""Your bot executed a {action} order:

📈 Signal Information:
   • Symbol: {trading_pair}
   • Action: {action}
   • Reason: {reason}
   • Confidence: {confidence or 'N/A'}
   • Timeframe: {timeframe}

{trade_info}

📝 Signal Reason: {reason or 'Bot signal'}
🔄 Mode: {'🧪 TESTNET' if is_testnet else '🚀 LIVE TRADING'}
⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

        if balance_info:
            body += f"\n{balance_info}"
            
        return subject, body
    
    @staticmethod
    def get_failed_trade_template(
        bot_name: str,
        trading_pair: str,
        action: str,
        reason: str,
        confidence: Any,
        timeframe: str,
        is_testnet: bool,
        current_price: float,
        error_msg: str,
        balance_info: str = ""
    ) -> tuple[str, str]:
        """
        Get failed trade execution email template
        
        Returns:
            tuple: (subject, body)
        """
        subject = f"⚠️ Bot Signal - Trade Failed - {bot_name}"
        
        body = f"""Your bot generated a {action} signal but trade execution failed:

📈 Signal Information:
   • Symbol: {trading_pair}
   • Action: {action}
   • Reason: {reason}
   • Confidence: {confidence or 'N/A'}
   • Timeframe: {timeframe}

❌ Trade Execution Error:
   • Error: {error_msg}
   • Price: ${current_price:.2f}

📝 Signal Reason: {reason or 'Bot signal'}
🔄 Mode: {'🧪 TESTNET' if is_testnet else '🚀 LIVE TRADING'}
⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

        if balance_info:
            body += f"\n{balance_info}"
            
        return subject, body
    
    @staticmethod
    def get_balance_info_template(
        base_asset: str,
        quote_asset: str,
        base_balance: Any,
        quote_balance: Any,
        current_price: float,
        is_testnet: bool,
        is_demo: bool = False
    ) -> str:
        """
        Get account balance information template
        
        Returns:
            str: Balance info text
        """
        try:
            base_total = float(base_balance.free) + float(base_balance.locked)
            quote_total = float(quote_balance.free) + float(quote_balance.locked)
            
            # Calculate portfolio value in USDT
            portfolio_value = quote_total + (base_total * current_price)
            
            mode_label = "TESTNET" if is_testnet else "LIVE"
            
            if is_demo:
                balance_info = f"""💼 Account Balance ({mode_label} - DEMO):
   • {base_asset}: 0.100000 (Free: 0.100000, Locked: 0.000000)
   • {quote_asset}: 10000.00 (Free: 10000.00, Locked: 0.00)
   • Portfolio Value: ~${10000 + (0.1 * current_price):.2f} USDT
   ⚠️ Demo balance - Configure exchange credentials for real data"""
            else:
                balance_info = f"""💼 Account Balance ({mode_label}):
   • {base_asset}: {base_total:.6f} (Free: {base_balance.free}, Locked: {base_balance.locked})
   • {quote_asset}: {quote_total:.2f} (Free: {quote_balance.free}, Locked: {quote_balance.locked})
   • Portfolio Value: ~${portfolio_value:.2f} USDT"""
            
            return balance_info
            
        except Exception as e:
            return f"""💼 Account Balance ({'TESTNET' if is_testnet else 'LIVE'}):
   ⚠️ Unable to fetch balance information: {str(e)[:100]}"""

    @staticmethod
    def get_demo_balance_template(
        base_asset: str,
        quote_asset: str,
        current_price: float,
        is_testnet: bool
    ) -> str:
        """
        Get demo balance template
        
        Returns:
            str: Demo balance info text
        """
        mode_label = "TESTNET" if is_testnet else "LIVE"
        return f"""💼 Account Balance ({mode_label} - DEMO):
   • {base_asset}: 0.100000 (Free: 0.100000, Locked: 0.000000)
   • {quote_asset}: 10000.00 (Free: 10000.00, Locked: 0.00)
   • Portfolio Value: ~${10000 + (0.1 * current_price):.2f} USDT
   ⚠️ Demo balance - Configure exchange credentials for real data"""

def create_email_content(
    action: str,
    bot_name: str,
    trading_pair: str,
    current_price: float,
    reason: str,
    confidence: Any,
    timeframe: str,
    is_testnet: bool,
    trade_details: Optional[Dict[str, Any]] = None,
    balance_info: str = ""
) -> tuple[str, str]:
    """
    Create email content based on action type
    
    Returns:
        tuple: (subject, body)
    """
    if action == "HOLD":
        return EmailTemplates.get_hold_signal_template(
            trading_pair=trading_pair,
            current_price=current_price,
            action=action,
            reason=reason,
            confidence=confidence,
            timeframe=timeframe,
            is_testnet=is_testnet,
            balance_info=balance_info
        )
    elif action in ["BUY", "SELL"]:
        if trade_details and trade_details.get('success', False):
            return EmailTemplates.get_successful_trade_template(
                bot_name=bot_name,
                trading_pair=trading_pair,
                action=action,
                reason=reason,
                confidence=confidence,
                timeframe=timeframe,
                is_testnet=is_testnet,
                trade_details=trade_details,
                balance_info=balance_info
            )
        else:
            error_msg = trade_details.get('error', 'Unknown error') if trade_details else 'Trade execution failed'
            return EmailTemplates.get_failed_trade_template(
                bot_name=bot_name,
                trading_pair=trading_pair,
                action=action,
                reason=reason,
                confidence=confidence,
                timeframe=timeframe,
                is_testnet=is_testnet,
                current_price=current_price,
                error_msg=error_msg,
                balance_info=balance_info
            )
    else:
        # Default template for unknown actions
        subject = f"📊 Bot Signal - {action} - {bot_name}"
        body = f"""Your bot analysis complete:

📈 Signal Information:
   • Symbol: {trading_pair}
   • Action: {action}
   • Reason: {reason}
   • Confidence: {confidence or 'N/A'}
   • Timeframe: {timeframe}
   • Current Price: ${current_price:.2f}

📝 Signal Reason: {reason or 'Bot signal'}
🔄 Mode: {'🧪 TESTNET' if is_testnet else '🚀 LIVE TRADING'}
⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

        if balance_info:
            body += f"\n{balance_info}"
            
        return subject, body

def send_combined_notification(
    user_email: str,
    bot_name: str,
    action: str,
    details: Dict[str, Any]
) -> bool:
    """
    Send combined signal and trade execution notification
    
    Returns:
        bool: True if sent successfully
    """
    try:
        from services.sendgrid_email_service import SendGridEmailService
        from services.gmail_smtp_service import GmailSMTPService
        
        # Create email content
        subject, body = create_email_content(
            action=action,
            bot_name=bot_name,
            trading_pair=details.get('trading_pair', 'Unknown'),
            current_price=details.get('current_price', 0),
            reason=details.get('reason', 'Bot signal'),
            confidence=details.get('confidence', 'N/A'),
            timeframe=details.get('timeframe', 'Unknown'),
            is_testnet=details.get('is_testnet', True),
            trade_details=details.get('trade_details'),
            balance_info=details.get('balance_info', '')
        )
        
        # Try SendGrid first
        try:
            sendgrid_service = SendGridEmailService()
            success = sendgrid_service.send_email(user_email, subject, body)
            if success:
                return True
        except Exception as e:
            print(f"SendGrid failed: {e}")
        
        # Fallback to Gmail SMTP
        try:
            gmail_service = GmailSMTPService()
            success = gmail_service.send_email(user_email, subject, body)
            if success:
                return True
        except Exception as e:
            print(f"Gmail SMTP failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"Error sending combined notification: {e}")
        return False 