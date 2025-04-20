# Duelo de Plumas - Plataforma de Concursos Literarios

Sitio web minimalista para la gestión y participación en concursos literarios.

## Funcionalidades Principales

*   Gestión de Concursos (Crear, Editar, Abrir, Cerrar) por Administradores.
*   Asignación de Jueces a Concursos.
*   Envío de Textos por participantes (actualmente anónimo, sin login).
*   Interfaz de Evaluación para Jueces (Ranking 1º, 2º, 3º, M. Hon.).
*   Cálculo Automático de Resultados y Cierre de Concurso.
*   Visualización de Resultados y Textos Enviados en Concursos Cerrados.
*   Registro de Administrador (primer usuario) y Jueces.
*   Jueces de IA con personalidades distintas para evaluar textos automáticamente.

## Flujos de Usuario

### Visitante / Participante

1.  **Ver Inicio (`/`):** Ve la introducción, una lista de concursos públicos activos y una lista de concursos recién finalizados (con ganadores).
2.  **Ver Concursos (`/contests`):** Ve listas de concursos públicos agrupados por estado: Abiertos, En Evaluación, Finalizados (con ganadores).
3.  **Ver Detalles de Concurso (`/contest/<id>`):** Ve la descripción, estado y fecha límite de un concurso específico.
4.  **Enviar Texto (si el concurso está Abierto):**
    *   Accede a los detalles del concurso (`/contest/<id>`).
    *   Rellena el formulario con Nombre de Autor, Título del Texto y el Contenido.
    *   Envía el formulario.
    *   Ve un mensaje de confirmación.
5.  **Ver Resultados (si el concurso está Cerrado):**
    *   Accede a los detalles del concurso (`/contest/<id>`).
    *   Ve la lista de envíos ordenada por ranking.
    *   Ve los puntos totales de cada envío.
    *   Ve el texto completo de cada envío.
    *   Ve los comentarios (si existen) dejados por los jueces para cada envío.

### Juez

1.  **Registro (si no tiene cuenta):**
    *   Accede a `/auth/register`.
    *   Completa el formulario de registro (Username, Email opcional, Password).
    *   Es redirigido a la página de login.
2.  **Iniciar Sesión (`/auth/login`):**
    *   Introduce nombre de usuario/email y contraseña.
    *   Es redirigido a la página principal o a la que intentaba acceder.
3.  **Ver Concursos Asignados (`/contests`):**
    *   Ve una sección especial "Mis Evaluaciones Pendientes" con los concursos a los que ha sido asignado y que están en estado 'evaluation'.
    *   Ve también las listas públicas de concursos Abiertos, En Evaluación y Finalizados.
4.  **Acceder a Evaluación:**
    *   Desde "Mis Evaluaciones Pendientes" en `/contests`, hace clic en el título del concurso.
    *   Es llevado a la lista de envíos para ese concurso (`/contest/<id>/submissions`).
5.  **Evaluar Concurso (`/contest/<id>/evaluate`):**
    *   Desde la lista de envíos, hace clic en "Registrar mi Ranking" o "Editar mi Ranking".
    *   Ve una tabla con todos los envíos del concurso.
    *   Puede hacer clic en "Mostrar/Ocultar Texto" para leer cada envío.
    *   Asigna lugares (1º, 2º, 3º, M. Hon.) usando los desplegables, respetando las reglas de asignación.
    *   Escribe comentarios específicos para cada envío (opcional).
    *   Guarda el ranking.
    *   Si es el último juez requerido en votar, los resultados se calculan y el concurso se cierra.
    *   Es redirigido a la lista de envíos o a los detalles del concurso (si se cerró).
6.  **Cerrar Sesión (`/auth/logout`):**
    *   Hace clic en "Cerrar Sesión" en la navegación.
    *   Es redirigido a la página de inicio.

### Administrador

1.  **Registro (Primer Usuario):**
    *   Si la base de datos está vacía, accede a `/auth/register`.
    *   Completa el formulario. Se le asigna el rol 'admin' automáticamente.
    *   Es logueado y redirigido a la página de inicio.
2.  **Iniciar Sesión (`/auth/login`):**
    *   Igual que el Juez.
3.  **Acceder al Panel de Admin:**
    *   Hace clic en el enlace "Admin" en la navegación (solo visible para admins).
4.  **Gestionar Concursos (`/admin/contests`):**
    *   Ve la lista de todos los concursos con su estado, tipo y jueces asignados.
    *   Puede hacer clic en "+ Crear Nuevo Concurso".
5.  **Crear/Editar Concurso (`/admin/contests/create`, `/admin/contests/<id>/edit`):**
    *   Rellena/modifica los detalles del concurso (título, descripción, fecha límite, estado, tipo, contraseña si es privado, número de jueces requeridos).
    *   Selecciona/deselecciona jueces de la lista "Jueces Asignados".
    *   (Opcional) Hace clic en "(+ Agregar Nuevo Juez)" para abrir la página de creación de jueces en una nueva pestaña.
    *   Guarda los cambios.
