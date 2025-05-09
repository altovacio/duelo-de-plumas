Duelo de plumas.

Es una plataforma de concursos literarios. Consta de un backend y un frontend. 

En esta plataforma los usuarios pueden subir textos a concursos y, opcionalmente, usar herramientas IA tales como jueces o escritores IA, pero el foco es el concurso, el cual también puede ser realizado únicamente por humanos.



## Usuarios

### tipos de usuarios

Hay tres tipos de usuarios: Administrador, Usuario y Visitante

#### Visitante
* Los visitantes, que son aquellos que no han iniciado sesión, pueden:
    * Crear una cuenta gratuita para volverse usuarios
    * Ver listados todos los concursos en existencia, incluidos los privados
    * Ver el detalle de los concursos públicos y de los privados de los que tenga el password.

#### Usuario
* Los usuarios, identificados por una cuenta gratuita. Ellos tienen todas las capacidades de visitantes y además:
    * Elegir un username único con el que se les identificará.
    * Cada usuario tendrá su espacio de trabajo, donde podrá:
        * Crear, editar y borrar concursos
        * Crear, editar y borrar textos
        * Crear, editar y borrar escritores y jueces IA
        * Ejecutar acciones con sus jueces IA (evaluar) o escritores IA (escribir), siempre y cuando tengan suficientes créditos. Cada acción tendrá un costo asociado en créditos basado en el modelo LLM utilizado y el consumo (tokens).
        * Consultar su balance de créditos actual.
    * Participar como autores en concursos creados por otros usuarios siempre y cuando sean públicos o cuando sean privados y cuenten con la contraseña para tener acceso
    * Participar como jueces en concursos donde estén registrados como tales.
    * Los usuarios empiezan con 0 créditos al registrarse. Sólo el administrador puede asignarles créditos.
* Los usuarios NO pueden:
    * Ejecutar acciones IA si no tienen suficientes créditos.
    * Editar o borrar concursos, textos, jueces IA o escritores IA de los que no sean dueños.

#### Administrador
* Hay un admin que tiene control y acceso a todas las funcionalidades. Es un super usuario. No tiene ninguna restricción.

### Eliminacion de un usuario
* Cuando un usuario se elimina, se borran todos los concursos, textos, escritores y jueces IA que haya creado. Sin embargo, el registro de los costos y de sus créditos queda guardado.
* Sólo un administrador puede borrar un usuario

## Textos
* Los textos puede ser generados en el sitio usando un editor de Markdown o ser subidos en formato .pdf
* Se identifican por un número único.
* los textos tienen 4 propiedades:
    * Dueño
    * Autor
    * Título
    * Contenido
* El dueño es quien tiene la capacidad administrativa (borrar, editar, meter a concursos)
* El autor es quien lo escribió. Notemos que el autor no necesariamente es el dueño
* Los textos pueden ser sometidos a concursos. De ser así, recibirán un lugar y un comentario por parte de los jueces. Un texto puede tener asociados múltiples lugares y múltiples comentarios.

## Concursos

Los concursos son espacios donde varios textos compiten por un primer, segundo y tercer lugar. 
En específico:
* Los concursos se definen de manera obligatoria por un título y una descripción (que tiene las indicaciones para el concurso). Se identifican por un número único de concurso irrepetible.
* El título y descripción se editan en formato Markdown
* Los concursos tienen, de manera opcional, un número mínimo requerido de votos y un listado de jueces asignados. 
* Los concursos tienen, de manera opcional, la posibilidad de restringir que los jueces asignados no participen como autores, o que los autores no puedan meter más de un texto. El administrador queda exento de estas restricciones.
* Los concursos tienen una carátula y un detalle. 
    * En la carátula va el título, breve descripción, número de participantes, fecha de última modificación, fecha de término [si hay], su tipo y su estado. La carátula es visible a todos.
    * En el detalle se ve todo lo de la carátula más la descripción completa y:
        * Si el concurso está abierto, un lugar para someter un texto a participación
        * Si están cerrados, el ranking final del concurso, donde se pueden leer los textos y los comentarios de los jueces. 
* Tipo: Pueden ser públicos o privados. La única diferencia es que los privados requieren un password para poder participar en ellos o ver el detalle.
* Estado: Pueden estar en tres estados: abiertos, en evaluación o cerrados.
    * En un concurso abierto se reciben textos. No se pueden recibir votos. 
    * En uno en evaluación no se reciben textos, pero se reciben votos de los jueces
    * En uno cerrado, no se reciben ni votos ni textos.
