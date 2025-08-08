

#se cargan las dependencias necesarias para el proyecto
!pip install osmnx folium

#se obtienen las librerias para su uso
#revisar "networkx" para el uso de redes en las calles
import osmnx as ox
import networkx as nx
#con esto creamos un mapa interactivo con el que podemos visualizar las rutas y el mapa
#donde estamos trabajando

import folium
#Es importante las permutaciones? aun asi revisarlas 
from itertools import permutations
#con esto logramos tener un mejor grafico a la hora de visualizar la informacion a presentar
from IPython.display import display


#comienza la "APP"
class MultiRouteOptimizer:
    #estamos descargando las redes de todo puerto vallarta
    #asi se ve
    def __init__(self, place_name="Puerto Vallarta, Jalisco, Mexico"):
        self.place_name = place_name
        self.G = ox.graph_from_place(place_name, network_type="drive")
        self.starting_point = None
        self.starting_point_name = ""
        self.routes = []

    def set_starting_point(self, name, lat, lon):
        self.starting_point = (lat, lon)
        self.starting_point_name = name

    def add_route(self, name, a_name, a_coords, b_name, b_coords):
        self.routes.append({
            'name': name,
            'point_a': {'name': a_name, 'coords': a_coords},
            'point_b': {'name': b_name, 'coords': b_coords}
        })

    def get_node(self, coord):
        return ox.distance.nearest_nodes(self.G, X=coord[1], Y=coord[0])

    def route_distance(self, start, end):
        try:
            return nx.shortest_path_length(self.G, self.get_node(start), self.get_node(end), weight="length")
        except:
            return float("inf")

    def evaluate_sequence(self, sequence):
        pos = self.starting_point
        total = 0
        details = []

        for idx in sequence:
            r = self.routes[idx]
            d1 = self.route_distance(pos, r['point_a']['coords'])
            d2 = self.route_distance(r['point_a']['coords'], r['point_b']['coords'])
            total += d1 + d2
            details.append((r['name'], d1, d2))
            pos = r['point_b']['coords']

        regreso = self.route_distance(pos, self.starting_point)
        total += regreso
        return total, details, regreso

    def find_optimal(self):
        best = float("inf")
        best_seq, best_det, best_ret = None, None, None

        for seq in permutations(range(len(self.routes))):
            t, d, r = self.evaluate_sequence(seq)
            if t < best:
                best = t
                best_seq, best_det, best_ret = seq, d, r

        return best_seq, best, best_det, best_ret

    def path_coords(self, a, b):
        try:
            path = nx.shortest_path(self.G, self.get_node(a), self.get_node(b), weight="length")
            return [[self.G.nodes[n]['y'], self.G.nodes[n]['x']] for n in path]
        except:
            return []

    def draw_map(self, seq, det, regreso):
        m = folium.Map(location=self.starting_point, zoom_start=13)
        #Colores con los que se pintan las rutas
        colors = ["red", "blue", "green", "purple", "orange"]
        pos = self.starting_point

        folium.Marker(self.starting_point, popup=f"Inicia: {self.starting_point_name}",
                      icon=folium.Icon(color="black", icon="home")).add_to(m)

        for i, idx in enumerate(seq):
            r = self.routes[idx]
            color = colors[i % len(colors)]
            folium.Marker(r['point_a']['coords'], popup=f"A: {r['point_a']['name']}",
                          icon=folium.Icon(color=color, icon="play")).add_to(m)
            folium.Marker(r['point_b']['coords'], popup=f"B: {r['point_b']['name']}",
                          icon=folium.Icon(color=color, icon="stop")).add_to(m)

            for path in [self.path_coords(pos, r['point_a']['coords']), self.path_coords(r['point_a']['coords'], r['point_b']['coords'])]:
                if path:
                    folium.PolyLine(path, color=color, weight=4).add_to(m)
            pos = r['point_b']['coords']

        path_back = self.path_coords(pos, self.starting_point)
        if path_back:
            folium.PolyLine(path_back, color="gray", weight=2, dash_array="5,5").add_to(m)

        return m

    def optimize_routes(self):
        if not self.routes or not self.starting_point:
            print("❌ Debes ingresar un punto de inicio y al menos una ruta.")
            return None
        #
        seq, total, det, regreso = self.find_optimal()
        print(f"\n✅ Distancia total: {total/1000:.2f} km")
        print(f"🕓 Estimado: {(total/1000)*3:.0f} minutos")
        print("📋 Orden:")
        for i, (name, d1, d2) in enumerate(det):
            print(f" {i+1}. {name}: hacia A {d1/1000:.2f} km + ruta {d2/1000:.2f} km")
        print(f" ↩️ Regreso: {regreso/1000:.2f} km")

        return self.draw_map(seq, det, regreso)

def get_coords(msg):
    while True:
        try:
            lat, lon = map(float, input(f"{msg} (lat, lon): ").split(","))
            return (lat, lon)
        except:
            print("❌ Formato inválido. Usa: lat, lon")

#Aquí comienza la logica 
def main():
    print("🚀 OPTIMIZADOR DE RUTAS")
    #podriamos poner un "INPUT" pero teniendo la lista correcta del nombre de las ciudades que se 
    #pueden extraer
    place = "Puerto Vallarta, Jalisco, Mexico"
    #aqui comienza la "APP"
    optimizer = MultiRouteOptimizer(place)

    #usamos nombre de la ruta y de los puntos
    name = input("Nombre del punto de inicio: ") or "Inicio"
    coords = get_coords("Coordenadas del punto de inicio")
    optimizer.set_starting_point(name, coords[0], coords[1])

    while True:
        try:
            # "n"  representa la cantidad de rutas que podemos generar
            n = int(input("¿Cuántas rutas quieres ingresar? "))
            break
        except:
            print("❌ Ingresa un número válido")

    #aqui comienza la logica de los nombres de "n-Rutas"
    for i in range(n):
        print(f"\nRuta {i+1}")
        r_name = input("Nombre de la ruta: ") or f"Ruta {i+1}"
        a_name = input("Nombre del punto A: ") or f"A{i+1}"
        a_coords = get_coords("Coordenadas punto A")
        b_name = input("Nombre del punto B: ") or f"B{i+1}"
        b_coords = get_coords("Coordenadas punto B")
        optimizer.add_route(r_name, a_name, a_coords, b_name, b_coords)


    #finalizamos llamando a la secuencia que se llama "optimizer.optimize_routes()" 
    #y luego lo guardamos en una variable "result"
    print("\nCalculando mejor secuencia...")
    result = optimizer.optimize_routes()
    return result
