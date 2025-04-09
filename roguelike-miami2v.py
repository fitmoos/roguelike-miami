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
    hardness= random.randint(0, 20)
    darkness= random.randint(-10, 10) # genera montes el mayor rango
    lightness= random.randint(0, 20)        
    # Algoritmo para abrir caminos en el laberinto
    while stack:
        x, y = stack.pop()  # Tomar la última posición de la pila
        direcciones = [(darkness, -lightness), (-lightness, hardness), (-lightness, darkness), (hardness, darkness)]  # Direcciones posibles para avanzar 0, -1), (0, 1), (-1, 0), (1, 0)
        #random.shuffle(direcciones)  # Aleatoriza las direcciones para que el laberinto sea impredecible
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
    
    for _ in range(height * width // 100):  # Número de lagunas
        x, y = random.randint(1, width - 2), random.randint(1, height - 2)
        if mapa[y][x] == " ":
            mapa[y][x] = "█"
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

# Función para mover una entidad (personaje o NPC) en el mapa
def mover(entidad, dx, dy, mapa, npcs, ancho, alto, personaje=False):
    """Mueve una entidad y maneja colisiones con paredes, NPCs y cajas."""
    nueva_x = entidad["x"] + dx  # Calcula la nueva posición en X
    nueva_y = entidad["y"] + dy  # Calcula la nueva posición en Y

    if not (0 <= nueva_x < ancho and 0 <= nueva_y < alto):  # Verifica si la nueva posición está fuera de rango
        if personaje:
            entidad["energia"] -= 1  # Si es el personaje, se pierde energía por estar fuera de rango
        return False  # No se puede mover fuera de los límites

    if mapa[nueva_y][nueva_x] == "#":  # Si el siguiente lugar es una pared
        muro_nueva_x = nueva_x + dx  # Calcula la posición de la pared adyacente
        muro_nueva_y = nueva_y + dy  # Calcula la posición de la pared adyacente
        if (0 <= muro_nueva_x < ancho and 0 <= muro_nueva_y < alto and
                mapa[muro_nueva_y][muro_nueva_x] == " "):  # Si el espacio adyacente es vacío
            mapa[muro_nueva_y][muro_nueva_x] = "#"  # Empuja la pared al espacio vacío
            mapa[nueva_y][nueva_x] = " "  # Marca la posición actual como espacio vacío
            entidad["energia"] -= 1  # Pérdida de energía al chocar con la pared
        else:
            if personaje:
                entidad["energia"] -= 1  # Pérdida de energía al chocar con la pared
            return False  # No se puede mover si hay una pared

    if mapa[nueva_y][nueva_x] == "O":  # Si la entidad toca una caja
        mapa[nueva_y][nueva_x] = " "  # Destruye la caja al colisionar con ella
        if personaje:
            entidad["energia"] -= 1  # Pérdida de energía por destruir la caja
        return False  # No permite el movimiento si toca una caja

    if mapa[nueva_y][nueva_x] == "Y":  # Si toca comida (NPC muerto)
        if personaje:
            entidad["energia"] += 50  # Aumenta la energía del personaje al comer comida
        mapa[nueva_y][nueva_x] = " "  # La comida desaparece después de ser comida

    if mapa[nueva_y][nueva_x] in {"#", "█"}:  # Pared, caja o laguna bloquean el movimiento
        if personaje:
            entidad["energia"] -= 1  # Pierde energía si choca
        return False
    # Revisa las colisiones con los NPCs
    for npc in npcs:
        if npc["x"] == nueva_x and npc["y"] == nueva_y:
            entidad["energia"] -= 10  # Pérdida de energía por colisión con NPC
            npc["energia"] -= 10  # El NPC también pierde energía
            if npc["energia"] <= 0:  # Si el NPC muere
                mapa[npc["y"]][npc["x"]] = "Y"  # El NPC se convierte en comida
                npcs.remove(npc)  # Elimina al NPC de la lista
            return False  # No se permite movimiento si hay colisión con NPC

    entidad["x"], entidad["y"] = nueva_x, nueva_y  # Realiza el movimiento
    if personaje:
        entidad["energia"] -= 1  # Cada paso consume energía
    return True  # El movimiento es exitoso

# Función para mover aleatoriamente los NPCs
def mover_npcs(entidades, mapa, ancho, alto):
    """Las entidades (NPCs o personaje) se mueven aleatoriamente, colisionan entre ellas."""
    entidades_a_eliminar = []

    for entidad in entidades[:]:  # Usamos copia para evitar errores al eliminar
        dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        nueva_x = entidad["x"] + dx
        nueva_y = entidad["y"] + dy

        # Verifica si está dentro del mapa
        if not (0 <= nueva_x < ancho and 0 <= nueva_y < alto):
            continue

        # Verifica colisión con otra entidad
        colision = False
        for otra in entidades:
            if otra != entidad and otra["x"] == nueva_x and otra["y"] == nueva_y:
                otra["energia"] -= 10
                entidad["energia"] -= 10

                if otra["energia"] <= 0 and otra not in entidades_a_eliminar:
                    mapa[otra["y"]][otra["x"]] = "Y"
                    entidades_a_eliminar.append(otra)

                if entidad["energia"] <= 0 and entidad not in entidades_a_eliminar:
                    mapa[entidad["y"]][entidad["x"]] = "Y"
                    entidades_a_eliminar.append(entidad)

                colision = True
                break  # Salir del bucle si hay colisión

        if colision:
            continue  # No se mueve si colisionó

        mover(entidad, dx, dy, mapa, entidades, ancho, alto)

    # Elimina las entidades al final del ciclo
    for e in entidades_a_eliminar:
        if e in entidades:
            entidades.remove(e)



# Función para lanzar una caja en una dirección
def poner_caja(personaje, dx, dy, mapa, ancho, alto):
    """Lanza una caja en la dirección especificada y reduce la energía del personaje."""
    x, y = personaje["x"] + dx, personaje["y"] + dy
    while 0 <= x < ancho and 0 <= y < alto:
        if mapa[y][x] == " ":
            mapa[y][x] = "O"  # Coloca una caja en el nuevo espacio vacío
            personaje["energia"] -= 1  # Reducir la energía al lanzar
            return  
        elif mapa[y][x] in {"#", "O"}:  # Si encuentra una pared o caja
            return  
        x += dx  
        y += dy  

# Función para cambiar el color según energía
def cambiar_color(entidad):
    """
    Cambia el color de la(s) entidad(es) según su energía.
    La función acepta un diccionario (para un solo personaje o NPC)
    o una lista de diccionarios (para múltiples NPCs).
    """
    def asignar_color(e):
        if e["energia"] > 512:
            e["color"] = 5  # Azul
        elif e["energia"] > 256:
            e["color"] = 6  # cyan
        elif e["energia"] > 124:
            e["color"] = 4  # verde
        elif e["energia"] > 64:
            e["color"] = 3  # Blanco
        elif e["energia"] > 32:
            e["color"] = 2  # Amarillo
        elif e["energia"] > 16:
            e["color"] = 1  # Rojo
        else:
            e["color"] = 7  # Magenta

    if isinstance(entidad, list):
        for e in entidad:
            asignar_color(e)
    elif isinstance(entidad, dict):
        asignar_color(entidad)
    else:
        raise TypeError("Se esperaba un diccionario o una lista de diccionarios.")

def esta_en_limites(x, y, ancho, alto):
    return 0 <= x < ancho and 0 <= y < alto

def tirar_objeto(personaje, dx, dy, mapa, ancho, alto):
    """Mueve un objeto de la casilla frente al personaje a su posición."""
    x, y = personaje["x"] + dx, personaje["y"] + dy

    if not (0 <= x < ancho and 0 <= y < alto):  # Si está fuera del mapa, no hacemos nada
        return

    if mapa[y][x] == "#":  # Si hay una pared
        mapa[y][x] = " "  # Quitamos la pared de la posición actual            
        mapa[personaje["y"]][personaje["x"]] = "#"  # Colocamos la pared en la posición del personaje
        personaje["energia"] -= 10  # Restar energía
        #turn += 1

def lanzar_objeto(personaje, dx, dy, mapa, npcs, width, height):
    """Lanza una 'O' en línea recta hasta chocar con un NPC, pared, caja o comida."""
    x, y = personaje["x"], personaje["y"]  # Posición inicial

    while True:
        x += dx
        y += dy
        # turn += 1
        # Si sale del mapa, se detiene
        if not (0 <= x < width and 0 <= y < height):
            personaje["energia"] -= 2  # Restar energía
            return  

        # Si choca con un NPC, lo elimina y detiene el proyectil
        for npc in npcs:
            if npc["x"] == x and npc["y"] == y:
                npcs.remove(npc) # Elimina el NPC
                mapa[y][x] = "O"  # Le pone un obstaculo
                personaje["energia"] -= 2  # Restar energía
                return

        # Si choca con una pared, caja o comida, se detiene antes del impacto
        if mapa[y][x] in {"#", "O", "Y"}:
            personaje["energia"] -= 2  # Restar energía
            return  

        # Si no choca con nada, deja una "O" en la última posición libre
        mapa[y][x] = "O"
        personaje["energia"] -= 2  # Restar energía

# Función principal que ejecuta el juego
def init_screen(stdscr, nombre_personaje, energia, turn, victorias):
    def cambiar_mapa(mapa_actual, npcs, personaje, ancho, alto):
        """Cambia el mapa cuando el personaje toca un borde, manteniendo los NPCs y los objetos."""
        
        # Genera un nuevo mapa
        nuevo_mapa = generar_laberinto_conectado(alto, ancho)
        
        # Coloca comida "Y"
        colocar_elementos(nuevo_mapa, "Y", cantidad=random.randint(100, 200))
        
        # Coloca cajas "O"
        colocar_elementos(nuevo_mapa, "O", cantidad=random.randint(100, 1000))
        
        # Inicializa nuevos NPCs asegurándose de que no se ubiquen en posiciones rodeadas de "#"
        npcs = []
        for _ in range(width):
            while True:
                nueva_x = random.randint(1, ancho - 2)
                nueva_y = random.randint(1, alto - 2)
                
                # Verifica que la posición no esté rodeada de "#"
                if nuevo_mapa[nueva_y][nueva_x] == " " and not (
                    nuevo_mapa[nueva_y - 1][nueva_x] == "#" and  # Arriba
                    nuevo_mapa[nueva_y + 1][nueva_x] == "#" and  # Abajo
                    nuevo_mapa[nueva_y][nueva_x - 1] == "#" and  # Izquierda
                    nuevo_mapa[nueva_y][nueva_x + 1] == "#"):    # Derecha
                    # Coloca el NPC en la posición válida
                    npcs.append({
                        "x": nueva_x,
                        "y": nueva_y,
                        "char": "☻",
                        "energia": random.randint(50, 100),
                        "color": 3
                    })
                    nuevo_mapa[nueva_y][nueva_x] = "Y"  # Representación NPC como comida
                    break  # Sale del ciclo mientras (while) si encuentra una posición válida
        
        # Limpia los bordes del mapa de objetos
        for y in range(alto):
            nuevo_mapa[y][0] = " "  # Limpia la columna izquierda
            nuevo_mapa[y][ancho - 1] = " "  # Limpia la columna derecha
        
        for x in range(ancho):
            nuevo_mapa[0][x] = " "  # Limpia la fila superior
            nuevo_mapa[alto - 1][x] = " "  # Limpia la fila inferior
        
        # Coloca al personaje en el borde opuesto si cambia de mapa
        if personaje["x"] == 0:
            personaje["x"] = ancho - 2
        elif personaje["x"] == ancho - 1:
            personaje["x"] = 1
        elif personaje["y"] == 0:
            personaje["y"] = alto - 2
        elif personaje["y"] == alto - 1:
            personaje["y"] = 1

        return nuevo_mapa, npcs

    """Función para iniciar la pantalla del juego."""
    curses.curs_set(0)
    stdscr.nodelay(0)
    stdscr.timeout(-1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    # Inicializar personaje
    personaje = {"x": 1, "y": 1, "char": "♥", "energia": min(energia,1024), "aura": [  # Offsets for the four directions
        (0, -1),  # UP
        (0, 1),   # DOWN
        (-1, 0),  # LEFT
        (1, 0),   # RIGHT
    ]}
    turn = turn
    victorias = victorias

    # Posición y mapas generados
    mapas_generados = {}
    posicion_actual = (0, 0)

    # Definir dimensiones del mapa
    height, width = 45, 180  # Tamaño fijo 45x180 para pc, 45x45 para phone

    # Generar mapa inicial y NPCs
    mapa, npcs = cambiar_mapa(None, [], personaje, width, height)
    mapas_generados[posicion_actual] = (mapa, npcs)

    # Mostrar información inicial
    stdscr.clear()
    stdscr.addstr(0, 0, f"personaje: {nombre_personaje} | Energía: {personaje['energia']} | Turnos: {turn} | Victorias: {victorias} | Mapa: {posicion_actual}")
    stdscr.refresh()
    
    # Bucle principal para la ejecución del juego
    while True:
        stdscr.clear()  # Limpia la pantalla
            
        # Imprime el mapa
        for y in range(height):
            for x in range(width):
                if mapa[y][x] == "Y":
                    stdscr.addch(y, x, "Y", curses.color_pair(4))  # Verde
                elif mapa[y][x] == "O":
                    stdscr.addch(y, x, "O", curses.color_pair(2))  # Amarillo
                elif mapa[y][x] == "#":
                    stdscr.addch(y, x, "#", curses.color_pair(5))  # Azul
                else:
                    stdscr.addch(y, x, mapa[y][x])  # 

        # Actualizamos los NPCs y su color basado en la energía
        cambiar_color(npcs)
        # Imprime los NPCs con el color correspondiente
        for npc in npcs:
            stdscr.addch(npc["y"], npc["x"], npc["char"], curses.color_pair(npc["color"]))

        # Dibuja al personaje
        cambiar_color(personaje)
        stdscr.addch(personaje["y"], personaje["x"], personaje["char"], curses.color_pair(personaje["color"]) )

        # Muestra la energía del personaje y el tiempo
        stdscr.addstr(0, 0, f"personaje: {nombre_personaje} | Energía: {personaje['energia']} | Turno: {turn} | Victorias: {victorias} | Mapa: {posicion_actual}")

        stdscr.refresh()  # Refresca la pantalla

        key = stdscr.getch()  # Lee la tecla presionada

        if key == ord('q'):  # Si se presiona 'q', sale del juego
            break
        elif key == ord('.'):  # Si se presiona '.', avanza el turn
            turn += 1
        elif key == curses.KEY_UP:  # Si se presiona la tecla arriba
            mover(personaje, 0, -1, mapa, npcs, width, height, personaje=True)
            turn += 1
        elif key == curses.KEY_DOWN:  # Si se presiona la tecla abajo
            mover(personaje, 0, 1, mapa, npcs, width, height, personaje=True)
            turn += 1
        elif key == curses.KEY_LEFT:  # Si se presiona la tecla izquierda
            mover(personaje, -1, 0, mapa, npcs, width, height, personaje=True)
            turn += 1
        elif key == curses.KEY_RIGHT:  # Si se presiona la tecla derecha
            mover(personaje, 1, 0, mapa, npcs, width, height, personaje=True)
            turn += 1
        elif key == ord('z'):  # Si se presiona 'z', lanza una caja - cambiar caja por cosa
            poner_caja(personaje, 0, 0, mapa, width, height)
            turn += 1
        elif key == ord('r'):  # Reinicia el juego -agregar r minus para reiniciar el mapa
            return init_screen(stdscr, nombre_personaje, energia=512, turn=0, victorias=0)  # Pasa los valores de energía, turn y victorias
        # Imprime el mapa
        elif key == ord('x'):  # Si se presiona 'X', tira un objeto en la dirección elegida
            subkey = stdscr.getch()  # Esperamos otra tecla
            if subkey == curses.KEY_UP:  # X + Arriba
                tirar_objeto(personaje, 0, -1, mapa, width, height)
                turn += 1 
            elif subkey == curses.KEY_DOWN:  # X + Abajo
                tirar_objeto(personaje, 0, 1, mapa, width, height)
                turn += 1 
            elif subkey == curses.KEY_LEFT:  # X + Izquierda
                tirar_objeto(personaje, -1, 0, mapa, width, height)
                turn += 1 
            elif subkey == curses.KEY_RIGHT:  # X + Derecha
                tirar_objeto(personaje, 1, 0, mapa, width, height)
                turn += 1    
        elif key == ord('c'):  # Si se presiona 'c', lanza un objeto en la dirección elegida
            subkey = stdscr.getch()  # Esperamos otra tecla
            if subkey == curses.KEY_UP:  # c + Arriba
                lanzar_objeto(personaje, 0, -1, mapa, npcs, width, height)
                turn += 1 
            elif subkey == curses.KEY_DOWN:  # c + Abajo
                lanzar_objeto(personaje, 0, 1, mapa, npcs,  width, height)
                turn += 1 
            elif subkey == curses.KEY_LEFT:  # c + Izquierda
                lanzar_objeto(personaje, -1, 0, mapa, npcs,  width, height)
                turn += 1 
            elif subkey == curses.KEY_RIGHT:  # c + Derecha
                lanzar_objeto(personaje, 1, 0, mapa, npcs,  width, height)
                turn += 1  	
                    # Recorre las posiciones del aura
        elif key == ord('a'):  # Si se presiona "a", muestra el aura
            stdscr.addch(personaje["y"], personaje["x"], personaje["char"], curses.color_pair(personaje["color"]) | curses.A_REVERSE)
            for dx, dy in personaje["aura"]:
                ax = personaje["x"] + dx  # Calcula la posición x de la aura
                ay = personaje["y"] + dy  # Calcula la posición y de la aura
                if 0 <= ax < width and 0 <= ay < height:  # Asegura que las coordenadas están dentro de los límites
                    stdscr.addch(ay, ax, " ", curses.A_REVERSE)  # Dibuja el aura con color invertido
            stdscr.refresh()  # Refresca la pantalla después de dibujar el aura
            curses.napms(100)  # Pausa de 500 ms para dar tiempo a ver el aura		
        # Movimiento de los NPCs
        mover_npcs(npcs, mapa, width, height)
        
        if personaje['energia'] <= 0:
            stdscr.addstr(1,1, "PERDISTE! Energía agotada.")
            stdscr.refresh()
            stdscr.getch()  # Espera a que el personaje presione una tecla para continuar
            return init_screen(stdscr, nombre_personaje, energia=50, turn=0, victorias=0)

        victorias_por_mapa = {}

        # Verifica si todos los NPCs están muertos y si aún no se ganó en este mapa
        if not npcs and not victorias_por_mapa.get(posicion_actual, False):
            victorias += 1 #(45 // width)  # División entera
            victorias_por_mapa[posicion_actual] = True  # Marca victoria en este mapa

            # Agregar NPC no visible con energía infinita energia para detener el contador de victoria
            npcs.append({
                "x": 1,
                "y": 1,
                "energia": 9999999999,
                "char": " ",       # Carácter invisible
                "color": 0         # Color por defecto (neutro)
            })

            # Mostrar el mensaje de victoria
            stdscr.addstr(1, 1, f"¡Victoria! NPCs eliminados. Total victorias: {victorias}")
            stdscr.getch()  # Espera a que el personaje presione una tecla
            
        cambio = None
        if personaje["x"] == 0:
            cambio = (-1, 0)
        elif personaje["x"] == width - 1:
            cambio = (1, 0)
        elif personaje["y"] == 0:
            cambio = (0, -1)
        elif personaje["y"] == height - 1:
            cambio = (0, 1)
            
        if cambio:
            nueva_pos = (posicion_actual[0] + cambio[0], posicion_actual[1] + cambio[1])

            if nueva_pos in mapas_generados:
                mapa, npcs = mapas_generados[nueva_pos]
            else:
                mapa, npcs = cambiar_mapa(mapa, npcs, personaje, width, height)
                mapas_generados[nueva_pos] = (mapa, npcs)

            posicion_actual = nueva_pos

            # Recolocar al personaje en la posición opuesta
            if cambio == (-1, 0):  # izquierda
                personaje["x"] = width - 2
            elif cambio == (1, 0):  # derecha
                personaje["x"] = 1
            elif cambio == (0, -1):  # arriba
                personaje["y"] = height - 2
            elif cambio == (0, 1):  # abajo
                personaje["y"] = 1

            turn += 1
            stdscr.clear()
            stdscr.addstr(0, 0, f"personaje: {nombre_personaje} | Energía: {personaje['energia']} | Turnos: {turn} | Posición mapa: {posicion_actual}")
            stdscr.refresh()

def main(stdscr):
    # Mostrar la portada y capturar el nombre
    nombre_personaje = mostrar_portada_y_nombre(stdscr)
    # Iniciar el juego
    init_screen(stdscr, nombre_personaje, energia=50, turn=0, victorias=0)  

# Función para mostrar la portada con instrucciones
def mostrar_portada_y_nombre(stdscr):
    """Muestra la portada del juego y permite ingresar el nombre del personaje."""
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
-ARCADE-ARCADE-ARCADE-ARCADE-ARCADE-ARCADE-ARCADE-ARCADE-
    """
    instrucciones = """
    Survive as long as possible while exploring procedurally generated mazes. Avoid enemies, collect food to restore energy, and use boxes strategically.
    The maze changes every time you reach the edge of the screen.
    Energy is everything.

Keys
Low energy cost
↑ ↓ ← →	Move your character (♥)
z	Throw a box in front of you (O)

high energy cost:
x + Arrow	Swap places with a wall in that direction
c + Arrow	Launch a projectile (O) toward that direction

.	Wait (skip a turn)
r	Restart the game
q	Quit the game
a   Show your position
    """

    stdscr.addstr(2, 5, title, curses.A_BOLD)
    stdscr.addstr(25, 5, instrucciones)
    stdscr.addstr(20, 5, "Por favor, introduce tu nombre: ", curses.A_BOLD)
    stdscr.refresh()

    curses.echo()  # Activar la entrada visible
    nombre = stdscr.getstr(21, 5, 20).decode("utf-8")  # Leer el nombre del personaje
    curses.noecho()  # Desactivar la entrada visible
    stdscr.clear()
    return nombre
random.seed()

# Función para iniciar el juego
if __name__ == "__main__":
    curses.wrapper(main)  # Llama a la función que maneja la interfaz y el juego

#Paso a paso para agregar funciones al codigo: Una vez limpiado un Mapa  de Npc, los otros no tienen, solo se está cambiando los mapas, y cada  mapa tiene sus propios npc. Modifica la función cambiar_mapa para que  todos los mapas tengas sus npc independientes. tirar_objeto no funciona,  sigue moviendo casillas # a espacios rodeados de # donde está el  personaje o casilla de destino, y sigue poniendo # donde ya hay #, incluso  si ponemos en else: antes de "# Si la casilla actual". 
