from flask import Blueprint, jsonify, request, current_app, send_from_directory, render_template_string, send_file
from app.models import DeviceInfo, FiscalDay, Invoice, InvoiceLineItem, DeviceBranchAddress, DeviceBranchContact, DeviceConfiguration
from app import db
from utils.close_day_string_utilts import generate_close_day_string, add_zeros
from utils.date_utils import  get_close_day_string_date
from utils.generate_counters import generate_counters
from utils.update_closeday import update_fiscal_counter_data
from utils.invoice_utils import (
    invoice_exists, get_fiscal_day_counter, get_global_number, calculate_tax_summary,
    calculate_total_sales_amount_with_tax, create_invoice_line_items, create_invoice,
    update_fiscalized_invoice, qr_string_generator, base64_to_hex_md5,
    qr_date, receipt_date_print, get_fiscal_day_open_date_time, get_previous_hash,
    get_credit_debit_note_invoice, ReceiptDeviceSignature, read_pem_file,
    generate_close_day_payload
)
from datetime import datetime
from enum import Enum
from traceback import format_exc
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64

import certifi
import requests
import os
import logging
import json
import urllib3
import hashlib
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime


# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

api = Blueprint('api', __name__)


class FiscaldayStatusEnum(Enum):
    FISCAL_DAY_OPENED = "FISCAL_DAY_OPENED"
    FISCAL_DAY_CLOSED = "FISCAL_DAY_CLOSED"
    # Add other statuses as needed


def get_fiscal_number(device_id: str) -> int:
    """
    Returns the fiscal_day_no for the current open fiscal day for a given device.
    Raises ValueError if no open fiscal day is found.
    """
    
    device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
    current_app.logger.debug(f"mydeviceId: {device}")

    # Get the most recent open fiscal day (highest fiscal_day_no)
    fiscal_day = FiscalDay.query.filter_by(
        device_id=device.device_id, 
        is_open=True
    ).order_by(FiscalDay.fiscal_day_no.desc()).first()
    current_app.logger.debug(f"fiscalDay: no {fiscal_day.fiscal_day_no}")
    if not fiscal_day:
        raise ValueError(f"No open fiscal day found for device_id: {device_id}")

    if not fiscal_day.fiscal_day_no:
        raise ValueError(f"fiscal_day_no not set for open fiscal day of device_id: {device_id}")

  #  return
    return fiscal_day.fiscal_day_no


def get_latest_fiscal_number(device_id: str) -> int:
    """
    Returns the highest fiscal_day_no for a given device, regardless of open/closed status.
    This is useful when you want the most recent fiscal day number, not necessarily the open one.
    Raises ValueError if no fiscal day is found.
    """
    
    device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
    current_app.logger.debug(f"mydeviceId: {device}")

    # Get the highest fiscal day number (regardless of open/closed status)
    fiscal_day = FiscalDay.query.filter_by(
        device_id=device.device_id
    ).order_by(FiscalDay.fiscal_day_no.desc()).first()
    current_app.logger.debug(f"latest fiscalDay: no {fiscal_day.fiscal_day_no}")
    if not fiscal_day:
        raise ValueError(f"No fiscal day found for device_id: {device_id}")

    if not fiscal_day.fiscal_day_no:
        raise ValueError(f"fiscal_day_no not set for fiscal day of device_id: {device_id}")

    return fiscal_day.fiscal_day_no


def get_device_config(device_id):
    """
    Get device configuration from database and return with certificate/key paths.
    """
    # Get device info for certificate and key paths
    device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
    if not device:
        # Fallback to hardcoded paths if device not found
        return {
            "certificate": os.path.abspath(f"certs/{device_id}.pem"),
            "key": os.path.abspath(f"certs/{device_id}.key"),
            "model_name": "Server",
            "model_version_number": "v1"
        }
    
    # Get device configuration from database
    device_config = DeviceConfiguration.query.filter_by(device_id=str(device_id)).first()
    
    config_data = {
        "certificate": device.certificate_path,
        "key": device.key_path,
        "model_name": device.model_name or "Server",
        "model_version_number": device.model_version or "v1"
    }
    
    # Add configuration data if available
    if device_config:
        config_data.update({
            "taxPayerName": device_config.tax_payer_name,
            "taxPayerTIN": device_config.tax_payer_tin,
            "vatNumber": device_config.vat_number,
            "deviceSerialNo": device_config.device_serial_no,
            "deviceBranchName": device_config.device_branch_name,
            "deviceBranchAddress": {
                "province": device_config.device_branch_address_province,
                "city": device_config.device_branch_address_city,
                "street": device_config.device_branch_address_street,
                "houseNo": device_config.device_branch_address_house_no
            },
            "deviceBranchContacts": {
                "phoneNo": device_config.device_branch_contacts_phone_no,
                "email": device_config.device_branch_contacts_email
            },
            "deviceOperatingMode": device_config.device_operating_mode,
            "taxPayerDayMaxHrs": device_config.tax_payer_day_max_hrs,
            "qrUrl": device_config.qr_url,
            "operationID": device_config.operation_id
        })
    
    return config_data


def get_submit_receipt_date():
    # Returns current UTC date-time in ISO 8601 format (e.g. 2025-07-23T12:45:30)
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')




    data = request.get_json()
    return jsonify({"message": "Day closed", "data": data}), 200


@api.route("/getstatus/<device_id>", methods=["GET"])
def get_status(device_id):
    try:

        current_app.logger.info(f"Received request for device_id: {device_id}")
        #device_id ="26428"
        # Fetch device config (from DB or mock)
        device_config = get_device_config(device_id)
        cert_path = device_config["certificate"]
        key_path = device_config["key"]
        device = DeviceInfo.query.filter_by(device_id=device_id).first()

        # Step 2: If device doesn't exist, create and add it
        if not device:
            device = DeviceInfo(
                device_id=str(device_id),
                certificate_path=cert_path,
                key_path=key_path,
                model_name="Server",
                model_version="v1"
            )
            db.session.add(device)
            db.session.commit()
            current_app.logger.debug(f"New device added with device_id: {device_id}")
        else:
            current_app.logger.debug(f"Device with device_id {device_id} already exists.") 






        session = requests.Session()
        session.cert = (cert_path, key_path)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "DeviceModelName": device_config["model_name"],
            "DeviceModelVersion": device_config["model_version_number"]
        }

        zimra_url = f"https://fdmsapitest.zimra.co.zw/Device/v1/{device_id}/GetStatus"
        current_app.logger.debug(f"Target URL: {zimra_url}")
           

        response = session.get(zimra_url, headers=headers, verify=False)
        current_app.logger.debug(f"Response: {response.content}")


        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Request failed", "status": response.status_code}), response.status_code

    except Exception as e:
        print(f"Exception occurred: {e}")
        return jsonify({"error": "Internal error", "details": str(e)}), 500
    


