from __future__ import annotations

import cv2
import sys
import time
import random
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Tuple, Optional

import mediapipe as mp

WINDOW_TITLE = "MiniJuego: Slice the Squares (k: volver, r: reiniciar, q/ESC: salir)"

# Tamaño deseado de la ventana de juego (se reescala el frame de cámara a esto)
WIN_W, WIN_H = 960, 540
FULLSCREEN = True          # ← pantalla completa ON/OFF

# Comportamiento de cámara
MIRROR = True             # espejo horizontal para control más natural

# Spawning (mantengo frecuencia; solo hacemos más lentos los cuadros)
SPAWN_EVERY = 0.8                 # segundos entre spawns
SPEED_MIN, SPEED_MAX = 80, 140    # ⬅️ velocidades más LENTAS (antes 180–320 px/s)
SIZE_MIN, SIZE_MAX = 50, 100      # tamaño del cuadro

# Puntuación (sin game over)
CUT_SCORE = 10

# Detección de corte (más reactivo)
TRAIL_MAXLEN = 18         # menos puntos en la estela → más “viva”
MIN_MOVE_PIX = 6          # ⬇️ desplazamiento mínimo entre frames
SPEED_GATE = 90           # ⬇️ velocidad mínima del segmento (px/s)
CUT_COOLDOWN = 0.06       # ⬇️ cooldown por cuadro (más cortes posibles)

# Visual
SQUARE_COLOR = (60, 170, 255)     # BGR
SQUARE_CUT_COLOR = (60, 255, 160)
SQUARE_ALPHA = 0.35              
TRAIL_COLOR = (40, 220, 255)
HUD_COLOR = (255, 255, 255)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

Point = Tuple[int, int]

def _ccw(a: Point, b: Point, c: Point) -> int:
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

def _on_segment(a: Point, b: Point, p: Point) -> bool:
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and \
           min(a[1], b[1]) <= p[1] <= max(a[1], b[1])

def _segments_intersect(p1: Point, p2: Point, q1: Point, q2: Point) -> bool:
    d1 = _ccw(p1, p2, q1)
    d2 = _ccw(p1, p2, q2)
    d3 = _ccw(q1, q2, p1)
    d4 = _ccw(q1, q2, p2)
    if (d1 == 0 and _on_segment(p1, p2, q1)) or \
       (d2 == 0 and _on_segment(p1, p2, q2)) or \
       (d3 == 0 and _on_segment(q1, q2, p1)) or \
       (d4 == 0 and _on_segment(q1, q2, p2)):
        return True
    return (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0)

def segment_intersects_rect(p1: Point, p2: Point, rect: Tuple[int,int,int,int]) -> bool:
    x, y, w, h = rect
    if x <= p1[0] <= x+w and y <= p1[1] <= y+h: return True
    if x <= p2[0] <= x+w and y <= p2[1] <= y+h: return True
    corners = [(x,y), (x+w,y), (x+w,y+h), (x,y+h)]
    edges = [(corners[i], corners[(i+1)%4]) for i in range(4)]
    for a,b in edges:
        if _segments_intersect(p1, p2, a, b):
            return True
    return False

def draw_filled_rect_alpha(frame: np.ndarray, rect: Tuple[int,int,int,int],
                           color_bgr: Tuple[int,int,int], alpha: float):
    x, y, w, h = rect
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(frame.shape[1], x + w), min(frame.shape[0], y + h)
    if x0 >= x1 or y0 >= y1:
        return
    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x1, y1), color_bgr, thickness=-1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, dst=frame)

@dataclass
class Square:
    x: float
    y: float
    size: int
    vy: float
    alive: bool = True
    last_cut_time: float = 0.0

    def rect(self) -> Tuple[int,int,int,int]:
        return int(self.x), int(self.y), self.size, self.size

    def update(self, dt: float):
        self.y += self.vy * dt

