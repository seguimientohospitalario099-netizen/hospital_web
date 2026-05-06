import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()

# Inicializamos cliente de Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)
app.secret_key = 'hospital_san_jose_2026'

# ─────────────────────────────────────────────────────────────
# CATÁLOGO DE ESTABLECIMIENTOS (para matching por nombre)
# ─────────────────────────────────────────────────────────────
_ESTABLECIMIENTOS = {
    '00003414': 'HOSPITAL SAN JOSE DE CHINCHA', '00003422': 'CONDORILLO ALTO',
    '00003442': 'SAN AGUSTIN',    '00007015': 'CRUZ BLANCA',
    '00003415': 'ALTO LARAN',     '00003423': 'AYLLOQUE',
    '00003424': 'HUACHINGA',      '00003425': 'CHAVIN',
    '00003416': 'CHINCHA BAJA',   '00003426': 'SANTA ROSA',
    '00003427': 'LURICHINCHA',    '00003417': 'EL CARMEN',
    '00003421': 'TOPARA',         '00003432': 'BALCONCITO',
    '00003419': 'PUEBLO NUEVO',   '00003433': 'SAN ISIDRO',
    '00003434': 'LOS ALAMOS',     '00003435': 'EL SALVADOR',
    '00003436': 'SAN JUAN DE YANAC', '00003437': 'HUAÑUPIZA',
    '00003438': 'SAN PEDRO DE HUACARPANA', '00003439': 'LISCAY',
    '00003440': 'BELLAVISTA',     '00003441': 'VISTA ALEGRE',
    '00003420': 'SUNAMPE',        '00024769': 'TAMBO DE MORA',
    '00003430': 'SAN JOSE',       '00027199': 'NUEVO HORIZONTE',
    '00003428': 'HOJA REDONDA',   '00003429': 'WIRACOCHA',
    '00003418': 'GROCIO PRADO',
}
_NOMBRE_A_CODIGO = {v.upper(): k for k, v in _ESTABLECIMIENTOS.items()}
_cache_est: dict[str, int] = {}   # cache en memoria por request
_cache_pac: dict[str, int] = {}


def _limpiar(val) -> str | None:
    s = str(val).strip() if val is not None else ''
    return s if s not in ('', 'nan', 'NaT', 'None') else None


def _limpiar_fecha(val) -> str | None:
    from datetime import datetime
    v = _limpiar(val)
    if not v: return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y'):
        try: return datetime.strptime(v, fmt).strftime('%Y-%m-%d')
        except ValueError: pass
    try: return pd.Timestamp(val).strftime('%Y-%m-%d')
    except Exception: return None


def _resolver_establecimiento(nombre_excel: str | None):
    """Devuelve (codigo, nombre_canonico) o (None, nombre_excel)."""
    if not nombre_excel: return None, None
    up = nombre_excel.strip().upper()
    if up in _NOMBRE_A_CODIGO:
        c = _NOMBRE_A_CODIGO[up]
        return c, _ESTABLECIMIENTOS[c]
    for nc, c in _NOMBRE_A_CODIGO.items():
        if up in nc or nc in up:
            return c, _ESTABLECIMIENTOS[c]
    return None, nombre_excel


def _upsert_establecimiento(nombre_excel: str | None) -> int | None:
    codigo, nombre = _resolver_establecimiento(nombre_excel)
    if not nombre: return None
    key_c = codigo or nombre
    if key_c in _cache_est: return _cache_est[key_c]
    if codigo:
        r = supabase.table('ESTABLECIMIENTO_SALUD').select('"IdEstablecimiento"').eq('"CodigoRenipres"', codigo).execute()
    else:
        r = supabase.table('ESTABLECIMIENTO_SALUD').select('"IdEstablecimiento"').eq('"NombreEstablecimiento"', nombre).execute()
    if r.data:
        id_est = r.data[0]['IdEstablecimiento']
    else:
        d = {'NombreEstablecimiento': nombre}
        if codigo: d['CodigoRenipres'] = codigo
        id_est = supabase.table('ESTABLECIMIENTO_SALUD').insert(d).execute().data[0]['IdEstablecimiento']
    _cache_est[key_c] = id_est
    return id_est


