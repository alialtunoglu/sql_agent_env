import sys
import os

# src modülünü bulabilmesi için path eklemesi (bazen gereklidir)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import build_agent

def main():
    print("SQL Ajanı Başlatılıyor...")
    
    try:
        agent = build_agent()
        
        while True:
            user_input = input("\nSorunuzu yazın (Çıkmak için 'q'): ")
            if user_input.lower() == 'q':
                break
            
            print("\nYanıt aranıyor...\n")
            try:
                response = agent.invoke(user_input)
                print(f"CEVAP: {response['output']}")
            except Exception as e:
                print(f"Hata oluştu: {e}")
                
    except Exception as e:
        print(f"Kritik Hata: {e}")

if __name__ == "__main__":
    main()