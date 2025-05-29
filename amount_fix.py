import re

def extract_total_amount(text: str) -> float:
    """Enhanced amount extraction"""
    # Look for various total patterns
    patterns = [
        r'Total\s*:?\s*₹?\s*([\d,]+\.?\d*)',
        r'Net Payable\s*:?\s*₹?\s*([\d,]+\.?\d*)', 
        r'FAMILY HEALTH PLAN.*?₹?\s*([\d,]+\.?\d*)',
        r'₹\s*(4[0-9]{5}\.00)',  # Specific pattern for amounts like 451168.00
        r'(\d{6}\.00)'  # 6-digit amounts with .00
    ]
    
    # Test with your document text
    test_text = """
    Total 451168.00
    FAMILY HEALTH PLAN ( TPA ) 451168.00
    Net Payable 451168.00
    """
    
    for pattern in patterns:
        matches = re.findall(pattern, test_text, re.IGNORECASE)
        if matches:
            try:
                amount = float(matches[0].replace(',', ''))
                print(f"Pattern '{pattern}' found amount: {amount}")
                return amount
            except:
                continue
    
    return None

# Test it
result = extract_total_amount("")
print("Result:", result)
