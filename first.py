import pygame
import asyncio
import random
import math

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Vehicle Simulation')

# Set FPS (Frames per second)
fps = 30
pixels_per_km = 1000 / (fps * 60)  # Assuming 1 km = 1000 meters

# Initialize global collision count and a set to track collisions
collision_count = 0
collisions_set = set()

# Increase the safe distance threshold and drift speed
safe_distance_threshold = 100  # Increased distance for evasion
base_drift_speed = 1.5        # Increased drift speed

class Vehicle:
    def __init__(self, vehicle_type, vehicles):
        self.type = vehicle_type
        self.size = random.randint(10, 15) if vehicle_type == "motorcycle" else random.randint(20, 30)
        self.height = random.randint(20, 25) if vehicle_type == "motorcycle" else self.size // 2
        self.x, self.y = self.get_random_position(vehicles)  # Ensure this returns a valid (x, y) tuple
       
        avg_speed = random.randint(45, 50) if vehicle_type == "motorcycle" else random.randint(35, 40)
        self.speed = avg_speed * pixels_per_km / 60
        self.drift_speed = 0  # No horizontal movement initially

    def get_random_position(self, vehicles):
        while True:
            x = random.randint(self.size // 2, width - self.size // 2)
            y = random.randint(-height, 0)

            # Check for collisions with other vehicles
            collision = False
            for vehicle in vehicles:
                distance = math.sqrt((x - vehicle.x) ** 2 + (y - vehicle.y) ** 2)
                min_distance = (self.size + vehicle.size) / 2
                if distance < min_distance:
                    collision = True
                    break

            if not collision:
                return x, y  # Return a valid (x, y) position

    def circle_circle_collision(self, other_vehicle):
        distance = math.sqrt((self.x - other_vehicle.x) ** 2 + (self.y - other_vehicle.y) ** 2)
        min_distance = (self.size + other_vehicle.size) / 2
        return distance < min_distance

    def circle_rectangle_collision(self, car):
        closest_x = max(car.x, min(self.x, car.x + car.size))
        closest_y = max(car.y, min(self.y, car.y + car.height // 2))
        distance = math.sqrt((self.x - closest_x) ** 2 + (self.y - closest_y) ** 2)
        return distance < self.size // 2

    def move(self, vehicles):  # Accept the vehicles list as an argument
        global collision_count
        self.y += self.speed
        self.x += self.drift_speed

        if self.x - self.size // 2 < 0:
            self.x = self.size // 2
        elif self.x + self.size // 2 > width:
            self.x = width - self.size // 2

        # Reset drift unless close to another vehicle
        self.drift_speed = 0
        for vehicle in vehicles:
            if vehicle != self:
                distance = math.sqrt((self.x - vehicle.x) ** 2 + (self.y - vehicle.y) ** 2)
                if distance < safe_distance_threshold:
                    if self.type == "motorcycle" and vehicle.type == "motorcycle":
                        if self.circle_circle_collision(vehicle):
                            self.start_evasion(vehicle)
                    elif self.type == "motorcycle" and vehicle.type == "car":
                        if self.circle_rectangle_collision(vehicle):
                            self.start_evasion(vehicle)

        if self.y > height:
            return False  # Signal to remove vehicle after exiting the screen

        if 0 <= self.y <= height:
            for vehicle in vehicles:
                if vehicle != self:
                    if self.type == "motorcycle" and vehicle.type == "motorcycle":
                        if self.circle_circle_collision(vehicle):
                            vehicle_pair = tuple(sorted([vehicles.index(self), vehicles.index(vehicle)]))
                            if vehicle_pair not in collisions_set:
                                collisions_set.add(vehicle_pair)
                                collision_count += 1
                    elif self.type == "motorcycle" and vehicle.type == "car":
                        if self.circle_rectangle_collision(vehicle):
                            vehicle_pair = tuple(sorted([vehicles.index(self), vehicles.index(vehicle)]))
                            if vehicle_pair not in collisions_set:
                                collisions_set.add(vehicle_pair)
                                collision_count += 1
        return True

    def start_evasion(self, vehicle):
        if self.x < vehicle.x and self.x + self.size < width - 10:
            self.drift_speed = -base_drift_speed  # Drift left to evade
        elif self.x > vehicle.x and self.x - self.size > 10:
            self.drift_speed = base_drift_speed   # Drift right to evade

    def draw(self, screen):
        if self.type == "motorcycle":
            pygame.draw.ellipse(screen, 'Yellow', (int(self.x - self.size // 2), int(self.y - self.height // 2), self.size, self.height))
        else:
            pygame.draw.rect(screen, 'White', (int(self.x - self.size // 2), int(self.y - self.height // 2), self.size, self.height))

async def get_user_input():
    input_box = pygame.Rect(width // 4, height // 3 + 40, 200, 40)
    font = pygame.font.Font(None, 36)
    user_input = ''
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    done = False

    while not done:
        screen.fill('#003366')

        prompt_text = font.render('Enter the number of vehicles:', True, pygame.Color('white'))
        screen.blit(prompt_text, (width // 4, height // 3 - 40))

        text_surface = font.render(user_input, True, color)
        width_text = max(200, text_surface.get_width() + 10)
        input_box.w = width_text
        screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        user_input = user_input[:-1]
                    else:
                        user_input += event.unicode

        pygame.display.flip()
        pygame.time.Clock().tick(30)
        await asyncio.sleep(0)

    return int(user_input)

async def main():
    num_vehicles = await get_user_input()
    vehicles = []
    for _ in range(num_vehicles):
        vehicle_type = "motorcycle" if random.random() < 0.6 else "car"
        vehicles.append(Vehicle(vehicle_type, vehicles))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill('#003366')
        
        # Update vehicle positions and remove those that exit the screen
        vehicles = [vehicle for vehicle in vehicles if vehicle.move(vehicles)]
        
        for vehicle in vehicles:
            vehicle.draw(screen)

        font = pygame.font.Font(None, 36)
        text = font.render(f"Collisions: {collision_count}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
       
        pygame.display.flip()
        pygame.time.delay(20)
        await asyncio.sleep(0)

    pygame.quit()

# Run the game
asyncio.run(main())
