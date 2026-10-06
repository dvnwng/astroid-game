import pygame
import random
import math
import asyncio

pygame.init()

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 80)

THRUST = 0.15
DRAG = 0.99
MAX_SPEED = 7

MAX_ASTEROIDS = 8
MAX_ENEMIES = 2


class Asteroid:
    def __init__(self, x, y, radius, speed, angle):
        self.pos = pygame.Vector2(x, y)
        self.radius = radius
        self.velocity = pygame.Vector2(1, 0).rotate(angle) * speed
        self.mass = radius ** 2

    def update(self):
        self.pos += self.velocity

        if self.pos.x - self.radius <= 0 or self.pos.x + self.radius >= WIDTH:
            self.velocity.x *= -1

        if self.pos.y - self.radius <= 0 or self.pos.y + self.radius >= HEIGHT:
            self.velocity.y *= -1

    def draw(self):
        pygame.draw.circle(
            screen,
            (180, 180, 180),
            self.pos,
            self.radius
        )


class Ship:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.angle = 90
        self.radius = 15
        self.immunity = 60

    def forward(self):
        radians = math.radians(self.angle)

        return pygame.Vector2(
            math.cos(radians),
            -math.sin(radians)
        )

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle += 3

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle -= 3

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity += self.forward() * THRUST

        self.velocity *= DRAG

        if self.velocity.length() > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)

        self.pos += self.velocity

        if self.pos.x > WIDTH:
            self.pos.x = 0

        if self.pos.x < 0:
            self.pos.x = WIDTH

        if self.pos.y > HEIGHT:
            self.pos.y = 0

        if self.pos.y < 0:
            self.pos.y = HEIGHT

        if self.immunity > 0:
            self.immunity -= 1

    def draw(self):
        forward = self.forward()

        front = self.pos + forward * 22
        left = self.pos + forward.rotate(140) * 16
        right = self.pos + forward.rotate(-140) * 16

        pygame.draw.polygon(
            screen,
            (255, 255, 255),
            [front, left, right],
            2
        )


class Enemy:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)

        self.velocity = pygame.Vector2(1, 0).rotate(
            random.randint(0, 360)
        ) * random.uniform(1, 2.5)

        self.radius = 16
        self.timer = 0

    def update(self):
        self.pos += self.velocity

        if self.pos.x <= 0 or self.pos.x >= WIDTH:
            self.velocity.x *= -1

        if self.pos.y <= 0 or self.pos.y >= HEIGHT:
            self.velocity.y *= -1

        if self.timer > 0:
            self.timer -= 1

    def shoot(self, player):
        distance = self.pos.distance_to(player.pos)

        if distance < 300 and self.timer <= 0:
            direction = player.pos - self.pos

            if direction.length() > 0:
                self.timer = 60

                return Bullet(
                    self.pos.x,
                    self.pos.y,
                    direction.normalize(),
                    5
                )

        return None

    def draw(self):
        forward = self.velocity.normalize()

        front = self.pos + forward * 22
        left = self.pos + forward.rotate(140) * 16
        right = self.pos + forward.rotate(-140) * 16

        pygame.draw.polygon(
            screen,
            (255, 0, 0),
            [front, left, right],
            2
        )


class Bullet:
    def __init__(self, x, y, direction, speed=7):
        self.pos = pygame.Vector2(x, y)
        self.velocity = direction * speed
        self.radius = 4

    def update(self):
        self.pos += self.velocity

    def draw(self, color):
        pygame.draw.circle(
            screen,
            color,
            self.pos,
            self.radius
        )

    def off_screen(self):
        return (
            self.pos.x < 0
            or self.pos.x > WIDTH
            or self.pos.y < 0
            or self.pos.y > HEIGHT
        )


def make_asteroid():
    return Asteroid(
        random.randint(30, WIDTH - 30),
        random.randint(30, HEIGHT - 30),
        random.randint(25, 40),
        random.uniform(1, 3),
        random.randint(0, 360)
    )


def make_enemy():
    return Enemy(
        random.randint(30, WIDTH - 30),
        random.randint(30, HEIGHT - 30)
    )


