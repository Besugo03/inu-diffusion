def printer(text: str, lines: int = 1):
    '''
    @param text: The string to print multiple times
    @param line: The number of lines the string should get printed. Defaults to 1.
    @return : 0 if it succeeded, -1 if it failed.
    '''
    for i in range(lines):
        print(text)
    return 0

printer("test","3")