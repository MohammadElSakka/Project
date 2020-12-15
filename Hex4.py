from tkinter import *
from math import *
from time import *
import random
import threading

class Hex(object):

    def __init__(self,size,canvas):
        self.size = size
        self.canvas = canvas
        self.hexagons = []
        self.initial = 0
        self.blue_win = 0

    def draw_hexagon(self,x,y,r,bg):
        coordinates = []
        for i in range(6):
            coordinates.append(x+r*cos(i*pi/3))
            coordinates.append(y+r*sin(i*pi/3))

        return self.canvas.create_polygon(
            coordinates,
            fill=bg,
            outline = 'black'
        )

    def hex_grid(self,canvas_w,canvas_h,r):


        w,h = canvas_w/2-r*self.size, canvas_h/2-r*self.size/2

        self.canvas.create_rectangle(
            w - r / 2, h - sqrt(3) * r / 2,
            w - r, h + 2 * self.size * sqrt(3) * r / 2 - sqrt(3) * r / 2,
            fill='red',
            outline=""
        )

        self.canvas.create_polygon(
            w - r / 2, h - sqrt(3) * r / 2,
            w + 3 * r / 2, h - sqrt(3) * r / 2,
            w + self.size * 3 * r / 2 - sqrt(3) * r / 2, h - self.size * sqrt(3) * r / 2,
            w + self.size * 3 * r / 2 - 2 * r, h - self.size * sqrt(3) * r / 2,
            fill='blue'
        )

        self.canvas.create_rectangle(
            w + (self.size / 2) * 2 * r + (2*self.size-1) * r / 4 - r / 2,
            h - self.size * sqrt(3) * r / 2,
            w + (self.size / 2) * 2 * r + (2*self.size-1) * r / 4,
            h + self.size * sqrt(3) * r / 2,
            fill='red',
            outline=""
        )

        self.canvas.create_polygon(
            w - r / 2,
            2*self.size*sqrt(3)*r/2 + h - sqrt(3) * r / 2,
            w + 3 * r / 2,
            2*self.size*sqrt(3)*r/2 + h - sqrt(3) * r / 2,
            w + self.size * 3 * r / 2 - sqrt(3) * r / 2,
            2*self.size*sqrt(3)*r/2 + h - self.size * sqrt(3) * r / 2,
            w + self.size * 3 * r / 2 - 2 * r,
            2*self.size*sqrt(3)*r/2 + h - self.size * sqrt(3) * r / 2,
            fill='blue'
        )


        self.hexagons = []
        for i in range(0,self.size):
            h2 = h
            w2 = w
            for j in range(0,self.size):
                self.hexagons.append(self.draw_hexagon(w2,h2,r,'White'))
                w2 += 3*r/2+1
                h2 -= sqrt(3)*r/2
            h += sqrt(3)*r

    def hex_create_graph(self):
        self.nodes = [0 for j in range(self.size**2)]
        self.edges = {}

        self.nodes.append(1)
        self.nodes.append(1)
        self.nodes.append(-1)
        self.nodes.append(-1)

        for i in range(self.size**2+4):
            self.edges[i] = []




        for i in range(self.size**2):
            if i - 1 >= 0 and i % self.size != 0:
               self.edges[i].append(i - 1)

            if i + 1 < self.size ** 2 and (i + 1) % self.size != 0:
               self.edges[i].append(i + 1)

            if i - self.size >= 0:
               self.edges[i].append(i - self.size)

            if i + self.size < self.size ** 2:
               self.edges[i].append(i + self.size)

            if i - self.size - 1 >= 0 and i % self.size != 0:
               self.edges[i].append(i - self.size - 1)

            if i + self.size + 1 < self.size ** 2 and (i + self.size + 1) % self.size != 0:
               self.edges[i].append(i + self.size + 1)



        for i in range(self.size):
            self.edges[self.size**2].append(i)
            self.edges[i].append(self.size**2)

            self.edges[self.size**2+1].append(self.size ** 2 - 1 - i)
            self.edges[self.size ** 2 - 1 - i].append(self.size**2+1)

            self.edges[self.size**2+2].append(i * self.size)
            self.edges[i * self.size].append(self.size**2+2)

            self.edges[self.size**2+3].append(self.size - 1 + self.size * i)
            self.edges[self.size - 1 + self.size * i].append(self.size**2+3)

    def launch(self):
        self.hex_grid(750, 750, 25)
        self.hex_create_graph()

        self.turn = 1

        def f(i):
            if self.finish == False:
                if self.turn == -1:
                    if self.nodes[i-5] == 0:
                        self.nodes[i-5] = self.turn
                        self.canvas.itemconfig(i,fill=['White','Blue','Red'][self.nodes[i-5]])
                        self.turn*=-1
                        if self.DFS_win(self.size**2+2):
                            print("winner: ",['','Blue','Red'][self.nodes[i-5]])
                            self.finish = True

        self.finish = False

        # move = self.initial
        # self.nodes[move] = 1
        # self.turn *= -1
        # self.canvas.itemconfig(move + 5, fill='blue')

        while True:
            eval = lambda x: (lambda p: f(x))
            for hex in self.hexagons:

                if self.finish:
                    if self.initial < self.size**2:
                        self.initial += 1
                    return
                if self.turn == 1:
                    move = self.get_best_move_pc()
                    self.nodes[move] = 1
                    self.turn *= -1
                    self.canvas.itemconfig(move+5,fill='blue')
                    sleep(0.5)

                    if self.DFS_win(self.size**2):
                        print("winner: Blue")
                        self.finish = True
                        self.blue_win += 1
                # elif self.turn == -1:
                #     move = self.get_best_move_player()
                #     self.nodes[move] = -1
                #     self.turn *= -1
                #     self.canvas.itemconfig(move + 5, fill='red')
                #     sleep(0.5)
                #
                #     if self.DFS_win(self.size ** 2 + 2):
                #         print("winner: Red")
                #         self.finish = True
                self.canvas.tag_bind(hex,"<Button-1>",eval(hex))

    def DFS_win(self,node):

        visit = [False]*(self.size**2+4)
        stack = [node]

        while len(stack):

            v = stack.pop(-1)


            if visit[v] == False:

                visit[v] = True
                if self.nodes[v] == self.nodes[node]:

                    if v >= self.size**2 and v != node:
                        return True
                    for child in self.edges[v]:
                        if self.nodes[child] == self.nodes[node]:
                            stack.append(child)
        return False

    def SPFA(self,source,destination):

        distance = [inf]*(self.size**2+4)
        path = [None]*(self.size**2+4)

        distance[source] = 0
        path[source] = source

        q = []
        q.append(source)

        while len(q):
            u = q.pop(0)
            if u == destination:
                break

            for child in self.edges[u]:
                if self.nodes[child] == 0 or self.nodes[child] == self.nodes[source]:
                    extra = 1 if self.nodes[child] == 0 else 0
                    if distance[u] + extra < distance[child]:
                        distance[child] = distance[u] + extra
                        path[child] = u
                        if child not in q:
                            q.append(child)

        paths = [destination]
        v = destination

        while v!= source:
            v = path[v]
            paths.append(v)

        paths.append(source)

        return paths

    def get_pc_shortest_path_spfa(self):
        if self.finish:
            return
        path = self.SPFA(self.size**2, self.size**2+1)

        return path

    def get_player_shortest_path_spfa(self):
        if self.finish:
            return
        return self.SPFA(self.size**2+2, self.size**2+3)

    def get_heuristic_score(self):
        pc_path = self.get_pc_shortest_path_spfa()
        player_path = self.get_player_shortest_path_spfa()

        def path_to_score(path):

            cnt = 0
            for node in path:
                if self.nodes[node] == 0:
                    cnt += 1
            return cnt

        pc_score = path_to_score(pc_path)
        player_score = path_to_score(player_path)

        return player_score-pc_score

    def get_best_move_pc(self):
        move = 0
        best_score = -inf

        for node in range(self.size**2):
            if self.nodes[node] == 0 :
                self.nodes[node] = 1
                score = self.minimax(node,4,-inf,+inf,False)

                self.nodes[node] = 0

                if score >= best_score:
                    move = node

                best_score = max(score,best_score)

        #self.canvas.itemconfig(move+5,fill='green')
        return move

    def get_best_move_player(self):
        move = 0
        best_score = inf

        for node in range(self.size ** 2):
            if self.nodes[node] == 0:
                self.nodes[node] = -1
                score = self.minimax(node, 6, -inf, +inf, True)

                self.nodes[node] = 0

                if score <= best_score:
                    move = node

                best_score = min(score, best_score)

        #self.canvas.itemconfig(move + 5, fill='green')
        return move

    def minimax(self,node,depth,alpha,beta,max_player):

        if self.DFS_win(self.size**2):
                return inf
        elif self.DFS_win(self.size**2+2):
                return -inf
        if depth == 0:
            return self.get_heuristic_score()

        if max_player:
            best_score = -inf
            for node in range(self.size**2):
                if self.nodes[node] == 0:
                    self.nodes[node] = 1

                    score = self.minimax(node,depth-1,alpha,beta,False)
                    best_score = max(score,best_score)

                    self.nodes[node] = 0
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break

            return best_score
        else:
            best_score = inf
            for node in range(self.size**2):
                if self.nodes[node] == 0:
                    self.nodes[node] = -1
                    score = self.minimax(node,depth - 1, alpha, beta, True)

                    best_score = min(score, best_score)
                    beta = min(score,beta)
                    self.nodes[node] = 0
                    if beta <= alpha:
                        break

            return best_score

    # def play(self):
    #     self.hex_grid(750,750,25)
    #     for i in range(self.size**2):
    #         self.hex_create_graph()
    #         for h in self.hexagons:
    #             self.canvas.itemconfig(h,fill='white')
    #         self.launch()
    #
    #     print(self.blue_win)
if __name__ == '__main__':

    root = Tk()
    canvas = Canvas(root,width=750,height=750)
    canvas.pack()

    size = 4

    threading.Thread(target=lambda:Hex(size,canvas).launch()).start()


    mainloop()