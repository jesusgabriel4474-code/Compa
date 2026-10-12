
import pygame
import ast
import math
import random
import time

# ============================================================
# NEBULA CALCULATOR — interface animada em um único script
# Pygame + Python | Mouse, teclado e toque
# ============================================================

pygame.init()

W, H = 430, 760
screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
pygame.display.set_caption("Nebula Calculator")
clock = pygame.time.Clock()

# Paleta visual
BG = (8, 12, 24)
PANEL = (15, 23, 41)
BUTTON = (21, 31, 51)
BUTTON_HOVER = (34, 51, 78)
BLUE = (45, 145, 255)
CYAN = (92, 205, 255)
WHITE = (242, 247, 255)
MUTED = (120, 143, 175)
RED = (255, 104, 125)

font_cache = {}

def font(size, bold=False):
    key = (int(size), bold)
    if key not in font_cache:
        font_cache[key] = pygame.font.SysFont(
            "dejavusans", int(size), bold=bold
        )
    return font_cache[key]

def clamp(v, a, b):
    return max(a, min(b, v))

def lerp(a, b, t):
    return a + (b - a) * t

def draw_text(text, size, color, x, y, align="center", bold=False):
    image = font(size, bold).render(str(text), True, color)
    rect = image.get_rect()
    setattr(rect, align, (int(x), int(y)))
    screen.blit(image, rect)

