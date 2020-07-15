import copy
import pickle

from plug_interface import *
from language_server import *
from tkinter import *
import threading
from time import sleep

# nécessaire pour pouvoir executer plusieurs analyses en parallel sur le meme run python
def synchronized(func):
    func.__lock__ = threading.Lock()

    def synced_func(*args, **kws):
        with func.__lock__:
            return func(*args, **kws)

    return synced_func


# regles du jeu
class TicTacToeTransitionRelation(AbstractTransitionRelation):

    def __init__(self, soup):
        self.soup = soup

    @synchronized # protege la fonction contre des appeles concurrents
    def initial_configurations(self):
        return [[-1] * (9) + [1]]

    @synchronized
    def fireable_transitions_from(self, source):
        # not(source[9])
        # actions : ensemble des actions possibles a partir de source    , [ tour , indice ]

        actions = []

        if source[9] == 0:
            tour = 1
            for i in range(0, 9):
                if source[i] == -1:
                    actions.append([tour, i])
        else:
            tour = 0
            for i in range(0, 9):
                if source[i] == -1:
                    actions.append([tour, i])

        return actions

    # executer
    @synchronized
    def fire_one_transition(self, source, transition):

        target = copy.deepcopy(source)
        target[9] = transition[0]
        target[transition[1]] = source[9]

        return [[target], None]

class TicTacToeEndGame(AbstractTransitionRelation):

    def __init__(self, TR):
        self.tr = TR


    @synchronized # protege la fonction contre des appeles concurrents
    def initial_configurations(self):
        return self.tr.initial_configurations()

    def detect_win(self,game_list,symbol):
        win = False
        tmp_list = []
        for i in range(0, 3):
            tmp_list.append(game_list[i * (3 + 1)])
        #
        # "Diagonale",tmp_list,win,i)
        win = all(elt == symbol for elt in tmp_list)
        if win == True:
            return win

        tmp_list = []
        for i in range(0, 3):
            tmp_list.append(game_list[(i + 1) * (3 - 1)])
        # print("Anti diagonale",tmp_list,win,i)
        win = all(elt == symbol for elt in tmp_list)
        if win == True:
            return win

        for i in range(0, 3):

            tmp_list = []
            for j in range(0, 3 ** 2, 3):
                tmp_list.append(game_list[i + j])
            win = all(elt == symbol for elt in tmp_list)
            #	print("colonnes",tmp_list,win,i)
            if win == True:
                return win

        tmp_list = []
        for i in range(0, 3 ** 2):

            tmp_list.append(game_list[i])
            if i % 3 == 3 - 1 and i > 0:
                win = all(elt == symbol for elt in tmp_list)
                tmp_list = []
            #	print("lignes",tmp_list,win,i)
            if win == True:
                return win
        return win

    @synchronized
    def fireable_transitions_from(self, source):

        if self.detect_win(source, not(source[9]) ) :
            return []

        return self.tr.fireable_transitions_from(source)

    # executer
    @synchronized
    def fire_one_transition(self, source, transition):

        return self.tr.fire_one_transition(source,transition)


class TicTacToeRuntimeView(AbstractRuntimeView):

    def __init__(self, soup):
        self.soup = soup


    # affichage
    def create_configuration_item(self, type_, name, icon=None, children=[]):

        result = {}
        result['type'] = type_
        result['name'] = name
        result['icon'] = icon
        result['children'] = children
        return result

    @synchronized
    def configuration_items(self, configuration) -> list:
        tableau = ""
        for i in range(0, 9):
            if i != 0 and (i % 3) == 0:
                tableau += "\n"
            tableau += str(configuration[i])

        items = [
            self.create_configuration_item("none", "tour=" + ("X", "O")[configuration[9]==0]),
            self.create_configuration_item("none", tableau)]
        return items

    @synchronized
    def fireable_transition_description(self, action) -> str:
        return "Tour: " + str([1,0][action[0]]) + ' Position: ' + str(action[1])