6.  **Agregar Nuevo Juez (`/admin/users/add_judge`):**
    *   (Accedido desde el enlace en el formulario de concurso o directamente).
    *   Introduce nombre de usuario y contraseña para el nuevo juez (email opcional).
    *   Crea la cuenta de juez.
    *   Vuelve a la pestaña del formulario de concurso y **refresca la página** para ver al nuevo juez en la lista de asignables.
7.  **Ver Envíos de un Concurso (`/admin/contests/<id>/submissions`):**
    *   Desde la lista de concursos, hace clic en "Ver Envíos".
    *   Ve una lista simple de los envíos para ese concurso.
    *   (Actualmente no permite ver el texto completo desde aquí).
8.  **Eliminar Concurso:**
    *   Desde la lista de concursos, hace clic en "Eliminar".
    *   Confirma la acción.
    *   El concurso (y potencialmente sus envíos/votos asociados, dependiendo de la configuración de cascada) es eliminado.
9.  **Evaluar Concursos:**
    *   El Admin tiene los mismos permisos que un Juez para evaluar (puede acceder a la interfaz de evaluación).
10. **Cerrar Sesión (`/auth/logout`):**
    *   Igual que el Juez.

## Instalación y Ejecución (Desarrollo)

1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv venv`
3. Activar el entorno: 
   * Linux/macOS: `source venv/bin/activate` 
   * Windows: `venv\Scripts\activate`
4. Instalar dependencias: `pip install -r requirements.txt`
5. Crear un archivo `.env` con las siguientes variables:
   ```
   SECRET_KEY=tu_clave_secreta_aqui # Para Flask
   OPENAI_API_KEY=tu_clave_de_openai  # Para jueces de IA
   ANTHROPIC_API_KEY=tu_clave_de_anthropic  # Para jueces de IA
   
   # Opcional: Para crear admin automáticamente
   ADMIN_USERNAME=nombre_de_usuario
   ADMIN_EMAIL=correo@ejemplo.com
   ADMIN_PASSWORD=contraseña_segura
   ```
6. Ejecutar la aplicación: `python run.py`
   * Esto creará automáticamente la base de datos (app.db)
7. Crear usuario administrador:
   * **Opción A:** Acceder a `http://127.0.0.1:5000/auth/register` y registrar el primer usuario manualmente (se convierte automáticamente en administrador).
   * **Opción B:** Ejecutar `python create_admin.py` para crear un administrador automáticamente usando las credenciales del archivo `.env`.
8. Inicializar los jueces de IA: `python seed_ai_judges.py`
   * Este paso crea los 5 jueces de IA con diferentes personalidades

## Despliegue a Producción

1. **Preparación del Servidor:**
   * Configura un servidor Linux (Ubuntu/Debian recomendado)
   * Instala Python 3.8+ y pip
   * Instala Git: `apt-get install git`
   * Instala virtualenv: `pip install virtualenv`

2. **Clonar y Configurar la Aplicación:**
   ```bash
   # Clonar el repositorio
   git clone https://github.com/tu-usuario/duelo-de-plumas.git
   cd duelo-de-plumas
   
   # Crear entorno virtual
   python -m venv venv
   source venv/bin/activate
   
   # Instalar dependencias
   pip install -r requirements.txt
   pip install gunicorn  # Servidor WSGI para producción
   
   # Configurar variables de entorno
   cp .env.example .env
   # Editar .env con editor de texto para configurar:
   # - SECRET_KEY (genera una clave segura)
   # - FLASK_ENV=production
   # - DATABASE_URL (si usas una base de datos externa)
   # - OPENAI_API_KEY y ANTHROPIC_API_KEY para los jueces de IA
   ```

3. **Configurar Gunicorn:**
   * Crea un archivo `wsgi.py` en la raíz del proyecto:
   ```python
   from app import create_app
   
   application = create_app()
   
   if __name__ == "__main__":
       application.run()
   ```
   
   * Prueba Gunicorn localmente:
   ```bash
   gunicorn --bind 0.0.0.0:8000 wsgi:application
   ```

4. **Configurar Systemd para Gestionar el Servicio:**
   * Crea un archivo de servicio:
   ```bash
   sudo nano /etc/systemd/system/duelo-de-plumas.service
   ```
   
   * Añade la configuración del servicio:
   ```
   [Unit]
   Description=Duelo de Plumas Web Application
   After=network.target
   
   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/ruta/completa/a/duelo-de-plumas
   Environment="PATH=/ruta/completa/a/duelo-de-plumas/venv/bin"
   ExecStart=/ruta/completa/a/duelo-de-plumas/venv/bin/gunicorn --workers 3 --bind unix:duelo-de-plumas.sock -m 007 wsgi:application
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   * Inicia y habilita el servicio:
   ```bash
   sudo systemctl start duelo-de-plumas
   sudo systemctl enable duelo-de-plumas
   sudo systemctl status duelo-de-plumas  # Verificar estado
   ```

5. **Configurar Nginx como Proxy Inverso:**
   * Instala Nginx: `sudo apt-get install nginx`
   * Configura un sitio para la aplicación:
   ```bash
   sudo nano /etc/nginx/sites-available/duelo-de-plumas
   ```
   
   * Añade la configuración del sitio:
   ```
   server {
       listen 80;
       server_name tu-dominio.com www.tu-dominio.com;
       
       location / {
           include proxy_params;
           proxy_pass http://unix:/ruta/completa/a/duelo-de-plumas/duelo-de-plumas.sock;
       }
       
       location /static {
           alias /ruta/completa/a/duelo-de-plumas/app/static;
       }
   }
   ```
   
   * Activa el sitio y reinicia Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/duelo-de-plumas /etc/nginx/sites-enabled
   sudo nginx -t  # Verifica la configuración
   sudo systemctl restart nginx
   ```