@api.route('/openday/<device_id>', methods=['POST'])
def open_day(device_id):
    # Load device config from DB or return 404 if not found
    device_config = get_device_config(device_id)
    if not device_config:
        return jsonify({"error": "Device not found"}), 404
    
    cert_path = device_config["certificate"]
    key_path = device_config["key"]

    device = DeviceInfo.query.filter_by(device_id=device_id).first()

        # Step 2: If device doesn't exist, create and add it
    if not device:
            device = DeviceInfo(
                device_id=str(device_id),
                certificate_path=cert_path,
                key_path=key_path,
                model_name="Server",
                model_version="v1"
            )
            db.session.add(device)
            db.session.commit()
            current_app.logger.debug(f"New device added with device_id: {device_id}")
    else:
            current_app.logger.debug(f"Device with device_id {device_id} already exists.") 



    # Prepare requests session with client cert and key
    session = requests.Session()
    session.cert = (cert_path, key_path)
    #current_app.logger.debug(f"OpenDay model: {device_config.model_name} , version: {device_config.model_version}")
    # Define headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "DeviceModelName": device_config["model_name"],
        "DeviceModelVersion": "v1"
    }

    # Prepare request data
    request_data = {
        "fiscalDayOpened": get_submit_receipt_date()  # implement this function to get the correct date string
    }
    json_data = json.dumps(request_data)

    current_app.logger.debug(f"OpenDay Payload: {json_data}")

    try:
        url = f'https://fdmsapitest.zimra.co.zw/Device/v1/{device_id}/OpenDay'
        response = session.post(url, data=json_data, headers=headers, verify=False)

        current_app.logger.debug(f"OpenDay Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            current_app.logger.debug(f"OpenDay Response data: {data}")
            
            # Create FiscalDay record in DB
            fiscal_day = FiscalDay(
                device_id = device.device_id,  # Use device.device_id instead of str(device.id)
                fiscal_day_open=request_data['fiscalDayOpened'],
                is_open=True,
                fiscal_day_no=data.get("fiscalDayNo"),
                fiscal_status=FiscaldayStatusEnum.FISCAL_DAY_OPENED.value  # or use an Enum or constant
            )
            db.session.add(fiscal_day)
            db.session.commit()

            return jsonify(data), 200
        else:
            return jsonify({"error": "Request failed"}), response.status_code

    except Exception as e:
        current_app.logger.error(f"Error in open_day: {str(e)}")
        return jsonify({"error": "Request failed"}), 400
    


@api.route('/close_day/<device_id>', methods=['POST'])
def close_day(device_id):
    """
    Close a fiscal day for a specific device according to ZIMRA API specification.
    
    This endpoint uses the Django-style approach with generate_counters function.
    """
    try:
        # 1. Load device config
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        cert_path = device.certificate_path
        key_path = device.key_path

        # 2. Get fiscal day number and close date
        fiscal_day_number = str(get_fiscal_number(device_id))
        
        # 3. Get the open fiscal day that matches the fiscal day number
        open_fiscal_day = FiscalDay.query.filter_by(
            device_id=device.device_id, 
            fiscal_day_no=int(fiscal_day_number),
            is_open=True
        ).first()
        if not open_fiscal_day:
            return jsonify({"error": f"No open fiscal day {fiscal_day_number} found for this device"}), 404

        # Use the fiscal day open date for closing (this is the correct approach)
        fiscal_close_date = open_fiscal_day.fiscal_day_open
        
        # Format the close date properly for signature generation
        from utils.close_day_string_utilts import get_close_day_date_format
        formatted_close_date = get_close_day_date_format(fiscal_close_date)
        
        # 4. Generate counters using Django-style approach
        try:
            # Read private key for generate_counters
            with open(key_path, 'rb') as key_file:
                private_key_data = key_file.read()
            
            # Generate the close day data using generate_counters
            close_data = generate_counters(
                private_key=private_key_data,
                device_id=str(device_id),
                date_string=open_fiscal_day.fiscal_day_open,
                close_day_date=fiscal_close_date,
                fiscal_day_no=int(fiscal_day_number)  # Use the fiscal day number from get_fiscal_number
            )
            
            current_app.logger.debug(f"Generated CloseDay data: {close_data}")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # 5. Update fiscal counter data (Django-style)
        updated_counters = update_fiscal_counter_data(close_data['fiscalDayCounters'])
        close_data['fiscalDayCounters'] = updated_counters

        # 6. Generate string to sign using the correct format
        string_to_sign = generate_close_day_string(
            device_id=str(device_id),
            fiscal_day_no=fiscal_day_number,
            date=formatted_close_date,
            receipt_close=close_data
        )
        
        current_app.logger.debug(f"String to sign for CloseDay: {string_to_sign}")

        # 7. Generate the signature using the device's private key
        with open(key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
        
        # Sign the string using SHA256 with PKCS1v15 padding
        signature = private_key.sign(
            string_to_sign.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Encode signature to base64
        fiscal_day_device_signature = base64.b64encode(signature).decode('utf-8')
        
        # 8. Add the signature to the payload
        # Generate MD5 hash of the signature (16 characters, uppercase)
        signature_bytes = base64.b64decode(fiscal_day_device_signature)
        md5_hash = hashlib.md5(signature_bytes).hexdigest().upper()
        signature_hash = md5_hash[:16]  # Take first 16 characters
        
        # Ensure the signature format matches ZIMRA expectations
        close_data['fiscalDayDeviceSignature'] = {
            "hash": signature_hash,
            "signature": fiscal_day_device_signature
        }
        
        # 9. Prepare secure session with ZIMRA
        session = requests.Session()
        session.cert = (cert_path, key_path)

        # 10. Prepare headers according to ZIMRA API specification
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "DeviceModelName": device.model_name,
            "DeviceModelVersion": device.model_version
        }

        # 11. Send request to ZIMRA
        json_data = json.dumps(close_data)
        current_app.logger.debug(f"CloseDay Payload with signature: {json_data}")
        #return jsonify(json_data), 200
        url = f'https://fdmsapitest.zimra.co.zw/Device/v1/{device_id}/CloseDay'
        response = session.post(url, data=json_data, headers=headers, verify=False)

        current_app.logger.debug(f"ZIMRA CloseDay status: {response.status_code}")

        # 12. Process response and update local DB if successful
        if response.status_code == 200:
            data = response.json()
            current_app.logger.debug(f"ZIMRA CloseDay response: {data}")
            
            # Update fiscal day status
            open_fiscal_day.is_open = False
            open_fiscal_day.fiscal_status = 'FISCAL_DAY_CLOSED'
            db.session.commit()

            return jsonify(data), 200
        else:
            try:
                error_data = response.json()
                current_app.logger.debug(f"ZIMRA CloseDay error response: {error_data}")
                return jsonify({
                    "error": "ZIMRA CloseDay request failed", 
                    "status_code": response.status_code, 
                    "details": error_data
                }), response.status_code
            except:
                current_app.logger.debug(f"ZIMRA CloseDay error response (raw): {response.content}")
                return jsonify({
                    "error": "ZIMRA CloseDay request failed", 
                    "status_code": response.status_code
                }), response.status_code

    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": format_exc()
        }
        current_app.logger.error(f"CloseDay error: {error_details}")
        return jsonify(error_details), 500
    


@api.route('/submit_receipt/<device_id>', methods=['POST'])
def submit_receipt(device_id):
    try:
        # 1. Read and validate posted JSON
        posted_data = request.get_json()
        #current_app.logger.debug(f"Received SubmitReceipt payload: {posted_data}")
        
        # Check if payload has nested receipt structure
        if "receipt" in posted_data:
            receipt_data = posted_data["receipt"]
        else:
            receipt_data = posted_data
        
        # Validate required fields in receipt data
        required_fields = ["invoiceNo", "receiptDate", "receiptType", "receiptTotal"]
        for field in required_fields:
            if field not in receipt_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate credit/debit note specific fields
        if receipt_data.get('creditDebitNote') is not None:
            if 'receiptID' not in receipt_data['creditDebitNote']:
                return jsonify({"error": "Credit/Debit note must include receiptID in creditDebitNote"}), 400
            if not receipt_data.get('receiptNotes'):
                return jsonify({"error": "Credit/Debit note must include receiptNotes"}), 400

        # 2. Load device config
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        cert_path = device.certificate_path
        key_path = device.key_path

        # 3. Get the last fiscal day (open or closed)
        last_fiscal_day = FiscalDay.query.filter_by(device_id=device.device_id).order_by(FiscalDay.id.desc()).first()
        if not last_fiscal_day:
            return jsonify({"error": "No fiscal day found for this device"}), 404

        # 4. Check for duplicate invoice
        if invoice_exists(device_id=str(device_id), invoice_id=str(receipt_data["invoiceNo"])):
            return jsonify({"error": "Duplication Of Invoice Number"}), 400

        # 5. Calculate counters and get previous hash
        formatted_datetime = get_submit_receipt_date()
        previous_receipt_hash = ''

        counter = get_fiscal_day_counter(
            device_id=str(device_id),
            fiscal_open_date_time=get_fiscal_day_open_date_time(
                open_day_date_time=last_fiscal_day.fiscal_day_open
            )
        )

        if counter > 0:
            previous_receipt_hash = get_previous_hash(
                device_id=str(device_id),
                fiscal_open_date_time=get_fiscal_day_open_date_time(
                    open_day_date_time=last_fiscal_day.fiscal_day_open
                )
            )

        # 6. Update receipt data with calculated values
        updated_data = receipt_data.copy()
        updated_data['receiptDate'] = formatted_datetime
        
       
  
        
        # Set receiptCounter to the number of line items in the current invoice
        receipt_lines = updated_data.get('receiptLines', [])
        updated_data['receiptCounter'] = len(receipt_lines)
        
        # Check if this is a credit/debit note and handle receipt lines
        is_credit_debit_note = updated_data.get('creditDebitNote') is not None
        is_credit_note = False
        is_debit_note = False
        
        if is_credit_debit_note:
            # Determine if it's a credit note or debit note based on receiptType
            receipt_type = updated_data.get('receiptType', '').lower()
            if 'credit' in receipt_type:
                is_credit_note = True
            elif 'debit' in receipt_type:
                is_debit_note = True
            else:
                # Default to credit note if receiptType is not specified
                is_credit_note = True
        
        if is_credit_note:
            # For credit notes, make all monetary values in receipt lines negative
            for line in receipt_lines:
                if 'receiptLinePrice' in line:
                    line['receiptLinePrice'] = -abs(line['receiptLinePrice'])
                if 'receiptLineTotal' in line:
                    line['receiptLineTotal'] = -abs(line['receiptLineTotal'])
        elif is_debit_note:
            # For debit notes, ensure all monetary values in receipt lines are positive
            for line in receipt_lines:
                if 'receiptLinePrice' in line:
                    line['receiptLinePrice'] = abs(line['receiptLinePrice'])
                if 'receiptLineTotal' in line:
                    line['receiptLineTotal'] = abs(line['receiptLineTotal'])

        # Auto-generate global number
        from utils.invoice_utils import increment_global_number
        global_number = increment_global_number(str(device_id))
        if global_number < 0:
            return jsonify({"error": "Global Value cannot be negative"}), 400
        current_app.logger.debug(f"Auto-generated global number: {global_number}")
        
        updated_data['receiptGlobalNo'] = global_number

        # 7. Calculate tax summary with enhanced logic
        tax_summary = calculate_tax_summary(updated_data.get('receiptLines', []))
        
        # Create tax objects based on actual tax codes used in receipt lines
        filtered_taxes = []
        
        # Map tax codes to their proper structure
        tax_mapping = {
            '15': {'taxCode': '15', 'taxPercent': 15.0, 'taxID': 3},
            '0': {'taxCode': '0', 'taxPercent': 0.0, 'taxID': 2},
            '-1': {'taxCode': None, 'taxID': 1},  # Exempt - no taxPercent
            '5': {'taxCode': '5', 'taxPercent': 5.0, 'taxID': 514}
        }
        
        # Check if this is a credit/debit note
        is_credit_debit_note = updated_data.get('creditDebitNote') is not None
        is_credit_note = False
        is_debit_note = False
        
        if is_credit_debit_note:
            # Determine if it's a credit note or debit note based on receiptType
            receipt_type = updated_data.get('receiptType', '').lower()
            if 'credit' in receipt_type:
                is_credit_note = True
            elif 'debit' in receipt_type:
                is_debit_note = True
            else:
                # Default to credit note if receiptType is not specified
                is_credit_note = True
        
        # Add tax objects for each tax code that has sales
        for tax_code, tax_data in tax_summary.items():
            if abs(tax_data['salesAmountWithTax']) > 0:  # Include taxes with non-zero sales (positive or negative)
                tax_object = {
                    'taxCode': tax_data['taxCode'],
                    'taxID': tax_data['taxID'],
                    'taxAmount': tax_data['taxAmount'],
                    'salesAmountWithTax': tax_data['salesAmountWithTax']
                }
                
                # For credit notes, make all monetary values negative
                if is_credit_note:
                    tax_object['taxAmount'] = -abs(tax_data['taxAmount'])
                    tax_object['salesAmountWithTax'] = -abs(tax_data['salesAmountWithTax'])
                # For debit notes, ensure all monetary values are positive
                elif is_debit_note:
                    tax_object['taxAmount'] = abs(tax_data['taxAmount'])
                    tax_object['salesAmountWithTax'] = abs(tax_data['salesAmountWithTax'])
                
                # Add taxPercent only for non-exempt items (exempt items have taxID 1)
                if tax_data['taxID'] != 1:
                    tax_object['taxPercent'] = tax_data['taxPercent']
                
                filtered_taxes.append(tax_object)

        # Calculate total
        receipt_total = calculate_total_sales_amount_with_tax(filtered_taxes)
        
        # For credit notes, ensure total is negative
        if is_credit_note:
            receipt_total = -abs(receipt_total)
        # For debit notes, ensure total is positive
        elif is_debit_note:
            receipt_total = abs(receipt_total)
        
        # Ensure receiptPayments has the proper structure
        if 'receiptPayments' not in updated_data or not updated_data['receiptPayments']:
            updated_data['receiptPayments'] = [{'moneyTypeCode': 'Cash', 'paymentAmount': receipt_total}]
        else:
            # Update the first payment method with the calculated total
            updated_data['receiptPayments'][0]['paymentAmount'] = receipt_total
        
        updated_data['receiptTotal'] = receipt_total
        updated_data['receiptTaxes'] = filtered_taxes

        # 8. Generate string to sign with previous hash if available using new method
        string_to_sign = generator_invoice_string(str(device_id), updated_data, filtered_taxes)

        if previous_receipt_hash != '':
            string_to_sign = string_to_sign + str(previous_receipt_hash)


        # 9. Generate signature using ReceiptDeviceSignature class
        private_key = read_pem_file(key_path)
        receipt_device_signature_obj = ReceiptDeviceSignature(string_to_sign, private_key)
        
        receipt_device_signature_obj_data = {
            "hash": receipt_device_signature_obj.get_hash(),
            "signature": receipt_device_signature_obj.sign_data()
        }
        
        # 11. Add signature to receipt data
        updated_data['receiptDeviceSignature'] = receipt_device_signature_obj_data
        
        # 12. Prepare full payload
        full_payload = {
            "receipt": updated_data
        }
        
        # 13. Prepare secure session with ZIMRA
        session = requests.Session()
        session.cert = (cert_path, key_path)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "DeviceModelName": device.model_name,
            "DeviceModelVersion": device.model_version
        }

        # 14. Send request to ZIMRA
        url = f'https://fdmsapitest.zimra.co.zw/Device/v1/{device_id}/SubmitReceipt'
        
        # Debug: Log the calculated values before sending
        current_app.logger.debug(f"Calculated receiptTotal: {updated_data.get('receiptTotal')}")
        current_app.logger.debug(f"Calculated receiptTaxes: {updated_data.get('receiptTaxes')}")
        current_app.logger.debug(f"Calculated receiptPayments: {updated_data.get('receiptPayments')}")
        if is_credit_note:
            current_app.logger.debug(f"Processing as Credit Note - all monetary values are negative")
        elif is_debit_note:
            current_app.logger.debug(f"Processing as Debit Note - all monetary values are positive")
        
        json_data = json.dumps(full_payload)
        current_app.logger.debug(f"SubmitReceipt Payload: {json_data}")
        #return jsonify(json_data), 200
        response = session.post(url, data=json_data, headers=headers, verify=False)
        #current_app.logger.debug(f"ZIMRA SubmitReceipt status: {json_data}")
        
        # 15. Process successful response
        if response.status_code == 200:
            zimra_response = response.json()
            current_app.logger.debug(f"ZIMRA Response: {zimra_response}")
            
            try:
                # Get device configuration from database
                device_config = DeviceConfiguration.query.filter_by(device_id=str(device_id)).first()
                config_data = get_device_config(str(device_id))
                
                # Create invoice data
                invoice_data = {
                    'invoice_id': updated_data['invoiceNo'],
                    'device_id': str(device_id),
                    'receipt_currency': updated_data.get('receiptCurrency', 'USD'),
                    'money_type': 'Cash',
                    'receipt_type': updated_data['receiptType'],
                    'receipt_total': receipt_total,
                    'line_items': updated_data.get('receiptLines', [])
                }
                
                # Create invoice in database
                created_invoice = create_invoice(invoice_data)
                
                # Generate QR code using stored QR URL from device config
                qr_url = device_config.qr_url if device_config and device_config.qr_url else "https://fdmstest.zimra.co.zw/"
                qr_string = qr_string_generator(
                    device_id=str(device_id),
                    qr_url=qr_url,
                    receipt_date=qr_date(),
                    reciept_global_no=global_number,
                    reciept_signature=receipt_device_signature_obj.sign_data()
                )
                
                # Generate verification code
                verification_string = base64_to_hex_md5(receipt_device_signature_obj.sign_data())

                current_app.logger.debug(f"#################################################")
                current_app.logger.debug(f"ZIMRA Response: {verification_string}")
                current_app.logger.debug(f"#################################################")
                
                # Handle credit/debit note logic
                debit_credit_note_invoice_ref = None
                debit_credit_note_invoice_ref_date = None
                
                if updated_data.get('creditDebitNote') is not None:
                    debited_credited_invoice = get_credit_debit_note_invoice(
                        device_id=str(device_id),
                        receipt_id=str(updated_data['creditDebitNote']['receiptID'])
                    )
                    
                    if debited_credited_invoice:
                        debit_credit_note_invoice_ref = debited_credited_invoice.invoice_id
                        debit_credit_note_invoice_ref_date = debited_credited_invoice.timestamp
                    else:
                        debit_credit_note_invoice_ref = str(updated_data['creditDebitNote']['receiptID'])
                
                # Prepare update data using stored device configuration
                update_data = {
                    'invoice_id': updated_data['invoiceNo'],
                    'zimra_receipt_number': str(zimra_response.get('receiptID', '')),
                    'operation_id': str(zimra_response.get('operationID', '')),
                    'qr_code_string': qr_string,
                    'verification_number': verification_string,
                    'hash_string': receipt_device_signature_obj.get_hash(),
                    'is_fiscalized': True,
                    'receipt_counter': len(receipt_lines),
                    'receipt_global_no': global_number,
                    'fiscal_day_number': str(last_fiscal_day.fiscal_day_no),
                    'receipt_notes': updated_data.get('receiptNotes', ''),
                    'tax_payer_name': device_config.tax_payer_name if device_config else config_data.get('taxPayerName', ''),
                    'tax_payer_tin': str(device_config.tax_payer_tin if device_config else config_data.get('taxPayerTIN', '')),
                    'vat_number': str(device_config.vat_number if device_config else config_data.get('vatNumber', '')),
                    'device_branch_name': str(device_config.device_branch_name if device_config else config_data.get('deviceBranchName', '')),
                    'device_branch_address': {
                        'province': device_config.device_branch_address_province if device_config else config_data.get('deviceBranchAddress', {}).get('province', ''),
                        'city': device_config.device_branch_address_city if device_config else config_data.get('deviceBranchAddress', {}).get('city', ''),
                        'street': device_config.device_branch_address_street if device_config else config_data.get('deviceBranchAddress', {}).get('street', ''),
                        'houseNo': device_config.device_branch_address_house_no if device_config else config_data.get('deviceBranchAddress', {}).get('houseNo', '')
                    },
                    'device_branch_contact': {
                        'phoneNo': device_config.device_branch_contacts_phone_no if device_config else config_data.get('deviceBranchContacts', {}).get('phoneNo', ''),
                        'email': device_config.device_branch_contacts_email if device_config else config_data.get('deviceBranchContacts', {}).get('email', '')
                    },
                    'debit_credit_note_invoice_ref': debit_credit_note_invoice_ref,
                    'debit_credit_note_invoice_ref_date': debit_credit_note_invoice_ref_date
                }
                
                # Update invoice with fiscalization data
                update_fiscalized_invoice(update_data)
                
                # Prepare response data using stored device configuration
                response_data = {
                    "taxPayerName": device_config.tax_payer_name if device_config else config_data.get('taxPayerName', ''),
                    "taxPayerTIN": device_config.tax_payer_tin if device_config else config_data.get('taxPayerTIN', ''),
                    "vatNumber": device_config.vat_number if device_config else config_data.get('vatNumber', ''),
                    "deviceBranchName": device_config.device_branch_name if device_config else config_data.get('deviceBranchName', ''),
                    "deviceBranchAddress": {
                        "province": device_config.device_branch_address_province if device_config else config_data.get('deviceBranchAddress', {}).get('province', ''),
                        "city": device_config.device_branch_address_city if device_config else config_data.get('deviceBranchAddress', {}).get('city', ''),
                        "street": device_config.device_branch_address_street if device_config else config_data.get('deviceBranchAddress', {}).get('street', ''),
                        "houseNo": device_config.device_branch_address_house_no if device_config else config_data.get('deviceBranchAddress', {}).get('houseNo', '')
                    },
                    "deviceBranchContacts": {
                        "phoneNo": device_config.device_branch_contacts_phone_no if device_config else config_data.get('deviceBranchContacts', {}).get('phoneNo', ''),
                        "email": device_config.device_branch_contacts_email if device_config else config_data.get('deviceBranchContacts', {}).get('email', '')
                    },
                    "taxCode": "A",
                    "qrUrl": device_config.qr_url if device_config and device_config.qr_url else config_data.get('qrUrl', 'https://fdmstest.zimra.co.zw/'),
                    "deviceSerialNo": device_config.device_serial_no if device_config else config_data.get('deviceSerialNo', ''),
                    "receiptCounter": len(receipt_lines),
                    "receiptGlobalNo": global_number,
                    "fiscalDayNumber": str(last_fiscal_day.fiscal_day_no),
                    "receiptID": zimra_response.get('receiptID', ''),
                    "invoiceNumber": updated_data['invoiceNo'],
                    "deviceID": str(device_id),
                    "date": receipt_date_print(),
                    "taxPercentage": "15",
                    "qrString": qr_string,
                    "verificationCode": verification_string,
                    # Include the calculated receipt data
                    "receiptTaxes": updated_data.get('receiptTaxes', []),
                    "receiptPayments": updated_data.get('receiptPayments', []),
                    "receiptTotal": updated_data.get('receiptTotal', 0),
                    "receiptLines": updated_data.get('receiptLines', [])
                }
                
                return jsonify(response_data), 200
                
            except Exception as e:
                current_app.logger.error(f"Error processing successful response: {str(e)}")
                return jsonify({"error": "Database operation failed", "details": str(e)}), 500
        else:
            try:
                error_data = response.json()
                current_app.logger.debug(f"ZIMRA Error Response: {error_data}")
                return jsonify({"error": "ZIMRA request failed", "status_code": response.status_code, "details": error_data}), response.status_code
            except:
                current_app.logger.debug(f"ZIMRA Error Response (raw): {response.content}")
                return jsonify({"error": "ZIMRA request failed", "status_code": response.status_code}), response.status_code

    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": format_exc()
        }
        return jsonify(error_details), 500