class TicTacToeProjection(object):

    def __init__(self, rules, canvas):
        self.tr = rules
        self.canvas = canvas
        self.canvas_items = []
        self.widget_items = []
        self.canvas.create_rectangle(0, 0, 600, 600, fill='yellow')
        for i in range(0, 600 - 600 // 3, 600 // 3):
            self.canvas.create_line(i + 600 / 3, 0, i + 600 / 3, 600, width=5)
            self.canvas.create_line(0, i + 600 / 3, 600, i + 600 / 3, width=5)

        self.projection(self.tr.initial_configurations()[0])


    def projection(self,source):

        self.projection_configuration(source)

        if source[-1] == 1:
            target = self.tr.fire_one_transition(source,self.best_move(source))[0][0]
            self.projection(target)
        else:

            self.projection_action(source)
            self.action_buttons(source)

        #return self.tr.fireable_transitions_from(source)


    def projection_action(self,configuration):
        def callback(event):
            x, y = event.x//200, event.y//200
            #print(configuration,[configuration[9],x+3*y])
            target = configuration
            if configuration[x+3*y] == -1 and not(self.tr.detect_win(configuration,1)) and not(self.tr.detect_win(configuration,0)):
                tour = [1,0][configuration[-1]]
                action = [tour,x+3*y]
                target = self.tr.fire_one_transition(configuration, action)[0][0]
            self.projection(target)

        self.canvas.bind("<Button-1>",callback)

    def projection_configuration(self, configuration):
        for item in self.canvas_items:
            self.canvas.delete(item)

        def draw(idx,x,y):
            c = 80
            if idx == 1:
                self.canvas_items.append(self.canvas.create_line(x - c, y - c, x + c, y + c, width=5, fill='blue'))
                self.canvas_items.append(self.canvas.create_line(x - c, y + c, x + c, y - c, width=5, fill='blue'))
            elif idx == 0:
                self.canvas_items.append(self.canvas.create_oval(x - c, y - c, x + c, y + c, width=5, outline='red'))

        def list_to_text(li):
            r = ''
            for i in range(0,len(li)-1):
                r += str(configuration[i]) + ' '
                if (i+1)%3 == 0 :
                    r+='\n'
            return r

        c = 200

        for i in range(0, len(configuration)):
            draw(configuration[i], (i % 3 + 1) * c - c / 2, (i // 3 + 1) * c - c / 2)

        self.canvas.update()

    def action_buttons(self,source):

        for item in self.widget_items:
            item.destroy()
        actions = self.tr.fireable_transitions_from(source)
        y = 0
        idx = 0
        for action in actions:

            button = Button(self.canvas,text=str(['X','O'][action[0]])+" dans "+str(action[1]),command=lambda info=[source,action]: self.fire_one_transition(info[0],info[1]))
            self.widget_items.append(button)
            button.configure(width=20, background= '#DDD',activebackground="#33B5E5", relief=FLAT)
            button = self.canvas.create_window(650, y, anchor=NW, window=button)

            y += 30
            idx += 1

    def fire_one_transition(self,source,action):
        target = self.tr.fire_one_transition(source,action)[0][0]
        if self.tr.detect_win(source,[1,0][source[-1]]) == False:
            self.projection(target)

    def best_move(self,source):
        actions = self.tr.fireable_transitions_from(source)
        targets = [self.tr.fire_one_transition(source, action)[0][0] for action in actions]

        board = source
        best_score = -2
        move = [1-source[-1],0]
        for i in range(0,9):
            if board[i] == -1:
                board[i] = 1
                score = Algorithms(self.tr).minimax(board,8,False)
                board[i] = -1
                if score > best_score:
                    best_score = score
                    move[1] = i
        return move


class Algorithms(object):
    def __init__(self,tr):
        self.tr = tr

    def minimax(self,source,depth,max_player):
        if self.tr.detect_win(source,1):
            return 1
        elif self.tr.detect_win(source,0):
            return -1
        elif depth == 0:
            return 0

        board = source
        if max_player:
            best_score = -2
            for i in range(0,9):
                if board[i] == -1:

                    board[i] = 1
                    score = self.minimax(board,depth-1,False)
                    board[i] = -1
                    if score > best_score:
                        best_score = score
            return best_score
        else:
            best_score = 2
            for i in range(0, 9):
                if board[i] == -1:
                    board[i] = 0
                    score = self.minimax(board, depth - 1, True)
                    board[i] = -1
                    if score < best_score:
                        best_score = score
            return best_score

class TicTacToeMarshaller(AbstractMarshaller):

    def __init__(self, soup):
        self.soup = soup

    def serialize_configuration(self, configuration) -> bytearray:
        return pickle.dumps(configuration)

    def deserialize_configuration(self, bytes):
        return pickle.loads(bytes)

    def serialize_transition(self, transition) -> bytearray:
        return pickle.dumps(transition)

    def deserialize_transition(self, bytes):
        return pickle.loads(bytes)

    def serialize_payload(self, payload) -> bytearray:
        return pickle.dumps(payload)

    def deserialize_payload(self, bytes):
        return pickle.loads(bytes)


class TicTacToeAtomEvaluator(AbstractAtomEvaluator):
    def __init__(self, soup):
        self.soup = soup

    @synchronized
    def register_atomic_propositions(self, propositions) -> list:
        result = []
        self.propositions = propositions
        for ap in propositions:
            result.append(len(result))
        return result

    @synchronized
    def atomic_proposition_valuations(self, configuration) -> list:
        result = []
        for ap in self.propositions:
            result.append(False)
        return result

    @synchronized
    def extended_atomic_proposition_valuations(self, source, transitionID, payload, target) -> list:
        result = []
        for ap in self.propositions:
            result.append(False)
        return result


def create_game(canvas):
    soup = None

    rules = TicTacToeEndGame(TicTacToeTransitionRelation(soup))
    projection = TicTacToeProjection(rules,canvas)

    return projection

  #  return LanguageModule(
  #      projection,
  #      TicTacToeRuntimeView(soup),
  #      TicTacToeAtomEvaluator(soup),
  #      TicTacToeMarshaller(soup)
  #  )


if __name__ == "__main__":
    root = Tk()
    canvas = Canvas(root, width=1200, height=600)
    canvas.pack()

    def go(anvas):
        #server(lambda :create_game(canvas))

        game = create_game(canvas)

    threading.Thread(target=lambda:go(canvas)).start()

    mainloop()