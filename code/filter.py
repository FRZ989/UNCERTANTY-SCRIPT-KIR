import json
import os
from typing import List, Dict, Any

def concatenate_sequential_entities_fixed(input_filename: str, output_filename: str, remove_empty: bool = False):
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"error'{input_filename}' blev ikke fundet.")
        return
    except json.JSONDecodeError:
        print(f"error'{input_filename}' er ikke gyldig JSON.")
        return

    processed_data = []

    for item in data:
        # Tjekker, om der er forudsigelser at behandle
        if 'predictions' not in item or not item['predictions']:
            if remove_empty:
                continue
            processed_data.append(item)
            continue
        
        predictions_block = item['predictions'][0]
        original_results = predictions_block.get('result', [])
        
        if not original_results:
            if remove_empty:
                continue
            processed_data.append(item)
            continue

        # Hent den fulde tekst
        full_text = item['data'].get('text', '') 
        if not full_text:
            processed_data.append(item)
            continue

        # Sorter resultaterne efter start-indeks
        original_results.sort(key=lambda x: x['value']['start'])
        
        merged_results = []
        current_entity = None
        
        for entity in original_results:
            value = entity['value']
            current_label = value.get('labels', [None])[0]
            
            if not current_label:
                continue

            if current_entity:
                prev_value = current_entity['value']
                prev_label = prev_value.get('labels', [None])[0]

                # Tjek for samme label og en lille eller ingen afstand (0, 1 eller 2 tegn)
                gap = value['start'] - prev_value['end']
                
                if current_label == prev_label and gap >= 0 and gap <= 2:
                    
                    #CONCAT
                    current_entity['value']['end'] = value['end']
                    
                    current_entity['value']['text'] = full_text[
                        current_entity['value']['start'] : current_entity['value']['end']
                    ]

                    # PREPROCESSING med score
                    if 'score' in current_entity['value']:
                        del current_entity['value']['score']
                        
                else:
                    merged_results.append(current_entity)
                    current_entity = entity.copy() 
            else:
                # Start den første entitet
                current_entity = entity.copy()
        
        # Tilføj den sidste entitet
        if current_entity:
            merged_results.append(current_entity)
            
        if remove_empty and not merged_results:
            continue
            
        item['predictions'][0]['result'] = merged_results
        processed_data.append(item)

    # Gem det opdaterede data
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)
    
    print(f"Filter påført og outputter til: '{output_filename}'.")
    if remove_empty and len(data) != len(processed_data):
        print(f"   ({len(data) - len(processed_data)} tomme objekter blev fjernet fra Label Studio importfilen.)")


def main():
    # Inputfiler
    RAW_FILE = 'model-predictions/predictions.json'
    LS_IMPORT_FILE = 'labelstudio/import/predictions_import.json'

    concatenate_sequential_entities_fixed(
        input_filename=RAW_FILE, 
        output_filename=RAW_FILE,
        remove_empty=False
    )
    
    concatenate_sequential_entities_fixed(
        input_filename=LS_IMPORT_FILE, 
        output_filename=LS_IMPORT_FILE,
        remove_empty=True
    )

if __name__ == "__main__":
    main()