async def main():

    asteroids = []

    for i in range(5):
        asteroids.append(make_asteroid())

    enemies = [make_enemy()]

    ship = Ship(
        WIDTH / 2,
        HEIGHT / 2
    )

    bullets = []
    enemy_bullets = []

    rocks_hit = 0
    asteroid_timer = 0
    enemy_timer = 0

    running = True
    game_over = False


    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_SPACE and not game_over:

                    bullets.append(
                        Bullet(
                            ship.pos.x,
                            ship.pos.y,
                            ship.forward()
                        )
                    )


        if not game_over:

            ship.update()

            asteroid_timer += 1
            enemy_timer += 1


            if asteroid_timer >= 120:

                asteroid_timer = 0

                if len(asteroids) < MAX_ASTEROIDS:
                    asteroids.append(make_asteroid())


            if enemy_timer >= 300:

                enemy_timer = 0

                if len(enemies) < MAX_ENEMIES:
                    enemies.append(make_enemy())


            for asteroid in asteroids:

                asteroid.update()

                if ship.immunity <= 0:

                    distance = ship.pos.distance_to(
                        asteroid.pos
                    )

                    if distance < ship.radius + asteroid.radius:
                        game_over = True


            for enemy in enemies:

                enemy.update()

                if ship.immunity <= 0:

                    distance = ship.pos.distance_to(
                        enemy.pos
                    )

                    if distance < ship.radius + enemy.radius:
                        game_over = True

                shot = enemy.shoot(ship)

                if shot:
                    enemy_bullets.append(shot)


            for i in range(len(asteroids)):

                for j in range(i + 1, len(asteroids)):

                    a = asteroids[i]
                    b = asteroids[j]

                    difference = b.pos - a.pos
                    distance = difference.length()

                    if distance > 0 and distance < a.radius + b.radius:

                        normal = difference.normalize()

                        speed = (
                            b.velocity - a.velocity
                        ).dot(normal)

                        if speed < 0:

                            impulse = (
                                2 * speed
                                / (a.mass + b.mass)
                            )

                            a.velocity += (
                                impulse
                                * b.mass
                                * normal
                            )

                            b.velocity -= (
                                impulse
                                * a.mass
                                * normal
                            )


            for bullet in bullets[:]:

                bullet.update()


                for asteroid in asteroids[:]:

                    distance = bullet.pos.distance_to(
                        asteroid.pos
                    )

                    if distance < bullet.radius + asteroid.radius:

                        rocks_hit += 1

                        old_radius = asteroid.radius
                        old_pos = asteroid.pos.copy()

                        asteroids.remove(asteroid)

                        if bullet in bullets:
                            bullets.remove(bullet)


                        if old_radius > 15:

                            new_radius = old_radius // 2

                            asteroids.append(
                                Asteroid(
                                    old_pos.x + new_radius,
                                    old_pos.y,
                                    new_radius,
                                    3,
                                    random.randint(0, 360)
                                )
                            )

                            asteroids.append(
                                Asteroid(
                                    old_pos.x - new_radius,
                                    old_pos.y,
                                    new_radius,
                                    3,
                                    random.randint(0, 360)
                                )
                            )

                        break


                if bullet in bullets:

                    for enemy in enemies[:]:

                        distance = bullet.pos.distance_to(
                            enemy.pos
                        )

                        if distance < bullet.radius + enemy.radius:

                            enemies.remove(enemy)
                            bullets.remove(bullet)

                            break


                if bullet in bullets and bullet.off_screen():
                    bullets.remove(bullet)


            for bullet in enemy_bullets[:]:

                bullet.update()

                distance = bullet.pos.distance_to(
                    ship.pos
                )

                if (
                    ship.immunity <= 0
                    and distance < bullet.radius + ship.radius
                ):

                    game_over = True
                    enemy_bullets.remove(bullet)

                elif bullet.off_screen():

                    enemy_bullets.remove(bullet)


        screen.fill((0, 0, 0))


        for asteroid in asteroids:
            asteroid.draw()


        for enemy in enemies:
            enemy.draw()


        for bullet in bullets:
            bullet.draw((255, 100, 100))


        for bullet in enemy_bullets:
            bullet.draw((0, 255, 255))


        ship.draw()


        if not game_over:

            rocks_text = font.render(
                f"Rocks Hit: {rocks_hit}",
                True,
                (255, 255, 255)
            )

            screen.blit(
                rocks_text,
                (10, 10)
            )


        else:

            lose_text = big_font.render(
                "YOU LOSE",
                True,
                (255, 0, 0)
            )

            score_text = font.render(
                f"Rocks Hit: {rocks_hit}",
                True,
                (255, 255, 255)
            )

            screen.blit(
                lose_text,
                (
                    WIDTH / 2 - lose_text.get_width() / 2,
                    HEIGHT / 2 - 50
                )
            )

            screen.blit(
                score_text,
                (
                    WIDTH / 2 - score_text.get_width() / 2,
                    HEIGHT / 2 + 30
                )
            )


        pygame.display.flip()

        clock.tick(60)

        await asyncio.sleep(0)


    pygame.quit()


asyncio.run(main())
