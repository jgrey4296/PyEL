"""
A Simple Trie for EL
"""
import IPython
import logging as root_logger
from ELParser import ELBaseData as ELBD
from ELParser.ELBaseData import ELTrieNode
from ELParser import ELExceptions as ELE
logging = root_logger.getLogger(__name__)

class ELTrie:
    """ A Simple Python Trie implementation for EL """
    def __init__(self):
        #The root element of the trie, everything starts here.
        #Is essentially the opening '.'
        self.root = ELTrieNode('ROOT')
        #all nodes indexed by uuid
        self.allNodes = {}        

    def __getitem__(self,key):
        if key in self.root:
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
                    newNode = ELTrieNode(statement)
                    current[statement] = newNode
                    self.allNodes[newNode.uuid] = newNode
                elif isinstance(statement,ELBD.ELPAIR) and statement not in current:
                    #came to a pair, and it is missing
                    logging.debug("Missing PAIR: {}".format(repr(statement)))
                    newNode = ELTrieNode(statement)
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
        retrieved = self.get(el_string,log_path=True)
        if not retrieved:
            return retrieved
        
        #now go up the chain
        path = retrieved.path
        focus = path.pop()
        parent = path.pop()

        if focus in parent:
            del parent[focus]
        else:
            raise ELE.ELConsistencyException("""Got to a state when a parent node somehow
            doesn't have the child just retrieved """)
        
        
    def query(self,query):
        """ Given an EL String, test the Trie to see if it is true """
        if not isinstance(query,ELBD.ELQUERY):
            raise ELE.ELConsistencyException("To query, wrap a fact in an ELBD.ELQUERY")
        result = self.get(query.value)
        logging.info('Get Result: {}'.format(result))
        if isinstance(result,ELBD.ELGet) and not query.value.negated:
            return result
        elif isinstance(result, ELBD.ELFail) and query.value.negated:
            return ELBD.ELSuccess()
        else:
            return ELBD.ELFail()
        
        
    def get(self,el_string,log_path=False):
        """ Get the values at the leaf of the specified EL String
            Returns an ELBD.ELRESULT

        """
        assert isinstance(el_string,ELBD.ELFACT)
        try:
            el_string.is_valid_for_searching()
            path = []
            returnVal = None
            current = None
            for statement in el_string:
                logging.info('Getting: {}'.format(statement))
                if isinstance(statement,ELBD.ELROOT):
                    current = self.root
                elif isinstance(statement.value, ELBD.ELVAR):
                    #is a variable. get all options, bind them
                    #then filter by the rest of the test
                    children = current.keys()
                    logging.info('Returning: {}'.format(children))
                    returnVal = ELBD.ELGet(statement.value.value,children, path=path.copy(), root=current)
                    break
                elif statement in current:
                    current = current[statement]
                else:
                    returnVal = ELBD.ELFail()
                    break
                path.append(current)
                    
            if not log_path:
                path = None
            #get the final current value:
            if returnVal is None:
                returnVal = ELBD.ELGet(current.value,list(current.keys()),path=path)
        except ELE.ELException as e:
            logging.critical("Trie Get Exception: {}".format(e))
            returnVal = ELBD.ELFail()
        finally:
            return returnVal

