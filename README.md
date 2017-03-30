# PyEL: Python Exclusion Logic

A Pyparsing based parser for EL, combined with a trie to manage facts,
glued together in a single runtime.

See *exampleGrammar* for the work in progress grammar.

The Parser is in ElParser/ELParser.py
The Trie is in ELParser/ELTrie.py

## Language

```
    #a comment
    .this.is.an.assertion  
    .this.is.an!exclusive.assertion  
    
    #exclusion semantics:
    .a.first
    .a.second
    # => .a.first && a.second
    .a!first
    # => .a!first   no .a.second
    .a.first
    .a.second
    # => back to .a.(first/second)
    
    $x <- .a.binding
    $x.blah
    #.a.binding.blah

    .this.is.a.query?  

    .this.is.a.rule.{ .a.condition?, .a.second.condition? -> .an.action }  
    .this.is.a.binding.rule.{ .a.condition.$a? -> .an.action.$a }
    .this.is.a.comparison.rule.{ .a.condition.$a?, .a.other.condition.$b? | $a < $b -> .an.action }
    .this.is.an.arithmetic.rule.{ .a.condition? -> .a.value + 20 }  

    .a.value.20  
    .a.large.value.10_000  
    .a.fraction.1/5  
    .a.decimal.1d5  
    .a.string."this is a string".with.subfacts  
    .a.sequence.[.a.b.c, .a.b.d]
    
    #TODO: subtree testing and application
```
