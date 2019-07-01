import os
from hashlib import md5
from .run import Run


output_file = './data/test.txt'
config = {'rounds': 1000}
hparams = {'length': 1024}
    

@Run(output_files=[output_file], config=config, hparams=hparams)
def main(config, output_file):
    with open(output_file, 'wb') as f:
        for _ in range(config['rounds']):
            f.write(os.urandom(hparams['length']) + b'\n')
    
    with open(output_file, 'rb') as f:
        text = f.read()
        result = md5(text).hexdigest()
        return {'md5': result}

if __name__ == "__main__":
    metric = main(config, output_file)
    print(metric)
