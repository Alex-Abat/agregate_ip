import ipaddress
import re
import time

IN_FILE = './ip_list.txt'       # Имя входного файла
OUTPUT_FILE = './subnets.txt'   # Имя выходного файла

IP_RE = re.compile(r'(\d{1,3}(?:\.\d{1,3}){3})')    # Регулярное выражение для поиска IP-адресов в строке

START_TIME = time.time()

def ip_to_int(ipstr: str) -> int:
    '''
    Преобразование IP-адреса из строки в целое число.
        - ipstr: Строка с IP-адресом.
    '''
    return int(ipaddress.IPv4Address(ipstr.strip()))

def int_to_ip(i: int) -> str:
    '''
    Преобразование IP-адреса из целого числа в строку.
        - i: Целое число с IP-адресом.
    '''
    return str(ipaddress.IPv4Network(i))

def read_ip_list() -> list:
    '''
    Чтение IP-адресов из входного файла.
    Возвращает список IP-адресов в виде целых чисел.
    '''
    ip_list = set()
    with open(IN_FILE, 'r') as f:
        
        for linenum, line in enumerate(f, 1):
            ip = IP_RE.search(line).group(1)  # Извлечение IP-адреса из строки
            if ip:
                ip_list.add(ip_to_int(ip))
            
    print(f'\rПрочитано строк {linenum:,} | Уникальных IP: {len(ip_list):,}', flush=True)
                    
    ip_list = list(ip_list)
    ip_list.sort()
    
    return ip_list

import ipaddress, time

def agregation_ips(ip_list: list[int], gap_threshold=2600, max_round_k=21) -> list:
    """
    Агрегация IP-адресов в подсети.
    Возвращает список агрегированных подсетей в формате ipaddress.IPv4Network.
        - ip_list: Список IP-адресов в виде целых чисел.
        - gap_threshold: Максимальный разрыв между IP-адресами для объединения в один диапазон.
        - max_round_k: Максимальное значение k для округления границ диапазона.
    """
    if not ip_list:
        return []

    subnets = []
    start_ip = ip_list[0]
    end_ip = start_ip

    # --- Поиск диапазонов ---
    for ip in ip_list[1:]:
        if ip <= end_ip + gap_threshold:
            end_ip = ip
        else:
            subnets.append((start_ip, end_ip))
            start_ip = ip
            end_ip = ip
    subnets.append((start_ip, end_ip))

    print(f"Диапазонов обнаружено: {len(subnets):,}")

    aggregated = []

    # --- Преобразование диапазонов в подсети ---
    for start, end in subnets:

        length = end - start + 1

        # Выбираем k динамически:
        # чем больше диапазон, тем больше можно округлить
        if length < 256:
            k = 8
        elif length < 1024:
            k = 11
        elif length < 2048:
            k = 12
        elif length < 4096:
            k = 14
        elif length < 8192:
            k = 17
        elif length < 16384:
            k = 18
        else:
            k = 20  
        k = min(k, max_round_k)

        # Округляем границы диапазона
        start = start & ~((1 << k) - 1)
        end = end | ((1 << k) - 1)

        networks = ipaddress.summarize_address_range(
            ipaddress.IPv4Address(start),
            ipaddress.IPv4Address(end)
        )
        aggregated.extend(networks)

    # --- Первая фаза слияния ---
    aggregated = list(ipaddress.collapse_addresses(aggregated))

    # --- Дополнительная фаза слияния ---
    aggregated = list(ipaddress.collapse_addresses(sorted(aggregated, key=lambda n: int(n.network_address))))
    print(f"После слияния: {len(aggregated):,} подсетей")

    return aggregated

def write_subnets(ip_list: list[ipaddress.IPv4Network]):
    '''
    Запись агрегированных подсетей в выходной файл.
        - ip_list: Список подсетей в формате ipaddress.IPv4Network.
    '''
    with open(OUTPUT_FILE, 'w') as f:
        for ip in ip_list:
            f.write(int_to_ip(ip) + '\n')

            
        elapsed = time.time() - START_TIME        
        print(f'Результат сохранеy в {OUTPUT_FILE}')
        print(f'Подсетей записано: {ip_list.index(ip)+1:,}') 
        print(f'Время обработки: {elapsed:6.1f} сек.')

def main():
    ip_list = read_ip_list()
    ip_list = agregation_ips(ip_list)
    write_subnets(ip_list)
    
if __name__ == '__main__':
    main()