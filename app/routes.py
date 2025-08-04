from flask import Blueprint, jsonify, request, current_app, send_from_directory, render_template_string
from app.models import DeviceInfo, FiscalDay, Invoice, InvoiceLineItem, DeviceBranchAddress, DeviceBranchContact
from app import db
from utils.close_day_string_utilts import generate_close_day_string, add_zeros
from utils.date_utils import  get_close_day_string_date
from utils.generate_counters import generate_counters
from utils.update_closeday import update_fiscal_counter_data
from utils.invoice_utils import (
    invoice_exists, get_fiscal_day_counter, get_global_number, calculate_tax_summary,
    calculate_total_sales_amount_with_tax, create_invoice_line_items, create_invoice,
    update_fiscalized_invoice, qr_string_generator, base64_to_hex_md5, get_device_config,
    qr_date, receipt_date_print
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

    fiscal_day = FiscalDay.query.filter_by(device_id= device.id, is_open=True).first()
    current_app.logger.debug(f"fiscalDay: no {fiscal_day.fiscal_day_no}")
    if not fiscal_day:
        raise ValueError(f"No open fiscal day found for device_id: {device_id}")

    if not fiscal_day.fiscal_day_no:
        raise ValueError(f"fiscal_day_no not set for open fiscal day of device_id: {device_id}")

  #  return
    return fiscal_day.fiscal_day_no





def get_device_config(device_id):
    """
    Replace this with actual DB call or ORM fetch.
    """
    # Simulate data (would come from DB in real-world case)
    return {
        "certificate": os.path.abspath(f"certs/{device_id}.pem"),
        "key": os.path.abspath(f"certs/{device_id}.key"),
        "model_name": "Server",
        "model_version_number": "v1"
    }


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
    #device_config = DeviceInfo.query.filter_by(device_id=device_id).first()
    device_config = get_device_config(device_id)
    cert_path = device_config["certificate"]
    key_path = device_config["key"]
    if not device_config:
        return jsonify({"error": "Device not found"}), 404

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
    
    Expected payload structure:
    {
        "fiscalDayNo": "123",
        "fiscalDayCounters": [
            {
                "fiscalCounterType": "TaxByTax",
                "fiscalCounterTaxPercent": 15.0,
                "fiscalCounterTaxID": 1,
                "fiscalCounterCurrency": "USD",
                "fiscalCounterValue": 100.00,
                "fiscalCounterMoneyType": "CASH"
            }
        ]
    }
    """
    try:
        # 1. Read and validate posted JSON
        posted_data = request.get_json()
        current_app.logger.debug(f"Received CloseDay payload: {posted_data}")
        
        # Validate required fields according to ZIMRA API specification
        if not posted_data:
            return jsonify({"error": "No payload provided"}), 400
            
        if "fiscalDayNo" not in posted_data:
            return jsonify({"error": "Missing required field: fiscalDayNo"}), 400
            
        if "fiscalDayCounters" not in posted_data:
            return jsonify({"error": "Missing required field: fiscalDayCounters"}), 400
            
        if not isinstance(posted_data["fiscalDayCounters"], list):
            return jsonify({"error": "fiscalDayCounters must be an array"}), 400

        # 2. Load device config
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        cert_path = device.certificate_path
        key_path = device.key_path

        # 3. Get the open fiscal day
        open_fiscal_day = FiscalDay.query.filter_by(device_id=device.device_id, is_open=True).first()
        if not open_fiscal_day:
            return jsonify({"error": "No open fiscal day found for this device"}), 404

        # 4. Validate fiscal day number matches
        expected_fiscal_day_no = str(open_fiscal_day.fiscal_day_no)
        provided_fiscal_day_no = str(posted_data["fiscalDayNo"])
        
        if expected_fiscal_day_no != provided_fiscal_day_no:
            return jsonify({
                "error": "Fiscal day number mismatch", 
                "expected": expected_fiscal_day_no,
                "provided": provided_fiscal_day_no
            }), 400

        # 5. Generate FiscalDayDeviceSignature
        fiscal_close_date = get_close_day_string_date()
        
        # Generate the string to sign
        string_to_sign = generate_close_day_string(
            device_id=str(device_id),
            fiscal_day_no=expected_fiscal_day_no,
            date=fiscal_close_date,
            receipt_close=posted_data
        )
        
        current_app.logger.debug(f"String to sign for CloseDay: {string_to_sign}")

        # Generate the signature using the device's private key
        with open(key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
        
        # Sign the string
        signature = private_key.sign(
            string_to_sign.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Encode signature to base64
        fiscal_day_device_signature = base64.b64encode(signature).decode('utf-8')
        
        # 6. Add the signature to the payload
        close_data = posted_data.copy()
        close_data['fiscalDayDeviceSignature'] = fiscal_day_device_signature
        
        # 7. Prepare secure session with ZIMRA
        session = requests.Session()
        session.cert = (cert_path, key_path)

        # 8. Prepare headers according to ZIMRA API specification
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "DeviceModelName": device.model_name,
            "DeviceModelVersion": device.model_version
        }

        # 9. Send request to ZIMRA
        json_data = json.dumps(close_data)
        current_app.logger.debug(f"CloseDay Payload with signature: {json_data}")

        url = f'https://fdmsapitest.zimra.co.zw/Device/v1/{device_id}/CloseDay'
        response = session.post(url, data=json_data, headers=headers, verify=False)

        current_app.logger.debug(f"ZIMRA CloseDay status: {response.status_code}")

        # 10. Process response and update local DB if successful
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
        current_app.logger.debug(f"Received SubmitReceipt payload: {posted_data}")
        
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

        # 2. Load device config
        device = DeviceInfo.query.filter_by(device_id=str(device_id)).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        cert_path = device.certificate_path
        key_path = device.key_path

        # 3. Get the open fiscal day
        open_fiscal_day = FiscalDay.query.filter_by(device_id=device.device_id, is_open=True).first()
        if not open_fiscal_day:
            return jsonify({"error": "No open fiscal day found for this device"}), 404

        # 4. Calculate receipt amounts from receiptLines and receiptTaxes
        receipt_total = float(receipt_data["receiptTotal"])
        receipt_tax_amount = 0.0
        
        # Calculate tax amount from receiptTaxes if available
        if "receiptTaxes" in receipt_data:
            for tax in receipt_data["receiptTaxes"]:
                receipt_tax_amount += float(tax.get("taxAmount", 0))
        
        # Calculate net amount (total - tax)
        receipt_amount = receipt_total - receipt_tax_amount
        
        # 5. Generate ReceiptDeviceSignature
        receipt_number = str(receipt_data["invoiceNo"])
        receipt_date_time = receipt_data["receiptDate"]
        
        # Generate the string to sign for receipt
        string_to_sign = generate_receipt_string(
            device_id=str(device_id),
            receipt_number=receipt_number,
            receipt_date_time=receipt_date_time,
            receipt_amount=str(receipt_amount),
            receipt_tax_amount=str(receipt_tax_amount),
            receipt_total_amount=str(receipt_total)
        )
        
        current_app.logger.debug(f"String to sign for SubmitReceipt: {string_to_sign}")

        # Generate the signature using the device's private key
        with open(key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
        
        # Sign the string
        signature = private_key.sign(
            string_to_sign.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Encode signature to base64
        receipt_device_signature = base64.b64encode(signature).decode('utf-8')
        
        # 6. Add the signature to the receipt data (following Django pattern)
        # Create the signature object structure like in Django
        # Generate hash from the string that was signed
        hash_obj = hashes.Hash(hashes.SHA256())
        hash_obj.update(string_to_sign.encode('utf-8'))
        hash_value = hash_obj.finalize()
        
        receipt_device_signature_obj = {
            "hash": base64.b64encode(hash_value).decode('utf-8'),
            "signature": receipt_device_signature
        }
        
        # Add signature to receipt data
        receipt_data_with_signature = receipt_data.copy()
        receipt_data_with_signature['receiptDeviceSignature'] = receipt_device_signature_obj
        
        # Create the full payload structure like in Django
        full_payload = {
            "receipt": receipt_data_with_signature
        }
        
        # 7. Prepare secure session with ZIMRA
        session = requests.Session()
        session.cert = (cert_path, key_path)

        # 8. Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "DeviceModelName": device.model_name,
            "DeviceModelVersion": device.model_version
        }

        # 9. Send request to ZIMRA (following Django pattern)
        url = f'https://fdmsapitest.zimra.co.zw/Device/v1/{device_id}/SubmitReceipt'
        
        # Use the same payload structure as the working Django code
        json_data = json.dumps(full_payload)
        current_app.logger.debug(f"SubmitReceipt Payload (Django pattern): {json_data}")
        
        # Send the request
        response = session.post(url, data=json_data, headers=headers, verify=False)
        current_app.logger.debug(f"ZIMRA SubmitReceipt status: {response.status_code}")
        
        # 10. Process successful response and update database
        if response.status_code == 200:
            zimra_response = response.json()
            current_app.logger.debug(f"#################################################")
            current_app.logger.debug(f"ZIMRA Response status Ok: {zimra_response}")
            current_app.logger.debug(f"#################################################")
            
            try:
                # Check for duplicate invoice
                if invoice_exists(device_id=str(device_id), invoice_id=str(receipt_data["invoiceNo"])):
                    return jsonify({"error": "Duplication Of Invoice Number"}), 400
                
                # Get device configuration
                config_data = get_device_config(str(device_id))
                
                # Calculate counters
                counter = get_fiscal_day_counter(device_id=str(device_id), fiscal_open_date_time=open_fiscal_day.fiscal_day_open)
                global_number = get_global_number(str(device_id))
                
                if global_number == -1:
                    return jsonify({"error": "Global Value cannot be negative"}), 400
                
                # Calculate tax summary
                tax_summary = calculate_tax_summary(receipt_data.get('receiptLines', []))
                filtered_taxes = [tax for tax in tax_summary.values() if tax['taxCode'] is not None and tax['taxID'] is not None]
                
                # Calculate total
                receipt_total = calculate_total_sales_amount_with_tax(filtered_taxes)
                
                # Create invoice data
                invoice_data = {
                    'invoice_id': receipt_data["invoiceNo"],
                    'device_id': str(device_id),
                    'receipt_currency': receipt_data.get('receiptCurrency', 'USD'),
                    'money_type': 'Cash',  # Default to Cash
                    'receipt_type': receipt_data["receiptType"],
                    'receipt_total': receipt_total,
                    'line_items': receipt_data.get('receiptLines', [])
                }
                
                # Create invoice in database
                created_invoice = create_invoice(invoice_data)
                
                # Generate QR code
                qr_string = qr_string_generator(
                    device_id=str(device_id),
                    qr_url="https://fdmstest.zimra.co.zw/",  
                    receipt_date=qr_date(),
                    reciept_global_no=global_number + 1,
                    reciept_signature=receipt_device_signature  # Use the signature directly, not the hash
                )
                
                # Generate verification code (convert signature to hex MD5)
                verification_string = base64_to_hex_md5(receipt_device_signature)
             
                
                # Prepare update data
                update_data = {
                    'invoice_id': receipt_data["invoiceNo"],
                    'zimra_receipt_number': str(zimra_response.get('receiptID', '')),
                    'operation_id': str(zimra_response.get('operationID', '')),
                    'qr_code_string': qr_string,
                    'verification_number': verification_string,
                    'hash_string': receipt_device_signature_obj['hash'],
                    'is_fiscalized': True,
                    'receipt_counter': counter + 1,
                    'receipt_global_no': global_number + 1,
                    'fiscal_day_number': str(open_fiscal_day.fiscal_day_no),
                    'receipt_notes': receipt_data.get('receiptNotes', ''),
                    'tax_payer_name': config_data.get('taxPayerName', ''),
                    'tax_payer_tin': str(config_data.get('taxPayerTIN', '')),
                    'vat_number': str(config_data.get('vatNumber', '')),
                    'device_branch_name': str(config_data.get('deviceBranchName', '')),
                    'device_branch_address': config_data.get('deviceBranchAddress', {}),
                    'device_branch_contact': config_data.get('deviceBranchContacts', {})
                }
                
                # Update invoice with fiscalization data
                update_fiscalized_invoice(update_data)
                
                # Prepare response data
                response_data = {
                    "taxPayerName": config_data.get('taxPayerName', ''),
                    "taxPayerTIN": config_data.get('taxPayerTIN', ''),
                    "vatNumber": config_data.get('vatNumber', ''),
                    "deviceBranchName": config_data.get('deviceBranchName', ''),
                    "deviceBranchAddress": config_data.get('deviceBranchAddress', {}),
                    "deviceBranchContacts": config_data.get('deviceBranchContacts', {}),
                    "taxCode": "A",
                    "qrUrl": config_data.get('qrUrl', 'https://fdmstest.zimra.co.zw/'),
                    "deviceSerialNo": config_data.get('deviceSerialNo', ''),
                    "receiptCounter": counter + 1,
                    "receiptGlobalNo": global_number + 1,
                    "fiscalDayNumber": str(open_fiscal_day.fiscal_day_no),
                    "receiptID": zimra_response.get('receiptID', ''),
                    "invoiceNumber": receipt_data["invoiceNo"],
                    "deviceID": str(device_id),
                    "date": receipt_date_print(),
                    "taxPercentage": "15",
                    "qrString": qr_string,
                    "verificationCode": verification_string,
                }
                
                return jsonify(response_data), 200
                
            except Exception as e:
                current_app.logger.error(f"Error processing successful response: {str(e)}")
                return jsonify({"error": "Database operation failed", "details": str(e)}), 500
        else:
            try:
                error_data = response.json()
                current_app.logger.debug(f"#################################################")
                current_app.logger.debug(f"ZIMRA Error Response: {error_data}")
                current_app.logger.debug(f"#################################################")
                return jsonify({"error": "ZIMRA request failed", "status_code": response.status_code, "details": error_data}), response.status_code
            except:
                current_app.logger.debug(f"#################################################")
                current_app.logger.debug(f"ZIMRA Error Response (raw): {response.content}")
                current_app.logger.debug(f"#################################################")
                return jsonify({"error": "ZIMRA request failed", "status_code": response.status_code}), response.status_code
        
        for i, payload in enumerate(payload_variations):
            json_data = json.dumps(payload)
            current_app.logger.debug(f"Trying payload variation {i+1}: {json_data}")
            
            response = session.post(url, data=json_data, headers=headers, verify=False)
            current_app.logger.debug(f"ZIMRA SubmitReceipt status (variation {i+1}): {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                current_app.logger.debug(f"#################################################")
                current_app.logger.debug(f"ZIMRA Response status Ok: {data}")
                current_app.logger.debug(f"#################################################")
                return jsonify(data), 200



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
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Request failed"}), response.status_code

    except Exception as e:
        current_app.logger.error(f"Error in get_config: {e}")
        return jsonify({"error": str(e)}), 400


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