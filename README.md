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
*   Soporte para formato Markdown en descripciones de concursos y textos de participantes.

## Flujos de Usuario

### Visitante / Participante

1.  **Ver Inicio (`/`):** Ve la introducción, una lista de concursos públicos activos y una lista de concursos recién finalizados (con ganadores).
2.  **Ver Concursos (`/contests`):** Ve listas de concursos públicos agrupados por estado: Abiertos, En Evaluación, Finalizados (con ganadores).
3.  **Ver Detalles de Concurso (`/contest/<id>`):** Ve la descripción, estado y fecha límite de un concurso específico. La descripción ahora se renderiza con formato Markdown.
4.  **Enviar Texto (si el concurso está Abierto):**
    *   Accede a los detalles del concurso (`/contest/<id>`).
    *   Rellena el formulario con Nombre de Autor, Título del Texto y el Contenido.
    *   El campo de contenido cuenta con un editor Markdown para dar formato al texto.
    *   Envía el formulario.
    *   Ve un mensaje de confirmación.
5.  **Ver Resultados (si el concurso está Cerrado):**
    *   Accede a los detalles del concurso (`/contest/<id>`).
    *   Ve la lista de envíos ordenada por ranking.
    *   Ve los puntos totales de cada envío.
    *   Ve el texto completo de cada envío con formato Markdown.
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
    *   Puede hacer clic en "Mostrar/Ocultar Texto" para leer cada envío con formato Markdown.
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
    *   La descripción del concurso utiliza un editor Markdown para dar formato al texto.
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
   
   # Obligatorio para init_db.py
   ADMIN_USERNAME=nombre_de_usuario
   ADMIN_EMAIL=correo@ejemplo.com
   ADMIN_PASSWORD=contraseña_segura
   ```
6. Ejecutar la aplicación **por primera vez**: `python run.py`
   * Esto creará automáticamente la base de datos (`app.db` por defecto) si no existe.
   * Puedes detener la aplicación después de que la base de datos se haya creado.
7. **Inicializar la base de datos:** Ejecutar `python init_db.py`
   * **Importante:** Este script debe ejecutarse *después* de que la base de datos haya sido creada (paso 6).
   * Creará el usuario administrador usando las credenciales del archivo `.env`.
   * Creará los jueces de IA iniciales.
   * Creará un concurso de ejemplo ("Muestra") con textos del directorio `/examples`.
8. Ejecutar la aplicación para usarla: `python run.py`

## Configuración Inicial del Servidor VPS (Ubuntu 24.04)

Si estás configurando un nuevo VPS Ubuntu 24.04 desde cero, sigue estos pasos iniciales antes de desplegar la aplicación.

### Conexión Inicial y Seguridad Básica

1.  **Conexión inicial:**
    ```bash
    ssh root@your_host_ip
    ```
    Ingresa la contraseña inicial cuando se te solicite.

2.  **Actualizar el sistema:**
    ```bash
    apt update && apt upgrade -y
    ```

3.  **Crear un usuario no-root:** Es más seguro operar con un usuario con privilegios `sudo`.
    ```bash
    adduser yourusername
    usermod -aG sudo yourusername
    ```
    Reemplaza `yourusername` con el nombre de usuario deseado.

4.  **Configurar autenticación por clave SSH (Recomendado):**
    *   En tu **máquina local**, genera una clave si no tienes una:
        ```bash
        # Usa ed25519 para mayor seguridad
        ssh-keygen -t ed25519 
        ```
        (Acepta las ubicaciones por defecto y opcionalmente añade una passphrase).
    *   Copia tu clave pública al servidor:
        ```bash
        ssh-copy-id yourusername@your_host_ip
        ```
    *   Ahora deberías poder conectar como tu nuevo usuario sin contraseña:
        ```bash
        ssh yourusername@your_host_ip
        ```

5.  **Asegurar la configuración SSH:** Edita el archivo de configuración SSH en el servidor.
    ```bash
    sudo nano /etc/ssh/sshd_config
    ```
    Realiza (o verifica) estos cambios para mayor seguridad:
    *   Cambia el puerto por defecto (obfuscación):
        `Port 2299` # Cambia 2299 por otro puerto no estándar si lo deseas.
    *   Deshabilita el login de root:
        `PermitRootLogin no`
    *   Deshabilita la autenticación por contraseña (si la clave SSH funciona):
        `PasswordAuthentication no`
    *   Asegúrate de que `PubkeyAuthentication` esté en `yes`.

    Guarda el archivo (Ctrl+X, luego Y, luego Enter en `nano`) y reinicia el servicio SSH para aplicar los cambios:
    ```bash
    sudo systemctl restart ssh.service
    ```
    **Importante:** ¡Asegúrate de que puedes conectar con el nuevo puerto (`ssh -p 2299 yourusername@your_host_ip`) *antes* de desconectar tu sesión actual! Si algo falla, puedes revertir los cambios en `sshd_config`.

### Configuración del Firewall (UFW)

6.  **Instalar y configurar UFW:**
    ```bash
    sudo apt install ufw
    # Permite el nuevo puerto SSH (¡MUY IMPORTANTE!)
    sudo ufw allow 2299/tcp # Usa el puerto que configuraste en sshd_config
    # Permite tráfico web estándar
    sudo ufw allow http 
    sudo ufw allow https
    # Habilita el firewall
    sudo ufw enable 
    # Verifica el estado
    sudo ufw status verbose
    ```
    Esto establece reglas básicas. Asegúrate de abrir otros puertos si tu aplicación los necesita.

Con estos pasos, tu servidor tiene una configuración base más segura. Ahora puedes proceder con el despliegue específico de la aplicación Duelo de Plumas.

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
   # Nota sobre estructura de directorios para múltiples sitios:
   # Si planeas alojar múltiples sitios, es una buena práctica clonar
   # la aplicación dentro de una estructura como /var/www/tu-dominio.com/app
   # Asegúrate de que el usuario que ejecutará la aplicación (p. ej., www-data)
   # tenga los permisos adecuados: sudo chown -R www-data:www-data /var/www/tu-dominio.com && sudo chmod -R 755 /var/www/tu-dominio.com
   
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
   # - ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD (obligatorios para init_db.py)
   ```

3. **Configurar Gunicorn y WSGI:**
   * Asegúrate de que tienes un archivo `wsgi.py` en la raíz (como se muestra en el ejemplo del README original).
   * La primera vez que Gunicorn/WSGI se ejecute (o al crear la base de datos si usas un gestor externo), la estructura de la base de datos se creará.

4. **Inicializar la Base de Datos:**
   * **Importante:** Después de que la base de datos haya sido creada por la aplicación, ejecuta el script de inicialización:
     ```bash
     # Asegúrate de estar en el directorio del proyecto y con el entorno activado
     python init_db.py
     ```
   * Este script creará el administrador, los jueces de IA y el concurso de ejemplo usando las credenciales del archivo `.env`.

5. **Configurar Systemd para Gestionar el Servicio:**
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

6. **Configurar Nginx como Proxy Inverso:**
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

7. **Configurar SSL con Certbot (Opcional pero Recomendado):**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
   ```

8. **Actualizar la Aplicación (Deploy):**
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
    *   ✅ Add Markdown support for contest descriptions and submission texts.
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