def generate_receipt_string(device_id: str, receipt_number: str, receipt_date_time: str, 
                           receipt_amount: str, receipt_tax_amount: str, receipt_total_amount: str) -> str:
    """
    Generates the string to sign for SubmitReceipt according to ZIMRA specifications.
    
    Parameters:
        device_id (str): The device identifier
        receipt_number (str): The receipt number
        receipt_date_time (str): The receipt date and time
        receipt_amount (str): The receipt amount
        receipt_tax_amount (str): The receipt tax amount
        receipt_total_amount (str): The receipt total amount
    
    Returns:
        str: Concatenated string ready for signing
    """
    # Format amounts to remove decimal places and ensure proper formatting
    formatted_amount = str(int(float(receipt_amount) * 100))
    formatted_tax_amount = str(int(float(receipt_tax_amount) * 100))
    formatted_total_amount = str(int(float(receipt_total_amount) * 100))
    
    # Concatenate values in the order specified by ZIMRA
    concatenated_string = f"{device_id}{receipt_number}{receipt_date_time}{formatted_amount}{formatted_tax_amount}{formatted_total_amount}"
    
    return concatenated_string.upper()


def generator_invoice_string(device_id: str, receipt: dict, taxes: list) -> str:
    """
    Generates the string to sign for SubmitReceipt using the new format with tax details.
    
    Parameters:
        device_id (str): The device identifier
        receipt (dict): The receipt data
        taxes (list): List of tax items
    
    Returns:
        str: Concatenated string ready for signing
    """
    generated_dict = extract_invoice_string_first_part(device_id, receipt)
    concat_string = concat_helper_invoice_string(generated_dict)

    return concat_string.upper() + get_concatenated_string_second_part(taxes)