class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.squares: List[Square] = []
        self.score = 0
        self.last_spawn = 0.0
        self.trail: Deque[Tuple[int,int,float]] = deque(maxlen=TRAIL_MAXLEN)

    def spawn_square(self, now: float):
        size = random.randint(SIZE_MIN, SIZE_MAX)
        x = random.randint(0, max(0, WIN_W - size))
        y = -size - 8
        vy = random.uniform(SPEED_MIN, SPEED_MAX)
        self.squares.append(Square(x=x, y=y, size=size, vy=vy))
        self.last_spawn = now

    def update(self, dt: float, now: float):
        if (now - self.last_spawn) >= SPAWN_EVERY:
            self.spawn_square(now)
        for sq in self.squares:
            sq.update(dt)
        self.squares = [s for s in self.squares if s.y <= WIN_H + 2 and s.alive or s.alive]

    def register_trail_point(self, x: int, y: int, t: float):
        self.trail.append((x, y, t))

    def try_slice_with_segment(self, p1: Point, p2: Point, seg_speed: float, now: float):
        if seg_speed < SPEED_GATE:
            return
        for sq in self.squares:
            if not sq.alive:
                continue
            if (now - sq.last_cut_time) < CUT_COOLDOWN:
                continue
            if segment_intersects_rect(p1, p2, sq.rect()):
                sq.alive = False
                sq.last_cut_time = now
                self.score += CUT_SCORE

def run(camera_index: int = 0) -> None:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara para el mini-juego")
        return

    # ---- Pantalla completa (en lugar de WINDOW_NORMAL/resizeWindow) ----
    if FULLSCREEN:
        cv2.namedWindow(WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    else:
        cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_TITLE, WIN_W, WIN_H)

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.8,  # ⬆️ mejor seguimiento → respuesta más estable/rápida
    )

    game = Game()
    prev_tip: Optional[Tuple[int,int,float]] = None  # (x,y,t)

    print("[ MiniJuego ] Corta los cuadros moviendo tu mano sobre ellos")
    print("Controles: k (volver), r (reiniciar), q/ESC: salir")

    last_time = time.time()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if MIRROR:
                frame = cv2.flip(frame, 1)

            # Reescalamos a tamaño lógico del juego (la ventana ya es fullscreen)
            frame = cv2.resize(frame, (WIN_W, WIN_H))

            now = time.time()
            dt = max(1e-3, now - last_time)
            last_time = now

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)
            tip_xy: Optional[Tuple[int,int]] = None

            if res.multi_hand_landmarks:
                lms = res.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame, lms, mp_hands.HAND_CONNECTIONS)
                tip = lms.landmark[8]
                x_px = int(tip.x * WIN_W)
                y_px = int(tip.y * WIN_H)
                tip_xy = (x_px, y_px)

            game.update(dt, now)

            if tip_xy:
                game.register_trail_point(tip_xy[0], tip_xy[1], now)
                if prev_tip:
                    p1 = (prev_tip[0], prev_tip[1])
                    p2 = (tip_xy[0], tip_xy[1])
                    seg_dt = max(1e-3, now - prev_tip[2])
                    dx = p2[0] - p1[0]
                    dy = p2[1] - p1[1]
                    seg_speed = (dx*dx + dy*dy) ** 0.5 / seg_dt
                    if (abs(dx) + abs(dy)) >= MIN_MOVE_PIX:
                        game.try_slice_with_segment(p1, p2, seg_speed, now)
                prev_tip = (tip_xy[0], tip_xy[1], now)
            else:
                prev_tip = None

            for sq in game.squares:
                x, y, w, h = sq.rect()
                color = SQUARE_COLOR if sq.alive else SQUARE_CUT_COLOR
                draw_filled_rect_alpha(frame, (x, y, w, h), color, SQUARE_ALPHA if sq.alive else 0.15)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            pts = [(x, y) for (x, y, t) in game.trail]
            for i in range(1, len(pts)):
                cv2.line(frame, pts[i-1], pts[i], TRAIL_COLOR, 2)
            if tip_xy:
                cv2.circle(frame, tip_xy, 6, (0, 255, 255), -1)

            cv2.putText(frame, f"Puntaje: {game.score}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, HUD_COLOR, 2)
            cv2.putText(frame, "k: volver | r: reiniciar | q/ESC: salir", (10, 58),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, HUD_COLOR, 1)

            cv2.imshow(WINDOW_TITLE, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('k'):
                break
            if key in (27, ord('q')):
                cap.release()
                cv2.destroyAllWindows()
                sys.exit(0)
            if key == ord('r'):
                game.reset()
                prev_tip = None

    finally:
        cap.release()
        cv2.destroyAllWindows()
