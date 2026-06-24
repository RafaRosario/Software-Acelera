"""Gera chaves VAPID para Web Push Notifications.

Execute uma vez, salve as chaves e configure no Railway como variaveis de ambiente.
Gerar novas chaves invalida todas as inscricoes existentes dos dispositivos.

Uso:
    python gerar_vapid.py
"""
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import base64

private_key = ec.generate_private_key(ec.SECP256R1())
private_raw = private_key.private_numbers().private_value.to_bytes(32, "big")
private_b64 = base64.urlsafe_b64encode(private_raw).rstrip(b"=").decode()

public_raw = private_key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
public_b64 = base64.urlsafe_b64encode(public_raw).rstrip(b"=").decode()

print("\n=== CHAVES VAPID GERADAS ===")
print("Adicione estas variaveis no Railway (Settings > Variables):\n")
print(f"VAPID_PRIVATE_KEY={private_b64}")
print(f"VAPID_PUBLIC_KEY={public_b64}")
print("\nIMPORTANTE: Use sempre as mesmas chaves apos configurar.")
print("Gerar novas chaves faz com que os dispositivos precisem re-aceitar a notificacao.\n")