* Cuando un concurso está abierto, nadie salvo el administador o el creador del concurso puede ver los textos participantes. 
* Cuando un concurso está en evaluación, o está cerrado, todo aquel con acceso al concurso puede ver los textos participantes.
* Los concursos tienen una fecha de creación, una de última modificación y una de término [opcional]. 
    * Los concursos se listan en orden de creación
    * Los concursos más allá de su fecha de término, si estan abiertos, pasan a estar en evaluación. 
* Cuando un concurso tiene todos sus votos, automáticamente se cierra.
* Un concurso siempre muestra, independientemente de sus características, su título, su descripción (breve o cortada), su creador, su fecha de última modificación y si tiene, su fecha de término. También muestra el número de autores y de textos que se han recibido.
* tienen una página propia donde se puede ver el detalle, y dependiendo de su estado, la capacidad de someter un texto o ver los ganadores.

### eliminación de un concurso
* Si un concurso se borra, se borran los votos asociados pero no los textos. 

### Los textos dentro de un concurso
* Mientras el concurso esté abierto o en evaluación, nadie (salvo el administrador) puede ver el nombre del autor ni del dueño.
* En un concurso cerrado, se revela el nombre de los autores y de los dueños.
* Un dueño puede en cualquier momento retirar un texto suyo.
* Un administrador puede en cualquier momento retirar cualquier texto. 
    * En caso de que el concurso esté en evaluación o cerrado, este se sustituirá por una leyenda TEXTO RETIRADO. Si el concurso está abierto, simplemente se retirará el texto sin dejar marca.

### Los votos:
* Pueden ser emitidos por jueces humanos o por jueces IA
* Se asignan 3 puntos a un primer lugar, 2 puntos a un segundo lugar y 1 punto a un tercer lugar.
* Junto con cada voto, se da una justificación/comentario acerca del voto emitido
* Los textos que no alcancen una calificación, podrán aún así recibir una justificación/comentario sobre su evaluación
* Los votos hechos por una IA registran el nombre del juez, el modelo usado y la versión base.

## Los jueces y escritores IA
* Son ejecutados directamente por el usuario si este tiene créditos suficientes. El costo en créditos se deduce automáticamente dependiendo del costo real incurrido.
* El usuario define su nombre, una breve descripción y un prompt de personalidad. Este usuario es el dueño.
* Tienen un mecanismo base, no editable por el usuario. Este mecanismo tiene una versión. La version es visible para el usuario.
* En su primera versión, el mecanismo base será un único prompt
* Un mismo juez/escritor puede ser ejecutado con diferentes modelos de LLMs determinados a partir de una lista
* Los jueces y escritores creados por un usuario sólo están disponibles para ese usuario.
* Los jueces y escritores creados por un administrador aparecerán en una base pública, de la cual, un usuario podra generar una copia.
* Los jueces y escritores se identifican por el dueño y un número 

## La página
* La página cuenta:
    * Una sección de iniciar sesión/ registrarse
    * Una página de inicio:
        * Mensaje de bienvenida
        * Highlight/selección de concursos abiertos recientemente
        * Highlight/selección de concursos cerrados recientemente
    * Una página de listado de todos los concursos, donde se muestran absolutamente todos los concursos.
    * Una página, taller de trabajo, visible para todos pero sólo disponible para usuarios registrados, donde el usuario puede:
         * administrar sus textos y sus agentes ai. 
         * Ver el listado de concursos donde participa como autor
         * Ver el listado de concursos donde participa como juez
         * Lista de acciones urgentes por tomar (por ejemplo, concursos a evaluar)
         * Ver sus créditos disponibles
         * Ver su historial de consumo de créditos.
    * Para usuarios se muestra todo lo que está disponible para visitantes y además:
        * Un listado de acciones urgentes (como concursos pendientes por evaluar) en la página de inicio
        * La posibilidad de participar en concursos.
        * Una página propia donde se pueden consultar los concursos donde se ha participado ya sea como juez o como autor. También ahí un listado de todos los textos sometidos. También esta página con un lugar para gestionar sus escritores y jueces IA.

    * Para el administrador:
        * todo lo que un usuario y además:
        * Un lugar para administrar cuentas de usuarios (incluyendo la asignación de créditos).
        * Un lugar para administrar jueces y escritores IA globales.
        * Un lugar para monitorear costos reales de IA y consumo de créditos por usuario.
        * Un lugar para ver el resumen del sitio (número de concursos, una tabla de ganadores más frecuentes, etc.)

