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
from .ELStructure import ELQUERY, ELVAR
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

    def execute(self, etype, data):
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

    def execute_as_trie(self, data):
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
        output = ["Start"]
        state = self.top_stack()
        #Parse, search, then get the exact node from the trie
        current = self.trie[self.fact_query(self.parser(data)[0]).nodes[0]]
        assert current is not None
        
        while len(current['next']) > 0:
            #verify the structure of the node:
            
            #perform the node
            success_value, state = self.perform_node(current, state)
            #get the text of the node
            text = current['text']
            #interpolate the text of the node with bindings
            interp_text = self.format_string(text.format, state)
            
            #add the text to the record
            output.append(interp_text)
            
            #pick the next node
            potential_children = current['next'].to_weighted_el_facts()
            next_location = choice(potential_children)
            current = self(next_location)
            

        #perform the final leaf

        self.pop_stack()
        return output

    def get_location(self,location, bindings=None):
        """ Utility to get a trie node based on string, fact, uuid, or trie node """
        if isinstance(location, ELTrieNode):
            return location
        elif isinstance(location, UUID):
            return self.trie[location]
        elif isinstance(location, str): #str -> ELFACT
            location = self.parser(location)[0]
        elif not isinstance(location, ELFACT): #UNKNONW
            raise ELE.ELConsistencyException("Unrecognised value passed to get_location: {}".format(location))

        #location :: ELFACT
        queried = self.fact_query(location, bindings)
        target = self.trie[queried.nodes[0]]
        return target

    def select_binding(self, bindings=None):
        if bindings is None:
            bindings = self.top_stack()
        return choice(bindings)
    
    def run_arithmetic(self, location, binding=None, bindings=None):
        logging.info("Running Arithmetic: {}".format(location))
        if binding is None:
            binding = self.select_binding(bindings)
        target = self.get_location(location, ELBindingFrame([binding]))
        actions = target.to_el_function_formatted(comp=False)
        #todo: verify bindings
        for arith_action in actions:
            binding = self.__run_arith(binding, arith_action)

        
    def __run_arith(self, binding, arith_action):
        operator, p1, p2, near = arith_action
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
        logging.info("Running Conditions: {}".format(location))
        if bindings is None:
            bindings = self.top_stack()
        target = self.get_location(location, bindings=bindings)
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
        target = self.get_location(location, bindings=bindings)
        #comparisons :: ( operator, p1, p2, near)
        comparisons = target.to_el_function_formatted()
        
        for comparison in comparisons:
            bindings = ELBindingFrame([slice for slice in bindings if self.__run_comparison(slice, comparison)])
        
        return bindings


    def __run_comparison(self, binding, comparison):
        operator, p1, p2, near = comparison
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





        
    
    def perform_node(self, target, state=None):
        """
        .node.next.[...],
        .node.conditions.[]
        .node.statemods...
        .node.performance."blah"
        .node.bindings.[] <- or is this implicit?
        .node.weight!n
        .node.rules...
        """
        logging.info("Perfoming node: {}".format(target))
        #SETUP:
        return_value = ELFail()
        if state is None:
            state = self.top_stack()
            
        internal_state = state.copy()

        if isinstance(target, ELTrieNode):
            target_node = target        
        elif isinstance(target, uuid.UUID):
            target_node = self.trie[target]
        else:
            parsed_target = self.parser(target)[0]
            #todo: make fact_query return the uuid of each possible leaf?
            target_node = self.trie[self.fact_query(parsed_target).nodes[0]]
        if 'conditions' not in target_node:
            raise ELE.ELConsistencyException("Performing a node without conditions")
        ###########
        #CONDITIONS:
        ###########
        conditions = [x.query() for x in target_node['conditions'].to_el_facts()]
        #run the conditions
        for cond in conditions:
            query_result = self.fact_query(cond, internal_state)
            #todo: go down state stack if conditions fail
            if bool(query_result) is not True:
                raise ELE.ELRuntimeException("A Condition failed in the performance of a node")
            #select a binding set from the conditions
            internal_state = query_result.bindings
        
        #run and filter by comparisons
        try:
            comp_tuple = self.format_comparisons(target_node['comparisons'])
            compared_bindings = self.filter_by_comparisons(comp_tuple, internal_state)

            
            if len(compared_bindings) == 0:
                raise ELE.ELRuleException('No passing bindings')

            #select:
            selection = choice(compared_bindings)
            
            #run modifications


            #enact actions 
            for action in target_node['actions']:
                if action.hasForAllBinding():
                    bound_actions = [action.bind(selection, x) \
                                     for x in compared_bindings]
                    logging.debug("Bound actions: {}".format(bound_actions))
                else:
                    bound_actions = [action.bind(selection)]
                    
                for act in bound_actions:
                    self.act(act)

            return_value = ELSuccess()

        except KeyError as e:
            logging.debug('No {} found'.format(e.args[0]))

        
        #return the bindings and truth value
        if return_value:
            return (return_value, selection)
        else:
            return (return_value, state)



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
            if isinstance(action[-1], ELQUERY):                       #QUERY
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
            
    def fact_query(self,query, bindingFrame=None):
        """ Test a fact, BE CAREFUL IT MODIFES THE TOP OF THE VAR STACK  """
        logging.debug('Recieved Query: {}'.format(query))
        if bindingFrame is None:
            bindingFrame = self.top_stack()
        assert isinstance(bindingFrame, ELBindingFrame)
        assert isinstance(query[-1], ELQUERY)
        
        current_frame = bindingFrame
        if len(current_frame) == 0:
            logging.debug("Nothing in the current frame")
            return (False, None)
        #fill in any variables from the current bindings
        bound_queries = [query.bind(slice) for slice in current_frame]
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

    def run_rule(self,rule):
        """ Given a rule, check its conditions then queue its results """
        logging.info("Running Rule: {}".format(rule))
        return_val = ELFail()
        try:
            self.push_stack()
            current_frame = self.top_stack()
            for condition in rule.conditions:
                result = self.fact_query(condition, current_frame)
                if not bool(result):
                    raise ELE.ELRuleException()

            # passing_bindings :: ELBindingFrame
            passing_bindings = current_frame.bindings
            
            #get the comparison functions, as a tuple 
            comp_tuple = self.format_comparisons(rule)
            compared_bindings = self.filter_by_comparisons(comp_tuple, passing_bindings)
            
            #if filtered the rule down to nothing
            if len(compared_bindings) == 0:
                raise ELE.ELRuleException()
            
            #select a still viable rule
            #todo: add variability here. utility, curves, distributions,
            #round_robins? state?
            selection = choice(compared_bindings)

            #perform modifications to bindings (regex?)
            
            #todo: make the parser check for unbound variables before adding to runtime?  or should that be covered by the parser?
            for action in rule.actions:

                if action.hasForAllBinding():
                    bound_actions = [action.bind(selection, x) \
                                     for x in compared_bindings]
                    logging.debug("Bound actions: {}".format(bound_actions))
                else:
                    bound_actions = [action.bind(selection)]

                for act in bound_actions:
                    self.act(act)

            return_val = ELSuccess()
        except ELE.ELRuleException:
            logging.warning("ELRule Exception occurred")
            return_val = ELFail()
        finally:
            #then pop the frame off
            self.pop_stack()
        return return_val


    def format_comparisons(self, comparisons): #Rule Utilities:
        #get the operator from the compariso
        retrieved = [(comp, get_COMP_FUNC(comp.op)) for comp in rule.binding_comparisons]
        return retrieved
    

    def filter_by_comparisons(self, comparison_tuples, potential_bindings):
        assert isinstance(potential_bindings, ELBindingFrame)
        compared_bindings = potential_bindings
        for comp, func in comparison_tuples:
            compared_bindings = ELBindingFrame([slice for slice in compared_bindings if self.run_function(slice, func, comp)])
        ## compared_bindings :: ELBD.ELBindingFrame
        return compared_bindings
        
    def run_function(self, binding, func, comparison):
        #get values from bindings:
        if comparison.b1.value not in binding or \
           (isinstance(comparison.b2, ELVAR) and comparison.b2.value not in binding):
            raise ELE.ELConsistencyException('Comparison being run without the necessary bindings')
        val1 = comparison.b1.get_val(binding)
        if isinstance(comparison.b2, ELVAR):
            val2 = comparison.b2.get_val(binding)
        else:
            val2 = comparison.b2
        if comparison.op == ELCOMP.NEAR:
            if isinstance(comparison.nearVal, ELVAR):
                nearVal = comparison.nearVal.get_val(binding)
            else:
                nearVal = comparison.nearVal

            return func(val1, nearVal, val2)
        else:
            return func(val1, val2)


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
