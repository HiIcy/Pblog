import os
from multiprocessing import Pool
import re

pattern = re.compile("(<.*?>|</.*?>)")
latex_pattern = re.compile('(<span\s+class="katex--display">.*?</span><br/>)')
def clean(infile,outfile):
    with open(infile,'r',encoding="utf-8") as filein:
        with open(outfile,"w",encoding="utf-8") as fileout:
            for i,line in enumerate(filein):
                res = re.sub(latex_pattern,"",line)
                res = re.sub(pattern,"",res)
                res = res.strip(" ")

                fileout.write(res)

def Process(filess,outputs_dir):
    print(len(filess))
    for file in filess:
        suffix = os.path.split(file)[1]
        outf = os.path.join(outputs_dir,suffix)
        clean(file,outf)

if __name__ == "__main__":
    # single_file = r"F:\Resources\kdata\blogp\origin\深度学习优化函数详解（4）-- momentum 动量法.html"
    # out_file = r"F:\Resources\kdata\blogp\outputs\ray.html"
    # clean(single_file,out_file)
    inputs_dir = r"F:\Resources\kdata\blogp\origin"
    outputs_dir = r"F:\Resources\kdata\blogp\outputs"
    files = [os.path.join(inputs_dir,file) for file in os.listdir(inputs_dir)]
    cores_num = os.cpu_count()
    pool = Pool(cores_num)
    each_num = len(files) // cores_num
    for i in range(cores_num):
        if i==(cores_num-1):
            pool.apply_async(Process,args=(files[i*each_num:],outputs_dir))
        else:
            pool.apply_async(Process,args=(files[i*each_num:(i+1)*each_num],outputs_dir))
    pool.close()
    pool.join()