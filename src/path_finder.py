import heapq
from collections import deque


class PathFinder:
    # Types de cases non traversables (adapter si besoin)
    BLOQUANTS = {"batiment", "eau"}
    # Types de cases ralenties (coût x2)
    RALENTIS = {"arbre", "aureus", "roche", "marais"}
    DIRS = (
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1),
    )

    def __init__(self, partie):
        self.partie = partie
        self.taillecase = partie.taillecase
        self.taillecarte = partie.taillecarte

    def pixel_to_case(self, px, py):
        cx = max(0, min(int(px / self.taillecase), self.taillecarte - 1))
        cy = max(0, min(int(py / self.taillecase), self.taillecarte - 1))
        return cx, cy

    def case_to_pixel(self, case):
        cx, cy = case
        return (cx * self.taillecase) + (self.taillecase // 2), (cy * self.taillecase) + (self.taillecase // 2)

    def est_traversable(self, cx, cy):
        if cx < 0 or cy < 0 or cx >= self.taillecarte or cy >= self.taillecarte:
            return False
        case = self.partie.cartecase[cy][cx]
        if getattr(case, "montype", None) in self.BLOQUANTS:
            return False
        # brouillard ignoré pour le pathfinding
        _ = self.partie.fog.map[cy][cx]
        return True

    def voisins(self, case):
        cx, cy = case
        for dx, dy in self.DIRS:
            nx, ny = cx + dx, cy + dy
            # éviter les diagonales à travers un coin bloqué
            if dx and dy:
                if not (self.est_traversable(cx + dx, cy) and self.est_traversable(cx, cy + dy)):
                    continue
            if self.est_traversable(nx, ny):
                yield nx, ny

    def cout(self, a, b):
        ax, ay = a
        bx, by = b
        # coût de base (diagonale ou ortho)
        base = 1.4 if ax != bx and ay != by else 1
        # si la case d'arrivée est ralentie, on double le coût
        bx_clamped = min(max(bx, 0), self.taillecarte - 1)
        by_clamped = min(max(by, 0), self.taillecarte - 1)
        case = self.partie.cartecase[by_clamped][bx_clamped]
        if getattr(case, "montype", None) in self.RALENTIS:
            base *= 2
        return base

    def heuristique(self, a, b):
        ax, ay = a
        bx, by = b
        dx = abs(ax - bx)
        dy = abs(ay - by)
        diag = min(dx, dy)
        ortho = max(dx, dy) - diag
        return (1.4 * diag) + ortho

    def reconstruire(self, parents, courant):
        chemin = [courant]
        while courant in parents:
            courant = parents[courant]
            chemin.append(courant)
        chemin.reverse()
        return [self.case_to_pixel(c) for c in chemin]

    def plus_proche_accessible(self, cible_case):
        """BFS autour de la cible pour trouver la première case traversable."""
        cx, cy = cible_case
        if self.est_traversable(cx, cy):
            return cx, cy
        directions = (
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        )
        seen = {(cx, cy)}
        queue = deque([(cx, cy)])
        while queue:
            x, y = queue.popleft()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= self.taillecarte or ny >= self.taillecarte:
                    continue
                if (nx, ny) in seen:
                    continue
                if self.est_traversable(nx, ny):
                    return nx, ny
                seen.add((nx, ny))
                queue.append((nx, ny))
        return None

    def trouver_chemin(self, depart_px, arrivee_px):
        start = self.pixel_to_case(*depart_px)
        goal = self.pixel_to_case(*arrivee_px)

        if not self.est_traversable(*start):
            start_alt = self.plus_proche_accessible(start)
            if start_alt is None:
                return []
            start = start_alt

        if start == goal and self.est_traversable(*goal):
            return [self.case_to_pixel(start)]

        open_set = [(0, start)]
        gscore = {start: 0}
        parents = {}
        closed = set()
        # meilleur noeud atteint en termes d'heuristique vers la cible initiale
        best_node = start
        best_h = self.heuristique(start, goal)

        while open_set:
            _, courant = heapq.heappop(open_set)
            if courant in closed:
                continue
            closed.add(courant)

            # met à jour le meilleur candidat approché de la cible (même si cible bloquante)
            h_c = self.heuristique(courant, goal)
            if h_c < best_h:
                best_h = h_c
                best_node = courant

            if courant == goal and self.est_traversable(*goal):
                return self.reconstruire(parents, courant)

            for voisin in self.voisins(courant):
                if voisin in closed:
                    continue
                tentative_g = gscore[courant] + self.cout(courant, voisin)
                if tentative_g < gscore.get(voisin, float("inf")):
                    parents[voisin] = courant
                    gscore[voisin] = tentative_g
                    fscore = tentative_g + self.heuristique(voisin, goal)
                    heapq.heappush(open_set, (fscore, voisin))

        # cible inatteignable : retourner le chemin vers le point le plus proche approché
        if best_node in parents or best_node == start:
            return self.reconstruire(parents, best_node)
        return []
