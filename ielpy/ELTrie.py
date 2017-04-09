"""
A Simple Trie for EL
"""
import IPython
import logging as root_logger
from . import ELBaseData as ELBD
from . ELBaseData import ELTrieNode
from . import ELExceptions as ELE
import uuid
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
        if isinstance(key, uuid.UUID) and key in self.allNodes:
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
            if current.contains_rule():
                rules.append(current)
            processed.add(current)

        return {
            'maxDepth': maxDepth,
            'leaves'  : leaves,
            'rules'   : rules
        }
    
    def is_empty(self):
        return self.root.is_empty()
        
    def push(self,el_string):
        """ Take an ELFact of [ROOT, [PAIRS], TERM],
        and attempt to add to the trie
        """
        logging.debug("Starting to push: {}".format(repr(el_string)))
        assert isinstance(el_string,ELBD.ELFACT)
        assert isinstance(el_string.data[0],ELBD.ELROOT)
        if len(el_string.data) > 1:
            assert isinstance(el_string.data[-1],ELBD.ELTERM)
        try:
            el_string.is_valid()
            returnVal = ELBD.ELFail()
            changes = []
            current = None
            #Go through the passed in string
            for statement in el_string:
                if isinstance(statement,ELBD.ELROOT):
                    logging.debug("Hit Root")
                    if isinstance(statement.value, uuid.UUID) and statement.value in self.allNodes:
                        current = self.allNodes[statement.value]
                    elif statement.value is None:
                        current = self.root
                    else:
                        raise ELE.ELConsistencyException('Root is not a uuid or empty')
                    continue # <---- note this
                elif isinstance(statement,ELBD.ELTERM) and statement not in current:
                    #came to the terminal, and it is missing
                    logging.debug("Missing TERM: {}".format(repr(statement)))
                    newNode = ELTrieNode(statement,parent=current)
                    current[statement] = newNode
                    self.allNodes[newNode.uuid] = newNode
                    returnVal = ELBD.ELSuccess()
                elif isinstance(statement,ELBD.ELPAIR) and statement not in current:
                    #came to a pair, and it is missing
                    logging.debug("Missing PAIR: {}".format(repr(statement)))
                    newNode = ELTrieNode(statement, parent=current)
                    current[statement] = newNode
                    self.allNodes[newNode.uuid] = newNode
                #for everything but finding the root:
                logging.debug("-> {}".format(repr(statement)))
                current = current[statement]
        except ELE.ELException as e:
            logging.critical(e)
            returnVal = ELBD.ELFail()
        finally:
            return returnVal
        
    def pop(self,el_string):
        """ Remove an EL String from the Trie """
        returnVal = ELBD.ELFail()
        theTarget = None
        if isinstance(el_string, ELBD.ELFACT):
            searchResult = self.get(el_string)
            if searchResult:
                theTarget = self.allNodes[searchResult.bindings[0].uuid]
        elif isinstance(el_string, ELBD.ELSuccess):
            theTarget = self.allNodes[el_string.bindings[0][0]]

        if theTarget is None:
            return ELBD.ELFail()
        
        target_parent = theTarget.parent
        
        del target_parent[theTarget]
        return ELBD.ELSuccess()
        
        
    def query(self,query):
        """ Given an EL String, test the Trie to see if it is true """
        assert isinstance(query,ELBD.ELQUERY)
        #result :: ELFail | ELSuccess
        result = self.get(query.value)
        logging.debug('Get Result: {}'.format(result))
        if isinstance(result,ELBD.ELSuccess) and not query.value.negated:
            return result
        elif isinstance(result, ELBD.ELFail) and query.value.negated:
            #successful, but with no bindings
            #Todo: or should it be the passed in bindings?
            return ELBD.ELSuccess(bindings=ELBD.ELBindingFrame([query.value.filled_bindings]))
        else:
            return ELBD.ELFail()
        
        
    def get(self,el_string):
        assert isinstance(el_string, ELBD.ELFACT)
        assert el_string.is_valid_for_searching()

        if not el_string.data[0].isVar():
            root = self.root
        elif el_string.data[0].value in self.allNodes: 
            root = self.allNodes[el_string.data[0].value]
        else:
            raise ELE.ELRuleException('Root Value not found in allnodes')
        #results :: ELBindingFrame
        results = self.sub_get(root, el_string.data[1:], el_string.filled_bindings)
        logging.debug("Sub Get Results: {}".format(results))
        returnVal = ELBD.ELFail()
        if isinstance(results,list) and not isinstance(results[0], ELBD.ELFail):
            #verify all bindings are the same:
            #firstKeys :: ELBindingSlice
            firstKeys = results[0].keys()
            allSame = all([firstKeys == bindings.keys() for bindings in results])
            if allSame:
                returnVal = ELBD.ELSuccess(path=el_string,bindings=results)

        # returnVal :: ELSuccess | ELFail
        return returnVal
                
    #the recursive call of get where most of the work goes on
    def sub_get(self, root, el_string, current_bindings=None, new_binding=None):
        assert isinstance(root, ELBD.ELTrieNode)
        assert isinstance(el_string, list)
        if current_bindings is None:
            internal_bindings = ELBD.ELBindingSlice()
        else:
            internal_bindings = ELBD.ELBindingSlice(current_bindings)
        if new_binding is not None:
            assert len(new_binding) == 3
            internal_bindings[new_binding[0]] = ELBD.ELBindingEntry(*new_binding)
        current = root
        results = ELBD.ELBindingFrame([])
        remaining_string = el_string.copy()
        while len(remaining_string) > 0:
            statement = remaining_string.pop(0)
            #if a var
            if (isinstance(statement, ELBD.ELPAIR) or \
               isinstance(statement, ELBD.ELTERM)) and \
               statement.isVar():
                #Trigger a recursion
                
                #todo: complain on duplicate keys
                varKey = statement.value.value
                for child in current.children.values():
                    results.extend(self.sub_get(self[child.uuid],
                                                remaining_string,
                                                internal_bindings,
                                                (varKey, child.uuid, child.value)))
                #clear so only the recursions continue
                remaining_string = []
                current = None
            #not a var
            elif (isinstance(statement, ELBD.ELPAIR) or \
                 isinstance(statement, ELBD.ELTERM)) and \
                 statement in current:
                current = current[statement]
            #not anything usable
            elif not isinstance(statement, ELBD.ELPAIR) and \
                 not isinstance(statement, ELBD.ELTERM):
                raise ELE.ELConsistencyException('Getting something that is not a pair or term')
            else:
                results.append(ELBD.ELFail())
                remaining_string = []

        #cleanup after looping:
        #remove all ELBD.ELFails
        containsAFail = any([isinstance(x, ELBD.ELFail) for x in results])
        results = ELBD.ELBindingFrame([x for x in results if not isinstance(x, ELBD.ELFail)])
        #if nothing remains, return just an ELFail
        if len(results) == 0 and containsAFail:
            results = ELBD.ELBindingFrame([ ELBD.ELFail() ])
        elif len(results) == 0:
            #if successful, store the internal bindings and where this node is
            results = ELBD.ELBindingFrame([ ELBD.ELBindingSlice(internal_bindings, current.uuid) ])
        #results are: [ ELFail | bindings ]
        #Results :: ELBindingFrame
        return results
        
