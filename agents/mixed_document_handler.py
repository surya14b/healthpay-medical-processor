def detect_mixed_document_types(text_content: str) -> list:
    """Detect if a single PDF contains multiple document types"""
    doc_types = []
    text_lower = text_content.lower()
    
    # Bill indicators
    if any(indicator in text_lower for indicator in ['total amount', 'bill of supply', 'net amount', 'gst']):
        doc_types.append('bill')
    
    # Discharge summary indicators  
    if any(indicator in text_lower for indicator in ['discharge summary', 'diagnosis', 'admission', 'chief complaint']):
        doc_types.append('discharge_summary')
    
    return doc_types
