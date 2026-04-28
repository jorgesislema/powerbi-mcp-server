from src.powerbi_client import PowerBIClient
import json

def main():
    client = PowerBIClient()
    print('Refrescando conexión...')
    print(client.refresh_connection())

    try:
        tables = client.get_tables()
    except Exception as e:
        print('No se pudieron listar tablas:', e)
        tables = []

    if tables:
        # elegir tabla conocida si existe
        preferred = next((t for t in tables if t.get('Name') == 'superstore_procesado'), None)
        table_name = preferred.get('Name') if preferred else tables[0].get('Name')
    else:
        table_name = 'superstore_procesado'

    measure_name = 'funcione'
    dax_expr = '1'

    print(f"Creando/actualizando medida '{measure_name}' en tabla: {table_name}")
    resp = client.create_measure(table_name, measure_name, dax_expr, execute=False)
    print(json.dumps(resp, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
