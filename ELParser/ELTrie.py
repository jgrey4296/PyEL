"""
A Simple Trie for EL
"""
import logging as root_logger
from ELParser import ELBaseData as ELBD
from ELParser.ELBaseData import ELTrieNode
logging = root_logger.getLogger(__name__)


    
class ELTrie:
    """ A Simple Python Trie implementation for EL """
    def __init__(self):
        #The root element of the trie, everything starts here.
        #Is essentially the opening '.'
        self.root = ELTrieNode('ROOT')

    def is_empty(self):
        return self.root.is_empty()
        
    def push(self,el_string):
        """ Take an ELFact of [ROOT, [PAIRS], TERM],
        and attempt to add to the trie
        """
        logging.debug("Starting to push: {}".format(str(el_string)))
        assert isinstance(el_string,ELBD.ELFACT)
        assert isinstance(el_string.data[0],ELBD.ELROOT)
        if len(el_string.data) > 1:
            assert isinstance(el_string.data[-1],ELBD.ELTERM)
        
        #First change is (Parent,Original,New) for rewinding
        first_change = (None,None,None)
        current = None
        for statement in el_string:
            if isinstance(statement,ELBD.ELROOT):
                logging.debug("Hit Root")
                current = self.root
                continue
            elif isinstance(statement,ELBD.ELTERM) and statement not in current:
                logging.debug("Missing TERM: {}".format(str(statement)))
                current[statement] = ELTrieNode(statement)
            elif isinstance(statement,ELBD.ELPAIR) and statement not in current:
                logging.debug("Missing PAIR: {}".format(str(statement)))
                current[statement] = ELTrieNode(statement)
            logging.debug("-> {}".format(str(statement)))
            current = current[statement]
            
        return ELBD.ELSuccess()
        
    def pop(self,el_string):
        """ Remove an EL String from the Trie """
        return False
        
    def test(self,el_string):
        """ Given an EL String, test the Trie to see if it is true """
        result = self.get(el_string)
        if isinstance(result,ELBD.ELGet):
            return ELBD.ELSuccess()
        else:
            return ELBD.ELFail()
        
        
    def get(self,el_string):
        """ Get the values at the leaf of the specified EL String
            Returns an ELBD.ELRESULT

        """
        assert isinstance(el_string,ELBD.ELFACT)
        if len(el_string.data) == 1 and isinstance(el_string.data[0],ELBD.ELROOT):
            return ELBD.ELGet(self.root.value, list(self.root.keys()))
        else:
            current = None
            for statement in el_string:
                if isinstance(statement,ELBD.ELROOT):
                    current = self.root
                    continue
                elif statement in current:
                    current = current[statement]
                else:
                    return ELBD.ELFail()

            return ELBD.ELGet(current.value,list(current.keys()))
        
        

          

