import socket
import os
import pygame
import threading
import random
import sys


class PingPongException(Exception):
    pass


class Server:
    def __init__(self):
        self.HOST = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.PORT = 12000
        self.hostName = socket.gethostname()
        self.hostAddress = socket.gethostbyname(self.hostName)

    def openServer(self):
        server_address = (self.hostAddress, self.PORT)
        try:
            self.HOST.bind(server_address)
            self.HOST.listen(1)
            print("Server is open")
            return 0
        except IndexError:
            print(server_address, "is not valid")
            return 1
        except OSError:
            print(server_address, "is already in use")
            return 2


class Client:
    def __init__(self):
        self.HOST = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.PORT = 12000

        self.hostName = socket.gethostname()
        self.hostAddress = socket.gethostbyname(self.hostName)

    def connect(self):
        while True:
            IP = input("Address: ")  # self.hostAddress
            PORT = int(input("Port: "))  # self.PORT
            try:
                self.HOST.connect((IP, PORT))
                print("Connected to", (IP, PORT))
                break
            except ConnectionRefusedError:
                print((IP, PORT), "refused to connect")
            except IndexError:
                print((IP, PORT), "is not valid")
            except OSError:
                print((IP, PORT), "is not valid")


def showInfo(port):
    hostName = socket.gethostname()
    hostAddress = socket.gethostbyname(hostName)
    print("Host Name:", hostName, "\n-----------------------")
    print("Your IP:", hostAddress)
    print("Your PORT:", port, "\n-----------------------")


def CommandLine():
    defaultPort = 12000
    if sys.platform == 'win32':
        os.system("cls")
    else:
        os.system("clear")
    showInfo(defaultPort)


def Prompt():
    connection = Server()
    while True:
        command = input("PingPongShell> ")
        if command == "openserver":
            connection.openServer()
            while True:
                client, address = connection.HOST.accept()
                if client:  # if client connected
                    print("Connected by", address)
                    return connection.HOST, client
        elif command == "connect":
            connection = Client()
            connection.connect()
            break
        elif command == "exit" or command == "quit":
            userEvent = "The user exited the shell."
            raise PingPongException(userEvent)
        elif command == "help":
            print("""Commands:
openserver - Opens a server
connect    - Connects to an existing server
exit/quit  - Exits the shell
help       - Prints this help page
""")
        else:
            print("Command '" + command + """' not found
Type 'help' for help.""")
    return connection.HOST, False


