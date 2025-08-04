from . import db
from datetime import datetime

class DeviceInfo(db.Model):
    __tablename__ = 'device_info'  # Add this line
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False)
    certificate_path = db.Column(db.String(255), nullable=False)
    key_path = db.Column(db.String(255), nullable=False)
    model_name = db.Column(db.String(100))
    model_version = db.Column(db.String(20))


class FiscalDay(db.Model):
    __tablename__ = 'fiscal_day'  # Add this line
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)  # Store the actual device_id string
    fiscal_day_open = db.Column(db.String(30))
    is_open = db.Column(db.Boolean, default=True)
    fiscal_status = db.Column(db.String(30))
    fiscal_day_no = db.Column(db.Integer, nullable=True)


class DeviceConfiguration(db.Model):
    __tablename__ = 'device_configuration'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('device_info.device_id'), nullable=False)
    
    # Tax Payer Information
    tax_payer_name = db.Column(db.String(255))
    tax_payer_tin = db.Column(db.String(50))
    vat_number = db.Column(db.String(50))
    
    # Device Information
    device_serial_no = db.Column(db.String(100))
    device_branch_name = db.Column(db.String(255))
    device_operating_mode = db.Column(db.String(50))
    tax_payer_day_max_hrs = db.Column(db.Integer)
    
    # QR URL
    qr_url = db.Column(db.String(255))
    
    # Operation ID
    operation_id = db.Column(db.String(100))
    
    # Address Information (stored as JSON)
    device_branch_address_province = db.Column(db.String(100))
    device_branch_address_city = db.Column(db.String(100))
    device_branch_address_street = db.Column(db.String(255))
    device_branch_address_house_no = db.Column(db.String(50))
    
    # Contact Information
    device_branch_contacts_phone_no = db.Column(db.String(50))
    device_branch_contacts_email = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceConfig(db.Model):
    __tablename__ = 'device_config'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('device_info.device_id'), nullable=False)
    config = db.Column(db.Text, nullable=False)  # JSON string containing device configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Invoice(db.Model):
    __tablename__ = 'invoice'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.String(100), unique=True, nullable=False)
    device_id = db.Column(db.String(50), nullable=False)
    receipt_currency = db.Column(db.String(10), nullable=False)
    money_type = db.Column(db.String(20), nullable=False)
    receipt_type = db.Column(db.String(50), nullable=False)
    receipt_total = db.Column(db.Float, nullable=False)
    
    # ZIMRA Response Data
    zimra_receipt_number = db.Column(db.String(100))
    operation_id = db.Column(db.String(100))
    qr_code_string = db.Column(db.Text)
    verification_number = db.Column(db.String(100))
    hash_string = db.Column(db.String(255))
    is_fiscalized = db.Column(db.Boolean, default=False)
    
    # Receipt Details
    receipt_counter = db.Column(db.Integer)
    receipt_global_no = db.Column(db.Integer)
    fiscal_day_number = db.Column(db.String(20))
    receipt_notes = db.Column(db.Text)
    
    # Tax Payer Information
    tax_payer_name = db.Column(db.String(255))
    tax_payer_tin = db.Column(db.String(50))
    vat_number = db.Column(db.String(50))
    device_branch_name = db.Column(db.String(255))
    
    # Credit/Debit Note Information
    debit_credit_note_invoice_ref = db.Column(db.String(100))
    debit_credit_note_invoice_ref_date = db.Column(db.DateTime)
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InvoiceLineItem(db.Model):
    __tablename__ = 'invoice_line_item'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    receipt_line_type = db.Column(db.String(20), nullable=False)
    receipt_line_no = db.Column(db.Integer, nullable=False)
    receipt_line_hs_code = db.Column(db.String(20))
    receipt_line_name = db.Column(db.String(255), nullable=False)
    receipt_line_price = db.Column(db.Float, nullable=False)
    receipt_line_quantity = db.Column(db.Float, nullable=False)
    receipt_line_total = db.Column(db.Float, nullable=False)
    tax_code = db.Column(db.String(10), nullable=False)
    tax_percent = db.Column(db.Float, nullable=False)
    tax_id = db.Column(db.Integer, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceBranchAddress(db.Model):
    __tablename__ = 'device_branch_address'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    city = db.Column(db.String(100))
    house_no = db.Column(db.String(50))
    province = db.Column(db.String(100))
    street = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceBranchContact(db.Model):
    __tablename__ = 'device_branch_contact'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    email = db.Column(db.String(255))
    phone_number = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)