def _upsert_paciente(dni, nombres, apellidos, fec_naci, genero, direccion, celular) -> int | None:
    if not dni and not nombres: return None
    ck = dni or nombres
    if ck in _cache_pac: return _cache_pac[ck]
    if dni:
        r = supabase.table('Paciente').select('"IdPaciente"').eq('"DNI"', dni).execute()
        if r.data:
            _cache_pac[ck] = r.data[0]['IdPaciente']
            return _cache_pac[ck]
    d = {}
    if nombres:   d['Nombres']       = nombres
    if apellidos: d['Apellidos']     = apellidos
    if dni:       d['DNI']           = dni
    if fec_naci:  d['fecNacimiento'] = fec_naci
    if genero:    d['Genero']        = genero
    if direccion: d['Direccion']     = direccion
    if celular:   d['Celular']       = celular
    id_pac = supabase.table('Paciente').insert(d).execute().data[0]['IdPaciente']
    _cache_pac[ck] = id_pac
    return id_pac

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form.get('username')
    password = request.form.get('password')

    try:
        response = supabase.table('usuarios').select("*").eq('username', usuario).execute()
        if len(response.data) > 0 and response.data[0]['password'] == password:
            session['user'] = usuario
            session['rol'] = response.data[0]['rol']
            
            if session['rol'] in ['administrador', 'desarrollador']:
                return redirect(url_for('panel_control', seccion='dashboard'))
            return redirect(url_for('inicio_estandar'))
        else:
            flash('Credenciales incorrectas.')
            return redirect(url_for('home'))
    except Exception as e:
        flash('Error de conexión a la base de datos.')
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/panel-de-control')
@app.route('/panel-de-control/<seccion>', methods=['GET', 'POST'])
def panel_control(seccion='dashboard'):
    if 'user' not in session or session.get('rol') not in ['administrador', 'desarrollador']:
        flash('Acceso denegado.')
        return redirect(url_for('home'))

    rol_actual = session.get('rol')
    usuario_actual = session.get('user')

    # Lógica de creación (POST)
    if request.method == 'POST' and seccion == 'gestion-usuarios':
        nuevo_user = request.form.get('nuevo_user')
        nueva_pass = request.form.get('nueva_pass')
        rol_asignado = request.form.get('rol')

        if rol_actual == 'administrador' and rol_asignado == 'administrador':
            flash('Error: Como Administrador no puedes crear otros Administradores.')
        else:
            try:
                existing = supabase.table('usuarios').select("username").eq("username", nuevo_user).execute()
                if len(existing.data) > 0:
                    flash(f'Error: El usuario "{nuevo_user}" ya existe.')
                else:
                    supabase.table('usuarios').insert({
                        "username": nuevo_user,
                        "password": nueva_pass,
                        "rol": rol_asignado,
                        "creado_por": usuario_actual
                    }).execute()
                    flash(f'Usuario "{nuevo_user}" creado con éxito.')
            except Exception as e:
                flash(f'Error al crear el usuario en la BD: {str(e)}')
            
        return redirect(url_for('panel_control', seccion='gestion-usuarios'))

    # Lógica para obtener listado de la base de datos
    try:
        response = supabase.table('usuarios').select("*").execute()
        datos_completos = response.data
    except Exception as e:
        datos_completos = []
        flash(f'Aún no hay usuarios o error: {str(e)}')

    usuarios_filtrados = {}
    for fila in datos_completos:
        nombre = fila['username']
        # Lógica de control de acceso: los admins solo ven a los que crearon, el dev ve todos
        if rol_actual == 'desarrollador' or fila.get('creado_por') == usuario_actual or nombre == usuario_actual:
            usuarios_filtrados[nombre] = {
                'pass': fila['password'],
                'rol': fila['rol'],
                'creado_por': fila.get('creado_por')
            }

    # ── Consulta de pacientes desde las tablas normalizadas ──
    try:
        resp = supabase.table('ATENCIONES').select(
            '"IdAtencion", "NumAtencion", "Seguro", "Lote", "NumFua", "FechaAtencion",'
            'Paciente("IdPaciente", "Nombres", "Apellidos", "DNI", "fecNacimiento", "Genero", "Direccion", "Celular"),'
            'ESTABLECIMIENTO_SALUD("NombreEstablecimiento", "CodigoRenipres"),'
            'EVALUACIONES_CLINICAS("Dx", "PresionA", "Hta", "Dm2")'
        ).limit(300).execute()

        pacientes_lista = []
        for aten in resp.data:
            pac  = aten.get('Paciente')              or {}
            est  = aten.get('ESTABLECIMIENTO_SALUD') or {}
            evals = aten.get('EVALUACIONES_CLINICAS') or []
            ev   = evals[0] if evals else {}
            pacientes_lista.append({
                'id_atencion':     aten.get('IdAtencion'),
                'nombres':         pac.get('Nombres', '') or '',
                'apellidos':       pac.get('Apellidos', '') or '',
                'dni':             pac.get('DNI', '') or '',
                'fec_naci':        pac.get('fecNacimiento', '') or '',
                'genero':          pac.get('Genero', '') or '',
                'direccion':       pac.get('Direccion', '') or '',
                'celular':         pac.get('Celular', '') or '',
                'establecimiento': est.get('NombreEstablecimiento', '') or '',
                'seguro':          aten.get('Seguro', '') or '',
                'fecha_atencion':  aten.get('FechaAtencion', '') or '',
                'num_atencion':    aten.get('NumAtencion', '') or '',
                'dx':              ev.get('Dx', '') or '',
                'presion':         ev.get('PresionA', '') or '',
                'hta':             ev.get('Hta', '') or '',
                'dm2':             ev.get('Dm2', '') or '',
            })
        # Ordenar por apellidos
        pacientes_lista.sort(key=lambda x: x.get('apellidos', '') or '')
    except Exception as e:
        pacientes_lista = []
        flash(f'Error consultando atenciones: {str(e)}')

    return render_template('panel_control.html', seccion=seccion,
                           usuarios_lista=usuarios_filtrados,
                           pacientes_lista=pacientes_lista)