def get_concatenated_string_second_part(data):
    """
    Generates the second part of the invoice string from tax data.
    
    Parameters:
        data (list): List of tax items
    
    Returns:
        str: Concatenated tax string
    """
    result = ""
    for item in data:
        if 'taxPercent' not in item:
            tax_percent_formatted = ""
            tax_amount_cents = round(item['taxAmount'] * 100)
            sales_amount_cents = round(item['salesAmountWithTax'] * 100)
            result = result + str(item['taxCode']) + str(tax_percent_formatted) + str(tax_amount_cents) + str(sales_amount_cents)
        else:
            tax_percent_formatted = f"{float(item['taxPercent']):.2f}"
            tax_amount_cents = round(item['taxAmount'] * 100)
            sales_amount_cents = round(item['salesAmountWithTax'] * 100)
            result = result + str(item['taxCode']) + str(tax_percent_formatted) + str(tax_amount_cents) + str(sales_amount_cents)

    return result.upper()


def extract_invoice_string_first_part(device_id: str, receipt: dict) -> dict:
    """
    Extracts the first part of the invoice string from receipt data.
    
    Parameters:
        device_id (str): The device identifier
        receipt (dict): The receipt data
    
    Returns:
        dict: Dictionary with extracted values
    """
    # Handle both nested and flat receipt structures
    if 'receipt' in receipt:
        receipt_data = receipt['receipt']
    else:
        receipt_data = receipt
    
    extracted_dict = {
        "device_id": device_id,
        "receiptType": receipt_data['receiptType'],
        "receiptCurrency": receipt_data['receiptCurrency'],
        "receiptGlobalNo": receipt_data['receiptGlobalNo'],
        "receiptDate": receipt_data['receiptDate'],
        "receiptTotal": str(round(receipt_data['receiptTotal']*100)).replace(".00","").replace(".0","")
    }

    return extracted_dict


def concat_helper_invoice_string(receipt: dict) -> str:
    """
    Concatenates the values from the receipt dictionary.
    
    Parameters:
        receipt (dict): The receipt dictionary
    
    Returns:
        str: Concatenated string
    """
    concatenated_values = ""
    for value in receipt.values():
        if isinstance(value, list):
            for item in value:
                concatenated_values += item + ""
        else:
            concatenated_values += str(value) + ""

    return concatenated_values


def add_zeros(value):
    """
    Formats a value to have 2 decimal places.
    
    Parameters:
        value: The value to format
    
    Returns:
        str: Formatted value
    """
    if isinstance(value, int):
        return f"{value:.2f}"
    else:
        return value


def add_leading_zeros_zfill(number, target_length) -> str:
    """
    Adds leading zeros to a number to reach the target length.
    
    Parameters:
        number: The number to format
        target_length (int): The target length
    
    Returns:
        str: Formatted number with leading zeros
    """
    return str(number).zfill(target_length)





