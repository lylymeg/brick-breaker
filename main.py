import sys
import random
import math
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)

# ------------------------------------------------------------------------------
# CONFIGURATION GLOBAL
# ------------------------------------------------------------------------------
GAME_WIDTH = 700
GAME_HEIGHT = 800

PADDLE_WIDTH_DEFAULT = 110
PADDLE_HEIGHT = 16
PADDLE_SPEED = 10

BALL_RADIUS = 8
BALL_BASE_SPEED = 6

BRICK_ROWS = 6
BRICK_COLS = 9
BRICK_PADDING = 6
BRICK_TOP_OFFSET = 80


# ------------------------------------------------------------------------------
# CLASSES DU JEU
# ------------------------------------------------------------------------------
class Paddle:
    def __init__(self):
        self.width = PADDLE_WIDTH_DEFAULT
        self.height = PADDLE_HEIGHT
        self.x = (GAME_WIDTH - self.width) / 2
        self.y = GAME_HEIGHT - 60
        self.speed = PADDLE_SPEED

    def rect(self):
        return QRectF(self.x, self.y, self.width, self.height)

    def move_left(self):
        self.x = max(10, self.x - self.speed)

    def move_right(self):
        self.x = min(GAME_WIDTH - self.width - 10, self.x + self.speed)

    def set_x_center(self, center_x):
        self.x = max(10, min(GAME_WIDTH - self.width - 10, center_x - self.width / 2))


