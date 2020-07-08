import copy
import pickle

from plug_interface import *
from language_server import *
from tkinter import *
import threading


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
            print("We have a winner: ",['O','X'][not(source[9])])
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

    def __init__(self, tr, canvas):
        self.tr = tr
        self.canvas = canvas
        self.l = []
        self.canvas.create_rectangle(0, 0, 600, 600, fill='yellow')
        for i in range(0, 600 - 600 // 3, 600 // 3):
            self.canvas.create_line(i + 600 / 3, 0, i + 600 / 3, 600, width=5)
            self.canvas.create_line(0, i + 600 / 3, 600, i + 600 / 3, width=5)

        self.projection(self.tr.initial_configurations()[0])


    def projection(self,source):
        self.projection_configuration(source)
        self.projection_action(source)
        return self.tr.fireable_transitions_from(source)
        return self.tr.fireable_transitions_from(source)

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
        for item in self.l:
            self.canvas.delete(item)

        def draw(idx,x,y):
            c = 80
            if idx == 1:
                self.l.append(self.canvas.create_line(x - c, y - c, x + c, y + c, width=5, fill='blue'))
                self.l.append(self.canvas.create_line(x - c, y + c, x + c, y - c, width=5, fill='blue'))
            elif idx == 0:
                self.l.append(self.canvas.create_oval(x - c, y - c, x + c, y + c, width=5, outline='red'))

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

    def fireable_transitions(self,source):
        actions = self.tr.fireable_transitions_from(source)

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


class Tree(object):
    def __init__(self,root,transitions,children):
        self.root = root
        self.children = children
        self.data = None

    def print_tree_action(self,n):
        r = "[GEN "+str(n)+"]"+str(self.root)+"("+str(self.data)+")"

        for child in self.children:
            r += '\n'+str(n*'  ')+' -> '
            r += str(child.print_tree_action(n+1))
        return r

    def print_tree(self):
        return self.print_tree_action(0)


    def minimax_action(self,depth,maxPlayer):
        return

    def minimax(self,depth):
        return self.minimax_action(depth,True)


class TicTacToeTree(AbstractTransitionRelation):

    def __init__(self, tr, depth):
        self.tr = tr
        self.depth = depth

    @synchronized # protege la fonction contre des appeles concurrents
    def initial_configurations(self):
        return self.tr.initial_configurations()

    @synchronized
    def fireable_transitions_from(self, source):
        t = self.create_tree(source, self.depth)
        print(t.print_tree())
        return self.tr.fireable_transitions_from(source)

    # executer
    @synchronized
    def fire_one_transition(self, source, transition):
        return self.ui.fire_one_transition(source,transition)

    def create_tree(self,source,n):
        root = source
        actions = self.tr.fireable_transitions_from(source)

        children = []
        target = []
        transition_list = []

        if n:
            for action in actions:
            #transition_list = source[0:(action[1])]+[1-action[0]]+source[(action[1]+1):len(source)]
                target = self.tr.fire_one_transition(source,action)[0][0]
                transition_list.append(action)
                children.append(self.create_tree(target,n-1))

        t = Tree(root,transition_list,children)

        if n == 0:
            winning = self.tr.detect_win(source,source[-1])
            print(winning,source[-1])
            if winning and source[-1] == 1:
                t.data = 1
            elif winning:
                t.data = -1
            else:
                t.data = 0

        return t


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

    def go(canvas):
        #server(lambda :create_game(canvas))

        game = create_game(canvas)

    threading.Thread(target=lambda:go(canvas)).start()

    mainloop()