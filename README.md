# PyEL: Python Exclusion Logic

A Pyparsing based parser for EL, combined with a trie to manage facts,
glued together in a single runtime.

See *exampleGrammar* for the work in progress grammar.

The Parser is in ElParser/ELParser.py
The Trie is in ELParser/ELTrie.py

*TODO: *: Add previous time checking?
    Making the Trie 3d? 3rd dimension of diffs?
    Run the trie forwards, and be able to take snapshots to ease the assertion and retraction log.
    
    Store the tree as the string, reconstruct by reading it in.
    Trie exists in a collection of nodes, so copy it, then run modifications.
    Store asserted actions list, reconstruct all history using (backwards jump + rerun)    
    

    Pass slices up and down rules
    Test across slices

    Represent time steps as indices, to find the state at a particular moment:
    If time now is t^n, focus time is t^f. To test that moment go to t^f on the root node,
    or t^i where i = maxExisting(0,f-1), and run the state on each successive node, always choosing
        t^j where j = maxExisting(i,f-1)
        
    To test if something has ever happened, search t^i - t^f simultaneously
    
    compiling: would diff different conditions, get duplicate parent structures,

    Mainly: Be able to run all variations of a rule,
        be able to run a group of rules (as a compiled test trie?)
        be able to compare against an aggreagate of potential rules instead of internal bindings,
        
        compiled test trie would be a retenet? fling bits from the
        actual trie, into the alpha network of a retenet, which
        collects into beta tokens, return as rule+stackframe
        combinations?
    

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

    //add to the value there
    .this.is.a.different.arithmetic.rule.{ .a.condition.$x? -> $..x + 20 }  
    .this.is.a.third.rule.{ .a.condition.$x?, .b.condition.$y? -> $..x + $y }  
    .this.is.a.fourth.rule.{ .a.condition.$x ? -> .a.result.$x }  
    

    .a.value.20  
    .a.large.value.10_000  
    .a.fraction.1/5  
    .a.decimal.1d5  
    .a.string."this is a string".with.subfacts  
    .a.sequence.[.a.b.c, .a.b.d]
    
    #TODO: subtree testing and application
```


# Forall binding...
.a.b.c, .a.b.d
.a.b.$x -> .q.e.@x
.q.e.c?, .q.e.d?

.a.b.c.e, .a.b.d.f
.a.b.$x.$y -> .q.e.@x.@$y
.q.e.c.e?, .q.e.d.f?

.a.b.$x.$y | $y == 'f' -> .q.e.@x.$y
.q.e.c.f?, .q.e.d.f?

.a.b.$x.$y | $x == c -> .q.e.$x.@y
.q.e.c.e?, .q.e.c.f?

