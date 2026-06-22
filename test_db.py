from app import supabase
try:
    r = supabase.table('ESTABLECIMIENTO_SALUD').select('"IdEstablecimiento","NombreEstablecimiento","CodigoRenipres"').order('"NombreEstablecimiento"').execute()
    print('OK:', len(r.data))
    print(r.data[:1])
except Exception as e:
    print('ERROR:', e)