@api.route('/get_config/<device_id>', methods=['GET'])
def get_config(device_id):
    try:
        # Retrieve device configuration
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()

        device_config = get_device_config(device_id)
        cert_path = device_config["certificate"]
        key_path = device_config["key"]
        device = DeviceInfo.query.filter_by(device_id=device_id).first()
        
        print("CloseDay Data ##########")
        print(certifi.where())
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Debug: View private key if needed
        # current_app.logger.debug(read_pem_file(device.key_path))

        # Set up session with client certificate and key
        session = requests.Session()
        session.cert = (cert_path, key_path)

        # Define request headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "DeviceModelName": device.model_name,
            "DeviceModelVersion": device.model_version
        }
        

      #  requests.get(url, verify='zimra-root-ca.pem')
        print("CloseDay Data ##########3")
        # Send request to ZIMRA API
        url = f'https://fdmsapitest.zimra.co.zw/Device/v1/{device_id}/GetConfig'
        #requests.get(url, verify='zimra-root-ca.pem')
        print("CloseDay Data ##########4")
        response = session.get(url, headers=headers, verify=False)
        
        
    
        current_app.logger.debug(f"GetConfig status: {response.status_code}")
        
        current_app.logger.debug(f"GetConfig body: {response}")
        if response.status_code == 200:
            # Parse the response data
            config_data = response.json()
            
            # Save or update device configuration in database
            device_config_record = DeviceConfiguration.query.filter_by(device_id=str(device_id)).first()
            
            if device_config_record:
                # Update existing record
                device_config_record.tax_payer_name = config_data.get('taxPayerName')
                device_config_record.tax_payer_tin = config_data.get('taxPayerTIN')
                device_config_record.vat_number = config_data.get('vatNumber')
                device_config_record.device_serial_no = config_data.get('deviceSerialNo')
                device_config_record.device_branch_name = config_data.get('deviceBranchName')
                device_config_record.device_operating_mode = config_data.get('deviceOperatingMode')
                device_config_record.tax_payer_day_max_hrs = config_data.get('taxPayerDayMaxHrs')
                device_config_record.qr_url = config_data.get('qrUrl')
                device_config_record.operation_id = config_data.get('operationID')
                
                # Address information
                if config_data.get('deviceBranchAddress'):
                    address = config_data['deviceBranchAddress']
                    device_config_record.device_branch_address_province = address.get('province')
                    device_config_record.device_branch_address_city = address.get('city')
                    device_config_record.device_branch_address_street = address.get('street')
                    device_config_record.device_branch_address_house_no = address.get('houseNo')
                
                # Contact information
                if config_data.get('deviceBranchContacts'):
                    contacts = config_data['deviceBranchContacts']
                    device_config_record.device_branch_contacts_phone_no = contacts.get('phoneNo')
                    device_config_record.device_branch_contacts_email = contacts.get('email')
                
                device_config_record.updated_at = datetime.utcnow()
            else:
                # Create new record
                device_config_record = DeviceConfiguration(
                    device_id=str(device_id),
                    tax_payer_name=config_data.get('taxPayerName'),
                    tax_payer_tin=config_data.get('taxPayerTIN'),
                    vat_number=config_data.get('vatNumber'),
                    device_serial_no=config_data.get('deviceSerialNo'),
                    device_branch_name=config_data.get('deviceBranchName'),
                    device_operating_mode=config_data.get('deviceOperatingMode'),
                    tax_payer_day_max_hrs=config_data.get('taxPayerDayMaxHrs'),
                    qr_url=config_data.get('qrUrl'),
                    operation_id=config_data.get('operationID')
                )
                
                # Address information
                if config_data.get('deviceBranchAddress'):
                    address = config_data['deviceBranchAddress']
                    device_config_record.device_branch_address_province = address.get('province')
                    device_config_record.device_branch_address_city = address.get('city')
                    device_config_record.device_branch_address_street = address.get('street')
                    device_config_record.device_branch_address_house_no = address.get('houseNo')
                
                # Contact information
                if config_data.get('deviceBranchContacts'):
                    contacts = config_data['deviceBranchContacts']
                    device_config_record.device_branch_contacts_phone_no = contacts.get('phoneNo')
                    device_config_record.device_branch_contacts_email = contacts.get('email')
            
            # Save to database
            db.session.add(device_config_record)
            db.session.commit()
            
            current_app.logger.info(f"Device configuration saved/updated for device_id: {device_id}")
            
            return jsonify(config_data), 200
        else:
            return jsonify({"error": "Request failed"}), response.status_code

    except Exception as e:
        current_app.logger.error(f"Error in get_config: {e}")
        return jsonify({"error": str(e)}), 400


