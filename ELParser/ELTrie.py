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

    def __getitem__(self,key):
        if key in self.root:
            return self.root[key]
        else:
            raise KeyError("{} not found in {}".format(repr(key),repr(self.root)))

        
    def __repr__(self):
        return "Trie: {}".format(self.root)
        
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
                    current[statement] = ELTrieNode(statement)
                elif isinstance(statement,ELBD.ELPAIR) and statement not in current:
                    #came to a pair, and it is missing
                    logging.debug("Missing PAIR: {}".format(repr(statement)))
                    current[statement] = ELTrieNode(statement)
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

        #now go up the chain, cleaning up as necessary
        path = retrieved.path
        prior = None
        focus = None
        while len(path) > 0 and len(path[-1]) < 2:
            prior = focus
            focus = path.pop()
        if len(path) > 0:
            prior = focus
            focus = path.pop()            

        if prior in focus:
            del focus[prior]
        else:
            raise ELE.ELConsistencyException("""Got to a state when a parent node somehow
            doesn't have the child just retrieved """)
        
        
    def query(self,query):
        """ Given an EL String, test the Trie to see if it is true """
        if not isinstance(query,ELBD.ELQUERY):
            raise ELE.ELConsistencyException("To query, wrap a fact in an ELBD.ELQUERY")
        result = self.get(query.value)
        if isinstance(result,ELBD.ELGet):
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
            if len(el_string.data) == 1 and isinstance(el_string.data[0],ELBD.ELROOT):
                returnVal = ELBD.ELGet(self.root.value, list(self.root.keys()))
            else:
                current = None
                for statement in el_string:
                    if isinstance(statement,ELBD.ELROOT):
                        current = self.root
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
            logging.critical(e)
            returnVal = ELBD.ELFail()
        finally:
            return returnVal
        
        

          

