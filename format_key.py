"""
Скрипт для правильного форматирования приватного ключа Firebase для .env файла.
Запустите этот скрипт, чтобы отформатировать ключ и обновить .env файл.
"""

import os
import sys

def format_key_for_env():
    print("=== Форматирование приватного ключа Firebase для .env файла ===\n")
    
    print("Вставьте приватный ключ (начиная с '-----BEGIN PRIVATE KEY-----'):")
    print("(Нажмите Enter, затем Ctrl+D или Ctrl+Z на Windows, когда закончите ввод)")
    
    # Читаем многострочный ввод
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        print("\nОперация отменена.")
        return
    
    if not lines:
        print("Ключ не введен. Операция отменена.")
        return
    
    # Соединяем строки и форматируем ключ
    key = '\n'.join(lines)
    
    # Убираем внешние кавычки и пробелы
    key = key.strip().strip('"\'')
    
    # Проверяем формат ключа
    if not key.startswith('-----BEGIN PRIVATE KEY-----'):
        print("\nПредупреждение: Ключ не начинается с '-----BEGIN PRIVATE KEY-----'")
        print("Это может привести к ошибкам при инициализации Firebase.")
    
    if not (key.endswith('-----END PRIVATE KEY-----') or key.endswith('-----END PRIVATE KEY-----\n')):
        print("\nПредупреждение: Ключ не заканчивается на '-----END PRIVATE KEY-----'")
        print("Это может привести к ошибкам при инициализации Firebase.")
    
    # Форматируем ключ для .env файла (заменяем переносы строк на \n)
    env_key = key.replace('\n', '\\n')
    
    print("\n=== Отформатированный ключ для .env файла ===")
    print(f'FIREBASE_PRIVATE_KEY="{env_key}"')
    
    # Спрашиваем, нужно ли обновить .env файл
    update_env = input("\nОбновить .env файл? (y/n): ").strip().lower()
    
    if update_env == 'y':
        env_file = '.env'
        
        if os.path.exists(env_file):
            # Читаем текущий .env файл
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
            
            # Находим и заменяем строку с приватным ключом
            key_found = False
            with open(env_file, 'w') as f:
                for line in env_lines:
                    if line.startswith('FIREBASE_PRIVATE_KEY='):
                        f.write(f'FIREBASE_PRIVATE_KEY="{env_key}"\n')
                        key_found = True
                    else:
                        f.write(line)
                
                # Если ключ не найден, добавляем его
                if not key_found:
                    f.write(f'\nFIREBASE_PRIVATE_KEY="{env_key}"\n')
            
            print(f"\nФайл {env_file} успешно обновлен!")
        else:
            print(f"\nФайл {env_file} не найден!")
            print("Создайте файл .env и добавьте в него строку с приватным ключом.")
    else:
        print("\nФайл .env не был обновлен.")
        print("Скопируйте отформатированный ключ и вставьте его в файл .env вручную.")

if __name__ == "__main__":
    format_key_for_env() 