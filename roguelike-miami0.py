import curses
import random
from collections import deque
import time

# Función para generar el laberinto conectado sin recursión infinita
def generar_laberinto_conectado(height, width):
    """Genera un laberinto conectado de manera iterativa para evitar recursión infinita."""
    mapa = [["#" for _ in range(width)] for _ in range(height)]  # Inicializa el mapa con paredes
    
    # Elige un punto de inicio aleatorio dentro del mapa
    inicio_x, inicio_y = random.choice(range(1, width, 2)), random.choice(range(1, height, 2)) 
    stack = deque([(inicio_x, inicio_y)])  # Pila para recorrer el mapa
    mapa[inicio_y][inicio_x] = " "  # Marca el punto de inicio como espacio vacío

    # Algoritmo para abrir caminos en el laberinto
    while stack:
        x, y = stack.pop()  # Tomar la última posición de la pila
        direcciones = [(0, -1), (0, 1), (-2, 0), (2, 0)]  # Direcciones posibles para avanzar
        random.shuffle(direcciones)  # Aleatoriza las direcciones para que el laberinto sea impredecible
        for dx, dy in direcciones:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and mapa[ny][nx] == "#":
                # Si el siguiente lugar es una pared, abrir el camino
                mapa[y + dy // 2][x + dx // 2] = " "  # Abre el camino intermedio
                mapa[ny][nx] = " "  # Abre el camino final
                stack.append((nx, ny))  # Añade la nueva posición a la pila para continuar

    # Más apertura de pasillos aleatoria
    for _ in range(height * width // 10):
        x, y = random.randint(1, width - 2), random.randint(1, height - 2)
        if mapa[y][x] == "#":
            mapa[y][x] = " "  # Si el lugar es una pared, lo convierte en espacio vacío
    return mapa

# Función para colocar elementos en posiciones aleatorias del mapa
def colocar_elementos(mapa, char, cantidad):
    """Coloca elementos en posiciones aleatorias del mapa."""
    height, width = len(mapa), len(mapa[0])  # Obtener las dimensiones del mapa
    for _ in range(cantidad):  # Coloca la cantidad de elementos especificados
        while True:
            x, y = random.randint(1, width - 2), random.randint(1, height - 2)
            if mapa[y][x] == " ":  # Solo coloca el elemento en espacios vacíos
                mapa[y][x] = char  # Coloca el elemento
                break  # Sale del ciclo una vez colocado el elemento

# Función para mover una entidad (jugador o NPC) en el mapa
def mover(entidad, dx, dy, mapa, npcs, ancho, alto, jugador=False):
    """Mueve una entidad y maneja colisiones con paredes, NPCs y cajas."""
    nueva_x = entidad["x"] + dx  # Calcula la nueva posición en X
    nueva_y = entidad["y"] + dy  # Calcula la nueva posición en Y

    if not (0 <= nueva_x < ancho and 0 <= nueva_y < alto):  # Verifica si la nueva posición está fuera de rango
        if jugador:
            entidad["energia"] -= 1  # Si es el jugador, se pierde energía por estar fuera de rango
        return False  # No se puede mover fuera de los límites

    if mapa[nueva_y][nueva_x] == "#":  # Si el siguiente lugar es una pared
        muro_nueva_x = nueva_x + dx  # Calcula la posición de la pared adyacente
        muro_nueva_y = nueva_y + dy  # Calcula la posición de la pared adyacente
        if (0 <= muro_nueva_x < ancho and 0 <= muro_nueva_y < alto and
                mapa[muro_nueva_y][muro_nueva_x] == " "):  # Si el espacio adyacente es vacío
            mapa[muro_nueva_y][muro_nueva_x] = "#"  # Empuja la pared al espacio vacío
            mapa[nueva_y][nueva_x] = " "  # Marca la posición actual como espacio vacío
        else:
            if jugador:
                entidad["energia"] -= 1  # Pérdida de energía al chocar con la pared
            return False  # No se puede mover si hay una pared

    if mapa[nueva_y][nueva_x] == "O":  # Si la entidad toca una caja
        mapa[nueva_y][nueva_x] = " "  # Destruye la caja al colisionar con ella
        if jugador:
            entidad["energia"] -= 1  # Pérdida de energía por destruir la caja
        return False  # No permite el movimiento si toca una caja

    if mapa[nueva_y][nueva_x] == "F":  # Si toca comida (NPC muerto)
        if jugador:
            entidad["energia"] += 50  # Aumenta la energía del jugador al comer comida
        mapa[nueva_y][nueva_x] = " "  # La comida desaparece después de ser comida

    # Revisa las colisiones con los NPCs
    for npc in npcs:
        if npc["x"] == nueva_x and npc["y"] == nueva_y:
            entidad["energia"] -= 10  # Pérdida de energía por colisión con NPC
            npc["energia"] -= 10  # El NPC también pierde energía
            if npc["energia"] <= 0:  # Si el NPC muere
                mapa[npc["y"]][npc["x"]] = "F"  # El NPC se convierte en comida
                npcs.remove(npc)  # Elimina al NPC de la lista
            return False  # No se permite movimiento si hay colisión con NPC

    entidad["x"], entidad["y"] = nueva_x, nueva_y  # Realiza el movimiento
    if jugador:
        entidad["energia"] -= 1  # Cada paso consume energía
    return True  # El movimiento es exitoso

# Función para lanzar una caja en una dirección
def lanzar_caja(jugador, dx, dy, mapa, ancho, alto):
    """Lanza una caja en la dirección especificada."""
    x, y = jugador["x"] + dx, jugador["y"] + dy
    while 0 <= x < ancho and 0 <= y < alto:
        if mapa[y][x] == " ":
            mapa[y][x] = "O"  # Coloca una caja en el nuevo espacio vacío
            return  # Termina la función después de lanzar la caja
        elif mapa[y][x] in {"#", "O"}:  # Si encuentra una pared o otra caja
            return  # No se puede lanzar la caja

        x += dx  # Avanza en la dirección especificada
        y += dy  # Avanza en la dirección especificada

# Función para mover aleatoriamente los NPCs
def mover_npcs(npcs, mapa, ancho, alto):
    """Los NPCs se mueven aleatoriamente."""
    for npc in npcs:
        dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])  # Elige una dirección aleatoria
        mover(npc, dx, dy, mapa, npcs, ancho, alto)  # Mueve al NPC en esa dirección

