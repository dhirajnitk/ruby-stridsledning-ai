import math
import heapq
from typing import List, Tuple, Dict

class AStarRouter:
    """
    Grid-based A* pathfinder for strategic aircraft routing.
    Accounts for distance, weather, and threat costs.
    """
    def __init__(self, width: int = 1000, height: int = 800, resolution: int = 20):
        self.width = width
        self.height = height
        self.res = resolution
        self.grid_w = width // resolution
        self.grid_h = height // resolution

    def get_path(self, start: Tuple[float, float], end: Tuple[float, float], 
                 weather_cells: List[Dict], threat_zones: List[Dict]) -> List[Tuple[float, float]]:
        
        start_node = (int(start[0] // self.res), int(start[1] // self.res))
        end_node = (int(end[0] // self.res), int(end[1] // self.res))
        
        # Clamp to grid
        start_node = (max(0, min(self.grid_w - 1, start_node[0])), max(0, min(self.grid_h - 1, start_node[1])))
        end_node = (max(0, min(self.grid_w - 1, end_node[0])), max(0, min(self.grid_h - 1, end_node[1])))

        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: self._heuristic(start_node, end_node)}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end_node:
                return self._reconstruct_path(came_from, current)

            for neighbor in self._get_neighbors(current):
                # Calculate movement cost
                move_cost = self.res * (1.414 if neighbor[0] != current[0] and neighbor[1] != current[1] else 1.0)
                
                # Apply penalties
                penalty = 1.0
                nx, ny = neighbor[0] * self.res, neighbor[1] * self.res
                
                for cell in weather_cells:
                    dist = math.hypot(nx - cell['x'], ny - cell['y'])
                    if dist < cell['radius']:
                        penalty *= 3.0 # Heavy weather penalty
                
                for zone in threat_zones:
                    dist = math.hypot(nx - zone['x'], ny - zone['y'])
                    if dist < zone['radius']:
                        penalty *= 10.0 # Extreme threat penalty
                
                tentative_g = g_score[current] + move_cost * penalty

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, end_node)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return [] # No path found

    def _heuristic(self, a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1]) * self.res

    def _get_neighbors(self, node):
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                nx, ny = node[0] + dx, node[1] + dy
                if 0 <= nx < self.grid_w and 0 <= ny < self.grid_h:
                    neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(self, came_from, current):
        path = [(float(current[0] * self.res), float(current[1] * self.res))]
        while current in came_from:
            current = came_from[current]
            path.append((float(current[0] * self.res), float(current[1] * self.res)))
        path.reverse()
        return path
