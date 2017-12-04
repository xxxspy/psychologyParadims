from random import randint
from base64 import b64decode, b64encode
import json
import os
from os import path 
import email
import email.mime.text
import smtplib
from datetime import datetime

HERE = path.dirname(path.abspath(__file__))
PASSWORDS = None
SUFFIXES = ('.es','.es2','.py','.psyexp')
DIRS = ('eprime','psychopy')

def _load_passwords():
    '''load passwords lazily'''
    global PASSWORDS
    if PASSWORDS is None:
        filename=path.join(HERE, '.passwords')
        if path.exists(filename):
            PASSWORDS = json.loads(open(filename, 'r').read())
        else:
            PASSWORDS={}
    return PASSWORDS

def _save_passwords():
    PASSWORDS = _load_passwords()
    filename = path.join(HERE, '.passwords')
    json.dump(PASSWORDS, filename)

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

def needEncodeFiles(dirname=None):
    # dirs = [path.join(HERE, d) for d in DIRS]
    files = []
    if dirname:
        dirname = dirname if path.isabs(dirname) else path.join(HERE, dirname)
        aim_dirs =[dirname,]
    else:
        aim_dirs = [path.join(HERE, p) for p in DIRS]
    for dr in aim_dirs:
        for fdr, subdirs, subfiles in os.walk(dr):
            for f in subfiles:
                for sf in SUFFIXES:
                    if f.endswith(sf):
                        files.append(path.join(fdr, f))
    return files

def needDecodeFiles(dirname=None):
    files =[]
    aim_dirs=[]
    if dirname:
        dirname = dirname if path.isabs(dirname) else path.join(HERE, dirname)
        aim_dirs = [dirname, ]
    else:
        aim_dirs = [path.join(HERE, p) for p in DIRS]
    for dr in aim_dirs:
        for fdr, subdirs, subfiles in os.walk(dr):
            for f in subfiles:
                if f.endswith('.encoded'):
                    files.append(path.join(fdr, f))
    return files

        

def encodeAll(dirname=None):
    '''将对dirname下的文件进行加密,
    如果没有指定dirname, 将会对DIRS下所有文件加密'''
    pw_map = _load_passwords()
    for abspath in needEncodeFiles(dirname=dirname):
        relpath = path.relpath(abspath,start=HERE)
        password, outname = encode(abspath)
        del outname
        pw_map[relpath]=password
    c=json.dumps(pw_map)
    open('.passwords', 'w').write(c)

def decodeAll(dirname=None):
    '''将会对dirname下的文件解密, 
    如果没有指定dirname, 会将所有DIRS下所有文件解密'''
    pw_map = _load_passwords()
    for abspath in needDecodeFiles(dirname=dirname):
        if abspath not in pw_map:
            raise ValueError('No Password, check `.passwords` file')
        password = pw_map[abspath]
        decode(abspath, password)

def sendPasswords(passwords: str):
    '''把密码发送到我的邮箱'''
    now = datetime.now().strftime('%Y%m%d')
    try:
        username = os.environ['SMTP_USER']
        token = os.environ['SMTP_TOKEN']
    except KeyError as e:
        print(e)
        raise ValueError('You should set environ variables(SMTP_USER, SMTP_TOKEN)')
    server_addr= 'smtp.163.com'
    # passwords = open('.passwords', 'r', encoding='utf8').read()
    server = smtplib.SMTP(server_addr, 25)
    server.login(username, token)
    content = email.mime.text.MIMEText(passwords, 'plain', 'utf8')
    header = email.header.Header(now + 'psychologyParadim密码', 'utf8')
    content['Subject']=header
    server.sendmail(username, [username], content.as_string())



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

def test_needEncodeFiles():
    test_file = path.join(HERE, DIRS[0], 'test.file.py')
    test_file2 = path.join(HERE, DIRS[1], 'test.file.es2')
    open(test_file, 'w').write('testcontent')
    open(test_file2, 'w').write('testcontent')
    files = needEncodeFiles()
    print(files)
    encodeAll()
    os.remove(test_file)
    os.remove(test_file2)
    os.remove(test_file + '.encoded')
    os.remove(test_file2 + '.encoded')

def test_encodeAll():
    test_file = path.join(HERE, DIRS[0], 'test.file.py')
    test_file2 = path.join(HERE, DIRS[1], 'test.file.es2')
    open(test_file, 'w').write('testcontent')
    open(test_file2, 'w').write('testcontent')
    encodeAll()
    print(PASSWORDS)
    os.remove(test_file)
    os.remove(test_file2)
    os.remove(test_file + '.encoded')
    os.remove(test_file2 + '.encoded')
    

def test_sendPasswords():
    pws = open('.passwords', 'r').read()
    sendPasswords(pws)


if __name__=='__main__':
    # test_genereate_password() 
    # test_encode_decode()
    # test_needEncodeFiles()
    test_encodeAll()
    test_sendPasswords()