# Función para cambiar el color de los NPCs según su energía
def cambiar_color_npcs(npcs):
    """Cambiar color de los NPCs según su energía."""
    for npc in npcs:
        if npc["energia"] > 75:
            npc["color"] = 3  # Blanco
        elif npc["energia"] > 40:
            npc["color"] = 2  # Amarillo
        else:
            npc["color"] = 1  # Rojo

def esta_en_limites(x, y, ancho, alto):
    return 0 <= x < ancho and 0 <= y < alto


# Función para mostrar la portada con instrucciones
def mostrar_portada_y_nombre(stdscr):
    """Muestra la portada del juego y permite ingresar el nombre del jugador."""
    curses.curs_set(0)  # Ocultar el cursor
    stdscr.clear()

    # ASCII Art de portada
    title = """
RRRR    OOO   GGG   U   U  EEEEE  L      I   K   K  EEEEE
R   R  O   O G      U   U  E      L      I   K  K   E
RRRR   O   O G  GG  U   U  EEEE   L      I   KK     EEEE
R  R   O   O G   G  U   U  E      L      I   K  K   E
R   R   OOO   GGG    UUU   EEEEE  LLLLL  I   K   K  EEEEE
M   M          I           A            M   M          I 
MM MM          I          A A           MM MM          I 
M M M          I         A   A          M M M          I 
M   M          I        A     A         M   M          I 
M   M          I       AAAAAAAAA        M   M          I 
=========================================================                               
RRRR    OOO   GGG   U   U  EEEEE  L      I   K   K  EEEEE
R   R  O   O G      U   U  E      L      I   K  K   E
RRRR   O   O G  GG  U   U  EEEE   L      I   KK     EEEE
R  R   O   O G   G  U   U  E      L      I   K  K   E
R   R   OOO   GGG    UUU   EEEEE  LLLLL  I   K   K  EEEEE
    """
    instrucciones = """
    Bienvenido a Hot Rougelike!
    - Usa las flechas para mover al jugador (@).
    - Mata a todos los NPCs (☻) para ganar.
    - Lanza cajas con 'L'.
    - Llega a la meta en la esquina inferior derecha para ganar.
    - Presiona 'R' para reiniciar el juego.
    - Cuida tu energia, regenerate comiendo 'F'!
    """

    stdscr.addstr(2, 5, title, curses.A_BOLD)
    stdscr.addstr(25, 5, instrucciones)
    stdscr.addstr(20, 5, "Por favor, introduce tu nombre: ", curses.A_BOLD)
    stdscr.refresh()

    curses.echo()  # Activar la entrada visible
    nombre = stdscr.getstr(21, 5, 20).decode("utf-8")  # Leer el nombre del jugador
    curses.noecho()  # Desactivar la entrada visible
    stdscr.clear()
    return nombre