@app.route('/upload_pacientes', methods=['POST'])
def upload_pacientes():
    if 'user' not in session or session.get('rol') not in ['administrador', 'desarrollador']:
        return redirect(url_for('home'))

    if 'file' not in request.files:
        flash("Error: No se subió ningún archivo Excel.")
        return redirect(url_for('panel_control', seccion='ingreso-pacientes'))

    file = request.files['file']
    if file.filename == '':
        flash("Error: El archivo está vacío.")
        return redirect(url_for('panel_control', seccion='ingreso-pacientes'))

    extensiones_ok = ('.xlsx', '.xls', '.xlsm', '.csv')
    if not any(file.filename.endswith(e) for e in extensiones_ok):
        flash("Formato denegado: usa .xlsx, .xls, .xlsm o .csv")
        return redirect(url_for('panel_control', seccion='ingreso-pacientes'))

    # Limpiar cachés de la sesión de carga
    _cache_est.clear()
    _cache_pac.clear()

    try:
        if file.filename.endswith('.csv'):
            file.stream.seek(0)
            df_raw = pd.read_csv(file, header=None)
            if len(df_raw.columns) <= 1:
                file.stream.seek(0)
                df_raw = pd.read_csv(file, sep=';', header=None)
        else:
            df_raw = pd.read_excel(file, header=None, engine='openpyxl')

        # Auto-detectar fila de encabezados (búsqueda por subcadena)
        header_idx = 0
        for i, row in df_raw.iterrows():
            vals = [str(v).strip().upper() for v in row.values]
            if any('DNI' == v or 'DNI' in v for v in vals) or \
               any('NOMBRES' == v or 'NOMBRES' in v for v in vals):
                header_idx = i
                break

        df_raw.columns = [str(c).strip().upper() for c in df_raw.iloc[header_idx].values]
        df = df_raw.iloc[header_idx + 1:].reset_index(drop=True).fillna('')

        # Detectar columnas disponibles
        def fc(*candidatos):
            for c in candidatos:
                if c.upper() in df.columns: return c.upper()
            return None

        COL_EST      = fc('ESTABLECIMIENTO DE SALUD', 'ESTABLECIMIENTO')
        COL_NOMBRES  = fc('NOMBRES')
        COL_APEL     = fc('APELLIDOS')
        COL_DNI      = fc('DNI')
        COL_FEC      = fc('FEC. NACI', 'FEC NACI', 'FECHA DE NACIMIENTO', 'FEC_NACI')
        COL_GENERO   = fc('GENERO', 'GÉNERO')
        COL_DIR      = fc('DIRECCION', 'DIRECCIÓN')
        COL_CEL      = fc('CELULAR')
        COL_SEGURO   = fc('SEGURO')
        COL_HTA      = fc('HTA')
        COL_DM2      = fc('DM2', 'DM')

        if not COL_DNI and not COL_NOMBRES:
            flash("Error: No se detectaron las columnas DNI o NOMBRES. Verifica el encabezado del Excel.")
            return redirect(url_for('panel_control', seccion='ingreso-pacientes'))

        ok = errores = omitidas = 0

        for _, row in df.iterrows():
            nombres   = _limpiar(row.get(COL_NOMBRES,  '')) if COL_NOMBRES else None
            apellidos = _limpiar(row.get(COL_APEL,     '')) if COL_APEL    else None
            dni       = _limpiar(row.get(COL_DNI,      '')) if COL_DNI     else None

            if not nombres and not apellidos and not dni:
                omitidas += 1
                continue

            est_nom  = _limpiar(row.get(COL_EST,    '')) if COL_EST    else None
            fec_naci = _limpiar_fecha(row.get(COL_FEC, '')) if COL_FEC else None
            genero   = _limpiar(row.get(COL_GENERO, '')) if COL_GENERO else None
            direccion= _limpiar(row.get(COL_DIR,    '')) if COL_DIR    else None
            celular  = _limpiar(row.get(COL_CEL,    '')) if COL_CEL    else None
            seguro   = _limpiar(row.get(COL_SEGURO, '')) if COL_SEGURO else None
            hta      = _limpiar(row.get(COL_HTA,    '')) if COL_HTA    else None
            dm2      = _limpiar(row.get(COL_DM2,    '')) if COL_DM2    else None

            try:
                id_est = _upsert_establecimiento(est_nom)
                id_pac = _upsert_paciente(dni, nombres, apellidos, fec_naci, genero, direccion, celular)

                # Insertar en ATENCIONES
                d_aten = {'IdPaciente': id_pac}
                if id_est:  d_aten['IdEstablecimiento'] = id_est
                if seguro:  d_aten['Seguro'] = seguro
                r_aten = supabase.table('ATENCIONES').insert(d_aten).execute()
                id_aten = r_aten.data[0]['IdAtencion']

                # Insertar en EVALUACIONES_CLINICAS (solo si hay datos)
                if hta or dm2:
                    d_ev = {'IdAtencion': id_aten}
                    if hta: d_ev['Hta'] = hta
                    if dm2: d_ev['Dm2'] = dm2
                    supabase.table('EVALUACIONES_CLINICAS').insert(d_ev).execute()

                ok += 1
            except Exception as e_row:
                errores += 1

        msg = f'✅ {ok} pacientes insertados en las tablas normalizadas.'
        if omitidas: msg += f' ⏭ {omitidas} filas vacías omitidas.'
        if errores:  msg += f' ❌ {errores} errores.'
        flash(msg)

    except Exception as e:
        flash(f"Error interno al leer el Excel: {str(e)}")

    return redirect(url_for('panel_control', seccion='ingreso-pacientes'))

