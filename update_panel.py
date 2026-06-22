import re

with open('templates/panel_control.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_css = """    <style>
        :root {
            --bg-main: #f4f6fa;
            --sidebar-bg: #180d2d;
            --sidebar-bg-gradient: linear-gradient(180deg, #180d2d 0%, #20113c 100%);
            --sidebar-text: #a296b8;
            --sidebar-hover: rgba(255, 255, 255, 0.04);
            --sidebar-active-bg: rgba(92, 53, 177, 0.15);
            --sidebar-active-border: #8b5cf6;
            --sidebar-active-text: #ffffff;
            --primary: #6d28d9;
            --primary-hover: #5b21b6;
            --secondary: #8b5cf6;
            --text-dark: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --card-bg: #ffffff;
            --danger: #ef4444;
            --success: #10b981;
            --radius-sm: 8px;
            --radius-md: 16px;
            --shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
            --shadow-md: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
            --shadow-hover: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Poppins', sans-serif; }

        body {
            background-color: var(--bg-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
            color: var(--text-dark);
            -webkit-font-smoothing: antialiased;
        }

        /* --- SIDEBAR --- */
        .sidebar {
            width: 270px;
            background: var(--sidebar-bg-gradient);
            color: white;
            display: flex;
            flex-direction: column;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.1);
            z-index: 100;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .sidebar-logo {
            text-align: center;
            padding: 35px 20px 25px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .logo-circle {
            width: 52px;
            height: 52px;
            background: linear-gradient(135deg, var(--secondary), var(--primary));
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 16px rgba(109, 40, 217, 0.3);
            margin-bottom: 12px;
            transform: rotate(-5deg);
            transition: transform 0.3s;
        }
        .sidebar-logo:hover .logo-circle { transform: rotate(0deg) scale(1.05); }

        .logo-circle i {
            color: #ffffff;
            font-size: 24px;
            transform: rotate(5deg);
        }

        .sidebar-logo h2 {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #ffffff;
        }

        .sidebar nav {
            display: flex;
            flex-direction: column;
            flex: 1;
            padding: 0 16px;
            gap: 6px;
        }

        .sidebar nav a {
            color: var(--sidebar-text);
            text-decoration: none;
            padding: 14px 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 13.5px;
            font-weight: 500;
            border-radius: var(--radius-sm);
            transition: all 0.2s ease;
            position: relative;
        }
        
        .sidebar nav a i {
            font-size: 16px;
            width: 20px;
            text-align: center;
            transition: transform 0.2s;
        }

        .sidebar nav a:hover {
            color: white;
            background: var(--sidebar-hover);
        }

        .sidebar nav a:hover i { transform: translateX(3px); }

        .sidebar nav a.active {
            background: var(--sidebar-active-bg);
            color: var(--sidebar-active-text);
            font-weight: 600;
        }

        .sidebar nav a.active::before {
            content: '';
            position: absolute;
            left: -16px;
            top: 50%;
            transform: translateY(-50%);
            height: 24px;
            width: 4px;
            background-color: var(--sidebar-active-border);
            border-radius: 0 4px 4px 0;
        }

        .logout-container {
            padding: 24px;
            margin-top: auto;
            border-top: 1px solid rgba(255, 255, 255, 0.04);
        }

        .logout-container a {
            color: #fca5a5;
            background: rgba(239, 68, 68, 0.05);
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            font-size: 13px;
            font-weight: 600;
            padding: 14px;
            border-radius: var(--radius-sm);
            transition: all 0.2s;
        }
        .logout-container a:hover {
            background: rgba(239, 68, 68, 0.15);
            color: #fee2e2;
        }

        /* --- HEADER & MAIN WRAPPER --- */
        .main-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
            height: 100vh;
        }

        .topbar {
            height: 76px;
            padding: 0 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(0,0,0,0.03);
            z-index: 50;
            flex-shrink: 0;
        }

        .topbar-left h1 {
            font-size: 18px;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 2px;
        }
        .topbar-left p {
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 500;
        }

        .topbar-right {
            display: flex;
            align-items: center;
            gap: 24px;
        }

        .search-container {
            position: relative;
            display: flex;
            align-items: center;
        }
        .search-container i {
            position: absolute;
            left: 16px;
            color: var(--text-muted);
            font-size: 13px;
        }
        .search-container input {
            padding: 10px 16px 10px 40px;
            border-radius: 40px;
            border: 1px solid var(--border);
            background: #ffffff;
            font-size: 13px;
            width: 240px;
            outline: none;
            transition: all 0.2s;
            box-shadow: var(--shadow-sm);
        }
        .search-container input:focus {
            border-color: var(--secondary);
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
        }

        .user-chip {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 6px 16px 6px 6px;
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 40px;
            cursor: pointer;
            transition: box-shadow 0.2s;
            box-shadow: var(--shadow-sm);
        }
        .user-chip:hover { box-shadow: var(--shadow-md); }
        .user-chip-avatar {
            width: 34px;
            height: 34px;
            background: linear-gradient(135deg, var(--secondary), var(--primary));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 13px;
        }
        .user-chip-info {
            display: flex;
            flex-direction: column;
        }
        .user-chip-name { font-size: 13px; font-weight: 600; color: var(--text-dark); line-height: 1.2; }
        .user-chip-role { font-size: 10px; font-weight: 600; color: var(--secondary); text-transform: uppercase; letter-spacing: 0.5px; }

        /* --- MAIN CONTENT & CARDS --- */
        .main-content {
            flex: 1;
            padding: 32px 40px;
            overflow-y: auto;
            scroll-behavior: smooth;
        }

        .card {
            background: var(--card-bg);
            padding: 32px;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-md);
            border: 1px solid rgba(255,255,255,0.5);
            margin-bottom: 30px;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        h3.card-title {
            color: var(--text-dark);
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 28px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        h3.card-title i {
            color: var(--primary);
            background: rgba(109, 40, 217, 0.08);
            padding: 8px;
            border-radius: 8px;
            font-size: 14px;
        }

        /* --- FORMS --- */
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            align-items: end;
            background: #fcfcfd;
            padding: 24px;
            border-radius: var(--radius-sm);
            margin-bottom: 28px;
            border: 1px solid var(--border);
        }

        .form-group {
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .form-group label {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .form-group input, .form-group select {
            width: 100%;
            padding: 12px 16px;
            border: 1.5px solid var(--border);
            border-radius: var(--radius-sm);
            font-size: 13.5px;
            color: var(--text-dark);
            outline: none;
            transition: all 0.2s;
            background: white;
        }
        .form-group input::placeholder { color: #cbd5e1; }

        .form-group input:focus, .form-group select:focus {
            border-color: var(--secondary);
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
        }

        button.btn-primary {
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s;
            height: 46px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0 4px 10px rgba(109, 40, 217, 0.2);
        }

        button.btn-primary:hover {
            background: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(109, 40, 217, 0.3);
        }

        /* --- TABLES --- */
        .table-responsive { overflow-x: auto; }
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: var(--radius-sm);
            overflow: hidden;
            border: 1px solid var(--border);
        }

        th {
            padding: 16px;
            text-align: left;
            background: #f8fafc;
            color: var(--text-muted);
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid var(--border);
        }

        td {
            padding: 18px 16px;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
            color: var(--text-dark);
            vertical-align: middle;
            transition: background 0.2s;
            background: white;
        }
        tr:last-child td { border-bottom: none; }
        tbody tr:hover td { background: #f8fafc; }

        .user-cell {
            display: flex;
            flex-direction: column;
        }
        .user-cell-name { font-weight: 600; color: var(--text-dark); margin-bottom: 2px; }
        .user-cell-id { font-size: 11.5px; color: #94a3b8; font-weight: 500; }

        /* --- BADGES --- */
        .role-badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .role-badge.admin { background: #fee2e2; color: #b91c1c; }
        .role-badge.dev { background: #f3e8ff; color: #6b21a8; }
        .role-badge.user { background: #e0f2fe; color: #0369a1; }

        /* --- ACTION LINKS --- */
        .action-link {
            text-decoration: none;
            font-weight: 600;
            font-size: 13px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 12px;
            border-radius: 6px;
            transition: 0.2s;
            cursor: pointer;
            border: none;
            background: none;
        }
        .action-edit { color: var(--primary); }
        .action-edit:hover { background: rgba(109, 40, 217, 0.08); }
        .action-delete { color: var(--danger); margin-left: 8px; }
        .action-delete:hover { background: rgba(239, 68, 68, 0.08); }

        .restricted-badge {
            color: #94a3b8;
            font-size: 12px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 12px;
        }

        /* --- DROPDOWN --- */
        details summary { list-style: none; }
        details summary::-webkit-details-marker { display: none; }
        .edit-form-dropdown {
            position: absolute;
            right: 80px;
            background: white;
            border: 1px solid var(--border);
            padding: 24px;
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-hover);
            z-index: 100;
            width: 260px;
            top: -10px;
        }
        .edit-form-dropdown label {
            display: block;
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            margin-top: 14px;
            margin-bottom: 6px;
            text-transform: uppercase;
        }
        .edit-form-dropdown input, .edit-form-dropdown select {
            width: 100%;
            padding: 10px 14px;
            border: 1.5px solid var(--border);
            border-radius: 6px;
            font-size: 13px;
            outline: none;
            margin-bottom: 4px;
        }
        .edit-form-dropdown input:focus, .edit-form-dropdown select:focus { border-color: var(--secondary); }

        /* --- MISC --- */
        .flashes { list-style: none; margin-bottom: 24px; }
        .flash-msg {
            padding: 14px 20px;
            border-radius: var(--radius-sm);
            margin-bottom: 12px;
            font-weight: 500;
            font-size: 13.5px;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: var(--shadow-sm);
        }
        .error { background: #fef2f2; color: #b91c1c; border-left: 4px solid #ef4444; }
        .success { background: #ecfdf5; color: #047857; border-left: 4px solid #10b981; }

        /* IP/Pacientes grid fixes */
        .form-paciente-grid, .ip-grid { display: grid; gap: 20px; }
        .ip-grid { grid-template-columns: repeat(3, 1fr); }
        .ip-field, .form-paciente-group { display: flex; flex-direction: column; }
        .ip-field--wide { grid-column: span 2; }
        .ip-label, .form-paciente-group label {
            font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase;
        }
        .ip-input, .form-paciente-group input, .form-paciente-group select {
            padding: 12px 16px; border: 1.5px solid var(--border); border-radius: var(--radius-sm); font-size: 13.5px; outline: none; transition: 0.2s; background: white;
        }
        .ip-input:focus, .form-paciente-group input:focus, .form-paciente-group select:focus {
            border-color: var(--secondary); box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
        }

        .btn-green, .btn-dark {
            color: white; border: none; border-radius: var(--radius-sm); padding: 12px 24px; font-size: 14px; font-weight: 600; cursor: pointer; transition: 0.2s;
        }
        .btn-green { background: var(--success); }
        .btn-green:hover { background: #059669; transform: translateY(-1px); }
        .btn-dark { background: #334155; }
        .btn-dark:hover { background: #1e293b; transform: translateY(-1px); }

        /* --- RESPONSIVE --- */
        .hamburger { display: none; background: none; border: none; font-size: 20px; color: var(--text-dark); cursor: pointer; }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 90; backdrop-filter: blur(2px); }
        .overlay.active { display: block; }

        @media (max-width: 1024px) {
            .search-container { display: none; }
        }
        @media (max-width: 768px) {
            .sidebar { position: fixed; left: -280px; top: 0; bottom: 0; }
            .sidebar.open { transform: translateX(280px); }
            .hamburger { display: block; }
            .topbar { padding: 0 24px; }
            .main-content { padding: 24px; }
            .ip-grid { grid-template-columns: repeat(2, 1fr); }
            .ip-field--wide { grid-column: span 2; }
            .user-chip-name, .user-chip-role { display: none; }
            .user-chip { padding: 4px; border-radius: 50%; }
        }
        @media (max-width: 560px) {
            .ip-grid { grid-template-columns: 1fr; }
            .ip-field--wide { grid-column: span 1; }
            .form-grid { grid-template-columns: 1fr; }
            .topbar { padding: 0 16px; height: 64px; }
            .main-content { padding: 16px; }
        }
    </style>"""

html_replacements = {
    '''<aside class="sidebar">
        <div class="sidebar-logo">
            <div class="logo-circle">
                <i class="fas fa-hospital-symbol"></i>
            </div>
            <h2>San José</h2>
        </div>
        <nav>
            {% if session.get('rol') in ['administrador', 'desarrollador'] %}
            <a href="#" onclick="showSection(event, 'gestion-usuarios')"
                class="nav-link {{ 'active' if seccion == 'gestion-usuarios' else '' }}"><i class="fas fa-users"></i>
                Gestión Usuarios</a>
            <a href="#" onclick="showSection(event, 'pacientes-ingresados')"
                class="nav-link {{ 'active' if seccion == 'pacientes-ingresados' else '' }}"><i
                    class="fas fa-list-alt"></i> Pacientes Ingresados</a>
            {% endif %}
            <a href="#" onclick="showSection(event, 'ingreso-paciente')"
                class="nav-link {{ 'active' if seccion == 'ingreso-paciente' else '' }}"><i
                    class="fas fa-user-plus"></i> Ingreso Paciente</a>
            <a href="#" onclick="showSection(event, 'seguimiento-pacientes')"
                class="nav-link {{ 'active' if seccion == 'seguimiento-pacientes' else '' }}"><i
                    class="fas fa-notes-medical"></i> Seguimiento</a>
            <a href="#" onclick="showSection(event, 'reportes')"
                class="nav-link {{ 'active' if seccion == 'reportes' else '' }}"><i class="fas fa-chart-pie"></i>
                Reportes</a>
        </nav>
        <div class="logout-container">
            <a href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Cerrar Sesión</a>
        </div>
    </aside>

    <main class="main-content">
        <div class="header-top">
            <div class="welcome-text">
                <h1>¡Bienvenido, {{ session.get('user', 'Usuario') | title }}!</h1>
                <p>Aquí tienes tu panel de administración ({{ session.get('rol', '') | title }})</p>
            </div>
        </div>''': '''<div class="overlay" id="mobileOverlay" onclick="toggleSidebar()"></div>
    
    <aside class="sidebar" id="sidebar">
        <div class="sidebar-logo">
            <div class="logo-circle">
                <i class="fas fa-hospital-symbol"></i>
            </div>
            <h2>San José</h2>
        </div>
        <nav>
            {% if session.get('rol') in ['administrador', 'desarrollador'] %}
            <a href="#" onclick="showSection(event, 'gestion-usuarios')" class="nav-link {{ 'active' if seccion == 'gestion-usuarios' else '' }}">
                <i class="fas fa-users"></i> Gestión Usuarios
            </a>
            <a href="#" onclick="showSection(event, 'pacientes-ingresados')" class="nav-link {{ 'active' if seccion == 'pacientes-ingresados' else '' }}">
                <i class="fas fa-list-alt"></i> Pacientes Ingresados
            </a>
            {% endif %}
            <a href="#" onclick="showSection(event, 'ingreso-paciente')" class="nav-link {{ 'active' if seccion == 'ingreso-paciente' else '' }}">
                <i class="fas fa-user-plus"></i> Ingreso Paciente
            </a>
            <a href="#" onclick="showSection(event, 'seguimiento-pacientes')" class="nav-link {{ 'active' if seccion == 'seguimiento-pacientes' else '' }}">
                <i class="fas fa-notes-medical"></i> Seguimiento
            </a>
            <a href="#" onclick="showSection(event, 'reportes')" class="nav-link {{ 'active' if seccion == 'reportes' else '' }}">
                <i class="fas fa-chart-pie"></i> Reportes
            </a>
        </nav>
        <div class="logout-container">
            <a href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Cerrar Sesión</a>
        </div>
    </aside>

    <div class="main-wrapper">
        <header class="topbar">
            <div class="topbar-left" style="display: flex; align-items: center; gap: 16px;">
                <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
                <div>
                    <h1>¡Bienvenido, {{ session.get('user', 'Usuario') | title }}!</h1>
                    <p>Panel de administración</p>
                </div>
            </div>
            
            <div class="topbar-right">
                <div class="search-container">
                    <i class="fas fa-search"></i>
                    <input type="text" placeholder="Buscar paciente o sección...">
                </div>
                
                <div class="user-chip">
                    <div class="user-chip-avatar">
                        {{ session.get('user', 'U')[0] | upper }}
                    </div>
                    <div class="user-chip-info">
                        <span class="user-chip-name">{{ session.get('user', 'Usuario') | title }}</span>
                        <span class="user-chip-role">{{ session.get('rol', '') | title }}</span>
                    </div>
                </div>
            </div>
        </header>

        <main class="main-content">''',

    '''</body>''': '''    <script>
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('open');
            document.getElementById('mobileOverlay').classList.toggle('active');
        }
    </script>
</body>''',

    '''<div>
                    <label>Nuevo Usuario</label>
                    <input type="text" name="nuevo_user" required placeholder="Ej: JuanPerez">
                </div>
                <div>
                    <label>Correo Electrónico</label>
                    <input type="email" name="nuevo_email" required placeholder="Ej: juan@correo.com">
                </div>
                <div>
                    <label>Contraseña</label>
                    <input type="password" name="nueva_pass" required placeholder="••••••••">
                </div>
                <div>
                    <label>Rol Asignado</label>
                    <select name="rol">
                        <option value="usuario">Usuario Estándar</option>
                        {% if session.get('rol') == 'desarrollador' %}
                        <option value="administrador">Administrador</option>
                        {% endif %}
                    </select>
                </div>''': '''<div class="form-group">
                    <label>Nuevo Usuario</label>
                    <input type="text" name="nuevo_user" required placeholder="Ej: JuanPerez">
                </div>
                <div class="form-group">
                    <label>Correo Electrónico</label>
                    <input type="email" name="nuevo_email" required placeholder="Ej: juan@correo.com">
                </div>
                <div class="form-group">
                    <label>Contraseña</label>
                    <input type="password" name="nueva_pass" required placeholder="••••••••">
                </div>
                <div class="form-group">
                    <label>Rol Asignado</label>
                    <select name="rol">
                        <option value="usuario">Usuario Estándar</option>
                        {% if session.get('rol') == 'desarrollador' %}
                        <option value="administrador">Administrador</option>
                        {% endif %}
                    </select>
                </div>''',

    '''<td>
                                <div style="font-weight: 600;">{{ nombre }}</div>
                                <div style="font-size: 11px; color: #a0a5ba; margin-top: 3px;">ID: #10{{ loop.index }}
                                </div>
                            </td>''': '''<td>
                                <div class="user-cell">
                                    <span class="user-cell-name">{{ nombre }}</span>
                                    <span class="user-cell-id">ID: #10{{ loop.index }}</span>
                                </div>
                            </td>''',
                            
    '''{% set var_class = 'dev' if datos.rol == 'desarrollador' else ('admin' if datos.rol ==
                                'administrador' else '') %}''': '''{% set var_class = 'dev' if datos.rol == 'desarrollador' else ('admin' if datos.rol == 'administrador' else 'user') %}''',
                                
    '''<span style="color: #c4c1d9; font-size: 12px; font-weight: 500;"><i
                                        class="fas fa-shield-alt"></i> Restringido</span>''': '''<span class="restricted-badge"><i class="fas fa-lock"></i> Restringido</span>''',
                                        
    '''</main>''': '''</main>\n    </div>'''
}

# 1. Replace CSS block
content = re.sub(r'<style>.*?</style>', new_css, content, flags=re.DOTALL)

# 2. String replacements
for old_str, new_str in html_replacements.items():
    content = content.replace(old_str, new_str)

with open('templates/panel_control.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Update completed.")