class Ball:
    def __init__(self, x, y):
        self.radius = BALL_RADIUS
        self.x = x
        self.y = y
        self.vx = random.choice([-3, 3])
        self.vy = -BALL_BASE_SPEED

    def rect(self):
        return QRectF(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def move(self):
        self.x += self.vx
        self.y += self.vy

    def speed(self):
        return math.hypot(self.vx, self.vy)

    def set_angle(self, angle_rad, speed=None):
        if speed is None:
            speed = self.speed()
        self.vx = speed * math.cos(angle_rad)
        self.vy = speed * math.sin(angle_rad)


class Brick:
    def __init__(self, x, y, width, height, hits_required, color, score_value):
        self.rect = QRectF(x, y, width, height)
        self.max_hits = hits_required
        self.hits_left = hits_required
        self.color = QColor(color)
        self.score_value = score_value

    def hit(self):
        self.hits_left -= 1
        return self.hits_left <= 0


class PowerUp:
    TYPES = {
        'PADDLE_EXPAND': {'color': '#00FF9D', 'label': '↔'},   # Raquette agrandie
        'SPEED_UP': {'color': '#FF3264', 'label': '⚡'},         # Vitesse balle +
        'EXTRA_LIFE': {'color': '#FF00EA', 'label': '♥'},        # Vie supplémentaire
        'SLOW_BALL': {'color': '#00E1FF', 'label': '❄'}         # Balle ralentie
    }

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.speed = 3
        self.kind = random.choice(list(self.TYPES.keys()))
        self.color = QColor(self.TYPES[self.kind]['color'])
        self.label = self.TYPES[self.kind]['label']

    def rect(self):
        return QRectF(self.x, self.y, self.width, self.height)

    def move(self):
        self.y += self.speed


# ------------------------------------------------------------------------------
# MOTEUR PRINCIPAL DU CASSE-BRIQUES
# ------------------------------------------------------------------------------
class BrickBreakerWidget(QWidget):
    def __init__(self, update_score_cb, update_lives_cb, game_over_cb, win_cb):
        super().__init__()
        self.setFixedSize(GAME_WIDTH, GAME_HEIGHT)
        self.setMouseTracking(True)

        self.update_score_cb = update_score_cb
        self.update_lives_cb = update_lives_cb
        self.game_over_cb = game_over_cb
        self.win_cb = win_cb

        self.paddle = Paddle()
        self.ball = Ball(GAME_WIDTH / 2, self.paddle.y - 20)
        self.bricks = []
        self.powerups = []

        self.score = 0
        self.lives = 3
        self.is_running = False
        self.keys_pressed = set()
        self.use_mouse = True

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop)

    def start_game(self):
        self.score = 0
        self.lives = 3
        self.is_running = True
        self.paddle = Paddle()
        self.powerups.clear()

        self.reset_ball()
        self.generate_bricks()

        self.update_score_cb(self.score)
        self.update_lives_cb(self.lives)
        self.timer.start(16)  # ~60 FPS

    def reset_ball(self):
        self.ball = Ball(self.paddle.x + self.paddle.width / 2, self.paddle.y - 15)

    def generate_bricks(self):
        self.bricks.clear()
        total_margin = 20 * 2
        available_width = GAME_WIDTH - total_margin - (BRICK_COLS - 1) * BRICK_PADDING
        brick_w = available_width / BRICK_COLS
        brick_h = 24

        # Modèles de briques selon la ligne
        row_configs = [
            {'hits': 3, 'color': '#FF3264', 'score': 30},  # Rouge (3 coups)
            {'hits': 3, 'color': '#FF3264', 'score': 30},
            {'hits': 2, 'color': '#FF9D00', 'score': 20},  # Orange (2 coups)
            {'hits': 2, 'color': '#FF9D00', 'score': 20},
            {'hits': 1, 'color': '#00E1FF', 'score': 10},  # Cyan (1 coup)
            {'hits': 1, 'color': '#00FF9D', 'score': 10},  # Vert (1 coup)
        ]

        for r in range(BRICK_ROWS):
            config = row_configs[r]
            y = BRICK_TOP_OFFSET + r * (brick_h + BRICK_PADDING)
            for c in range(BRICK_COLS):
                x = 20 + c * (brick_w + BRICK_PADDING)
                brick = Brick(x, y, brick_w, brick_h, config['hits'], config['color'], config['score'])
                self.bricks.append(brick)

    # --------------------------------------------------------------------------
    # BOUCLE DE JEU & PHYSIQUE
    # --------------------------------------------------------------------------
    def game_loop(self):
        if not self.is_running:
            return

        # Déplacement clavier
        if not self.use_mouse:
            if Qt.Key_Left in self.keys_pressed or Qt.Key_A in self.keys_pressed:
                self.paddle.move_left()
            if Qt.Key_Right in self.keys_pressed or Qt.Key_D in self.keys_pressed:
                self.paddle.move_right()

        # Déplacement de la balle
        self.ball.move()

        # 1. Collisions avec les murs
        if self.ball.x - self.ball.radius <= 0:
            self.ball.x = self.ball.radius
            self.ball.vx *= -1
        elif self.ball.x + self.ball.radius >= GAME_WIDTH:
            self.ball.x = GAME_WIDTH - self.ball.radius
            self.ball.vx *= -1

        if self.ball.y - self.ball.radius <= 0:
            self.ball.y = self.ball.radius
            self.ball.vy *= -1

        # Perte de balle
        if self.ball.y > GAME_HEIGHT:
            self.lives -= 1
            self.update_lives_cb(self.lives)
            if self.lives <= 0:
                self.is_running = False
                self.timer.stop()
                self.game_over_cb(self.score)
                return
            else:
                self.reset_ball()

        # 2. Collision Balle <-> Raquette (Physique d'angle dynamique)
        if self.ball.rect().intersects(self.paddle.rect()) and self.ball.vy > 0:
            # Calcul où la balle a frappé la raquette [-1.0 (gauche), 0.0 (centre), 1.0 (droite)]
            hit_pos = (self.ball.x - (self.paddle.x + self.paddle.width / 2)) / (self.paddle.width / 2)
            hit_pos = max(-0.9, min(0.9, hit_pos))

            # Conversion de l'impact en angle (entre 200° et 340°)
            angle_rad = math.radians(270 + hit_pos * 60)
            self.ball.set_angle(angle_rad)

        # 3. Collision Balle <-> Briques
        ball_r = self.ball.rect()
        for brick in list(self.bricks):
            if ball_r.intersects(brick.rect):
                # Déterminer la face de collision
                overlap_left = abs((self.ball.x + self.ball.radius) - brick.rect.left())
                overlap_right = abs((self.ball.x - self.ball.radius) - brick.rect.right())
                overlap_top = abs((self.ball.y + self.ball.radius) - brick.rect.top())
                overlap_bottom = abs((self.ball.y - self.ball.radius) - brick.rect.bottom())

                min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

                if min_overlap in (overlap_left, overlap_right):
                    self.ball.vx *= -1
                else:
                    self.ball.vy *= -1

                # Dégâts sur la brique
                destroyed = brick.hit()
                if destroyed:
                    self.score += brick.score_value
                    self.update_score_cb(self.score)
                    self.bricks.remove(brick)

                    # Chance d'apparition de Bonus/Malus (20%)
                    if random.random() < 0.20:
                        self.powerups.append(PowerUp(brick.rect.center().x(), brick.rect.center().y()))

                break  # Traiter une collision par frame

        # Victoire si toutes les briques sont détruites
        if not self.bricks:
            self.is_running = False
            self.timer.stop()
            self.win_cb(self.score)
            return

        # 4. Gestion des Power-ups tombants
        for p in list(self.powerups):
            p.move()
            if p.rect().intersects(self.paddle.rect()):
                self.apply_powerup(p.kind)
                self.powerups.remove(p)
            elif p.y > GAME_HEIGHT:
                self.powerups.remove(p)

        self.update()

    def apply_powerup(self, kind):
        if kind == 'PADDLE_EXPAND':
            self.paddle.width = min(200, self.paddle.width + 35)
        elif kind == 'SPEED_UP':
            spd = min(12, self.ball.speed() * 1.25)
            self.ball.set_angle(math.atan2(self.ball.vy, self.ball.vx), spd)
        elif kind == 'SLOW_BALL':
            spd = max(4, self.ball.speed() * 0.75)
            self.ball.set_angle(math.atan2(self.ball.vy, self.ball.vx), spd)
        elif kind == 'EXTRA_LIFE':
            self.lives += 1
            self.update_lives_cb(self.lives)

    # --------------------------------------------------------------------------
    # CONTRÔLES & RENDER
    # --------------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        self.use_mouse = True
        self.paddle.set_x_center(event.x())

    def keyPressEvent(self, event):
        self.use_mouse = False
        self.keys_pressed.add(event.key())

    def keyReleaseEvent(self, event):
        if event.key() in self.keys_pressed:
            self.keys_pressed.remove(event.key())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fond
        painter.fillRect(self.rect(), QColor("#0b0e14"))

        # Briques
        for brick in self.bricks:
            # Assombrir la couleur si la brique est fissurée
            c = QColor(brick.color)
            if brick.hits_left < brick.max_hits:
                c = c.darker(140)

            painter.setBrush(QBrush(c))
            painter.setPen(QPen(QColor("#FFFFFF"), 1))
            painter.drawRoundedRect(brick.rect, 4, 4)

        # Power-ups
        for p in self.powerups:
            painter.setBrush(QBrush(p.color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(p.rect())
            painter.setPen(QPen(QColor("#000000")))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(p.rect(), Qt.AlignCenter, p.label)

        # Raquette
        painter.setBrush(QBrush(QColor("#00E1FF")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawRoundedRect(self.paddle.rect(), 8, 8)

        # Balle
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.ball.rect())


# ------------------------------------------------------------------------------
# FENÊTRE PRINCIPALE
# ------------------------------------------------------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Casse-Briques Retro - PyQt5")
        self.setFixedSize(GAME_WIDTH + 40, GAME_HEIGHT + 100)
        self.setStyleSheet("""
            QWidget {
                background-color: #121824;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                font-weight: bold;
            }
            QPushButton {
                background-color: #00E1FF;
                color: #0B0E14;
                border: none;
                padding: 12px 28px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #33E7FF;
            }
        """)

        main_layout = QVBoxLayout(self)

        # Top Bar (Score / Vies)
        info_panel = QHBoxLayout()
        self.score_label = QLabel("SCORE: 0")
        self.score_label.setStyleSheet("font-size: 18px; color: #00E1FF;")

        self.lives_label = QLabel("VIES: ♥♥♥")
        self.lives_label.setStyleSheet("font-size: 18px; color: #FF3264;")

        info_panel.addWidget(self.score_label)
        info_panel.addStretch()
        info_panel.addWidget(self.lives_label)
        main_layout.addLayout(info_panel)

        # Zone de jeu
        self.game_widget = BrickBreakerWidget(
            update_score_cb=self.update_score,
            update_lives_cb=self.update_lives,
            game_over_cb=self.show_game_over,
            win_cb=self.show_win
        )
        main_layout.addWidget(self.game_widget, alignment=Qt.AlignCenter)

        # Overlay Menu / End Game
        self.overlay_frame = QFrame(self.game_widget)
        self.overlay_frame.setGeometry(0, 0, GAME_WIDTH, GAME_HEIGHT)
        self.overlay_frame.setStyleSheet("background-color: rgba(11, 14, 20, 0.88);")

        overlay_layout = QVBoxLayout(self.overlay_frame)

        self.title_label = QLabel("CASSE-BRIQUES")
        self.title_label.setStyleSheet("font-size: 42px; color: #00E1FF; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.subtitle_label = QLabel("Score Final: 0")
        self.subtitle_label.setStyleSheet("font-size: 20px; color: #FFFFFF;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.start_btn = QPushButton("🚀 JOUER")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_new_game)

        overlay_layout.addStretch()
        overlay_layout.addWidget(self.title_label)
        overlay_layout.addSpacing(10)
        overlay_layout.addWidget(self.subtitle_label)
        overlay_layout.addSpacing(30)
        overlay_layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)
        overlay_layout.addStretch()

        self.show_menu()

    def show_menu(self):
        self.title_label.setText("CASSE-BRIQUES")
        self.title_label.setStyleSheet("font-size: 42px; color: #00E1FF; font-weight: bold;")
        self.subtitle_label.setText("Déplacez la souris ou utilisez A/D (Flèches)")
        self.start_btn.setText("🚀 JOUER")
        self.overlay_frame.show()

    def start_new_game(self):
        self.overlay_frame.hide()
        self.game_widget.start_game()
        self.game_widget.setFocus()

    def update_score(self, score):
        self.score_label.setText(f"SCORE: {score}")

    def update_lives(self, lives):
        self.lives_label.setText(f"VIES: {'♥' * max(0, lives)}")

    def show_game_over(self, final_score):
        self.title_label.setText("GAME OVER")
        self.title_label.setStyleSheet("font-size: 42px; color: #FF3264; font-weight: bold;")
        self.subtitle_label.setText(f"Score Final: {final_score}")
        self.start_btn.setText("🔄 REJOUER")
        self.overlay_frame.show()

    def show_win(self, final_score):
        self.title_label.setText("VICTOIRE !")
        self.title_label.setStyleSheet("font-size: 42px; color: #00FF9D; font-weight: bold;")
        self.subtitle_label.setText(f"Score Parfait: {final_score}")
        self.start_btn.setText("🔄 REJOUER")
        self.overlay_frame.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())