from random import randint
from base64 import b64decode, b64encode
import json
from os import path 

HERE = path.dirname(path.abspath(__file__))
PASSWORDS = None

def _load_passwords():
    global PASSWORDS
    if PASSWORDS is None:
        filename=path.join(HERE, '.passwords')
        PASSWORDS = json.load(filename)
    return PASSWORDS

def genereate_password(file_len):
    password_len=10
    assert file_len>0
    password = []
    for i in range(password_len):
        position = randint(0, file_len)
        insertByte = bytes((randint(0, 63),))
        file_len += 1
        password.append((position, insertByte))
    return password

def encode(filename, outname=None):
    f= open(filename, 'rb')
    content = f.read()
    f.close()
    password = genereate_password(len(content))
    positions = []
    for position, insertByte in password:
        content = content[:position] + insertByte + content[position:]
        positions.append(position)
        print('content len: ', len(content))
    #save content
    content = b64encode(content).decode('ascii')
    outname = outname if outname else filename + '.encoded'
    f=open(outname, 'w')
    f.write(content)
    f.close()
    return json.dumps(positions), outname


def decode(filename, password, outname=None):
    '''password: json of list of tuples (position, insertByte)'''
    password = json.loads(password)
    password.reverse()
    with open(filename, 'r') as f:
        content = f.read()
    content = content.encode('ascii')
    content = b64decode(content)
    for position in password:
        content = content[:position]+content[position+1:]
    # content = b64decode
    if outname is None:
        if filename.endswith('.encoded'):
            outname = filename[:-8]
        else:
            raise ValueError('parmeter outname can not be None when filename not end with `.encoded`')
    with open(outname, 'wb') as f:
        f.write(content)
    return outname

#################### Test #############################


def test_genereate_password():
    file_len=100
    password = genereate_password(file_len)
    print(password)


def test_encode_decode():
    filename = path.join(HERE,'test/testdata/testfile.txt')
    line1 = '这是测试第一行....\n'
    line2 = '这是测试第2行.!@#$%^&^&*)))((*\年...'
    with open(filename, 'w')  as f:
        f.write(line1)
        f.write(line2)
    password, outname = encode(filename)
    decode(outname, password)
    with open(filename, 'r') as f:
        t_line1 = f.readline()
        t_line2 = f.readline()
    assert line1==t_line1
    assert line2==t_line2


if __name__=='__main__':
    test_genereate_password() 
    test_encode_decode()
