import sys

sys.path.append("../AVCommon")
sys.path.append("../AVMaster")

from AVCommon.protocol import Protocol
from AVCommon.procedure import Procedure
from AVCommon.command import Command
from AVCommon.mq import MQStar

import threading
import logging
import logging.config


def server_procedure(mq, clients, procedure):
    global received
    exit = False
    print "- SERVER ", len(procedure)
    numcommands = len(procedure)

    p = {}
    for c in clients:
        p[c] = Protocol(mq, c, procedure)
        p[c].send_next_command()

    ended = 0
    answered = 0
    while not exit and ended < len(clients):
        rec = mq.receive_server(blocking=True, timeout=10)
        if rec is not None:
            print "- SERVER RECEIVED %s %s" % (rec, type(rec))
            c, msg = rec
            answer = p[c].receive_answer(c, msg)
            answered += 1
            print "- SERVER RECEIVED ANSWER: ", answer.success
            if answer.name == "END" or not answer.success:
                ended += 1
                print "- SERVER RECEIVE END"
            if answer.success:
                p[c].send_next_command()

        else:
            print "- SERVER RECEIVED empty"
            exit = True

    print answered, ended, numcommands
    assert (ended == len(clients))
    assert (answered == (len(clients) * numcommands))


def test_ProtocolProcedure():
    host = "localhost"
    mq1 = MQStar(host)
    mq1.clean()
    c = "client1"
    mq1.add_client(c)

    commands = [("BEGIN", None, None),("START_AGENT", None, None),("STOP_AGENT", None, None), ("END", None, None)]
    procedure = Procedure("PROC", commands)

    thread1 = threading.Thread(target=server_procedure, args=(mq1, [c], procedure))
    thread1.start()

    cmdStart = Command.unserialize(('BEGIN', True, 'nothing else to say'))

    assert cmdStart

    print "- CLIENT: ", c
    pc = Protocol(mq1, c)
    exit = False
    while not exit:
        received = pc.receive_command()
        print "- CLIENT RECEIVED: ", received
        if received.name == "STOP_AGENT":
            exit = True


def test_ProtocolEval():
    host = "localhost"
    mq = MQStar(host)
    mq.clean()
    c = "client1"
    mq.add_client(c)

    commands = [("EVAL_SERVER", "dir()"),
                ("EVAL_SERVER", "locals()"),
                ("EVAL_SERVER", "__import__('os').getcwd()"),
                ("EVAL_SERVER", "*'END'")]
    procedure = Procedure("PROC", commands)

    p = Protocol(mq, c, procedure)

    while p.send_next_command():
        logging.debug("sent command")

    exit = False
    while not exit:
        rec = mq.receive_server(blocking=True, timeout=10)
        if rec is not None:
            print "- SERVER RECEIVED %s %s" % (rec, type(rec))
            c, msg = rec
            answer = p.receive_answer(c, msg)
            print "- SERVER RECEIVED ANSWER: ", answer.success
            if answer.name == "END" or not answer.success:
                print "- SERVER RECEIVE END"
                #if answer.success:
            a = """('client1', ('EVAL_SERVER', True, {'self': <Command_EVAL_SERVER.Command_EVAL_SERVER object at 0x10931f810>, 'args': 'locals()'}))"""#   p.send_next_command()

        else:
            print "- SERVER RECEIVED empty"
            exit = True

def test_ProtocolCall():
    host = "localhost"
    mq = MQStar(host)
    mq.clean()
    c = "client1"
    mq.add_client(c)

    yaml = """BASIC:
    - EVAL_SERVER: dir()

CALLER:
    - CALL: BASIC
    - EVAL_SERVER: locals()
    - EVAL_SERVER: *END
"""
    procedures = Procedure.load_from_yaml(yaml)

    caller = Procedure.procedures["CALLER"]
    basic = Procedure.procedures["BASIC"]

    p = Protocol(mq, c, caller)
    while p.send_next_command():
        logging.debug("sent command")

    exit = False
    answers =0
    while not exit:
        rec = mq.receive_server(blocking=True, timeout=10)
        if rec is not None:
            print "- SERVER RECEIVED %s %s" % (rec, type(rec))
            c, msg = rec
            answer = p.receive_answer(c, msg)
            print "- SERVER RECEIVED ANSWER: ", answer.success
            if answer.success:
                answers += 1
            if answer.name == "END" or not answer.success:
                print "- SERVER RECEIVE END"
                #if answer.success:

        else:
            print "- SERVER RECEIVED empty"
            exit = True

    assert answers == 2, "wrong answers: %s" % answers

if __name__ == '__main__':
    logging.config.fileConfig('../logging.conf')
    #test_ProtocolProcedure()
    #test_ProtocolEval()
    test_ProtocolCall()