@app.route('/editar-usuario/<nombre_original>', methods=['POST'])
def editar_usuario(nombre_original):
    if 'user' not in session or session.get('rol') not in ['administrador', 'desarrollador']:
        return redirect(url_for('home'))
    
    rol_actual = session.get('rol')
    usuario_operador = session.get('user')
    
    try:
        resp = supabase.table('usuarios').select("*").eq("username", nombre_original).execute()
        if len(resp.data) == 0:
            flash('El usuario no existe.')
            return redirect(url_for('panel_control', seccion='gestion-usuarios'))
        
        datos_objetivo = resp.data[0]
        
        if rol_actual != 'desarrollador':
            if datos_objetivo.get('creado_por') != usuario_operador and nombre_original != usuario_operador:
                flash('Error: No tienes permiso para editar este usuario.')
                return redirect(url_for('panel_control', seccion='gestion-usuarios'))

        nuevo_nombre = request.form.get('edit_user')
        nueva_pass = request.form.get('edit_pass')
        nuevo_rol = request.form.get('edit_rol')

        if rol_actual == 'administrador' and nuevo_rol == 'administrador':
            flash('Error: No puedes asignar el rol de Administrador.')
            return redirect(url_for('panel_control', seccion='gestion-usuarios'))

        supabase.table('usuarios').update({
            "username": nuevo_nombre,
            "password": nueva_pass,
            "rol": nuevo_rol
        }).eq("username", nombre_original).execute()

        # Si el usuario editado es uno mismo
        if session.get('user') == nombre_original:
            session['user'] = nuevo_nombre
            session['rol'] = nuevo_rol
            if nuevo_rol == 'usuario': 
                return redirect(url_for('inicio_estandar'))

        flash(f'Usuario {nombre_original} actualizado.')
    except Exception as e:
        flash(f'Error al modificar el usuario: {str(e)}')
    
    return redirect(url_for('panel_control', seccion='gestion-usuarios'))

@app.route('/eliminar-usuario/<nombre_user>')
def eliminar_usuario(nombre_user):
    rol_actual = session.get('rol')
    usuario_operador = session.get('user')

    if rol_actual not in ['administrador', 'desarrollador']:
        return redirect(url_for('home'))

    if rol_actual == 'administrador':
        try:
            resp = supabase.table('usuarios').select("rol, creado_por").eq("username", nombre_user).execute()
            if len(resp.data) > 0:
                datos_objetivo = resp.data[0]
                if nombre_user == 'desarrollador' or datos_objetivo.get('rol') == 'administrador':
                    flash('No puedes eliminar usuarios de nivel igual o superior.')
                    return redirect(url_for('panel_control', seccion='gestion-usuarios'))
                if datos_objetivo.get('creado_por') != usuario_operador:
                    flash('Error: No tienes permiso para eliminar usuarios que no creaste.')
                    return redirect(url_for('panel_control', seccion='gestion-usuarios'))
        except Exception:
            pass

    if nombre_user != usuario_operador:
        try:
            supabase.table('usuarios').delete().eq("username", nombre_user).execute()
            flash(f'Usuario eliminado permanentemente.')
        except Exception as e:
            flash(f'Error al eliminar usuario: {str(e)}')
    else:
        flash('No puedes auto-eliminarte.')
    
    return redirect(url_for('panel_control', seccion='gestion-usuarios'))

@app.route('/inicio')
def inicio_estandar():
    if 'user' not in session: return redirect(url_for('home'))
    return "<h1>Hospital San José</h1><p>Panel de Usuario.</p><a href='/logout'>Cerrar Sesión</a>"

# ─────────────────────────────────────────────────────────────
# API: SEGUIMIENTO — buscar paciente por DNI
# ─────────────────────────────────────────────────────────────
from flask import jsonify
import math

MESES_ES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
            'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

