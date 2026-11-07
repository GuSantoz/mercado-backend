import os
import random
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

class WhatsAppService:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception:
                self.client = None
        else:
            self.client = None
    
    @staticmethod
    def generate_code():
        token_codigo = str(random.randint(1000, 9999))
        return token_codigo
    
    def send_activation_message(self, to_number, code):
        if self.client and self.from_number:
            try:
                message = self.client.messages.create(
                    body=f'Seu código de ativação é: {code}',
                    from_=f'whatsapp:{self.from_number}',
                    to=f'whatsapp:{to_number}'
                )
                print(f'Mensagem enviada via Twilio: SID {message.sid}')
                return
            except Exception as e:
                print(f'Falha ao enviar via Twilio ({e}). Código gerado para ativação: {code}')
        else:
            print(f'=== [WhatsApp Simulado] ===\nCódigo de ativação para {to_number}: {code}\n===========================')