6. **Configurar SSL con Certbot (Opcional pero Recomendado):**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
   ```

7. **Actualizar la Aplicación (Deploy):**
   ```bash
   # Accede al directorio de la aplicación
   cd /ruta/completa/a/duelo-de-plumas
   
   # Activa el entorno virtual
   source venv/bin/activate
   
   # Obtén los últimos cambios
   git pull origin main
   
   # Instala nuevas dependencias si las hay
   pip install -r requirements.txt
   
   # Aplica migraciones de base de datos si son necesarias
   flask db upgrade
   
   # Reinicia el servicio
   sudo systemctl restart duelo-de-plumas
   ```

8. **Inicialización de la Aplicación:**
   * Para una instalación desde cero, asegúrate de:
     * **Opción A:** Acceder a la aplicación y registrar el primer usuario (que será administrador)
     * **Opción B:** Crear un administrador automáticamente:
       ```bash
       # Asegúrate de configurar ADMIN_USERNAME, ADMIN_EMAIL y ADMIN_PASSWORD en .env
       cd /ruta/completa/a/duelo-de-plumas
       source venv/bin/activate
       python create_admin.py
       ```
     * Ejecutar el script para inicializar los jueces de IA:
     ```bash
     cd /ruta/completa/a/duelo-de-plumas
     source venv/bin/activate
     python seed_ai_judges.py
     ```

9. **Verificación y Monitoreo:**
   * Verifica que la aplicación sea accesible en tu dominio
   * Configura logs y monitoreo según sea necesario:
   ```bash
   sudo journalctl -u duelo-de-plumas.service  # Ver logs del servicio
   sudo tail -f /var/log/nginx/error.log  # Ver logs de error de Nginx
   ```

10. **Backups Periódicos:**
   * Configura respaldos automáticos de la base de datos:
   ```bash
   # Ejemplo de script para backup diario de SQLite
   mkdir -p /backups/duelo-de-plumas
   sqlite3 /ruta/completa/a/duelo-de-plumas/app.db ".backup '/backups/duelo-de-plumas/backup_$(date +%Y%m%d).db'"
   
   # Añade este script a crontab para ejecutarlo diariamente
   ```

11. **Consideraciones de Seguridad:**
    * Configura un firewall (como UFW)
    * Mantén el sistema actualizado con `apt-get update` y `apt-get upgrade`
    * Considera implementar límites de tasa para prevenir abusos

## Comandos CLI Útiles

*   `flask shell`: Abre un shell interactivo con el contexto de la aplicación.
*   `flask check-contests`: Verifica concursos abiertos pasados de fecha y los mueve a evaluación; intenta calcular resultados para concursos en evaluación.

## To Do / Future Improvements

*   **Admin UI Enhancements:**
    *   Improve judge assignment in the contest edit form (e.g., search/filter for judges if the list becomes long).
    *   Consider adding pagination for lists (contests, users, submissions) in the admin panel.
    *   Allow admins to view submission text directly from the admin submission list.
*   **UI/UX:**
    *   Review the text display mechanism in the evaluation form (currently inline, was previously a toggle) for usability.
    *   Standardize confirmation messages and redirects.
    *   Improve visual design and responsiveness.
*   **Testing:**
    *   Implement unit tests for models and core logic (e.g., `calculate_contest_results`).
    *   Implement integration tests for user flows (submission, evaluation, admin actions).
*   **Seeding Script:**
    *   Make `seed_mock_data.py` more configurable (e.g., number of users, submissions via arguments).
    *   Add options to seed different scenarios (e.g., contests in 'open' state, partially judged contests).
*   **Error Handling & Robustness:**
    *   Add more specific error handling and user feedback in routes.
    *   Review input validation across all forms.
*   **Features:**
    *   Implement tie-breaking logic in `calculate_contest_results`.
    *   Allow user registration beyond just judges/admin (optional feature).
    *   Consider email notifications (e.g., when assigned as judge, contest closing).
*   **Deployment:**
    *   Add detailed deployment instructions (e.g., using Gunicorn, Nginx, Docker).
*   **Security:**
    *   Perform a security review (CSRF, XSS, SQL Injection, permissions).
