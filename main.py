import pygame
import sys
import math
import random

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Asteroids")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 18)
font_large = pygame.font.SysFont("arial", 40, bold=True)

ROTATION_SPEED = 4.5
THRUST = 0.22
DRAG = 0.985
MAX_SPEED = 7.5
MISSILE_SPEED = 11.0
ENEMY_MISSILE_SPEED = 6.0
DETECTION_RANGE = 280
FOV_THRESHOLD = 0.65

def reset_game():
    global ship_pos, ship_vel, ship_angle, ship_health, score, game_state
    global missiles, enemy_missiles, asteroids, enemy_pos, enemy_vel, enemy_angle, enemy_state, enemy_fire_cd, enemy_alive, respawn_timer
    ship_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    ship_vel = pygame.Vector2(0, 0)
    ship_angle = 90.0
    ship_health = 100
    score = 0
    game_state = "PLAY"
    missiles = []
    enemy_missiles = []
    asteroids = []
    enemy_pos = pygame.Vector2(120, 120)
    enemy_vel = pygame.Vector2(1.2, 0.9)
    enemy_angle = 0.0
    enemy_state = "PATROL"
    enemy_fire_cd = 0
    enemy_alive = True
    respawn_timer = 0
    for _ in range(5):
        spawn_asteroid()

def spawn_asteroid():
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top": pos = pygame.Vector2(random.randint(0, WIDTH), -30)
    elif side == "bottom": pos = pygame.Vector2(random.randint(0, WIDTH), HEIGHT + 30)
    elif side == "left": pos = pygame.Vector2(-30, random.randint(0, HEIGHT))
    else: pos = pygame.Vector2(WIDTH + 30, random.randint(0, HEIGHT))

    target = pygame.Vector2(random.randint(200, WIDTH - 200), random.randint(200, HEIGHT - 200))
    vel = (target - pos).normalize() * random.uniform(0.9, 2.0)
    asteroids.append({"pos": pos, "vel": vel, "radius": random.randint(20, 32)})

def fire_player_bullet():
    rad = math.radians(ship_angle)
    fwd = pygame.Vector2(math.cos(rad), -math.sin(rad))
    spawn_pt = ship_pos + fwd * 24
    bullet_vel = fwd * MISSILE_SPEED + ship_vel * 0.3
    missiles.append({"pos": pygame.Vector2(spawn_pt), "vel": bullet_vel, "radius": 4})

def fire_enemy_bullet(target_dir):
    rad = math.radians(enemy_angle)
    fwd = pygame.Vector2(math.cos(rad), -math.sin(rad))
    spawn_pt = enemy_pos + fwd * 22
    bullet_vel = target_dir * ENEMY_MISSILE_SPEED
    enemy_missiles.append({"pos": pygame.Vector2(spawn_pt), "vel": bullet_vel, "radius": 4})

