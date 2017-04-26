"""
	A Trie based runtime for EL
"""
import logging as root_logger
logging = root_logger.getLogger(__name__)

from enum import Enum
from collections import namedtuple
from fractions import Fraction
from random import choice
from uuid import UUID
import IPython
import uuid
from .ELUtil import EL, ELEXT, ELCOMP
from .ELBinding import ELBindingStack, ELBindingFrame
from .ELTrieNode import ELTrieNode
from .ELResults import ELFail, ELSuccess
from .ELActions import ELBIND
from .ELStructure import ELVAR
from .ELFactStructure import ELFACT, ELARITH_FACT
from .ELFunctions import COMP_FUNCS, get_EL_FUNC
from . import ELParser, ELTrie
from . import ELExceptions as ELE


class ELRuntime:
    """ The Unified EL Runtime,
    Parses strings into IRs, which are acted upon.
    """

    def __init__(self):
        self.parser = ELParser.ELPARSE
        self.trie = ELTrie.ELTrie()
        #list of tuples (asserted, retracted) for each action?
        self.history = []
        #bindings :: stack<ELBindingFrame>
        self.bindings = ELBindingStack()

        #todo: add default type structures


        
    def __call__(self,string):
        """ Parse a string, act accordingly with the results """
        parsed_representations = self.parser(string)
        #todo: return a {status: bool, data: [] } obj
        actResults = []
        for r in parsed_representations:
            actResults.append(self.act(r))
            
        if len(actResults) == 0:
            return None
        if len(actResults) == 1:
            return actResults[0]
        else:
            return actResults

    
    def push_stack(self): #Binding state operations:
        self.bindings.push_stack()

    def replace_stack(self,frame):
        self.bindings[-1] = frame

    def top_stack(self):
        return self.bindings.top()
        
    def pop_stack(self):
        self.bindings.pop()


    def run(self): #Simulation functions:
        """ run the simulation """
        None

    def execute(self, data, etype=ELEXT.TRIE):
        if isinstance(etype, str):
            try:
                etype = ELEXT[etype]
            except KeyError as e:
                logging.warning('Unrecognised Execution Enum: {}'.format(etype))
                etype = ELEXT.TRIE
        logging.info('Executing {} from {}'.format(etype, data))
        return_val = []
        if etype is ELEXT.TRIE:
            return_val = self.execute_as_trie(data)
        elif etype is ELEXT.TREE:
            None
        elif etype is ELEXT.FSM:
            None
        elif etype is ELEXT.SEL:
            None
        elif etype is ELEXT.INS:
            None
        else:
            raise ELE.ELNotImplementedException()

        return return_val

    def execute_as_trie(self, data, MAX_STEPS=100):
        """
        data :: string -> ELFACT
        Assumes structure where each node has a 'next' child,
        .node.next.[...],
        .node.preconditions.[]
        .node.condition_action_pairs.[]
        .node.actions.[]
        .node.performance."blah"
        .node.weight!n
        .node.rules...
        ....
        """
        self.push_stack()
        output = []
        steps = 0
        #state :: ELBindingFrame
        state = self.top_stack()
        #data:: string, current::ELTrieNode
        current = self.get_location(data)[0]
        assert current is not None
        
        while 'next' in current and \
              len(current['next']) > 0 and \
              steps < MAX_STEPS:
            steps += 1
            #current::ELTrieNode, state::ELBindingFrame
            #n_node::ELTrieNode
            #u_state::ELBindingFrame
            #o_text::String
            n_node, u_state, o_text = self.perform_node(current, state)
            current = n_node
            state = u_state
            output.append(o_text)
            
        #perform the final leaf
        n_node, u_state, o_text = self.perform_node(current, state)
        output.append(o_text)
        
        self.pop_stack()
        return output

    #node :: ELTrieNode, state :: ELBindingFrame
    def perform_node(self, node, state):
        #todo: verify the structure of the node:
        
        #run conditions
        if 'conditions' in node:
            #conditions_result :: ELResult
            #initial_bindings :: ELBindingFrame
            conditions_result = self.run_conditions(node['conditions'],
                                                   bindings=state)
            if isinstance(conditions_result, ELFail):
                return (None, None, None)
            initial_bindings = conditions_result.bindings
        else:
            initial_bindings = state
        #run comparisons
        if 'comparisons' in node:
            compared_bindings = self.run_comparisons(node['comparisons'],
                                                     initial_bindings)
        else:
            compared_bindings = initial_bindings

        if len(compared_bindings) == 0:
            return (None, None, None)
            
        compared_bindings.select()
        #run arithmetic actions
        if 'arithmetic' in node:
            updated_bindings = self.run_arithmetic(node['arithmetic'],
                                                  compared_bindings)
        else:
            updated_bindings = compared_bindings
        #run general actions
        if 'actions' in node:
            self.run_actions(node['actions'], updated_bindings)
        
        #Get the output of the node
        if 'output' in node:
            interp_text = self.run_output(node['output'], updated_bindings)
        else:
            interp_text = "N/A"
        
        #Get the next node:
        if 'next' in node:
            next_location = self.next_node(node['next'], updated_bindings)
        else:
            next_location = None

        #ELBindingSlice -> ELBindingFrame
        binding_frame = ELBindingFrame([updated_bindings.get_selected()])

        #next_loc::ELTrieNode,
        #binding_frame::ELBindingFrame
        #interp_text::String
        return (next_location, binding_frame, interp_text)

    
    def get_location(self,location):
        # ELFact -> ELBindingFrame -> [ELTrieNode]
        """ Utility to get a trie node based on string, fact, uuid, or trie node """
        if isinstance(location, ELTrieNode):
            return [location]
        elif isinstance(location, UUID):
            return [self.trie[location]]
        elif isinstance(location, str): #str -> ELFACT
            location = self.parser(location)[0]
        elif not isinstance(location, ELFACT): #UNKNONW
            raise ELE.ELConsistencyException("Unrecognised value passed to get_location: {}".format(location))

        if not location.is_query():
            location = location.query()
                     
        #location :: ELFACT
        queried = self.fact_query(location)
        assert isinstance(queried, ELSuccess)
        targets = [self.trie[x] for x in queried.nodes]
        return targets

    #location::ELTrieNode
    #binding::ELBindingSlice
    def next_node(self, location, bindings=None):
        #makes no sense to have multiple targets, so get just the first
        if bindings is None:
            bindings = self.top_stack()
            bindings.select()
        
        target = self.get_location(location)[0]
        potentials = [self.fact_query(x, bindings).nodes[0] for x in target.to_el_queries()]
        chosen = choice(potentials)
        node = self.trie[chosen]
        #node :: ELTrieNode
        return node

    def run_actions(self, location, bindings=None):
        logging.info("Running Actions: {}".format(location))
        if bindings is None:
            bindings = self.top_stack()
        #only a single target:
        target = self.get_location(location)[0]
        actions = target.to_el_facts()
        for action in actions:
            if action.has_forall_binding:
                for binding in bindings:
                    self.__run_action(action, binding)
            else:
                self.__run_action(action, bindings.get_selected())

    def __run_action(self, action, binding):
        bound = action.bind_slice(binding)
        if bound.negated:
            self.fact_retract(bound)
        else:
            self.fact_assert(bound)
            
    def run_output(self, location, bindings=None):
        if bindings is None:
            bindings = self.top_stack()
            bindings.select()
        target = self.get_location(location)[0]
        potentials = target.children_values()
        chosen = choice(potentials)
        #bind variables in the string:
        interpolated = self.interpolate_string(chosen, bindings.get_selected())
        return interpolated

    def interpolate_string(self, string, binding):
        try:
            dict_binding = {x: y.value for x,y in binding.items()}
            return string.format_map(dict_binding)
        except KeyError as e:
            logging.warning("Interpolating String: {}".format(string))
            logging.warning("No Key Found in binding: {}".format(binding))
            logging.warning("Missing Key: {}".format(e.args[0]))
            return string

    
    def run_arithmetic(self, location, bindings=None):
        logging.info("Running Arithmetic: {}".format(location))
        target = self.get_location(location)[0]
        actions = target.to_el_function_formatted(comp=False)

        all_bindings = bindings.copy()
        for arith_action in actions:
            if arith_action[-1]: #is forall scoped
                #run arith for all binding slices
                all_bindings = ELBindingFrame([self.__run_arith(arith_action,
                                                                binding) for binding in all_bindings])
            else:
                all_bindings[all_bindings.selected] = self.__run_arith(arith_action, all_bindings.get_selected())
        return all_bindings
        
    def __run_arith(self, arith_action, binding):
        binding = binding.copy()
        operator, p1, p2, near, forall_scoped = arith_action
        if p1.value not in binding or (isinstance(p2, ELVAR) and p2.value not in binding):
            raise ELE.ELConsistencyException('Arithmetic being run without the necessary bindings')

        if p1.is_path_var:
            node = self.trie[p1.get_val(binding)]
            val1 = node.value
        else:
            val1 = p1.get_val(binding)
            
        if isinstance(p2, ELVAR):
            val2 = p2.get_val(binding)
        else:
            val2 = p2

        result = operator(val1, val2)

        if p1.is_path_var:
            node.update_value(result)
        binding[p1.value].value = result
        return binding
    
    def run_conditions(self, location, bindings=None):
        # ELFact -> ELBindingFrame -> ELResult
        logging.info("Running Conditions: {}".format(location))
        if bindings is None:
            bindings = self.top_stack()
        target = self.get_location(location)[0]
        conditions = target.to_el_queries()
        #Run the conditions in sequence:
        for condition in conditions:
            result = self.fact_query(condition, bindings)
            if not bool(result):
                return ELFail() #EARLY RETURN
            bindings = result.bindings
        #Gotten to where all conditions pass, return the bindings:
        return ELSuccess(None, result.bindings)

    def run_comparisons(self, location, bindings):
        target = self.get_location(location)[0]
        #comparisons :: ( operator, p1, p2, near)
        comparisons = target.to_el_function_formatted()
        
        for comparison in comparisons:
            bindings = ELBindingFrame([slice for slice in bindings if self.__run_comparison(comparison, slice)])
        
        return bindings


    def __run_comparison(self, comparison, binding):
        operator, p1, p2, near, forall_scoped = comparison
        if p1.value not in binding or (isinstance(p2, ELVAR) and p2.value not in binding):
            raise ELE.ELConsistencyException('Comparison being run without the necessary bindings')

        if p1.is_path_var:
            node = p1.get_val(binding)
            val1 = self.trie[node]
        else:
            val1 = p1.get_val(binding)
            
        if isinstance(p2, ELVAR):
            val2 = p2.get_val(binding)
        else:
            val2 = p2
            
        if operator == COMP_FUNCS[ELCOMP.NEAR]:
            if isinstance(near, ELVAR):
                nearVal = near.get_val(binding)
            else:
                nearVal = near

            return operator(val1, nearVal, val2)
        else:
            return operator(val1, val2)


        
    def act(self,action): #Action functions:
        """ Given an action (one of ELBDs action types),
        perform it
        """
        #Store in the history
        self.history.append(action)
        
        result = ELFail()
        #Perform based on parsed type
        if isinstance(action, ELFACT):
            #Fact: Assert /retract
            if action.is_query():                       #QUERY
                #Don't replace vars with bindings, populate them
                logging.debug("Querying")
                self.push_stack()
                result = self.fact_query(action, self.top_stack())
                self.pop_stack()
                logging.debug('Query Result: {}'.format(result))
            elif action.negated:                                      #RETRACT
                logging.debug("Hit a negation, retracting")
                result = self.fact_retract(action) 
            else:                                                     #ASSERT
                logging.debug("Hit an assertion")
                result = self.fact_assert(action)
        elif isinstance(action, ELBIND):                              #BIND
            raise ELE.ELRuntimeException("Not Implemented")
            #self.set_binding(action.var,action.root)
        elif isinstance(action, ELARITH_FACT):                        #ARITH
            #Get the designated leaf.
            node = self.trie[action.data]
            result = action.apply(node)
        else:
            raise ELE.ELRuntimeException("Unrecognised Action: {}".format(action))
        return result


    def fact_assert(self,fact): #Fact operations:
        """ Add a fact """
        return_val = []
        expanded = fact.expand()
        for f in expanded:
            return_val.append(self.trie.push(f))
        return all(return_val)
            
    def fact_retract(self,fact):
        """ Remove a fact """
        return_val = []
        expanded = fact.expand()
        for f in expanded:
            return_val.append(self.trie.pop(fact))
        return all(return_val)
            
    def fact_query(self,query, bindingFrame=None, force_selection=False):
        """ Test a fact, BE CAREFUL IT MODIFES THE TOP OF THE VAR STACK  """
        # ELFact -> ELBindingFrame -> ELResult
        #todo: make sure it no longer modifies the top of the var stack
        logging.debug('Recieved Query: {}'.format(query))
        if bindingFrame is None:
            bindingFrame = self.top_stack()
        assert isinstance(bindingFrame, ELBindingFrame)
        assert query.is_query()
        assert not query.has_forall_binding() #not supported yet

        if force_selection:
            current_frame = ELBindingFrame([bindingFrame.get_selected().copy()])
        else:
            current_frame = bindingFrame
        if len(current_frame) == 0:
            logging.debug("Nothing in the current frame")
            return ELFail()
        #fill in any variables from the current bindings
        bound_queries = [query.bind_slice(slice) for slice in current_frame]
        logging.debug('Bound: {}'.format(bound_queries))
        
        #then query
        results = [self.trie.query(query) for query in bound_queries]
        logging.debug("Trie Query results: {}".format(results))
        
        #then integrate into bindings:
        successes = [success for success in results if bool(success) is True]
        logging.debug("Trie Query Successes: {}".format(successes))
        
        #Flatten the frame
        updated_frame = ELBindingFrame([bind_slice for success in successes for bind_slice in success.bindings])
        nodes = [x for success in successes for x in success.nodes]
        
        #a frame is valid if it has at least ELSuccess(none,{}) in it
        if len(updated_frame) > 0:
            return ELSuccess(path=query, bindings=updated_frame, nodes=nodes)
        else:
            return ELFail()


    #     if action.hasForAllBinding():
    #         bound_actions = [action.bind(selection, x) \
    #                          for x in compared_bindings]
    #         logging.debug("Bound actions: {}".format(bound_actions))
    #     else:
    #         bound_actions = [action.bind(selection)]
            
    #String Operations:
    def format_string(self,raw_string, bindings):
        """ Given a format_string, use defined variables in the runtime
        to fill it in """
        #todo: Take a string of "this is a $x test", and replace $x with the variable val
        return raw_string

    #### METRICS
    def max_depth(self):
        return self.trie.dfs_for_metrics()['maxDepth']

    def num_leaves(self):
        return len(self.trie.dfs_for_metrics()['leaves'])
        
    def num_assertions(self):
        return len([x for x in self.history if isinstance(x, ELFACT) and not x.negated])
        
    def num_retractions(self):
        return len([x for x in self.history if isinstance(x, ELFACT)  and x.negated])
        
        
    #EXPORTING
    def __str__(self):
        leaves = self.trie.dfs_for_metrics()['leaves']
        strings = [str(x) for x in leaves]
        return "\n".join(strings)
