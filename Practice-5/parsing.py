import re
import json
from datetime import datetime

def parse_receipt(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
    
    receipt_data = {}

    store_match = re.search(r'Филиал\s+(.+)', text)
    if store_match:
        receipt_data['store'] = store_match.group(1).strip()
    bin_match = re.search(r'БИН\s+(\d+)', text)
    
    
    
    if bin_match:
        receipt_data['bin'] = bin_match.group(1)
    receipt_num_match = re.search(r'Чек\s+№(\d+)', text)
    if receipt_num_match:
        receipt_data['receipt_number'] = receipt_num_match.group(1)

    datetime_match = re.search(r'Время:\s+(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})', text)
    
    
    if datetime_match:
        receipt_data['datetime'] = datetime_match.group(1)
    payment_match = re.search(r'(Банковская карта|Наличные|Карта):', text)
    if payment_match:
        receipt_data['payment_method'] = payment_match.group(1)
    
    products = []
    total_amount = 0
    product_pattern = r'(\d+)\.\s+(.+?)(?:\n|$)(?:\s+\d+,\d+\s+x\s+[\d\s]+,\d+)?\s*([\d\s]+,\d+)'
    product_matches = re.finditer(product_pattern, text, re.MULTILINE)
    
    for match in product_matches:
        product_num = match.group(1)
        product_name = match.group(2).strip()
        price_str = match.group(3).strip()

        price_clean = price_str.replace(' ', '').replace(',', '.')
        price = float(price_clean)
        
        products.append({
            'number': int(product_num),
            'name': product_name,
            'price': price
        })
        
        total_amount += price
    
    receipt_data['products'] = products
    receipt_data['total'] = total_amount

    all_prices = re.findall(r'([\d\s]+,\d+)', text)

    all_prices_clean = [float(p.replace(' ', '').replace(',', '.')) for p in all_prices]
    
    receipt_data['all_prices'] = all_prices_clean

    product_names = []
    product_name_pattern = r'\d+\.\s+(.+?)(?:\n|$)'
    name_matches = re.finditer(product_name_pattern, text, re.MULTILINE)
    
    for match in name_matches:
        product_names.append(match.group(1).strip())
    
    receipt_data['product_names'] = product_names
    
    return receipt_data

def format_output(receipt_data, output_format='text'):
    if output_format == 'json':
        return json.dumps(receipt_data, indent=2, ensure_ascii=False)
    else:
        output = []
        output.append("=" * 50)
        output.append("RECEIPT PARSER RESULTS")
        output.append("=" * 50)
        
        output.append(f"\nSTORE: {receipt_data.get('store', 'N/A')}")
        output.append(f"BIN: {receipt_data.get('bin', 'N/A')}")
        output.append(f"RECEIPT #: {receipt_data.get('receipt_number', 'N/A')}")
        output.append(f"DATETIME: {receipt_data.get('datetime', 'N/A')}")
        output.append(f"PAYMENT METHOD: {receipt_data.get('payment_method', 'N/A')}")
        
        output.append("\n" + "-" * 50)
        output.append("PRODUCTS:")
        output.append("-" * 50)
        
        for product in receipt_data.get('products', []):
            output.append(f"{product['number']:2d}. {product['name'][:50]}")
            output.append(f"     Price: {product['price']:,.2f}")
        
        output.append("-" * 50)
        output.append(f"TOTAL AMOUNT: {receipt_data.get('total', 0):,.2f}")
        output.append("=" * 50)
        
        return '\n'.join(output)
if __name__ == "__main__":
    filename = "/Users/halel.muslim/VScode/PP-2/Practice-5/raw.txt"
    
    try:
        parsed_data = parse_receipt(filename)
        print(format_output(parsed_data, 'text'))
        with open('receipt_parsed.json', 'w', encoding='utf-8') as f:
            f.write(format_output(parsed_data, 'json'))
        
        print("\nJSON output saved to 'receipt_parsed.json'")
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found in the current directory.")
    except Exception as e:
        print(f"Error parsing receipt: {e}")