# Función principal que ejecuta el juego
def init_screen(stdscr, nombre_jugador):
    """Función para iniciar la pantalla del juego."""
    curses.curs_set(0)  # Ocultar el cursor
    stdscr.nodelay(0)  # Desactivar la espera de teclas
    stdscr.timeout(-1)  # Desactivar el timeout
    curses.start_color()  # Iniciar el uso de colores
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)  # Rojo
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Amarillo
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Blanco

    # Tamaño del mapa
    height, width = curses.LINES - 1, curses.COLS - 1  
    mapa = generar_laberinto_conectado(height, width)  # Genera el laberinto
    colocar_elementos(mapa, "F", cantidad=random.randint(100, 200))  # Coloca NPCs transformados en comida
    colocar_elementos(mapa, "O", cantidad=random.randint(100, 1000))  # Coloca cajas

    # Inicializa al jugador con una posición y energía
    personaje = {"x": 4, "y": 4, "char": "@", "energia": 50} #50 
    
    # Inicializa los NPCs con posiciones aleatorias, energía aleatoria y color blanco por defecto
    npcs = [{"x": random.randint(1, width - 2), "y": random.randint(1, height - 2), "char": "☻", "energia": random.randint(50, 100), "color": 3} for _ in range(250)]  # Reducción de NPCs 250
    reloj = 0  # Inicializa el reloj de turnos en cero

    stdscr.clear()
    stdscr.addstr(0, 0, f"Jugador: {nombre_jugador} | Energía: {personaje['energia']} | Turnos: {reloj} ")
    stdscr.refresh()
    
    # Bucle principal para la ejecución del juego
    while True:
        stdscr.clear()  # Limpia la pantalla

        # Actualizamos los NPCs y su color basado en la energía
        cambiar_color_npcs(npcs)

        # Imprime el mapa
        for y in range(height):
            for x in range(width):
                stdscr.addch(y, x, mapa[y][x])  # Dibuja cada celda

        # Imprime los NPCs con el color correspondiente
        for npc in npcs:
            stdscr.addch(npc["y"], npc["x"], npc["char"], curses.color_pair(npc["color"]))

        # Dibuja al jugador
        stdscr.addch(personaje["y"], personaje["x"], personaje["char"])
        
        # Muestra la energía del jugador y el tiempo
        stdscr.addstr(0, 0, f"Jugador: {nombre_jugador} | Energía: {personaje['energia']} | Turno: {reloj} pulsos")
        stdscr.refresh()  # Refresca la pantalla

        key = stdscr.getch()  # Lee la tecla presionada

        if key == ord('q'):  # Si se presiona 'q', sale del juego
            break
        elif key == ord('.'):  # Si se presiona '.', avanza el reloj
            reloj += 1
        elif key == curses.KEY_UP:  # Si se presiona la tecla arriba
            mover(personaje, 0, -1, mapa, npcs, width, height, jugador=True)
            reloj += 1
        elif key == curses.KEY_DOWN:  # Si se presiona la tecla abajo
            mover(personaje, 0, 1, mapa, npcs, width, height, jugador=True)
            reloj += 1
        elif key == curses.KEY_LEFT:  # Si se presiona la tecla izquierda
            mover(personaje, -1, 0, mapa, npcs, width, height, jugador=True)
            reloj += 1
        elif key == curses.KEY_RIGHT:  # Si se presiona la tecla derecha
            mover(personaje, 1, 0, mapa, npcs, width, height, jugador=True)
            reloj += 1
        elif key == ord('L'):  # Si se presiona 'L', lanza una caja - cambiar caja por cosa
            lanzar_caja(personaje, 0, 0, mapa, width, height)
            reloj += 1
        elif key == ord('R'):  # Reinicia el juego -agregar r minus para reiniciar el mapa
            return init_screen(stdscr, nombre_jugador)

        # Movimiento de los NPCs
        mover_npcs(npcs, mapa, width, height)
        
        if personaje['energia'] <= 0:
            stdscr.addstr(1,1, "PERDISTE! Energía agotada.")
            stdscr.refresh()
            stdscr.getch()  # Espera a que el jugador presione una tecla para continuar
            return init_screen(stdscr, nombre_jugador)

        # Verifica si todos los NPCs están muertos y si se ha llegado a la meta
        if not npcs and personaje["x"] == width - 1:
            stdscr.addstr(1,1, "You Win! Final Energy: " + str(personaje["energia"]))
            stdscr.refresh()
            stdscr.getch()  # Espera a que el jugador presione una tecla para continuar
            return init_screen(stdscr, nombre_jugador)
        


def main(stdscr):
    # Mostrar la portada y capturar el nombre
    nombre_jugador = mostrar_portada_y_nombre(stdscr)
    # Iniciar el juego
    init_screen(stdscr, nombre_jugador)

# Función para iniciar el juego
if __name__ == "__main__":
    curses.wrapper(main)  # Llama a la función que maneja la interfaz y el juego


