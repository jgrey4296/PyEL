"""
A Simple Trie for EL
"""
import IPython
import logging as root_logger
from .ELBinding import ELBindingFrame, ELBindingSlice, ELBindingEntry
from .ELStructure import ELROOT
from .ELFactStructure import ELFACT, ELPAIR
from .ELTrieNode import ELTrieNode
from .ELResults import ELSuccess, ELFail
from . import ELExceptions as ELE
from uuid import UUID


logging = root_logger.getLogger(__name__)

class ELTrie:
    """ A Simple Python Trie implementation for EL """
    def __init__(self):
        #The root element of the trie, everything starts here.
        #Is essentially the opening '.'
        self.root = ELTrieNode('ROOT')
        #all nodes indexed by uuid
        self.allNodes = {self.root.uuid : self.root}
        

    def __getitem__(self,key):
        if isinstance(key, UUID) and key in self.allNodes:
            return self.allNodes[key]
        elif key in self.root:
            return self.root[key]
        else:
            raise KeyError("{} not found in {}".format(repr(key),repr(self.root)))
        
    def __repr__(self):
        return "Trie: {}".format(self.root)

    def dfs_for_metrics(self):
        #Queue is an array of (node,depth)
        queue = [(self.root,0)]
        processed = set()
        maxDepth = 0
        leaves = []
        rules = []
        while len(queue) > 0:
            current,depth = queue.pop(0)
            if current in processed:
                raise ELE.ELConsistencyException("DFS on Trie, cross edges should be impossible")
            queue.extend([(x,depth+1) for x in current.values()])
            if depth > maxDepth:
                maxDepth = depth
            if len(current) == 0:
                leaves.append(current)
            processed.add(current)

        return {
            'maxDepth': maxDepth,
            'leaves'  : leaves,
        }
    
    def is_empty(self):
        return self.root.is_empty()
        
    def push(self,el_string):
        """ Take an ELFact of [ROOT, [PAIRS]],
        and attempt to add to the trie
        """
        logging.debug("Starting to push: {}".format(repr(el_string)))
        assert isinstance(el_string, ELFACT)
        assert isinstance(el_string.data[0], ELROOT)
        try:
            returnVal = ELFail()
            current = None
            #Go through the passed in string
            for statement in el_string:
                if isinstance(statement, ELROOT) and current is None:
                    logging.debug("Hit Root")
                    if isinstance(statement.value, UUID) and statement.value in self.allNodes:
                        current = self.allNodes[statement.value]
                    elif statement.value is None and current is None:
                        current = self.root
                    else:
                        raise ELE.ELConsistencyException("Issue with the root")
                    continue # <---- note this
                elif isinstance(statement, ELROOT) and current is not None and \
                     statement not in current:
                    logging.debug("Adding a pseudo-root")
                    newNode = ELTrieNode(statement, parent=current)
                    current[newNode] = newNode
                    self.allNodes[newNode.uuid] = newNode
                elif isinstance(statement, ELPAIR) and statement not in current:
                    #came to a pair, and it is missing
                    logging.debug("Missing PAIR: {}".format(repr(statement)))
                    newNode = ELTrieNode(statement, parent=current)
                    current[newNode] = newNode
                    self.allNodes[newNode.uuid] = newNode
                #for everything but finding the root:
                logging.debug("-> {}".format(repr(statement)))
                current = current[statement]
                #update the elop if necessary:
                current.update_elop(statement.elop)                    
                
            returnVal = ELSuccess()
        except ELE.ELException as e:
            logging.critical(e)
            returnVal = ELFail()
        finally:
            return returnVal
        
    def pop(self,el_string):
        """ Remove an EL String from the Trie """
        theTarget = None
        if isinstance(el_string, UUID):
            theTarget = self.allNodes[el_string]
        elif isinstance(el_string, ELFACT):
            searchResult = self.get(el_string)
            if searchResult:
                theTarget = self.allNodes[searchResult.nodes[0]]
        elif isinstance(el_string, ELSuccess):
            theTarget = self.allNodes[el_string.nodes[0]]

        if theTarget is None:
            return ELFail()
        
        target_parent = theTarget.parent
        
        del target_parent[theTarget]
        return ELSuccess()
        
        
    def query(self,query):
        """ Given an EL String, test the Trie to see if it is true """
        assert query.is_query()
        #result :: ELFail | ELSuccess
        result = self.get(query)
        logging.debug('Get Result: {}'.format(result))
        if isinstance(result, ELSuccess) and not query.negated:
            return result
        elif isinstance(result, ELFail) and query.negated:
            #successful, but with no bindings
            #Todo: or should it be the passed in bindings?
            return ELSuccess(path=query,
                                  bindings=ELBindingFrame([query.filled_bindings]),
                                  nodes=None)
        else:
            return ELFail()
        
        
    def get(self,el_string):
        assert isinstance(el_string, ELFACT)
        if not el_string[0].isVar():
            root = self.root
        elif el_string[0].value in self.allNodes: 
            root = self.allNodes[el_string[0].value]
        else:
            raise ELE.ELRuleException('Root Value not found in allnodes')
        #lop off the final query (?) structure:
        if el_string.is_query():
            search_string = el_string[1:-1]
        else:
            search_string = el_string[1:]
                    
        #results :: ELBindingFrame< ELBindingSlice | ELFail >
        results = self.sub_get(root, search_string, el_string.filled_bindings)
        logging.debug("Sub Get Results: {}".format(results))
        returnVal = ELFail()
        if isinstance(results,list) and not isinstance(results[0], ELFail):
            #verify all bindings are the same:
            #firstKeys :: ELBindingSlice
            firstKeys = results[0].keys()
            allSame = all([firstKeys == bindings.keys() for bindings in results])
            if allSame:
                returnVal = ELSuccess(path=el_string,
                                           bindings=results,
                                           nodes=[x.uuid for x in results if x.uuid is not None])

        # returnVal :: ELSuccess | ELFail
        return returnVal
                
    #the recursive call of get where most of the work goes on
    def sub_get(self, root, el_string, current_bindings=None, new_binding=None):
        assert isinstance(root, ELTrieNode)
        assert isinstance(el_string, list)
        if current_bindings is None:
            internal_bindings = ELBindingSlice()
        else:
            internal_bindings = ELBindingSlice(current_bindings)
        if new_binding is not None:
            assert len(new_binding) == 3
            internal_bindings[new_binding[0]] = ELBindingEntry(*new_binding)
        current = root
        results = ELBindingFrame([])
        remaining_string = el_string[:]
        while len(remaining_string) > 0:
            statement = remaining_string.pop(0)
            logging.debug("Sub Getting: {}".format(statement))
            #if a var
            if isinstance(statement, ELPAIR) and statement.isVar():
                logging.debug("Dealing with a Variable")
                #Trigger a recursion
                #todo: complain on duplicate keys
                varKey = statement.value.value
                for child in current.children.values():
                    results.extend(self.sub_get(self[child.uuid],
                                                remaining_string,
                                                current_bindings=internal_bindings,
                                                new_binding=(varKey, child.uuid, child.value)))
                #clear so only the recursions continue
                remaining_string = []
                current = None
            #not a var
            elif isinstance(statement, ELPAIR) and \
                 statement in current and \
                 (len(remaining_string) == 0 or \
                  statement.elop == current[statement].elop):
                logging.debug("ELPair matches")
                current = current[statement]
            elif isinstance(statement, ELROOT) and statement in current:
                logging.debug("Retrieved ROOT")
                current = current[statement]
            elif not isinstance(statement, ELPAIR):
                raise ELE.ELConsistencyException('Getting something that is not a pair: {}'.format(statement))
            else:
                logging.debug("Failing out")
                logging.debug("Remaining: {}".format(remaining_string))
                results.append(ELFail())
                remaining_string = []

        #cleanup after looping:
        #remove all ELBD.ELFails
        containsAFail = any([isinstance(x, ELFail) for x in results])
        results = ELBindingFrame([x for x in results if not isinstance(x, ELFail)])
        #if nothing remains, return just an ELFail
        if len(results) == 0 and containsAFail:
            results = ELBindingFrame([ ELFail() ])
        elif len(results) == 0:
            #if successful, store the internal bindings and where this node is
            results = ELBindingFrame([ ELBindingSlice(internal_bindings, current.uuid) ])
        #Results :: ELBindingFrame
        return results
        
