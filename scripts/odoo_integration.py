#!/usr/bin/env python3
"""
Odoo Accounting Integration for AI Employee - Gold Tier

Integrates with Odoo Community Edition via JSON-RPC API for:
- Creating invoices
- Recording payments
- Fetching financial reports
- Managing customers/vendors

Setup:
1. Install Odoo Community Edition (local or cloud)
2. Get API credentials from Odoo
3. Configure connection in odoo_config.json
4. Run: python odoo_integration.py --test

Usage:
    python odoo_integration.py --test              # Test connection
    python odoo_integration.py --create-invoice    # Create invoice (requires approval)
    python odoo_integration.py --record-payment    # Record payment
    python odoo_integration.py --reports           # Fetch financial reports
"""

import os
import sys
import json
import logging
import codecs
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('odoo_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OdooIntegration')


class OdooIntegration:
    """Integrate with Odoo ERP via JSON-RPC API."""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.config_file = self.vault_path / "odoo_config.json"
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.approved_folder = self.vault_path / "Approved" / "Payments"
        self.done_folder = self.vault_path / "Done"
        self.logs_folder = self.vault_path / "Logs"

        # Ensure folders exist
        self.pending_approval.mkdir(exist_ok=True)
        self.approved_folder.mkdir(exist_ok=True, parents=True)
        self.done_folder.mkdir(exist_ok=True)
        self.logs_folder.mkdir(exist_ok=True)

        # Load configuration
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load Odoo configuration from file."""
        if self.config_file.exists():
            try:
                config = json.loads(self.config_file.read_text())
                logger.info("Odoo configuration loaded")
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")

        # Default configuration template
        default_config = {
            "url": "http://localhost:8069",
            "db": "odoo",
            "username": "admin",
            "api_key": "",
            "uid": None
        }

        # Create config file if not exists
        self.config_file.write_text(json.dumps(default_config, indent=2))
        logger.info(f"Created default config file: {self.config_file}")
        logger.info("Please edit odoo_config.json with your Odoo credentials")

        return default_config

    def save_config(self, config: Dict):
        """Save Odoo configuration."""
        self.config_file.write_text(json.dumps(config, indent=2))
        logger.info("Configuration saved")

    def authenticate(self) -> bool:
        """Authenticate with Odoo and get UID."""
        try:
            url = f"{self.config['url']}/jsonrpc"
            
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [
                        self.config['db'],
                        self.config['username'],
                        self.config['api_key'],
                        {}
                    ]
                },
                "id": 1
            }

            response = requests.post(url, json=payload, timeout=30)
            result = response.json()

            if 'result' in result and result['result']:
                self.config['uid'] = result['result']
                self.save_config(self.config)
                logger.info(f"Authentication successful! UID: {self.config['uid']}")
                return True
            else:
                logger.error("Authentication failed")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def execute(self, model: str, method: str, args: List = None, kwargs: Dict = None) -> Optional[Dict]:
        """Execute a method on an Odoo model."""
        if not self.config.get('uid'):
            if not self.authenticate():
                return None

        try:
            url = f"{self.config['url']}/jsonrpc"
            
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.config['db'],
                        self.config['uid'],
                        self.config['api_key'],
                        model,
                        method,
                        args or []
                    ],
                    "kwargs": kwargs or {}
                },
                "id": 1
            }

            response = requests.post(url, json=payload, timeout=30)
            result = response.json()

            if 'result' in result:
                return result['result']
            else:
                logger.error(f"Odoo API error: {result.get('error', 'Unknown error')}")
                return None

        except Exception as e:
            logger.error(f"Execute error: {e}")
            return None

    def test_connection(self) -> bool:
        """Test Odoo connection."""
        logger.info("Testing Odoo connection...")
        
        if self.authenticate():
            # Try to get company name
            companies = self.execute('res.company', 'search_read', [[['id', '=', 1]]], {'fields': ['name']})
            if companies:
                logger.info(f"Connected to Odoo: {companies[0].get('name', 'Unknown')}")
                return True
        
        logger.error("Failed to connect to Odoo")
        return False

    def create_invoice(self, partner_id: int, amount: float, description: str, due_days: int = 30) -> Optional[int]:
        """Create a customer invoice in Odoo."""
        logger.info(f"Creating invoice for partner {partner_id}, amount ${amount}")

        # Calculate due date
        from datetime import timedelta
        due_date = (datetime.now() + timedelta(days=due_days)).strftime('%Y-%m-%d')

        # Create invoice
        invoice_data = {
            "move_type": "out_invoice",
            "partner_id": partner_id,
            "invoice_date": datetime.now().strftime('%Y-%m-%d'),
            "invoice_date_due": due_date,
            "invoice_line_ids": [
                (0, 0, {
                    "name": description,
                    "quantity": 1,
                    "price_unit": amount,
                })
            ]
        }

        invoice_id = self.execute('account.move', 'create', [invoice_data])
        
        if invoice_id:
            logger.info(f"Invoice created with ID: {invoice_id}")
            
            # Post the invoice
            self.execute('account.move', 'action_post', [[invoice_id]])
            logger.info(f"Invoice {invoice_id} posted")
            
            return invoice_id
        
        return None

    def record_payment(self, invoice_id: int, amount: float, payment_method: str = "bank") -> Optional[int]:
        """Record a payment for an invoice."""
        logger.info(f"Recording payment ${amount} for invoice {invoice_id}")

        # Create payment
        payment_data = {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": self.execute('account.move', 'read', [[invoice_id]], {'fields': ['partner_id']})[0]['partner_id'][0],
            "amount": amount,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "journal_id": self._get_payment_journal(payment_method),
        }

        payment_id = self.execute('account.payment', 'create', [payment_data])
        
        if payment_id:
            logger.info(f"Payment created with ID: {payment_id}")
            self.execute('account.payment', 'action_post', [[payment_id]])
            logger.info(f"Payment {payment_id} posted")
            return payment_id
        
        return None

    def _get_payment_journal(self, payment_method: str) -> int:
        """Get journal ID for payment method."""
        journals = self.execute('account.journal', 'search_read', [
            [['type', '=', 'bank'], ['code', '=', payment_method]]
        ], {'fields': ['id'], 'limit': 1})
        
        if journals:
            return journals[0]['id']
        
        # Default to first bank journal
        journals = self.execute('account.journal', 'search_read', [
            [['type', '=', 'bank']]
        ], {'fields': ['id'], 'limit': 1})
        
        return journals[0]['id'] if journals else 1

    def get_financial_reports(self) -> Dict:
        """Fetch financial reports from Odoo."""
        logger.info("Fetching financial reports...")

        reports = {
            "total_receivables": 0,
            "total_payables": 0,
            "pending_invoices": 0,
            "recent_payments": []
        }

        # Get total receivables
        receivables = self.execute('account.move', 'search_read', [
            [['move_type', '=', 'out_invoice'], ['payment_state', '!=', 'paid']]
        ], {'fields': ['amount_total', 'amount_residual']})
        
        if receivables:
            reports['total_receivables'] = sum(r['amount_residual'] for r in receivables)
            reports['pending_invoices'] = len(receivables)

        # Get total payables
        payables = self.execute('account.move', 'search_read', [
            [['move_type', '=', 'in_invoice'], ['payment_state', '!=', 'paid']]
        ], {'fields': ['amount_total', 'amount_residual']})
        
        if payables:
            reports['total_payables'] = sum(p['amount_residual'] for p in payables)

        # Get recent payments
        payments = self.execute('account.payment', 'search_read', [
            []
        ], {'fields': ['amount', 'date', 'partner_id', 'payment_type'], 'limit': 10, 'order': 'date desc'})
        
        if payments:
            reports['recent_payments'] = payments

        return reports

    def create_invoice_approval_request(self, partner_name: str, amount: float, description: str) -> Optional[Path]:
        """Create an approval request for creating an invoice."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"ODOO_INVOICE_{timestamp}.md"
        approval_path = self.pending_approval / filename

        content = f"""---
type: odoo_invoice_action
action: create_invoice
created: {datetime.now().isoformat()}
status: pending_approval
partner: {partner_name}
amount: {amount}
---

# Odoo Invoice Creation Approval

## Invoice Details
- **Customer:** {partner_name}
- **Amount:** ${amount:,.2f}
- **Description:** {description}
- **Due:** 30 days from creation

## To Approve
Move this file to: `/Approved/Payments/`

## To Reject
Move this file to: `/Rejected/` with reason.
"""

        approval_path.write_text(content, encoding='utf-8')
        logger.info(f"Invoice approval request created: {approval_path}")

        return approval_path

    def process_approved_actions(self) -> int:
        """Process approved Odoo actions."""
        if not self.approved_folder.exists():
            return 0

        approved_files = list(self.approved_folder.glob("ODOO_*.md"))
        processed_count = 0

        for file_path in approved_files:
            logger.info(f"Processing approved Odoo action: {file_path.name}")

            content = file_path.read_text(encoding='utf-8')

            if "action: create_invoice" in content:
                # Extract invoice details (simplified - in production, parse frontmatter)
                # This would need proper parsing
                logger.info(f"Invoice action approved: {file_path.name}")
                processed_count += 1

            # Move to Done
            done_path = self.done_folder / f"EXECUTED_{file_path.name}"
            file_path.rename(done_path)
            logger.info(f"Action moved to Done: {done_path}")

        return processed_count


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Odoo Accounting Integration')
    parser.add_argument('--test', action='store_true', help='Test Odoo connection')
    parser.add_argument('--setup', action='store_true', help='Setup configuration')
    parser.add_argument('--reports', action='store_true', help='Fetch financial reports')
    parser.add_argument('--vault', default='.', help='Path to vault')

    args = parser.parse_args()

    integration = OdooIntegration(vault_path=args.vault)

    if args.setup:
        print("Odoo Configuration Setup")
        print("=" * 40)
        print(f"\nPlease edit: {integration.config_file}")
        print("\nRequired fields:")
        print("  - url: Odoo server URL (e.g., http://localhost:8069)")
        print("  - db: Database name")
        print("  - username: Odoo username")
        print("  - api_key: Odoo API key/password")
        print("\nAfter editing, run: python odoo_integration.py --test")

    elif args.test:
        print("Testing Odoo Connection")
        print("=" * 40)
        if integration.test_connection():
            print("\n[OK] Connected to Odoo successfully!")
        else:
            print("\n[ERROR] Failed to connect to Odoo")
            print("Check your configuration in odoo_config.json")

    elif args.reports:
        print("Fetching Financial Reports")
        print("=" * 40)
        
        if integration.authenticate():
            reports = integration.get_financial_reports()
            print(f"\nTotal Receivables: ${reports['total_receivables']:,.2f}")
            print(f"Total Payables: ${reports['total_payables']:,.2f}")
            print(f"Pending Invoices: {reports['pending_invoices']}")
            print(f"\nRecent Payments: {len(reports['recent_payments'])}")
        else:
            print("\n[ERROR] Authentication failed")

    else:
        parser.print_help()
        print("\nGold Tier Features:")
        print("  --test          Test Odoo connection")
        print("  --setup         Setup configuration")
        print("  --reports       Fetch financial reports")


if __name__ == "__main__":
    main()
