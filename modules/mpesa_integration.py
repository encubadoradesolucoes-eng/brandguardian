"""
Integração com M-Pesa API para Moçambique
Processa pagamentos de assinaturas
"""

import requests
import os
import json
from datetime import datetime
import hashlib
import base64

class MPesaAPI:
    def __init__(self):
        # Credenciais (usar variáveis de ambiente em produção)
        self.api_key = os.getenv('MPESA_API_KEY', '')
        self.public_key = os.getenv('MPESA_PUBLIC_KEY', '')
        self.service_provider_code = os.getenv('MPESA_SERVICE_PROVIDER_CODE', '')
        
        # URLs da API
        self.base_url = os.getenv('MPESA_BASE_URL', 'https://api.vm.co.mz')
        self.c2b_url = f"{self.base_url}/ipg/v1x/c2bPayment/singleStage/"
        
        # Configurações
        self.timeout = 30
    
    def _generate_bearer_token(self):
        """Gera token de autenticação"""
        try:
            # M-Pesa usa Public Key para gerar token
            # Implementação simplificada - ajustar conforme documentação oficial
            auth_string = f"{self.api_key}:{self.public_key}"
            auth_bytes = auth_string.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            return f"Bearer {auth_b64}"
        except Exception as e:
            print(f"Erro ao gerar token: {e}")
            return None
    
    def initiate_c2b_payment(self, amount, phone_number, reference, description="M24 PRO Subscription"):
        """
        Inicia pagamento Customer-to-Business (C2B)
        
        Args:
            amount (float): Valor em MT
            phone_number (str): Número de telefone (formato: 258XXXXXXXXX)
            reference (str): Referência única da transação
            description (str): Descrição do pagamento
        
        Returns:
            dict: Resposta da API com status e detalhes
        """
        
        # Validar número de telefone
        if not phone_number.startswith('258'):
            phone_number = f"258{phone_number.lstrip('0')}"
        
        # Preparar payload
        payload = {
            "input_Amount": str(amount),
            "input_CustomerMSISDN": phone_number,
            "input_Country": "MZB",
            "input_Currency": "MZN",
            "input_ServiceProviderCode": self.service_provider_code,
            "input_ThirdPartyReference": reference,
            "input_TransactionReference": reference,
            "input_PurchasedItemsDesc": description
        }
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": self._generate_bearer_token(),
            "Origin": "*"
        }
        
        try:
            response = requests.post(
                self.c2b_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            result = response.json()
            
            # Processar resposta
            if response.status_code == 201:
                return {
                    'status': 'success',
                    'transaction_id': result.get('output_TransactionID'),
                    'conversation_id': result.get('output_ConversationID'),
                    'response_code': result.get('output_ResponseCode'),
                    'response_desc': result.get('output_ResponseDesc'),
                    'raw_response': result
                }
            else:
                return {
                    'status': 'error',
                    'message': result.get('output_ResponseDesc', 'Erro desconhecido'),
                    'code': result.get('output_ResponseCode'),
                    'raw_response': result
                }
        
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'message': 'Timeout na comunicação com M-Pesa',
                'code': 'TIMEOUT'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erro ao processar pagamento: {str(e)}',
                'code': 'EXCEPTION'
            }
    
    def query_transaction_status(self, transaction_id):
        """
        Consulta status de uma transação
        
        Args:
            transaction_id (str): ID da transação M-Pesa
        
        Returns:
            dict: Status da transação
        """
        # TODO: Implementar consulta de status
        # Endpoint: GET /ipg/v1x/queryTransactionStatus/
        pass
    
    def reverse_transaction(self, transaction_id, amount):
        """
        Reverte uma transação (reembolso)
        
        Args:
            transaction_id (str): ID da transação a reverter
            amount (float): Valor a reverter
        
        Returns:
            dict: Resultado da reversão
        """
        # TODO: Implementar reversão
        # Endpoint: PUT /ipg/v1x/reversal/
        pass


# Função auxiliar para gerar referência única
def generate_payment_reference(user_id, plan_name):
    """Gera referência única para pagamento"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_string = f"M24-{user_id}-{plan_name}-{timestamp}"
    hash_obj = hashlib.md5(unique_string.encode())
    return f"M24{hash_obj.hexdigest()[:12].upper()}"


# Simulador para testes (quando M-Pesa não está disponível)
class MPesaSimulator:
    """Simulador de M-Pesa para desenvolvimento/testes"""
    
    def initiate_c2b_payment(self, amount, phone_number, reference, description="Test"):
        """Simula pagamento bem-sucedido"""
        import random
        
        # Simular 90% de sucesso
        if random.random() < 0.9:
            return {
                'status': 'success',
                'transaction_id': f"SIM{random.randint(100000, 999999)}",
                'conversation_id': f"CONV{random.randint(100000, 999999)}",
                'response_code': 'INS-0',
                'response_desc': 'Request processed successfully (SIMULATED)',
                'raw_response': {
                    'simulated': True,
                    'amount': amount,
                    'phone': phone_number,
                    'reference': reference
                }
            }
        else:
            return {
                'status': 'error',
                'message': 'Saldo insuficiente (SIMULATED)',
                'code': 'INS-13',
                'raw_response': {'simulated': True}
            }
    
    def query_transaction_status(self, transaction_id):
        return {
            'status': 'completed',
            'transaction_id': transaction_id,
            'simulated': True
        }


# Factory para escolher implementação
def get_mpesa_client(use_simulator=False):
    """
    Retorna cliente M-Pesa (real ou simulado)
    
    Args:
        use_simulator (bool): Se True, usa simulador
    
    Returns:
        MPesaAPI ou MPesaSimulator
    """
    if use_simulator or not os.getenv('MPESA_API_KEY'):
        print("⚠️ Usando M-Pesa SIMULADOR (modo desenvolvimento)")
        return MPesaSimulator()
    else:
        print("✅ Usando M-Pesa API REAL")
        return MPesaAPI()
