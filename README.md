# P3-MSR

## Descripción
Este repositorio contiene el análisis de la simulación de un rover equipado con un brazo SCARA y un actuador final (gripper) en un entorno de simulación (Gazebo/RViz2).

## Estructura
Para el desarrollo de la práctica se han hecho uso de los siguientes paquetes:
- `rover_description`: contiene la descripción URDF/Xacro del rover al completo, los controladores de la base y dos de los launchers usados: `robot_state_publisher.launch.py` y `rover_controllers.launch.py`
- `rover_moveit_config`: contiene la configuración hecha con MoveIt Setup Assistant, con eel tercer launcher usado, necesario para usar el plugin de MoveIt en RViz: `move_group.launch.py`
- `urjc-excavation-world`: contiene el mundo de Gazebo usado. [(enlace)](https://github.com/juanscelyg/urjc-excavation-world)

## Robot en RViz
En esta captura se demuestra el correcto funcionamiento de las TFs y el `joint_state_publisher_gui`:

<img width="1846" height="1009" alt="rviz" src="https://github.com/user-attachments/assets/e00ad62b-077d-44a1-8ad8-5cb6f9b91e90" />

## Árbol de transformadas
Este es el árbol de transformadas: [tf_tree](data/tf_tree.pdf)

## Simulación
El propósito de la simulación consiste en ejecutar una secuencia de tres tareas operativas:
- Almacenar el cubo verde en el compartimento de carga del rover.
- Realizar una maniobra de pick and place para trasladar el cubo azul (situado a la izquierda) y apilarlo sobre el cubo rojo (ubicado a la derecha).
- Ejecutar un desplazamiento en línea recta usando `teleop_twist_keyboard` para publicar comandos de velocidad en `/cmd_vel`

### Cubo verde sujeto en el aire
<img width="721" height="680" alt="cubo_verde" src="https://github.com/user-attachments/assets/1493bb42-c404-42f8-b7ee-2fc93c1da0f2" />

### Cubo azul sobre cubo rojo
<img width="721" height="680" alt="cubo_azul" src="https://github.com/user-attachments/assets/f0627ef1-9fde-422d-818a-8ada1ad7687a" />

Además se ha conseguido que el cubo azul se quede sobre el rojo:
<img width="721" height="680" alt="azul_sobre_rojo" src="https://github.com/user-attachments/assets/49de774c-1004-49b1-87dd-83bc769f0933" />

### Vídeo
Este es el vídeo de la simulación completa. Se puede observar que ha costado coger el cubo azul debido a que se movía, pero finalmente se ha conseguido.

https://github.com/user-attachments/assets/0dc2bd32-be5b-4a63-a649-3f6f85747109

## Análisis de la simulación
A partir de los datos del rosbag en el cual se han grabado los topics `/cmd_vel`, `/imu` y `/joint_states`, se han generado tres gráficas para estudiar el resultado.
### Rosbag
Este es el rosbag resultante: [Descargar](https://github.com/AlejandroYG14/P3-MSR/releases/download/v1.0/rosbag.zip)

### Ruedas vs Tiempo
<img width="2000" height="1000" alt="pos_ruedas" src="https://github.com/user-attachments/assets/bb6a1b5e-a9f3-4224-9f14-b66a5d68de0f" />

Se ha generado leyendo el topic `/joint_states`, extrayendo específicamente la variable `position` (en radianes) de los joints de las ruedas.

Aquí se muestra que el rover empieza quieto, luego hace maniobras de giro sobre sí mismo (las ruedas izquierdas y derechas giran en sentidos opuestos) para orientarse hacia los cubos, y termina con una aceleración sincronizada donde todas avanzan a la vez para ir línea recta.

### Aceleración (IMU) vs Tiempo
<img width="2000" height="1000" alt="aceleracion_imu" src="https://github.com/user-attachments/assets/f7be8c81-a679-45ea-bf70-e5a1e4220635" />

Se ha generado leyendo el topic `/imu`, extrayendo directamente los valores físicos del vector `linear_acceleration` (ejes X, Y y Z)

Refleja la gravedad constante en el eje Z (peso del robot), picos bruscos cuando el movimiento del brazo transmite sacudidas al chasis (sobre todo por los intentos de coger el cubo azul) . Además, un ruido continuo de vibraciones en X e Y al final, provocado por el rozamiento de las ruedas contra el suelo al avanzar.

### Gasto vs Tiempo
<img width="2000" height="1000" alt="gasto_pick_place" src="https://github.com/user-attachments/assets/a7e5e69a-a069-405d-bee6-242ead008ac9" />

Se ha generado leyendo el topic `/joint_states`, extrayendo la variable `effort` (fuerza o par motor) exclusiva de las articulaciones del brazo y la pinza, y aplicando en cada instante el sumatorio de sus valores absolutos según la fórmula:
<img width="195" height="72" alt="image" src="https://github.com/user-attachments/assets/4b8697fb-9fbf-4385-9683-cc5a611156e0" />

Se observan dos grandes bloques de gran esfuerzo en los motores del brazo: uno corto para recoger el cubo verde, y uno más largo y complejo para apilar el azul sobre el rojo. El resto del tiempo el gasto cae a casi cero porque el brazo descansa mientras la base se mueve.


