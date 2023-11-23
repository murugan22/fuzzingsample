all_inst = set()

for i in open("all_insts.txt", "r"):
    all_inst.add(i.strip())

test_inst = set()

for i in open("output_classes/all_cov_insts.txt", "r"):
    test_inst.add(i.strip().split()[1])

print("Covered Instructions")
print(sorted(test_inst))
print("\n\n")
print("Uncovered Instructions:")
print(sorted(all_inst - test_inst))
print("\n\n")
print("Total percentage of covered Instructions")
print(len(test_inst) / len(all_inst) * 100)
print("Total number of instructions covered")
print(len(test_inst))