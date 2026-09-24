import prompt


def welcome():
    print('Первая попытка запустить проект!')
    print('\n***')

    command = 'help'
    while command != 'exit':
        if command == 'help':
            print('<command> exit - выйти из программы')
            print('<command> help - справочная информация')

        command = prompt.string('Введите команду: ')
