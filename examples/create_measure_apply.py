import json
import sys
from src.powerbi_client import PowerBIClient


def main():
    c = PowerBIClient()
    payload_path = 'artifacts/tmsl_Ventas_Copilot.json'
    with open(payload_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    print('Loaded payload from', payload_path)
    try:
        resp = c.apply_tmsl(payload)
        print('APPLY_RESPONSE_OK')
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print('APPLY_ERROR')
        print(str(e))
        return 2


if __name__ == '__main__':
    sys.exit(main())
