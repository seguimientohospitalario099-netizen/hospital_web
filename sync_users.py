from app import supabase
from supabase_auth import AdminUserAttributes

try:
    # 1. Obtener usuarios de la tabla local 'usuarios'
    r = supabase.table('usuarios').select('*').execute()
    local_users = r.data or []
    
    # 2. Obtener usuarios registrados en Supabase Auth
    auth_users = supabase.auth.admin.list_users()
    auth_emails = {u.email.lower() for u in auth_users if u.email}
    
    print(f"Encontrados {len(local_users)} usuarios locales y {len(auth_emails)} usuarios en Supabase Auth.\n")
    
    for u in local_users:
        email = u.get('email')
        if email:
            email_lower = email.lower()
            if email_lower not in auth_emails:
                print(f"Sincronizando '{email_lower}' a Supabase Auth...")
                # Crear el usuario en Supabase Auth con confirmación automática (email_confirm=True)
                supabase.auth.admin.create_user(AdminUserAttributes(
                    email=email,
                    password=u['password'],
                    email_confirm=True
                ))
                print(f"¡Usuario '{email_lower}' sincronizado con éxito!")
            else:
                print(f"El usuario '{email_lower}' ya existe en Supabase Auth.")
                
    print("\nSincronización completada.")
except Exception as e:
    print("Error durante la sincronización:", e)