@api.route('/device_config/<device_id>', methods=['GET'])
def get_stored_device_config(device_id):
    """Get stored device configuration from database"""
    try:
        device_config = DeviceConfiguration.query.filter_by(device_id=str(device_id)).first()
        
        if not device_config:
            return jsonify({"error": "Device configuration not found"}), 404
        
        # Format the response to match the ZIMRA API response structure
        config_data = {
            "taxPayerName": device_config.tax_payer_name,
            "taxPayerTIN": device_config.tax_payer_tin,
            "vatNumber": device_config.vat_number,
            "deviceSerialNo": device_config.device_serial_no,
            "deviceBranchName": device_config.device_branch_name,
            "deviceBranchAddress": {
                "province": device_config.device_branch_address_province,
                "city": device_config.device_branch_address_city,
                "street": device_config.device_branch_address_street,
                "houseNo": device_config.device_branch_address_house_no
            },
            "deviceBranchContacts": {
                "phoneNo": device_config.device_branch_contacts_phone_no,
                "email": device_config.device_branch_contacts_email
            },
            "deviceOperatingMode": device_config.device_operating_mode,
            "taxPayerDayMaxHrs": device_config.tax_payer_day_max_hrs,
            "qrUrl": device_config.qr_url,
            "operationID": device_config.operation_id
        }
        
        return jsonify(config_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_stored_device_config: {e}")
        return jsonify({"error": str(e)}), 500


@api.route('/invoices', methods=['GET'])
def list_invoices():
    """List all invoices with optional filtering"""
    try:
        # Get query parameters
        device_id = request.args.get('device_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status')  # fiscalized, pending
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = Invoice.query
        
        # Apply filters
        if device_id:
            query = query.filter_by(device_id=device_id)
        
        if status:
            if status == 'fiscalized':
                query = query.filter_by(is_fiscalized=True)
            elif status == 'pending':
                query = query.filter_by(is_fiscalized=False)
        
        if date_from:
            query = query.filter(Invoice.created_at >= date_from)
        
        if date_to:
            query = query.filter(Invoice.created_at <= date_to)
        
        # Order by creation date (newest first)
        query = query.order_by(Invoice.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        invoices = pagination.items
        
        # Format response
        invoice_list = []
        for invoice in invoices:
            invoice_data = {
                'id': invoice.id,
                'invoice_id': invoice.invoice_id,
                'device_id': invoice.device_id,
                'receipt_currency': invoice.receipt_currency,
                'money_type': invoice.money_type,
                'receipt_type': invoice.receipt_type,
                'receipt_total': float(invoice.receipt_total),
                'zimra_receipt_number': invoice.zimra_receipt_number,
                'operation_id': invoice.operation_id,
                'qr_code_string': invoice.qr_code_string,
                'verification_number': invoice.verification_number,
                'is_fiscalized': invoice.is_fiscalized,
                'receipt_counter': invoice.receipt_counter,
                'receipt_global_no': invoice.receipt_global_no,
                'fiscal_day_number': invoice.fiscal_day_number,
                'receipt_notes': invoice.receipt_notes,
                'tax_payer_name': invoice.tax_payer_name,
                'tax_payer_tin': invoice.tax_payer_tin,
                'vat_number': invoice.vat_number,
                'device_branch_name': invoice.device_branch_name,
                'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
                'updated_at': invoice.updated_at.isoformat() if invoice.updated_at else None
            }
            invoice_list.append(invoice_data)
        
        response_data = {
            'invoices': invoice_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in list_invoices: {str(e)}")
        return jsonify({"error": "Failed to fetch invoices", "details": str(e)}), 500


@api.route('/invoices/<invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Get a specific invoice with line items"""
    try:
        invoice = Invoice.query.filter_by(invoice_id=invoice_id).first()
        
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        
        # Get line items
        line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice.id).all()
        
        # Get branch address and contact
        branch_address = DeviceBranchAddress.query.filter_by(invoice_id=invoice.id).first()
        branch_contact = DeviceBranchContact.query.filter_by(invoice_id=invoice.id).first()
        
        # Format line items
        line_items_data = []
        for item in line_items:
            line_item_data = {
                'id': item.id,
                'receipt_line_type': item.receipt_line_type,
                'receipt_line_no': item.receipt_line_no,
                'receipt_line_hs_code': item.receipt_line_hs_code,
                'receipt_line_name': item.receipt_line_name,
                'receipt_line_price': float(item.receipt_line_price),
                'receipt_line_quantity': float(item.receipt_line_quantity),
                'receipt_line_total': float(item.receipt_line_total),
                'tax_code': item.tax_code,
                'tax_percent': float(item.tax_percent),
                'tax_id': item.tax_id
            }
            line_items_data.append(line_item_data)
        
        # Format branch address
        branch_address_data = None
        if branch_address:
            branch_address_data = {
                'city': branch_address.city,
                'house_no': branch_address.house_no,
                'province': branch_address.province,
                'street': branch_address.street
            }
        
        # Format branch contact
        branch_contact_data = None
        if branch_contact:
            branch_contact_data = {
                'email': branch_contact.email,
                'phone_number': branch_contact.phone_number
            }
        
        invoice_data = {
            'id': invoice.id,
            'invoice_id': invoice.invoice_id,
            'device_id': invoice.device_id,
            'receipt_currency': invoice.receipt_currency,
            'money_type': invoice.money_type,
            'receipt_type': invoice.receipt_type,
            'receipt_total': float(invoice.receipt_total),
            'zimra_receipt_number': invoice.zimra_receipt_number,
            'operation_id': invoice.operation_id,
            'qr_code_string': invoice.qr_code_string,
            'verification_number': invoice.verification_number,
            'hash_string': invoice.hash_string,
            'is_fiscalized': invoice.is_fiscalized,
            'receipt_counter': invoice.receipt_counter,
            'receipt_global_no': invoice.receipt_global_no,
            'fiscal_day_number': invoice.fiscal_day_number,
            'receipt_notes': invoice.receipt_notes,
            'tax_payer_name': invoice.tax_payer_name,
            'tax_payer_tin': invoice.tax_payer_tin,
            'vat_number': invoice.vat_number,
            'device_branch_name': invoice.device_branch_name,
            'debit_credit_note_invoice_ref': invoice.debit_credit_note_invoice_ref,
            'debit_credit_note_invoice_ref_date': invoice.debit_credit_note_invoice_ref_date.isoformat() if invoice.debit_credit_note_invoice_ref_date else None,
            'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
            'updated_at': invoice.updated_at.isoformat() if invoice.updated_at else None,
            'line_items': line_items_data,
            'branch_address': branch_address_data,
            'branch_contact': branch_contact_data
        }
        
        return jsonify(invoice_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_invoice: {str(e)}")
        return jsonify({"error": "Failed to fetch invoice", "details": str(e)}), 500


@api.route('/invoices/<invoice_id>/pdf', methods=['GET'])
def download_invoice_pdf(invoice_id):
    """Download invoice as PDF using A4 template format"""
    try:
        invoice = Invoice.query.filter_by(invoice_id=invoice_id).first()
        
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        
        # Get line items
        line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice.id).all()
        
        # Get branch address and contact
        branch_address = DeviceBranchAddress.query.filter_by(invoice_id=invoice.id).first()
        branch_contact = DeviceBranchContact.query.filter_by(invoice_id=invoice.id).first()
        
        # Prepare invoice data for template
        invoice_data = {
            'invoice_id': invoice.invoice_id,
            'zimra_receipt_number': invoice.zimra_receipt_number,
            'device_id': invoice.device_id,
            'created_at': invoice.created_at.strftime('%Y-%m-%d %H:%M:%S') if invoice.created_at else 'N/A',
            'is_fiscalized': invoice.is_fiscalized,
            'receipt_type': invoice.receipt_type,
            'money_type': invoice.money_type,
            'receipt_counter': invoice.receipt_counter,
            'receipt_global_no': invoice.receipt_global_no,
            'fiscal_day_number': invoice.fiscal_day_number,
            'operation_id': invoice.operation_id,
            'verification_number': invoice.verification_number,
            'hash_string': invoice.hash_string,
            'tax_payer_name': invoice.tax_payer_name,
            'tax_payer_tin': invoice.tax_payer_tin,
            'vat_number': invoice.vat_number,
            'device_branch_name': invoice.device_branch_name,
            'debit_credit_note_invoice_ref_date': invoice.debit_credit_note_invoice_ref_date.strftime('%Y-%m-%d %H:%M:%S') if invoice.debit_credit_note_invoice_ref_date else None,
            'receipt_total': invoice.receipt_total,
            'notes': invoice.receipt_notes,
            'qr_code_url': invoice.qr_code_string,
            'branch_address': f"{branch_address.street}, {branch_address.house_no}, {branch_address.city}, {branch_address.province}" if branch_address else None,
            'branch_contact': f"Email: {branch_contact.email}, Phone: {branch_contact.phone_number}" if branch_contact else None,
            'line_items': []
        }
        
        # Add line items
        for item in line_items:
            invoice_data['line_items'].append({
                'receipt_line_name': item.receipt_line_name,
                'receipt_line_quantity': item.receipt_line_quantity,
                'receipt_line_price': item.receipt_line_price,
                'receipt_line_total': item.receipt_line_total,
                'tax_code': item.tax_code,
                'tax_percent': item.tax_percent,
                'receipt_line_hs_code': item.receipt_line_hs_code,
                'tax_id': item.tax_id
            })
        
        # Import and use the A4 template
        from invoice_template import generate_invoice_pdf_a4_format
        
        # Generate PDF using A4 template
        buffer = generate_invoice_pdf_a4_format(invoice_data)
        
        # Return PDF file
        filename = f"invoice_{invoice.invoice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error generating PDF for invoice {invoice_id}: {str(e)}")
        return jsonify({"error": "Failed to generate PDF", "details": str(e)}), 500


@api.route('/invoices-ui', methods=['GET'])
def invoices_ui():
    """Serve the invoice listing UI"""
    try:
        with open('static/invoices.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({"error": "Invoice UI file not found"}), 404
    except Exception as e:
        return jsonify({"error": "Failed to load invoice UI", "details": str(e)}), 500


@api.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


@api.route('/static_files/<path:filename>')
def serve_static_files(filename):
    """Serve static files from static_files directory"""
    import os
    static_files_dir = os.path.join(os.getcwd(), 'static_files')
    current_app.logger.debug(f"Serving static file: {filename} from directory: {static_files_dir}")
    current_app.logger.debug(f"File exists: {os.path.exists(os.path.join(static_files_dir, filename))}")
    return send_from_directory(static_files_dir, filename)


@api.route('/', methods=['GET'])
def index():
    """Serve the main index page"""
    try:
        with open('static/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({"error": "Index file not found"}), 404
    except Exception as e:
        return jsonify({"error": "Failed to load index", "details": str(e)}), 500


@api.route('/invoices/<invoice_id>/view', methods=['GET'])
def view_invoice(invoice_id):
    """View invoice details in HTML format using InvoiceA4 template"""
    try:
        invoice = Invoice.query.filter_by(invoice_id=invoice_id).first()
        
        if not invoice:
            return jsonify({"error": "Invoice not found"}), 404
        
        # Get line items
        line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice.id).all()
        
        # Get branch address and contact
        branch_address = DeviceBranchAddress.query.filter_by(invoice_id=invoice.id).first()
        branch_contact = DeviceBranchContact.query.filter_by(invoice_id=invoice.id).first()
        
        # Calculate tax summaries
        tax_summaries = []
        tax_groups = {}
        
        for item in line_items:
            tax_percent = item.tax_percent or 0
            if tax_percent not in tax_groups:
                tax_groups[tax_percent] = {
                    'amount': 0,
                    'vat_amount': 0,
                    'tax_code': item.tax_code
                }
            
            amount = item.receipt_line_total or 0
            vat_amount = amount * (tax_percent / 100)
            
            tax_groups[tax_percent]['amount'] += amount
            tax_groups[tax_percent]['vat_amount'] += vat_amount
        
        # Convert to list format for template
        for tax_percent, data in sorted(tax_groups.items(), reverse=True):
            if tax_percent > 0:
                tax_summaries.append({
                    'label': f"Total {tax_percent}%",
                    'amount': data['amount'],
                    'vat_amount': data['vat_amount']
                })
        
        # Generate QR code image for HTML display
        qr_code_image = None
        if invoice.qr_code_string:
            try:
                import qrcode
                import base64
                from io import BytesIO
                
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(invoice.qr_code_string)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert to base64 for HTML display
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                qr_code_image = base64.b64encode(buffer.getvalue()).decode()
            except Exception as e:
                current_app.logger.warning(f"Could not generate QR code: {e}")
        
        # Prepare template data
        template_data = {
            'invoice': invoice,
            'line_items': line_items,
            'branch_address': branch_address,
            'branch_contact': branch_contact,
            'tax_summaries': tax_summaries,
            'qr_code_image': qr_code_image
        }
        
        # Use Jinja2 for template rendering
        try:
            from jinja2 import Environment, FileSystemLoader
            
            # Set up Jinja2 environment
            env = Environment(loader=FileSystemLoader('static'))
            template = env.get_template('invoice_a4_template.html')
            
            # Render the template
            rendered_html = template.render(**template_data)
            
            return rendered_html, 200, {'Content-Type': 'text/html'}
            
        except ImportError:
            # Fallback to simple template rendering if Jinja2 is not available
            try:
                with open('static/invoice_a4_template.html', 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # Simple template rendering
                from string import Template
                template = Template(template_content)
                
                # Convert template data to string format
                rendered_html = template.safe_substitute(
                    invoice_id=invoice.invoice_id,
                    device_id=invoice.device_id,
                    verification_number=invoice.verification_number or '-',
                    qr_code_string=invoice.qr_code_string or '-',
                    qr_code_image=qr_code_image or '',
                    receipt_type=invoice.receipt_type or 'SALE',
                    tax_payer_name=invoice.tax_payer_name or '-',
                    tax_payer_tin=invoice.tax_payer_tin or '-',
                    vat_number=invoice.vat_number or '',
                    device_branch_name=invoice.device_branch_name or '-',
                    receipt_counter=invoice.receipt_counter or '-',
                    receipt_global_no=invoice.receipt_global_no or '-',
                    zimra_receipt_number=invoice.zimra_receipt_number or '-',
                    fiscal_day_number=invoice.fiscal_day_number or '-',
                    created_at=invoice.created_at.strftime('%d/%m/%Y %H:%M') if invoice.created_at else '-',
                    debit_credit_note_invoice_ref_date=invoice.debit_credit_note_invoice_ref_date.strftime('%d/%m/%Y %H:%M') if invoice.debit_credit_note_invoice_ref_date else '',
                    receipt_total=f"{invoice.receipt_total:.2f}" if invoice.receipt_total else '0.00',
                    notes=invoice.receipt_notes or '',
                    branch_address_street=branch_address.street if branch_address else '',
                    branch_address_house_no=branch_address.house_no if branch_address else '',
                    branch_address_city=branch_address.city if branch_address else '',
                    branch_address_province=branch_address.province if branch_address else '',
                    branch_contact_email=branch_contact.email if branch_contact else '-',
                    branch_contact_phone=branch_contact.phone_number if branch_contact else '-'
                )
                
                return rendered_html, 200, {'Content-Type': 'text/html'}
                
            except FileNotFoundError:
                return jsonify({"error": "Invoice template file not found"}), 404
            except Exception as e:
                current_app.logger.error(f"Error rendering invoice template: {str(e)}")
                return jsonify({"error": "Failed to render invoice template", "details": str(e)}), 500
        
    except Exception as e:
        current_app.logger.error(f"Error viewing invoice {invoice_id}: {str(e)}")
        return jsonify({"error": "Failed to view invoice", "details": str(e)}), 500


@api.route('/fiscal_counters/<device_id>', methods=['GET'])
def get_fiscal_counters(device_id):
    """
    Get fiscal counters for a specific device and fiscal day.
    
    This endpoint implements section 6. FISCAL COUNTERS from the ZIMRA API specification.
    
    Parameters:
        device_id (str): Device identifier
        fiscal_day_no (int, optional): Specific fiscal day number. If not provided, uses current open fiscal day.
        
    Returns:
        JSON response with fiscal counter data
    """
    try:
        # Get query parameters
        fiscal_day_no = request.args.get('fiscal_day_no')
        
        # Load device config
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Determine fiscal day number
        if fiscal_day_no:
            # Use provided fiscal day number
            target_fiscal_day_no = int(fiscal_day_no)
        else:
            # Use current open fiscal day
            try:
                target_fiscal_day_no = get_fiscal_number(device_id)
            except ValueError as e:
                return jsonify({"error": str(e)}), 404

        # Get fiscal day record
        fiscal_day = FiscalDay.query.filter_by(
            device_id=device.device_id,
            fiscal_day_no=target_fiscal_day_no
        ).first()
        
        if not fiscal_day:
            return jsonify({"error": f"Fiscal day {target_fiscal_day_no} not found for device {device_id}"}), 404

        # Get all invoices for this device and fiscal day
        invoices = Invoice.query.filter_by(
            device_id=str(device_id),
            fiscal_day_number=str(target_fiscal_day_no)
        ).all()

        if not invoices:
            return jsonify({
                "error": f"No invoices found for device {device_id} and fiscal day {target_fiscal_day_no}",
                "fiscal_day_no": target_fiscal_day_no,
                "fiscal_day_open": fiscal_day.fiscal_day_open,
                "is_open": fiscal_day.is_open,
                "fiscal_counters": []
            }), 404

        # Generate fiscal counters using existing utility
        from utils.generate_counters import generate_counters
        
        # Read private key for signature generation
        with open(device.key_path, 'rb') as key_file:
            private_key_data = key_file.read()
        
        # Generate counters
        counters_data = generate_counters(
            private_key=private_key_data,
            device_id=str(device_id),
            date_string=fiscal_day.fiscal_day_open,
            close_day_date=fiscal_day.fiscal_day_open,
            fiscal_day_no=target_fiscal_day_no
        )
        
        # Update fiscal counter data (apply ZIMRA-specific formatting)
        updated_counters = update_fiscal_counter_data(counters_data['fiscalDayCounters'])
        
        # Calculate summary statistics
        total_receipts = len(invoices)
        total_amount = sum(float(invoice.receipt_total or 0) for invoice in invoices)
        
        # Group counters by type for better organization
        counters_by_type = {}
        for counter in updated_counters:
            counter_type = counter.get('fiscalCounterType', 'Unknown')
            if counter_type not in counters_by_type:
                counters_by_type[counter_type] = []
            counters_by_type[counter_type].append(counter)
        
        # Prepare response data
        response_data = {
            "device_id": str(device_id),
            "fiscal_day_no": target_fiscal_day_no,
            "fiscal_day_open": fiscal_day.fiscal_day_open,
            "fiscal_day_status": "OPEN" if fiscal_day.is_open else "CLOSED",
            "total_receipts": total_receipts,
            "total_amount": round(total_amount, 2),
            "receipt_counter": counters_data.get('receiptCounter', 0),
            "fiscal_counters": updated_counters,
            "counters_by_type": counters_by_type,
            "summary": {
                "sale_counters": len([c for c in updated_counters if c.get('fiscalCounterType') == 'SaleByTax']),
                "tax_counters": len([c for c in updated_counters if c.get('fiscalCounterType') == 'SaleTaxByTax']),
                "balance_counters": len([c for c in updated_counters if c.get('fiscalCounterType') == 'BalanceByMoneyType']),
                "credit_note_counters": len([c for c in updated_counters if 'CreditNote' in c.get('fiscalCounterType', '')]),
                "debit_note_counters": len([c for c in updated_counters if 'DebitNote' in c.get('fiscalCounterType', '')])
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": format_exc()
        }
        current_app.logger.error(f"Fiscal counters error: {error_details}")
        return jsonify(error_details), 500


@api.route('/fiscal_counters/<device_id>/detailed', methods=['GET'])
def get_detailed_fiscal_counters(device_id):
    """
    Get detailed fiscal counters with breakdown by currency, tax type, and payment method.
    
    This endpoint provides a more detailed view of fiscal counters for analysis.
    """
    try:
        # Get query parameters
        fiscal_day_no = request.args.get('fiscal_day_no')
        
        # Load device config
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Determine fiscal day number
        if fiscal_day_no:
            target_fiscal_day_no = int(fiscal_day_no)
        else:
            try:
                target_fiscal_day_no = get_fiscal_number(device_id)
            except ValueError as e:
                return jsonify({"error": str(e)}), 404

        # Get fiscal day record
        fiscal_day = FiscalDay.query.filter_by(
            device_id=device.device_id,
            fiscal_day_no=target_fiscal_day_no
        ).first()
        
        if not fiscal_day:
            return jsonify({"error": f"Fiscal day {target_fiscal_day_no} not found for device {device_id}"}), 404

        # Get all invoices with line items
        invoices = Invoice.query.filter_by(
            device_id=str(device_id),
            fiscal_day_number=str(target_fiscal_day_no)
        ).all()

        if not invoices:
            return jsonify({
                "error": f"No invoices found for device {device_id} and fiscal day {target_fiscal_day_no}",
                "fiscal_day_no": target_fiscal_day_no,
                "fiscal_day_open": fiscal_day.fiscal_day_open,
                "is_open": fiscal_day.is_open,
                "detailed_breakdown": {}
            }), 404

        # Calculate detailed breakdown
        detailed_breakdown = {
            "by_currency": {},
            "by_tax_type": {},
            "by_payment_method": {},
            "by_receipt_type": {},
            "invoice_details": []
        }

        # Process each invoice
        for invoice in invoices:
            line_items = InvoiceLineItem.query.filter_by(invoice_id=invoice.id).all()
            
            # Currency breakdown
            currency = invoice.receipt_currency or 'ZWL'
            if currency not in detailed_breakdown["by_currency"]:
                detailed_breakdown["by_currency"][currency] = {
                    "total_amount": 0.0,
                    "total_tax": 0.0,
                    "invoice_count": 0
                }
            detailed_breakdown["by_currency"][currency]["total_amount"] += float(invoice.receipt_total or 0)
            detailed_breakdown["by_currency"][currency]["invoice_count"] += 1
            
            # Payment method breakdown
            payment_method = invoice.money_type or 'Cash'
            if payment_method not in detailed_breakdown["by_payment_method"]:
                detailed_breakdown["by_payment_method"][payment_method] = {
                    "total_amount": 0.0,
                    "invoice_count": 0
                }
            detailed_breakdown["by_payment_method"][payment_method]["total_amount"] += float(invoice.receipt_total or 0)
            detailed_breakdown["by_payment_method"][payment_method]["invoice_count"] += 1
            
            # Receipt type breakdown
            receipt_type = invoice.receipt_type or 'SALE'
            if receipt_type not in detailed_breakdown["by_receipt_type"]:
                detailed_breakdown["by_receipt_type"][receipt_type] = {
                    "total_amount": 0.0,
                    "invoice_count": 0
                }
            detailed_breakdown["by_receipt_type"][receipt_type]["total_amount"] += float(invoice.receipt_total or 0)
            detailed_breakdown["by_receipt_type"][receipt_type]["invoice_count"] += 1
            
            # Process line items for tax breakdown
            for line_item in line_items:
                tax_code = line_item.tax_code or 'C'
                tax_percent = line_item.tax_percent or 15.0
                tax_id = line_item.tax_id or 3
                
                tax_key = f"{tax_code}_{tax_percent}%"
                if tax_key not in detailed_breakdown["by_tax_type"]:
                    detailed_breakdown["by_tax_type"][tax_key] = {
                        "tax_code": tax_code,
                        "tax_percent": tax_percent,
                        "tax_id": tax_id,
                        "total_amount": 0.0,
                        "total_tax": 0.0,
                        "line_count": 0
                    }
                
                line_total = float(line_item.receipt_line_total or 0)
                tax_amount = float(line_item.tax_percent or 0) / 100 * line_total if line_item.tax_percent else 0
                
                detailed_breakdown["by_tax_type"][tax_key]["total_amount"] += line_total
                detailed_breakdown["by_tax_type"][tax_key]["total_tax"] += tax_amount
                detailed_breakdown["by_tax_type"][tax_key]["line_count"] += 1
            
            # Add invoice details
            invoice_detail = {
                "invoice_id": invoice.invoice_id,
                "zimra_receipt_number": invoice.zimra_receipt_number,
                "receipt_type": invoice.receipt_type,
                "receipt_total": float(invoice.receipt_total or 0),
                "receipt_currency": invoice.receipt_currency,
                "money_type": invoice.money_type,
                "is_fiscalized": invoice.is_fiscalized,
                "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
                "line_items_count": len(line_items)
            }
            detailed_breakdown["invoice_details"].append(invoice_detail)

        # Round all amounts to 2 decimal places
        for currency_data in detailed_breakdown["by_currency"].values():
            currency_data["total_amount"] = round(currency_data["total_amount"], 2)
            currency_data["total_tax"] = round(currency_data["total_tax"], 2)
        
        for payment_data in detailed_breakdown["by_payment_method"].values():
            payment_data["total_amount"] = round(payment_data["total_amount"], 2)
        
        for receipt_data in detailed_breakdown["by_receipt_type"].values():
            receipt_data["total_amount"] = round(receipt_data["total_amount"], 2)
        
        for tax_data in detailed_breakdown["by_tax_type"].values():
            tax_data["total_amount"] = round(tax_data["total_amount"], 2)
            tax_data["total_tax"] = round(tax_data["total_tax"], 2)

        response_data = {
            "device_id": str(device_id),
            "fiscal_day_no": target_fiscal_day_no,
            "fiscal_day_open": fiscal_day.fiscal_day_open,
            "fiscal_day_status": "OPEN" if fiscal_day.is_open else "CLOSED",
            "total_invoices": len(invoices),
            "detailed_breakdown": detailed_breakdown
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": format_exc()
        }
        current_app.logger.error(f"Detailed fiscal counters error: {error_details}")
        return jsonify(error_details), 500


@api.route('/fiscal_counters/<device_id>/<fiscal_day_no>', methods=['GET'])
def get_fiscal_counters_by_day(device_id, fiscal_day_no):
    """
    Get fiscal counters for a specific device and fiscal day number.
    
    This endpoint allows explicit querying by device ID and fiscal day number.
    
    Parameters:
        device_id (str): Device identifier (path parameter)
        fiscal_day_no (int): Fiscal day number (path parameter)
        
    Returns:
        JSON response with fiscal counter data
    """
    try:
        # Convert fiscal day number to int
        try:
            target_fiscal_day_no = int(fiscal_day_no)
        except ValueError:
            return jsonify({"error": "Invalid fiscal day number. Must be an integer."}), 400
        
        # Load device config
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Get fiscal day record
        fiscal_day = FiscalDay.query.filter_by(
            device_id=device.device_id,
            fiscal_day_no=target_fiscal_day_no
        ).first()
        
        if not fiscal_day:
            return jsonify({
                "error": f"Fiscal day {target_fiscal_day_no} not found for device {device_id}",
                "device_id": device_id,
                "fiscal_day_no": target_fiscal_day_no
            }), 404

        # Get all invoices for this device and fiscal day
        invoices = Invoice.query.filter_by(
            device_id=str(device_id),
            fiscal_day_number=str(target_fiscal_day_no)
        ).all()

        # Generate fiscal counters using existing utility
        from utils.generate_counters import generate_counters
        
        # Read private key for signature generation
        with open(device.key_path, 'rb') as key_file:
            private_key_data = key_file.read()
        
        # Generate counters
        counters_data = generate_counters(
            private_key=private_key_data,
            device_id=str(device_id),
            date_string=fiscal_day.fiscal_day_open,
            close_day_date=fiscal_day.fiscal_day_open,
            fiscal_day_no=target_fiscal_day_no
        )
        
        # Update fiscal counter data (apply ZIMRA-specific formatting)
        updated_counters = update_fiscal_counter_data(counters_data['fiscalDayCounters'])
        
        # Calculate summary statistics
        total_receipts = len(invoices)
        total_amount = sum(float(invoice.receipt_total or 0) for invoice in invoices)
        
        # Group counters by type for better organization
        counters_by_type = {}
        for counter in updated_counters:
            counter_type = counter.get('fiscalCounterType', 'Unknown')
            if counter_type not in counters_by_type:
                counters_by_type[counter_type] = []
            counters_by_type[counter_type].append(counter)
        
        # Group counters by currency
        counters_by_currency = {}
        for counter in updated_counters:
            currency = counter.get('fiscalCounterCurrency', 'Unknown')
            if currency not in counters_by_currency:
                counters_by_currency[currency] = []
            counters_by_currency[currency].append(counter)
        
        # Prepare response data
        response_data = {
            "device_id": str(device_id),
            "fiscal_day_no": target_fiscal_day_no,
            "fiscal_day_open": fiscal_day.fiscal_day_open,
            "fiscal_day_status": "OPEN" if fiscal_day.is_open else "CLOSED",
            "total_receipts": total_receipts,
            "total_amount": round(total_amount, 2),
            "receipt_counter": counters_data.get('receiptCounter', 0),
            "fiscal_counters": updated_counters,
            "counters_by_type": counters_by_type,
            "counters_by_currency": counters_by_currency,
            "summary": {
                "sale_counters": len([c for c in updated_counters if c.get('fiscalCounterType') == 'SaleByTax']),
                "tax_counters": len([c for c in updated_counters if c.get('fiscalCounterType') == 'SaleTaxByTax']),
                "balance_counters": len([c for c in updated_counters if c.get('fiscalCounterType') == 'BalanceByMoneyType']),
                "credit_note_counters": len([c for c in updated_counters if 'CreditNote' in c.get('fiscalCounterType', '')]),
                "debit_note_counters": len([c for c in updated_counters if 'DebitNote' in c.get('fiscalCounterType', '')])
            },
            "query_info": {
                "device_id": device_id,
                "fiscal_day_no": target_fiscal_day_no,
                "total_counters": len(updated_counters),
                "currencies": list(counters_by_currency.keys())
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": format_exc()
        }
        current_app.logger.error(f"Fiscal counters query error: {error_details}")
        return jsonify(error_details), 500


@api.route('/fiscal_counters/<device_id>/latest', methods=['GET'])
def get_fiscal_counters_latest(device_id):
    """
    Get fiscal counters for a specific device using the latest (current) fiscal day.
    
    This endpoint automatically uses the latest fiscal day number for the device.
    
    Parameters:
        device_id (str): Device identifier (path parameter)
        
    Returns:
        JSON response with fiscal counter data for the latest fiscal day
    """
    try:
        # Load device config
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Get the latest fiscal day number (highest number, regardless of open/closed status)
        try:
            target_fiscal_day_no = get_latest_fiscal_number(device_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404

        # Get fiscal day record
        fiscal_day = FiscalDay.query.filter_by(
            device_id=device.device_id,
            fiscal_day_no=target_fiscal_day_no
        ).first()
        
        if not fiscal_day:
            return jsonify({
                "error": f"Latest fiscal day {target_fiscal_day_no} not found for device {device_id}",
                "device_id": device_id,
                "fiscal_day_no": target_fiscal_day_no
            }), 404

        # Get all invoices for this device and fiscal day
        invoices = Invoice.query.filter_by(
            device_id=str(device_id),
            fiscal_day_number=str(target_fiscal_day_no)
        ).all()

        # Generate fiscal counters using existing utility
        from utils.generate_counters import generate_counters
        
        # Read private key for signature generation
        with open(device.key_path, 'rb') as key_file:
            private_key_data = key_file.read()
        
        # Generate counters
        counters_data = generate_counters(
            private_key=private_key_data,
            device_id=str(device_id),
            date_string=fiscal_day.fiscal_day_open,
            close_day_date=fiscal_day.fiscal_day_open,
            fiscal_day_no=target_fiscal_day_no
        )
        
        # Update fiscal counter data (apply ZIMRA-specific formatting)
        updated_counters = update_fiscal_counter_data(counters_data['fiscalDayCounters'])
        
        # Calculate summary statistics
        total_receipts = len(invoices)
        total_amount = sum(float(invoice.receipt_total or 0) for invoice in invoices)
        
        # Group counters by type for better organization
        counters_by_type = {}
        for counter in updated_counters:
            counter_type = counter.get('fiscalCounterType', 'Unknown')
            if counter_type not in counters_by_type:
                counters_by_type[counter_type] = []
            counters_by_type[counter_type].append(counter)
        
        # Group counters by currency
        counters_by_currency = {}
        for counter in updated_counters:
            currency = counter.get('fiscalCounterCurrency', 'Unknown')
            if currency not in counters_by_currency:
                counters_by_currency[currency] = []
            counters_by_currency[currency].append(counter)
        
        # Prepare response data
        response_data = {
            "device_id": str(device_id),
            "fiscal_day_no": target_fiscal_day_no,
            "fiscal_day_open": fiscal_day.fiscal_day_open,
            "fiscal_day_status": "OPEN" if fiscal_day.is_open else "CLOSED",
            "total_receipts": total_receipts,
            "total_amount": round(total_amount, 2),
            "receipt_counter": counters_data.get('receiptCounter', 0),
            "fiscal_counters": updated_counters,
            "counters_by_type": counters_by_type,
            "counters_by_currency": counters_by_currency,
            "summary": {
                "sale_counters": len([c for c in updated_counters if c.get('fiscalCounterType') == 'SaleByTax']),
                "tax_counters": len([c for c in updated_counters if c.get('fiscalCounterType') == 'SaleTaxByTax']),
                "balance_counters": len([c for c in updated_counters if c.get('fiscalCounterType') == 'BalanceByMoneyType']),
                "credit_note_counters": len([c for c in updated_counters if 'CreditNote' in c.get('fiscalCounterType', '')]),
                "debit_note_counters": len([c for c in updated_counters if 'DebitNote' in c.get('fiscalCounterType', '')])
            },
            "query_info": {
                "device_id": device_id,
                "fiscal_day_no": target_fiscal_day_no,
                "total_counters": len(updated_counters),
                "currencies": list(counters_by_currency.keys()),
                "is_latest": True,
                "note": "Using latest fiscal day number"
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": format_exc()
        }
        current_app.logger.error(f"Latest fiscal counters query error: {error_details}")
        return jsonify(error_details), 500