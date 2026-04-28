from src.powerbi_client import PowerBIClient
import json

def main():
    client = PowerBIClient()
    try:
        measures = client.get_measures()
    except Exception as e:
        print(json.dumps({'ok': False, 'error': str(e)}))
        return 2
    # Select relevant fields
    out = [{
        'Name': m.get('Name'),
        'Table': m.get('TableName') or m.get('TableID'),
        'Expression': m.get('Expression') or m.get('Formula') or m.get('Definition')
    } for m in measures]
    print(json.dumps({'ok': True, 'count': len(out), 'measures': out}, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
