import os
import sys

def check_playwright(application_path: str):
    """ 
    Configura las rutas de Playwright. En modo producción (.exe),
    verifica si Chromium existe; si no, lo descarga e instala de forma
    aislada en la carpeta de la aplicación la primera vez.
    """
    print("Verificando estado de Playwright...")
    try:
        es_produccion = getattr(sys, 'frozen', False)

        if es_produccion:
            # Guardamos los navegadores en la raíz del programa (fuera de _internal por temas de permisos)
            ruta_navegadores = os.path.join(os.environ["LOCALAPPDATA"], "SaludsaActas", "playwright-browsers")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ruta_navegadores
            print(f"Ruta asignada para navegadores (Producción): {ruta_navegadores}")
            
            # Comprobamos si Chromium ya fue descargado previamente
            chromium_instalado = False
            if os.path.exists(ruta_navegadores):
                # Buscamos si existe alguna carpeta del tipo 'chromium-1234'
                for item in os.listdir(ruta_navegadores):
                    if item.startswith("chromium-"):
                        chromium_instalado = True
                        break
            
            # Solo ejecutamos la instalación si es la primera vez y la carpeta está vacía
            if not chromium_instalado:
                print("Primera ejecución detectada. Descargando Chromium de forma aislada (esto puede tardar)...")
                
                # Al haber añadido el driver en el Paso 1, este import ahora sí funcionará con sus binarios
                from playwright.__main__ import main as playwright_main
                argumentos_originales = sys.argv       
                
                try:
                    # Forzamos el comando interno: playwright install chromium
                    sys.argv = ["playwright", "install", "chromium"]
                    playwright_main()
                    print("ÉXITO: Chromium se ha descargado y configurado correctamente.")
                except SystemExit:
                    print("Verificación de descarga finalizada exitosamente.")
                finally:
                    # Restauramos los argumentos para no romper el ciclo de Flask/Waitress
                    sys.argv = argumentos_originales
            else:
                print(f"Chromium detectado en: {ruta_navegadores}. Saltando instalación.")
                
        else:
            print("Modo desarrollo detectado: Usando la instalación nativa del .venv")
            if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
                del os.environ["PLAYWRIGHT_BROWSERS_PATH"]
            return

    except Exception as e:
        print(f"ERROR CRÍTICO al inicializar Playwright: {e}")
