import logging
import random
import re

from lib import config
from lib import irc

class _Question:
    """Encapsulate a question and its answers."""
    def __init__(self, question, answers, correct_answer_idx):
        self.question = question
        self.answers = tuple(answers)
        self.correct_answer_idx = correct_answer_idx


class _RandomIterator:
    """An iterator over a given sequence returning elements randomly."""

    def __init__(self, elements):
        self._elements = list(elements)
        # Get a random permutation of the elements list and start going
        # through it from the beginning.
        random.shuffle(self._elements)
        self._idx = 0

    def __iter__(self):
        return self

    def __next__(self):
        """Advance to the next element."""
        if self._idx >= len(self._elements):
            raise StopIteration
        self._idx += 1
        return self._elements[self._idx - 1]


class Handler(irc.HandlerBase):
    """IRC handler to implement a trivia bot."""

    # Regular expressions to match against supported commands.
    _QUESTION_RE = re.compile(r'^!trivia$', flags=re.IGNORECASE)
    _ANSWER_RE = re.compile(r'^!answer +([a-zA-Z])$', flags=re.IGNORECASE)

    def __init__(self, conn, conf):
        super().__init__(conn)
        self._channel = conf['CONNECTION']['channel'].lower()
        trivia_section = config.GetSection(conf, 'trivia')
        if 'questions_file' not in trivia_section:
            raise Exception('"questions_file" not found in TRIVIA config '
                            'section')
        self._report_errors = trivia_section.getboolean('report_errors')
        self._use_whisper = trivia_section.getboolean('use_whisper')
        self._questions = self._ParseQuestions(trivia_section['questions_file'])
        if not self._questions:
            raise Exception('Question list is empty.')
        self._Restart()
        logging.info('plugin ready')

    @staticmethod
    def _ParseQuestions(questions_file):
        questions = []
        with open(questions_file) as f:
            question = None
            answers = []
            correct_answer = -1
            for line in f:
                # Drop any comment part of the line.
                line = line.split('#', maxsplit=1)[0]
                line = line.strip()
                if not line:
                    continue
                if line.startswith('Q:'):
                    if question and len(answers) > 1 and correct_answer >= 0:
                        questions.append(_Question(question, answers,
                                                   correct_answer))
                    question = line[2:].strip()
                    answers = []
                    correct_answer = -1
                elif line.startswith('CA:') or line.startswith('A:'):
                    if not question:
                        continue
                    if line.startswith('CA:'):
                        answer = line[3:]
                        if correct_answer >= 0:
                            logging.warning(
                                'found multiple correct answers for question '
                                '%r: %r and %r', question,
                                answers[correct_answer], answer)
                            # Skip this question entirely.
                            question = None
                            answers = []
                            correct_answer = -1
                            continue
                        # Got correct answer, store it.
                        correct_answer = len(answers)
                        answers.append(answer)
                    else:
                        # Line starts with "A:".
                        answers.append(line[2:])
            if question and len(answers) > 1 and correct_answer >= 0:
                questions.append(_Question(question, answers, correct_answer))

        return questions

    def _Restart(self):
        """(re)start going over the question list."""
        self._iter = _RandomIterator(self._questions)
        self._active_question = None

    def HandlePRIVMSG(self, msg):
        """The entry point into this plugin, handle a chat message."""
        parts = irc.SplitPRIVMSG(msg)
        if len(parts) < 2 or not parts[1]:
            logging.warning('Got invalid PRIVMSG: %r', msg)
            return False

        command = parts[1].strip()
        if not command:
            return False

        match = self._QUESTION_RE.match(command)
        if match:
            return self._HandleQuestion(msg)

        match = self._ANSWER_RE.match(command)
        if match:
            return self._HandleAnswer(msg, match)

        return False

    def _ReportError(self, recipient, fmt, *args, level=logging.WARNING):
        if level is not None:
            logging.log(level, fmt, *args)
        if self._report_errors:
            if self._use_whisper:
                self._conn.SendWhisper(recipient, fmt % args)
            else:
                # Send a nicely formatted chat (public) message with the
                # user as a prefix.
                self._conn.SendMessage(self._channel,
                                       ''.join((recipient, ': ', fmt % args)))

    @staticmethod
    def _FormatQuestion(question):
        choices = ('%s. %s' % (chr(ord('A') + i), a)
                   for i, a in enumerate(question.answers))
        return ('%s %s. Type "!answer <letter>".' %
                (question.question, ' | '.join(choices)))

    def _HandleQuestion(self, msg):
        """Handle "!trivia" command to ask a new question."""
        if not self._active_question:
            # New question.
            self._active_question = next(self._iter, None)
            if not self._active_question:
                # Ran out of questions, restart.
                logging.info("Exhausted all questions. Starting over.")
                self._Restart()
                self._active_question = next(self._iter)
        self._conn.SendMessage(
            self._channel, self._FormatQuestion(self._active_question))
        return True

    def _HandleAnswer(self, msg, match):
        """Handle "!answer <choice-id>" command."""
        if not self._active_question:
            self._ReportError(msg.sender, 'Answer given but no trivia question '
                              'is currently active.')
            return True

        choice = match.group(1).strip().upper()
        choice = ord(choice) - ord('A')
        if choice == self._active_question.correct_answer_idx:
            self._conn.SendMessage(
                self._channel,
                msg.sender + ': You are correct, congratulations! To continue '
                'type !trivia')
            self._active_question = None
        # Don't do anything if the answer is wrong.
        return True
