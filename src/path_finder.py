import heapq


class PathFinder:
    """Simple A* pathfinder working on the map grid and current vision."""
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
        if getattr(case, "montype", None) in ("batiment", "eau"):
            return False

        # On laisse la possibilit�� de cliquer dans le brouillard;
        # si une case est simplement cach��e, on la traite comme traversable.
        _ = self.partie.fog.map[cy][cx]
        return True

    def voisins(self, case):
        cx, cy = case
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nx, ny = cx + dx, cy + dy
            if self.est_traversable(nx, ny):
                yield nx, ny

    def ligne_libre(self, p1_px, p2_px):
        """Teste la visibilit�� cellule-par-cellule (Bresenham) entre deux points pixels."""
        x0, y0 = self.pixel_to_case(*p1_px)
        x1, y1 = self.pixel_to_case(*p2_px)

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if not self.est_traversable(x0, y0):
                return False
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return True

    def lisser_chemin(self, chemin_px):
        """String-pulling: on saute les points interm��diaires si la ligne est libre."""
        if len(chemin_px) <= 2:
            return chemin_px
        lisse = [chemin_px[0]]
        ancre = chemin_px[0]
        for i in range(2, len(chemin_px)):
            candidat = chemin_px[i]
            if not self.ligne_libre(ancre, candidat):
                # le point pr��c��dent est le dernier visible
                lisse.append(chemin_px[i - 1])
                ancre = chemin_px[i - 1]
        lisse.append(chemin_px[-1])
        return lisse

    def cout(self, a, b):
        ax, ay = a
        bx, by = b
        return 1.4 if ax != bx and ay != by else 1

    def heuristique(self, a, b):
        ax, ay = a
        bx, by = b
        return abs(ax - bx) + abs(ay - by)

    def reconstruire(self, parents, courant):
        chemin = [courant]
        while courant in parents:
            courant = parents[courant]
            chemin.append(courant)
        chemin.reverse()
        return [self.case_to_pixel(c) for c in chemin]

    def trouver_chemin(self, depart_px, arrivee_px):
        start = self.pixel_to_case(*depart_px)
        goal = self.pixel_to_case(*arrivee_px)

        if not self.est_traversable(*start) or not self.est_traversable(*goal):
            return []

        if start == goal:
            return [self.case_to_pixel(start)]

        file_ouverte = [(0, start)]
        gscore = {start: 0}
        parents = {}

        while file_ouverte:
            _, courant = heapq.heappop(file_ouverte)
            if courant == goal:
                brut = self.reconstruire(parents, courant)
                return self.lisser_chemin(brut)

            for voisin in self.voisins(courant):
                tentative_g = gscore[courant] + self.cout(courant, voisin)
                if tentative_g < gscore.get(voisin, float("inf")):
                    parents[voisin] = courant
                    gscore[voisin] = tentative_g
                    fscore = tentative_g + self.heuristique(voisin, goal)
                    heapq.heappush(file_ouverte, (fscore, voisin))

        return []