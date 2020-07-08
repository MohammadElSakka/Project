from abc import abstractmethod


class AbstractTransitionRelation:
    module: object

    @abstractmethod
    def initial_configurations(self) -> set:
        pass

    @abstractmethod
    def fireable_transitions_from(self, source) -> set:
        pass

    @abstractmethod
    def fire_one_transition(self, source, transition) -> set:
        pass


class AbstractRuntimeView:
    module: object

    @abstractmethod
    def configuration_items(self, configuration) -> list:
        pass

    @abstractmethod
    def fireable_transition_description(self, transition) -> str:
        pass


class AbstractAtomEvaluator:
    module: object

    @abstractmethod
    def register_atomic_propositions(self, propositions) -> list:
        pass

    @abstractmethod
    def atomic_proposition_valuations(self, configuration) -> list:
        pass

    @abstractmethod
    def extended_atomic_proposition_valuations(self, source, transition, payload, target) -> list:
        pass


class AbstractMarshaller:
    module: object

    @abstractmethod
    def serialize_configuration(self, configuration) -> bytearray:
        pass

    @abstractmethod
    def deserialize_configuration(self, bytes):
        pass

    @abstractmethod
    def serialize_transition(self, transition) -> bytearray:
        pass

    @abstractmethod
    def deserialize_transition(self, bytes):
        pass

    @abstractmethod
    def serialize_payload(self, payload) -> bytearray:
        pass

    @abstractmethod
    def deserialize_payload(self, bytes):
        pass


class LanguageModule:
    transition_relation: AbstractTransitionRelation
    runtime_view: AbstractRuntimeView
    atom_evaluator: AbstractAtomEvaluator
    marshaller: AbstractMarshaller

    def __init__(self, transition_relation = None, runtime_view = None, atom_evaluator = None, marshaller = None):
        self.transition_relation = transition_relation
        if transition_relation != None :
            self.transition_relation.module = self
        self.runtime_view = runtime_view
        if runtime_view != None :
            self.runtime_view.module = self
        self.atom_evaluator = atom_evaluator
        if atom_evaluator != None :
            self.atom_evaluator.module = self
        self.marshaller = marshaller
        if marshaller != None :
            self.marshaller.module = self
     
