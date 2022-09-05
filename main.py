#!/usr/bin/env python
# -*- coding: utf-8 -*-
import atexit
import codecs
import csv
import random
import time
from os.path import join
from statistics import mean

import yaml
from psychopy import visual, event, logging, gui, core

from misc.screen_misc import get_screen_res, get_frame_rate
from itertools import combinations_with_replacement, product


@atexit.register
def save_beh_results():
    # Cała funkcja dostarczona od Bartka
    # Wykonuje zapis wyników do pliku
    """
    Save results of experiment. Decorated with @atexit in order to make sure, that intermediate
    results will be saved even if interpreter will broke.
    """
    with open(
            join('results', PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'),
            'w',
            encoding='utf-8'
    ) as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def abort_with_error(err):
    # Funkcja zapisuje błąd w tym całym logu i przerywa działanie programu z błędem
    logging.critical(err)
    raise Exception(err)


def execute_dialog_popup():
    # Wyświetla modal z formularzem do podania danych osoby badanej
    # Zamienia podane dane w identifokator badanego
    info = {
        'IDENTYFIKATOR': '',
        u'P\u0141EC': ['M', "K"],
        'WIEK': '20'
    }
    dictDlg = gui.DlgFromDict(
        dictionary=info,
        title='Funkcjonowanie mózgowych mechanizmów percepcji i uwagi wzrokowej'
    )
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    return info['IDENTYFIKATOR'] + info[u'P\u0141EC'] + info['WIEK']


def configure_logging(part_id):
    # Konfiguracja logowania z aplikacji (podanie nazwy pliku)
    # Od Bartka
    logging.LogFile(
        join('results', part_id + '.log'),
        level=logging.INFO
    )


def create_results_headers():
    # Tworzy nagłówki dla listy wyników badanego
    return [
        'Part ID',  # ID
        'Trial no',  # numer próby
        'Reaction time',  # czas reakcji osoby badanej
        'Correctness',  # poprawnosc odpowiedzi badanego wzgledem klucza
        'Stimulus',  # rodzaj bodzca w danej próbie
        'Hint',  # rodzaj podpowiedzi (czerwona lub zielona)
        'Complies with distractors',  # wcisniety klawisz przy blednej odpowiedzi (zgodny z dystraktorami lub zupelnie inny)
        'Fail time'  # szybkosc nastepnych odpowiedzi po udzieleniu blednej
    ]


def load_config():
    # Załaduj konfirugajcę eksperymentu z pliku configu gdzie wszystko jest
    # Od Bartka też
    return yaml.safe_load(open('config.yaml', encoding='utf-8'))


def create_window(conf):
    # Tworzy okno do przeprowadzanie eksperytmentu
    win = visual.Window(
        list(SCREEN_RES.values()),
        fullscr=False,
        monitor='testMonitor',
        units='pix',
        screen=0,
        color=conf['BACKGROUND_COLOR']
    )

    # Make mouse invisible
    event.Mouse(visible=False, newPos=None, win=win)

    # Check frame rate
    frame_rate = get_frame_rate(win)

    # check if a detected frame rate is consistent with a frame rate for witch experiment was designed
    # important only if milisecond precision design is used
    # nie wiem, ale działa

    # Od Bartka
    if frame_rate < conf['FRAME_RATE']:
        dlg = gui.Dlg(title="Critical error")
        dlg.addText('Wrong no of frames detected: {}. Experiment terminated.'.format(frame_rate))
        dlg.show()
        return None

    logging.info('FRAME RATE: {}'.format(frame_rate))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    return win


def read_text_from_file(file_name, insert=''):
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    :param file_name: Name of file to read
    :param insert:
    :return: message
    """
    # Od Bartka
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def abort_with_escape():
    abort_with_error('Experiment finished by user on info screen! ESC pressed.')


def show_info(win, conf, file_name, insert=''):
    # Od Bartka (przerobione w pewnym stopniu)
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(
        win,
        color=conf['STIM_COLOR'],
        text=msg,
        height=20,
        wrapWidth=SCREEN_RES['width']
    )
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['escape', 'space'])
    if key == ['escape']:
        abort_with_escape()
    win.flip()


def show_break_info(win, conf):
    msg = read_text_from_file(join('.', 'messages', 'break.txt'))
    msg = visual.TextStim(
        win,
        color=conf['STIM_COLOR'],
        text=msg,
        height=20,
        wrapWidth=SCREEN_RES['width']
    )
    msg.draw()
    win.flip()


def generate_experiment_values(conf):
    # Wygenerowanie wartości dla pojedyńczego eksperymentu
    target = random.choice(conf['REACTION_KEYS'])
    dist = random.choice(conf['REACTION_KEYS'])
    que = True
    if target != dist:
        que = False

    # Skrypt decyduje tu (losowo) czy dystraktory neutralne będą po lewej czy prawej stronie
    if random.random() > 0.5:
        empty_stim = '[][]_' + dist.upper() + dist.upper()
        stim = '[][]' + target.upper() + dist.upper() + dist.upper()
    else:
        empty_stim = dist.upper() + dist.upper() + '_[][]'
        stim = dist.upper() + dist.upper() + target.upper() + '[][]'

    return {
        'target': target,
        'dist': dist,
        'que': que,
        'empty_stim': empty_stim,
        'stim': stim
    }

def display_fix_point(win, conf):
    # Wyświetla sam punkt fiksacji
    msg = visual.TextStim(
        win,
        color=conf['FIX_CROSS_COLOR'],
        text='+',
        height=20,
        wrapWidth=SCREEN_RES['width']
    )
    # Od Bartka i nie wiem do czego to msg dokładnie ale działa
    msg.draw()
    win.flip()
    time.sleep(conf['FIX_CROSS_TIME_MS'] / 1000)


def display_que(win, conf, is_correct):
    # Wyświetla kółko w określonym kolorze
    color = conf['QUE_INCORRECT_COLOR']
    if is_correct:
        color = conf['QUE_CORRECT_COLOR']

    msg = visual.Circle(
        win,
        radius=conf['QUE_RADIUS'],
        fillColor=conf['QUE_FILL_COLOR'],
        lineColor=color
    )

    msg.draw()
    win.flip()
    time.sleep(conf['QUE_TIME_MS'] / 1000)


def display_with_empty_stimulus(win, conf, stim):
    # Wyświetla punkt fiksacji razem z bodźcem z podkreślnikiem
    text = '\n\n'.join(['+', stim])
    msg = visual.TextStim(
        win,
        color=conf['STIM_COLOR'],
        text=text,
        height=20,
        wrapWidth=SCREEN_RES['width'],
        pos=(0, -20)
    )
    msg.draw()
    win.flip()
    time.sleep(conf['STIM_EMPTY_MS'] / 1000)


def display_with_stimulus(win, conf, stim):
    # Wyświetla punkt fiksacji razem z bodźcem
    text = '\n\n'.join(['+', stim])
    msg = visual.TextStim(
        win,
        color=conf['STIM_COLOR'],
        text=text,
        height=20,
        wrapWidth=SCREEN_RES['width'],
        pos=(0, -20)
    )
    msg.draw()
    win.flip()
    keys = conf['REACTION_KEYS'] + ['escape']
    key = event.waitKeys(keyList=keys)
    if key == ['escape']:
        abort_with_escape()
    win.flip()
    return key


def perform_experiment(win, conf, clock):
    # Przeprowadza pojedyńczy eksperyment
    experiment_values = generate_experiment_values(conf)
    print(experiment_values)

    # punkt fiksacji 500ms
    display_fix_point(win, conf)

    # kółko 200ms
    display_que(win, conf, experiment_values.get('que'))

    display_with_empty_stimulus(win, conf, experiment_values.get('empty_stim'))

    clock.reset()
    # prezentacja (do kliknięcia)
    result = display_with_stimulus(win, conf, experiment_values.get('stim'))
    print(result)
    reaction_time = clock.getTime()
    print(reaction_time)

    return {
        'reaction_time': reaction_time,
        'correctness': result[0] == experiment_values.get('target'),
        'stimulus': experiment_values.get('target'),
        'hint': experiment_values.get('que'),
        'complies_with_distractors': result[0] == experiment_values.get('dist')
    }


def display_training_result(win, conf, correct):
    # Wyświetla wynik eksperymentu testowego
    stim = visual.TextStim(
        win,
        text="Poprawnie" if correct else "Niepoprawnie",
        height=50,
        color=conf['STIM_COLOR']
    )
    stim.draw()
    win.flip()

    # Chodzi o ten czas odpowiedzi jaki był po failu jednym
def calculate_fail_time():
    for idx, result in enumerate(RESULTS):
        print(idx)
        print(result)

        if idx == 0:
            continue
        if idx == 1:
            RESULTS[idx].append(0)
            continue
        before_result = RESULTS[idx - 1]
        if before_result[3] == 'YES':
            RESULTS[idx].append(0)
        else:
            RESULTS[idx].append(result[2])


# GLOBALS i tu się zaczyna właśnie wszystko
RESULTS = list()  # list in which data will be colected

def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global
    random.seed()
    #seed jest dlatego bo się daje ziarno jak np clock i na tej podstawie rośnie drzewo z "losowymi" liczbami

    PART_ID = execute_dialog_popup()
    configure_logging(PART_ID)

    conf = load_config()
    clock = core.Clock()
    win = create_window(conf)

    RESULTS.append(create_results_headers())

    show_info(win, conf, join('.', 'messages', 'before_training.txt'))

    for x in range(conf['TRAININGS_QUANTITY']):
        result = perform_experiment(win, conf, clock)

        if (result.get('correctness')):
            display_training_result(win, conf, True)
        else:
            display_training_result(win, conf, False)

        # przerwa 1s
        time.sleep(conf['EXPERIMENT_BREAK_TIME_MS'] / 1000)

        print(result)

    show_info(win, conf, join('.', 'messages', 'before_experiment.txt'))

    trial_no = 1
    for session in range(conf['EXPERIMENTS_SESSIONS_QUANTITY']):
        for experiment in range(conf['EXPERIMENTS_QUANTITY']):
            result = perform_experiment(win, conf, clock)
            RESULTS.append([
                PART_ID,
                trial_no,
                result.get('reaction_time'),
                'YES' if result.get('correctness') else 'NO',
                result.get('stimulus'),
                'GREEN' if result.get('hint') else 'RED',
                'YES' if result.get('complies_with_distractors') else 'NO'
            ])
            trial_no = trial_no + 1

            # przerwa 1s
            time.sleep(conf['EXPERIMENT_BREAK_TIME_MS'] / 1000)

            print(result)

        if ((session+1) != conf['EXPERIMENTS_SESSIONS_QUANTITY']):
            show_break_info(win, conf)
            # przerwa 1min
            time.sleep(conf['SESSION_BREAK_TIME_MS'] / 1000)

    print(RESULTS)

    calculate_fail_time()

    save_beh_results()

    show_info(win, conf, join('.', 'messages', 'end.txt'))
    win.close()

if __name__ == '__main__':
    PART_ID=''
    SCREEN_RES=get_screen_res()
    main()
