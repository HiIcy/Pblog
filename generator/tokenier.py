import os
from multiprocessing import Pool
import sys
import nltk

def chinese_process(filein, fileout):
    with open(filein, 'r',encoding='utf-8') as infile:
        with open(fileout, 'w',encoding="utf-8") as outfile:
            # pass
            contents = nltk.sent_tokenize(infile.read())
            for line in contents:
                output = list()
                # line = line.decode('utf-8')
                try:
                    hang = nltk.word_tokenize(line,"chinese")[0]
                    for char in hang:
                        output.append(char)
                        output.append(' ')
                    output.append('\n')
                    output = ''.join(output)
                    outfile.write(output)
                except Exception as e:
                    # hang = nltk.word_tokenize(line,"chinese")[0]
                    print(e)
                    # exit(-1)
                

def Process(filess,outputs_dir):
    print(len(filess))
    for file in filess:
        suffix = os.path.split(file)[1]
        outf = os.path.join(outputs_dir,suffix)
        chinese_process(file,outf)

if __name__ == "__main__":
    inputs_dir = r"F:\Resources\kdata\blogp\cleanTag"
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