def rounded_rect(surface, color, rect, radius=18, width=0):
    pygame.draw.rect(
        surface, color, rect, width=width,
        border_radius=min(radius, rect.width // 2, rect.height // 2)
    )

def safe_calculate(expression):
    """Calcula somente operações matemáticas permitidas."""
    expression = expression.replace("×", "*").replace("÷", "/")
    expression = expression.replace("−", "-").replace("%", "/100")

    tree = ast.parse(expression, mode="eval")

    allowed_binary = (
        ast.Add, ast.Sub, ast.Mult, ast.Div,
        ast.Pow, ast.Mod, ast.FloorDiv
    )
    allowed_unary = (ast.UAdd, ast.USub)

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise ValueError("Número inválido")

        if isinstance(node, ast.BinOp):
            if type(node.op) not in allowed_binary:
                raise ValueError("Operação inválida")

            a = evaluate(node.left)
            b = evaluate(node.right)

            if abs(a) > 1e100 or abs(b) > 1e100:
                raise ValueError("Número muito grande")

            if isinstance(node.op, ast.Add):
                result = a + b
            elif isinstance(node.op, ast.Sub):
                result = a - b
            elif isinstance(node.op, ast.Mult):
                result = a * b
            elif isinstance(node.op, ast.Div):
                result = a / b
            elif isinstance(node.op, ast.Pow):
                if abs(b) > 100:
                    raise ValueError("Expoente muito grande")
                result = a ** b
            elif isinstance(node.op, ast.Mod):
                result = a % b
            else:
                result = a // b

            if isinstance(result, complex) or not math.isfinite(result):
                raise ValueError("Resultado inválido")
            return result

        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in allowed_unary:
                raise ValueError("Operação inválida")
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value

        raise ValueError("Expressão inválida")

    result = evaluate(tree)
    if abs(result) > 1e100:
        raise ValueError("Resultado muito grande")
    return result

def format_number(value):
    if isinstance(value, float) and value.is_integer():
        value = int(value)

    if isinstance(value, float):
        return f"{value:.10f}".rstrip("0").rstrip(".")

    return str(value)

# Estado da calculadora
expression = ""
display_value = "0"
history = ""
just_calculated = False
error_message = ""

# Botões
keys = [
    ["AC", "⌫", "%", "÷"],
    ["7", "8", "9", "×"],
    ["4", "5", "6", "−"],
    ["1", "2", "3", "+"],
    ["±", "0", ".", "="],
]

# Estado das animações de cada botão
button_states = {}
particles = []

# Fundo com pequenas estrelas
stars = [
    (
        random.randint(0, W),
        random.randint(0, H),
        random.uniform(0.5, 1.8),
        random.uniform(0, 6.28)
    )
    for _ in range(65)
]

def layout():
    w, h = screen.get_size()
    margin = max(12, int(w * 0.045))
    gap = max(7, int(w * 0.018))

    top = max(145, int(h * 0.245))
    bottom = h - max(18, int(h * 0.035))
    button_h = max(48, (bottom - top - gap * 4) // 5)
    button_w = (w - margin * 2 - gap * 3) // 4

    result = {}
    for row_i, row in enumerate(keys):
        for col_i, key in enumerate(row):
            x = margin + col_i * (button_w + gap)
            y = top + row_i * (button_h + gap)
            result[key] = pygame.Rect(x, y, button_w, button_h)

    return result, top, button_h

def add_particles(x, y):
    for _ in range(12):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(35, 150)
        particles.append({
            "x": float(x),
            "y": float(y),
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.uniform(0.25, 0.55),
            "max": 0.55,
            "size": random.randint(2, 4),
        })

def press_key(key):
    global expression, display_value, history
    global just_calculated, error_message

    error_message = ""

    if key == "AC":
        expression = ""
        display_value = "0"
        history = ""
        just_calculated = False
        return

    if key == "⌫":
        expression = expression[:-1]
        display_value = expression or "0"
        just_calculated = False
        return

    if key == "=":
        if not expression:
            return
        try:
            result = safe_calculate(expression)
            history = expression + " ="
            display_value = format_number(result)
            expression = display_value
            just_calculated = True
        except ZeroDivisionError:
            error_message = "Não é possível dividir por zero"
            display_value = "Erro"
        except Exception:
            error_message = "Expressão inválida"
            display_value = "Erro"
        return

    if key == "±":
        if expression:
            try:
                expression = format_number(-safe_calculate(expression))
                display_value = expression
                just_calculated = True
            except Exception:
                pass
        return

    if key == "%":
        if expression:
            try:
                expression = format_number(safe_calculate(expression) / 100)
                display_value = expression
                just_calculated = True
            except Exception:
                pass
        return

    operators = "+−×÷"

    if key in "0123456789.":
        if just_calculated:
            expression = ""
            history = ""
            just_calculated = False

        if key == ".":
            current = expression.split("+")[-1]
            for op in operators:
                current = current.split(op)[-1]
            if "." in current:
                return
            if not current:
                expression += "0"

        expression += key

    elif key in operators:
        if not expression:
            if key == "−":
                expression = "−"
            return

        if expression[-1] in operators:
            expression = expression[:-1] + key
        else:
            expression += key

        just_calculated = False

    display_value = expression or "0"

# Loop principal
running = True
previous_time = time.perf_counter()
elapsed = 0.0

while running:
    now = time.perf_counter()
    dt = min(now - previous_time, 0.04)
    previous_time = now
    elapsed += dt

    w, h = screen.get_size()
    mouse = pygame.mouse.get_pos()
    rects, top, button_h = layout()

    # Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(
                (max(280, event.w), max(440, event.h)),
                pygame.RESIZABLE
            )

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for key, rect in rects.items():
                    if rect.collidepoint(event.pos):
                        state = button_states.setdefault(
                            key, {"scale": 1.0, "flash": 0.0}
                        )
                        state["flash"] = 1.0
                        add_particles(rect.centerx, rect.centery)
                        press_key(key)
                        break

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                press_key("=")
            elif event.key == pygame.K_BACKSPACE:
                press_key("⌫")
            elif event.key == pygame.K_DELETE:
                press_key("AC")
            elif event.unicode in "0123456789.":
                press_key(event.unicode)
            elif event.unicode in "+-*/%":
                mapping = {"-": "−", "*": "×", "/": "÷"}
                press_key(mapping.get(event.unicode, event.unicode))

    # Fundo
    screen.fill(BG)

    # Estrelas animadas
    for sx, sy, size, phase in stars:
        brightness = int(45 + 55 * (
            0.5 + 0.5 * math.sin(elapsed * 1.5 + phase)
        ))
        color = (brightness // 2, brightness, min(255, brightness + 45))
        pygame.draw.circle(
            screen, color, (int(sx % w), int(sy % h)), max(1, int(size))
        )

    # Halo azul atrás do painel
    halo = pygame.Surface((w, h), pygame.SRCALPHA)
    pulse = 0.5 + 0.5 * math.sin(elapsed * 1.5)
    pygame.draw.ellipse(
        halo, (20, 100, 255, int(10 + pulse * 12)),
        (w * 0.08, h * 0.12, w * 0.84, h * 0.65)
    )
    screen.blit(halo, (0, 0))

    margin = max(12, int(w * 0.045))

    # Cabeçalho
    draw_text("NEBULA", 15, CYAN, margin, 25, align="topleft", bold=True)
    draw_text("CALCULATOR", 12, MUTED, margin, 46, align="topleft")
    draw_text("● ONLINE", 10, (92, 220, 165), w - margin, 31, align="topright")

    # Painel de resultado
    panel_rect = pygame.Rect(
        margin, 66, w - margin * 2, max(112, top - 80)
    )
    rounded_rect(screen, (19, 30, 51), panel_rect, 23)
    rounded_rect(screen, (35, 61, 94), panel_rect, 23, 1)

    draw_text(
        history if history else "SEU RESULTADO",
        12, MUTED, panel_rect.right - 16, panel_rect.y + 18,
        align="topright"
    )

    # Ajusta o tamanho do resultado para caber na tela
    max_text_width = panel_rect.width - 28
    size = 40
    while size > 18 and font(size, True).size(display_value)[0] > max_text_width:
        size -= 2

    result_color = RED if error_message else WHITE
    draw_text(
        display_value, size, result_color,
        panel_rect.right - 16, panel_rect.bottom - 20,
        align="bottomright", bold=True
    )

    # Pequeno indicador animado
    line_width = int((panel_rect.width - 28) * (0.3 + 0.7 * pulse))
    pygame.draw.line(
        screen, BLUE,
        (panel_rect.x + 14, panel_rect.bottom - 5),
        (panel_rect.x + 14 + line_width, panel_rect.bottom - 5), 2
    )

    if error_message:
        draw_text(
            error_message, 10, RED,
            panel_rect.x + 14, panel_rect.y + 40,
            align="topleft"
        )

    # Botões com hover, brilho, escala e sombra
    for key, rect in rects.items():
        state = button_states.setdefault(
            key, {"scale": 1.0, "flash": 0.0}
        )

        hovered = rect.collidepoint(mouse)
        target_scale = 0.96 if hovered else 1.0
        state["scale"] = lerp(
            state["scale"], target_scale, min(1, dt * 14)
        )
        state["flash"] = max(0, state["flash"] - dt * 2.5)

        scale = state["scale"]
        rw, rh = int(rect.width * scale), int(rect.height * scale)
        animated_rect = pygame.Rect(
            rect.centerx - rw // 2,
            rect.centery - rh // 2,
            rw, rh
        )

        # Sombra
        shadow = animated_rect.move(0, 5)
        rounded_rect(screen, (3, 6, 14), shadow, 17)

        is_operator = key in ("÷", "×", "−", "+", "=")
        is_special = key in ("AC", "⌫", "%", "±")

        if key == "=":
            base = (
                int(30 + pulse * 12),
                int(105 + pulse * 25),
                255
            )
        elif is_operator:
            base = (23, 51, 83)
        elif is_special:
            base = (28, 40, 62)
        else:
            base = BUTTON_HOVER if hovered else BUTTON

        if state["flash"] > 0:
            blend = state["flash"] * 0.45
            base = tuple(
                int(lerp(c, 130 if key == "=" else 100, blend))
                for c in base
            )

        rounded_rect(screen, base, animated_rect, 17)

        if hovered or state["flash"] > 0:
            rounded_rect(
                screen,
                (65, 153, 255),
                animated_rect,
                17, 1
            )

        text_color = WHITE
        if is_special:
            text_color = CYAN
        if key == "=":
            text_color = WHITE

        label_size = min(25, max(16, rect.height // 3))
        draw_text(
            key, label_size, text_color,
            animated_rect.centerx, animated_rect.centery,
            bold=key in operators if (operators := "+−×÷") else False
        )

    # Partículas de clique
    for p in particles[:]:
        p["life"] -= dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["vy"] += 90 * dt

        if p["life"] <= 0:
            particles.remove(p)
            continue

        alpha = clamp(p["life"] / p["max"], 0, 1)
        radius = max(1, int(p["size"] * alpha))
        pygame.draw.circle(
            screen,
            (int(50 + 100 * alpha), int(140 + 80 * alpha), 255),
            (int(p["x"]), int(p["y"])),
            radius
        )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
