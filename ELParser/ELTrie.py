"""
A Simple Trie for EL
"""
import IPython
import logging as root_logger
from ELParser import ELBaseData as ELBD
from ELParser.ELBaseData import ELTrieNode
from ELParser import ELExceptions as ELE
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
            'leaves'  : len(leaves),
            'rules'   : len(rules)
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
            returnVal = ELBD.ELSuccess()
            changes = []
            current = None
            #Go through the passed in string
            for statement in el_string:
                if isinstance(statement,ELBD.ELROOT):
                    logging.debug("Hit Root")
                    current = self.root
                    continue # <---- note this
                elif isinstance(statement,ELBD.ELTERM) and statement not in current:
                    #came to the terminal, and it is missing
                    logging.debug("Missing TERM: {}".format(repr(statement)))
                    newNode = ELTrieNode(statement,parent=current)
                    current[statement] = newNode
                    self.allNodes[newNode.uuid] = newNode
                elif isinstance(statement,ELBD.ELPAIR) and statement not in current:
                    #came to a pair, and it is missing
                    logging.debug("Missing PAIR: {}".format(repr(statement)))
                    newNode = ELTrieNode(statement, parent=current)
                    current[statement] = newNode
                    self.allNodes[newNode.uuid] = newNode
                #for everything but finding the root:
                logging.debug("-> {}".format(repr(statement)))
                current = current[statement]
        except Exception as e:
            logging.critical(e)
            returnVal = ELBD.ELFail()
        finally:
            return returnVal
        
    def pop(self,el_string):
        """ Remove an EL String from the Trie """
        theTarget = None
        if isinstance(el_string, ELBD.ELFACT):
            searchResult = self.get(el_string)
            if searchResult:
                theTarget = self.allNodes[searchResult.bindings[0][0]]
            else:
                return ELBD.ELFail()
        elif isinstance(el_string, ELBD.ELSuccess):
            theTarget = self.allNodes[el_string.bindings[0][0]]

        if theTarget is None:
            raise ELE.ELConsistencyException('Pop requires a valid target')
        
        target_parent = theTarget.parent
        
        del target_parent[theTarget]
        return ELBD.ELSuccess()
        
        
    def query(self,query):
        """ Given an EL String, test the Trie to see if it is true """
        if not isinstance(query,ELBD.ELQUERY):
            raise ELE.ELConsistencyException("To query, wrap a fact in an ELBD.ELQUERY")
        result = self.get(query.value)
        #logging.info('Get Result: {}'.format(result))
        if isinstance(result,ELBD.ELSuccess) and not query.value.negated:
            return result
        elif isinstance(result, ELBD.ELFail) and query.value.negated:
            return ELBD.ELSuccess()
        else:
            return ELBD.ELFail()
        
        
    def get(self,el_string):
        assert isinstance(el_string, ELBD.ELFACT)
        assert el_string.is_valid_for_searching()
        #todo: deal with non-root starts
        results = self.sub_get(self.root, el_string.data[1:], el_string.filled_bindings)
        if len(results) == 1 and isinstance(results[0], ELBD.ELFail):
            return ELBD.ELFail()
        if len(results) == 1 and len(results[0]) == 0:
            return ELBD.ELSuccess(path=el_string,bindings=results)
        else:
            #verify all bindings are the same:
            first = results[0][1].keys()
            allSame = all([first == bindings.keys() for node,bindings in results])
            if not allSame:
                return ELBD.ELFail()
            return ELBD.ELSuccess(path=el_string,bindings=results)        

    #the recursive call of get where most of the work goes on
    def sub_get(self, root, el_string, current_bindings={}, new_binding=None):
        internal_bindings = current_bindings.copy()
        if new_binding is not None:
            internal_bindings[new_binding[0]] = new_binding[1]
        current = root
        results = []
        remaining_string = el_string.copy()
        while len(remaining_string) > 0:
            statement = remaining_string.pop(0)
            #if a var
            if (isinstance(statement, ELBD.ELPAIR) or \
               isinstance(statement, ELBD.ELTERM)) and \
               statement.isVar():
                #todo: complain on duplicate keys
                varKey = statement.value.value
                for child in current.children.values():
                    results.extend(self.sub_get(self[child.uuid],
                                                remaining_string,
                                                internal_bindings,
                                                (varKey,child.value)))
                remaining_string = []
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

        #remove all ELBD.ELFails
        containsAFail = any([isinstance(x, ELBD.ELFail) for x in results])
        results = [x for x in results if not isinstance(x, ELBD.ELFail)]
        #if nothing remains, return just an ELFail
        if len(results) == 0 and containsAFail:
            results = [ ELBD.ELFail()]
        elif len(results) == 0:
            results = [ (current.uuid,internal_bindings) ]
        return results
        