reset_game()
fire_cooldown = 0
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game_state == "PLAY" and fire_cooldown == 0:
                fire_player_bullet()
                fire_cooldown = 10
            elif event.key == pygame.K_r and game_state != "PLAY":
                reset_game()

    keys = pygame.key.get_pressed()

    if game_state == "PLAY":
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            ship_angle += ROTATION_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            ship_angle -= ROTATION_SPEED

        if keys[pygame.K_SPACE] and fire_cooldown == 0:
            fire_player_bullet()
            fire_cooldown = 10

        if fire_cooldown > 0:
            fire_cooldown -= 1

        radians = math.radians(ship_angle)
        forward = pygame.Vector2(math.cos(radians), -math.sin(radians))

        ship_acc = pygame.Vector2(0, 0)
        is_thrusting = False

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            ship_acc = forward * THRUST
            is_thrusting = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            ship_acc = -forward * (THRUST * 0.5)

        ship_vel += ship_acc
        ship_vel *= DRAG

        if ship_vel.length() > MAX_SPEED:
            ship_vel.scale_to_length(MAX_SPEED)

        ship_pos += ship_vel

        if ship_pos.x > WIDTH: ship_pos.x = 0
        elif ship_pos.x < 0: ship_pos.x = WIDTH
        if ship_pos.y > HEIGHT: ship_pos.y = 0
        elif ship_pos.y < 0: ship_pos.y = HEIGHT

        if enemy_alive:
            diff = ship_pos - enemy_pos
            distance = enemy_pos.distance_to(ship_pos)
            to_player = diff.normalize() if diff.length() > 0 else pygame.Vector2(1, 0)

            e_rad = math.radians(enemy_angle)
            enemy_forward = pygame.Vector2(math.cos(e_rad), -math.sin(e_rad))
            dot = enemy_forward.dot(to_player)

            detected = distance < DETECTION_RANGE and dot > FOV_THRESHOLD
            enemy_state = "ATTACK" if detected else "PATROL"

            if detected:
                desired_angle = math.degrees(math.atan2(-to_player.y, to_player.x))
                angle_diff = (desired_angle - enemy_angle + 180) % 360 - 180
                enemy_angle += angle_diff * 0.08
                if distance > 120:
                    enemy_pos += enemy_forward * 1.8
                enemy_fire_cd += 1
                if enemy_fire_cd >= 40:
                    fire_enemy_bullet(to_player)
                    enemy_fire_cd = 0
            else:
                enemy_angle = (enemy_angle + 0.6) % 360
                enemy_pos += enemy_vel
                if enemy_pos.x < 50 or enemy_pos.x > WIDTH - 50: enemy_vel.x *= -1
                if enemy_pos.y < 50 or enemy_pos.y > HEIGHT - 50: enemy_vel.y *= -1
                if enemy_fire_cd > 0: enemy_fire_cd -= 1
        else:
            respawn_timer -= 1
            if respawn_timer <= 0:
                enemy_alive = True
                enemy_pos = pygame.Vector2(random.choice([80, WIDTH - 80]), random.choice([80, HEIGHT - 80]))

        for m in missiles[:]:
            m["pos"] += m["vel"]
            if m["pos"].x < -10 or m["pos"].x > WIDTH + 10 or m["pos"].y < -10 or m["pos"].y > HEIGHT + 10:
                missiles.remove(m)

        for em in enemy_missiles[:]:
            em["pos"] += em["vel"]
            if em["pos"].x < -10 or em["pos"].x > WIDTH + 10 or em["pos"].y < -10 or em["pos"].y > HEIGHT + 10:
                enemy_missiles.remove(em)
            elif em["pos"].distance_to(ship_pos) < 18:
                ship_health -= 15
                enemy_missiles.remove(em)
                if ship_health <= 0:
                    game_state = "GAMEOVER"

        for a in asteroids:
            a["pos"] += a["vel"]
            if a["pos"].x < -40: a["pos"].x = WIDTH + 40
            elif a["pos"].x > WIDTH + 40: a["pos"].x = -40
            if a["pos"].y < -40: a["pos"].y = HEIGHT + 40
            elif a["pos"].y > HEIGHT + 40: a["pos"].y = -40

            if a["pos"].distance_to(ship_pos) < a["radius"] + 14:
                ship_health -= 25
                ship_vel += (ship_pos - a["pos"]).normalize() * 4.0
                if ship_health <= 0:
                    game_state = "GAMEOVER"

        for m in missiles[:]:
            hit = False
            for a in asteroids[:]:
                if m["pos"].distance_to(a["pos"]) < m["radius"] + a["radius"]:
                    asteroids.remove(a)
                    spawn_asteroid()
                    score += 20
                    hit = True
                    break
            if not hit and enemy_alive:
                if m["pos"].distance_to(enemy_pos) < 22:
                    enemy_alive = False
                    respawn_timer = 240
                    score += 100
                    hit = True
            if hit and m in missiles:
                missiles.remove(m)

        if score >= 600:
            game_state = "WIN"

    screen.fill((10, 12, 18))

    if enemy_alive and game_state == "PLAY":
        pygame.draw.circle(screen, (40, 45, 60), (int(enemy_pos.x), int(enemy_pos.y)), DETECTION_RANGE, 1)

        fov_angle = math.degrees(math.acos(FOV_THRESHOLD))
        for sign in (-1, 1):
            brad = math.radians(enemy_angle + sign * fov_angle)
            bvec = pygame.Vector2(math.cos(brad), -math.sin(brad)) * DETECTION_RANGE
            pygame.draw.line(screen, (35, 40, 55), enemy_pos, enemy_pos + bvec, 1)

        pygame.draw.line(screen, (220, 50, 50), enemy_pos, enemy_pos + enemy_forward * 65, 2)

        e_color = (255, 60, 60) if enemy_state == "ATTACK" else (220, 220, 220)
        ep1 = enemy_pos + enemy_forward * 20
        e_left = enemy_forward.rotate(135)
        e_right = enemy_forward.rotate(-135)
        ep2 = enemy_pos + e_left * 15
        ep3 = enemy_pos + e_right * 15
        pygame.draw.polygon(screen, e_color, [ep1, ep2, ep3])
        pygame.draw.polygon(screen, (255, 255, 255), [ep1, ep2, ep3], 1)

    for a in asteroids:
        pygame.draw.circle(screen, (135, 130, 120), (int(a["pos"].x), int(a["pos"].y)), a["radius"])
        pygame.draw.circle(screen, (75, 70, 65), (int(a["pos"].x), int(a["pos"].y)), a["radius"], 2)

    for m in missiles:
        pygame.draw.circle(screen, (255, 230, 80), (int(m["pos"].x), int(m["pos"].y)), m["radius"])

    for em in enemy_missiles:
        pygame.draw.circle(screen, (255, 60, 60), (int(em["pos"].x), int(em["pos"].y)), em["radius"])

    if game_state == "PLAY":
        p1 = ship_pos + forward * 22
        left_vec = forward.rotate(140)
        right_vec = forward.rotate(-140)
        p2 = ship_pos + left_vec * 16
        p3 = ship_pos + right_vec * 16

        if is_thrusting:
            flame_len = random.uniform(14, 22)
            flame_tip = ship_pos - forward * flame_len
            f_left = ship_pos + left_vec * 8
            f_right = ship_pos + right_vec * 8
            pygame.draw.polygon(screen, (255, 120, 20), [flame_tip, f_left, f_right])
            pygame.draw.polygon(screen, (255, 240, 60), [ship_pos - forward * (flame_len * 0.6), f_left, f_right])

        pygame.draw.polygon(screen, (0, 220, 255), [p1, p2, p3])
        pygame.draw.polygon(screen, (255, 255, 255), [p1, p2, p3], 2)

        health_pct = max(0, ship_health / 100)
        pygame.draw.rect(screen, (60, 60, 60), (20, 20, 140, 14))
        pygame.draw.rect(screen, (50, 230, 90) if health_pct > 0.35 else (230, 50, 50), (20, 20, int(140 * health_pct), 14))
        pygame.draw.rect(screen, (255, 255, 255), (20, 20, 140, 14), 1)

        t_hp = font.render(f"Shield: {max(0, ship_health)}%", True, (255, 255, 255))
        t_score = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(t_hp, (170, 18))
        screen.blit(t_score, (20, 42))

        if enemy_alive:
            t_dist = font.render(f"Distance: {distance:.1f}", True, (180, 190, 200))
            t_dot = font.render(f"Dot: {dot:.2f}", True, (255, 200, 50))
            state_color = (255, 80, 80) if enemy_state == "ATTACK" else (100, 255, 100)
            t_state = font.render(f"Enemy: {enemy_state}", True, state_color)
            screen.blit(t_dist, (20, 66))
            screen.blit(t_dot, (20, 88))
            screen.blit(t_state, (20, 110))
    elif game_state == "GAMEOVER":
        msg = font_large.render("GAME OVER", True, (255, 60, 60))
        sub = font.render("Press 'R' to Restart", True, (220, 220, 220))
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))
    elif game_state == "WIN":
        msg = font_large.render("YOU WIN!", True, (60, 255, 120))
        sub = font.render(f"Final Score: {score}  |  Press 'R' to Play Again", True, (220, 220, 220))
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
