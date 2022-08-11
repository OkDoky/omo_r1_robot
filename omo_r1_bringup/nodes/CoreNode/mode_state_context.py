#! /usr/bin/python

from abc import ABCMeta, abstractmethod

class ModeContext:
    """
    The Context defines the interfaces of interest to clients.
    It also maintains a reference to an instance of a State subclass,
    which represents the current state of the Context
    """
    
    _mode_state = None
    """
    A reference to the current state of the Context
    """
    
    def __init__(self, state):
        self.transition_to(state)
        
    def transition_to(self, state):
        """
        The ModeContext allows changing the State object at runtime

        Args:
            state (str): nav, slam, reset
        """
        print("[ModeContext] Transition to %s"%state.get_state_name())
        self._mode_state = state
        self._mode_state.context = self
        
        """
        The ModeContext delegates part of its behavior to the current State object.
        """
        
    def request_reset(self):
        self._mode_state.reset_current_mode()
        
    def request_switch(self):
        self._mode_state.transition_switch()
    
    def request_current_state_name(self):
        return self._mode_state.get_state_name()
            
            
class State():
    __metaclass__ = ABCMeta
    """
    The base State class declares methods that all Concrete State should
    implement and also provides a backreference to the ModeContext object,
    associated with the State. This backreference can be used by States to
    transition the Context to another State.
    """
    
    @property
    def context(self):
        return self._context
    
    @context.setter
    def context(self, context):
        self._context = context
        
    @abstractmethod
    def transition_switch(self):
        pass
    @abstractmethod
    def reset_current_mode(self):
        pass
    @abstractmethod
    def get_state_name(self):
        pass
    
"""
Concrete States implement various behaviors,
associated with a state of the Context.
"""
        
class ConcreteStateNav(State):
    def get_state_name(self):
        return "nav"
    def transition_switch(self):
        self.context.transition_to(ConcreteStateSlam())
    def reset_current_mode(self):
        pass
    
class ConcreteStateSlam(State):
    def get_state_name(self):
        return "slam"
    def transition_switch(self):
        self.context.transition_to(ConcreteStateNav())
    def reset_current_mode(self):
        pass