@app.route('/api/seguimiento/buscar')
def seguimiento_buscar():
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    dni       = request.args.get('dni', '').strip()
    num_aten  = request.args.get('atencion', '1').strip()   # '1' o '2'

    if not dni:
        return jsonify({'error': 'DNI requerido'}), 400

    try:
        # Buscar paciente por DNI
        r_pac = supabase.table('Paciente')\
            .select('"IdPaciente","Nombres","Apellidos","DNI"')\
            .eq('"DNI"', dni).limit(1).execute()

        if not r_pac.data:
            return jsonify({'error': f'No se encontró paciente con DNI {dni}'}), 404

        pac      = r_pac.data[0]
        id_pac   = pac['IdPaciente']
        nombre_completo = f"{pac.get('Apellidos','').strip()}, {pac.get('Nombres','').strip()}"

        # Traer TODAS las atenciones del paciente ordenadas por IdAtencion
        r_aten = supabase.table('ATENCIONES')\
            .select('"IdAtencion","NumAtencion","Lote","NumFua","FechaAtencion","Seguro",'
                    'EVALUACIONES_CLINICAS("Dx","PresionA","Hta","Dm2")')\
            .eq('"IdPaciente"', id_pac)\
            .order('"IdAtencion"').execute()

        # Solo atenciones clínicas (tienen FechaAtencion o NumAtencion).
        # Las atenciones de Hoja 1 solo tienen Seguro → las descartamos aquí.
        atenciones = [
            a for a in (r_aten.data or [])
            if a.get('FechaAtencion') or a.get('NumAtencion') or a.get('Lote')
        ]

        idx = int(num_aten) - 1   # 0-based
        if idx >= len(atenciones):
            return jsonify({'error': f'El paciente no tiene una atención N°{num_aten}'}), 404

        aten  = atenciones[idx]
        evals = aten.get('EVALUACIONES_CLINICAS') or []
        ev    = evals[0] if evals else {}

        lote   = aten.get('Lote')     or ''
        fua    = aten.get('NumFua')   or ''
        fecha  = aten.get('FechaAtencion') or ''
        presion= ev.get('PresionA')   or ''
        dx     = ev.get('Dx')         or ''

        # ── CUMPLE / NO CUMPLE ──
        campos_requeridos = {'LOTE': lote, 'N°FUA': fua, 'FECHA': fecha,
                             'PRESIÓN': presion, 'DX': dx}
        faltantes = [k for k, v in campos_requeridos.items() if not str(v).strip()]
        cumple = 'CUMPLE' if not faltantes else 'NO CUMPLE'

        # ── SEMANA Y MES ──
        num_semana = ''
        mes_nombre = ''
        if fecha:
            try:
                from datetime import datetime as dt
                fecha_dt = dt.strptime(str(fecha)[:10], '%Y-%m-%d')
                num_semana = math.ceil(fecha_dt.day / 7)
                mes_nombre = MESES_ES[fecha_dt.month - 1]
            except Exception:
                pass

        return jsonify({
            'nombre_completo': nombre_completo,
            'dni':     pac.get('DNI', ''),
            'lote':    lote,
            'fua':     fua,
            'fecha':   fecha[:10] if fecha else '',
            'presion': presion,
            'dx':      dx,
            # Resultado
            'cumple':      cumple,
            'faltantes':   faltantes,
            'num_semana':  num_semana,
            'mes':         mes_nombre,
            'total_atenciones': len(atenciones),
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# ─────────────────────────────────────────────────────────────
# API: INGRESO PACIENTE
# ─────────────────────────────────────────────────────────────

@app.route('/api/establecimientos')
def api_establecimientos():
    """Retorna la lista de establecimientos para el combo box."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    try:
        resp = supabase.table('ESTABLECIMIENTO_SALUD')\
            .select('"IdEstablecimiento","NombreEstablecimiento","CodigoRenipres"')\
            .order('"NombreEstablecimiento"').execute()
        return jsonify(resp.data or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/paciente/buscar-dni')
def api_buscar_paciente_dni():
    """Busca un paciente por DNI y devuelve sus datos personales + establecimiento."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    dni = request.args.get('dni', '').strip()
    if not dni:
        return jsonify({'error': 'DNI requerido'}), 400

    try:
        r = supabase.table('Paciente')\
            .select('"IdPaciente","Nombres","Apellidos","DNI","fecNacimiento","Genero","Direccion","Celular"')\
            .eq('"DNI"', dni).limit(1).execute()

        if not r.data:
            return jsonify({'encontrado': False,
                            'mensaje': f'No se encontró ningún paciente con DNI {dni}'}), 404

        p = r.data[0]
        id_pac = p['IdPaciente']

        # Buscar las atenciones del paciente para la "Primera Atención"
        r_est = supabase.table('ATENCIONES')\
            .select('"IdAtencion","IdEstablecimiento","Lote","NumFua","FechaAtencion","Seguro",ESTABLECIMIENTO_SALUD("IdEstablecimiento","NombreEstablecimiento","CodigoRenipres"),EVALUACIONES_CLINICAS("Dx","PresionA")')\
            .eq('"IdPaciente"', id_pac)\
            .order('"IdAtencion"')\
            .execute()

        establecimiento = {}
        primera_atencion = {}
        segunda_atencion = {}
        if r_est.data:
            # Separar las atenciones válidas e inválidas para poder extraer la 1ra y 2da correctamente
            valid_ats = [x for x in r_est.data if x.get('Lote') or x.get('NumFua') or x.get('FechaAtencion')]
            if len(valid_ats) == 0:
                at1 = r_est.data[0] if len(r_est.data) > 0 else {}
                at2 = r_est.data[1] if len(r_est.data) > 1 else {}
            else:
                at1 = valid_ats[0]
                at2 = valid_ats[1] if len(valid_ats) > 1 else {}
            
            if at1.get('ESTABLECIMIENTO_SALUD'):
                establecimiento = at1['ESTABLECIMIENTO_SALUD']
            
            evs1 = at1.get('EVALUACIONES_CLINICAS') or []
            ev1 = evs1[0] if evs1 else {}
            
            primera_atencion = {
                'lote': at1.get('Lote') or '',
                'fua': at1.get('NumFua') or '',
                'fecha': at1.get('FechaAtencion') or '',
                'seguro': at1.get('Seguro') or '',
                'dx': ev1.get('Dx') or '',
                'presion': ev1.get('PresionA') or ''
            }

            evs2 = at2.get('EVALUACIONES_CLINICAS') or []
            ev2 = evs2[0] if evs2 else {}
            
            segunda_atencion = {
                'lote': at2.get('Lote') or '',
                'fua': at2.get('NumFua') or '',
                'fecha': at2.get('FechaAtencion') or '',
                'dx': ev2.get('Dx') or '',
                'presion': ev2.get('PresionA') or ''
            }

        return jsonify({
            'encontrado': True,
            'id_paciente':   id_pac,
            'nombres':       p.get('Nombres')       or '',
            'apellidos':     p.get('Apellidos')      or '',
            'dni':           p.get('DNI')            or '',
            'fec_nacimiento':p.get('fecNacimiento')  or '',
            'genero':        p.get('Genero')         or '',
            'direccion':     p.get('Direccion')      or '',
            'celular':       p.get('Celular')        or '',
            'establecimiento': establecimiento,
            'primera_atencion': primera_atencion,
            'segunda_atencion': segunda_atencion,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500




# ═══════════════════════════════════════════════════════
#  API DE REPORTES ESTADÍSTICOS (6 reportes estratégicos)
# ═══════════════════════════════════════════════════════

@app.route('/api/reportes/demografia')
def api_reporte_demografia():
    """R1: Distribución demográfica por grupos de edad y sexo."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    try:
        from datetime import datetime
        r = supabase.table('Paciente').select('"fecNacimiento","Genero"').execute()
        hoy = datetime.now()
        grupos = {
            'M': {'0-17': 0, '18-29': 0, '30-44': 0, '45-59': 0, '60+': 0},
            'F': {'0-17': 0, '18-29': 0, '30-44': 0, '45-59': 0, '60+': 0},
        }
        for p in r.data:
            fec = p.get('fecNacimiento')
            gen = (p.get('Genero') or '').lower()
            sexo = 'F' if 'fem' in gen else 'M'
            if not fec:
                continue
            try:
                nac = datetime.strptime(fec[:10], '%Y-%m-%d')
                edad = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
                grupo = '60+' if edad >= 60 else ('45-59' if edad >= 45 else ('30-44' if edad >= 30 else ('18-29' if edad >= 18 else '0-17')))
                grupos[sexo][grupo] += 1
            except:
                pass
        labels = ['0-17', '18-29', '30-44', '45-59', '60+']
        return jsonify({
            'labels': labels,
            'masculino': [grupos['M'][l] for l in labels],
            'femenino': [grupos['F'][l] for l in labels],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/patologias')
def api_reporte_patologias():
    """R2: Frecuencia de diagnósticos (DX) más comunes."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    try:
        from collections import Counter
        r = supabase.table('EVALUACIONES_CLINICAS').select('"Dx","Hta","Dm2"').execute()
        dx_counter = Counter()
        hta_si = 0
        dm2_si = 0
        for ev in r.data:
            dx = (ev.get('Dx') or '').strip().upper()
            if dx:
                dx_counter[dx] += 1
            if (ev.get('Hta') or '').upper() in ('SI', 'SÍ', 'S', '1', 'TRUE', 'YES'):
                hta_si += 1
            if (ev.get('Dm2') or '').upper() in ('SI', 'SÍ', 'S', '1', 'TRUE', 'YES'):
                dm2_si += 1
        top = dx_counter.most_common(8)
        return jsonify({
            'dx_labels': [t[0] for t in top],
            'dx_counts': [t[1] for t in top],
            'hta': hta_si,
            'dm2': dm2_si,
            'total': len(r.data),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/riesgo-cronico')
def api_reporte_riesgo():
    """R3: Riesgo crónico (HTA/DM2) cruzado por grupo etario."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    try:
        from datetime import datetime
        r = supabase.table('ATENCIONES')\
            .select('"IdPaciente",Paciente("fecNacimiento"),EVALUACIONES_CLINICAS("Hta","Dm2")')\
            .execute()
        hoy = datetime.now()
        grupos_hta = {'30-44': 0, '45-59': 0, '60+': 0}
        grupos_dm2 = {'30-44': 0, '45-59': 0, '60+': 0}
        for at in r.data:
            pac = at.get('Paciente') or {}
            fec = pac.get('fecNacimiento')
            evs = at.get('EVALUACIONES_CLINICAS') or []
            ev = evs[0] if evs else {}
            hta = (ev.get('Hta') or '').upper() in ('SI', 'SÍ', 'S', '1')
            dm2 = (ev.get('Dm2') or '').upper() in ('SI', 'SÍ', 'S', '1')
            if not fec or (not hta and not dm2):
                continue
            try:
                nac = datetime.strptime(fec[:10], '%Y-%m-%d')
                edad = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
                grupo = '60+' if edad >= 60 else ('45-59' if edad >= 45 else ('30-44' if edad >= 30 else None))
                if grupo:
                    if hta: grupos_hta[grupo] += 1
                    if dm2: grupos_dm2[grupo] += 1
            except:
                pass
        labels = ['30-44', '45-59', '60+']
        return jsonify({
            'labels': labels,
            'hta': [grupos_hta[l] for l in labels],
            'dm2': [grupos_dm2[l] for l in labels],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/actividad-establecimientos')
def api_reporte_establecimientos():
    """R4: Volumen de atenciones por establecimiento."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    try:
        from collections import Counter
        r = supabase.table('ATENCIONES')\
            .select('"IdEstablecimiento",ESTABLECIMIENTO_SALUD("NombreEstablecimiento")')\
            .not_.is_('"IdEstablecimiento"', 'null')\
            .execute()
        conteo = Counter()
        nombres = {}
        for at in r.data:
            id_est = at.get('IdEstablecimiento')
            est = at.get('ESTABLECIMIENTO_SALUD') or {}
            nombre = est.get('NombreEstablecimiento') or f'Est#{id_est}'
            # Abbreviate long names
            nombre_corto = nombre[:22] + '…' if len(nombre) > 22 else nombre
            conteo[nombre_corto] += 1
        top = conteo.most_common(10)
        return jsonify({
            'labels': [t[0] for t in top],
            'counts': [t[1] for t in top],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/tendencia-temporal')
def api_reporte_tendencia():
    """R5: Tendencia mensual de atenciones registradas."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    try:
        from collections import Counter
        r = supabase.table('ATENCIONES').select('"FechaAtencion"').not_.is_('"FechaAtencion"', 'null').execute()
        meses = Counter()
        for at in r.data:
            fecha = at.get('FechaAtencion')
            if fecha and len(fecha) >= 7:
                meses[fecha[:7]] += 1
        ordenado = sorted(meses.items())
        labels_raw = [m[0] for m in ordenado]
        MESES_ES = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        labels_fmt = []
        for m in labels_raw:
            try:
                y, mo = m.split('-')
                labels_fmt.append(f"{MESES_ES[int(mo)]} {y}")
            except:
                labels_fmt.append(m)
        return jsonify({
            'labels': labels_fmt,
            'counts': [m[1] for m in ordenado],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/calidad-datos')
def api_reporte_calidad():
    """R6: Índice de calidad de registro de datos clínicos."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    try:
        r_pac = supabase.table('Paciente').select('"DNI","Nombres","Apellidos","fecNacimiento","Genero","Celular"').execute()
        total_pac = len(r_pac.data)
        campos_pac = {'DNI': 0, 'Nombres': 0, 'Apellidos': 0, 'Fecha Nacimiento': 0, 'Género': 0, 'Celular': 0}
        for p in r_pac.data:
            if p.get('DNI'): campos_pac['DNI'] += 1
            if p.get('Nombres'): campos_pac['Nombres'] += 1
            if p.get('Apellidos'): campos_pac['Apellidos'] += 1
            if p.get('fecNacimiento'): campos_pac['Fecha Nacimiento'] += 1
            if p.get('Genero'): campos_pac['Género'] += 1
            if p.get('Celular'): campos_pac['Celular'] += 1
        completitud = {k: round(v * 100 / total_pac) if total_pac else 0 for k, v in campos_pac.items()}
        
        r_ev = supabase.table('EVALUACIONES_CLINICAS').select('"Dx","PresionA","Hta","Dm2"').execute()
        total_ev = len(r_ev.data)
        campos_ev = {'DX': 0, 'Presión': 0, 'HTA': 0, 'DM2': 0}
        for ev in r_ev.data:
            if ev.get('Dx'): campos_ev['DX'] += 1
            if ev.get('PresionA'): campos_ev['Presión'] += 1
            if ev.get('Hta'): campos_ev['HTA'] += 1
            if ev.get('Dm2'): campos_ev['DM2'] += 1
        completitud_ev = {k: round(v * 100 / total_ev) if total_ev else 0 for k, v in campos_ev.items()}
        
        todos = {**completitud, **completitud_ev}
        return jsonify({
            'labels': list(todos.keys()),
            'porcentajes': list(todos.values()),
            'total_pacientes': total_pac,
            'total_evaluaciones': total_ev,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


from datetime import datetime

def calcular_edad(fec_nac_str):
    if not fec_nac_str:
        return ''
    try:
        fec_nac = datetime.strptime(fec_nac_str[:10], '%Y-%m-%d')
        hoy = datetime.now()
        edad = hoy.year - fec_nac.year - ((hoy.month, hoy.day) < (fec_nac.month, fec_nac.day))
        return str(edad)
    except:
        return ''

@app.route('/api/pacientes/ultimos')
def api_ultimos_pacientes():
    """Devuelve los últimos 5 pacientes registrados para la tabla Pacientes Ingresados."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    try:
        resp = supabase.table('Paciente').select('*').order('"IdPaciente"', desc=True).limit(5).execute()
        pacientes = []
        for p in resp.data:
            edad = calcular_edad(p.get('fecNacimiento'))
            genero = (p.get('Genero') or '').title()
            
            fec_str = p.get('fecNacimiento')
            if fec_str:
                try:
                    f_obj = datetime.strptime(fec_str[:10], '%Y-%m-%d')
                    fec_formateada = f_obj.strftime('%d/%m/%Y')
                except:
                    fec_formateada = fec_str[:10]
            else:
                fec_formateada = ''
                
            nombres_completos = f"{p.get('Nombres') or ''} {p.get('Apellidos') or ''}".strip()

            pacientes.append({
                'id_paciente': p.get('IdPaciente'),
                'nombres': nombres_completos,
                'dni': p.get('DNI') or '',
                'edad_sexo': f"{edad} / {genero}" if edad else genero,
                'celular': p.get('Celular') or 'N/A',
                'fec_nacimiento': fec_formateada or '—',
                'establecimiento': 'S/N'
            })
        return jsonify(pacientes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/paciente/guardar', methods=['POST'])
def api_guardar_paciente():
    """Crea o actualiza los datos personales de un paciente."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    datos = request.get_json(force=True) or {}
    dni        = (datos.get('dni') or '').strip()
    nombres    = (datos.get('nombres') or '').strip()
    apellidos  = (datos.get('apellidos') or '').strip()
    fec_naci   = (datos.get('fec_nacimiento') or '').strip()
    genero     = (datos.get('genero') or '').strip()
    direccion  = (datos.get('direccion') or '').strip()
    celular    = (datos.get('celular') or '').strip()
    id_est     = datos.get('id_establecimiento')   # puede ser None
    id_pac     = datos.get('id_paciente')          # None si es paciente nuevo

    if not dni and not nombres:
        return jsonify({'error': 'Se requiere al menos DNI o Nombre'}), 400

    try:
        payload = {}
        if nombres:    payload['Nombres']       = nombres
        if apellidos:  payload['Apellidos']     = apellidos
        if dni:        payload['DNI']           = dni
        if fec_naci:   payload['fecNacimiento'] = fec_naci
        if genero:     payload['Genero']        = genero
        if direccion:  payload['Direccion']     = direccion
        if celular:    payload['Celular']       = celular

        if id_pac:
            # Actualizar paciente existente (solo los campos que vienen en el payload)
            supabase.table('Paciente').update(payload).eq('"IdPaciente"', id_pac).execute()
            nuevo_id = id_pac
        else:
            # Insertar nuevo paciente
            ins = supabase.table('Paciente').insert(payload).execute()
            nuevo_id = ins.data[0]['IdPaciente']

        return jsonify({'ok': True, 'id_paciente': nuevo_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/atencion/guardar', methods=['POST'])
def api_guardar_atencion():
    """Crea o actualiza una atención (1 o 2) de un paciente."""
    if 'user' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    datos = request.get_json(force=True) or {}
    id_pac = datos.get('id_paciente')
    num_aten = int(datos.get('num_atencion', 1)) 
    
    if not id_pac:
        return jsonify({'error': 'Falta ID del paciente'}), 400

    try:
        # Obtener atenciones existentes del paciente ordenadas
        r_est = supabase.table('ATENCIONES').select('"IdAtencion"').eq('"IdPaciente"', id_pac).order('"IdAtencion"').execute()
        atenciones = r_est.data or []

        id_atencion = None
        if num_aten == 1 and len(atenciones) > 0:
            id_atencion = atenciones[0]['IdAtencion']
        elif num_aten == 2 and len(atenciones) > 1:
            id_atencion = atenciones[1]['IdAtencion']

        atencion_payload = {
            'IdPaciente': id_pac,
            'Lote': datos.get('lote') or None,
            'NumFua': datos.get('fua') or None,
            'FechaAtencion': datos.get('fecha') or None,
        }
        if 'seguro' in datos:
            atencion_payload['Seguro'] = datos.get('seguro')

        if id_atencion:
            supabase.table('ATENCIONES').update(atencion_payload).eq('"IdAtencion"', id_atencion).execute()
        else:
            res_at = supabase.table('ATENCIONES').insert(atencion_payload).execute()
            id_atencion = res_at.data[0]['IdAtencion']

        # Guardar la evaluación clínica (Dx y Presion)
        dx = datos.get('dx') or None
        presion = datos.get('presion') or None
        
        r_ev = supabase.table('EVALUACIONES_CLINICAS').select('"IdEvaluacion"').eq('"IdAtencion"', id_atencion).execute()
        eval_payload = {
            'IdAtencion': id_atencion,
            'Dx': dx,
            'PresionA': presion
        }
        if r_ev.data:
            supabase.table('EVALUACIONES_CLINICAS').update(eval_payload).eq('"IdEvaluacion"', r_ev.data[0]['IdEvaluacion']).execute()
        else:
            supabase.table('EVALUACIONES_CLINICAS').insert(eval_payload).execute()

        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)