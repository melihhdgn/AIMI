import socket

SERVER_IP = "192.168.1.103"  # 2. PC'nin IP adresi
SERVER_PORT = 8055

def send_error_code(error_code, mod="oblik"):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            msg = f"{mod}:{error_code}"
            s.sendall(msg.encode())
            print(f"Gönderildi: {msg}")
    except Exception as e:
        print("Socket Hatası:", e)