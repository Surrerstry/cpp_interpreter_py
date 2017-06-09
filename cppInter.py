import os
import re
import sys
import doctest
import subprocess
import termcolor
import readline


def check_existed_environments(working_directory = '.'):
    """
    :type working_directory: str
    :rtype: list[str]
    
    Function check if passed directory already contains environments 
    directories that match to pattern 'env\d+', because next envronment 
    will be created with next number
    
    >>> check_existed_environments('.')
    ('env...', '.')
    >>> check_existed_environments('./test')
    ('env...', './test')
    """
    
    if os.path.exists(working_directory)==False:
        os.mkdir(working_directory)
    
    dir_tree = os.walk(working_directory)

    dirs = [dirnames for root, dirnames, filenames in dir_tree if root == working_directory]

    dirs = [envX for envX in dirs[0] if re.match(r'env\d+', envX)][::-1]
    
    number = 1
    for item in dirs:
        res = re.search('\d+', item)
        if int(item[res.start():res.end()+1])+1>number:
                number = int(item[res.start():res.end()+1])+1
    
    return 'env'+str(number) if len(dirs)>0 else 'env1', working_directory


def create_next_catalog(next_directory, working_directory):
    """    
    :type next_directory: str
    :type working_directory: str
    
    :rtype: str
    
    >>> create_next_catalog('env33', '.')
    'env33'
    >>> create_next_catalog('env22', './test')    
    './test/env22'
    """
            
    if working_directory=='.':
        os.mkdir(next_directory)
        open(next_directory+'/'+'main.cpp', 'a').close()
        return next_directory
        
    else:
        os.mkdir(working_directory+'/'+next_directory)
        open(working_directory+'/'+next_directory+'/'+'main.cpp', 'a').close()
        return working_directory+'/'+next_directory


def command_loop(env_directory):
    """
    :type env_directory: str
    
    :rtype: int    
    
    To make multiline block of code end line with space
    
    to remove specific line from code write line_number:-
    for example: 
    5:- # it cause remove fifth line from buffer
    
    to change specific line in buffer type line_number:: new code here;
    for example:
    1::#include <stdio.h> 
    
    _exit - finish program
    
    _r - restart buffer    
    
    ***
    other issues:
    
    statements that start with hash sign(#)
    eg. 
    #include <math.h> 
    #include <stdio.h>
    have to be adding one by one
    you cannot add these statements in multiline block of code
    ***
    
    """

    print('env:', env_directory)
    
    include_stack = ['#include <iostream>',]
    main_stack = 'int main() {\n'
    
    include_stack_restart_buffer = include_stack[:]
    main_stack_restart_buffer = main_stack
    
    last_include_stack = include_stack[:]
    last_main_stack = main_stack
    
    remove_flag = False
    inc_stack = False
    change_flag = False
    line_to_remove = 0
    line_to_change = 0
    
    while True:
        
        prompt = termcolor.colored('>>', 'green')
        command = input(prompt)
        
        if command=="_exit":
            break
        
                
        if command == '_r':
            main_stack = main_stack_restart_buffer
            include_stack = include_stack_restart_buffer
            continue
        

        if re.match('\d+::', command):
            line_to_change = re.match('\d+', command)
            line_to_change = int(line_to_change.string[:line_to_change.end()])
            command_shift = re.match('\d+::', command).span()[1]
            change_flag = True
        
        if re.match('\d+:-', command):
            line_to_remove = re.match('\d+', command)
            line_to_remove = line_to_remove.string[:line_to_remove.end()]
            command = ''
            remove_flag = True

        with open(env_directory+'/commands.log', 'a') as f:
            f.write(command+'\n')
                
        if len(command) and command[0]=='#':
            include_stack.append(command)
            inc_stack = True
        
        file = open(env_directory+'/main.cpp', 'w')
        
        if len(command) and command[-1] == " " and remove_flag!=True and change_flag==False:
            main_stack += command+'\n'
            continue
        elif remove_flag!=True and inc_stack==False and change_flag==False:
            main_stack += command+'\n'
        inc_stack = False
            
        code = '\n'.join(include_stack)+'\n'+main_stack+'}'
        code = code.split('\n')
        
        if change_flag:
            try:
                code[line_to_change-1] = command[command_shift:]
            except:
                include_stack = last_include_stack[:]
                main_stack = last_main_stack
                change_flag=False
                print('incorrect line!')
                continue
        
        if remove_flag:
            line_to_remove = int(line_to_remove)
            try:
                code.pop(line_to_remove-1)
            except:
                include_stack = last_include_stack[:]
                main_stack = last_main_stack
                remove_flag=False
                print('incorrect line!')
                continue
        
        code = [non_empty_string for non_empty_string in code if len(non_empty_string)>0]
        
        if remove_flag or change_flag:
            main_pos = code.index('int main() {')
            include_stack = '\n'.join(code[:main_pos]).split('\n')
            main_stack = '\n'.join(code[main_pos:-1])+'\n'
        
        remove_flag=False
        change_flag = False
        
        to_print = [termcolor.colored(str(idx)+':', 'yellow')+' '+line for idx, line in enumerate(code, start=1)]
        to_print = '\n'.join(to_print)
        
        execute = [line for idx, line in enumerate(code, start=1)]
        execute = '\n'.join(execute)
        
        file.write(execute)
        file.close()
        
        return_code = subprocess.Popen('g++ '+env_directory+'/main.cpp -o {}/main.bin'.format(env_directory, env_directory), shell=True)
        return_code.wait()

        if return_code.returncode:
            include_stack = last_include_stack[:]
            main_stack = last_main_stack
            print('Compilation failed\nStacks restored to last correct structure!')
            continue
        
        print(to_print)
        
        called_program = subprocess.Popen('{}/main.bin'.format(env_directory), stdout=subprocess.PIPE, shell=True)
        called_program.wait()
        
        print('return_code: {}; output: {}'.format(return_code.returncode, called_program.stdout.read()), end='')
        print('')
        
        last_include_stack = include_stack[:]
        last_main_stack = main_stack
            
    return 0
        

if __name__ == "__main__":
    """
    As first parameter you can define workplace directory.
    If you don't pass second parameter,
    script will make 'env' directory in current script position('.')
    """

    if len(sys.argv)==2:
        workplace = sys.argv[1]
    else:
        workplace = '.'
    
    #doctest.testmod(verbose=True, optionflags=doctest.ELLIPSIS)
    
    # to doctest
    #print(create_next_catalog(*check_existed_environments()))
    #print(create_next_catalog(*check_existed_environments('./tests')))    
    #print(create_next_catalog(*check_existed_environments('./tests123')))
        
    command_loop(create_next_catalog(*check_existed_environments(workplace)))
    
    
