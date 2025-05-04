* Hay un admin que tiene control y acceso a todas las funcionalidades. Es un super usuario. No tienen ninguna restricción.
* Los usuarios, identificados por una cuenta gratuita. Ellos tienen la capacidad de:
    * Elegir un username único con el que se les identificará.
    * Crear concursos
    * Editar y borrar concursos creados por ellos mismos. 
    * Participar como autores en concursos creados por otros usuarios siempre y cuando sean públicos o cuando sean privados y cuenten con la contraseña para tener acceso
    * Participar como jueces en concursos donde estén registrados como tales.
    * Crear jueces y escritores IA
    * Editar y borrar jueces y escritories IA creados por ellos
    * Ejecutar acciones con sus jueces IA (evaluar) o escritores IA (escribir), siempre y cuando tengan suficientes créditos. Cada acción tendrá un costo asociado en créditos basado en el modelo LLM utilizado y el consumo (tokens).
    * Consultar su balance de créditos actual.
    * Ver listados todos los concursos en existencia, incluidos los privados
    * Los usuarios empiezan con 0 créditos al registrarse. Sólo el administrador puede asignarles créditos.
* Los usuarios NO pueden:
    * Ejecutar acciones IA si no tienen suficientes créditos.
    * Editar o borrar concursos, jueces IA o escritores IA no creados por ellos mismos
* Los visitantes, que son aquellos que no han iniciado sesión, pueden:
    * Crear una cuenta gratuita para volverse usuarios
    * Ver listados todos los concursos en existencia, incluidos los privados
    * Ver el detalle de los concursos públicos y de los privados de los que tenga el password.

* Los concursos:
    * Los concursos se definen de manera obligatoria por un título y una descripción (que tiene las indicaciones para el concurso). Se identifican por un número único de concurso irrepetible. Esto se puede hacer en un formato Markdown.
    * Los concursos tienen además, de manera opcional, un número mínimo requerido de votos y un listado de jueces asignados. 
    * Los concursos tienen, de manera opcional, la posibilidad de restringir que los jueces asignados no participen como autores, o que los autores no puedan meter más de un texto. El administrador queda exento de estas restricciones.
    * Pueden ser públicos o privados. La única diferencia es que los privados requieren un password para poder participar en ellos o ver el detalle.
    * Pueden estar en tres estados: abiertos, en evaluación o cerrados.
        * En un concurso abierto se reciben textos. No se pueden recibir votos. 
        * En uno en evaluación no se reciben textos, pero se reciben votos de los jueces
        * En uno cerrado, no se reciben ni votos ni textos.
        * Un administrador puede en cualquier momento añadir un texto o añadir un voto. El administrador no tiene restricciones.
    * Cuando un concurso está abierto, nadie salvo el administador puede ver los textos participantes. 
    * Cuando un concurso está en evaluación, o está cerrado, todo aquel con acceso al concurso puede ver los textos participantes.
    * Los concursos tienen una fecha de creación, una de última modificación y una de término [opcional]. 
        * Los concursos se listan en orden de creación
        * Los concursos más allá de su fecha de término, si estan abiertos, pasan a estar en evaluación. 
    * Cuando un concurso tiene todos sus votos, automáticamente se cierra.
    * Un concurso siempre muestra, independientemente de sus características, su título, su descripción (breve o cortada), su creador, su fecha de última modificación y si tiene, su fecha de término. También muestra el número de autores y de textos que se han recibido.
    * tienen una página propia donde se puede ver el detalle, y dependiendo de su estado, la capacidad de someter un texto o ver los ganadores.
    * Si un concurso se borra, se borran los votos asociados pero no los textos. 

* Los textos:
    * Se reciben en formato Markdown
    * Tienen tres campos. Autor, Título, Texto. Se identifican por un número único.
    * Al ser sometidos a un concurso, mientras el concurso esté abierto o en evaluación, nadie (salvo el administrador) puede ver el nombre del autor. Este se reemplazará por un código para mantener el anonimato.
    * En un concurso cerrado, se revela el nombre de los autores.
    * Un autor puede en cualquier momento borrar un texto suyo.
    * Un administrador puede en cualquier momento borrar cualquier texto. 
        * En caso de que el concurso esté en evaluación o cerrado, este se sustituirá por una leyenda TEXTO RETIRADO. Si el concurso está abierto, simplemente se borrará su texto.


* Los votos:
    * Pueden ser emitidos por jueces humanos o por jueces IA
    * Se asignan 3 puntos a un primer lugar, 2 puntos a un segundo lugar y 1 punto a un tercer lugar.
    * Junto con cada voto, se da una justificación/comentario acerca del voto emitido
    * Los textos que no alcancen una calificación, podrán aún así recibir una justificación/comentario sobre su evaluación

* Los jueces y escritores IA:
    * Son ejecutados directamente por el usuario si este tiene créditos suficientes. El costo en créditos se deduce automáticamente dependiendo del costo real incurrido.
    * Son identificados por un nombre único, una breve descripción y un prompt de personalidad
    * Tienen un prompt base que les da las instrucciones de qué hacer que es el mismo para todos
    * Un mismo juez/escritor puede ser ejecutado con diferentes modelos de LLMs determinados a partir de una lista
    * Los jueces y escritores creados por un usuario sólo están disponibles para ese usuario.
    * Los jueces y escritores creados por el administrador están disponibles para todos los usuarios.

* La página cuenta:
    * Para todos con:
        * La posibilidad de registrarse como usuario
        * La posibilidad de iniciar sesión ya sea como usuario o como administrador
        * Una página de inicio, donde se muestran los concursos abiertos y los concursos cerrados recientemente. 
        * Una página de listado de todos los concursos, donde se muestran absolutamente todos los concursos.
    * Para usuarios:
        * Un listado de acciones urgentes (como concursos pendientes por evaluar) en la página de inicio
        * La posibilidad de participar en o crear concursos.
        * Una página propia donde se pueden consultar los concursos donde se ha participado ya sea como juez o como autor. También ahí un listado de todos los textos sometidos. También esta página con un lugar para gestionar sus escritores y jueces IA.

    * Para el administrador:
        * todo lo que un usuario y además:
        * Un lugar para administrar cuentas de usuarios (incluyendo la asignación de créditos).
        * Un lugar para administrar jueces y escritores IA (globales y, potencialmente, ver/borrar los de usuarios).
        * Un lugar para administrar concursos
        * Un lugar para monitorear costos reales de IA y consumo de créditos por usuario.
        * Un lugar para ver el resumen del sitio (número de concursos, una tabla de ganadores más frecuentes, etc.)