class Ball:
    def __init__(self, surface):
        self.radius = 10
        self.interface = surface
        self.WIDTH, self.HEIGHT = pygame.display.get_surface().get_size()
        self.location = [self.WIDTH // 2, self.HEIGHT // 2]

        step = 5
        self.speed = [random.choice((step, -step)), random.choice((step, -step))]

        self.player_point = 0

    def isCollision(self, player, competitor, top, bottom, left, right):
        if self.location[0] <= left + self.radius:
            self.speed[0] = -self.speed[0]
        elif self.location[0] >= right - self.radius:
            self.speed[0] = -self.speed[0]
            self.player_point += 1
        elif self.location[1] <= top + self.radius or self.location[1] >= bottom - self.radius:
            self.speed[1] = -self.speed[1]
        elif self.location[0] <= player.location[0] + player.WIDTH + self.radius:
            if player.location[1] <= self.location[1] <= player.location[1] + player.HEIGHT:
                self.speed[0] = -self.speed[0]
        elif self.location[0] >= competitor.location[0] - self.radius:
            if competitor.location[1] <= self.location[1] <= competitor.location[1] + competitor.HEIGHT:
                self.speed[0] = -self.speed[0]

    def render(self):
        WHITE = (255, 255, 255)
        pygame.draw.circle(self.interface, WHITE, self.location, self.radius)


class Player:
    def __init__(self, surface):
        self.WIDTH, self.HEIGHT = 10, 100
        self.location = [30, 30]
        self.interface = surface
        self.speed = 5
        self.point = 0

    def sendingRequest(self, host, ball_location):
        try:
            location = "%s %s %s %s" % (self.location[1], ball_location[0], ball_location[1], self.point)
            host.sendall(location.encode("utf-8"))
        except ConnectionResetError:
            print("Partner is disconnected")
            pygame.quit()
        except ConnectionAbortedError:
            print("Your partner software has some errors")
            pygame.quit()

    def render(self):
        WHITE = (255, 255, 255)
        pygame.draw.rect(self.interface, WHITE, (self.location[0], self.location[1], self.WIDTH, self.HEIGHT))


class Competitor:
    def __init__(self, surface):
        self.WIDTH, self.HEIGHT = 10, 100
        self.location = [970, 30]
        self.interface = surface
        self.speed = 5

        self.ball_location = [10, 10]
        self.point = 0
        self.requestErrors = 0

    def handlingRequest(self, client):
        try:
            data_received = client.recv(128).decode("utf-8")
            location = data_received.split()

            self.location[1] = int(location[0])
            # ball_location[0] = midOfScreen + (midOfScreen - competitor_location)
            self.ball_location[0] = 500 + (500 - int(location[1]))
            self.ball_location[1] = int(location[2])
            self.point = int(location[3])
        except ConnectionResetError:
            print("The competitor disconnected")
            self.requestErrors = 1
        except ConnectionAbortedError:
            print("The competitor has issues with their thread")
            self.requestErrors = 2
        except BrokenPipeError:
            print("The competitor disconnected")
            self.requestErrors = 1
        except IndexError:
            print("The competitor disconnected")
            self.requestErrors = 1

    def render(self):
        WHITE = (255, 255, 255)
        pygame.draw.rect(self.interface, WHITE, (self.location[0], self.location[1], self.WIDTH, self.HEIGHT))


class PingPong:
    init_directory = os.path.dirname(__file__)

    def __init__(self):
        self.WIDTH, self.HEIGHT = 1000, 500
        self.screen = None

        if sys.platform == 'win32':
            icon = pygame.image.load("icon.png")
        else:
            icon = pygame.image.load(os.path.join(PingPong.init_directory, "icon.png"))
        pygame.display.set_icon(icon)

    def scoreBoard(self, player_point, competitor_point):
        GREY = (128, 128, 128)
        MIDDLE = [self.WIDTH // 2, self.HEIGHT // 2]

        player_point = str(player_point)
        competitor_point = str(competitor_point)

        font = os.path.join(PingPong.init_directory, "cour.ttf")
        size = 48
        render_font = pygame.font.Font(font, size)

        renderPlayerPoint = render_font.render(player_point, True, GREY)
        renderCompetitorPoint = render_font.render(competitor_point, True, GREY)

        self.screen.blit(renderPlayerPoint, (MIDDLE[0] - 100, MIDDLE[1] - 25))
        self.screen.blit(renderCompetitorPoint, (MIDDLE[0] + 50, MIDDLE[1] - 25))

    def start(self):
        pygame.init()
        frame = pygame.time.Clock()
        FPS = 60

        host, server = Prompt()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        if server:  # server
            pygame.display.set_caption("Ping Pong ! Server")
            host = server
        else:  # client
            pygame.display.set_caption("Ping Pong ! Client")
        gameOver = False

        player = Player(self.screen)
        competitor = Competitor(self.screen)
        ball = Ball(self.screen)

        BLACK = (0, 0, 0)
        TOP, BOTTOM, LEFT, RIGHT = 0, self.HEIGHT, 0, self.WIDTH
        while not gameOver:
            self.screen.fill(BLACK)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    gameOver = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        gameOver = True

            # player moving
            moving = pygame.key.get_pressed()
            if moving[pygame.K_w] or moving[pygame.K_a] or moving[pygame.K_UP] or moving[pygame.K_RIGHT]:
                player.location[1] -= player.speed
            elif moving[pygame.K_s] or moving[pygame.K_d] or moving[pygame.K_DOWN] or moving[pygame.K_LEFT]:
                player.location[1] += player.speed

            if player.location[1] <= TOP:
                player.location[1] = TOP
            elif player.location[1] >= BOTTOM - player.HEIGHT:
                player.location[1] = BOTTOM - player.HEIGHT

            # if this device host is server
            if server:
                # if ball is collision
                ball.location[0] += ball.speed[0]
                ball.location[1] += ball.speed[1]

            else:
                ball.location = competitor.ball_location

            ball_parameters = (player, competitor, TOP, BOTTOM, LEFT, RIGHT)
            ball_collision = threading.Thread(target=ball.isCollision, args=ball_parameters)

            handling = threading.Thread(target=competitor.handlingRequest, args=(host,))
            sending = threading.Thread(target=player.sendingRequest, args=(host, ball.location))

            handling.start()
            sending.start()
            ball_collision.start()

            if competitor.requestErrors:
                break

            player.point = ball.player_point
            self.scoreBoard(player.point, competitor.point)

            ball.render()
            player.render()
            competitor.render()

            frame.tick(FPS)
            pygame.display.update()
        host.close()
        pygame.quit()


if __name__ == "__main__":
    game = PingPong()
    CommandLine()
    while True:
        game.start()
