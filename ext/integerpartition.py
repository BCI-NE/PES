"""
PES - Pandemic Experiment Scenario

This code calculates the number of available partitions of integers divisions
given a constraint in the number of available resources.

This is the combinatorial program that needs to be solved in this experiment.

"""




def partition(n,d,limit, depth=0):
    if d == depth:
        return [[]]
    return [
            item + [i]
            for i in range(n+1) if i<=limit
            for item in partition(n-i, d, limit, depth=depth+1)
            ]


n = 40 # MAX_ALLOCATABLE_RESOURCES
d = 5
limitsize = 10
lst =[[n-sum(p)] + p for p in partition(n, d-1, limitsize)]


lst = partition(n,d,limitsize)
print (lst)
print('Length: ' + str(len(lst)))

lengths = []
for N in range(0,10):
    lst = partition(n, N, limitsize)
    print('Length %03e:  %d' % (N, len(lst)))
    lengths.append(len(lst))

print( lengths )



