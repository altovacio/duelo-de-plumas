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

1.  Clonar el repositorio.
2.  Crear un entorno virtual: `python -m venv venv`
3.  Activar el entorno: `source venv/bin/activate` (Linux/macOS) o `venv\Scripts\activate` (Windows)
4.  Instalar dependencias: `pip install -r requirements.txt`
5.  Crear un archivo `.env` y definir `SECRET_KEY` (ver `config.py`).
6.  (Opcional) Eliminar `app.db` si existe y se quiere empezar de cero.
7.  Ejecutar la aplicación: `flask run` o `python run.py`
8.  Acceder a `http://127.0.0.1:5000`
9.  Registrar el primer usuario (admin) vía `/auth/register`.

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
