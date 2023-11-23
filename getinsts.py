import sys 

disas_file = sys.argv[1] + "/disassembled.txt"
all_cov_insts_file = "output_classes/all_cov_insts.txt"
f = open(all_cov_insts_file, "a+")

main = False 
code = False
for i in open(disas_file, "r"):
    if i.strip() == "public static void main(java.lang.String[]);":
        main = True 
        continue
    
    if i.strip() == "Code:" and main == True:
        code = True 
        continue
    
    if main and code:
        if i.strip() == "}":
            exit()
        f.write(i)