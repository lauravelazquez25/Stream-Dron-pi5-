# Stream-Dron-pi5-

### INTRODUCCION A LOS SISTEMAS DISTRIBUIDOS Y PARALELOS
Proyecto Final Integrador: Sistema concurrente de transmisión distribuida para monitoreo con dron
---



Universidad Nacional de Rio Negro - Sede Bariloche -Primer Cuatrimestre 2025

### Asignatura: Introduccion a los Sistemas Distribuidos y Paralelos

Docente: Walter Agüero
---

Estudiante: Laura Velazquez
---

Este notebook tiene como propósito documentar el desarrollo del proyecto de promoción de la asignatura Sistemas Distribuidos y Paralelos, en articulación con el trabajo que se está realizando en la asignatura Laboratorio de Sistemas Embebidos. Se busca no sólo cumplir con los objetivos técnicos de ambas materias, sino también generar un aporte significativo en términos de integración, visión de sistemas y aplicación real, a mi formación profesional.

### Descripción del Proyecto
El proyecto tiene como base el desarrollo de un sistema de monitoreo embarcado en un dron, equipado con una cámara CSI conectada a una Raspberry Pi 5 de 8 GB, con el objetivo de capturar y transmitir video en tiempo real. La estación base, también implementada con tecnología embebida, permite supervisar y controlar los procesos de vuelo, comunicación y procesamiento distribuido.

Este trabajo surge de una integración entre dos asignaturas: **Sistemas Distribuidos y Paralelos** y **Laboratorio de Sistemas Embebidos**, combinando el control de sensores (IMU, distancia, altitud) con la transmisión de video y el procesamiento concurrente de imágenes.

La Etapa 1 del desarrollo se centra en la captura de video mediante una cámara CSI y la transmisión del stream en tiempo real, utilizando un servidor HTTP embebido desarrollado en Python. Si bien el sistema puede operar en red local, la intención principal es compartir la transmisión en vivo con un cliente remoto, de forma que un operador autorizado pueda visualizar en tiempo real las imágenes captadas por el dron desde cualquier ubicación con acceso a red.

Esta transmisión se gestiona mediante lógica de programación concurrente con hilos (threading), lo que permite mantener la captura y la publicación del video en paralelo y sin bloqueos.

En la Etapa 2 se incorporará una red neuronal preentrenada mediante TensorFlow Lite, con el propósito de realizar reconocimiento facial en tiempo real sobre los frames capturados. El objetivo final es que el dron sea capaz de identificar visualmente a una persona desaparecida, como parte de un sistema de búsqueda y rescate autónomo, integrando visión artificial, procesamiento paralelo y movilidad aérea.

La elección de la Raspberry Pi 5 responde a su capacidad de cómputo, su compatibilidad con aceleración por hardware (GPU), y su integración directa con periféricos CSI y sensores, facilitando un entorno ideal para la implementación de algoritmos concurrentes y distribuidos en tiempo real con aplicaciones de inteligencia artificial embebida.

### Justificación del Enfoque Integrado
Dado el carácter interdisciplinario del proyecto, se propone abordarlo integrando contenidos de dos asignaturas clave:

**Laboratorio de Sistemas Embebidos**: implementación física y programación de los sensores y actuadores del dron.
**Sistemas Distribuidos y Paralelos**: desarrollo del sistema de transmisión concurrente de video, control distribuido y procesamiento embebido.
Este enfoque me permite consolidar aprendizajes vinculados a la lógica de programación orientada a objetos y a la estructuración de sistemas paralelos en escenarios reales. A través del uso de herramientas como threading, Lock, Queue, OpenCV, Flask y TensorFlow Lite, el proyecto se convierte en un espacio de aplicación concreta de conceptos avanzados sobre concurrencia, comunicación y visión computacional.

El profesor Walter Agüero ha propuesto como desafío adicional la creación de un objeto concurrente accesible por dirección IP, capaz de transmitir imágenes en tiempo real desde el dron, y ha sugerido explorar su aplicación en escenarios reales de búsqueda de personas mediante visión artificial embebida.

### Objetivos Técnicos
**Arquitectura de la Etapa 1**
Cámara CSI conectada a la Raspberry Pi 5 de 8GB
Captura de video mediante OpenCV (cv2)
Servidor Flask o HTTP que transmite el video en tiempo real
Uso de hilos (threading) para separar captura y transmisión

### Aclaracion

En este repositorio sólo se incluye la programacion del stream del video capturado por la camara CSI embebida en la Raspberry pi5
