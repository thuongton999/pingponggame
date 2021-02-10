import socket
import time
import os
import pygame
import threading


class Server:
    def __init__(self):
        self.HOST = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.PORT = 1000
        self.hostName = socket.gethostname()
        self.hostAddress = socket.gethostbyname(self.hostName)

    def openServer(self):
        server_address = (self.hostAddress, self.PORT)
        try:
            self.HOST.bind(server_address)
            self.HOST.listen(1)
            print("Server is open")
        except IndexError or OSError:
            print(server_address, "is not valid")


class Client:
    def __init__(self):
        self.HOST = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.PORT = 1000

        self.hostName = socket.gethostname()
        self.hostAddress = socket.gethostbyname(self.hostName)

    def connect(self):
        while True:
            os.system("cls")
            showInfo(self.PORT)
            IP = input("Address: ")  # self.hostAddress
            PORT = int(input("Port: "))  # self.PORT
            try:
                self.HOST.connect((IP, PORT))
                print("Connected to", (IP, PORT))
                break
            except ConnectionRefusedError:
                print((IP, PORT), "refuse to connect, wait 1 second to continue")
                time.sleep(1)
            except IndexError or OSError:
                print((IP, PORT), "is not valid, wait 1 second to continue")
                time.sleep(1)


def showInfo(port):
    hostName = socket.gethostname()
    hostAddress = socket.gethostbyname(hostName)
    print("Host Name:", hostName, "\n-----------------------")
    print("Your IP:", hostAddress)
    print("Your PORT:", port, "\n-----------------------")


def CommandLine():
    defaultPORT = 1000
    connection = Server()
    while True:
        os.system("cls")
        showInfo(defaultPORT)
        command = input("Command: ")
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
        elif command == "exit":
            break
        else:
            print("Command '" + command + "' not found, wait 1 second to continue")
            time.sleep(1)
    return connection.HOST, False


class Player:
    def __init__(self, surface):
        self.WIDTH, self.HEIGHT = 10, 100
        self.location = [30, 30]
        self.interface = surface
        self.speed = 5

    def sendingRequest(self, host):
        try:
            location = str(self.location[1])
            host.sendall(location.encode("utf-8"))
        except ConnectionResetError:
            print("Partner is disconnected")
        except ConnectionAbortedError:
            print("Your partner software has some errors")

    def render(self):
        WHITE = (255, 255, 255)
        pygame.draw.rect(self.interface, WHITE, (self.location[0], self.location[1], self.WIDTH, self.HEIGHT))


class Competitor:
    def __init__(self, surface):
        self.WIDTH, self.HEIGHT = 10, 100
        self.location = [970, 30]
        self.interface = surface
        self.speed = 5

    def handlingRequest(self, client):
        try:
            location = client.recv(32).decode("utf-8")
            if 3 >= len(location) >= 1:
                self.location[1] = int(location)
        except ConnectionResetError or ConnectionAbortedError:
            print("Partner is disconnected")

    def render(self):
        WHITE = (255, 255, 255)
        pygame.draw.rect(self.interface, WHITE, (self.location[0], self.location[1], self.WIDTH, self.HEIGHT))


class PingPong:
    def __init__(self):
        self.WIDTH, self.HEIGHT = 1000, 500
        self.screen = None

        icon = pygame.image.load("icon.png")
        pygame.display.set_icon(icon)

    def start(self):
        frame = pygame.time.Clock()
        FPS = 60

        host, client = CommandLine()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        if client:
            pygame.display.set_caption("Ping Pong ! Server")
        else:
            pygame.display.set_caption("Ping Pong ! Client")
        gameOver = False

        player = Player(self.screen)
        competitor = Competitor(self.screen)

        BLACK = (0, 0, 0)
        TOP, BOTTOM = 0, self.HEIGHT
        while not gameOver:
            self.screen.fill(BLACK)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    gameOver = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        gameOver = True

            moving = pygame.key.get_pressed()
            if moving[pygame.K_w] or moving[pygame.K_a] or moving[pygame.K_UP] or moving[pygame.K_RIGHT]:
                player.location[1] -= player.speed
            elif moving[pygame.K_s] or moving[pygame.K_d] or moving[pygame.K_DOWN] or moving[pygame.K_LEFT]:
                player.location[1] += player.speed

            if player.location[1] <= TOP:
                player.location[1] = TOP
            elif player.location[1] >= BOTTOM - player.HEIGHT:
                player.location[1] = BOTTOM - player.HEIGHT

            # server
            if client:
                handling = threading.Thread(target=competitor.handlingRequest, args=(client, ))
                sending = threading.Thread(target=player.sendingRequest, args=(client, ))

                handling.start()
                sending.start()
            # client
            else:
                handling = threading.Thread(target=competitor.handlingRequest, args=(host,))
                sending = threading.Thread(target=player.sendingRequest, args=(host,))

                handling.start()
                sending.start()

            player.render()
            competitor.render()

            frame.tick(FPS)
            pygame.display.update()


if __name__ == "__main__":
    PingPong().start()
