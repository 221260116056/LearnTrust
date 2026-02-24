import hashlib
import requests
from django.conf import settings
from django.utils import timezone


def anchor_certificate_to_blockchain(certificate):
    """
    Anchor certificate hash to external blockchain API.
    
    Args:
        certificate: Certificate model instance with certificate_hash
        
    Returns:
        dict: Contains transaction_id and anchor_timestamp on success,
              error message on failure
    """
    try:
        # Prepare the hash data
        hash_data = {
            'hash': certificate.certificate_hash,
            'metadata': {
                'certificate_id': certificate.certificate_id,
                'student_id': certificate.student_id,
                'course_id': certificate.course_id,
                'issued_at': certificate.issued_at.isoformat()
            }
        }
        
        # Send to blockchain anchoring service
        # Replace with your actual blockchain API endpoint
        blockchain_api_url = getattr(settings, 'BLOCKCHAIN_API_URL', 'https://api.blockchain-anchor.com/v1/anchor')
        api_key = getattr(settings, 'BLOCKCHAIN_API_KEY', None)
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        response = requests.post(
            blockchain_api_url,
            json=hash_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Update certificate with blockchain info
            transaction_id = result.get('transaction_id') or result.get('tx_hash')
            anchor_timestamp = timezone.now()
            
            # You may want to store these in the Certificate model
            # certificate.blockchain_tx_id = transaction_id
            # certificate.blockchain_anchor_timestamp = anchor_timestamp
            # certificate.save()
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'anchor_timestamp': anchor_timestamp.isoformat(),
                'certificate_hash': certificate.certificate_hash
            }
        else:
            return {
                'success': False,
                'error': f'Blockchain API returned status {response.status_code}',
                'response': response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def verify_certificate_on_blockchain(certificate_hash, transaction_id):
    """
    Verify that a certificate hash exists on the blockchain.
    
    Args:
        certificate_hash: The SHA256 hash of the certificate
        transaction_id: The blockchain transaction ID
        
    Returns:
        dict: Verification result
    """
    try:
        blockchain_api_url = getattr(settings, 'BLOCKCHAIN_VERIFY_URL', 'https://api.blockchain-anchor.com/v1/verify')
        api_key = getattr(settings, 'BLOCKCHAIN_API_KEY', None)
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        response = requests.get(
            f"{blockchain_api_url}/{transaction_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            stored_hash = result.get('hash')
            
            return {
                'verified': stored_hash == certificate_hash,
                'stored_hash': stored_hash,
                'certificate_hash': certificate_hash,
                'timestamp': result.get('timestamp'),
                'block_number': result.get('block_number')
            }
        else:
            return {
                'verified': False,
                'error': f'Verification failed with status {response.status_code}'
            }
            
    except Exception as e:
        return {
            'verified': False,
            'error': str(e)
        }
