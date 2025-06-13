# app/flask_app.py
# Este script inicia la app Flask y configura correctamente las rutas a las carpetas /static y /templates
# que están en el directorio raíz del proyecto (no dentro de /app).

from flask import Flask, render_template  # Importamos Flask y la función para renderizar plantillas HTML
import os  # Para trabajar con rutas del sistema
from app import stream_manager  # Importamos el módulo stream_manager desde el paquete app

# Calculamos la ruta base de este archivo (es decir, app/)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Creamos la aplicación Flask, pero indicamos explícitamente dónde están las carpetas static y templates
# Usamos rutas relativas desde app/ hacia el root del proyecto
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, '../static'),
    template_folder=os.path.join(BASE_DIR, '../templates')
)

# Ruta principal del servidor web Flask
@app.route('/')
def index():
    # Verificamos si el stream está activo, usando una función del módulo stream_manager
    stream_activo = stream_manager.is_stream_active()

    # Renderizamos index.html y le pasamos el estado del stream a través de una variable llamada stream_activo
    return render_template('index.html', stream_activo=stream_activo)

# Este bloque se ejecuta solo si este archivo se corre directamente (no si es importado como módulo)
if __name__ == '__main__':
    # Aseguramos que el directorio donde se guardan los fragmentos HLS exista
    os.makedirs(os.path.join(BASE_DIR, '../static/hls'), exist_ok=True)

    # Iniciamos la app en modo escucha en todas las interfaces disponibles, puerto 5000
    app.run(host='0.0.0.0', port=5000)




